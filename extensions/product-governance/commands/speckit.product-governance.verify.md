---
description: "Collect and validate feature verification evidence"
scripts:
  sh: ../scripts/bash/product-governance.sh
  ps: ../scripts/powershell/product-governance.ps1
---

# Verify Product Requirements

For the active feature, read `feature-trace.json`, collect pass/fail/not-run
evidence for every `implements` requirement, and call deterministic `verify
--gate`. Do not append the changelog and do not transition lifecycle state
without a separate deterministic registry operation.

