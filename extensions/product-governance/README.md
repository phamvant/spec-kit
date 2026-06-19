# Product Governance Extension

Product Governance adds a deterministic, CI-compatible product requirement
registry, feature traceability, coverage, verification evidence, audit reports,
and an append-only change ledger.

## Quickstart

```bash
specify extension add product-governance
python .specify/extensions/product-governance/scripts/product_governance/cli.py \
  init --product-id example --product-name "Example Product"
python .specify/extensions/product-governance/scripts/product_governance/cli.py \
  --json validate
```

The CLI returns exit `0` for success, `1` for validation/audit blocking
findings, and `2` for invocation or infrastructure failures.

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

