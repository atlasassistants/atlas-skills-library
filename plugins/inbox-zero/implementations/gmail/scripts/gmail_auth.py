"""
Gmail OAuth2 Authentication Module
===================================
Handles token loading, refresh, and the initial browser-based consent flow.
Used by all atlas-inbox-zero scripts that need Gmail API access.

Usage:
    from gmail_auth import get_credentials

    creds = get_credentials()
    # creds is a google.oauth2.credentials.Credentials object ready to use
"""

import os
import sys
import json
import argparse
import webbrowser
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urlparse

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from runtime_paths import ensure_runtime_paths
from profile_paths import CLIENT_PROFILE_DIR

ensure_runtime_paths()

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# H3: Bound the token-refresh network call so a hung DNS / TCP connect can't
# indefinitely block a skill. 10s is deliberately short — refresh should be
# a single HTTP POST to oauth2.googleapis.com.
REFRESH_TIMEOUT_SEC = 10.0


class _BoundedTimeoutRequest(Request):
    """google-auth Request subclass that injects REFRESH_TIMEOUT_SEC as the
    default HTTP timeout. The parent __call__ honors whatever timeout kwarg
    is passed through."""

    def __call__(
        self,
        url,
        method="GET",
        body=None,
        headers=None,
        timeout=REFRESH_TIMEOUT_SEC,
        **kwargs,
    ):
        return super().__call__(
            url, method=method, body=body, headers=headers, timeout=timeout, **kwargs
        )


# Full Gmail access — needed to create labels, filters, modify messages, etc.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.settings.sharing",
    "https://www.googleapis.com/auth/gmail.labels",
]

# Default paths — relative to the runtime client profile (atlas-inbox-zero/client-profile/)
# Scripts can override these by passing paths to get_credentials()
_DEFAULT_CREDENTIALS_PATH = CLIENT_PROFILE_DIR / "credentials" / "credentials.json"
_DEFAULT_TOKEN_PATH = CLIENT_PROFILE_DIR / "credentials" / "token.json"
_DEFAULT_PENDING_AUTH_PATH = CLIENT_PROFILE_DIR / "credentials" / ".oauth-pending.json"


def get_credentials(
    credentials_path: str | Path | None = None,
    token_path: str | Path | None = None,
) -> Credentials:
    """
    Returns authenticated Gmail API credentials.

    Flow:
    1. If token.json exists and is valid → return it
    2. If token.json exists but is expired → refresh it
    3. If no token.json → run the browser-based OAuth consent flow

    Args:
        credentials_path: Path to credentials.json (OAuth app identity).
                          Defaults to client-profile/credentials/credentials.json
        token_path: Path to token.json (user's auth token).
                    Defaults to client-profile/credentials/token.json

    Returns:
        google.oauth2.credentials.Credentials ready for API calls.

    Raises:
        FileNotFoundError: If credentials.json doesn't exist (run setup first).
    """
    credentials_path = Path(credentials_path or _DEFAULT_CREDENTIALS_PATH)
    token_path = Path(token_path or _DEFAULT_TOKEN_PATH)

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {credentials_path}\n"
            "Run the onboarding wizard first: setup_credentials.py"
        )

    creds = None

    # Step 1: Try loading existing token
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except (json.JSONDecodeError, ValueError):
            # Corrupted token file — will re-auth below
            creds = None

    # Step 2: Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds, token_path)
            return creds
        except Exception:
            # Refresh failed — will re-auth below
            creds = None

    # Step 3: If we have valid creds, return them
    if creds and creds.valid:
        return creds

    # Step 4: Run the full OAuth consent flow
    creds = _run_auth_flow(credentials_path)
    _save_token(creds, token_path)
    return creds


def _run_auth_flow(credentials_path: Path) -> Credentials:
    """
    Runs the OAuth2 consent flow.
    Opens a browser for the user to log in and grant access.
    Falls back to printing the URL if the browser can't open.
    """
    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path), SCOPES
    )

    # Try browser-based flow first, fall back to console if no browser
    try:
        creds = flow.run_local_server(
            port=0,  # Use any available port
            open_browser=True,
            success_message=(
                "Authentication complete! You can close this tab and go back to your terminal."
            ),
        )
    except Exception:
        # Headless / remote environment — print URL for manual copy
        print("\n--- Gmail Authentication ---")
        print("Could not open a browser automatically.")
        print("Please open this URL in your browser to authorize:\n")
        auth_url, state = flow.authorization_url(prompt="consent")
        _save_pending_auth(flow, auth_url, state)
        print(f"  {auth_url}\n")
        print("After authorizing, paste either the full callback URL or just the code below:")
        auth_input = input("Authorization code: ").strip()
        _complete_manual_auth_flow(flow, auth_input)
        creds = flow.credentials

    return creds


def _normalize_auth_input(auth_input: str) -> tuple[str | None, str | None]:
    """Return ``(code, authorization_response)`` from manual auth input.

    Users sometimes paste:
    - the raw code only
    - the full redirected localhost URL
    - a code suffixed with HTML-escaped ``&amp;`` fragments from chat clients
    """
    cleaned = unescape((auth_input or "").strip())
    if not cleaned:
        raise ValueError("Empty authorization input.")

    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        parsed = urlparse(cleaned)
        code_values = parse_qs(parsed.query).get("code", [])
        if not code_values:
            raise ValueError("No `code` parameter found in the callback URL.")
        code = code_values[0].strip()
        return code, cleaned

    code = cleaned.split("&", 1)[0].strip()
    return code, None


