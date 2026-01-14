# SpecKit Constitution

## Core Principles

### I. Spec-First Development
Every feature begins with formal specification in Markdown format. Specifications must be human-readable, AI-parseable, and contain testable scenarios. No implementation without approved spec.

### II. Test-First (NON-NEGOTIABLE)
TDD mandatory: Tests written before implementation. Red-Green-Refactor cycle strictly enforced. Every requirement must have testable scenarios in WHEN/THEN format.

### III. Validation Gates
All workflow phases have automated validation gates. Specifications, plans, tasks, and implementations must pass validation before proceeding. Manual review required before archival.

### IV. Agent-Based Workflow
Each development phase handled by dedicated agent. Workflow: Constitution → Specify → Clarify → Plan → Tasks → Checklist → Analyze → Implement → Archive.

### V. File-Based Persistence
All state persisted in human-readable Markdown files. No databases required for core workflow. Version control mandatory for all artifacts.

## Additional Constraints
Technology stack: PowerShell 7+, Markdown, Git, VS Code. Compliance standards: No placeholders in final deliverables. Markdown must be human-readable and AI-parseable. No external dependencies for core workflow.

## Development Workflow
Constitution establishes governance. Specify creates feature structure. Clarify resolves ambiguities. Plan creates technical plan. Tasks generates checklist. Checklist creates acceptance criteria. Analyze validates consistency. Implement executes tasks. Archive preserves history.

## Governance
Constitution supersedes all other practices. Amendments require documentation, approval, and migration plan. All PRs/reviews must verify compliance. Complexity must be justified.

**Version**: 1.0.0 | **Ratified**: 2026-01-14 | **Last Amended**: 2026-01-14
