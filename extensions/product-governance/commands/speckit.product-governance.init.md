---
description: "Initialize product governance artifacts"
scripts:
  sh: ../scripts/bash/product-governance.sh
  ps: ../scripts/powershell/product-governance.ps1
---

# Initialize Product Governance

Parse `$ARGUMENTS` for product ID, product name, and optional `--force`. Run the
deterministic launcher with `init --product-id <id> --product-name <name>`.
Do not edit `.product/` directly. Report changed files and validation status.

