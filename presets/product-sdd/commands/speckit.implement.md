---
description: "Product-context implementation"
strategy: wrap
---

## Product Implementation Boundary

Before loading implementation context, execute the mandatory
`speckit.product-governance.sprint-check` hook for the active feature. Stop if
the Agile plan is not approved, the feature is not allocated to a sprint, or a
dependency sprint is not verified.

Load only the linked product requirements and direct relationships. Preserve
normal task progress. Emit an implementation summary for verification. Never
mark product requirements verified and never write the product ledger.

{CORE_TEMPLATE}
