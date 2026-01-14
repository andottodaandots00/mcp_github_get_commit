# [PROJECT_NAME] Project Context
<!-- Example: SpecKit, TaskFlow, MyApp -->

## Purpose
[DESCRIBE_PROJECT_PURPOSE_AND_GOALS]
<!-- Example: Provide specification-driven development workflow for engineering teams with automated validation gates -->

## Tech Stack
- [TECHNOLOGY_1]
- [TECHNOLOGY_2]
- [TECHNOLOGY_3]
<!-- Example: PowerShell 7+, Markdown, Git, VS Code -->

## Project Conventions

### Code Style
[DESCRIBE_CODE_STYLE_PREFERENCES_FORMATTING_NAMING]
<!-- Example: 
- File naming: kebab-case for scripts, PascalCase for modules
- Indentation: 4 spaces, no tabs
- Line length: Max 120 characters
- Function naming: Verb-Noun pattern (e.g., Get-Specification, Invoke-Validation)
-->

### Architecture Patterns
[DOCUMENT_ARCHITECTURAL_DECISIONS_AND_PATTERNS]
<!-- Example:
- Spec-first development: All features begin with formal specification
- Dual-state model: Truth in capability folders, proposals in changes/
- Agent-based workflow: Each phase handled by dedicated agent
- File-based persistence: All state in human-readable Markdown
-->

### Testing Strategy
[EXPLAIN_TESTING_APPROACH_AND_REQUIREMENTS]
<!-- Example:
- Every requirement must have testable scenarios in WHEN/THEN format
- Validation gates at specification, implementation, and archive phases
- Automated checks via validate.ps1 script
- Manual review required before archival
-->

### Git Workflow
[DESCRIBE_BRANCHING_STRATEGY_AND_COMMIT_CONVENTIONS]
<!-- Example:
- Branch naming: feature/*, fix/*, refactor/*
- Commit format: <type>(<scope>): <subject>
- Merge strategy: Squash merges to main
- Tag releases: v1.0.0 format
-->

## Domain Context
[ADD_DOMAIN_SPECIFIC_KNOWLEDGE_FOR_AI_ASSISTANTS]
<!-- Example:
- Capability: Deployed feature specification in specs/<name>/
- Change: Active proposal in specs/changes/<id>/
- Delta: Incremental modification to existing capability
- Gate: Validation checkpoint before workflow transition
- Constitution: Governance document in specs/memory/constitution.md
-->

## Important Constraints
[LIST_TECHNICAL_BUSINESS_REGULATORY_CONSTRAINTS]
<!-- Example:
- No placeholders (TODO, TBD, [INSERT]) in final deliverables
- All specifications must pass validation before implementation
- Markdown must be human-readable and AI-parseable
- Version control required for all artifacts
- No external dependencies for core workflow
-->

## External Dependencies
[DOCUMENT_KEY_EXTERNAL_SERVICES_APIS_SYSTEMS]
<!-- Example:
- Git 2.30+ for version control
- PowerShell 7+ for automation scripts
- VS Code (recommended) with Markdown extensions
- GitHub (optional) for issue tracking via speckit.taskstoissues
-->
