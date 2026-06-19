---
description: "Analyze feature impact and propose product traceability"
scripts:
  sh: ../scripts/bash/product-governance.sh
  ps: ../scripts/powershell/product-governance.ps1
---

# Product Impact Analysis

Use `$ARGUMENTS` and the bounded product registry to create `proposal.md` and
`impact.md` in the target feature directory. Propose `implements`, `refines`,
`impacts`, and `unaffected` links. Ask for explicit human approval before
calling the deterministic `trace` command. Do not approve requirements or edit
the registry.

