---
description: "Break an approved Agile implementation plan into sprint delivery files"
scripts:
  sh: .specify/extensions/agile/scripts/bash/agile.sh
  ps: .specify/extensions/agile/scripts/powershell/agile.ps1
---

# Agile Sprint Breakdown

Read `.product/agile/implementation-plan.md` and execute:

```text
{SCRIPT} --json agile breakdown
```

The plan must be approved. The deterministic backend creates one file per
sprint under `.product/agile/sprints/`.

Sprint files own sprint goal, feature allocation, dependency, and aggregated
progress. They do not duplicate technical tasks. Technical task status remains
owned by `specs/<feature>/tasks.md`.

After generation, report sprint files in dependency order and identify the
first sprint whose dependencies are satisfied.
