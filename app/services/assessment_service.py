from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import desc, func, select

from app.core import cvss, scoring
from app.core.cvss import (
    AttackComplexity,
    AttackVector,
    CvssMetrics,
    Impact,
    PrivilegesRequired,
    Scope,
    UserInteraction,
)
from app.core.deadline import policy_for
from app.core.scoring import ScoringInput
from app.core.severity import Severity, severity_color
from app.models import Assessment, AssessmentDetail, User
from app.services.audit_service import AuditContext, AuditService
from app.services.database import DatabaseService

_STEP_SEPARATOR = "\n"
_LIST_SEPARATOR = "; "


@dataclass(frozen=True)
class AssessmentSummary:
    id: int
    target: str
    finding_name: str
    found_on: date
    researcher: str
    cvss_score: float
    final_severity: str
    business_impact: str
    deadline_label: str
    owner_username: str
    created_at: datetime


@dataclass(frozen=True)
class AssessmentView:
    id: int
    owner_id: int
    owner_username: str
    target: str
    finding_name: str
    found_on: date
    researcher: str
    cvss_vector: str
    cvss_score: float
    base_severity: str
    final_severity: str
    severity_upgraded: bool
    severity_reasons: tuple[str, ...]
    parameter_labels: dict[str, str]
    metric_codes: dict[str, str]
    public_exploit: bool
    cve_id: str
    reproducible: bool
    poc_available: bool
    poc_attachment_path: str
    impacted_data: str
    estimated_users: str
    regulations: tuple[str, ...]
    business_impact: str
    chain_phpinfo_cve: bool
    chain_dev_credentials: bool
    chain_version_critical_cve: bool
    chain_entry_point: bool
    remediation_name: str
    remediation_steps: tuple[str, ...]
    remediation_owasp: str
    remediation_cwe: str
    remediation_capec: str
    remediation_references: tuple[str, ...]
    deadline_label: str
    created_at: datetime

    @property
    def severity_hex(self) -> str:
        return severity_color(Severity(self.final_severity))


@dataclass(frozen=True)
class AssessmentResult:
    success: bool
    message: str = ""
    assessment_id: int | None = None


@dataclass(frozen=True)
class DashboardStats:
    total_assessments: int
    severity_counts: dict[str, int]
    business_impact_counts: dict[str, int]
    this_month: int
    monthly_trend: list[tuple[str, int]]
    top_vulnerabilities: list[tuple[str, int]]
    average_score: float


