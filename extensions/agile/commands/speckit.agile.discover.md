---
description: "Discover candidate Agile governance from an existing brownfield codebase"
scripts:
  sh: .specify/extensions/agile/scripts/bash/agile.sh
  ps: .specify/extensions/agile/scripts/powershell/agile.ps1
---

# Discover Brownfield Agile

Analyze the existing project and propose Agile governance from source code,
tests, API/schema definitions, configuration, migrations, package manifests,
and existing documentation.

## User Input

```text
$ARGUMENTS
```

Use the input to narrow scope when provided. Never treat inferred behavior as
approved product intent.

## Process

1. Inspect the repository structure and identify languages, frameworks,
   executable entrypoints, public interfaces, tests, persistence models, and
   operational configuration.
2. Exclude generated/vendor/build directories, secrets, caches, binaries, and
   files outside the project root. Respect exclusions in
   `.specify/extensions/agile/agile-config.yml`.
3. If `.product/requirements.yml` does not exist:
   - infer a product ID and name from repository metadata;
   - show them to the user and obtain confirmation;
   - execute:

   ```text
   {SCRIPT} --json init --product-id "<confirmed-id>" --product-name "<confirmed-name>"
   ```

4. Produce candidate requirements only when supported by concrete repository
   evidence. Each candidate must include:
   - stable temporary ID `CAND-NNN`;
   - capability token and capability name;
   - testable requirement statement;
   - proposed type and priority;
   - owner (`unassigned` when unknown);
   - source path;
   - verification method;
   - one or more project-relative evidence paths with line ranges and reasons;
   - confidence from `0` to `1`.
5. Capture ambiguous behavior as open questions instead of requirements.
6. Write the JSON candidate document to
   `.specify/agile/brownfield-discovery-input.json`, following
   `.specify/extensions/agile/schemas/brownfield-discovery.schema.json`.
7. Execute:

   ```text
   {SCRIPT} --json discover write \
     --input ".specify/agile/brownfield-discovery-input.json"
   ```

8. Present `.product/reports/brownfield-discovery.md` to the user. Clearly
   distinguish observed behavior from intended product policy.
9. Ask the user to approve specific candidate IDs. Do not import anything from
   an implicit “yes,” broad approval, or absence of feedback.
10. After receiving explicit candidate IDs, execute:

    ```text
    {SCRIPT} --json discover import --approve CAND-001 CAND-004
    ```

11. Report allocated requirement IDs. Every imported requirement must remain
    `proposed`; lifecycle review and approval are separate operations.

## Safety Rules

- Do not edit `.product/requirements.yml` directly.
- Do not infer released, implemented, or verified lifecycle status from code.
- Do not claim complete coverage of dynamically loaded or unreachable behavior.
- Do not include secrets or source excerpts in reports; cite paths and ranges.
- Do not import duplicate or unapproved candidates.

