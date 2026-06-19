---
description: "Manage product requirements through the deterministic registry API"
scripts:
  sh: .specify/extensions/agile/scripts/bash/agile.sh
  ps: .specify/extensions/agile/scripts/powershell/agile.ps1
---

# Product Requirement

Interpret `$ARGUMENTS` as one of `add`, `update`, `transition`, `deprecate`,
`list`, or `show`. Convert prose fields into a JSON object without inventing
missing product decisions.

Run exactly one matching operation from the project root:

```text
{SCRIPT} --json requirement add --capability-token "<token>" --data '<json>'
{SCRIPT} --json requirement update --id "<requirement-id>" --data '<json>'
{SCRIPT} --json requirement transition --id "<requirement-id>" --status "<status>"
{SCRIPT} --json requirement deprecate --id "<requirement-id>"
{SCRIPT} --json requirement list
{SCRIPT} --json requirement show --id "<requirement-id>"
```

Execute the selected command rather than printing it. Never assign IDs or
mutate `.product/requirements.yml` directly. Preserve user text exactly when
constructing JSON and quote it safely for the active shell.
