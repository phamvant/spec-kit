---
description: "Run read-only deterministic and bounded semantic product audit"
scripts:
  sh: .specify/extensions/agile/scripts/bash/agile.sh
  ps: .specify/extensions/agile/scripts/powershell/agile.ps1
---

# Product Audit

Run deterministic `--json audit` first. Optionally add semantic candidate
findings using only bounded registry, trace, specification, constitution, and
ledger context. Each semantic finding must include evidence, confidence, and a
recommendation. Do not mutate source artifacts; write reports only.

Execute the deterministic layer from the project root:

```text
{SCRIPT} --json audit --threshold high
```

Use `--threshold critical` only when project configuration explicitly requests
it. Return report paths and preserve the deterministic exit status.
