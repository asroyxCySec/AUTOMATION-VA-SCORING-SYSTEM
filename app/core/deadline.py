from __future__ import annotations

from dataclasses import dataclass

from app.core.severity import Severity


@dataclass(frozen=True)
class DeadlinePolicy:
    label: str
    hours: int
    mandatory: bool


_POLICIES = {
    Severity.CRITICAL: DeadlinePolicy(label="24 jam", hours=24, mandatory=True),
    Severity.HIGH: DeadlinePolicy(label="7 hari", hours=168, mandatory=True),
    Severity.MEDIUM: DeadlinePolicy(label="30 hari", hours=720, mandatory=True),
    Severity.LOW: DeadlinePolicy(label="30 hari", hours=720, mandatory=True),
    Severity.INFORMATIONAL: DeadlinePolicy(label="Tidak wajib", hours=0, mandatory=False),
}


def policy_for(severity: Severity) -> DeadlinePolicy:
    return _POLICIES[severity]
