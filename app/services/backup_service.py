from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import desc, select

from app import config
from app.models import BackupHistory
from app.services.audit_service import AuditContext, AuditService
from app.services.database import DatabaseService
from app.utils.helpers import now_stamp


@dataclass(frozen=True)
class BackupResult:
    success: bool
    message: str = ""
    path: str = ""


@dataclass(frozen=True)
class BackupRow:
    id: int
    file_path: str
    size_bytes: int
    action: str
    created_at: datetime


class BackupService:
    def __init__(self, database: DatabaseService, audit: AuditService) -> None:
        self._database = database
        self._audit = audit

    def _source_file(self) -> Path:
        return config.database_file()

    def create_backup(self, actor: AuditContext, destination: str | None = None) -> BackupResult:
        source = self._source_file()
        if not source.exists():
            return BackupResult(False, "Berkas database tidak ditemukan.")
        if destination:
            target = Path(destination)
        else:
            config.ensure_directories()
            target = config.BACKUP_DIR / f"vulnscore_backup_{now_stamp()}.db"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        except OSError as error:
            return BackupResult(False, f"Gagal membuat backup: {error}")
        size = target.stat().st_size
        with self._database.session() as session:
            session.add(
                BackupHistory(
                    user_id=actor.user_id,
                    file_path=str(target),
                    size_bytes=size,
                    action="BACKUP",
                )
            )
        self._audit.record(actor, "BACKUP_DATABASE", f"Backup ke {target.name} ({size} byte).")
        return BackupResult(True, "Backup berhasil dibuat.", path=str(target))

    def restore_backup(self, actor: AuditContext, source_path: str) -> BackupResult:
        source = Path(source_path)
        if not source.exists():
            return BackupResult(False, "Berkas backup tidak ditemukan.")
        target = self._source_file()
        safety_copy = config.BACKUP_DIR / f"pre_restore_{now_stamp()}.db"
        try:
            config.ensure_directories()
            self._database.engine.dispose()
            if target.exists():
                shutil.copy2(target, safety_copy)
            shutil.copy2(source, target)
        except OSError as error:
            return BackupResult(False, f"Gagal restore: {error}")
        size = source.stat().st_size
        with self._database.session() as session:
            session.add(
                BackupHistory(
                    user_id=actor.user_id,
                    file_path=str(source),
                    size_bytes=size,
                    action="RESTORE",
                )
            )
        self._audit.record(actor, "RESTORE_DATABASE", f"Restore dari {source.name}.")
        return BackupResult(True, "Restore berhasil. Disarankan untuk restart aplikasi.", path=str(target))

    def history(self, limit: int = 50) -> list[BackupRow]:
        with self._database.session() as session:
            stmt = select(BackupHistory).order_by(desc(BackupHistory.created_at)).limit(limit)
            return [
                BackupRow(
                    id=row.id,
                    file_path=row.file_path,
                    size_bytes=row.size_bytes,
                    action=row.action,
                    created_at=row.created_at,
                )
                for row in session.scalars(stmt).all()
            ]
