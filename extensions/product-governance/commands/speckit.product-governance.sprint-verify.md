---
description: "Verify sprint progress from Spec Kit feature tasks, traces, and evidence"
scripts:
  sh: .specify/extensions/product-governance/scripts/bash/product-governance.sh
  ps: .specify/extensions/product-governance/scripts/powershell/product-governance.ps1
---

# Verify Agile Sprint

Interpret `$ARGUMENTS` as a sprint ID such as `SPRINT-001`, then execute:

```text
{SCRIPT} --json agile sprint-verify --sprint "<sprint-id>"
```

The deterministic backend scans each declared feature:

- `specs/<feature>/tasks.md` for structured task completion;
- `feature-trace.json` and its synchronized `spec.md` section;
- `evidence/verification.json` for passed requirement evidence;
- dependency sprint status.

It updates only the sprint progress projection and the matching status in the
Agile implementation plan. Never mark an incomplete task complete, invent
evidence, or declare a sprint verified from prose alone.

Return task counts, feature statuses, sprint status, and every blocking
finding. A non-zero exit means the sprint is not yet verified.
