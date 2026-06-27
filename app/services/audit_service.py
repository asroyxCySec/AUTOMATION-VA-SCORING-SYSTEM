from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import desc, func, select

from app.models import AuditLog, User
from app.services.database import DatabaseService
from app.utils.helpers import hostname, local_ip


@dataclass(frozen=True)
class AuditContext:
    user_id: int | None
    username: str
    role: str


class AuditService:
    def __init__(self, database: DatabaseService) -> None:
        self._database = database

    def record(
        self,
        context: AuditContext | None,
        action: str,
        detail: str = "",
        status: str = "SUCCESS",
    ) -> None:
        entry = AuditLog(
            user_id=context.user_id if context else None,
            username=context.username if context else "anonymous",
            role=context.role if context else "",
            ip_address=local_ip(),
            hostname=hostname(),
            action=action,
            detail=detail,
            status=status,
        )
        with self._database.session() as session:
            session.add(entry)

    def list_logs(
        self,
        page: int = 1,
        page_size: int = 25,
        username: str | None = None,
        action: str | None = None,
        status: str | None = None,
    ) -> tuple[list[AuditLog], int]:
        with self._database.session() as session:
            stmt = select(AuditLog)
            count_stmt = select(func.count()).select_from(AuditLog)
            if username:
                stmt = stmt.where(AuditLog.username == username)
                count_stmt = count_stmt.where(AuditLog.username == username)
            if action:
                stmt = stmt.where(AuditLog.action == action)
                count_stmt = count_stmt.where(AuditLog.action == action)
            if status:
                stmt = stmt.where(AuditLog.status == status)
                count_stmt = count_stmt.where(AuditLog.status == status)
            total = session.scalar(count_stmt) or 0
            offset = max(page - 1, 0) * page_size
            stmt = stmt.order_by(desc(AuditLog.created_at)).offset(offset).limit(page_size)
            rows = list(session.scalars(stmt).all())
            for row in rows:
                session.expunge(row)
            return rows, total

    def login_history(self, limit: int = 50) -> list[AuditLog]:
        with self._database.session() as session:
            stmt = (
                select(AuditLog)
                .where(AuditLog.action.in_(("LOGIN", "LOGIN_FAILED", "LOGOUT", "ACCOUNT_LOCKED")))
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
            )
            rows = list(session.scalars(stmt).all())
            for row in rows:
                session.expunge(row)
            return rows

    def distinct_actions(self) -> list[str]:
        with self._database.session() as session:
            rows = session.scalars(select(AuditLog.action).distinct()).all()
            return sorted(rows)