class AssessmentService:
    def __init__(self, database: DatabaseService, audit: AuditService) -> None:
        self._database = database
        self._audit = audit

    def _apply_scoring(self, detail: AssessmentDetail, assessment: Assessment, result) -> None:
        assessment.cvss_vector = result.cvss.vector_string
        assessment.cvss_score = result.cvss.base_score
        assessment.base_severity = result.base_severity.value
        assessment.final_severity = result.final_severity.value
        assessment.severity_upgraded = result.severity_upgraded
        assessment.severity_reasons = _STEP_SEPARATOR.join(result.severity_reasons)
        assessment.deadline_label = result.deadline.label
        assessment.deadline_hours = result.deadline.hours
        detail.remediation_name = result.remediation.name
        detail.remediation_steps = _STEP_SEPARATOR.join(result.remediation.steps)
        detail.remediation_owasp = result.remediation.owasp
        detail.remediation_cwe = result.remediation.cwe
        detail.remediation_capec = result.remediation.capec
        detail.remediation_references = _STEP_SEPARATOR.join(result.remediation.references)

    @staticmethod
    def _write_detail(detail: AssessmentDetail, data: ScoringInput) -> None:
        detail.attack_vector = data.attack_vector.value
        detail.attack_complexity = data.attack_complexity.value
        detail.privileges_required = data.privileges_required.value
        detail.user_interaction = data.user_interaction.value
        detail.scope = data.scope.value
        detail.confidentiality = data.confidentiality.value
        detail.integrity = data.integrity.value
        detail.availability = data.availability.value
        detail.public_exploit = data.public_exploit
        detail.cve_id = data.cve_id.strip()
        detail.reproducible = data.reproducible
        detail.poc_available = data.poc_available
        detail.poc_attachment_path = data.poc_attachment_path
        detail.impacted_data = data.impacted_data.strip()
        detail.estimated_users = data.estimated_users.strip()
        detail.regulations = _LIST_SEPARATOR.join(data.regulations)
        detail.chain_phpinfo_cve = data.chain_phpinfo_cve
        detail.chain_dev_credentials = data.chain_dev_credentials
        detail.chain_version_critical_cve = data.chain_version_critical_cve
        detail.chain_entry_point = data.chain_entry_point

    def create(self, actor: AuditContext, owner_id: int, data: ScoringInput) -> AssessmentResult:
        result = scoring.compute(data)
        with self._database.session() as session:
            owner = session.get(User, owner_id)
            if owner is None:
                return AssessmentResult(False, "Pemilik penilaian tidak ditemukan.")
            assessment = Assessment(
                owner_id=owner_id,
                target=data.target.strip(),
                finding_name=data.finding_name.strip(),
                found_on=data.found_on,
                researcher=data.researcher.strip(),
                business_impact=data.business_impact,
            )
            detail = AssessmentDetail()
            assessment.detail = detail
            self._write_detail(detail, data)
            self._apply_scoring(detail, assessment, result)
            session.add(assessment)
            session.flush()
            assessment_id = assessment.id
            self._audit.record(
                actor,
                "CREATE_ASSESSMENT",
                f"{data.finding_name.strip()} @ {data.target.strip()} "
                f"(CVSS {result.cvss.base_score} {result.final_severity.value}).",
            )
            return AssessmentResult(True, "Penilaian berhasil disimpan.", assessment_id=assessment_id)

    def update(self, actor: AuditContext, assessment_id: int, data: ScoringInput) -> AssessmentResult:
        result = scoring.compute(data)
        with self._database.session() as session:
            assessment = session.get(Assessment, assessment_id)
            if assessment is None:
                return AssessmentResult(False, "Penilaian tidak ditemukan.")
            assessment.target = data.target.strip()
            assessment.finding_name = data.finding_name.strip()
            assessment.found_on = data.found_on
            assessment.researcher = data.researcher.strip()
            assessment.business_impact = data.business_impact
            detail = assessment.detail
            if detail is None:
                detail = AssessmentDetail()
                assessment.detail = detail
            self._write_detail(detail, data)
            self._apply_scoring(detail, assessment, result)
            self._audit.record(
                actor,
                "EDIT_ASSESSMENT",
                f"Memperbarui penilaian #{assessment_id} ({data.finding_name.strip()}).",
            )
            return AssessmentResult(True, "Penilaian berhasil diperbarui.", assessment_id=assessment_id)

    def delete(self, actor: AuditContext, assessment_id: int) -> AssessmentResult:
        with self._database.session() as session:
            assessment = session.get(Assessment, assessment_id)
            if assessment is None:
                return AssessmentResult(False, "Penilaian tidak ditemukan.")
            label = f"{assessment.finding_name} @ {assessment.target}"
            session.delete(assessment)
            self._audit.record(actor, "DELETE_ASSESSMENT", f"Menghapus penilaian #{assessment_id} ({label}).")
            return AssessmentResult(True, "Penilaian berhasil dihapus.")

    def _build_view(self, assessment: Assessment) -> AssessmentView:
        detail = assessment.detail
        metrics = CvssMetrics(
            attack_vector=AttackVector(detail.attack_vector),
            attack_complexity=AttackComplexity(detail.attack_complexity),
            privileges_required=PrivilegesRequired(detail.privileges_required),
            user_interaction=UserInteraction(detail.user_interaction),
            scope=Scope(detail.scope),
            confidentiality=Impact(detail.confidentiality),
            integrity=Impact(detail.integrity),
            availability=Impact(detail.availability),
        )
        return AssessmentView(
            id=assessment.id,
            owner_id=assessment.owner_id,
            owner_username=assessment.owner.username if assessment.owner else "",
            target=assessment.target,
            finding_name=assessment.finding_name,
            found_on=assessment.found_on,
            researcher=assessment.researcher,
            cvss_vector=assessment.cvss_vector,
            cvss_score=assessment.cvss_score,
            base_severity=assessment.base_severity,
            final_severity=assessment.final_severity,
            severity_upgraded=assessment.severity_upgraded,
            severity_reasons=tuple(filter(None, assessment.severity_reasons.split(_STEP_SEPARATOR))),
            parameter_labels=cvss.metric_labels(metrics),
            metric_codes={
                "AV": detail.attack_vector,
                "AC": detail.attack_complexity,
                "PR": detail.privileges_required,
                "UI": detail.user_interaction,
                "S": detail.scope,
                "C": detail.confidentiality,
                "I": detail.integrity,
                "A": detail.availability,
            },
            public_exploit=detail.public_exploit,
            cve_id=detail.cve_id,
            reproducible=detail.reproducible,
            poc_available=detail.poc_available,
            poc_attachment_path=detail.poc_attachment_path,
            impacted_data=detail.impacted_data,
            estimated_users=detail.estimated_users,
            regulations=tuple(filter(None, detail.regulations.split(_LIST_SEPARATOR))),
            business_impact=assessment.business_impact,
            chain_phpinfo_cve=detail.chain_phpinfo_cve,
            chain_dev_credentials=detail.chain_dev_credentials,
            chain_version_critical_cve=detail.chain_version_critical_cve,
            chain_entry_point=detail.chain_entry_point,
            remediation_name=detail.remediation_name,
            remediation_steps=tuple(filter(None, detail.remediation_steps.split(_STEP_SEPARATOR))),
            remediation_owasp=detail.remediation_owasp,
            remediation_cwe=detail.remediation_cwe,
            remediation_capec=detail.remediation_capec,
            remediation_references=tuple(filter(None, detail.remediation_references.split(_STEP_SEPARATOR))),
            deadline_label=assessment.deadline_label,
            created_at=assessment.created_at,
        )

    def get_view(self, assessment_id: int) -> AssessmentView | None:
        with self._database.session() as session:
            assessment = session.get(Assessment, assessment_id)
            if assessment is None:
                return None
            return self._build_view(assessment)

    def list_summaries(
        self,
        page: int = 1,
        page_size: int = 10,
        owner_id: int | None = None,
        search: str = "",
        severity: str | None = None,
    ) -> tuple[list[AssessmentSummary], int]:
        with self._database.session() as session:
            stmt = select(Assessment)
            count_stmt = select(func.count()).select_from(Assessment)
            if owner_id is not None:
                stmt = stmt.where(Assessment.owner_id == owner_id)
                count_stmt = count_stmt.where(Assessment.owner_id == owner_id)
            search = search.strip()
            if search:
                pattern = f"%{search}%"
                clause = (Assessment.target.like(pattern)) | (Assessment.finding_name.like(pattern))
                stmt = stmt.where(clause)
                count_stmt = count_stmt.where(clause)
            if severity:
                stmt = stmt.where(Assessment.final_severity == severity)
                count_stmt = count_stmt.where(Assessment.final_severity == severity)
            total = session.scalar(count_stmt) or 0
            offset = max(page - 1, 0) * page_size
            stmt = stmt.order_by(desc(Assessment.created_at)).offset(offset).limit(page_size)
            summaries = [
                AssessmentSummary(
                    id=a.id,
                    target=a.target,
                    finding_name=a.finding_name,
                    found_on=a.found_on,
                    researcher=a.researcher,
                    cvss_score=a.cvss_score,
                    final_severity=a.final_severity,
                    business_impact=a.business_impact,
                    deadline_label=a.deadline_label,
                    owner_username=a.owner.username if a.owner else "",
                    created_at=a.created_at,
                )
                for a in session.scalars(stmt).all()
            ]
            return summaries, total

    def dashboard_stats(self, owner_id: int | None = None) -> DashboardStats:
        severities = ("Critical", "High", "Medium", "Low", "Informational")
        impacts = ("Critical", "High", "Medium", "Low")
        with self._database.session() as session:
            base = select(Assessment)
            if owner_id is not None:
                base = base.where(Assessment.owner_id == owner_id)
            assessments = list(session.scalars(base).all())

            severity_counts = {key: 0 for key in severities}
            impact_counts = {key: 0 for key in impacts}
            vuln_counts: dict[str, int] = {}
            monthly: dict[str, int] = {}
            total_score = 0.0
            this_month = 0
            now = datetime.utcnow()

            for a in assessments:
                severity_counts[a.final_severity] = severity_counts.get(a.final_severity, 0) + 1
                impact_counts[a.business_impact] = impact_counts.get(a.business_impact, 0) + 1
                vuln_counts[a.finding_name] = vuln_counts.get(a.finding_name, 0) + 1
                total_score += a.cvss_score
                key = a.created_at.strftime("%Y-%m")
                monthly[key] = monthly.get(key, 0) + 1
                if a.created_at.year == now.year and a.created_at.month == now.month:
                    this_month += 1

            total = len(assessments)
            average = round(total_score / total, 1) if total else 0.0
            trend = sorted(monthly.items())[-6:]
            top = sorted(vuln_counts.items(), key=lambda item: item[1], reverse=True)[:5]

            return DashboardStats(
                total_assessments=total,
                severity_counts=severity_counts,
                business_impact_counts=impact_counts,
                this_month=this_month,
                monthly_trend=trend,
                top_vulnerabilities=top,
                average_score=average,
            )

    def to_scoring_input(self, view: AssessmentView) -> ScoringInput:
        return ScoringInput(
            target=view.target,
            finding_name=view.finding_name,
            found_on=view.found_on,
            researcher=view.researcher,
            attack_vector=AttackVector(view.metric_codes["AV"]),
            attack_complexity=AttackComplexity(view.metric_codes["AC"]),
            privileges_required=PrivilegesRequired(view.metric_codes["PR"]),
            user_interaction=UserInteraction(view.metric_codes["UI"]),
            scope=Scope(view.metric_codes["S"]),
            confidentiality=Impact(view.metric_codes["C"]),
            integrity=Impact(view.metric_codes["I"]),
            availability=Impact(view.metric_codes["A"]),
            public_exploit=view.public_exploit,
            cve_id=view.cve_id,
            reproducible=view.reproducible,
            poc_available=view.poc_available,
            poc_attachment_path=view.poc_attachment_path,
            impacted_data=view.impacted_data,
            estimated_users=view.estimated_users,
            regulations=view.regulations,
            business_impact=view.business_impact,
            chain_phpinfo_cve=view.chain_phpinfo_cve,
            chain_dev_credentials=view.chain_dev_credentials,
            chain_version_critical_cve=view.chain_version_critical_cve,
            chain_entry_point=view.chain_entry_point,
        )
