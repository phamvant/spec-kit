---
description: "Append an idempotent product change event after verification"
scripts:
  sh: ../scripts/bash/product-governance.sh
  ps: ../scripts/powershell/product-governance.ps1
---

# Product Changelog

Require approved verification evidence. Run deterministic validation and
pre-change audit, then call `changelog --feature <feature>`. The script owns the
ledger append and post-change integrity validation. Never edit or truncate
`.product/changes/ledger.jsonl`.

