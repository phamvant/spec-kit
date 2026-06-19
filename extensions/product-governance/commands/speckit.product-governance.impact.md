---
description: "Analyze feature impact and propose product traceability"
scripts:
  sh: .specify/extensions/product-governance/scripts/bash/product-governance.sh
  ps: .specify/extensions/product-governance/scripts/powershell/product-governance.ps1
---

# Product Impact Analysis

Use `$ARGUMENTS` and the bounded product registry to create `proposal.md` and
`impact.md` in the target feature directory. Propose `implements`, `refines`,
`impacts`, and `unaffected` links. Ask for explicit human approval before
calling the deterministic `trace` command. Do not approve requirements or edit
the registry.

After approval, execute from the project root:

```text
{SCRIPT} --json trace --feature "<feature-directory-name>" \
  [--implements <requirement-ids...>] \
  [--refines <requirement-ids...>] \
  [--impacts <requirement-ids...>] \
  [--unaffected <requirement-ids...>]
```

Use only requirement IDs that exist in the registry. Return the generated
`spec.md` and `feature-trace.json` paths from the JSON response.
