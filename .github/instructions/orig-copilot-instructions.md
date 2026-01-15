---
description: Optimized execution instructions for speckit.document.optimized agent - prompt synthesis and gap coverage
applyTo: "**"
---

# SpecKit Document - Execution Instructions

## Context

### Codebase Environment
- **Governance paths**: `specs/memory/constitution.md`, `specs/project.md`
- **Fallback governance**: `.github/copilot-instructions.md` → `README.md`
- **Tech stack source**: `project.md` under `## Technology` or `## Stack` sections

### Search Optimization
When `semantic_search` returns 50+ results, narrow with:
1. Add domain prefix: `"[domain] handler|service|controller"`
2. Filter by file type: grep with `includePattern: "**/*.ts"` or `"**/*.tsx"`
3. Scope to directories: `src/[domain]/**` patterns

## Execution Boundaries

### Discovery Limits
| Metric | Threshold | Action at Limit |
|--------|-----------|-----------------|
| Search iterations | 5 | Stop, use best matches |
| Files to read | 10 per step | Prioritize by relevance |
| Grep results | 100 | Add specificity filters |
| Total execution | 3 minutes | Output with `[PARTIAL]` flag |

### Scope Restrictions
- **Single domain per run**: If request spans domains, primary = first noun mentioned
- **No file creation**: Output to chat only, never `create_file` or `editFiles`
- **No execution**: Generate prompts, never invoke `@speckit.*` agents directly

### Completion Signals
Output is complete when:
- [ ] All 10 prompts populated OR marked with SKIP reason
- [ ] Zero placeholders remain in any prompt
- [ ] Feature type is one of: GREENFIELD, EXTENSION, UPGRADE, REFACTOR
- [ ] Tech stack is concrete OR user prompted for definition

## Gap Coverage

### Ambiguous Input Handling
If `$ARGUMENTS` lacks specificity:

| Missing | Default | Prompt Addition |
|---------|---------|-----------------|
| Action verb | `create` | "Assuming new feature creation" |
| Domain noun | **ABORT** | "Specify the domain: user? auth? payments?" |
| Scope | `single entity` | "Scope limited to [domain] entity" |
| Tech stack | from `project.md` | If missing: "Define stack in Step 1" |

### Governance Edge Cases
- **Both files template**: Step 1 prompt mandatory with `[GOVERNANCE_REQUIRED]` prefix
- **Constitution ready, project.md template**: Skip Step 1, but prompt for tech stack inline
- **Conflicting principles**: Flag in output, use most recent file by git history
- **Missing both + no fallbacks**: Generate prompts with `[NO_GOVERNANCE]` warnings

### Search Failure Recovery
When all searches return empty:
1. Confirm GREENFIELD classification
2. Check for typos in domain term
3. Expand search: `"[domain]" OR "[Domain]" OR "[DOMAIN]"`
4. Try singular/plural variants
5. If still empty: valid GREENFIELD, proceed with scaffold prompts

## Prompt Templates

### Prompt Synthesis Rules
Each prompt must:
- Start with exact agent invocation: `@speckit.[name]`
- Include discovered file paths (not generic patterns)
- Specify concrete values from governance/codebase
- Be copy-paste executable with no editing required

### The 10 Prompts (In Execution Order)

