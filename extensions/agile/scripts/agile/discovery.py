"""Brownfield discovery report persistence and approved candidate import."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import DomainError
from .io import _atomic_write, atomic_write_json, atomic_write_yaml, load_yaml
from .models import Requirement
from .registry import allocate_id, validate_registry_data


def validate_discovery_semantics(report: dict[str, Any]) -> None:
    candidates = report.get("candidates", [])
    candidate_ids = [item.get("candidate_id") for item in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise DomainError("Duplicate brownfield candidate ID")
    for candidate in candidates:
        for evidence in candidate.get("evidence", []):
            path = Path(evidence["path"])
            if path.is_absolute() or ".." in path.parts:
                raise DomainError(
                    f"Discovery evidence path must be project-relative: {path}"
                )


def render_discovery_markdown(report: dict[str, Any]) -> str:
    product = report["product"]
    lines = [
        "# Brownfield Product Discovery",
        "",
        f"Product: **{product['name']}** (`{product['id']}`)",
        f"Generated: {report['generated_at']}",
        "",
        "## Scope",
        "",
        f"- Included: {', '.join(report['scope']['included']) or 'none'}",
        f"- Excluded: {', '.join(report['scope']['excluded']) or 'none'}",
        "",
        "## Candidate Requirements",
        "",
    ]
    if not report["candidates"]:
        lines.append("No candidates were identified.")
    for candidate in report["candidates"]:
        lines.extend([
            f"### {candidate['candidate_id']} — {candidate['title']}",
            "",
            candidate["description"],
            "",
            f"- Capability: `{candidate['capability']}`",
            f"- Proposed type/priority: `{candidate['type']}` / `{candidate['priority']}`",
            f"- Confidence: `{candidate['confidence']:.2f}`",
            "- Evidence:",
        ])
        for evidence in candidate["evidence"]:
            location = evidence["path"]
            if evidence.get("lines"):
                location += f":{evidence['lines']}"
            lines.append(f"  - `{location}` — {evidence['reason']}")
        lines.append("")
    lines.extend(["## Open Questions", ""])
    if report["open_questions"]:
        lines.extend(f"- {question}" for question in report["open_questions"])
    else:
        lines.append("None.")
    return "\n".join(lines).rstrip() + "\n"


def write_discovery_report(
    project_root: Path,
    report: dict[str, Any],
    *,
    json_path: Path,
    markdown_path: Path,
) -> list[Path]:
    validate_discovery_semantics(report)
    for candidate in report["candidates"]:
        for evidence in candidate["evidence"]:
            evidence_path = project_root / evidence["path"]
            if not evidence_path.exists():
                raise DomainError(
                    f"Discovery evidence does not exist: {evidence['path']}"
                )
    atomic_write_json(json_path, report)
    _atomic_write(markdown_path, render_discovery_markdown(report))
    return [json_path, markdown_path]


def import_candidates(
    registry_path: Path,
    report: dict[str, Any],
    approved_candidate_ids: list[str],
) -> tuple[list[Requirement], list[str]]:
    validate_discovery_semantics(report)
    approved = list(dict.fromkeys(approved_candidate_ids))
    if not approved:
        raise DomainError("At least one explicitly approved candidate ID is required")
    by_id = {item["candidate_id"]: item for item in report["candidates"]}
    unknown = sorted(set(approved) - set(by_id))
    if unknown:
        raise DomainError(f"Unknown discovery candidate IDs: {', '.join(unknown)}")

    registry = load_yaml(registry_path)
    validate_registry_data(registry)
    if report["product"]["id"] != registry["product"]["id"]:
        raise DomainError(
            "Discovery report product ID does not match the initialized registry"
        )
    existing_signatures = {
        (item["title"].strip().casefold(), item["description"].strip().casefold())
        for item in registry.get("requirements", [])
    }
    imported: list[Requirement] = []
    skipped: list[str] = []
    for candidate_id in approved:
        candidate = by_id[candidate_id]
        signature = (
            candidate["title"].strip().casefold(),
            candidate["description"].strip().casefold(),
        )
        if signature in existing_signatures:
            skipped.append(candidate_id)
            continue
        value = {
            "id": allocate_id(registry, candidate["capability_token"]),
            "title": candidate["title"],
            "description": candidate["description"],
            "type": candidate["type"],
            "capability": candidate["capability"],
            "status": "proposed",
            "priority": candidate["priority"],
            "owner": candidate["owner"],
            "source": candidate["source"],
            "verification": candidate["verification"],
            "depends_on": [],
            "supersedes": [],
            "tags": sorted(set(candidate.get("tags", []) + ["brownfield-discovery"])),
        }
        requirement = Requirement.from_dict(value)
        registry.setdefault("requirements", []).append(requirement.to_dict())
        existing_signatures.add(signature)
        imported.append(requirement)
    registry["requirements"].sort(key=lambda item: item["id"])
    validate_registry_data(registry)
    if imported:
        atomic_write_yaml(registry_path, registry)
    return imported, skipped
