---
schema_version: "1.0"
plan:
  id: AGILE-PLAN-001
  title: "<product implementation plan>"
  status: draft
  source_requirements:
    - PRD-EXAMPLE-001
sprints:
  - id: SPRINT-001
    title: "<sprint title>"
    goal: "<testable sprint outcome>"
    status: planned
    requirements:
      - PRD-EXAMPLE-001
    features:
      - id: 001-example-feature
        title: "<feature title>"
        required: true
        requirements:
          - PRD-EXAMPLE-001
    depends_on: []
---

# Agile Implementation Plan

## 1. Estimation Assumptions

## 2. Backlog Conventions

## 3. Definition of Ready and Definition of Done

## 4. Overall Roadmap

| Sprint | Goal | Demoable increment |
|---|---|---|
| Sprint 1 | `<outcome-oriented goal>` | `<increment that can be shown to users/stakeholders>` |

## 5. Detailed Sprint Backlog

### Sprint 1 — `<sprint title>`

**Goal:** `<testable sprint outcome>`

| ID | Pri | SP | Backlog item | Dependency | Acceptance criteria |
|---|---:|---:|---|---|---|
| `<ITEM-ID>` | P0 | 5 | `<deliverable backlog item>` | — | `<testable acceptance criteria>` |

#### Task breakdown

| Subtask ID | Parent | Owner | Est. | Task / output |
|---|---|---|---:|---|
| `<ITEM-ID>-T01` | `<ITEM-ID>` | `<role>` | 1d | `<concrete implementation output>` |

## 6. Critical Path and Key Dependencies

## 7. Epic-Level Acceptance Criteria

## 8. Minimum Test Plan

## 9. Release Gates

## 10. Risks and Mitigations

## 11. Open Decisions

## 12. Proposed Actions After Open Decisions
