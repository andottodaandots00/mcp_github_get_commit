# SpecKit Project Context

## Purpose
Provide specification-driven development workflow for engineering teams with automated validation gates.

## Tech Stack
- PowerShell 7+
- Markdown
- Git
- VS Code

## Project Conventions

### Code Style
- File naming: kebab-case for scripts, PascalCase for modules
- Indentation: 4 spaces, no tabs
- Line length: Max 120 characters
- Function naming: Verb-Noun pattern (e.g., Get-Specification, Invoke-Validation)

### Architecture Patterns
- Spec-first development: All features begin with formal specification
- Dual-state model: Truth in capability folders, proposals in changes/
- Agent-based workflow: Each phase handled by dedicated agent
- File-based persistence: All state in human-readable Markdown

### Testing Strategy
- Every requirement must have testable scenarios in WHEN/THEN format
- Validation gates at specification, implementation, and archive phases
- Automated checks via validate.ps1 script
- Manual review required before archival

### Git Workflow
- Branch naming: feature/*, fix/*, refactor/*
- Commit format: <type>(<scope>): <subject>
- Merge strategy: Squash merges to main
- Tag releases: v1.0.0 format

## Domain Context
- Capability: Deployed feature specification in specs/<name>/
- Change: Active proposal in specs/changes/<id>/
- Delta: Incremental modification to existing capability
- Gate: Validation checkpoint before workflow transition
- Constitution: Governance document in specs/memory/constitution.md

## Important Constraints
- No placeholders (TODO, TBD, [INSERT]) in final deliverables
- All specifications must pass validation before implementation
- Markdown must be human-readable and AI-parseable
- Version control required for all artifacts
- No external dependencies for core workflow

## External Dependencies
- Git 2.30+ for version control
- PowerShell 7+ for automation scripts
- VS Code (recommended) with Markdown extensions
- GitHub (optional) for issue tracking via speckit.taskstoissues
