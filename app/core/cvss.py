from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class AttackVector(Enum):
    NETWORK = "N"
    ADJACENT = "A"
    LOCAL = "L"
    PHYSICAL = "P"


class AttackComplexity(Enum):
    LOW = "L"
    HIGH = "H"


class PrivilegesRequired(Enum):
    NONE = "N"
    LOW = "L"
    HIGH = "H"


class UserInteraction(Enum):
    NONE = "N"
    REQUIRED = "R"


class Scope(Enum):
    UNCHANGED = "U"
    CHANGED = "C"


class Impact(Enum):
    NONE = "N"
    LOW = "L"
    HIGH = "H"


_ATTACK_VECTOR_WEIGHTS = {
    AttackVector.NETWORK: 0.85,
    AttackVector.ADJACENT: 0.62,
    AttackVector.LOCAL: 0.55,
    AttackVector.PHYSICAL: 0.2,
}

_ATTACK_COMPLEXITY_WEIGHTS = {
    AttackComplexity.LOW: 0.77,
    AttackComplexity.HIGH: 0.44,
}

_PRIVILEGES_REQUIRED_UNCHANGED = {
    PrivilegesRequired.NONE: 0.85,
    PrivilegesRequired.LOW: 0.62,
    PrivilegesRequired.HIGH: 0.27,
}

_PRIVILEGES_REQUIRED_CHANGED = {
    PrivilegesRequired.NONE: 0.85,
    PrivilegesRequired.LOW: 0.68,
    PrivilegesRequired.HIGH: 0.5,
}

_USER_INTERACTION_WEIGHTS = {
    UserInteraction.NONE: 0.85,
    UserInteraction.REQUIRED: 0.62,
}

_IMPACT_WEIGHTS = {
    Impact.NONE: 0.0,
    Impact.LOW: 0.22,
    Impact.HIGH: 0.56,
}

_ATTACK_VECTOR_LABELS = {
    AttackVector.NETWORK: "Network",
    AttackVector.ADJACENT: "Adjacent",
    AttackVector.LOCAL: "Local",
    AttackVector.PHYSICAL: "Physical",
}

_ATTACK_COMPLEXITY_LABELS = {
    AttackComplexity.LOW: "Low",
    AttackComplexity.HIGH: "High",
}

_PRIVILEGES_REQUIRED_LABELS = {
    PrivilegesRequired.NONE: "None",
    PrivilegesRequired.LOW: "Low",
    PrivilegesRequired.HIGH: "High",
}

_USER_INTERACTION_LABELS = {
    UserInteraction.NONE: "None",
    UserInteraction.REQUIRED: "Required",
}

_SCOPE_LABELS = {
    Scope.UNCHANGED: "Unchanged",
    Scope.CHANGED: "Changed",
}

_IMPACT_LABELS = {
    Impact.NONE: "None",
    Impact.LOW: "Low",
    Impact.HIGH: "High",
}


@dataclass(frozen=True)
class CvssMetrics:
    attack_vector: AttackVector
    attack_complexity: AttackComplexity
    privileges_required: PrivilegesRequired
    user_interaction: UserInteraction
    scope: Scope
    confidentiality: Impact
    integrity: Impact
    availability: Impact


@dataclass(frozen=True)
class CvssResult:
    base_score: float
    vector_string: str
    exploitability_subscore: float
    impact_subscore: float
    metrics: CvssMetrics


def _roundup(value: float) -> float:
    int_input = round(value * 100000)
    if int_input % 10000 == 0:
        return int_input / 100000.0
    return (math.floor(int_input / 10000.0) + 1) / 10.0


def _impact_subscore_base(metrics: CvssMetrics) -> float:
    c = _IMPACT_WEIGHTS[metrics.confidentiality]
    i = _IMPACT_WEIGHTS[metrics.integrity]
    a = _IMPACT_WEIGHTS[metrics.availability]
    return 1.0 - ((1.0 - c) * (1.0 - i) * (1.0 - a))


def _impact_subscore(metrics: CvssMetrics, iss: float) -> float:
    if metrics.scope is Scope.UNCHANGED:
        return 6.42 * iss
    return 7.52 * (iss - 0.029) - 3.25 * math.pow(iss - 0.02, 15)


def _exploitability_subscore(metrics: CvssMetrics) -> float:
    av = _ATTACK_VECTOR_WEIGHTS[metrics.attack_vector]
    ac = _ATTACK_COMPLEXITY_WEIGHTS[metrics.attack_complexity]
    if metrics.scope is Scope.CHANGED:
        pr = _PRIVILEGES_REQUIRED_CHANGED[metrics.privileges_required]
    else:
        pr = _PRIVILEGES_REQUIRED_UNCHANGED[metrics.privileges_required]
    ui = _USER_INTERACTION_WEIGHTS[metrics.user_interaction]
    return 8.22 * av * ac * pr * ui


def build_vector_string(metrics: CvssMetrics) -> str:
    return (
        "CVSS:3.1"
        f"/AV:{metrics.attack_vector.value}"
        f"/AC:{metrics.attack_complexity.value}"
        f"/PR:{metrics.privileges_required.value}"
        f"/UI:{metrics.user_interaction.value}"
        f"/S:{metrics.scope.value}"
        f"/C:{metrics.confidentiality.value}"
        f"/I:{metrics.integrity.value}"
        f"/A:{metrics.availability.value}"
    )


def calculate(metrics: CvssMetrics) -> CvssResult:
    iss = _impact_subscore_base(metrics)
    impact = _impact_subscore(metrics, iss)
    exploitability = _exploitability_subscore(metrics)

    if impact <= 0:
        base_score = 0.0
    elif metrics.scope is Scope.UNCHANGED:
        base_score = _roundup(min(impact + exploitability, 10.0))
    else:
        base_score = _roundup(min(1.08 * (impact + exploitability), 10.0))

    return CvssResult(
        base_score=base_score,
        vector_string=build_vector_string(metrics),
        exploitability_subscore=round(exploitability, 1),
        impact_subscore=round(impact, 1),
        metrics=metrics,
    )


def metric_labels(metrics: CvssMetrics) -> dict[str, str]:
    return {
        "Attack Vector": _ATTACK_VECTOR_LABELS[metrics.attack_vector],
        "Attack Complexity": _ATTACK_COMPLEXITY_LABELS[metrics.attack_complexity],
        "Privileges Required": _PRIVILEGES_REQUIRED_LABELS[metrics.privileges_required],
        "User Interaction": _USER_INTERACTION_LABELS[metrics.user_interaction],
        "Scope": _SCOPE_LABELS[metrics.scope],
        "Confidentiality Impact": _IMPACT_LABELS[metrics.confidentiality],
        "Integrity Impact": _IMPACT_LABELS[metrics.integrity],
        "Availability Impact": _IMPACT_LABELS[metrics.availability],
    }
