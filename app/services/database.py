from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app import config
from app.core.security import hash_password
from app.models import (
    ADMIN_PERMISSIONS,
    ROLE_ADMINISTRATOR,
    ROLE_USER,
    USER_PERMISSIONS,
    Base,
    Permission,
    Role,
    Setting,
    User,
)

DEFAULT_SETTINGS = {
    "institution_name": "Dinas Komunikasi, Informatika, dan Statistik",
    "institution_address": "",
    "institution_email": "",
    "institution_phone": "",
    "report_header": "VULNERABILITY ASSESSMENT REPORT",
    "report_footer": "Dokumen ini bersifat rahasia dan hanya untuk kebutuhan internal.",
    "report_logo_path": "",
    "app_theme": "dark",
    "app_language": "id",
}


class DatabaseService:
    def __init__(self, database_url: str | None = None) -> None:
        config.ensure_directories()
        self._url = database_url or config.DATABASE_URL
        connect_args = {"check_same_thread": False} if self._url.startswith("sqlite") else {}
        self._engine: Engine = create_engine(
            self._url, echo=False, future=True, connect_args=connect_args
        )
        if self._url.startswith("sqlite"):
            self._enable_sqlite_foreign_keys()
        self._session_factory = sessionmaker(
            bind=self._engine, expire_on_commit=False, class_=Session, future=True
        )
        self._local = threading.local()

    def _enable_sqlite_foreign_keys(self) -> None:
        @event.listens_for(self._engine, "connect")
        def _set_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

    @property
    def engine(self) -> Engine:
        return self._engine

    def create_schema(self) -> None:
        Base.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        existing = getattr(self._local, "session", None)
        if existing is not None:
            self._local.depth += 1
            try:
                yield existing
            finally:
                self._local.depth -= 1
            return

        session = self._session_factory()
        self._local.session = session
        self._local.depth = 1
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            self._local.session = None
            self._local.depth = 0

    def new_session(self) -> Session:
        return self._session_factory()

    def seed(self) -> None:
        with self.session() as session:
            self._seed_permissions(session)
            self._seed_roles(session)
            self._seed_admin(session)
            self._seed_settings(session)

    def _seed_permissions(self, session: Session) -> None:
        existing = {p.code for p in session.scalars(select(Permission)).all()}
        catalog = {code: desc for code, desc in (*ADMIN_PERMISSIONS, *USER_PERMISSIONS)}
        for code, description in catalog.items():
            if code not in existing:
                session.add(Permission(code=code, description=description))
        session.flush()

    def _seed_roles(self, session: Session) -> None:
        permissions = {p.code: p for p in session.scalars(select(Permission)).all()}

        admin = session.scalar(select(Role).where(Role.name == ROLE_ADMINISTRATOR))
        if admin is None:
            admin = Role(name=ROLE_ADMINISTRATOR, description="Akses penuh sistem")
            session.add(admin)
        admin.permissions = [permissions[code] for code, _ in ADMIN_PERMISSIONS]

        user_role = session.scalar(select(Role).where(Role.name == ROLE_USER))
        if user_role is None:
            user_role = Role(name=ROLE_USER, description="Akses penilaian milik sendiri")
            session.add(user_role)
        user_role.permissions = [permissions[code] for code, _ in USER_PERMISSIONS]
        session.flush()

    def _seed_admin(self, session: Session) -> None:
        existing = session.scalar(
            select(User).where(User.username == config.DEFAULT_ADMIN_USERNAME)
        )
        if existing is not None:
            return
        admin_role = session.scalar(select(Role).where(Role.name == ROLE_ADMINISTRATOR))
        admin = User(
            username=config.DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(config.DEFAULT_ADMIN_PASSWORD),
            full_name="Administrator",
            instansi=DEFAULT_SETTINGS["institution_name"],
            jabatan="System Administrator",
            is_active=True,
            must_change_password=True,
        )
        admin.roles.append(admin_role)
        session.add(admin)
        session.flush()

    def _seed_settings(self, session: Session) -> None:
        existing = {s.key for s in session.scalars(select(Setting)).all()}
        for key, value in DEFAULT_SETTINGS.items():
            if key not in existing:
                session.add(Setting(key=key, value=value))
        session.flush()

    def initialize(self) -> None:
        self.create_schema()
        self.seed()
