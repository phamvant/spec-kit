"""Agile delivery planning and deterministic sprint progress aggregation."""

from __future__ import annotations

import re
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .errors import DomainError, SchemaError
from .io import _atomic_write, load_json, safe_path, validate_schema
from .trace import validate_trace_pair
from .verification import validate_evidence

PLAN_PATH = Path(".product/agile/implementation-plan.md")
SPRINTS_PATH = Path(".product/agile/sprints")
PROGRESS_START = "<!-- SPRINT PROGRESS START -->"
PROGRESS_END = "<!-- SPRINT PROGRESS END -->"
REQUIRED_PLAN_HEADINGS = (
    "## 1. Estimation Assumptions",
    "## 2. Backlog Conventions",
    "## 3. Definition of Ready and Definition of Done",
    "## 4. Overall Roadmap",
    "## 5. Detailed Sprint Backlog",
    "## 6. Critical Path and Key Dependencies",
    "## 7. Epic-Level Acceptance Criteria",
    "## 8. Minimum Test Plan",
    "## 9. Release Gates",
    "## 10. Risks and Mitigations",
    "## 11. Open Decisions",
    "## 12. Proposed Actions After Open Decisions",
)
TASK_RE = re.compile(r"^\s*-\s+\[(?P<mark>[ xX])\]\s+(?P<id>T\d{3,})\b")


def _parse_markdown(path: Path) -> tuple[dict[str, Any], str]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SchemaError(f"Unable to read Markdown artifact: {path}") from exc
    if not content.startswith("---\n"):
        raise SchemaError(f"YAML frontmatter is required: {path}")
    end = content.find("\n---\n", 4)
    if end < 0:
        raise SchemaError(f"Unterminated YAML frontmatter: {path}")
    try:
        metadata = yaml.safe_load(content[4:end])
    except yaml.YAMLError as exc:
        raise SchemaError(
            f"Unable to parse Markdown frontmatter: {path}",
            details={"error": str(exc)},
        ) from exc
    if not isinstance(metadata, dict):
        raise SchemaError(f"Expected frontmatter object: {path}")
    return metadata, content[end + 5 :]


def _render_markdown(metadata: dict[str, Any], body: str) -> str:
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    return f"---\n{frontmatter}\n---\n\n{body.lstrip()}"


def _requirement_statuses(root: Path) -> dict[str, str]:
    registry_path = root / ".product" / "requirements.yml"
    try:
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SchemaError(f"Unable to load requirement registry: {registry_path}") from exc
    if not isinstance(registry, dict):
        raise SchemaError(f"Expected requirement registry object: {registry_path}")
    return {
        str(item["id"]): str(item.get("status", ""))
        for item in registry.get("requirements", [])
        if isinstance(item, dict) and item.get("id")
    }


def _validate_requirement_refs(root: Path, metadata: dict[str, Any]) -> None:
    known = set(_requirement_statuses(root))
    referenced = set(metadata.get("plan", {}).get("source_requirements", []))
    for sprint in metadata.get("sprints", []):
        referenced.update(sprint.get("requirements", []))
    unknown = sorted(referenced - known)
    if unknown:
        raise DomainError(
            f"Agile plan references unknown requirements: {', '.join(unknown)}"
        )


def _require_requirement_statuses(
    root: Path,
    metadata: dict[str, Any],
    *,
    allowed: set[str],
    message: str,
) -> None:
    statuses = _requirement_statuses(root)
    referenced = set(metadata["plan"]["source_requirements"])
    for sprint in metadata["sprints"]:
        referenced.update(sprint["requirements"])
    not_approved = sorted(
        requirement_id
        for requirement_id in referenced
        if statuses.get(requirement_id) not in allowed
    )
    if not_approved:
        raise DomainError(
            message,
            details={
                "requirements": [
                    {
                        "id": requirement_id,
                        "status": statuses.get(requirement_id, "missing"),
                    }
                    for requirement_id in not_approved
                ]
            },
        )


