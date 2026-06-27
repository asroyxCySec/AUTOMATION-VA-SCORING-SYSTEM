from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, user_roles, utcnow
from app.models.role import ROLE_ADMINISTRATOR, Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    instansi: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    jabatan: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    photo_path: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    roles: Mapped[list[Role]] = relationship(
        secondary=user_roles, back_populates="users", lazy="selectin"
    )

    def permission_codes(self) -> set[str]:
        codes: set[str] = set()
        for role in self.roles:
            codes |= role.permission_codes()
        return codes

    def has_permission(self, code: str) -> bool:
        return code in self.permission_codes()

    def is_administrator(self) -> bool:
        return any(role.name == ROLE_ADMINISTRATOR for role in self.roles)

    @property
    def role_name(self) -> str:
        if self.is_administrator():
            return ROLE_ADMINISTRATOR
        if self.roles:
            return self.roles[0].name
        return "User"
