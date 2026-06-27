from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, role_permissions, utcnow
from sqlalchemy import DateTime


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    roles: Mapped[list["Role"]] = relationship(
        secondary=role_permissions, back_populates="permissions"
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permissions, back_populates="roles", lazy="selectin"
    )
    users: Mapped[list["User"]] = relationship(
        secondary="user_roles", back_populates="roles"
    )

    def permission_codes(self) -> set[str]:
        return {permission.code for permission in self.permissions}


ROLE_ADMINISTRATOR = "Administrator"
ROLE_USER = "User"


class Perm:
    VIEW_DASHBOARD = "view_dashboard"
    CREATE_ASSESSMENT = "create_assessment"
    EDIT_OWN_ASSESSMENT = "edit_own_assessment"
    EDIT_ANY_ASSESSMENT = "edit_any_assessment"
    DELETE_ASSESSMENT = "delete_assessment"
    VIEW_OWN_ASSESSMENT = "view_own_assessment"
    VIEW_ANY_ASSESSMENT = "view_any_assessment"
    EXPORT_REPORT = "export_report"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_BACKUP = "manage_backup"
    MANAGE_SETTINGS = "manage_settings"
    CHANGE_OWN_PASSWORD = "change_own_password"


ADMIN_PERMISSIONS = (
    (Perm.VIEW_DASHBOARD, "Melihat dashboard"),
    (Perm.CREATE_ASSESSMENT, "Membuat penilaian kerentanan"),
    (Perm.EDIT_OWN_ASSESSMENT, "Mengedit penilaian sendiri"),
    (Perm.EDIT_ANY_ASSESSMENT, "Mengedit seluruh penilaian"),
    (Perm.DELETE_ASSESSMENT, "Menghapus penilaian"),
    (Perm.VIEW_OWN_ASSESSMENT, "Melihat penilaian sendiri"),
    (Perm.VIEW_ANY_ASSESSMENT, "Melihat seluruh laporan"),
    (Perm.EXPORT_REPORT, "Export DOCX dan PDF"),
    (Perm.MANAGE_USERS, "Manajemen pengguna"),
    (Perm.VIEW_AUDIT_LOG, "Melihat audit log"),
    (Perm.MANAGE_BACKUP, "Backup dan restore database"),
    (Perm.MANAGE_SETTINGS, "Mengubah pengaturan aplikasi"),
    (Perm.CHANGE_OWN_PASSWORD, "Mengubah password sendiri"),
)

USER_PERMISSIONS = (
    (Perm.VIEW_DASHBOARD, "Melihat dashboard"),
    (Perm.CREATE_ASSESSMENT, "Membuat penilaian"),
    (Perm.EDIT_OWN_ASSESSMENT, "Mengedit penilaian sendiri"),
    (Perm.VIEW_OWN_ASSESSMENT, "Melihat penilaian sendiri"),
    (Perm.EXPORT_REPORT, "Export laporan sendiri"),
    (Perm.CHANGE_OWN_PASSWORD, "Mengubah password sendiri"),
)
