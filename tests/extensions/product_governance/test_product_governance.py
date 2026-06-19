from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from specify_cli.extensions import CommandRegistrar, ExtensionManifest, ExtensionManager
from specify_cli.integrations.base import IntegrationBase
from specify_cli.presets import PresetManifest
from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXTENSION_ROOT = PROJECT_ROOT / "extensions" / "product-governance"
PACKAGE_PARENT = EXTENSION_ROOT / "scripts"
CLI = EXTENSION_ROOT / "scripts" / "product_governance" / "cli.py"

sys.path.insert(0, str(PACKAGE_PARENT))

from product_governance.coverage import calculate_coverage
from product_governance.errors import DomainError, InfrastructureError
from product_governance.graph import build_graph
from product_governance.io import load_json, safe_path
from product_governance.ledger import append_event, read_ledger
from product_governance.models import FeatureTrace, Relationship, Requirement
from product_governance.registry import allocate_id, transition_requirement
from product_governance.trace import validate_trace_pair, write_trace


def run_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(root), "--json", *args],
        capture_output=True,
        text=True,
    )


def init_project(root: Path) -> None:
    (root / ".specify").mkdir()
    result = run_cli(
        root, "init", "--product-id", "example", "--product-name", "Example"
    )
    assert result.returncode == 0, result.stderr


def requirement_value(**overrides) -> dict:
    value = {
        "title": "Authenticate users",
        "description": "Users must authenticate before protected data is returned.",
        "type": "functional",
        "capability": "CAP-IDENTITY",
        "status": "proposed",
        "priority": "must",
        "owner": "product",
        "source": "product.md#authentication",
        "verification": {"method": "acceptance-test"},
        "depends_on": [],
        "supersedes": [],
        "tags": ["identity"],
    }
    value.update(overrides)
    return value


def setup_verified_agile_sprint(root: Path) -> Path:
    init_project(root)
    add = run_cli(
        root,
        "requirement", "add",
        "--capability-token", "AUTH",
        "--data", json.dumps(requirement_value()),
    )
    assert add.returncode == 0, add.stderr
    reviewed = run_cli(
        root,
        "requirement", "transition",
        "--id", "PRD-AUTH-001",
        "--status", "reviewed",
    )
    assert reviewed.returncode == 0, reviewed.stderr
    approved = run_cli(
        root,
        "requirement", "transition",
        "--id", "PRD-AUTH-001",
        "--status", "approved",
    )
    assert approved.returncode == 0, approved.stderr

    plan_input = root / ".specify" / "product-governance" / "agile-plan-input.md"
    plan_input.parent.mkdir()
    headings = [
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
    ]
    metadata = {
        "schema_version": "1.0",
        "plan": {
            "id": "AGILE-PLAN-001",
            "title": "Authentication delivery",
            "status": "draft",
            "source_requirements": ["PRD-AUTH-001"],
        },
        "sprints": [{
            "id": "SPRINT-001",
            "title": "Authentication foundation",
            "goal": "Deliver verified authentication",
            "status": "planned",
            "requirements": ["PRD-AUTH-001"],
            "features": [{
                "id": "001-auth",
                "title": "Authentication",
                "required": True,
                "requirements": ["PRD-AUTH-001"],
            }],
            "depends_on": [],
        }],
    }
    plan_input.write_text(
        "---\n"
        + yaml.safe_dump(metadata, sort_keys=False)
        + "---\n\n# Agile Implementation Plan\n\n"
        + "\n\nContent\n\n".join(headings)
        + "\n"
    )

    kickoff_result = run_cli(
        root,
        "agile", "kickoff",
        "--input", str(plan_input.relative_to(root)),
        "--approve",
    )
    assert kickoff_result.returncode == 0, kickoff_result.stderr
    breakdown_result = run_cli(root, "agile", "breakdown")
    assert breakdown_result.returncode == 0, breakdown_result.stderr
    sprint_path = root / ".product" / "agile" / "sprints" / "SPRINT-001.md"
    assert sprint_path.is_file()

    trace = run_cli(
        root,
        "trace", "--feature", "001-auth",
        "--implements", "PRD-AUTH-001",
    )
    assert trace.returncode == 0, trace.stderr
    (root / "specs" / "001-auth" / "tasks.md").write_text(
        "# Tasks\n\n- [X] T001 Implement authentication in src/auth.py\n"
    )
    (root / "tests").mkdir()
    evidence = {
        "PRD-AUTH-001": {
            "status": "passed",
            "evidence": [{"type": "path", "reference": "tests"}],
        }
    }
    verify = run_cli(
        root,
        "verify", "--feature", "001-auth", "--commit", "abc123",
        "--requirements", json.dumps(evidence), "--gate",
    )
    assert verify.returncode == 0, verify.stderr
    return sprint_path


