---
description: External context, recovery procedures, and output format for speckit.document agent
applyTo: "**/speckit.document.agent.md"
---

# SpecKit Document - Execution Instructions

## Purpose
This file provides **external context** and **edge case handling** the agent needs but doesn't contain.
Agent defines WHAT to do. This file defines HOW to handle gaps and format output.

---

## Output Format Template

Use this exact template for all feature analysis output:

```
═══════════════════════════════════════════════════════════
📊 FEATURE ANALYSIS: [Name]
═══════════════════════════════════════════════════════════

[PHASE 1-8 REPORTS - from agent execution]

═══════════════════════════════════════════════════════════
🚀 SPECKIT WORKFLOW PROMPTS
═══════════════════════════════════════════════════════════

### 1. /speckit.constitution.prompt.md
[Status: REQUIRED | AMEND | SKIP - reason with evidence]

[Rich paragraph with governance gap analysis. If AMEND/REQUIRED: describe
specific gaps (new patterns, new tech, conflicts). If SKIP: cite exact
principles from constitution.md that cover this feature (with line numbers
or principle names). NEVER skip without concrete evidence.]

---

### 2. /speckit.specify.prompt.md
[Status: REQUIRED]

[Rich paragraph containing: feature name, discovered file paths
to reference as patterns, type definitions found, tech stack
specifics with versions, expected operations, related entities]

---

### 3. /speckit.clarify.prompt.md
[Status: REQUIRED | SKIP - reason]

[Rich paragraph listing specific questions from analysis OR
skip reason explaining why no ambiguities exist]

---

### 4. /speckit.plan.prompt.md
[Status: REQUIRED]

[Rich paragraph containing: folder structure from discovered
patterns, file naming conventions, component architecture,
integration points, new file paths to create]

---

### 5. /speckit.tasks.prompt.md
[Status: REQUIRED]

[Rich paragraph containing: phase breakdown, dependencies,
files to create/modify with paths, testing requirements,
integration milestones]

---

### 6. /speckit.checklist.prompt.md
[Status: REQUIRED]

[Rich paragraph containing: functional requirements, technical
requirements from governance, quality gates, testing coverage,
accessibility/performance criteria]

---

### 7. /speckit.taskstoissues.prompt.md
[Status: REQUIRED | SKIP - reason]

[Rich paragraph containing: repository context, suggested labels,
milestone assignment, issue breakdown strategy]

---

### 8. /speckit.analyze.prompt.md
[Status: REQUIRED]

[Rich paragraph containing: constitution principles to validate,
convention compliance checks, pattern adherence verification]

---

### 9. /speckit.implement.prompt.md
[Status: REQUIRED]

[Rich paragraph containing: entry point file path, reference
files with specific paths, code conventions, testing framework,
import structure to follow]

---

### 10. /speckit.archive.prompt.md
[Status: REQUIRED]

[Rich paragraph containing: validation checklist, documentation
updates, promotion criteria, archive location]

═══════════════════════════════════════════════════════════
▶ NEXT: Copy prompt #[first-applicable] and invoke
        /speckit.[name].prompt.md
═══════════════════════════════════════════════════════════
```

---

## Project-Specific Context

### When Searches Return Unexpected Results

**Too many results (50+)**:
```
1. DO NOT just pick first 5
2. ADD domain qualifier to narrow: "{domain} component|hook"
3. SCOPE by directory: includePattern: "src/{domain}/**"
4. IF still too many → read types files first (highest signal)
```

**Zero results**:
```
1. TRY case variants: "wizard|Wizard|WIZARD"
2. TRY singular/plural: "form|forms"
3. CHECK package.json for related package names
4. IF still zero → CONFIRM greenfield, document assumption
```

### When Governance Files Are Missing/Template

**Constitution missing or template**:
```
1. READ .github/copilot-instructions.md (fallback #1)
2. READ README.md (fallback #2)
3. EXTRACT any principles or rules found
4. MARK Prompt #1 as REQUIRED
5. NOTE in output: "Constitution needs initialization"
```

