from __future__ import annotations

import re
import socket
from datetime import date, datetime


def slugify(value: str, fallback: str = "item") -> str:
    cleaned = re.sub(r"https?://", "", value.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", cleaned).strip("_")
    return cleaned[:60] if cleaned else fallback


def report_basename(target: str, finding: str, found_on: date) -> str:
    target_slug = slugify(target, "target")
    finding_slug = slugify(finding, "temuan")
    return f"{target_slug}_{finding_slug}_{found_on.strftime('%Y%m%d')}"


def hostname() -> str:
    try:
        return socket.gethostname()
    except OSError:
        return "unknown-host"


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def format_datetime(value: datetime) -> str:
    return value.strftime("%d-%m-%Y %H:%M:%S")
