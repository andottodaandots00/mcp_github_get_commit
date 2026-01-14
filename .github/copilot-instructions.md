<!-- BEGIN SPECKIT AUTO -->
# Copilot Context for hybrid

**Last Updated**: 2026-01-15 02:38:41

## Project Overview

This project follows SpecKit Consolidated governance with spec-first development and file-based truth.

## Governance Principles

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


## Technology Stack

### Backend
- PowerShell 7+
- Markdown
- Git
- VS Code


## Code Conventions
- 

## Architecture Patterns
- 

## Active Changes
- No active changes

## SpecKit Workflow

All features follow the 11-phase SpecKit workflow:

1. **document** - Generate workflow guide
2. **constitution** - Verify governance
3. **specify** - Create specification
4. **clarify** - Resolve ambiguities
5. **plan** - Technical implementation plan
6. **tasks** - Task breakdown
7. **checklist** - Acceptance criteria
8. **taskstoissues** - Convert to GitHub issues
9. **analyze** - Validate consistency
10. **implement** - Execute implementation
11. **archive** - Archive and promote to truth

## References

- Constitution: specs/memory/constitution.md
- Project Context: specs/project.md
- Changes: specs/changes/
- SpecKit Agents: .github/agents/
<!-- END SPECKIT AUTO -->