def _validate_plan_semantics(metadata: dict[str, Any]) -> None:
    sprints = metadata.get("sprints", [])
    sprint_ids = [item["id"] for item in sprints]
    if len(sprint_ids) != len(set(sprint_ids)):
        raise DomainError("Duplicate sprint ID in Agile implementation plan")
    known_sprints = set(sprint_ids)
    dependencies: dict[str, list[str]] = {}
    feature_ids: set[str] = set()
    for sprint in sprints:
        unknown_dependencies = sorted(set(sprint["depends_on"]) - known_sprints)
        if unknown_dependencies:
            raise DomainError(
                f"{sprint['id']} depends on unknown sprints: "
                f"{', '.join(unknown_dependencies)}"
            )
        if sprint["id"] in sprint["depends_on"]:
            raise DomainError(f"{sprint['id']} cannot depend on itself")
        dependencies[sprint["id"]] = sprint["depends_on"]
        for feature in sprint["features"]:
            feature_requirements = set(feature["requirements"])
            if not feature_requirements.issubset(set(sprint["requirements"])):
                raise DomainError(
                    f"{feature['id']} references requirements outside "
                    f"{sprint['id']}"
                )
            if feature["id"] in feature_ids:
                raise DomainError(
                    f"Feature is allocated to multiple sprints: {feature['id']}"
                )
            feature_ids.add(feature["id"])

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(sprint_id: str) -> None:
        if sprint_id in visiting:
            raise DomainError(f"Sprint dependency cycle includes {sprint_id}")
        if sprint_id in visited:
            return
        visiting.add(sprint_id)
        for dependency in dependencies[sprint_id]:
            visit(dependency)
        visiting.remove(sprint_id)
        visited.add(sprint_id)

    for sprint_id in sprint_ids:
        visit(sprint_id)


def kickoff(
    root: Path,
    input_path: Path | str,
    *,
    approve: bool,
    plan_schema: Path,
) -> tuple[Path, dict[str, Any]]:
    source = safe_path(root, input_path, must_exist=True)
    metadata, body = _parse_markdown(source)
    validate_schema(metadata, plan_schema, artifact_path=source)
    missing = [heading for heading in REQUIRED_PLAN_HEADINGS if heading not in body]
    if missing:
        raise DomainError(
            "Agile implementation plan is missing required sections",
            details={"missing_headings": missing},
        )
    _validate_requirement_refs(root, metadata)
    _validate_plan_semantics(metadata)
    if approve:
        _require_requirement_statuses(
            root,
            metadata,
            allowed={"approved"},
            message="Agile plan approval requires approved product requirements",
        )
    metadata["plan"]["status"] = "approved" if approve else "draft"
    destination = safe_path(root, PLAN_PATH)
    _atomic_write(destination, _render_markdown(metadata, body))
    return destination, metadata


def _sprint_body(sprint: dict[str, Any]) -> str:
    feature_lines = [
        f"- [ ] {feature['id']} — {feature['title']}"
        for feature in sprint["features"]
    ]
    requirement_text = ", ".join(sprint["requirements"]) or "none"
    dependencies = ", ".join(sprint["depends_on"]) or "none"
    return "\n".join(
        [
            f"# {sprint['id']} — {sprint['title']}",
            "",
            "## Goal",
            "",
            sprint["goal"],
            "",
            "## Requirements",
            "",
            requirement_text,
            "",
            "## Feature Delivery",
            "",
            *feature_lines,
            "",
            "## Dependencies",
            "",
            dependencies,
            "",
            "## Task Breakdown",
            "",
            "Implementation tasks are owned by each feature's `specs/<feature>/tasks.md`.",
            "",
            "## Verification",
            "",
            PROGRESS_START,
            "Progress has not been verified.",
            PROGRESS_END,
            "",
        ]
    )


