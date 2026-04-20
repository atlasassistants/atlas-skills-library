"""
Gmail API Client Wrapper
=========================
High-level wrapper around the Gmail API. Every Gmail operation in the plugin
goes through this class so that individual skill scripts stay clean and readable.

Usage:
    from gmail_client import GmailClient

    client = GmailClient()  # Authenticates automatically via gmail_auth
    labels = client.list_labels()
    messages = client.search_messages("is:unread")
"""

import base64
import email.mime.text
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from runtime_paths import ensure_runtime_paths

ensure_runtime_paths()

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gmail_auth import get_credentials, ensure_fresh
from rate_limiter import get_default_limiter
from atlas_labels import ALL_ATLAS_LABELS, is_atlas_label
from safety import block_send_on_service
from structured_logger import get_logger
from quota_tracker import get_quota_tracker

# H6: Refresh the token at least every 10 minutes of wall-clock time, even if
# op count hasn't reached the 50-call threshold. Long skills with light API
# use would otherwise outlive the token and hit 401 mid-operation.
WALL_CLOCK_REFRESH_SEC = 600.0


class GmailClient:
    """
    High-level Gmail API client for the Atlas Inbox Zero plugin.

    Wraps the raw Google API into clean methods that the skill scripts call.
    Handles authentication automatically on init.
    """

    def __init__(
        self,
        credentials_path: str | Path | None = None,
        token_path: str | Path | None = None,
        user_id: str = "me",
    ):
        """
        Initialize the Gmail client. Authenticates on creation.

        Args:
            credentials_path: Path to credentials.json (optional, uses default)
            token_path: Path to token.json (optional, uses default)
            user_id: Gmail user ID. "me" = the authenticated user.
        """
        self._credentials_path = credentials_path
        self._token_path = token_path
        creds = get_credentials(credentials_path, token_path)
        self.service = build("gmail", "v1", credentials=creds)
        block_send_on_service(self.service)
        self.user_id = user_id
        self._limiter = get_default_limiter()
        self._ops_since_refresh_check = 0
        self._last_refresh_monotonic = time.monotonic()

    def _maybe_refresh_token(self) -> None:
        """Refresh if we've crossed the op-count (50) or wall-clock (10 min)
        threshold. Either trigger resets both counters."""
        log = get_logger()
        self._ops_since_refresh_check += 1
        now = time.monotonic()
        op_trigger = self._ops_since_refresh_check >= 50
        wall_trigger = (now - self._last_refresh_monotonic) >= WALL_CLOCK_REFRESH_SEC
        if not (op_trigger or wall_trigger):
            return

        self._ops_since_refresh_check = 0
        try:
            creds = ensure_fresh(self._credentials_path, self._token_path)
            self.service = build("gmail", "v1", credentials=creds)
            block_send_on_service(self.service)
            self._last_refresh_monotonic = now
        except Exception as exc:
            log.event(
                "gmail_api_error",
                kind="token_refresh",
                message=str(exc)[:500],
            )
            # will fail naturally on next API call — behavior preserved

    @staticmethod
    def _log_http_error(log, exc: "HttpError") -> None:
        """Emit a gmail_api_error structured event for an HttpError. Field
        shape: kind=http_error, status=<int>, message=str(exc)[:500]."""
        log.event(
            "gmail_api_error",
            kind="http_error",
            status=exc.resp.status,
            message=str(exc)[:500],
        )

    def _call_api(self, request):
        """
        Execute a Gmail API request with one retry on 401 (Unauthorized).

        If the first attempt raises a 401 HttpError, re-authenticates by
        calling get_credentials() + build() and retries the call once.
        Any caught HttpError that is re-raised first emits a
        gmail_api_error structured event.

        Every execute() attempt — success, failure, or retry — increments
        the quota tracker by 1. Tracker exceptions are isolated so they
        cannot break the API call.
        """
        log = get_logger()

        def _bump_quota() -> None:
            try:
                get_quota_tracker().record(1)
            except Exception:
                pass

        _bump_quota()
        try:
            return request.execute()
        except HttpError as exc:
            if exc.resp.status != 401:
                self._log_http_error(log, exc)
                raise
            creds = get_credentials(self._credentials_path, self._token_path)
            self.service = build("gmail", "v1", credentials=creds)
            block_send_on_service(self.service)
            _bump_quota()
            try:
                return request.execute()
            except HttpError as exc2:
                self._log_http_error(log, exc2)
                raise

    # ─────────────────────────────────────────────
    # LABELS
    # ─────────────────────────────────────────────

    def list_labels(self) -> list[dict]:
        """Return all labels in the account."""
        self._maybe_refresh_token()
        self._limiter.acquire()
        result = self._call_api(self.service.users().labels().list(userId=self.user_id))
        return result.get("labels", [])

    def get_label(self, label_id: str) -> dict:
        """Get a single label by ID."""
        self._maybe_refresh_token()
        self._limiter.acquire()
        return self._call_api(self.service.users().labels().get(
            userId=self.user_id, id=label_id
        ))

    def find_label_by_name(self, name: str) -> dict | None:
        """Find a label by its display name. Returns None if not found."""
        self._maybe_refresh_token()
        for label in self.list_labels():
            if label["name"] == name:
                return label
        return None

    def create_label(
        self,
        name: str,
        label_list_visibility: str = "labelShow",
        message_list_visibility: str = "show",
        color: dict[str, str] | None = None,
    ) -> dict:
        """
        Create a new Gmail label.

        Args:
            name: Display name (e.g., "1-Action Required")
            label_list_visibility: "labelShow", "labelShowIfUnread", or "labelHide"
            message_list_visibility: "show" or "hide"
            color: Optional Gmail label color object with backgroundColor/textColor

        Returns:
            The created label resource.

        Skips creation if a label with the same name already exists (returns existing).
        """
        self._maybe_refresh_token()
        existing = self.find_label_by_name(name)
        if existing:
            return existing

        body = {
            "name": name,
            "labelListVisibility": label_list_visibility,
            "messageListVisibility": message_list_visibility,
        }
        if color is not None:
            body["color"] = color
        self._limiter.acquire()
        return self._call_api(self.service.users().labels().create(
            userId=self.user_id, body=body
        ))

    def update_label(
        self,
        label_id: str,
        *,
        name: str | None = None,
        label_list_visibility: str | None = None,
        message_list_visibility: str | None = None,
        color: dict[str, str] | None = None,
    ) -> dict:
        """Patch a label's metadata and return the updated resource."""
        self._maybe_refresh_token()
        self._limiter.acquire()
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if label_list_visibility is not None:
            body["labelListVisibility"] = label_list_visibility
        if message_list_visibility is not None:
            body["messageListVisibility"] = message_list_visibility
        if color is not None:
            body["color"] = color
        return self._call_api(self.service.users().labels().patch(
            userId=self.user_id, id=label_id, body=body
        ))

    def hide_label(self, label_id: str) -> dict:
        """Hide a label from the Gmail label list without deleting it."""
        return self.update_label(label_id, label_list_visibility="labelHide")

    def delete_label(self, label_id: str) -> None:
        """Delete a label by ID."""
        self._maybe_refresh_token()
        self._limiter.acquire()
        self._call_api(self.service.users().labels().delete(
            userId=self.user_id, id=label_id
        ))

    # ─────────────────────────────────────────────
    # MESSAGES — Search, Read, Modify
    # ─────────────────────────────────────────────

    def search_messages(
        self,
        query: str,
        max_results: int = 100,
        page_token: str | None = None,
    ) -> dict:
        """
        Search for messages using Gmail search syntax.

        Args:
            query: Gmail search query (e.g., "is:unread", "from:boss@company.com",
                   "label:1-action-required", "before:2026/01/01")
            max_results: Maximum messages to return (default 100, max 500)
            page_token: Token for pagination (from previous response)

        Returns:
            Dict with "messages" (list of {id, threadId}) and optional "nextPageToken"
        """
        self._maybe_refresh_token()
        self._limiter.acquire()
        kwargs = {
            "userId": self.user_id,
            "q": query,
            "maxResults": min(max_results, 500),
        }
        if page_token:
            kwargs["pageToken"] = page_token

        result = self._call_api(self.service.users().messages().list(**kwargs))
        return {
            "messages": result.get("messages", []),
            "nextPageToken": result.get("nextPageToken"),
            "resultSizeEstimate": result.get("resultSizeEstimate", 0),
        }

    def search_all_messages(self, query: str, max_results: int = 1000) -> list[dict]:
        """
        Search and paginate through all results up to max_results.
        Returns a flat list of {id, threadId} dicts.
        """
        all_messages = []
        page_token = None

        while len(all_messages) < max_results:
            self._maybe_refresh_token()
            batch_size = min(500, max_results - len(all_messages))
            result = self.search_messages(query, max_results=batch_size, page_token=page_token)
            all_messages.extend(result["messages"])

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        return all_messages[:max_results]

    def read_message(
        self,
        message_id: str,
        format: str = "full",
    ) -> dict:
        """
        Read a single message.

        Args:
            message_id: The message ID
            format: "full" (parsed), "raw" (RFC 2822), "metadata" (headers only),
                    or "minimal" (just IDs and labels)

        Returns:
            The message resource with headers, body, labels, etc.
        """
        self._maybe_refresh_token()
        self._limiter.acquire()
        return self._call_api(self.service.users().messages().get(
            userId=self.user_id, id=message_id, format=format
        ))

    def read_thread(self, thread_id: str, format: str = "full") -> dict:
        """
        Read an entire thread (all messages in a conversation).

        Args:
            thread_id: The thread ID
            format: Same options as read_message

        Returns:
            Thread resource with "messages" list.
        """
        self._maybe_refresh_token()
        self._limiter.acquire()
        return self._call_api(self.service.users().threads().get(
            userId=self.user_id, id=thread_id, format=format
        ))

    def get_message_headers(self, message: dict) -> dict[str, str]:
        """
        Extract common headers from a message resource into a clean dict.
        Returns: {from, to, cc, bcc, subject, date}
        """
        headers = {}
        payload = message.get("payload", {})
        for header in payload.get("headers", []):
            name = header["name"].lower()
            if name in ("from", "to", "cc", "bcc", "subject", "date"):
                headers[name] = header["value"]
        return headers

    def get_message_body(self, message: dict) -> str:
        """
        Extract the plain-text body from a message resource.
        Handles both simple and multipart messages.
        """
        payload = message.get("payload", {})
        return self._extract_body(payload)

    def _extract_body(self, payload: dict) -> str:
        """Recursively extract plain text from message payload."""
        mime_type = payload.get("mimeType", "")

        # Simple message with body directly
        if mime_type == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        # Multipart — recurse into parts
        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        # If no plain text found, try HTML as fallback
        for part in parts:
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        # Nested multipart
        for part in parts:
            if part.get("mimeType", "").startswith("multipart/"):
                result = self._extract_body(part)
                if result:
                    return result

        return ""

    # ─────────────────────────────────────────────
    # MESSAGES — Label Operations
    # ─────────────────────────────────────────────

    def apply_label(self, message_id: str, label_id: str) -> dict:
        """Apply a label to a message."""
        self._maybe_refresh_token()
        return self.modify_message(message_id, add_label_ids=[label_id])

    def apply_atlas_label(
        self,
        message_id: str,
        label_name: str,
        state_store=None,
    ) -> dict:
        """
        Apply an Atlas label, enforcing single-label rule.

        1. Read message's current labels
        2. Identify existing Atlas labels
        3. Remove existing Atlas label(s) before applying the new one
        4. Optionally record in state store
        5. Return what was removed + added

        Args:
            message_id: The message ID
            label_name: Atlas label name (e.g., "1-Action Required")
            state_store: Optional StateStore instance for recording
        """
        import warnings
        if not is_atlas_label(label_name):
            warnings.warn(
                f"apply_atlas_label called with non-Atlas label '{label_name}'. "
                "Use apply_label() for non-Atlas labels.",
                stacklevel=2,
            )

        # Resolve the new label's ID
        new_label = self.find_label_by_name(label_name)
        if not new_label:
            raise ValueError(f"Atlas label '{label_name}' not found in Gmail.")
        new_label_id = new_label["id"]

        # Read current labels on the message
        msg = self.read_message(message_id, format="minimal")
        current_label_ids = set(msg.get("labelIds", []))

        # Find existing Atlas labels to remove
        remove_ids = []
        removed_names = []
        for atlas_name in ALL_ATLAS_LABELS:
            if atlas_name == label_name:
                continue  # Don't remove the one we're adding
            atlas_label = self.find_label_by_name(atlas_name)
            if atlas_label and atlas_label["id"] in current_label_ids:
                remove_ids.append(atlas_label["id"])
                removed_names.append(atlas_name)

        # Apply in one API call: remove old + add new
        self.modify_message(
            message_id,
            add_label_ids=[new_label_id],
            remove_label_ids=remove_ids if remove_ids else None,
        )

        # Record in state store if provided
        if state_store is not None:
            for old_name in removed_names:
                state_store.remove_label_record(message_id, old_name)
            state_store.record_label_applied(message_id, label_name)

        return {
            "message_id": message_id,
            "added": label_name,
            "removed": removed_names,
        }

    def remove_label(self, message_id: str, label_id: str) -> dict:
        """Remove a label from a message."""
        self._maybe_refresh_token()
        return self.modify_message(message_id, remove_label_ids=[label_id])

    def modify_message(
        self,
        message_id: str,
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
    ) -> dict:
        """
        Modify a message's labels.

        Args:
            message_id: The message ID
            add_label_ids: Label IDs to add
            remove_label_ids: Label IDs to remove

        Returns:
            Updated message resource.
        """
        self._maybe_refresh_token()
        self._limiter.acquire()
        body = {}
        if add_label_ids:
            body["addLabelIds"] = add_label_ids
        if remove_label_ids:
            body["removeLabelIds"] = remove_label_ids

        return self._call_api(self.service.users().messages().modify(
            userId=self.user_id, id=message_id, body=body
        ))

    def archive_message(self, message_id: str) -> dict:
        """Archive a message (remove INBOX label). Never deletes."""
        self._maybe_refresh_token()
        return self.remove_label(message_id, "INBOX")

    def batch_archive(self, message_ids: list[str]) -> list[dict]:
        """Archive multiple messages. Returns list of results."""
        results = []
        for msg_id in message_ids:
            self._maybe_refresh_token()
            results.append(self.archive_message(msg_id))
        return results

    def batch_modify_messages(
        self,
        message_ids: list[str],
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
    ) -> None:
        """
        Modify labels on multiple messages in a single API call (up to 1000).

        NOTE (C2 integrity tradeoff): Gmail's batchModify is all-or-nothing at the
        HTTP level and returns no per-message response body. Callers that need
        per-message error attribution MUST use per-message modify_message instead
        (as apply_decisions does). Only low-stakes bulk paths (initial_cleanup)
        should use this method.
        """
        log = get_logger()
        self._maybe_refresh_token()
        self._limiter.acquire()
        body: dict[str, Any] = {"ids": message_ids}
        if add_label_ids:
            body["addLabelIds"] = add_label_ids
        if remove_label_ids:
            body["removeLabelIds"] = remove_label_ids

        try:
            self._call_api(self.service.users().messages().batchModify(
                userId=self.user_id, body=body
            ))
        except Exception:
            log.event(
                "batch_modify",
                count=len(message_ids),
                add_labels=len(add_label_ids or []),
                remove_labels=len(remove_label_ids or []),
                status="error",
            )
            raise

        log.event(
            "batch_modify",
            count=len(message_ids),
            add_labels=len(add_label_ids or []),
            remove_labels=len(remove_label_ids or []),
            status="ok",
        )

    # ─────────────────────────────────────────────
    # FILTERS
    # ─────────────────────────────────────────────

    def create_filter(
        self,
        criteria: dict,
        add_label_ids: list[str] | None = None,
        remove_label_ids: list[str] | None = None,
        should_archive: bool = False,
        should_mark_read: bool = False,
        should_never_spam: bool = False,
    ) -> dict:
        """
        Create a Gmail filter.

        Args:
            criteria: Filter criteria dict. Keys can include:
                - "from": sender email/pattern
                - "to": recipient email/pattern
                - "subject": subject pattern
                - "query": freeform Gmail search query
                - "hasAttachment": bool
                - "size": size in bytes
                - "sizeComparison": "larger" or "smaller"
            add_label_ids: Labels to apply to matching messages
            remove_label_ids: Labels to remove from matching messages
            should_archive: Skip the inbox (remove INBOX label)
            should_mark_read: Mark matching messages as read
            should_never_spam: Never send to spam

        Returns:
            The created filter resource.
        """
        action = {}
        if add_label_ids:
            action["addLabelIds"] = add_label_ids
        if remove_label_ids:
            action["removeLabelIds"] = remove_label_ids
        if should_archive:
            action["removeLabelIds"] = action.get("removeLabelIds", []) + ["INBOX"]
        if should_mark_read:
            # Removing UNREAD label marks as read
            action["removeLabelIds"] = action.get("removeLabelIds", []) + ["UNREAD"]
        if should_never_spam:
            action["addLabelIds"] = action.get("addLabelIds", []) + ["IMPORTANT"]
            # Gmail uses "neverSpam" in filter action, but the API represents it
            # by adding to "never spam" — handled via the action object
            # Note: the API doesn't have a direct "neverSpam" field in v1,
            # but we set IMPORTANT and remove SPAM as a workaround
            action["removeLabelIds"] = action.get("removeLabelIds", []) + ["SPAM"]

        self._maybe_refresh_token()
        self._limiter.acquire()
        body = {
            "criteria": criteria,
            "action": action,
        }

        return self._call_api(self.service.users().settings().filters().create(
            userId=self.user_id, body=body
        ))

    def list_filters(self) -> list[dict]:
        """List all existing Gmail filters."""
        self._maybe_refresh_token()
        self._limiter.acquire()
        result = self._call_api(self.service.users().settings().filters().list(
            userId=self.user_id
        ))
        return result.get("filter", [])

    def delete_filter(self, filter_id: str) -> None:
        """Delete a filter by ID."""
        self._maybe_refresh_token()
        self._limiter.acquire()
        self._call_api(self.service.users().settings().filters().delete(
            userId=self.user_id, id=filter_id
        ))

    # ─────────────────────────────────────────────
    # DRAFTS
    # ─────────────────────────────────────────────

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str | None = None,
        bcc: str | None = None,
        thread_id: str | None = None,
        in_reply_to: str | None = None,
        references: str | None = None,
    ) -> dict:
        """
        Create a draft email. Does NOT send — human reviews and sends.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            thread_id: Thread to attach the draft to (for replies)
            in_reply_to: Message-ID header for threading (for replies)
            references: References header for threading (for replies)

        Returns:
            The created draft resource (includes draft ID and message).
        """
        message = email.mime.text.MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if cc:
            message["cc"] = cc
        if bcc:
            message["bcc"] = bcc
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
        if references:
            message["References"] = references

        self._maybe_refresh_token()
        self._limiter.acquire()
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        draft_body: dict[str, Any] = {"message": {"raw": raw}}
        if thread_id:
            draft_body["message"]["threadId"] = thread_id

        return self._call_api(self.service.users().drafts().create(
            userId=self.user_id, body=draft_body
        ))

    def create_reply_draft(
        self,
        original_message: dict,
        body: str,
        reply_all: bool = False,
    ) -> dict:
        """
        Create a reply draft for an existing message.
        Handles threading headers automatically.

        Args:
            original_message: The message resource being replied to (from read_message)
            body: Plain text reply body
            reply_all: If True, includes all original recipients

        Returns:
            The created draft resource.
        """
        headers = self.get_message_headers(original_message)
        thread_id = original_message.get("threadId")

        # Build subject with Re: prefix if not already there
        subject = headers.get("subject", "")
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        # Get Message-ID for threading
        msg_id_header = None
        for h in original_message.get("payload", {}).get("headers", []):
            if h["name"].lower() == "message-id":
                msg_id_header = h["value"]
                break

        # Determine recipients
        to = headers.get("from", "")
        cc = None
        if reply_all:
            # Include original To and CC, excluding self
            all_recipients = []
            if headers.get("to"):
                all_recipients.append(headers["to"])
            if headers.get("cc"):
                all_recipients.append(headers["cc"])
            cc = ", ".join(all_recipients) if all_recipients else None

        return self.create_draft(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            thread_id=thread_id,
            in_reply_to=msg_id_header,
            references=msg_id_header,
        )

    def create_forward_draft(
        self,
        original_message: dict,
        to: str,
        note: str = "",
    ) -> dict:
        """
        Create a forward draft for an existing message.

        Args:
            original_message: The message resource to forward
            to: Recipient to forward to
            note: Optional note to prepend to the forwarded message

        Returns:
            The created draft resource.
        """
        headers = self.get_message_headers(original_message)
        original_body = self.get_message_body(original_message)
        thread_id = original_message.get("threadId")

        subject = headers.get("subject", "")
        if not subject.lower().startswith("fwd:"):
            subject = f"Fwd: {subject}"

        forward_body = ""
        if note:
            forward_body += f"{note}\n\n"
        forward_body += "---------- Forwarded message ----------\n"
        forward_body += f"From: {headers.get('from', 'Unknown')}\n"
        forward_body += f"Date: {headers.get('date', 'Unknown')}\n"
        forward_body += f"Subject: {headers.get('subject', 'No subject')}\n"
        forward_body += f"To: {headers.get('to', 'Unknown')}\n\n"
        forward_body += original_body

        return self.create_draft(
            to=to,
            subject=subject,
            body=forward_body,
            thread_id=thread_id,
        )

    def list_drafts(self, max_results: int = 100) -> list[dict]:
        """List all drafts."""
        self._maybe_refresh_token()
        self._limiter.acquire()
        result = self._call_api(self.service.users().drafts().list(
            userId=self.user_id, maxResults=max_results
        ))
        return result.get("drafts", [])

    # ─────────────────────────────────────────────
    # SENT MESSAGES (for voice extraction)
    # ─────────────────────────────────────────────

    def get_sent_messages(self, max_results: int = 30) -> list[dict]:
        """
        Retrieve recent sent messages (full format).
        Used by exec-voice-builder to extract writing patterns.

        Args:
            max_results: Number of sent messages to retrieve (default 30)

        Returns:
            List of full message resources from the sent folder.
        """
        self._maybe_refresh_token()
        result = self.search_messages("in:sent", max_results=max_results)
        messages = []
        for msg_stub in result["messages"]:
            full_msg = self.read_message(msg_stub["id"])
            messages.append(full_msg)
        return messages

    # ─────────────────────────────────────────────
    # SETTINGS
    # ─────────────────────────────────────────────

    def update_settings(self, settings: dict) -> dict:
        """
        Update Gmail auto-forwarding/IMAP/POP settings.
        Note: Most general settings (like Multiple Inboxes) are not directly
        available via the API — they require the Gmail Settings API or
        are configured through the Gmail UI. This method handles what the
        API supports.

        Args:
            settings: Settings dict (varies by endpoint)

        Returns:
            Updated settings.
        """
        # The Gmail API has limited settings support.
        # Auto-advance, multiple inboxes, etc. are Labs/Settings features
        # that aren't in the REST API. We'll handle these via the
        # configure_settings.py script which guides the user through
        # any manual steps needed.
        raise NotImplementedError(
            "Direct settings update is limited in the Gmail API. "
            "Use configure_settings.py for full configuration."
        )

    def get_profile(self) -> dict:
        """Get the authenticated user's Gmail profile (email, messages total, etc.)."""
        self._maybe_refresh_token()
        self._limiter.acquire()
        return self._call_api(self.service.users().getProfile(userId=self.user_id))

    # ─────────────────────────────────────────────
    # UTILITY METHODS
    # ─────────────────────────────────────────────

    def get_senders_with_count(
        self,
        query: str = "in:inbox",
        min_count: int = 5,
        max_messages: int = 1000,
    ) -> list[tuple[str, int]]:
        """
        Scan messages matching a query and return senders with >= min_count messages.
        Used during initial cleanup to identify bulk filter candidates.

        Args:
            query: Gmail search query to scope the scan
            min_count: Minimum messages from a sender to include
            max_messages: Max messages to scan

        Returns:
            List of (sender_email, count) tuples, sorted by count descending.
        """
        messages = self.search_all_messages(query, max_results=max_messages)

        sender_counts: dict[str, int] = {}
        for msg_stub in messages:
            msg = self.read_message(msg_stub["id"], format="metadata")
            headers = self.get_message_headers(msg)
            sender = headers.get("from", "unknown")
            # Extract just the email address from "Name <email>" format
            if "<" in sender and ">" in sender:
                sender = sender[sender.index("<") + 1 : sender.index(">")]
            sender = sender.lower().strip()
            sender_counts[sender] = sender_counts.get(sender, 0) + 1

        return sorted(
            [(s, c) for s, c in sender_counts.items() if c >= min_count],
            key=lambda x: x[1],
            reverse=True,
        )

    def thread_has_reply_from(self, thread_id: str, email_address: str) -> bool:
        """
        Check if a thread contains a reply from a specific email address.
        Used for label sweep (checking if exec replied, team member responded, etc.)

        Args:
            thread_id: The thread ID to check
            email_address: Email address to look for in replies

        Returns:
            True if the thread contains a message from that address.
        """
        thread = self.read_thread(thread_id, format="metadata")
        email_lower = email_address.lower()

        for msg in thread.get("messages", []):
            headers = self.get_message_headers(msg)
            sender = headers.get("from", "").lower()
            if email_lower in sender:
                return True

        return False
