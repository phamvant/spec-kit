---
description: "Validate product governance artifacts deterministically"
scripts:
  sh: .specify/extensions/product-governance/scripts/bash/product-governance.sh
  ps: .specify/extensions/product-governance/scripts/powershell/product-governance.ps1
---

# Validate Product Governance

Execute from the project root:

```text
{SCRIPT} --json validate
```

Return its findings and exit status without changing source artifacts.
