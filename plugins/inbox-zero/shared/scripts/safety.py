"""
Plugin Safety
=============
Safety mechanisms that prevent the plugin from performing dangerous operations.

- PluginSafetyError: custom exception for greppability
- block_send_on_service: monkey-patches the Gmail API service object to
  raise on any send() call
"""

class PluginSafetyError(RuntimeError):
    """Raised when the plugin attempts a blocked operation (e.g., sending email)."""
    pass


def _raise_on_send(*args, **kwargs):
    """Replacement for users().messages().send() that always raises."""
    raise PluginSafetyError(
        "Atlas Inbox Zero does NOT send emails. "
        "This is a draft-only plugin. If you see this error, "
        "a code path attempted to call send(). This is a bug."
    )


def block_send_on_service(service) -> None:
    """
    Monkey-patch a Gmail API service object so that
    users().messages().send() raises PluginSafetyError.

    Call this immediately after building the service in GmailClient.__init__.

    The patch is applied at the ``service.users`` level so it survives
    across multiple ``service.users()`` calls — real
    ``googleapiclient.discovery.Resource`` objects return a *new* child
    Resource on every call, so patching a single ``users()`` return value
    would be ephemeral.
    """
    original_users = service.users

    class _BlockedSendRequest:
        def execute(self):
            _raise_on_send()

    def _blocked_send(**kwargs):
        return _BlockedSendRequest()

    class SafeMessages:
        """Wrapper that intercepts send() and delegates everything else."""

        def __init__(self, real_messages_fn):
            self._real = real_messages_fn

        def __call__(self):
            real_obj = self._real()
            real_obj.send = _blocked_send
            return real_obj

    def patched_users():
        users_resource = original_users()
        original_messages = users_resource.messages
        users_resource.messages = SafeMessages(original_messages)
        return users_resource

    service.users = patched_users
