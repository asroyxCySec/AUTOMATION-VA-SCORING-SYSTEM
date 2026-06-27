from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app import config
from app.core.security import hash_password, password_strength_error, verify_password
from app.models import User
from app.services.audit_service import AuditContext, AuditService
from app.services.database import DatabaseService


@dataclass(frozen=True)
class Principal:
    id: int
    username: str
    full_name: str
    role_name: str
    permissions: frozenset[str]
    must_change_password: bool
    is_administrator: bool

    def can(self, permission: str) -> bool:
        return permission in self.permissions

    def audit_context(self) -> AuditContext:
        return AuditContext(user_id=self.id, username=self.username, role=self.role_name)


@dataclass(frozen=True)
class AuthResult:
    success: bool
    principal: Principal | None = None
    message: str = ""
    locked: bool = False
    must_change_password: bool = False


class AuthService:
    def __init__(self, database: DatabaseService, audit: AuditService) -> None:
        self._database = database
        self._audit = audit

    @staticmethod
    def _to_principal(user: User) -> Principal:
        return Principal(
            id=user.id,
            username=user.username,
            full_name=user.full_name or user.username,
            role_name=user.role_name,
            permissions=frozenset(user.permission_codes()),
            must_change_password=user.must_change_password,
            is_administrator=user.is_administrator(),
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _as_aware(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def authenticate(self, username: str, password: str) -> AuthResult:
        username = username.strip()
        if not username or not password:
            return AuthResult(False, message="Username dan password wajib diisi.")

        with self._database.session() as session:
            user = session.scalar(select(User).where(User.username == username))
            now = self._now()

            if user is None:
                self._audit.record(
                    AuditContext(None, username, ""),
                    "LOGIN_FAILED",
                    "Username tidak ditemukan.",
                    status="FAILED",
                )
                return AuthResult(False, message="Username atau password salah.")

            locked_until = self._as_aware(user.locked_until)
            if locked_until and locked_until > now:
                remaining = int((locked_until - now).total_seconds() // 60) + 1
                self._audit.record(
                    AuditContext(user.id, user.username, user.role_name),
                    "LOGIN_FAILED",
                    "Akun terkunci.",
                    status="LOCKED",
                )
                return AuthResult(
                    False,
                    locked=True,
                    message=f"Akun terkunci. Coba lagi dalam {remaining} menit.",
                )

            if not user.is_active:
                self._audit.record(
                    AuditContext(user.id, user.username, user.role_name),
                    "LOGIN_FAILED",
                    "Akun nonaktif.",
                    status="FAILED",
                )
                return AuthResult(False, message="Akun Anda dinonaktifkan. Hubungi administrator.")

            if not verify_password(password, user.password_hash):
                user.failed_login_count += 1
                status = "FAILED"
                message = "Username atau password salah."
                locked = False
                if user.failed_login_count >= config.MAX_FAILED_LOGINS:
                    user.locked_until = now + timedelta(seconds=config.LOCKOUT_DURATION_SECONDS)
                    user.failed_login_count = 0
                    locked = True
                    status = "LOCKED"
                    message = (
                        f"Terlalu banyak percobaan gagal. Akun dikunci selama "
                        f"{config.LOCKOUT_DURATION_SECONDS // 60} menit."
                    )
                    self._audit.record(
                        AuditContext(user.id, user.username, user.role_name),
                        "ACCOUNT_LOCKED",
                        "Akun dikunci karena brute force.",
                        status="LOCKED",
                    )
                else:
                    self._audit.record(
                        AuditContext(user.id, user.username, user.role_name),
                        "LOGIN_FAILED",
                        f"Password salah ({user.failed_login_count}/{config.MAX_FAILED_LOGINS}).",
                        status=status,
                    )
                return AuthResult(False, locked=locked, message=message)

            user.failed_login_count = 0
            user.locked_until = None
            user.last_login_at = now
            principal = self._to_principal(user)
            self._audit.record(
                AuditContext(user.id, user.username, user.role_name),
                "LOGIN",
                "Login berhasil.",
            )
            return AuthResult(
                True,
                principal=principal,
                must_change_password=user.must_change_password,
            )

    def change_password(
        self, user_id: int, current_password: str, new_password: str, confirm_password: str
    ) -> AuthResult:
        if new_password != confirm_password:
            return AuthResult(False, message="Konfirmasi password tidak cocok.")
        strength = password_strength_error(new_password)
        if strength:
            return AuthResult(False, message=strength)

        with self._database.session() as session:
            user = session.get(User, user_id)
            if user is None:
                return AuthResult(False, message="Pengguna tidak ditemukan.")
            if not verify_password(current_password, user.password_hash):
                self._audit.record(
                    AuditContext(user.id, user.username, user.role_name),
                    "CHANGE_PASSWORD",
                    "Password lama salah.",
                    status="FAILED",
                )
                return AuthResult(False, message="Password lama salah.")
            if verify_password(new_password, user.password_hash):
                return AuthResult(False, message="Password baru tidak boleh sama dengan password lama.")
            user.password_hash = hash_password(new_password)
            user.must_change_password = False
            principal = self._to_principal(user)
            self._audit.record(
                AuditContext(user.id, user.username, user.role_name),
                "CHANGE_PASSWORD",
                "Password berhasil diubah.",
            )
            return AuthResult(True, principal=principal, message="Password berhasil diubah.")

    def logout(self, principal: Principal) -> None:
        self._audit.record(principal.audit_context(), "LOGOUT", "Logout berhasil.")
