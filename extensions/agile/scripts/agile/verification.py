"""Verification evidence validation and gate service."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from .errors import DomainError
from .io import atomic_write_json, safe_path


def validate_evidence(project_root: Path, value: dict, known_ids: set[str] | None = None) -> set[str]:
    if not str(value.get("commit", "")).strip():
        raise DomainError("Verification commit is required")
    passed: set[str] = set()
    for requirement_id, result in value.get("requirements", {}).items():
        if known_ids is not None and requirement_id not in known_ids:
            raise DomainError(f"Verification references unknown requirement: {requirement_id}")
        for evidence in result.get("evidence", []):
            kind, reference = evidence.get("type"), str(evidence.get("reference", "")).strip()
            if not reference:
                raise DomainError(f"Empty evidence reference for {requirement_id}")
            if kind == "path":
                safe_path(project_root, reference, must_exist=True)
            elif kind == "url":
                parsed = urlparse(reference)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    raise DomainError(f"Invalid evidence URL: {reference}")
            elif kind not in {"test", "commit"}:
                raise DomainError(f"Unsupported evidence type: {kind}")
        if result.get("status") == "passed" and result.get("evidence"):
            passed.add(requirement_id)
    return passed


def write_evidence(
    project_root: Path,
    path: Path,
    *,
    feature: str,
    commit: str,
    requirements: dict,
) -> dict:
    value = {
        "schema_version": "1.0",
        "feature": feature,
        "verified_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "commit": commit,
        "requirements": requirements,
    }
    validate_evidence(project_root, value)
    atomic_write_json(safe_path(project_root, path), value)
    return value


def require_passed_implements(project_root: Path, evidence: dict, implements: list[str]) -> None:
    passed = validate_evidence(project_root, evidence)
    missing = sorted(set(implements) - passed)
    if missing:
        raise DomainError(f"Passed verification evidence required for: {', '.join(missing)}")