def breakdown(
    root: Path,
    *,
    plan_schema: Path,
    sprint_schema: Path,
    force: bool = False,
) -> list[Path]:
    plan_path = safe_path(root, PLAN_PATH, must_exist=True)
    metadata, _ = _parse_markdown(plan_path)
    validate_schema(metadata, plan_schema, artifact_path=plan_path)
    _validate_requirement_refs(root, metadata)
    _validate_plan_semantics(metadata)
    if metadata["plan"]["status"] != "approved":
        raise DomainError("Agile implementation plan must be approved before breakdown")

    changed: list[Path] = []
    for sprint in metadata["sprints"]:
        sprint_path = safe_path(root, SPRINTS_PATH / f"{sprint['id']}.md")
        if sprint_path.exists() and not force:
            continue
        sprint_metadata = {
            "schema_version": "1.0",
            "sprint": {
                "id": sprint["id"],
                "plan_id": metadata["plan"]["id"],
                "title": sprint["title"],
                "goal": sprint["goal"],
                "status": "planned",
                "requirements": sprint["requirements"],
                "features": [
                    {
                        **feature,
                        "status": "planned",
                        "tasks": {"total": 0, "completed": 0, "incomplete": 0},
                        "verification": {"status": "not-run"},
                    }
                    for feature in sprint["features"]
                ],
                "depends_on": sprint["depends_on"],
                "updated_at": None,
            },
        }
        validate_schema(sprint_metadata, sprint_schema, artifact_path=sprint_path)
        _atomic_write(
            sprint_path,
            _render_markdown(sprint_metadata, _sprint_body(sprint)),
        )
        changed.append(sprint_path)
    return changed


def validate_agile_artifacts(
    root: Path,
    *,
    plan_schema: Path,
    sprint_schema: Path,
) -> None:
    plan_path = root / PLAN_PATH
    if not plan_path.exists():
        return
    metadata, _ = _parse_markdown(plan_path)
    validate_schema(metadata, plan_schema, artifact_path=plan_path)
    _validate_requirement_refs(root, metadata)
    _validate_plan_semantics(metadata)
    declared = {item["id"]: item for item in metadata["sprints"]}
    sprints_dir = root / SPRINTS_PATH
    if not sprints_dir.exists():
        return
    for sprint_path in sorted(sprints_dir.glob("SPRINT-*.md")):
        sprint_metadata, _ = _parse_markdown(sprint_path)
        validate_schema(
            sprint_metadata, sprint_schema, artifact_path=sprint_path
        )
        sprint = sprint_metadata["sprint"]
        declared_sprint = declared.get(sprint["id"])
        if declared_sprint is None:
            raise DomainError(
                f"Sprint file is not declared in implementation plan: {sprint['id']}"
            )
        if sprint["plan_id"] != metadata["plan"]["id"]:
            raise DomainError(f"Sprint plan ID mismatch: {sprint['id']}")
        if sprint["status"] != declared_sprint["status"]:
            raise DomainError(f"Sprint status projection drift: {sprint['id']}")
        declared_features = [item["id"] for item in declared_sprint["features"]]
        actual_features = [item["id"] for item in sprint["features"]]
        if actual_features != declared_features:
            raise DomainError(
                f"Sprint feature allocation drift: {sprint['id']}"
            )


def _task_counts(path: Path) -> dict[str, int]:
    if not path.exists():
        return {"total": 0, "completed": 0, "incomplete": 0}
    total = completed = 0
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = TASK_RE.match(line)
        if not match:
            continue
        total += 1
        if match.group("mark").lower() == "x":
            completed += 1
    return {"total": total, "completed": completed, "incomplete": total - completed}


