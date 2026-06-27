from __future__ import annotations

import re

import bcrypt

_MIN_PASSWORD_LENGTH = 8


def hash_password(plaintext: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    digest = bcrypt.hashpw(plaintext.encode("utf-8"), salt)
    return digest.decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def password_strength_error(plaintext: str) -> str | None:
    if len(plaintext) < _MIN_PASSWORD_LENGTH:
        return f"Password minimal {_MIN_PASSWORD_LENGTH} karakter."
    if not re.search(r"[A-Z]", plaintext):
        return "Password harus memuat minimal satu huruf kapital."
    if not re.search(r"[a-z]", plaintext):
        return "Password harus memuat minimal satu huruf kecil."
    if not re.search(r"[0-9]", plaintext):
        return "Password harus memuat minimal satu angka."
    return None
