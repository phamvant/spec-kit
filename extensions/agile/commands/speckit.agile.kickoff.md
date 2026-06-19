---
description: "Create and approve an Agile implementation plan from product requirements"
scripts:
  sh: .specify/extensions/agile/scripts/bash/agile.sh
  ps: .specify/extensions/agile/scripts/powershell/agile.ps1
---

# Agile Product Kickoff

Use `$ARGUMENTS` and `.product/requirements.yml` to prepare a product-wide
Agile implementation plan.

1. Read the requirement registry and include only existing requirement IDs.
2. Copy
   `.specify/extensions/agile/templates/agile-implementation-plan-template.md`
   to `.specify/agile/agile-plan-input.md`.
3. Replace every placeholder. Keep the YAML frontmatter machine-readable and
   complete all twelve required sections.
4. Split delivery into outcome-oriented sprints. Each feature ID must use the
   Spec Kit directory form `NNN-kebab-case`.
5. Show assumptions, sprint allocation, dependencies, open questions, and
   release gates to the user.
6. Ask for explicit approval. Do not interpret silence as approval.
7. After approval, execute:

```text
{SCRIPT} --json agile kickoff \
  --input ".specify/agile/agile-plan-input.md" \
  --approve
```

If approval is withheld, omit `--approve`; the deterministic backend will
store a draft that cannot be broken down into sprint files.

Do not edit `.product/agile/implementation-plan.md` directly.