class TestSchemas:
    @pytest.mark.parametrize(
        "name",
        [
            "requirements",
            "relationships",
            "feature-trace",
            "verification",
            "ledger-event",
            "audit-report",
            "brownfield-discovery",
            "agile-plan",
            "agile-sprint",
        ],
    )
    def test_schema_is_draft_2020_12(self, name: str):
        schema = load_json(EXTENSION_ROOT / "schemas" / f"{name}.schema.json")
        Draft202012Validator.check_schema(schema)

    def test_unsupported_version_fails(self, tmp_path: Path):
        init_project(tmp_path)
        path = tmp_path / ".product" / "requirements.yml"
        data = yaml.safe_load(path.read_text())
        data["schema_version"] = "2.0"
        path.write_text(yaml.safe_dump(data))
        result = run_cli(tmp_path, "validate")
        assert result.returncode == 1
        assert "Unsupported schema_version" in result.stdout


class TestRegistryAndGraph:
    def test_allocator_uses_high_water_mark(self):
        data = {
            "requirements": [
                {"id": "PRD-AUTH-001", **requirement_value()}
            ],
            "id_sequences": {"AUTH": 7},
        }
        assert allocate_id(data, "auth") == "PRD-AUTH-008"

    def test_allocator_rejects_inconsistent_manual_state(self):
        data = {
            "requirements": [
                {"id": "PRD-AUTH-004", **requirement_value()}
            ],
            "id_sequences": {"AUTH": 2},
        }
        with pytest.raises(DomainError, match="Inconsistent"):
            allocate_id(data, "AUTH")

    def test_lifecycle_forbids_skipped_transition(self, tmp_path: Path):
        init_project(tmp_path)
        add = run_cli(
            tmp_path,
            "requirement", "add",
            "--capability-token", "AUTH",
            "--data", json.dumps(requirement_value()),
        )
        assert add.returncode == 0, add.stderr
        with pytest.raises(DomainError, match="Forbidden"):
            transition_requirement(
                tmp_path / ".product" / "requirements.yml",
                "PRD-AUTH-001",
                "approved",
            )

    def test_graph_normalizes_conflict_and_rejects_cycle(self):
        ids = {"PRD-A-001", "PRD-B-001"}
        normalized = build_graph(ids, [
            Relationship.from_dict({
                "from": "PRD-B-001", "type": "conflicts_with", "to": "PRD-A-001"
            })
        ])
        assert normalized[0].source == "PRD-A-001"
        with pytest.raises(DomainError, match="cycle"):
            build_graph(ids, [
                Relationship.from_dict({"from": "PRD-A-001", "type": "depends_on", "to": "PRD-B-001"}),
                Relationship.from_dict({"from": "PRD-B-001", "type": "depends_on", "to": "PRD-A-001"}),
            ])

    def test_safe_path_rejects_escape(self, tmp_path: Path):
        with pytest.raises(InfrastructureError, match="escapes"):
            safe_path(tmp_path, "../outside")


class TestTraceCoverageLedger:
    def test_trace_round_trip_and_drift(self, tmp_path: Path):
        feature = tmp_path / "specs" / "001-auth"
        trace = FeatureTrace(feature="001-auth", implements=["PRD-AUTH-001"])
        write_trace(tmp_path, feature, trace)
        assert validate_trace_pair(tmp_path, feature).implements == ["PRD-AUTH-001"]
        sidecar = feature / "feature-trace.json"
        value = json.loads(sidecar.read_text())
        value["implements"] = []
        sidecar.write_text(json.dumps(value))
        with pytest.raises(DomainError, match="drift"):
            validate_trace_pair(tmp_path, feature)

    def test_empty_denominator_is_null(self):
        coverage = calculate_coverage([], [], [])
        assert coverage["feature"] == {"covered": 0, "total": 0, "ratio": None}
        assert coverage["verification"] == {"covered": 0, "total": 0, "ratio": None}

    def test_ledger_is_idempotent_and_monotonic(self, tmp_path: Path):
        ledger = tmp_path / ".product" / "changes" / "ledger.jsonl"
        first, changed = append_event(
            ledger,
            feature="001-auth",
            requirements=["PRD-AUTH-001"],
            commit="abc123",
            evidence=["specs/001-auth/evidence/verification.json"],
        )
        duplicate, changed_again = append_event(
            ledger,
            feature="001-auth",
            requirements=["PRD-AUTH-001"],
            commit="abc123",
            evidence=["specs/001-auth/evidence/verification.json"],
        )
        assert changed is True
        assert changed_again is False
        assert duplicate["event_id"] == first["event_id"] == "CHG-000001"
        assert len(read_ledger(ledger)) == 1