**Project.md missing or template**:
```
1. READ package.json
2. EXTRACT: dependencies, devDependencies versions
3. INFER tech stack: React version, TypeScript version, etc.
4. NOTE in output: "Tech stack inferred from package.json"
```

---

## Project-Specific Context

### Canonical Pattern Source
All wizard forms MUST reference `src/components/forms/sell-like-builders/` as the canonical pattern:
- `WizardCard.tsx` - Card container with BorderBeam
- `WizardProgress.tsx` - Circular progress indicator
- `WizardNavigation.tsx` - Back/Next/Submit buttons
- `SellLikeBuildersWizard.tsx` - Orchestration pattern

### Required Imports (Not Duplication)
Per constitution Principle IX, shared components must be IMPORTED:
```typescript
// ✅ CORRECT
import { WizardCard, WizardProgress, WizardNavigation } from '@/components/forms/sell-like-builders';

// ❌ WRONG - Creating duplicate implementations
// src/components/forms/my-form/WizardCard.tsx (DO NOT CREATE)
```

### Color Scheme Constants
All wizard forms use these exact colors:
- Background: `bg-[#030d30]` (dark navy)
- Border: `border-[#7882b4]` (muted blue-gray)
- Submit button: `bg-[#d91e2b]` (LoanARK red)
- Progress primary: `#d91e2b`

---

## Governance Gap Detection Examples

### Example 1: New Pattern Detected
**Scenario**: User wants to create a "server action" form handler
**Constitution check**: Search for "server action", "server component", "React Server Components"
**Result**: Not mentioned in constitution
**Action**: AMEND - add principle for server-side patterns

### Example 2: New Technology Introduced
**Scenario**: Feature uses Prisma ORM (not in existing codebase)
**Constitution check**: Search for "Prisma", "ORM", "database"
**Result**: Constitution only covers Zod validation, no database principles
**Action**: AMEND - add database interaction principles

### Example 3: Architecture Change
**Scenario**: Feature needs real-time WebSocket updates
**Constitution check**: Search for "WebSocket", "real-time", "subscription"
**Result**: Constitution assumes REST APIs only
**Action**: AMEND - add real-time communication principles

### Example 4: Quality Standard Missing
**Scenario**: Feature includes AI-generated content
**Constitution check**: Search for "AI", "LLM", "generation", "content validation"
**Result**: No principles for AI-generated content validation
**Action**: AMEND - add AI content quality gates

### Example 5: Existing Principle Conflicts
**Scenario**: Feature duplicates wizard components (violates Principle IX)
**Constitution check**: Principle IX exists: "Pattern Library Discipline"
**Result**: Feature violates existing principle
**Action**: AMEND - strengthen enforcement or document exceptions

### Example 6: Truly Covered (SKIP is valid)
**Scenario**: Create new wizard form following SLB pattern
**Constitution check**:
- Principle IX: "Import shared components, don't duplicate" ✅
- Principle VII: "Dark theme color scheme constants" ✅
- Principle III: "Zod validation for all forms" ✅
**Result**: All aspects covered by existing principles
**Action**: SKIP - cite "Principles III, VII, IX cover wizard form patterns"

---

## Gap Coverage

### When Searches Return Unexpected Results

**Too many results (50+)**:
```
1. DO NOT just pick first 5
2. ADD domain qualifier to narrow: "{domain} component|hook"
3. SCOPE by directory: includePattern: "src/{domain}/**"
4. IF still too many → read types files first (highest signal)
```

**Zero results**:
```
1. TRY case variants: "wizard|Wizard|WIZARD"
2. TRY singular/plural: "form|forms"
3. CHECK package.json for related package names
4. IF still zero → CONFIRM greenfield, document assumption
```

### When Governance Files Are Missing/Template

**Constitution missing or template**:
```
1. READ .github/copilot-instructions.md (fallback #1)
2. READ README.md (fallback #2)
3. EXTRACT any principles or rules found
4. MARK Prompt #1 as REQUIRED
5. NOTE in output: "Constitution needs initialization"
```

