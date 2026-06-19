---
description: "Validate Agile governance artifacts deterministically"
scripts:
  sh: .specify/extensions/agile/scripts/bash/agile.sh
  ps: .specify/extensions/agile/scripts/powershell/agile.ps1
---

# Validate Agile

Execute from the project root:

```text
{SCRIPT} --json validate
```

Return its findings and exit status without changing source artifacts.