class TestCLIEndToEnd:
    def test_init_add_trace_verify_changelog_audit(self, tmp_path: Path):
        init_project(tmp_path)
        add = run_cli(
            tmp_path,
            "requirement", "add",
            "--capability-token", "AUTH",
            "--data", json.dumps(requirement_value()),
        )
        assert add.returncode == 0, add.stderr
        trace = run_cli(
            tmp_path,
            "trace", "--feature", "001-auth",
            "--implements", "PRD-AUTH-001",
        )
        assert trace.returncode == 0, trace.stderr
        (tmp_path / "tests").mkdir()
        evidence = {
            "PRD-AUTH-001": {
                "status": "passed",
                "evidence": [{"type": "path", "reference": "tests"}],
            }
        }
        verify = run_cli(
            tmp_path,
            "verify", "--feature", "001-auth", "--commit", "abc123",
            "--requirements", json.dumps(evidence), "--gate",
        )
        assert verify.returncode == 0, verify.stderr
        changelog = run_cli(tmp_path, "changelog", "--feature", "001-auth")
        assert changelog.returncode == 0, changelog.stderr
        repeated = run_cli(tmp_path, "changelog", "--feature", "001-auth")
        assert repeated.returncode == 0, repeated.stderr
        assert json.loads(repeated.stdout)["no_op"] is True
        audit = run_cli(tmp_path, "audit")
        assert audit.returncode == 0, audit.stderr
        assert len(list((tmp_path / ".product" / "reports").glob("audit-*.json"))) == 1

    def test_brownfield_discovery_requires_explicit_import(self, tmp_path: Path):
        init_project(tmp_path)
        source = tmp_path / "src" / "auth.py"
        source.parent.mkdir()
        source.write_text("def authenticate(user):\n    return bool(user)\n")
        candidate_input = (
            tmp_path
            / ".specify"
            / "product-governance"
            / "brownfield-discovery-input.json"
        )
        candidate_input.parent.mkdir()
        candidate_input.write_text(json.dumps({
            "schema_version": "1.0",
            "generated_at": "2026-06-19T10:00:00Z",
            "product": {"id": "example", "name": "Example"},
            "scope": {"included": ["src"], "excluded": [".venv"]},
            "candidates": [{
                "candidate_id": "CAND-001",
                "capability_token": "AUTH",
                "title": "Authenticate users",
                "description": "The product must authenticate a supplied user before access is granted.",
                "type": "functional",
                "capability": "CAP-IDENTITY",
                "priority": "must",
                "owner": "unassigned",
                "source": "src/auth.py",
                "verification": {"method": "acceptance-test"},
                "evidence": [{
                    "path": "src/auth.py",
                    "lines": "1-2",
                    "reason": "The public function implements an authentication decision."
                }],
                "confidence": 0.8,
                "tags": ["authentication"]
            }],
            "open_questions": ["What identities are considered valid?"]
        }))
        write = run_cli(
            tmp_path,
            "discover",
            "write",
            "--input",
            str(candidate_input.relative_to(tmp_path)),
        )
        assert write.returncode == 0, write.stderr
        registry = yaml.safe_load(
            (tmp_path / ".product" / "requirements.yml").read_text()
        )
        assert registry["requirements"] == []
        rejected = run_cli(tmp_path, "discover", "import")
        assert rejected.returncode == 1
        imported = run_cli(
            tmp_path,
            "discover",
            "import",
            "--approve",
            "CAND-001",
        )
        assert imported.returncode == 0, imported.stderr
        requirement = json.loads(imported.stdout)["requirements"][0]
        assert requirement["id"] == "PRD-AUTH-001"
        assert requirement["status"] == "proposed"
        assert "brownfield-discovery" in requirement["tags"]
        assert (
            tmp_path / ".product" / "reports" / "brownfield-discovery.md"
        ).is_file()

    def test_agile_kickoff_breakdown_and_sprint_verify(self, tmp_path: Path):
        sprint_path = setup_verified_agile_sprint(tmp_path)

        eligibility = run_cli(
            tmp_path, "agile", "sprint-check", "--feature", "001-auth"
        )
        assert eligibility.returncode == 0, eligibility.stderr
        assert json.loads(eligibility.stdout)["eligibility"]["sprint"] == "SPRINT-001"

        sprint_verify = run_cli(
            tmp_path, "agile", "sprint-verify", "--sprint", "SPRINT-001"
        )
        assert sprint_verify.returncode == 0, sprint_verify.stderr
        payload = json.loads(sprint_verify.stdout)
        assert payload["sprint"]["status"] == "verified"
        assert payload["sprint"]["features"][0]["tasks"] == {
            "total": 1,
            "completed": 1,
            "incomplete": 0,
        }
        assert "Sprint status:** verified" in sprint_path.read_text()
        assert "status: verified" in (
            tmp_path / ".product" / "agile" / "implementation-plan.md"
        ).read_text()
        validation = run_cli(tmp_path, "validate")
        assert validation.returncode == 0, validation.stdout

    def test_sprint_verify_reports_incomplete_tasks(self, tmp_path: Path):
        setup_verified_agile_sprint(tmp_path)
        tasks = tmp_path / "specs" / "001-auth" / "tasks.md"
        tasks.write_text(
            "# Tasks\n\n"
            "- [X] T001 Implement authentication in src/auth.py\n"
            "- [ ] T002 Add rejection tests in tests/test_auth.py\n"
        )
        result = run_cli(
            tmp_path, "agile", "sprint-verify", "--sprint", "SPRINT-001"
        )
        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["sprint"]["status"] == "in_progress"
        assert payload["sprint"]["features"][0]["tasks"]["incomplete"] == 1

    def test_agile_plan_approval_rejects_unapproved_requirements(
        self, tmp_path: Path
    ):
        init_project(tmp_path)
        add = run_cli(
            tmp_path,
            "requirement", "add",
            "--capability-token", "AUTH",
            "--data", json.dumps(requirement_value()),
        )
        assert add.returncode == 0, add.stderr
        template = (
            EXTENSION_ROOT / "templates" / "agile-implementation-plan-template.md"
        ).read_text()
        template = template.replace("PRD-EXAMPLE-001", "PRD-AUTH-001")
        plan_input = tmp_path / ".specify" / "product-governance" / "plan.md"
        plan_input.parent.mkdir()
        plan_input.write_text(template)

        result = run_cli(
            tmp_path,
            "agile", "kickoff",
            "--input", str(plan_input.relative_to(tmp_path)),
            "--approve",
        )
        assert result.returncode == 1
        assert "requires approved product requirements" in result.stderr

    def test_sprint_check_rejects_feature_outside_plan(self, tmp_path: Path):
        setup_verified_agile_sprint(tmp_path)
        result = run_cli(
            tmp_path, "agile", "sprint-check", "--feature", "999-outside"
        )
        assert result.returncode == 1
        assert "not allocated to an Agile sprint" in result.stderr

    def test_sprint_check_rejects_unverified_dependency(self, tmp_path: Path):
        setup_verified_agile_sprint(tmp_path)
        plan_path = tmp_path / ".product" / "agile" / "implementation-plan.md"
        content = plan_path.read_text()
        _, frontmatter, body = content.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        metadata["sprints"].append({
            "id": "SPRINT-002",
            "title": "Dependent delivery",
            "goal": "Deliver a dependent feature",
            "status": "planned",
            "requirements": ["PRD-AUTH-001"],
            "features": [{
                "id": "002-dependent",
                "title": "Dependent feature",
                "required": True,
                "requirements": ["PRD-AUTH-001"],
            }],
            "depends_on": ["SPRINT-001"],
        })
        plan_path.write_text(
            "---\n"
            + yaml.safe_dump(metadata, sort_keys=False)
            + "---"
            + body
        )
        breakdown = run_cli(tmp_path, "agile", "breakdown")
        assert breakdown.returncode == 0, breakdown.stderr

        result = run_cli(
            tmp_path, "agile", "sprint-check", "--feature", "002-dependent"
        )
        assert result.returncode == 1
        assert "dependencies are not verified" in result.stderr

    def test_sprint_verify_rejects_trace_missing_planned_requirement(
        self, tmp_path: Path
    ):
        setup_verified_agile_sprint(tmp_path)
        trace = run_cli(tmp_path, "trace", "--feature", "001-auth")
        assert trace.returncode == 0, trace.stderr

        result = run_cli(
            tmp_path, "agile", "sprint-verify", "--sprint", "SPRINT-001"
        )
        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["sprint"]["status"] == "implemented"
        assert payload["sprint"]["features"][0]["verification"]["status"] == "failed"
        assert any(
            "does not implement planned requirements" in finding
            for finding in payload["findings"]
        )


