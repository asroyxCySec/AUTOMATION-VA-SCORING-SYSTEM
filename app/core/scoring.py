from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.core import cvss, deadline, remediation, severity
from app.core.cvss import (
    AttackComplexity,
    AttackVector,
    CvssMetrics,
    Impact,
    PrivilegesRequired,
    Scope,
    UserInteraction,
)
from app.core.severity import ChainingFlags, Severity


@dataclass(frozen=True)
class ScoringInput:
    target: str
    finding_name: str
    found_on: date
    researcher: str
    attack_vector: AttackVector
    attack_complexity: AttackComplexity
    privileges_required: PrivilegesRequired
    user_interaction: UserInteraction
    scope: Scope
    confidentiality: Impact
    integrity: Impact
    availability: Impact
    public_exploit: bool = False
    cve_id: str = ""
    reproducible: bool = False
    poc_available: bool = False
    poc_attachment_path: str = ""
    impacted_data: str = ""
    estimated_users: str = ""
    regulations: tuple[str, ...] = field(default_factory=tuple)
    business_impact: str = "Low"
    chain_phpinfo_cve: bool = False
    chain_dev_credentials: bool = False
    chain_version_critical_cve: bool = False
    chain_entry_point: bool = False


@dataclass(frozen=True)
class ScoringResult:
    cvss: cvss.CvssResult
    base_severity: Severity
    final_severity: Severity
    severity_upgraded: bool
    severity_reasons: tuple[str, ...]
    remediation: remediation.RemediationEntry
    deadline: deadline.DeadlinePolicy


def compute(data: ScoringInput) -> ScoringResult:
    metrics = CvssMetrics(
        attack_vector=data.attack_vector,
        attack_complexity=data.attack_complexity,
        privileges_required=data.privileges_required,
        user_interaction=data.user_interaction,
        scope=data.scope,
        confidentiality=data.confidentiality,
        integrity=data.integrity,
        availability=data.availability,
    )
    cvss_result = cvss.calculate(metrics)
    base_severity = severity.severity_from_score(cvss_result.base_score)

    flags = ChainingFlags(
        phpinfo_with_active_cve=data.chain_phpinfo_cve,
        dev_server_with_credentials=data.chain_dev_credentials,
        version_disclosure_critical_cve=data.chain_version_critical_cve,
        public_exploit_available=data.public_exploit,
        chained_entry_point=data.chain_entry_point,
    )
    severity_result = severity.apply_chaining(base_severity, flags)

    remediation_entry = remediation.resolve(data.finding_name).entry
    deadline_policy = deadline.policy_for(severity_result.final_severity)

    return ScoringResult(
        cvss=cvss_result,
        base_severity=severity_result.base_severity,
        final_severity=severity_result.final_severity,
        severity_upgraded=severity_result.upgraded,
        severity_reasons=severity_result.reasons,
        remediation=remediation_entry,
        deadline=deadline_policy,
    )
