# Product Governance Extension

Product Governance adds a deterministic, CI-compatible product requirement
registry, feature traceability, coverage, verification evidence, audit reports,
and an append-only change ledger.

## Installation

Run the installation commands from the root of an initialized Spec Kit project.

### Bundled release

Use this after installing a Spec Kit release that includes Product Governance:

```bash
specify extension add product-governance
specify preset add product-sdd
specify workflow add product-feature-cycle
```

The extension provides product commands, the preset composes product context
into the core SDD commands, and the workflow provides the complete gated
feature cycle.

### Source checkout

When developing or testing from a local Spec Kit checkout:

```bash
SPEC_KIT=/absolute/path/to/spec-kit

specify extension add \
  --dev "$SPEC_KIT/extensions/product-governance"

specify preset add \
  --dev "$SPEC_KIT/presets/product-sdd"

specify workflow add \
  "$SPEC_KIT/workflows/product-feature-cycle/workflow.yml"
```

If `specify` is not installed globally, use the checkout executable:

```bash
SPEC_KIT=/absolute/path/to/spec-kit

"$SPEC_KIT/.venv/bin/specify" extension add \
  --dev "$SPEC_KIT/extensions/product-governance"

"$SPEC_KIT/.venv/bin/specify" preset add \
  --dev "$SPEC_KIT/presets/product-sdd"

"$SPEC_KIT/.venv/bin/specify" workflow add \
  "$SPEC_KIT/workflows/product-feature-cycle/workflow.yml"
```

To reinstall after changing extension command files:

```bash
specify extension add \
  --dev "$SPEC_KIT/extensions/product-governance" \
  --force
```

Restart or reload the coding agent after installation so it discovers the new
commands or skills.

## Agent command names

Most integrations expose slash commands:

```text
/speckit.product-governance.init
/speckit.product-governance.requirement
/speckit.product-governance.impact
/speckit.product-governance.validate
/speckit.product-governance.verify
/speckit.product-governance.audit
/speckit.product-governance.changelog
```

Codex uses skills mode and replaces dots with hyphens:

```text
$speckit-product-governance-init
$speckit-product-governance-requirement
$speckit-product-governance-impact
$speckit-product-governance-validate
$speckit-product-governance-verify
$speckit-product-governance-audit
$speckit-product-governance-changelog
```

## Quickstart

For most integrations:

```text
/speckit.product-governance.init --product-id example --product-name "Example Product"
/speckit.product-governance.requirement add an approved authentication requirement
/speckit.product-governance.validate
```

For Codex:

```text
$speckit-product-governance-init Initialize Example Product with product ID example
$speckit-product-governance-requirement Add an approved authentication requirement
$speckit-product-governance-validate
```

The installed slash commands execute the extension-local deterministic CLI.
For CI or debugging, the same backend can be called directly:

```bash
python .specify/extensions/product-governance/scripts/product_governance/cli.py \
  --json validate
```

The backend returns exit `0` for success, `1` for validation/audit blocking
findings, and `2` for invocation or infrastructure failures.

## Command workflow

For most integrations:

```text
/speckit.product-governance.init
/speckit.product-governance.requirement
/speckit.product-governance.impact
/speckit.specify
/speckit.plan
/speckit.tasks
/speckit.analyze
/speckit.implement
/speckit.product-governance.verify
/speckit.product-governance.audit
/speckit.product-governance.changelog
/speckit.product-governance.validate
```

Codex uses the equivalent `$speckit-*` names.

The complete workflow can also be started from the terminal:

```bash
specify workflow run product-feature-cycle \
  -i spec="Describe the product feature" \
  -i feature=001-feature-name \
  -i integration=codex
```

The `feature` input must match the directory name under `specs/`.

## Artifacts

- `.product/requirements.yml`: canonical product requirement registry.
- `.product/relationships.yml`: requirement relationship graph.
- `specs/*/feature-trace.json`: canonical feature trace sidecar.
- `specs/*/evidence/verification.json`: verification evidence.
- `.product/coverage.json`: generated coverage.
- `.product/changes/ledger.jsonl`: append-only product change history.
- `.product/reports/audit-*.{json,md}`: read-only audit reports.

Existing features are not backfilled automatically. Register requirements,
then link and verify features incrementally. Disabling or uninstalling the
extension preserves `.product/` and `specs/` artifacts.

Requirement statements should be testable, have a non-empty owner and source,
use stable capability tokens, and reference local evidence with project-relative
paths. URLs are syntax-checked without network access.
