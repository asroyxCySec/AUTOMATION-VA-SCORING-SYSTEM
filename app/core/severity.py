from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    INFORMATIONAL = "Informational"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


_SEVERITY_ORDER = {
    Severity.INFORMATIONAL: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

_SEVERITY_BY_RANK = {value: key for key, value in _SEVERITY_ORDER.items()}

_SEVERITY_COLORS = {
    Severity.INFORMATIONAL: "#4F8DFD",
    Severity.LOW: "#2FBF71",
    Severity.MEDIUM: "#E8B931",
    Severity.HIGH: "#F06A2A",
    Severity.CRITICAL: "#E5384F",
}


@dataclass(frozen=True)
class ChainingFlags:
    phpinfo_with_active_cve: bool = False
    dev_server_with_credentials: bool = False
    version_disclosure_critical_cve: bool = False
    public_exploit_available: bool = False
    chained_entry_point: bool = False


@dataclass(frozen=True)
class SeverityResult:
    base_severity: Severity
    final_severity: Severity
    upgraded: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)


def severity_from_score(score: float) -> Severity:
    if score <= 0.0:
        return Severity.INFORMATIONAL
    if score < 4.0:
        return Severity.LOW
    if score < 7.0:
        return Severity.MEDIUM
    if score < 9.0:
        return Severity.HIGH
    return Severity.CRITICAL


def severity_color(severity: Severity) -> str:
    return _SEVERITY_COLORS[severity]


def severity_rank(severity: Severity) -> int:
    return _SEVERITY_ORDER[severity]


def _raise_to(current: Severity, target: Severity) -> Severity:
    if _SEVERITY_ORDER[target] > _SEVERITY_ORDER[current]:
        return target
    return current


def _raise_by(current: Severity, steps: int) -> Severity:
    rank = min(_SEVERITY_ORDER[current] + steps, _SEVERITY_ORDER[Severity.CRITICAL])
    return _SEVERITY_BY_RANK[rank]


def apply_chaining(base: Severity, flags: ChainingFlags) -> SeverityResult:
    final = base
    reasons: list[str] = []

    if flags.phpinfo_with_active_cve:
        promoted = _raise_to(final, Severity.HIGH)
        if promoted is not final:
            final = promoted
            reasons.append(
                "phpinfo terekspos pada versi PHP dengan CVE aktif menjadi entry point eksploitasi; "
                "severity dinaikkan minimal ke High."
            )

    if flags.dev_server_with_credentials:
        promoted = _raise_to(final, Severity.HIGH)
        if promoted is not final:
            final = promoted
            reasons.append(
                "Development server membuka akses ke source code atau credential; "
                "severity dinaikkan minimal ke High."
            )

    if flags.version_disclosure_critical_cve:
        promoted = _raise_to(final, Severity.CRITICAL)
        if promoted is not final:
            final = promoted
            reasons.append(
                "Version disclosure memetakan langsung ke CVE Critical yang dapat dieksploitasi; "
                "severity dinaikkan ke Critical."
            )

    if flags.chained_entry_point:
        promoted = _raise_by(final, 1)
        if promoted is not final:
            final = promoted
            reasons.append(
                "Temuan dapat dirantai sebagai entry point serangan lanjutan; "
                "severity dinaikkan satu tingkat."
            )

    if flags.public_exploit_available:
        promoted = _raise_to(final, Severity.HIGH)
        if promoted is not final:
            final = promoted
            reasons.append(
                "Eksploit publik telah tersedia sehingga probabilitas eksploitasi tinggi; "
                "severity dinaikkan minimal ke High."
            )

    return SeverityResult(
        base_severity=base,
        final_severity=final,
        upgraded=final is not base,
        reasons=tuple(reasons),
    )
