---
description: "Run read-only deterministic and bounded semantic product audit"
scripts:
  sh: ../scripts/bash/product-governance.sh
  ps: ../scripts/powershell/product-governance.ps1
---

# Product Audit

Run deterministic `--json audit` first. Optionally add semantic candidate
findings using only bounded registry, trace, specification, constitution, and
ledger context. Each semantic finding must include evidence, confidence, and a
recommendation. Do not mutate source artifacts; write reports only.

