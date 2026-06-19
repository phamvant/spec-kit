---
description: "Collect and validate feature verification evidence"
scripts:
  sh: .specify/extensions/agile/scripts/bash/agile.sh
  ps: .specify/extensions/agile/scripts/powershell/agile.ps1
---

# Verify Product Requirements

For the active feature, read `feature-trace.json`, collect pass/fail/not-run
evidence for every `implements` requirement, and call deterministic `verify
--gate`. Do not append the changelog and do not transition lifecycle state
without a separate deterministic registry operation.

Execute from the project root:

```text
{SCRIPT} --json verify --feature "<feature-directory-name>" \
  --commit "<commit-reference>" \
  --requirements '<requirements-evidence-json>' \
  --gate
```

Preserve evidence references exactly and quote JSON safely for the active
shell. Report every failed, missing, or not-run requirement.
