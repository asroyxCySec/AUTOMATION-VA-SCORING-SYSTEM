from __future__ import annotations

import time

from app import config


class SessionManager:
    def __init__(self, idle_timeout_seconds: int | None = None) -> None:
        self._timeout = idle_timeout_seconds or config.SESSION_IDLE_TIMEOUT_SECONDS
        self._last_activity: float | None = None
        self._active = False

    def start(self) -> None:
        self._active = True
        self._last_activity = time.monotonic()

    def stop(self) -> None:
        self._active = False
        self._last_activity = None

    def touch(self) -> None:
        if self._active:
            self._last_activity = time.monotonic()

    @property
    def active(self) -> bool:
        return self._active

    def remaining_seconds(self) -> int:
        if not self._active or self._last_activity is None:
            return self._timeout
        elapsed = time.monotonic() - self._last_activity
        return max(0, int(self._timeout - elapsed))

    def is_expired(self) -> bool:
        if not self._active or self._last_activity is None:
            return False
        return (time.monotonic() - self._last_activity) >= self._timeout
