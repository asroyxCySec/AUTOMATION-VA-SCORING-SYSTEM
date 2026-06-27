from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.models import Setting
from app.services.audit_service import AuditContext, AuditService
from app.services.database import DatabaseService


@dataclass(frozen=True)
class AppSettings:
    institution_name: str
    institution_address: str
    institution_email: str
    institution_phone: str
    report_header: str
    report_footer: str
    report_logo_path: str
    app_theme: str
    app_language: str


class SettingsService:
    def __init__(self, database: DatabaseService, audit: AuditService) -> None:
        self._database = database
        self._audit = audit

    def load(self) -> AppSettings:
        with self._database.session() as session:
            data = {s.key: s.value for s in session.scalars(select(Setting)).all()}
        return AppSettings(
            institution_name=data.get("institution_name", ""),
            institution_address=data.get("institution_address", ""),
            institution_email=data.get("institution_email", ""),
            institution_phone=data.get("institution_phone", ""),
            report_header=data.get("report_header", "VULNERABILITY ASSESSMENT REPORT"),
            report_footer=data.get("report_footer", ""),
            report_logo_path=data.get("report_logo_path", ""),
            app_theme=data.get("app_theme", "dark"),
            app_language=data.get("app_language", "id"),
        )

    def save(self, actor: AuditContext, values: dict[str, str]) -> None:
        with self._database.session() as session:
            existing = {s.key: s for s in session.scalars(select(Setting)).all()}
            for key, value in values.items():
                if key in existing:
                    existing[key].value = value
                else:
                    session.add(Setting(key=key, value=value))
            self._audit.record(actor, "UPDATE_SETTINGS", "Memperbarui pengaturan aplikasi.")

    def get(self, key: str, default: str = "") -> str:
        with self._database.session() as session:
            setting = session.scalar(select(Setting).where(Setting.key == key))
            return setting.value if setting else default
