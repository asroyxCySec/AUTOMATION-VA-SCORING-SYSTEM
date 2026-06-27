from __future__ import annotations

from app.services.assessment_service import AssessmentService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.backup_service import BackupService
from app.services.database import DatabaseService
from app.services.session_manager import SessionManager
from app.services.settings_service import SettingsService
from app.services.user_service import UserService


class ServiceContainer:
    def __init__(self, database_url: str | None = None) -> None:
        self.database = DatabaseService(database_url)
        self.database.initialize()
        self.audit = AuditService(self.database)
        self.auth = AuthService(self.database, self.audit)
        self.users = UserService(self.database, self.audit)
        self.assessments = AssessmentService(self.database, self.audit)
        self.settings = SettingsService(self.database, self.audit)
        self.backups = BackupService(self.database, self.audit)
        self.session = SessionManager()
