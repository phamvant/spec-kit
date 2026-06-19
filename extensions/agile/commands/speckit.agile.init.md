---
description: "Initialize Agile governance artifacts"
scripts:
  sh: .specify/extensions/agile/scripts/bash/agile.sh
  ps: .specify/extensions/agile/scripts/powershell/agile.ps1
---

# Initialize Agile

Parse `$ARGUMENTS` for product ID, product name, and optional `--force`.

Run from the project root:

```text
{SCRIPT} --json init --product-id "<id>" --product-name "<name>" [--force]
```

Execute the command rather than printing it. Do not edit `.product/` directly.
Return the operation ID, changed files, no-op state, and validation result from
the JSON response.
