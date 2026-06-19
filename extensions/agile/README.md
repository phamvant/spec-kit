# Agile Extension

Agile adds a deterministic, CI-compatible product requirement
registry, feature traceability, coverage, verification evidence, audit reports,
and an append-only change ledger.

## Installation

Run the installation commands from the root of an initialized Spec Kit project.

### Bundled release

Use this after installing a Spec Kit release that includes Agile:

```bash
specify extension add agile
specify preset add product-sdd
specify workflow add product-feature-cycle
specify workflow add product-sprint-feature-cycle
```

The extension provides product commands, the preset composes product context
into the core SDD commands, and the workflow provides the complete gated
feature cycle.

### Source checkout

When developing or testing from a local Spec Kit checkout:

```bash
SPEC_KIT=/absolute/path/to/spec-kit

specify extension add \
  --dev "$SPEC_KIT/extensions/agile"

specify preset add \
  --dev "$SPEC_KIT/presets/product-sdd"

specify workflow add \
  "$SPEC_KIT/workflows/product-feature-cycle/workflow.yml"

specify workflow add \
  "$SPEC_KIT/workflows/product-sprint-feature-cycle/workflow.yml"
```

If `specify` is not installed globally, use the checkout executable:

```bash
SPEC_KIT=/absolute/path/to/spec-kit

"$SPEC_KIT/.venv/bin/specify" extension add \
  --dev "$SPEC_KIT/extensions/agile"

"$SPEC_KIT/.venv/bin/specify" preset add \
  --dev "$SPEC_KIT/presets/product-sdd"

"$SPEC_KIT/.venv/bin/specify" workflow add \
  "$SPEC_KIT/workflows/product-feature-cycle/workflow.yml"
```

To reinstall after changing extension command files:

```bash
specify extension add \
  --dev "$SPEC_KIT/extensions/agile" \
  --force
```

Restart or reload the coding agent after installation so it discovers the new
commands or skills.

## Agent command names

Most integrations expose slash commands:

```text
/speckit.agile.architech
/speckit.agile.init
/speckit.agile.requirement
/speckit.agile.impact
/speckit.agile.discover
/speckit.agile.validate
/speckit.agile.verify
/speckit.agile.audit
/speckit.agile.changelog
/speckit.agile.kickoff
/speckit.agile.breakdown
/speckit.agile.sprint-check
/speckit.agile.sprint-verify
```

Codex uses skills mode and replaces dots with hyphens:

```text
$speckit-agile-architech
$speckit-agile-init
$speckit-agile-requirement
$speckit-agile-impact
$speckit-agile-discover
$speckit-agile-validate
$speckit-agile-verify
$speckit-agile-audit
$speckit-agile-changelog
$speckit-agile-kickoff
$speckit-agile-breakdown
$speckit-agile-sprint-check
$speckit-agile-sprint-verify
```

## Quickstart

For most integrations:

```text
/speckit.agile.architech docs/architecture.md
/speckit.agile.init --product-id example --product-name "Example Product"
/speckit.agile.requirement add an approved authentication requirement
/speckit.agile.validate
```

For Codex:

```text
$speckit-agile-architech docs/architecture.md
$speckit-agile-init Initialize Example Product with product ID example
$speckit-agile-requirement Add an approved authentication requirement
$speckit-agile-validate
```

## Architecture and tech-stack context

Use `speckit.agile.architech` when an existing architecture document should
become durable context for coding agents:

```text
/speckit.agile.architech docs/architecture.md
```

Codex:

```text
$speckit-agile-architech docs/architecture.md
```

The command reads the specified project-relative architecture file, generates
a concise `.specify/agile/architech-summary.md`, and updates the active coding
agent context file configured by the `agent-context` extension, such as
`AGENTS.md` or `CLAUDE.md`. The update is contained inside a managed
`SPECKIT AGILE ARCHITECH` section so rerunning the command replaces only that
section.

## Brownfield projects

For an existing codebase with no governance documentation, run:

```text
/speckit.agile.discover
```

Codex:

```text
$speckit-agile-discover
```

The command:

1. Inspects source code, tests, public interfaces, schemas, configuration, and
   existing documentation.
2. Initializes `.product/` after confirming the inferred product identity.
3. Writes evidence-backed candidates to:
   - `.product/reports/brownfield-discovery.json`
   - `.product/reports/brownfield-discovery.md`
4. Asks which `CAND-NNN` entries should be imported.
5. Imports only explicitly selected candidates as `proposed` requirements.

Discovery describes behavior observed in the repository. It does not assume
that existing behavior is correct product policy, and it never marks inferred
requirements as approved, implemented, or verified.

The installed slash commands execute the extension-local deterministic CLI.
For CI or debugging, the same backend can be called directly:

```bash
python .specify/extensions/agile/scripts/agile/cli.py \
  --json validate
```

The backend returns exit `0` for success, `1` for validation/audit blocking
findings, and `2` for invocation or infrastructure failures.

## Command workflow

For most integrations:

```text
/speckit.agile.init
/speckit.agile.requirement
/speckit.agile.discover
/speckit.agile.impact
/speckit.specify
/speckit.plan
/speckit.tasks
/speckit.analyze
/speckit.implement
/speckit.agile.verify
/speckit.agile.audit
/speckit.agile.changelog
/speckit.agile.validate
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

For strict Agile enforcement, run the sprint workflow instead:

```bash
specify workflow run product-sprint-feature-cycle \
  -i spec="Describe the sprint feature" \
  -i feature=001-feature-name \
  -i integration=codex
```

This workflow executes deterministic sprint eligibility checks before planning
and again before implementation. A failed check stops the workflow.

## Agile delivery progress

Agile can derive sprint progress while keeping Spec Kit feature
tasks as the implementation source of truth:

```text
/speckit.agile.kickoff
/speckit.agile.breakdown
/speckit.agile.sprint-check
/speckit.agile.sprint-verify SPRINT-001
```

Codex exposes the equivalent `$speckit-agile-*` skills.

`kickoff` creates `.product/agile/implementation-plan.md` from approved product
requirements. `breakdown` creates one file under `.product/agile/sprints/` per
sprint. `sprint-check` is a mandatory pre-hook for plan, tasks, analyze, and
implement; it blocks features outside the approved sprint plan or behind
unverified dependencies. `sprint-verify` reads each feature's `tasks.md`, trace,
and verification evidence, then updates the aggregated sprint status. It never
marks incomplete implementation tasks complete.

## Artifacts

- `.product/requirements.yml`: canonical product requirement registry.
- `.product/relationships.yml`: requirement relationship graph.
- `specs/*/feature-trace.json`: canonical feature trace sidecar.
- `specs/*/evidence/verification.json`: verification evidence.
- `.product/coverage.json`: generated coverage.
- `.product/changes/ledger.jsonl`: append-only product change history.
- `.product/reports/audit-*.{json,md}`: read-only audit reports.
- `.product/agile/implementation-plan.md`: approved Agile roadmap and sprint allocation.
- `.product/agile/sprints/SPRINT-*.md`: sprint goals and generated progress projections.

Existing features are not backfilled automatically. Register requirements,
then link and verify features incrementally. Disabling or uninstalling the
extension preserves `.product/` and `specs/` artifacts.

Requirement statements should be testable, have a non-empty owner and source,
use stable capability tokens, and reference local evidence with project-relative
paths. URLs are syntax-checked without network access.
