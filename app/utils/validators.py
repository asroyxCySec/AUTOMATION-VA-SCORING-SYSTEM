from __future__ import annotations

import re
from datetime import date, datetime

_URL_PATTERN = re.compile(
    r"^(https?://)"
    r"([A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)+|localhost|(\d{1,3}\.){3}\d{1,3})"
    r"(:\d{1,5})?"
    r"(/[^\s]*)?$",
    re.IGNORECASE,
)

_HOST_PATTERN = re.compile(
    r"^([A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)+|localhost|(\d{1,3}\.){3}\d{1,3})(:\d{1,5})?(/[^\s]*)?$",
    re.IGNORECASE,
)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CVE_PATTERN = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)
_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,32}$")
_PHONE_PATTERN = re.compile(r"^[+0-9][0-9\s-]{6,19}$")


def is_valid_target(value: str) -> bool:
    candidate = value.strip()
    if not candidate:
        return False
    if _URL_PATTERN.match(candidate):
        return True
    return bool(_HOST_PATTERN.match(candidate))


def is_valid_email(value: str) -> bool:
    return bool(_EMAIL_PATTERN.match(value.strip()))


def is_valid_cve(value: str) -> bool:
    return bool(_CVE_PATTERN.match(value.strip()))


def is_valid_username(value: str) -> bool:
    return bool(_USERNAME_PATTERN.match(value.strip()))


def is_valid_phone(value: str) -> bool:
    if not value.strip():
        return True
    return bool(_PHONE_PATTERN.match(value.strip()))


def parse_date(value: str) -> date | None:
    candidate = value.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    return None


def is_not_empty(value: str) -> bool:
    return bool(value and value.strip())
