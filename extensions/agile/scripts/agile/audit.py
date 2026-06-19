"""Read-only deterministic product audit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .coverage import calculate_coverage, scan_traces, scan_verifications
from .ledger import read_ledger
from .models import Requirement


@dataclass(slots=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    evidence: list[str]
    confidence: float
    remediation: str

    def to_dict(self) -> dict:
        return asdict(self)


def run_audit(project_root: Path, requirements: list[Requirement]) -> tuple[list[Finding], dict]:
    trace_pairs = scan_traces(project_root)
    verification_pairs = scan_verifications(project_root)
    traces = [trace for _, trace in trace_pairs]
    verifications = [value for _, value in verification_pairs]
    coverage = calculate_coverage(requirements, traces, verifications)
    findings: list[Finding] = []
    links = {item for trace in traces for item in trace.implements}
    for requirement in requirements:
        if requirement.status.value == "approved" and requirement.id not in links:
            severity = "high" if requirement.priority.value == "must" else "medium"
            findings.append(Finding(
                "PG-COVERAGE-001", severity,
                f"Approved {requirement.priority.value} requirement has no implementation coverage: {requirement.id}",
                [".product/requirements.yml"], 1.0,
                "Link an implementing feature or explicitly change the requirement lifecycle.",
            ))
        if not requirement.owner or not requirement.source:
            findings.append(Finding(
                "PG-METADATA-001", "medium",
                f"Requirement is missing owner or source: {requirement.id}",
                [".product/requirements.yml"], 1.0,
                "Set both owner and source on the requirement.",
            ))
    ledger_path = project_root / ".product" / "changes" / "ledger.jsonl"
    events = read_ledger(ledger_path) if ledger_path.exists() else []
    for path, evidence in verification_pairs:
        if all(result.get("status") == "passed" for result in evidence.get("requirements", {}).values()):
            if not any(event.get("feature") == evidence.get("feature") for event in events):
                findings.append(Finding(
                    "PG-LEDGER-001", "high",
                    f"Verified feature has no ledger event: {evidence.get('feature')}",
                    [str(path.relative_to(project_root))], 1.0,
                    "Append the verified feature through the changelog command.",
                ))
    return sorted(findings, key=lambda item: (item.severity, item.rule_id, item.message)), coverage


def is_blocking(findings: list[Finding], threshold: str = "high") -> bool:
    rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    return any(rank[item.severity] >= rank[threshold] for item in findings)

