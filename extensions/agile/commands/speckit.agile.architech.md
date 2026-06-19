---
description: "Inject architecture and tech-stack vision into the active coding agent context"
scripts:
  sh: .specify/extensions/agile/scripts/bash/agile.sh
  ps: .specify/extensions/agile/scripts/powershell/agile.ps1
---

# Architech Context

Use this command when the user wants the coding agent context file
(`AGENTS.md`, `CLAUDE.md`, or the active integration's configured context file)
to include architecture and tech-stack direction from an existing architecture
document.

## User Input

```text
$ARGUMENTS
```

Interpret `$ARGUMENTS` as the project-relative path to the architecture file.
Accept plain paths and common wording such as `from docs/architecture.md`.

## Process

1. Resolve the requested architecture file under the project root. Do not read
   files outside the project root.
2. Read the architecture file and extract only durable guidance useful to a
   coding agent:
   - product/system architecture vision;
   - tech stack and runtime choices;
   - major components, boundaries, and ownership;
   - data storage, external services, and integration points;
   - build, test, deployment, and operational constraints;
   - architectural decisions, constraints, and non-goals.
3. Do not copy the whole architecture file into the context file. Produce a
   concise markdown summary, preserving important names and version constraints.
   Omit marketing language, stale TODOs, and implementation detail that is not
   architectural direction.
4. Write the generated summary to:

   ```text
   .specify/agile/architech-summary.md
   ```

5. Execute the deterministic updater from the project root:

   ```text
   {SCRIPT} --json architech \
     --source "<architecture-file>" \
     --summary-file ".specify/agile/architech-summary.md"
   ```

6. Report the updated context file, source architecture file, summary file, and
   operation ID from the JSON response.

## Safety Rules

- Never edit the active context file directly; use the deterministic updater.
- Never overwrite content outside the managed
  `<!-- SPECKIT AGILE ARCHITECH START -->` /
  `<!-- SPECKIT AGILE ARCHITECH END -->` section.
- If the architecture file is missing or ambiguous, stop and ask for the exact
  project-relative path.
- If the architecture file contains secrets, credentials, or tokens, do not
  include them in the generated summary.