**Project.md missing or template**:
```
1. READ package.json
2. EXTRACT: dependencies, devDependencies versions
3. INFER tech stack: React version, TypeScript version, etc.
4. NOTE in output: "Tech stack inferred from package.json"
```

---

## Recovery Procedures

### If Phase 4 Produces < 5 Files
```
1. EXPAND search scope (remove directory filter)
2. TRY broader semantic query
3. LOOK for similar features (other forms, other wizards)
4. IF still < 5 → Proceed with [LIMITED_CONTEXT] warning
```

### If Placeholder Detected in Draft Output
```
1. IDENTIFY which placeholder: [TECH_STACK], [FILE_PATH], etc.
2. RETURN to relevant phase:
   - [TECH_STACK] → Re-read package.json
   - [FILE_PATH] → Re-run Phase 4 searches
   - [PATTERN] → Re-read similar feature files
3. REPLACE placeholder with concrete value
4. RE-VALIDATE before output
```

### If Output Rejected at Gate 3
```
1. IDENTIFY which check failed
2. FIX specific failure:
   - Placeholder → Replace with real value
   - Short prompt → Add sentences with context
   - Missing path → Add path from Phase 4
3. RE-RUN Gate 3 validation
4. MAX 2 revision attempts, then output with warnings
```

---

---

## Recovery Procedures

### If Phase 4 Produces < 5 Files
```
1. EXPAND search scope (remove directory filter)
2. TRY broader semantic query
3. LOOK for similar features (other forms, other wizards)
4. IF still < 5 → Proceed with [LIMITED_CONTEXT] warning
```

### If Placeholder Detected in Draft Output
```
1. IDENTIFY which placeholder: [TECH_STACK], [FILE_PATH], etc.
2. RETURN to relevant phase:
   - [TECH_STACK] → Re-read package.json
   - [FILE_PATH] → Re-run Phase 4 searches
   - [PATTERN] → Re-read similar feature files
3. REPLACE placeholder with concrete value
4. RE-VALIDATE before output
```

### If Gate Validation Fails
```
1. IDENTIFY which gate failed (Gate 1, 2, or 3)
2. FIX specific failure:
   - Gate 1 (files) → Read more files, expand scope
   - Gate 2 (quality) → Replace placeholders, add specifics
   - Gate 3 (output) → Add paths, extend sentences
3. RE-RUN gate validation
4. MAX 2 revision attempts, then output with warnings
```

### If Constitution Gap Analysis Is Unclear
```
1. RE-READ constitution.md sections relevant to feature domain
2. SEARCH for keywords from feature in constitution:
   - Feature technology (e.g., "React", "Zod", "API")
   - Feature pattern (e.g., "wizard", "form", "validation")
   - Feature domain (e.g., "authentication", "data", "UI")
3. ASK each gap question explicitly:
   - New pattern? → grep_search constitution for pattern mentions
   - New tech? → grep_search constitution for tech stack section
   - Violations? → compare discovered patterns to principles
4. IF still unclear after search:
   - Default to AMEND (safer to suggest governance update)
   - Document uncertainty in prompt #1
   - List specific areas needing governance clarification
5. NEVER default to SKIP without concrete evidence (quotes from constitution)
```

**Bias toward AMEND**: When in doubt, suggest governance updates. Better to propose unnecessary updates than miss critical governance gaps.

---

## Prompt Quality Examples

### Constitution Prompt Examples

#### ✅ GOOD - AMEND with Specific Gaps
```
[Status: AMEND]

Update the constitution to add governance for wizard pattern migrations. Analysis
revealed four wizard forms (Co-Marketing Flyers, Listing Flyers, Ultimate Buyer,
Let's Get Social) duplicated WizardCard/Progress/Navigation components instead of
importing from src/components/forms/sell-like-builders/ canonical source. Current
Principle IX (Pattern Library Discipline) exists but lacks enforcement guidance
for refactoring violations. Proposed additions: (1) Refactoring protocol for
pattern violations, (2) Visual regression testing requirements when consolidating
duplicates, (3) Migration checklist for forms inheriting from canonical patterns.
```

