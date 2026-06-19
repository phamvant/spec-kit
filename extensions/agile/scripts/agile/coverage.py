"""Coverage scanning and calculation."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .io import atomic_write_json, load_json
from .models import FeatureTrace, Requirement


def scan_traces(project_root: Path) -> list[tuple[Path, FeatureTrace]]:
    results: list[tuple[Path, FeatureTrace]] = []
    specs = project_root / "specs"
    if not specs.exists():
        return results
    for path in sorted(specs.glob("*/feature-trace.json")):
        if path.is_symlink():
            continue
        results.append((path, FeatureTrace.from_dict(load_json(path))))
    return results


def scan_verifications(project_root: Path) -> list[tuple[Path, dict]]:
    results: list[tuple[Path, dict]] = []
    specs = project_root / "specs"
    if not specs.exists():
        return results
    for path in sorted(specs.glob("*/evidence/verification.json")):
        if path.is_symlink():
            continue
        results.append((path, load_json(path)))
    return results


def _ratio(covered: int, total: int) -> dict[str, int | float | None]:
    return {"covered": covered, "total": total, "ratio": covered / total if total else None}


def calculate_coverage(
    requirements: list[Requirement],
    traces: list[FeatureTrace],
    verifications: list[dict],
    *,
    count_refines: bool = False,
) -> dict[str, Any]:
    implemented_links = {item for trace in traces for item in trace.implements}
    if count_refines:
        implemented_links |= {item for trace in traces for item in trace.refines}
    passed = {
        requirement_id
        for evidence in verifications
        for requirement_id, result in evidence.get("requirements", {}).items()
        if result.get("status") == "passed" and result.get("evidence")
    }
    approved = [req for req in requirements if req.status.value == "approved"]
    implemented = [req for req in requirements if req.status.value == "implemented"]
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "feature": _ratio(sum(req.id in implemented_links for req in approved), len(approved)),
        "verification": _ratio(sum(req.id in passed for req in implemented), len(implemented)),
        "breakdown": {},
    }
    for dimension in ("priority", "type", "capability", "status"):
        grouped: dict[str, list[Requirement]] = defaultdict(list)
        for req in requirements:
            value = getattr(req, dimension)
            grouped[value.value if hasattr(value, "value") else value].append(req)
        result["breakdown"][dimension] = {
            key: _ratio(sum(req.id in implemented_links for req in values), len(values))
            for key, values in sorted(grouped.items())
        }
    return result


def write_coverage(project_root: Path, coverage: dict[str, Any]) -> Path:
    path = project_root / ".product" / "coverage.json"
    atomic_write_json(path, coverage)
    return path

