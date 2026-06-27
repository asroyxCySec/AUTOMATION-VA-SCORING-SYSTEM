from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    hostname: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SUCCESS")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False, index=True)


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")


class BackupHistory(Base):
    __tablename__ = "backup_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    file_path: Mapped[str] = mapped_column(String(400), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    action: Mapped[str] = mapped_column(String(20), nullable=False, default="BACKUP")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