def _feature_progress(root: Path, feature: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    feature_id = feature["id"]
    feature_dir = safe_path(root, Path("specs") / feature_id)
    tasks = _task_counts(feature_dir / "tasks.md")
    findings: list[str] = []
    if tasks["total"] == 0:
        status = "planned"
        findings.append(f"{feature_id}: tasks.md is missing or contains no structured tasks")
    elif tasks["completed"] == 0:
        status = "planned"
    elif tasks["incomplete"] > 0:
        status = "in_progress"
    else:
        status = "implemented"

    verification_status = "not-run"
    if feature_dir.exists() and (feature_dir / "feature-trace.json").exists():
        try:
            trace = validate_trace_pair(root, feature_dir)
        except DomainError as exc:
            findings.append(f"{feature_id}: {exc.message}")
        else:
            missing_trace = sorted(
                set(feature["requirements"]) - set(trace.implements)
            )
            if missing_trace:
                findings.append(
                    f"{feature_id}: feature trace does not implement planned "
                    f"requirements {', '.join(missing_trace)}"
                )
            evidence_path = feature_dir / "evidence" / "verification.json"
            if evidence_path.exists():
                evidence = load_json(evidence_path)
                passed = validate_evidence(root, evidence)
                missing = sorted(set(feature["requirements"]) - passed)
                if missing_trace:
                    verification_status = "failed"
                elif missing:
                    verification_status = "failed"
                    findings.append(
                        f"{feature_id}: missing passed evidence for {', '.join(missing)}"
                    )
                else:
                    verification_status = "passed"
                    if status == "implemented":
                        status = "verified"
            else:
                findings.append(f"{feature_id}: verification evidence is missing")
    else:
        findings.append(f"{feature_id}: feature trace is missing")

    return {
        **feature,
        "status": status,
        "tasks": tasks,
        "verification": {"status": verification_status},
    }, findings


def _dependency_statuses(root: Path, sprint_ids: list[str]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for sprint_id in sprint_ids:
        path = safe_path(root, SPRINTS_PATH / f"{sprint_id}.md")
        if not path.exists():
            statuses[sprint_id] = "missing"
            continue
        metadata, _ = _parse_markdown(path)
        statuses[sprint_id] = str(metadata.get("sprint", {}).get("status", "missing"))
    return statuses


def _resolve_active_feature(root: Path, feature: str | None) -> str:
    raw = feature or os.environ.get("SPECIFY_FEATURE_DIRECTORY")
    if not raw:
        feature_state = root / ".specify" / "feature.json"
        if feature_state.exists():
            raw = str(load_json(feature_state).get("feature_directory", ""))
    if not raw:
        raise DomainError(
            "No active feature is available; pass --feature or set Spec Kit feature context"
        )
    path = Path(raw)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(root.resolve())
        except ValueError as exc:
            raise DomainError(f"Active feature escapes project root: {raw}") from exc
    parts = path.parts
    if len(parts) == 1:
        feature_id = parts[0]
    elif len(parts) == 2 and parts[0] == "specs":
        feature_id = parts[1]
    else:
        raise DomainError(f"Invalid Spec Kit feature path: {raw}")
    if not re.fullmatch(r"[0-9]{3,}-[a-z0-9][a-z0-9-]*", feature_id):
        raise DomainError(f"Invalid Spec Kit feature ID: {feature_id}")
    return feature_id


def check_feature_eligibility(
    root: Path,
    feature: str | None,
    *,
    plan_schema: Path,
    sprint_schema: Path,
) -> dict[str, Any]:
    feature_id = _resolve_active_feature(root, feature)
    validate_agile_artifacts(
        root,
        plan_schema=plan_schema,
        sprint_schema=sprint_schema,
    )
    plan_path = safe_path(root, PLAN_PATH, must_exist=True)
    plan_metadata, _ = _parse_markdown(plan_path)
    validate_schema(plan_metadata, plan_schema, artifact_path=plan_path)
    _validate_requirement_refs(root, plan_metadata)
    _validate_plan_semantics(plan_metadata)
    if plan_metadata["plan"]["status"] != "approved":
        raise DomainError("Agile implementation plan is not approved")
    _require_requirement_statuses(
        root,
        plan_metadata,
        allowed={"approved", "implementing", "implemented", "verified"},
        message="Feature delivery requires approved or active product requirements",
    )

    matches = [
        sprint
        for sprint in plan_metadata["sprints"]
        if feature_id in {item["id"] for item in sprint["features"]}
    ]
    if not matches:
        raise DomainError(
            f"Feature is not allocated to an Agile sprint: {feature_id}"
        )
    sprint = matches[0]
    sprint_path = safe_path(
        root, SPRINTS_PATH / f"{sprint['id']}.md", must_exist=True
    )
    sprint_metadata, _ = _parse_markdown(sprint_path)
    validate_schema(sprint_metadata, sprint_schema, artifact_path=sprint_path)
    sprint_state = sprint_metadata["sprint"]
    if sprint_state["status"] in {"blocked", "verified"}:
        raise DomainError(
            f"Feature delivery is not eligible while {sprint['id']} is "
            f"{sprint_state['status']}"
        )
    dependency_statuses = _dependency_statuses(root, sprint["depends_on"])
    unsatisfied = {
        dependency: status
        for dependency, status in dependency_statuses.items()
        if status != "verified"
    }
    if unsatisfied:
        raise DomainError(
            f"Sprint dependencies are not verified for {sprint['id']}",
            details={"dependencies": unsatisfied},
        )
    return {
        "feature": feature_id,
        "sprint": sprint["id"],
        "sprint_status": sprint_state["status"],
        "eligible": True,
    }


def _replace_progress(body: str, progress: str) -> str:
    start = body.find(PROGRESS_START)
    end = body.find(PROGRESS_END, start + len(PROGRESS_START))
    if start < 0 or end < 0:
        return body.rstrip() + f"\n\n## Verification\n\n{progress}\n"
    return (
        body[:start]
        + progress
        + body[end + len(PROGRESS_END) :]
    )


def _render_progress(sprint: dict[str, Any], findings: list[str]) -> str:
    total = sum(item["tasks"]["total"] for item in sprint["features"])
    completed = sum(item["tasks"]["completed"] for item in sprint["features"])
    rows = [
        "| Feature | Status | Tasks | Verification |",
        "|---|---|---:|---|",
    ]
    rows.extend(
        f"| {item['id']} | {item['status']} | "
        f"{item['tasks']['completed']}/{item['tasks']['total']} | "
        f"{item['verification']['status']} |"
        for item in sprint["features"]
    )
    finding_lines = ["", "### Findings", ""] + (
        [f"- {finding}" for finding in findings] if findings else ["- None"]
    )
    return "\n".join(
        [
            PROGRESS_START,
            f"**Sprint status:** {sprint['status']}",
            "",
            f"**Task progress:** {completed}/{total}",
            "",
            *rows,
            *finding_lines,
            PROGRESS_END,
        ]
    )


def _update_plan_sprint_status(
    root: Path,
    sprint_id: str,
    status: str,
    *,
    plan_schema: Path,
) -> Path:
    plan_path = safe_path(root, PLAN_PATH, must_exist=True)
    metadata, body = _parse_markdown(plan_path)
    for item in metadata["sprints"]:
        if item["id"] == sprint_id:
            item["status"] = status
            break
    else:
        raise DomainError(f"Sprint is not declared in implementation plan: {sprint_id}")
    validate_schema(metadata, plan_schema, artifact_path=plan_path)
    _atomic_write(plan_path, _render_markdown(metadata, body))
    return plan_path


def verify_sprint(
    root: Path,
    sprint_id: str,
    *,
    plan_schema: Path,
    sprint_schema: Path,
) -> tuple[Path, Path, dict[str, Any], list[str]]:
    sprint_path = safe_path(root, SPRINTS_PATH / f"{sprint_id}.md", must_exist=True)
    metadata, body = _parse_markdown(sprint_path)
    validate_schema(metadata, sprint_schema, artifact_path=sprint_path)
    sprint = metadata["sprint"]

    dependency_statuses = _dependency_statuses(root, sprint["depends_on"])
    findings = [
        f"Dependency {dependency} is {status}, expected verified"
        for dependency, status in dependency_statuses.items()
        if status != "verified"
    ]
    features: list[dict[str, Any]] = []
    for feature in sprint["features"]:
        progress, feature_findings = _feature_progress(root, feature)
        features.append(progress)
        findings.extend(feature_findings)

    required = [item for item in features if item["required"]]
    if findings and any("Dependency " in item for item in findings):
        status = "blocked"
    elif required and all(item["status"] == "verified" for item in required):
        status = "verified"
    elif required and all(item["status"] in {"implemented", "verified"} for item in required):
        status = "implemented"
    elif any(item["status"] in {"in_progress", "implemented", "verified"} for item in features):
        status = "in_progress"
    else:
        status = "planned"

    sprint["features"] = features
    sprint["status"] = status
    sprint["updated_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    progress = _render_progress(sprint, findings)
    updated_body = _replace_progress(body, progress)
    validate_schema(metadata, sprint_schema, artifact_path=sprint_path)
    _atomic_write(sprint_path, _render_markdown(metadata, updated_body))
    plan_path = _update_plan_sprint_status(
        root, sprint_id, status, plan_schema=plan_schema
    )
    return sprint_path, plan_path, sprint, findings
