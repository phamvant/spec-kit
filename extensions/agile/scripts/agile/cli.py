#!/usr/bin/env python3
"""Deterministic CLI for the agile extension."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "agile"

from .audit import is_blocking, run_audit
from .agile import (
    breakdown,
    check_feature_eligibility,
    kickoff,
    validate_agile_artifacts,
    verify_sprint,
)
from .coverage import calculate_coverage, scan_traces, scan_verifications, write_coverage
from .discovery import (
    import_candidates,
    validate_discovery_semantics,
    write_discovery_report,
)
from .errors import DomainError, GovernanceError, InfrastructureError, InvocationError
from .graph import build_graph
from .io import (
    _atomic_write,
    atomic_write_json,
    atomic_write_yaml,
    discover_project_root,
    load_json,
    load_yaml,
    safe_path,
    validate_schema,
)
from .ledger import append_event, read_ledger, render_changelog
from .models import FeatureTrace, Relationship
from .registry import (
    add_requirement,
    find_requirement,
    transition_requirement,
    update_requirement,
    validate_registry_data,
)
from .reporting import build_report, write_report
from .trace import validate_trace_pair, write_trace
from .verification import require_passed_implements, write_evidence

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = PACKAGE_ROOT / "schemas"
TEMPLATES = PACKAGE_ROOT / "templates"
ARCHITECH_MARKER_START = "<!-- SPECKIT AGILE ARCHITECH START -->"
ARCHITECH_MARKER_END = "<!-- SPECKIT AGILE ARCHITECH END -->"


def operation_id() -> str:
    return f"pg-{uuid.uuid4().hex[:12]}"


def _emit(payload: dict, as_json: bool, *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    if as_json:
        print(json.dumps(payload, sort_keys=True, ensure_ascii=False), file=stream)
    else:
        print(payload.get("message", json.dumps(payload, indent=2, ensure_ascii=False)), file=stream)


def _paths(root: Path) -> tuple[Path, Path]:
    return root / ".product" / "requirements.yml", root / ".product" / "relationships.yml"


def _load_registry(root: Path) -> tuple[dict, list]:
    registry_path, _ = _paths(root)
    data = load_yaml(registry_path)
    validate_schema(data, SCHEMAS / "requirements.schema.json", artifact_path=registry_path)
    return data, validate_registry_data(data)


def validate_project(root: Path) -> list[dict]:
    findings: list[dict] = []
    try:
        data, requirements = _load_registry(root)
        del data
        relationship_path = root / ".product" / "relationships.yml"
        relationship_data = load_yaml(relationship_path)
        validate_schema(relationship_data, SCHEMAS / "relationships.schema.json", artifact_path=relationship_path)
        build_graph(
            [item.id for item in requirements],
            [Relationship.from_dict(item) for item in relationship_data["relationships"]],
        )
        known = {item.id for item in requirements}
        for feature_dir in sorted((root / "specs").glob("*")) if (root / "specs").exists() else []:
            sidecar = feature_dir / "feature-trace.json"
            if not sidecar.exists():
                continue
            validate_schema(load_json(sidecar), SCHEMAS / "feature-trace.schema.json", artifact_path=sidecar)
            trace = validate_trace_pair(root, feature_dir)
            unknown = sorted(set(trace.implements + trace.refines + trace.impacts + trace.unaffected) - known)
            if unknown:
                raise DomainError(f"{feature_dir.name} references unknown requirements: {', '.join(unknown)}")
            evidence = feature_dir / "evidence" / "verification.json"
            if evidence.exists():
                validate_schema(load_json(evidence), SCHEMAS / "verification.schema.json", artifact_path=evidence)
        ledger_path = root / ".product" / "changes" / "ledger.jsonl"
        for event in read_ledger(ledger_path):
            validate_schema(event, SCHEMAS / "ledger-event.schema.json", artifact_path=ledger_path)
        discovery_path = root / ".product" / "reports" / "brownfield-discovery.json"
        if discovery_path.exists():
            discovery = load_json(discovery_path)
            validate_schema(
                discovery,
                SCHEMAS / "brownfield-discovery.schema.json",
                artifact_path=discovery_path,
            )
            validate_discovery_semantics(discovery)
        validate_agile_artifacts(
            root,
            plan_schema=SCHEMAS / "agile-plan.schema.json",
            sprint_schema=SCHEMAS / "agile-sprint.schema.json",
        )
    except GovernanceError as exc:
        findings.append(exc.as_dict())
    return findings


def cmd_init(args: argparse.Namespace, root: Path) -> dict:
    product = root / ".product"
    if product.exists() and any(product.iterdir()) and not args.force:
        raise DomainError(".product already exists; use --force to replace managed files")
    managed = {
        "product.md": TEMPLATES / "product-template.md",
        "glossary.md": TEMPLATES / "glossary-template.md",
    }
    changed: list[str] = []
    product.mkdir(parents=True, exist_ok=True)
    for relative, source in managed.items():
        destination = product / relative
        if not destination.exists() or args.force:
            shutil.copyfile(source, destination)
            changed.append(str(destination.relative_to(root)))
    registry = product / "requirements.yml"
    if not registry.exists() or args.force:
        atomic_write_yaml(registry, {
            "schema_version": "1.0",
            "product": {"id": args.product_id, "name": args.product_name},
            "requirements": [],
            "id_sequences": {},
        })
        changed.append(".product/requirements.yml")
    relationships = product / "relationships.yml"
    if not relationships.exists() or args.force:
        atomic_write_yaml(relationships, {"schema_version": "1.0", "relationships": []})
        changed.append(".product/relationships.yml")
    (product / "changes").mkdir(exist_ok=True)
    (product / "changes" / "ledger.jsonl").touch(exist_ok=True)
    (product / "reports").mkdir(exist_ok=True)
    (product / "reports" / ".gitkeep").touch(exist_ok=True)
    (product / "schemas").mkdir(exist_ok=True)
    (product / "schemas" / "schema-version").write_text("1.0\n", encoding="utf-8")
    findings = validate_project(root)
    if findings:
        raise DomainError("Initialization validation failed", details={"findings": findings})
    return {"message": "Agile governance initialized", "changed_files": changed, "no_op": not changed}


def _load_json_argument(raw: str) -> dict:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvocationError(f"Invalid JSON value: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise InvocationError("Expected a JSON object")
    return value


def _project_relative(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def _configured_context_file(root: Path) -> Path:
    config_path = root / ".specify" / "extensions" / "agent-context" / "agent-context-config.yml"
    context_file = ""
    if config_path.exists():
        config = load_yaml(config_path)
        value = config.get("context_file")
        if isinstance(value, str):
            context_file = value.strip()

    if not context_file:
        for candidate in (
            "AGENTS.md",
            "AGENT.md",
            "CLAUDE.md",
            ".github/copilot-instructions.md",
            "GEMINI.md",
        ):
            if (root / candidate).exists():
                context_file = candidate
                break

    if not context_file:
        context_file = "AGENTS.md"

    if "\\" in context_file:
        raise InfrastructureError(
            f"context_file must use forward-slash separators: {context_file}"
        )
    context_path = safe_path(root, context_file)
    if context_path.is_dir():
        raise InfrastructureError(f"context_file points to a directory: {context_file}")
    return context_path


def _replace_marked_section(
    content: str,
    section: str,
    *,
    start: str = ARCHITECH_MARKER_START,
    end: str = ARCHITECH_MARKER_END,
) -> str:
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    s = content.find(start)
    e = content.find(end, s if s != -1 else 0)
    if s != -1 and e != -1 and e > s:
        end_of_marker = e + len(end)
        if end_of_marker < len(content) and content[end_of_marker] == "\n":
            end_of_marker += 1
        return content[:s] + section + content[end_of_marker:]
    if s != -1:
        return content[:s] + section
    if e != -1:
        end_of_marker = e + len(end)
        if end_of_marker < len(content) and content[end_of_marker] == "\n":
            end_of_marker += 1
        return section + content[end_of_marker:]
    if content and not content.endswith("\n"):
        content += "\n"
    return (content + "\n" + section) if content else section


def cmd_architech(args: argparse.Namespace, root: Path) -> dict:
    source_path = safe_path(root, args.source, must_exist=True)
    if source_path.is_dir():
        raise InfrastructureError(f"Architecture source must be a file: {args.source}")

    summary_path = safe_path(root, args.summary_file, must_exist=True)
    if summary_path.is_dir():
        raise InfrastructureError(f"Architecture summary must be a file: {args.summary_file}")
    summary = summary_path.read_text(encoding="utf-8").strip()
    if not summary:
        raise InvocationError("Architecture summary file is empty")

    context_path = _configured_context_file(root)
    context = context_path.read_text(encoding="utf-8-sig") if context_path.exists() else ""
    source_rel = _project_relative(root, source_path)
    generated_rel = _project_relative(root, summary_path)
    updated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    section = (
        f"{ARCHITECH_MARKER_START}\n"
        "## Architecture and Tech Stack Vision\n\n"
        f"- Source: `{source_rel}`\n"
        f"- Generated summary: `{generated_rel}`\n"
        f"- Updated: `{updated_at}`\n\n"
        f"{summary}\n"
        f"{ARCHITECH_MARKER_END}\n"
    )
    new_context = _replace_marked_section(context, section)
    _atomic_write(context_path, new_context)
    return {
        "message": f"Architecture context updated in {_project_relative(root, context_path)}",
        "context_file": _project_relative(root, context_path),
        "source_file": source_rel,
        "summary_file": generated_rel,
        "changed_files": [_project_relative(root, context_path)],
        "no_op": new_context == context,
    }


def cmd_requirement(args: argparse.Namespace, root: Path) -> dict:
    registry_path, _ = _paths(root)
    if args.action == "add":
        item = add_requirement(registry_path, _load_json_argument(args.data), args.capability_token)
        message = f"Added {item.id}"
        value = item.to_dict()
    elif args.action == "update":
        item = update_requirement(registry_path, args.id, _load_json_argument(args.data))
        message, value = f"Updated {item.id}", item.to_dict()
    elif args.action in {"transition", "deprecate"}:
        target = "deprecated" if args.action == "deprecate" else args.status
        verified: set[str] = set()
        for _, evidence in scan_verifications(root):
            verified |= {
                key for key, result in evidence.get("requirements", {}).items()
                if result.get("status") == "passed" and result.get("evidence")
            }
        item = transition_requirement(registry_path, args.id, target, verified_requirement_ids=verified)
        message, value = f"Transitioned {item.id} to {item.status.value}", item.to_dict()
    else:
        data, requirements = _load_registry(root)
        if args.action == "show":
            value = find_requirement(data, args.id)
            message = args.id
        else:
            value = [item.to_dict() for item in requirements]
            message = f"{len(value)} requirements"
    return {"message": message, "requirement": value, "changed_files": [".product/requirements.yml"] if args.action not in {"list", "show"} else [], "no_op": False}


def cmd_trace(args: argparse.Namespace, root: Path) -> dict:
    feature_dir = root / "specs" / args.feature
    trace = FeatureTrace(
        feature=args.feature,
        implements=sorted(set(args.implements)),
        refines=sorted(set(args.refines)),
        impacts=sorted(set(args.impacts)),
        unaffected=sorted(set(args.unaffected)),
    )
    changed = write_trace(root, feature_dir, trace)
    return {"message": f"Trace synchronized for {args.feature}", "changed_files": [str(path.relative_to(root)) for path in changed], "no_op": False}


def cmd_verify(args: argparse.Namespace, root: Path) -> dict:
    feature_dir = root / "specs" / args.feature
    trace = validate_trace_pair(root, feature_dir)
    requirements = _load_json_argument(args.requirements)
    path = feature_dir / "evidence" / "verification.json"
    value = write_evidence(root, path, feature=args.feature, commit=args.commit, requirements=requirements)
    if args.gate:
        require_passed_implements(root, value, trace.implements)
    return {"message": f"Verification evidence written for {args.feature}", "changed_files": [str(path.relative_to(root))], "no_op": False}


def cmd_coverage(args: argparse.Namespace, root: Path) -> dict:
    _, requirements = _load_registry(root)
    coverage = calculate_coverage(
        requirements,
        [trace for _, trace in scan_traces(root)],
        [value for _, value in scan_verifications(root)],
        count_refines=args.count_refines,
    )
    path = write_coverage(root, coverage)
    return {"message": "Coverage calculated", "coverage": coverage, "changed_files": [str(path.relative_to(root))], "no_op": False}


def cmd_discover(args: argparse.Namespace, root: Path) -> dict:
    reports_dir = root / ".product" / "reports"
    report_path = reports_dir / "brownfield-discovery.json"
    markdown_path = reports_dir / "brownfield-discovery.md"
    if args.action == "write":
        if args.input is None:
            raise InvocationError("discover write requires --input")
        source_path = safe_path(root, args.input, must_exist=True)
        report = load_json(source_path)
        validate_schema(
            report,
            SCHEMAS / "brownfield-discovery.schema.json",
            artifact_path=source_path,
        )
        registry, _ = _load_registry(root)
        if report["product"]["id"] != registry["product"]["id"]:
            raise DomainError(
                "Discovery report product ID does not match the initialized registry"
            )
        changed = write_discovery_report(
            root,
            report,
            json_path=report_path,
            markdown_path=markdown_path,
        )
        return {
            "message": f"Brownfield discovery recorded with {len(report['candidates'])} candidates",
            "candidate_ids": [item["candidate_id"] for item in report["candidates"]],
            "changed_files": [str(path.relative_to(root)) for path in changed],
            "no_op": False,
        }
    selected_report = safe_path(
        root,
        args.report or report_path,
        must_exist=True,
    )
    report = load_json(selected_report)
    validate_schema(
        report,
        SCHEMAS / "brownfield-discovery.schema.json",
        artifact_path=selected_report,
    )
    if args.action == "show":
        return {
            "message": f"{len(report['candidates'])} brownfield candidates",
            "report": report,
            "changed_files": [],
            "no_op": True,
        }
    registry_path, _ = _paths(root)
    imported, skipped = import_candidates(registry_path, report, args.approve)
    return {
        "message": f"Imported {len(imported)} approved brownfield candidates",
        "requirements": [item.to_dict() for item in imported],
        "skipped_candidate_ids": skipped,
        "changed_files": [".product/requirements.yml"] if imported else [],
        "no_op": not imported,
    }


def cmd_changelog(args: argparse.Namespace, root: Path) -> dict:
    feature_dir = root / "specs" / args.feature
    trace = validate_trace_pair(root, feature_dir)
    evidence_path = feature_dir / "evidence" / "verification.json"
    evidence = load_json(evidence_path)
    require_passed_implements(root, evidence, trace.implements)
    findings = validate_project(root)
    if findings:
        raise DomainError("Pre-change validation failed", details={"findings": findings})
    audit_findings, _ = run_audit(root, _load_registry(root)[1])
    blocking = [item.to_dict() for item in audit_findings if item.severity in {"critical", "high"} and item.rule_id != "PG-LEDGER-001"]
    if blocking:
        raise DomainError("Pre-change audit blocked ledger append", details={"findings": blocking})
    ledger_path = root / ".product" / "changes" / "ledger.jsonl"
    event, changed = append_event(
        ledger_path,
        feature=args.feature,
        requirements=trace.implements,
        commit=evidence["commit"],
        evidence=[str(evidence_path.relative_to(root))],
    )
    summary_path = root / ".product" / "changes" / "CHANGELOG.md"
    _atomic_write(summary_path, render_changelog(read_ledger(ledger_path)))
    post = validate_project(root)
    if post:
        raise DomainError("Ledger appended but post-change validation failed", details={"event": event, "findings": post})
    return {
        "message": f"{'Appended' if changed else 'Reused'} {event['event_id']}",
        "event": event,
        "changed_files": [str(ledger_path.relative_to(root)), str(summary_path.relative_to(root))] if changed else [],
        "no_op": not changed,
    }


def cmd_audit(args: argparse.Namespace, root: Path, op_id: str) -> tuple[dict, int]:
    _, requirements = _load_registry(root)
    findings, coverage = run_audit(root, requirements)
    report = build_report(op_id, findings, coverage)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    base = root / ".product" / "reports" / f"audit-{timestamp}"
    changed = write_report(report, base.with_suffix(".json"), base.with_suffix(".md"))
    payload = {
        "message": f"Audit completed with {len(findings)} findings",
        "report": report,
        "changed_files": [str(path.relative_to(root)) for path in changed],
        "no_op": False,
    }
    return payload, 1 if is_blocking(findings, args.threshold) else 0


def cmd_agile(args: argparse.Namespace, root: Path) -> tuple[dict, int]:
    plan_schema = SCHEMAS / "agile-plan.schema.json"
    sprint_schema = SCHEMAS / "agile-sprint.schema.json"
    if args.action == "kickoff":
        path, metadata = kickoff(
            root,
            args.input,
            approve=args.approve,
            plan_schema=plan_schema,
        )
        return {
            "message": (
                "Agile implementation plan approved"
                if args.approve
                else "Agile implementation plan created as draft"
            ),
            "plan": metadata["plan"],
            "changed_files": [str(path.relative_to(root))],
            "no_op": False,
        }, 0
    if args.action == "breakdown":
        changed = breakdown(
            root,
            plan_schema=plan_schema,
            sprint_schema=sprint_schema,
            force=args.force,
        )
        return {
            "message": f"Created or replaced {len(changed)} sprint files",
            "changed_files": [str(path.relative_to(root)) for path in changed],
            "no_op": not changed,
        }, 0
    if args.action == "sprint-check":
        eligibility = check_feature_eligibility(
            root,
            args.feature,
            plan_schema=plan_schema,
            sprint_schema=sprint_schema,
        )
        return {
            "message": (
                f"{eligibility['feature']} is eligible for delivery in "
                f"{eligibility['sprint']}"
            ),
            "eligibility": eligibility,
            "changed_files": [],
            "no_op": True,
        }, 0

    sprint_path, plan_path, sprint, findings = verify_sprint(
        root,
        args.sprint,
        plan_schema=plan_schema,
        sprint_schema=sprint_schema,
    )
    code = 0 if sprint["status"] == "verified" else 1
    return {
        "message": f"{args.sprint} is {sprint['status']}",
        "sprint": sprint,
        "findings": findings,
        "changed_files": [
            str(sprint_path.relative_to(root)),
            str(plan_path.relative_to(root)),
        ],
        "no_op": False,
    }, code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agile")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--product-id", required=True)
    init.add_argument("--product-name", required=True)
    init.add_argument("--force", action="store_true")
    sub.add_parser("validate")
    requirement = sub.add_parser("requirement")
    requirement.add_argument("action", choices=["add", "update", "transition", "deprecate", "list", "show"])
    requirement.add_argument("--id")
    requirement.add_argument("--data", default="{}")
    requirement.add_argument("--capability-token")
    requirement.add_argument("--status")
    trace = sub.add_parser("trace")
    trace.add_argument("--feature", required=True)
    for field in ("implements", "refines", "impacts", "unaffected"):
        trace.add_argument(f"--{field}", nargs="*", default=[])
    verify = sub.add_parser("verify")
    verify.add_argument("--feature", required=True)
    verify.add_argument("--commit", required=True)
    verify.add_argument("--requirements", required=True)
    verify.add_argument("--gate", action="store_true")
    coverage = sub.add_parser("coverage")
    coverage.add_argument("--count-refines", action="store_true")
    discover = sub.add_parser("discover")
    discover.add_argument("action", choices=["write", "show", "import"])
    discover.add_argument("--input", type=Path)
    discover.add_argument("--report", type=Path)
    discover.add_argument("--approve", nargs="*", default=[])
    architech = sub.add_parser("architech")
    architech.add_argument("--source", type=Path, required=True)
    architech.add_argument("--summary-file", type=Path, required=True)
    changelog = sub.add_parser("changelog")
    changelog.add_argument("--feature", required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--threshold", choices=["critical", "high"], default="high")
    agile = sub.add_parser("agile")
    agile_sub = agile.add_subparsers(dest="action", required=True)
    kickoff_parser = agile_sub.add_parser("kickoff")
    kickoff_parser.add_argument("--input", type=Path, required=True)
    kickoff_parser.add_argument("--approve", action="store_true")
    breakdown_parser = agile_sub.add_parser("breakdown")
    breakdown_parser.add_argument("--force", action="store_true")
    check_parser = agile_sub.add_parser("sprint-check")
    check_parser.add_argument("--feature")
    verify_parser = agile_sub.add_parser("sprint-verify")
    verify_parser.add_argument("--sprint", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = discover_project_root(args.root)
    op_id = operation_id()
    try:
        if args.command == "init":
            payload, code = cmd_init(args, root), 0
        elif args.command == "validate":
            findings = validate_project(root)
            payload = {"message": "Valid" if not findings else "Validation failed", "findings": findings, "changed_files": [], "no_op": True}
            code = 1 if findings else 0
        elif args.command == "requirement":
            payload, code = cmd_requirement(args, root), 0
        elif args.command == "trace":
            payload, code = cmd_trace(args, root), 0
        elif args.command == "verify":
            payload, code = cmd_verify(args, root), 0
        elif args.command == "coverage":
            payload, code = cmd_coverage(args, root), 0
        elif args.command == "discover":
            payload, code = cmd_discover(args, root), 0
        elif args.command == "architech":
            payload, code = cmd_architech(args, root), 0
        elif args.command == "changelog":
            payload, code = cmd_changelog(args, root), 0
        elif args.command == "audit":
            payload, code = cmd_audit(args, root, op_id)
        else:
            payload, code = cmd_agile(args, root)
        payload.update({"operation_id": op_id, "ok": code == 0})
        _emit(payload, args.json)
        return code
    except GovernanceError as exc:
        payload = {"ok": False, "operation_id": op_id, "error": exc.as_dict(), "changed_files": [], "no_op": True}
        _emit(payload, args.json, error=True)
        return exc.exit_code
    except (OSError, KeyError, ValueError) as exc:
        payload = {"ok": False, "operation_id": op_id, "error": {"code": "infrastructure_error", "message": str(exc)}, "changed_files": [], "no_op": True}
        _emit(payload, args.json, error=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
