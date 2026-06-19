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
   complete all twelve required sections with concrete content.
4. Split delivery into outcome-oriented sprints. Each feature ID must use the
   Spec Kit directory form `NNN-kebab-case`.
5. For long requirement sets, do not summarize into a short sprint list.
   Produce a detailed implementation plan:
   - section 4 must include a roadmap table with one row per sprint:
     `Sprint`, `Goal`, and `Increment có thể demo` / demoable increment;
   - section 5 must include one subsection per sprint using the heading form
     `### Sprint N — <title>` (or `### SPRINT-NNN — <title>`);
   - each sprint subsection must include `**Goal:**`, a backlog table with
     `ID`, `Pri`, `SP`, `Backlog item`, `Dependency`, and
     `Acceptance criteria`;
   - each sprint subsection must also include a `#### Task breakdown` table
     with `Subtask ID`, `Parent`, `Owner`, `Est.`, and `Task / output`.
     Decompose every backlog item into concrete implementation tasks. Use
     stable IDs like `BE-001-T01`, `FL-010-T02`, or `QA-001-T03`.
6. The YAML frontmatter is the machine contract; the markdown body is the
   human execution plan. Keep them aligned: every sprint and feature in
   frontmatter must appear in sections 4 and 5, and every backlog row in
   section 5 must map to an existing requirement ID through the sprint's
   frontmatter `requirements`.
7. Show assumptions, sprint allocation, dependencies, open questions, and
   release gates to the user.
8. Ask for explicit approval. Do not interpret silence as approval.
9. After approval, execute:

```text
{SCRIPT} --json agile kickoff \
  --input ".specify/agile/agile-plan-input.md" \
  --approve
```

If approval is withheld, omit `--approve`; the deterministic backend will
store a draft that cannot be broken down into sprint files.

Do not edit `.product/agile/implementation-plan.md` directly. Do not collapse
large products into a minimal skeleton; preserve enough detail for engineering
teams to execute sprint by sprint.