class TestPackageSurface:
    def test_manifest_and_commands(self):
        manifest = ExtensionManifest(EXTENSION_ROOT / "extension.yml")
        assert manifest.id == "product-governance"
        assert len(manifest.commands) == 12
        assert all((EXTENSION_ROOT / command["file"]).is_file() for command in manifest.commands)
        assert manifest.hooks["before_implement"]["optional"] is False

    def test_commands_resolve_extension_local_tool_calls(self):
        manifest = ExtensionManifest(EXTENSION_ROOT / "extension.yml")
        for command in manifest.commands:
            source = (EXTENSION_ROOT / command["file"]).read_text(encoding="utf-8")
            assert "{SCRIPT}" in source
            rendered = IntegrationBase.process_template(
                source,
                agent_name="codex",
                script_type="sh",
            )
            assert "{SCRIPT}" not in rendered
            assert (
                ".specify/extensions/product-governance/scripts/bash/"
                "product-governance.sh"
            ) in rendered

    def test_codex_registers_agile_commands_as_skills(self, tmp_path: Path):
        skills_dir = tmp_path / ".agents" / "skills"
        skills_dir.mkdir(parents=True)
        manifest = ExtensionManifest(EXTENSION_ROOT / "extension.yml")
        CommandRegistrar().register_commands_for_agent(
            "codex", manifest, EXTENSION_ROOT, tmp_path
        )
        for name in ("kickoff", "breakdown", "sprint-check", "sprint-verify"):
            skill = (
                skills_dir
                / f"speckit-product-governance-{name}"
                / "SKILL.md"
            )
            assert skill.is_file()
            assert "product-governance.sh" in skill.read_text()

    def test_install_copies_deterministic_package(self, tmp_path: Path):
        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(
            EXTENSION_ROOT, "0.11.3", register_commands=False
        )
        installed = tmp_path / ".specify" / "extensions" / "product-governance"
        assert manifest.id == "product-governance"
        assert (installed / "scripts" / "product_governance" / "cli.py").is_file()
        assert (installed / "schemas" / "requirements.schema.json").is_file()

    def test_preset_and_workflow_contracts(self):
        preset = PresetManifest(
            PROJECT_ROOT / "presets" / "product-sdd" / "preset.yml"
        )
        assert preset.id == "product-sdd"
        assert len(preset.templates) == 5
        workflow = WorkflowDefinition.from_yaml(
            PROJECT_ROOT / "workflows" / "product-feature-cycle" / "workflow.yml"
        )
        assert validate_workflow(workflow) == []
        ids = [step["id"] for step in workflow.steps]
        assert ids.index("verify") < ids.index("approve-verification")
        assert ids.index("approve-verification") < ids.index("pre-change-audit")
        assert ids.index("pre-change-audit") < ids.index("changelog")
        assert ids.index("changelog") < ids.index("post-change-validation")

        sprint_workflow = WorkflowDefinition.from_yaml(
            PROJECT_ROOT
            / "workflows"
            / "product-sprint-feature-cycle"
            / "workflow.yml"
        )
        assert validate_workflow(sprint_workflow) == []
        sprint_ids = [step["id"] for step in sprint_workflow.steps]
        assert sprint_ids.index("enforce-sprint-eligibility") < sprint_ids.index("plan")
        assert sprint_ids.index("enforce-before-implement") < sprint_ids.index("implement")
