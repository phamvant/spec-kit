---
description: "Initialize product governance artifacts"
scripts:
  sh: .specify/extensions/product-governance/scripts/bash/product-governance.sh
  ps: .specify/extensions/product-governance/scripts/powershell/product-governance.ps1
---

# Initialize Product Governance

Parse `$ARGUMENTS` for product ID, product name, and optional `--force`.

Run from the project root:

```text
{SCRIPT} --json init --product-id "<id>" --product-name "<name>" [--force]
```

Execute the command rather than printing it. Do not edit `.product/` directly.
Return the operation ID, changed files, no-op state, and validation result from
the JSON response.
