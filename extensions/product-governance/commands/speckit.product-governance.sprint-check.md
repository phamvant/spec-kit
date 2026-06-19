---
description: "Block feature implementation unless its Agile sprint is eligible"
scripts:
  sh: .specify/extensions/product-governance/scripts/bash/product-governance.sh
  ps: .specify/extensions/product-governance/scripts/powershell/product-governance.ps1
---

# Check Agile Sprint Eligibility

Resolve the active Spec Kit feature from `$ARGUMENTS`,
`SPECIFY_FEATURE_DIRECTORY`, or `.specify/feature.json`.

Execute from the project root:

```text
{SCRIPT} --json agile sprint-check [--feature "<feature-directory-name>"]
```

Do not continue to specification, planning, task generation, or implementation
if the command fails. A feature is eligible only when:

- the Agile implementation plan is approved;
- every referenced product requirement is approved;
- the feature is allocated to exactly one sprint;
- the sprint file exists;
- every dependency sprint is verified;
- the sprint is not blocked or already verified.

Return the feature ID, sprint ID, and sprint status.
