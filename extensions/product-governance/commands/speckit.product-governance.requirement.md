---
description: "Manage product requirements through the deterministic registry API"
scripts:
  sh: ../scripts/bash/product-governance.sh
  ps: ../scripts/powershell/product-governance.ps1
---

# Product Requirement

Interpret `$ARGUMENTS` as one of `add`, `update`, `transition`, `deprecate`,
`list`, or `show`. Confirm mutation intent, then call the deterministic launcher
with the corresponding `requirement` action. Never assign IDs or mutate
`.product/requirements.yml` directly.

