"""Requirement registry operations and lifecycle enforcement."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import DomainError
from .io import atomic_write_yaml, load_yaml
from .models import Requirement, RequirementStatus

ID_RE = re.compile(r"^PRD-([A-Z0-9]+)-([0-9]{3,})$")
ALLOWED_TRANSITIONS = {
    RequirementStatus.PROPOSED: {RequirementStatus.REVIEWED},
    RequirementStatus.REVIEWED: {RequirementStatus.PROPOSED, RequirementStatus.APPROVED},
    RequirementStatus.APPROVED: {RequirementStatus.IMPLEMENTING, RequirementStatus.DEPRECATED},
    RequirementStatus.IMPLEMENTING: {
        RequirementStatus.APPROVED,
        RequirementStatus.IMPLEMENTED,
        RequirementStatus.DEPRECATED,
    },
    RequirementStatus.IMPLEMENTED: {
        RequirementStatus.IMPLEMENTING,
        RequirementStatus.VERIFIED,
        RequirementStatus.DEPRECATED,
    },
    RequirementStatus.VERIFIED: {RequirementStatus.DEPRECATED},
    RequirementStatus.DEPRECATED: {RequirementStatus.RETIRED},
    RequirementStatus.RETIRED: set(),
}
MUTABLE_FIELDS = {
    "title", "description", "type", "capability", "priority", "owner", "source",
    "verification", "depends_on", "supersedes", "tags",
}


def validate_registry_data(data: dict[str, Any]) -> list[Requirement]:
    requirements = [Requirement.from_dict(item) for item in data.get("requirements", [])]
    ids = [item.id for item in requirements]
    if len(ids) != len(set(ids)):
        raise DomainError("Duplicate requirement ID")
    sequences = data.get("id_sequences", {})
    seen: dict[str, int] = {}
    for requirement in requirements:
        match = ID_RE.fullmatch(requirement.id)
        if not match:
            raise DomainError(f"Invalid requirement ID: {requirement.id}")
        token, raw_sequence = match.groups()
        seen[token] = max(seen.get(token, 0), int(raw_sequence))
    for token, maximum in seen.items():
        if token not in sequences or not isinstance(sequences[token], int) or sequences[token] < maximum:
            raise DomainError(
                f"Inconsistent id_sequences for {token}: expected at least {maximum}"
            )
    return requirements


def allocate_id(data: dict[str, Any], capability_token: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]", "", capability_token).upper()
    if not token:
        raise DomainError("Capability token must contain alphanumeric characters")
    validate_registry_data(data)
    sequences = data.setdefault("id_sequences", {})
    sequence = int(sequences.get(token, 0)) + 1
    candidate = f"PRD-{token}-{sequence:03d}"
    if any(item.get("id") == candidate for item in data.get("requirements", [])):
        raise DomainError(f"Allocator collision for {candidate}")
    sequences[token] = sequence
    return candidate


def add_requirement(path: Path, value: dict[str, Any], capability_token: str) -> Requirement:
    data = load_yaml(path)
    if "id" in value:
        raise DomainError("Requirement ID is allocated by the registry")
    item = dict(value)
    item["id"] = allocate_id(data, capability_token)
    item.setdefault("status", "proposed")
    item.setdefault("depends_on", [])
    item.setdefault("supersedes", [])
    item.setdefault("tags", [])
    requirement = Requirement.from_dict(item)
    data.setdefault("requirements", []).append(requirement.to_dict())
    data["requirements"].sort(key=lambda entry: entry["id"])
    validate_registry_data(data)
    atomic_write_yaml(path, data)
    return requirement


def find_requirement(data: dict[str, Any], requirement_id: str) -> dict[str, Any]:
    for item in data.get("requirements", []):
        if item.get("id") == requirement_id:
            return item
    raise DomainError(f"Unknown requirement: {requirement_id}")


def update_requirement(path: Path, requirement_id: str, changes: dict[str, Any]) -> Requirement:
    if "id" in changes or "status" in changes:
        raise DomainError("ID is immutable and status changes require transition")
    unknown = set(changes) - MUTABLE_FIELDS
    if unknown:
        raise DomainError(f"Unsupported mutable fields: {', '.join(sorted(unknown))}")
    data = load_yaml(path)
    item = find_requirement(data, requirement_id)
    item.update(changes)
    requirement = Requirement.from_dict(item)
    item.clear()
    item.update(requirement.to_dict())
    validate_registry_data(data)
    atomic_write_yaml(path, data)
    return requirement


def transition_requirement(
    path: Path,
    requirement_id: str,
    target: str,
    *,
    verified_requirement_ids: set[str] | None = None,
) -> Requirement:
    data = load_yaml(path)
    item = find_requirement(data, requirement_id)
    current = RequirementStatus(item["status"])
    desired = RequirementStatus(target)
    if desired not in ALLOWED_TRANSITIONS[current]:
        raise DomainError(f"Forbidden lifecycle transition: {current.value} -> {desired.value}")
    if desired is RequirementStatus.VERIFIED and requirement_id not in (verified_requirement_ids or set()):
        raise DomainError(f"Passed verification evidence is required for {requirement_id}")
    item["status"] = desired.value
    requirement = Requirement.from_dict(item)
    atomic_write_yaml(path, data)
    return requirement

