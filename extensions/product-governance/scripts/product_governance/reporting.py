"""Deterministic JSON/Markdown report rendering."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .audit import Finding
from .io import atomic_write_json, _atomic_write


def build_report(operation_id: str, findings: list[Finding], coverage: dict) -> dict:
    return {
        "schema_version": "1.0",
        "operation_id": operation_id,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "findings": [item.to_dict() for item in findings],
        "coverage": coverage,
    }


def render_markdown(report: dict) -> str:
    lines = ["# Product Governance Audit", "", f"Operation: `{report['operation_id']}`", ""]
    if not report["findings"]:
        lines.append("No findings.")
    for finding in report["findings"]:
        message = finding["message"].replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")
        lines.extend([
            f"## {finding['severity'].upper()} — {finding['rule_id']}",
            "",
            message,
            "",
            f"Remediation: {finding['remediation']}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict, json_path: Path, markdown_path: Path) -> list[Path]:
    atomic_write_json(json_path, report)
    _atomic_write(markdown_path, render_markdown(report))
    return [json_path, markdown_path]

