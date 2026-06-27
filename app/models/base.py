from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table
from sqlalchemy.orm import DeclarativeBase


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)
