---
name: speckit.document-instructions
description: Optimized execution instructions for speckit.document agent
---
# speckit.document - Execution Instructions

## Context

This agent transforms vague feature requests into actionable SpecKit workflow prompts. The agent file defines WHAT to do; this file defines HOW to do it well.

**Actual Tool Requirements** (corrected from agent header):
- `get_changed_files` - git state check
- `semantic_search` - broad codebase discovery
- `grep_search` - exact pattern matching
- `list_code_usages` - entity usage tracing (conditional)
- `file_search` - file pattern matching (conditional)
- `list_dir` - directory structure (conditional)
- `read_file` - governance file reading

## Execution Boundaries

### Phase Timing
- Phases 1-2 (Parse + Context): Complete within first 2 tool calls
- Phases 3-5 (Discovery): Maximum 5 search iterations before proceeding
- Phases 6-7 (Governance + Type): Single read pass per governance file
- Phases 8-9 (Synthesis): Output generation after all discovery complete

### When to Stop Discovery
Proceed to synthesis when ANY of these are true:
- 3+ related files found with consistent patterns
- Entity existence definitively confirmed or denied
- Governance files read and status determined
- 5 search iterations completed without new information

### Success Completion Signal
Output "✅ ANALYSIS COMPLETE - Ready for workflow execution" after validation checklist passes. This signals the user can begin copying prompts.

## Gap Coverage

### Multi-Domain Requests
If user request spans multiple domains (e.g., "Create user management with payment integration"):
1. Identify primary domain (first noun = primary)
2. Generate prompts for primary domain
3. Append note: "Secondary domain [X] requires separate @speckit.document run"

### Ambiguous Classification
If feature type is unclear after Phase 7:
- Default to EXTENSION if any related code exists
- Default to GREENFIELD only if zero matches across all searches
- Never default to ABORT - ask clarifying question instead

### Partial Tool Results
If a tool returns partial/incomplete results:
- `semantic_search` partial → Proceed with available matches, note "Limited search results" in summary
- `grep_search` empty → Confirm greenfield, don't retry with looser patterns
- `read_file` partial → Treat missing sections as "needs definition"

### Governance File Alternatives
If `specs/memory/constitution.md` or `specs/project.md` don't exist:
1. Check for `.github/copilot-instructions.md` as fallback governance
2. Check for `README.md` project conventions
3. If none exist, mark "Governance: REQUIRES SETUP" and make Step 1 mandatory

## Quality Gates

### Before Phase 9 (Prompt Generation)
Verify these are determined (not assumed):
- [ ] Feature type is one of: greenfield/extension/upgrade/refactor (not "unclear")
- [ ] Tech stack is specific (not "various" or "standard")
- [ ] At least one governance file was successfully read
- [ ] No unresolved merge conflicts

### Prompt Quality Threshold
Each generated prompt must:
- Contain zero placeholder tokens (`[FIELD]`, `{VALUE}`, `TBD`)
- Reference at least one specific file, path, or pattern from discovery
- Be executable without additional context gathering

### Output Validation
Before displaying final output:
- Count prompts = exactly 10 (or explicitly marked as SKIP with reason)
- Every prompt starts with correct agent name (`@speckit.X`)
- Summary section contains all 4 fields (Original Request, Feature Type, Tech Stack, Governance)

## Recovery Procedures

### Phase Failure Recovery
| Failed Phase | Recovery Action |
|--------------|-----------------|
| Phase 2 (Context) | Assume clean state, continue |
| Phase 3-4 (Search) | Mark as greenfield, continue |
| Phase 5 (Pinpoint) | Skip, use Phase 3-4 results |
| Phase 6 (Governance) | Mark governance as "REQUIRES SETUP", Step 1 mandatory |
| Phase 7 (Type) | Default to EXTENSION, note uncertainty |
| Phase 8 (Optimize) | Use original query with "[NEEDS ENRICHMENT]" flag |

### User Clarification Triggers
Ask for clarification (don't assume) when:
- User request contains contradictory requirements
- Tech stack cannot be determined from any source
- Feature appears to already exist but request implies new creation
