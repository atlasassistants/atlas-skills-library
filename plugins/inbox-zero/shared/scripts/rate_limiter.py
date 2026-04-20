# atlas-inbox-zero/shared/scripts/rate_limiter.py
"""
Rate Limiter + Retry Logic
===========================
Throttles Gmail API calls to stay under quota (250 units/second)
and retries transient errors (429, 5xx) with exponential backoff.

Usage — as a decorator:
    @retry_on_api_error(max_retries=3, base_delay=1.0)
    def my_api_call():
        return service.users().messages().get(...).execute()

Usage — as a rate limiter:
    limiter = RateLimiter(max_calls_per_second=200)
    limiter.acquire()  # blocks if at limit
    response = api_call()
"""

import functools
import random
import time
from collections import deque
from typing import Callable, TypeVar

T = TypeVar("T")

# Retryable HTTP status codes
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


class RateLimitExceeded(Exception):
    """Raised when the rate limiter can't acquire within the timeout."""
    pass


class RateLimiter:
    """
    Sliding-window rate limiter.

    Tracks API calls within a 1-second window and blocks (via sleep)
    when the window is full. Does NOT raise — it waits.
    """

    def __init__(self, max_calls_per_second: int = 200):
        self.max_calls = max_calls_per_second
        self._timestamps: deque[float] = deque()
        self.total_calls = 0

    @property
    def calls_in_current_window(self) -> int:
        self._prune_old()
        return len(self._timestamps)

    def _prune_old(self) -> None:
        now = time.monotonic()
        while self._timestamps and (now - self._timestamps[0]) > 1.0:
            self._timestamps.popleft()

    def acquire(self, timeout: float = 30.0) -> None:
        """
        Wait until a call slot is available, then claim it.

        Args:
            timeout: Max seconds to wait before raising RateLimitExceeded.
        """
        deadline = time.monotonic() + timeout

        while True:
            self._prune_old()
            if len(self._timestamps) < self.max_calls:
                self._timestamps.append(time.monotonic())
                self.total_calls += 1
                return

            if time.monotonic() >= deadline:
                raise RateLimitExceeded(
                    f"Rate limiter: still at {self.max_calls}/s after {timeout}s wait"
                )

            # Sleep until the oldest call exits the window. max(0.0, ...)
            # collapses the prior `if sleep_time > 0` guard into one line and
            # also defends against pathological cases where _timestamps[0]
            # is in the future (clock fiddle, monkey-patched test state) —
            # time.sleep() raises ValueError on negative input. (L2)
            sleep_time = 1.0 - (time.monotonic() - self._timestamps[0])
            time.sleep(max(0.0, min(sleep_time + 0.01, 0.5)))


# Module-level default limiter (shared across all scripts in a session)
_default_limiter = RateLimiter(max_calls_per_second=200)


def get_default_limiter() -> RateLimiter:
    return _default_limiter


def retry_on_api_error(
    max_retries: int = 3,
    base_delay: float = 1.0,
    limiter: RateLimiter | None = None,
) -> Callable:
    """
    Decorator that retries on transient Gmail API errors (429, 5xx)
    with exponential backoff and jitter.

    Does NOT retry on 4xx client errors (except 429) — those are
    permanent failures where retrying won't help.

    Args:
        max_retries: Maximum retry attempts after the initial call.
        base_delay: Base delay in seconds (doubles each retry + jitter).
        limiter: Optional RateLimiter to acquire before each attempt.
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            _limiter = limiter or _default_limiter
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    _limiter.acquire()
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last_error = exc

                    # Check if it's an HttpError with a retryable status
                    status = _get_http_status(exc)
                    if status is None or status not in _RETRYABLE_STATUSES:
                        # Not retryable — raise immediately
                        raise

                    if attempt == max_retries:
                        raise

                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    time.sleep(delay)

            raise last_error  # should never reach here, but just in case

        return wrapper
    return decorator


def _get_http_status(exc: Exception) -> int | None:
    """Extract HTTP status code from a googleapiclient.errors.HttpError."""
    # Check for googleapiclient HttpError
    if hasattr(exc, "resp") and hasattr(exc.resp, "status"):
        try:
            return int(exc.resp.status)
        except (ValueError, TypeError):
            return None
    # Check for status attribute directly
    if hasattr(exc, "status_code"):
        try:
            return int(exc.status_code)
        except (ValueError, TypeError):
            return None
    return None