def _complete_manual_auth_flow(flow: InstalledAppFlow, auth_input: str) -> None:
    """Complete the manual OAuth flow from a pasted code or callback URL."""
    code, authorization_response = _normalize_auth_input(auth_input)
    kwargs = {"code": code}
    if authorization_response:
        kwargs["authorization_response"] = authorization_response
    flow.fetch_token(**kwargs)


def _save_pending_auth(flow: InstalledAppFlow, auth_url: str, state: str | None) -> None:
    """Persist PKCE/state details so a later non-interactive token exchange can finish."""
    payload = {
        "auth_url": auth_url,
        "redirect_uri": flow.redirect_uri,
        "state": state,
        "code_verifier": flow.code_verifier,
    }
    _DEFAULT_PENDING_AUTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_DEFAULT_PENDING_AUTH_PATH, "w") as f:
        json.dump(payload, f)


def _clear_pending_auth() -> None:
    try:
        _DEFAULT_PENDING_AUTH_PATH.unlink(missing_ok=True)
    except Exception:
        pass


def _load_pending_flow(credentials_path: Path) -> InstalledAppFlow:
    if not _DEFAULT_PENDING_AUTH_PATH.exists():
        raise FileNotFoundError(
            f"Pending OAuth state not found at {_DEFAULT_PENDING_AUTH_PATH}. "
            "Start the manual auth flow again to generate a fresh approval URL."
        )
    with open(_DEFAULT_PENDING_AUTH_PATH) as f:
        payload = json.load(f)
    state = payload.get("state")
    redirect_uri = payload.get("redirect_uri")
    code_verifier = payload.get("code_verifier")
    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path),
        SCOPES,
        state=state,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
        autogenerate_code_verifier=False,
    )
    return flow


def _save_token(creds: Credentials, token_path: Path) -> None:
    """Save credentials to token.json for future use."""
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as f:
        f.write(creds.to_json())


def check_credentials_exist(
    credentials_path: str | Path | None = None,
) -> bool:
    """Check whether credentials.json exists (without attempting auth)."""
    path = Path(credentials_path or _DEFAULT_CREDENTIALS_PATH)
    return path.exists()


def check_token_exists(
    token_path: str | Path | None = None,
) -> bool:
    """Check whether token.json exists (user has authenticated before)."""
    path = Path(token_path or _DEFAULT_TOKEN_PATH)
    return path.exists()


def ensure_fresh(
    credentials_path: str | Path | None = None,
    token_path: str | Path | None = None,
) -> Credentials:
    """
    Get credentials, refreshing the token if it's within 5 minutes of expiry.
    Call this before long operations to prevent mid-operation auth failures.
    """
    creds = get_credentials(credentials_path, token_path)
    # Proactively refresh if expiring soon (within 5 minutes)
    if creds.expiry and creds.refresh_token:
        import datetime
        # creds.expiry is a naive UTC datetime per google.oauth2 contract;
        # promote to aware so subtraction with the aware now() works.
        expiry_aware = creds.expiry.replace(tzinfo=datetime.timezone.utc)
        remaining = (
            expiry_aware - datetime.datetime.now(datetime.timezone.utc)
        ).total_seconds()
        if remaining < 300:  # less than 5 minutes left
            try:
                creds.refresh(_make_refresh_request())
            except Exception as exc:
                _log_token_refresh_failure(exc)
                raise
            _token_path = Path(token_path or _DEFAULT_TOKEN_PATH)
            _save_token(creds, _token_path)
    return creds


def _log_token_refresh_failure(exc: Exception) -> None:
    """Emit a structured token_refresh_failed event. Never raises.

    structured_logger is a sibling module in shared/scripts; import it lazily
    to avoid module-import-time coupling for callers that import gmail_auth
    without shared/scripts on sys.path yet."""
    try:
        from structured_logger import get_logger
        get_logger().event(
            "token_refresh_failed",
            message=str(exc)[:500],
            error_type=type(exc).__name__,
        )
    except Exception:
        pass  # logger failure must never mask the original refresh error


def _make_refresh_request():
    """Build the transport Request used for token refresh. Uses
    _BoundedTimeoutRequest so a hung DNS / TCP connect can't block the skill."""
    return _BoundedTimeoutRequest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Atlas Inbox Zero Gmail authentication")
    parser.add_argument(
        "--auth-code",
        help="Complete the manual OAuth step with a pasted authorization code or callback URL.",
    )
    args = parser.parse_args()

    print("Testing Gmail authentication...")
    try:
        if args.auth_code:
            flow = _load_pending_flow(_DEFAULT_CREDENTIALS_PATH)
            _complete_manual_auth_flow(flow, args.auth_code)
            creds = flow.credentials
            _save_token(creds, _DEFAULT_TOKEN_PATH)
            _clear_pending_auth()
        else:
            creds = get_credentials()
        print(f"Authenticated successfully. Token valid: {creds.valid}")
    except FileNotFoundError as e:
        print(f"Setup needed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)
