from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from specify_cli.extensions import ExtensionManifest, ExtensionManager
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


class TestPackageSurface:
    def test_manifest_and_commands(self):
        manifest = ExtensionManifest(EXTENSION_ROOT / "extension.yml")
        assert manifest.id == "product-governance"
        assert len(manifest.commands) == 7
        assert all((EXTENSION_ROOT / command["file"]).is_file() for command in manifest.commands)

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