```markdown
## Prompt 1: Constitution
@speckit.constitution Initialize governance for [PROJECT_NAME]:
- Principles: [DISCOVERED_PATTERNS] OR [REQUEST_DEFINITION]
- Tech stack: [FROM_PROJECT_MD] OR [REQUEST_DEFINITION]
- Conventions: [FROM_CODEBASE] OR [STANDARD_DEFAULTS]
SKIP IF: constitution.md is populated (no placeholders)

## Prompt 2: Specify
@speckit.specify Document [FEATURE_NAME] feature:
- Type: [GREENFIELD|EXTENSION|UPGRADE|REFACTOR]
- Domain: [DOMAIN_NOUN]
- Tech: [STACK_FROM_PROJECT_MD]
- Operations: [DISCOVERED_OR_STANDARD: create, read, update, delete]
- Fields: [FROM_EXISTING_ENTITY OR REASONABLE_DEFAULTS]
- Auth: [FROM_CONSTITUTION OR "define in spec"]
- Related files: [LIST_DISCOVERED_PATHS]

## Prompt 3: Clarify
@speckit.clarify Resolve ambiguities for [FEATURE_NAME]:
- [GAP_1]: [QUESTION_WITH_OPTIONS]
- [GAP_2]: [QUESTION_WITH_OPTIONS]
SKIP IF: No gaps found during discovery

## Prompt 4: Plan
@speckit.plan Architecture for [FEATURE_NAME]:
- Pattern: [DISCOVERED_PATTERN: repository, service, controller]
- Folder: [EXISTING_STRUCTURE]/[domain]/
- Integrations: [DISCOVERED_DEPENDENCIES]
- New files: [PROJECTED_PATHS]

## Prompt 5: Tasks
@speckit.tasks Break down [FEATURE_NAME]:
- Phase 1: [FOUNDATION_TASKS]
- Phase 2: [CORE_IMPLEMENTATION]
- Phase 3: [INTEGRATION_TESTING]
- Dependencies: [TASK_ORDER_CONSTRAINTS]

## Prompt 6: Checklist
@speckit.checklist Acceptance criteria for [FEATURE_NAME]:
- Functional: [DOMAIN_SPECIFIC_REQUIREMENTS]
- Technical: [FROM_CONSTITUTION_QUALITY_GATES]
- Security: [AUTH_REQUIREMENTS]
- Performance: [FROM_PROJECT_MD_OR_DEFAULTS]

## Prompt 7: Tasks to Issues
@speckit.taskstoissues GitHub issues for [FEATURE_NAME]:
- Repository: [REPO_NAME]
- Labels: [feature, domain:[DOMAIN], priority:[HIGH|MEDIUM|LOW]]
- Milestone: [VERSION_OR_SPRINT]
- Assignee: [FROM_CONTEXT_OR_BLANK]

## Prompt 8: Analyze
@speckit.analyze Validate [FEATURE_NAME] against constitution:
- Principles check: [LIST_RELEVANT_PRINCIPLES]
- Convention compliance: [DISCOVERED_PATTERNS]
- Conflict detection: [ANY_DEVIATIONS]

## Prompt 9: Implement
@speckit.implement Code [FEATURE_NAME]:
- Conventions: [FROM_CONSTITUTION]
- Testing: [FRAMEWORK_FROM_PROJECT_MD]
- Examples: [SIMILAR_FILES_DISCOVERED]
- Entry point: [STARTING_FILE_PATH]

## Prompt 10: Archive
@speckit.archive Complete [FEATURE_NAME]:
- Validation: [CHECKLIST_ITEMS]
- Documentation: [README_UPDATES]
- Promotion: [DEPLOY_CRITERIA_FROM_CONSTITUTION]
```

### Prompt Priority Guide
| Scenario | Start With | Skip |
|----------|------------|------|
| Greenfield + no governance | Prompt 1 | None |
| Greenfield + governance ready | Prompt 2 | Prompt 1 |
| Extension/Upgrade | Prompt 2 | Prompt 1 (usually) |
| Refactor | Prompt 4 | Prompts 1-3 (usually) |
| Ambiguous request | Prompt 3 | Hold others until resolved |

## Quality Gates

### Pre-Output Verification
Before generating final output, confirm:
1. **Tool execution**: Did semantic_search, grep_search, read_file all run?
2. **Placeholder check**: Scan all prompts for `[PLACEHOLDER]` patterns
3. **Type determination**: Is feature type in {GREENFIELD, EXTENSION, UPGRADE, REFACTOR}?
4. **Stack specification**: Is tech stack concrete or user explicitly prompted?
5. **Path validation**: Do referenced file paths exist in codebase?

### Output Format Compliance
- Summary block: 4 lines exactly (Request, Type, Tech, Governance)
- Enriched description: 1-3 paragraphs, no placeholders
- Prompts: All 10 present OR marked `SKIP: [reason]`
- Final line: `✅ START: Copy prompt #[N] and run it`

## Error Escalation

| Error | Severity | Response |
|-------|----------|----------|
| Git conflicts | CRITICAL | ABORT, show conflict files |
| Both governance missing | HIGH | Continue with [NO_GOVERNANCE] flags |
| Empty search results | MEDIUM | Confirm GREENFIELD, proceed |
| Partial governance | LOW | Note gaps, use fallbacks |
| Ambiguous feature type | LOW | Default EXTENSION if any code exists |