#### ✅ GOOD - SKIP with Evidence
```
[Status: SKIP - Principles III, VII, IX fully cover wizard forms]

Constitution adequately covers wizard form implementation. Principle IX
(Pattern Library Discipline, lines 89-103) explicitly requires importing
shared components from canonical sources and prohibits duplication. Principle
VII (Design System Consistency, lines 67-78) mandates dark theme colors
(bg-[#030d30], border-[#7882b4], bg-[#d91e2b]) for all wizard forms.
Principle III (Validation Discipline, lines 34-48) requires Zod schemas for
all form validation. No governance gaps detected for standard wizard form creation.
```

#### ❌ BAD - SKIP without Evidence
```
[Status: SKIP]

Constitution looks good, no updates needed.
```
**Failures**: No evidence, no principle citations, no analysis

#### ❌ BAD - Vague AMEND
```
[Status: AMEND]

Update constitution with new patterns and best practices for the feature.
```
**Failures**: No specific gaps, no concrete proposals, generic

---

### Specification Prompt Examples

#### ✅ GOOD - Rich Context (Passes All Gates)
```
Create a specification for the Co-Marketing Flyers wizard form,
following the card-based wizard pattern discovered in
src/components/forms/sell-like-builders/SellLikeBuildersWizard.tsx.
The form should use React 19.0.0 with TypeScript 5.7, Zod 3.24.1 for
validation, and IMPORT WizardCard, WizardProgress, and WizardNavigation
components from sell-like-builders (not duplicate them). Per constitution
Principle IX (Pattern Library Discipline), all shared wizard components
must be imported from the canonical source. Reference Card01_PropertyAddress.tsx
for the address autocomplete pattern with Google Places integration.
```

#### ❌ BAD - Generic (Fails Gates)
```
Create a specification for the Co-Marketing Flyers wizard form,
following the card-based wizard pattern discovered in
src/components/forms/sell-like-builders/SellLikeBuildersWizard.tsx.
The form should use React 19.0.0 with TypeScript 5.7, Zod 3.24.1 for
validation, and IMPORT WizardCard, WizardProgress, and WizardNavigation
components from sell-like-builders (not duplicate them). Per constitution
Principle IX (Pattern Library Discipline), all shared wizard components
must be imported from the canonical source. Reference Card01_PropertyAddress.tsx
for the address autocomplete pattern with Google Places integration.
```

#### ❌ BAD - Generic (Fails Gates)
```
Create a specification for the form using appropriate technology.
Follow existing patterns in the codebase. [NEEDS_FILE_PATHS]
```
**Failures**: No file path, placeholder present, no version numbers, < 3 sentences

---

## Usage Notes

**When to use SKIP status**:
- Constitution prompt: SKIP if constitution.md fully populated AND covers feature domain
- Clarify prompt: SKIP if no ambiguities AND all requirements clear
- Tasks-to-issues prompt: SKIP if user explicitly said "no GitHub issues"

**Tech stack version format**:
- ✅ GOOD: "React 19.0.0", "TypeScript 5.7", "Zod 3.24.1"
- ❌ BAD: "React 19", "TypeScript", "latest Zod"

**File path specificity**:
- ✅ GOOD: "src/components/forms/sell-like-builders/WizardCard.tsx"
- ❌ BAD: "WizardCard component", "the wizard file"

---

## Completion Verification

Before presenting final output, mentally execute:

```
CHECKLIST:
├─ [ ] applyTo in copilot-instructions.md matches agent filename
├─ [ ] 5+ files were read (count read_file calls)
├─ [ ] Zero /\[[A-Z_]+\]/ patterns in output
├─ [ ] Each prompt has ≥ 3 sentences
├─ [ ] Each prompt cites a concrete src/ path
├─ [ ] Tech versions include minor version (e.g., "5.7" not "5")
├─ [ ] SKIP reasons cite specific evidence

IF any unchecked → FIX before output
IF all checked → OUTPUT is valid
```
