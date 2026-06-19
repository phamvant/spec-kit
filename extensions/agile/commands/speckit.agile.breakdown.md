---
description: "Break an approved Agile implementation plan into sprint delivery files"
scripts:
  sh: .specify/extensions/agile/scripts/bash/agile.sh
  ps: .specify/extensions/agile/scripts/powershell/agile.ps1
---

# Agile Sprint Breakdown

Read `.product/agile/implementation-plan.md`. If `$ARGUMENTS` includes
`--force` or the user asks to regenerate existing sprint files, include
`--force`. Execute:

```text
{SCRIPT} --json agile breakdown [--force]
```

The plan must be approved. The deterministic backend creates one file per
sprint under `.product/agile/sprints/`.

Sprint files own sprint goal, feature allocation, dependency, and aggregated
progress. When section 5 of `.product/agile/implementation-plan.md` contains
per-sprint detailed backlog or task-decomposition tables, those details are
copied into the matching sprint file's `## Task Breakdown` section. Runtime
completion status remains owned by `specs/<feature>/tasks.md`.

After generation, report sprint files in dependency order and identify the
first sprint whose dependencies are satisfied.
