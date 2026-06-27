from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, or_, select

from app.core.security import hash_password, password_strength_error
from app.models import ROLE_ADMINISTRATOR, ROLE_USER, Role, User
from app.services.audit_service import AuditContext, AuditService
from app.services.database import DatabaseService
from app.utils.validators import is_valid_email, is_valid_phone, is_valid_username


@dataclass(frozen=True)
class UserRow:
    id: int
    username: str
    full_name: str
    email: str
    phone: str
    instansi: str
    jabatan: str
    role_name: str
    is_active: bool
    photo_path: str
    created_at: datetime
    last_login_at: datetime | None


@dataclass(frozen=True)
class ServiceResult:
    success: bool
    message: str = ""
    user_id: int | None = None


class UserService:
    def __init__(self, database: DatabaseService, audit: AuditService) -> None:
        self._database = database
        self._audit = audit

    @staticmethod
    def _to_row(user: User) -> UserRow:
        return UserRow(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            instansi=user.instansi,
            jabatan=user.jabatan,
            role_name=user.role_name,
            is_active=user.is_active,
            photo_path=user.photo_path,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )

    def get_row(self, user_id: int) -> UserRow | None:
        with self._database.session() as session:
            user = session.get(User, user_id)
            return self._to_row(user) if user else None

    def list_users(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str = "",
        role: str | None = None,
        active: bool | None = None,
    ) -> tuple[list[UserRow], int]:
        with self._database.session() as session:
            stmt = select(User)
            count_stmt = select(func.count(func.distinct(User.id))).select_from(User)
            search = search.strip()
            if search:
                pattern = f"%{search}%"
                clause = or_(
                    User.username.like(pattern),
                    User.full_name.like(pattern),
                    User.email.like(pattern),
                )
                stmt = stmt.where(clause)
                count_stmt = count_stmt.where(clause)
            if role:
                stmt = stmt.join(User.roles).where(Role.name == role)
                count_stmt = count_stmt.join(User.roles).where(Role.name == role)
            if active is not None:
                stmt = stmt.where(User.is_active.is_(active))
                count_stmt = count_stmt.where(User.is_active.is_(active))
            total = session.scalar(count_stmt) or 0
            offset = max(page - 1, 0) * page_size
            stmt = stmt.order_by(User.id).offset(offset).limit(page_size)
            rows = [self._to_row(user) for user in session.scalars(stmt).unique().all()]
            return rows, total

    def create_user(
        self,
        actor: AuditContext,
        username: str,
        password: str,
        full_name: str,
        email: str,
        phone: str,
        instansi: str,
        jabatan: str,
        role_name: str,
    ) -> ServiceResult:
        username = username.strip()
        if not is_valid_username(username):
            return ServiceResult(False, "Username 3-32 karakter alfanumerik, titik, strip, atau garis bawah.")
        if email and not is_valid_email(email):
            return ServiceResult(False, "Format email tidak valid.")
        if phone and not is_valid_phone(phone):
            return ServiceResult(False, "Format nomor HP tidak valid.")
        strength = password_strength_error(password)
        if strength:
            return ServiceResult(False, strength)
        if role_name not in (ROLE_ADMINISTRATOR, ROLE_USER):
            return ServiceResult(False, "Role tidak valid.")

        with self._database.session() as session:
            exists = session.scalar(select(User).where(User.username == username))
            if exists is not None:
                return ServiceResult(False, "Username sudah digunakan.")
            role = session.scalar(select(Role).where(Role.name == role_name))
            user = User(
                username=username,
                password_hash=hash_password(password),
                full_name=full_name.strip(),
                email=email.strip(),
                phone=phone.strip(),
                instansi=instansi.strip(),
                jabatan=jabatan.strip(),
                is_active=True,
                must_change_password=True,
            )
            user.roles.append(role)
            session.add(user)
            session.flush()
            user_id = user.id
            self._audit.record(actor, "CREATE_USER", f"Membuat user {username} ({role_name}).")
            return ServiceResult(True, "User berhasil dibuat.", user_id=user_id)

    def update_profile(
        self,
        actor: AuditContext,
        user_id: int,
        full_name: str,
        email: str,
        phone: str,
        instansi: str,
        jabatan: str,
    ) -> ServiceResult:
        if email and not is_valid_email(email):
            return ServiceResult(False, "Format email tidak valid.")
        if phone and not is_valid_phone(phone):
            return ServiceResult(False, "Format nomor HP tidak valid.")
        with self._database.session() as session:
            user = session.get(User, user_id)
            if user is None:
                return ServiceResult(False, "Pengguna tidak ditemukan.")
            user.full_name = full_name.strip()
            user.email = email.strip()
            user.phone = phone.strip()
            user.instansi = instansi.strip()
            user.jabatan = jabatan.strip()
            self._audit.record(actor, "UPDATE_PROFILE", f"Memperbarui profil {user.username}.")
            return ServiceResult(True, "Profil berhasil diperbarui.")

    def set_photo(self, actor: AuditContext, user_id: int, photo_path: str) -> ServiceResult:
        with self._database.session() as session:
            user = session.get(User, user_id)
            if user is None:
                return ServiceResult(False, "Pengguna tidak ditemukan.")
            user.photo_path = photo_path
            self._audit.record(actor, "UPLOAD_PHOTO", f"Memperbarui foto {user.username}.")
            return ServiceResult(True, "Foto profil diperbarui.")

    def reset_password(self, actor: AuditContext, user_id: int, new_password: str) -> ServiceResult:
        strength = password_strength_error(new_password)
        if strength:
            return ServiceResult(False, strength)
        with self._database.session() as session:
            user = session.get(User, user_id)
            if user is None:
                return ServiceResult(False, "Pengguna tidak ditemukan.")
            user.password_hash = hash_password(new_password)
            user.must_change_password = True
            user.failed_login_count = 0
            user.locked_until = None
            self._audit.record(actor, "RESET_PASSWORD", f"Reset password {user.username}.")
            return ServiceResult(True, "Password berhasil direset.")

    def set_active(self, actor: AuditContext, user_id: int, active: bool) -> ServiceResult:
        with self._database.session() as session:
            user = session.get(User, user_id)
            if user is None:
                return ServiceResult(False, "Pengguna tidak ditemukan.")
            if not active and user.is_administrator() and self._last_active_admin(session, user.id):
                return ServiceResult(False, "Tidak dapat menonaktifkan administrator aktif terakhir.")
            user.is_active = active
            label = "mengaktifkan" if active else "menonaktifkan"
            self._audit.record(actor, "SET_USER_STATUS", f"{label.capitalize()} {user.username}.")
            return ServiceResult(True, f"User berhasil {'diaktifkan' if active else 'dinonaktifkan'}.")

    def change_role(self, actor: AuditContext, user_id: int, role_name: str) -> ServiceResult:
        if role_name not in (ROLE_ADMINISTRATOR, ROLE_USER):
            return ServiceResult(False, "Role tidak valid.")
        with self._database.session() as session:
            user = session.get(User, user_id)
            if user is None:
                return ServiceResult(False, "Pengguna tidak ditemukan.")
            if (
                role_name == ROLE_USER
                and user.is_administrator()
                and self._last_active_admin(session, user.id)
            ):
                return ServiceResult(False, "Tidak dapat menurunkan administrator aktif terakhir.")
            role = session.scalar(select(Role).where(Role.name == role_name))
            user.roles = [role]
            self._audit.record(actor, "CHANGE_ROLE", f"Mengubah role {user.username} menjadi {role_name}.")
            return ServiceResult(True, "Role berhasil diubah.")

    def delete_user(self, actor: AuditContext, user_id: int) -> ServiceResult:
        with self._database.session() as session:
            user = session.get(User, user_id)
            if user is None:
                return ServiceResult(False, "Pengguna tidak ditemukan.")
            if user.is_administrator() and self._last_active_admin(session, user.id):
                return ServiceResult(False, "Tidak dapat menghapus administrator aktif terakhir.")
            username = user.username
            session.delete(user)
            self._audit.record(actor, "DELETE_USER", f"Menghapus user {username}.")
            return ServiceResult(True, "User berhasil dihapus.")

    @staticmethod
    def _last_active_admin(session, user_id: int) -> bool:
        admin_role = session.scalar(select(Role).where(Role.name == ROLE_ADMINISTRATOR))
        if admin_role is None:
            return False
        active_admins = [u for u in admin_role.users if u.is_active and u.id != user_id]
        return len(active_admins) == 0

    def count_by_role(self) -> dict[str, int]:
        with self._database.session() as session:
            result: dict[str, int] = {}
            for role in session.scalars(select(Role)).all():
                result[role.name] = len([u for u in role.users])
            return result
