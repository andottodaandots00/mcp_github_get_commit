---
name: optimizeAgentInstructions
description: Strategic guidance for analyzing agents and generating complementary instruction files
applyTo: "**/*.agent.md"
---

# Agent Instruction Generator - Strategic Guide

This guide provides strategic judgment and pattern recognition to complement the optimize.agent.md execution workflow. Use this to understand the "why" behind each analysis decision.

---

## Before You Begin: Pre-Flight Checklist

**Mental preparation before starting analysis:**

- [ ] **Clear objective**: Generate instructions that COMPLEMENT (not duplicate) the agent
- [ ] **Time estimate**: Budget 5-10 minutes for thorough analysis
- [ ] **Success criteria**: Instruction file fills gaps, zero redundancy, evidence-based
- [ ] **Failure modes**: Know when to abort (< 20 lines, no structure, malformed)

**Question to ask yourself**:
> "What does this agent ASSUME I know, that isn't written down?"

That's what the instruction file should contain.

---

## 1. Analysis Strategy: What to Look For

### 1.1: Big Picture First

**Don't start with details. Start with purpose.**

**Ask**:
- What problem does this agent solve?
- Who is the user? (Developer, AI, automated system?)
- What's the happy path? (Ideal execution from start to finish)
- What's the design philosophy? (Rigid vs flexible, autonomous vs guided)

**How to find answers**:
1. Read description in frontmatter - that's the "why"
2. Scan all phase headers - that's the "what"
3. Look at constraints table - that's the "limits"
4. Trace input to output - that's the "flow"

**Time budget**: Spend 30% of analysis time on big picture.

---

### 1.2: What Makes THIS Agent Unique

**Every agent has quirks. Find them.**

**Generic agent traits** (ignore these):
- Uses search tools
- Creates files
- Has error handling
- Follows phases

**Unique agent traits** (document these):
- Specific decision matrices (classification tables)
- Unusual routing logic (skip phases conditionally)
- Domain-specific patterns (search for exact strings)
- Novel workflows (synthesize before searching)

**Red flag if you can't answer**:
> "What would I do differently if I had to implement this agent?"

If answer is "nothing, it's generic" → look deeper or agent may be self-sufficient.

---

### 1.3: Patterns Only Visible Holistically

**Some knowledge emerges only when reading the whole agent.**

**Look for**:
- **Recurring themes**: Same validation repeated across phases
- **Implicit contracts**: Phase 2 output must have X for Phase 3 to work
- **Hidden dependencies**: Phase 4 assumes Phase 2 built a mental model
- **Progressive refinement**: Each phase narrows scope

**Example** (from optimize.agent.md):
- Phases 2-4 build classification, Phase 4 uses it to select strategy
- This contract isn't explicit - it's discovered by reading all phases
- Instruction file should clarify: "Phase 4 depends on complete Phase 3 classification"

---

### 1.4: Gaps vs Intentional Omissions

**Not every silence is a gap.**

**True gaps** (add to instructions):
- Agent says "analyze file" but not what to do if file is 10,000 lines
- Agent says "classify" but not how to handle hybrid/ambiguous cases
- Agent says "generate" but not minimum quality thresholds

**Intentional omissions** (leave silent):
- Agent doesn't specify which text editor to use (irrelevant)
- Agent doesn't explain how tools work (not agent's job)
- Agent doesn't define what "file" means (assumed knowledge)

**Heuristic**:
> If omission could cause agent to fail or produce inconsistent output → Gap
> If omission is about general knowledge or tool mechanics → Intentional

---

## 2. Classification Strategy: Decision-Making

### 2.1: Why Classification Matters

**Classification drives strategy selection.**

**Core principle**:
- What agent ALREADY DOES → don't add to instructions
- What agent LACKS based on classification → add to instructions

**Example**:
- High autonomy agent lacks: Guardrails, stop conditions
- Low autonomy agent lacks: Continuation triggers, defaults

---

### 2.2: Handling Hybrid Classifications

**Most agents don't fit cleanly into one category.**

**When agent is hybrid**:
1. **Document both positions**
   - "High autonomy in Phases 1-3, Low autonomy in Phase 4"

2. **Apply strategies for each**
   - Add guardrails for autonomous phases
   - Add triggers for guided phases

3. **Note potential conflicts**
   - "Phase 3's fixed rules may conflict with Phase 5's adaptive behavior"

**Red flag**:
> Agent classified as "Medium" on all dimensions = you didn't look hard enough.

Most agents lean one way or another. Find the lean.

---

### 2.3: Evidence-Based Classification

**Every classification claim needs evidence.**

**Good evidence**:
- Direct quote from agent showing autonomy level
- Tool call that proves discovery-heavy
- Phase count indicating orchestration complexity
- Decision table showing deterministic logic

**Bad evidence**:
- "It seems like..." (too vague)
- "Usually agents..." (generic, not THIS agent)
- "I think..." (opinion, not evidence)

**Format**:
```
├─ Autonomy: High
│  └─ Evidence: "Automatically proceeds through all phases" (Phase 1, line 45)
```

Not:
```
├─ Autonomy: High
│  └─ Evidence: It's pretty autonomous
```

---

### 2.4: Classification Quick Reference

| Dimension | High | Medium | Low |
|-----------|------|--------|-----|
| **Autonomy** | "automatically", "proceeds", no user prompts | Mix of auto and manual steps | "ask user", "confirm", "wait for" |
| **Predictability** | Fixed tables, exact patterns, same I/O | Some flexibility, context-aware | semantic_search, adaptive, varies |
| **Primary Mode** | 3+ search tools, exploration dominant | Balanced search and create | 3+ create tools, generation dominant |
| **Complexity** | 5+ phases, dependencies, branching | 3-4 phases, some dependencies | 1-2 phases, linear flow |

---

## 3. The Soulmate Principle: Avoiding Redundancy

### 3.1: What "Complement" Really Means

**Complement** ≠ Summarize
**Complement** ≠ Repeat in different words
**Complement** = Fill gaps the agent doesn't cover

**Metaphor**: 
- Agent is the map
- Instructions are the compass
- Map shows the route, compass shows which way is north when route is unclear

---

### 3.2: Redundancy Detection Process

**For each potential instruction:**

1. **Extract key concept**
   - Example: "Verify output before creating file"

2. **Search agent for same concept**
   ```
   grep_search(query="verify|validation|check", includePattern="**/optimize.agent.md")
   ```

3. **Evaluate matches**
   - Exact match? → REDUNDANT, skip
   - Partial match? → Check if instruction adds new info
   - No match? → GAP, add to instructions

4. **Document decision**
   - "Skipped 'verify output' - already in Phase 7, lines 280-290"
   - "Added 'verify intermediate state' - not covered by agent"

---

### 3.3: The 80/20 Overlap Rule

**Some overlap is acceptable if value is added.**

**Acceptable overlap** (20%):
- Agent mentions concept briefly, instruction provides detailed procedure
- Agent covers happy path, instruction covers edge cases
- Agent is implicit, instruction makes explicit

**Unacceptable overlap** (80%):
- Agent has detailed table, instruction repeats same table
- Agent has step-by-step, instruction re-explains same steps
- Agent has examples, instruction provides same examples

**Test**:
> If I removed this instruction, would agent still work correctly?
> - Yes → probably redundant
> - No → filling a gap

---

### 3.4: Common Redundancy Traps

**Trap 1: Rephrasing**
- Agent: "Search for IF statements"
- Instruction: "Look for conditional branches (IF)" ← REDUNDANT

**Trap 2: Obvious implications**
- Agent: "Generate instruction file with sections"
- Instruction: "Create a file with content" ← REDUNDANT

**Trap 3: Generic advice**
- Agent: [any workflow]
- Instruction: "Be thorough and careful" ← REDUNDANT + USELESS

**Trap 4: Tool mechanics**
- Agent: "Use grep_search to find patterns"
- Instruction: "grep_search syntax: query, isRegexp" ← WRONG SCOPE

**How to avoid**: After writing each instruction, search agent for that concept. If found, either skip it or add genuinely new information.

---

## 4. Strategic Instruction Building

### 4.1: Context Section Strategy

**Purpose**: External knowledge agent can't contain.

**What belongs here**:
- Project-specific file locations (`.github/` directory structure)
- Related files and their purposes (constitution.md defines rules)
- Environment assumptions (VS Code workspace, tool availability)
- User preferences (line length limits, naming conventions)

**What doesn't belong here**:
- How the agent works (that's in the agent)
- General programming concepts (assumed knowledge)
- Tool documentation (external reference)

**Quality test**:
> Could this context change per project/environment?
> - Yes → belongs in Context
> - No → probably redundant or out of scope

---

### 4.2: Execution Boundaries Strategy

**Purpose**: Limits and guardrails the agent doesn't enforce.

**Derive from classification**:
- **High autonomy** → Add stop conditions, timeouts, scope limits
- **Orchestrated** → Add phase-level boundaries
- **Discovery-heavy** → Add "enough data" criteria

**Examples** (based on classify):
```
High Autonomy Agent:
├─ Time Limits: Max 5 minutes total execution
├─ Iteration Limits: Max 3 retries per phase
└─ Scope Limits: Analyze files <= 1000 lines

Orchestrated Agent:
├─ Phase 1: Must complete in 30 seconds
├─ Phase 2-4: Max 2 minutes combined
└─ Abort if any phase fails twice

Discovery-Heavy Agent:
├─ Search Results: Stop after 50 matches
├─ File Reads: Max 10 files per search
└─ Token Limit: 10,000 tokens per analysis
```

**Red flag**: Boundaries that agent already enforces → redundant.

---

### 4.3: Gap Coverage Strategy

**Purpose**: Handle scenarios agent doesn't explicitly address.

**Source**: Phase 2.7 gap analysis from agent execution.

**Structure pattern**:
```markdown
### When [Scenario Agent Doesn't Handle]
**Situation**: [Describe the gap]
**Behavior**: [What to do instead]
**Rationale**: [Why this approach]
```

**Example**:
```markdown
### When Classification Is Ambiguous (Hybrid)
**Situation**: Agent scores "Medium" on autonomy - neither clearly high nor low
**Behavior**: 
1. Document both possible positions
2. Apply strategies for both High and Low autonomy
3. Note which phases lean which direction
**Rationale**: Hybrid agents need dual strategy to cover both behaviors
```

**Quality test**:
> Is this scenario plausible during agent execution?
> Does agent already handle this?
> - Both yes → add to instructions
> - First no → too contrived, skip
> - Second yes → redundant, skip

---

### 4.4: Quality Gates Strategy

**Purpose**: Verification steps before output, beyond what agent checks.

**Derive from agent's verification phase**:
1. List what agent DOES check (from Phase 7)
2. Identify what agent DOESN'T check
3. Add missing checks to instructions

**Example** (from optimize.agent.md):
```
Agent checks:
- Zero redundancy with agent content
- ApplyTo pattern matches filename

Agent doesn't check:
- Instruction quality (too vague, too generic)
- Line length (some instructions too terse)
- Example quality (are examples realistic?)

Add to instructions:
- Min 20 words per instruction (not too terse)
- Every instruction has concrete example
- Examples cite real agent line numbers
```

**Red flag**: Quality gate that duplicates agent's Phase 7 checks → redundant.

---

## 5. Common Pitfalls & How to Avoid Them

### 5.1: Pitfall: Analysis Paralysis

**Symptom**: Spending 20+ minutes on Phase 2, reading agent 5+ times.

**Cause**: Trying to understand every detail before proceeding.

**Solution**: 
- First pass: Big picture (5 min)
- Second pass: Decision points and gaps (5 min)
- Third pass: Only if gaps unclear (3 min)
- **Total**: 13 minutes maximum

**Mantra**: "Good enough to classify is good enough to proceed."

---

### 5.2: Pitfall: Generic Instruction Syndrome

**Symptom**: Instructions could apply to ANY agent.

**Examples**:
- "Handle errors gracefully"
- "Think step by step"
- "Be thorough and accurate"
- "Follow best practices"

**Cause**: Not grounding instructions in THIS agent's specifics.

**Solution**:
- Every instruction must cite agent section/line
- Every instruction must use agent's terminology
- Every instruction must address agent's specific workflow

**Test**: 
> Could I apply this instruction to a different agent?
> - Yes → too generic, make specific
> - No → good, it's tailored

---

### 5.3: Pitfall: Instruction Creep

**Symptom**: Instruction file reaches 300+ lines, exceeds agent length.

**Cause**: Adding nice-to-have instead of only need-to-have.

**Solution**:
- Prioritize by classification (autonomy → boundaries, etc.)
- Remove anything agent already says
- Consolidate similar instructions
- **Hard stop** at 200 lines

**Priority order**:
1. Context (environment, project-specific)
2. Gap Coverage (critical failures agent doesn't handle)
3. Execution Boundaries (guardrails for autonomous agents)
4. Quality Gates (verification beyond agent's checks)
5. Error Escalation (only if agent has error paths)

Cut from bottom up if over 200 lines.

---

### 5.4: Pitfall: Classification Laziness

**Symptom**: All dimensions classified as "Medium" or "Balanced".

**Cause**: Not looking for evidence, going with safe middle ground.

**Solution**:
- Force yourself to choose High or Low first
- Only use Medium if genuinely torn with equal evidence
- Provide specific evidence (quote + line number) for each

**Rule of thumb**: 
- At least 2 dimensions should be High or Low
- If all Medium → you haven't analyzed deeply enough

---

### 5.5: Pitfall: Ignoring Agent's Voice

**Symptom**: Instructions use different terminology than agent.

**Examples**:
- Agent: "ABORT" → Instruction: "Stop execution"
- Agent: "Phase" → Instruction: "Step"
- Agent: "Tool Chain" → Instruction: "Tool dependencies"

**Cause**: Writing instructions without agent open for reference.

**Solution**:
- Mirror agent's terminology exactly
- Use agent's section names when referencing
- Adopt agent's formatting conventions (tables, reports)

**Benefit**: Instructions feel like natural extension of agent, not separate document.

---

## 6. Quality Signals: Knowing When You're Done

### 6.1: Positive Signals (Analysis is Complete)

- [ ] **Can explain agent's purpose in one sentence**
- [ ] **Can trace execution path without re-reading**
- [ ] **Have identified 3+ specific gaps agent doesn't handle**
- [ ] **Classification has evidence for each dimension**
- [ ] **Can distinguish this agent from similar agents**
- [ ] **Found patterns only visible by reading whole agent**

**If 5+ checked**: Proceed to instruction generation.
**If < 4 checked**: Continue analysis.

---

### 6.2: Positive Signals (Instruction File is Complete)

- [ ] **Every instruction cites agent section/line**
- [ ] **No instruction could apply to different agent**
- [ ] **Searched agent for each concept, found no redundancy**
- [ ] **All gaps from analysis are addressed**
- [ ] **File is 100-200 lines (not too short, not too long)**
- [ ] **Each section has concrete examples from agent**
- [ ] **Could use instructions to execute agent successfully**

**If 6+ checked**: Proceed to verification.
**If < 5 checked**: Revise instruction file.

---

### 6.3: Negative Signals (Need More Work)

**Analysis phase**:
- ❌ "I'm not sure what this agent does"
- ❌ "It seems like a standard agent"
- ❌ "Can't find any unique patterns"
- ❌ "Don't see any gaps to fill"

**Solution**: Re-read with focus on:
- Decision points (IF, ABORT, SKIP)
- Constraints tables (MUST, NEVER)
- Phase dependencies (what each needs from previous)

---

**Instruction phase**:
- ❌ "These instructions could apply to any agent"
- ❌ "Can't cite specific agent sections"
- ❌ "Instructions mostly repeat what agent says"
- ❌ "File is only 50 lines" or "File is 300 lines"

**Solution**: 
- Ground every instruction in agent specifics
- Remove redundancy aggressively
- Add more gap coverage if too short
- Consolidate if too long

---

## 7. Reference Document Nuances

**When input is constitution.md, project.md, or governance document:**

### 7.1: Different Analysis Approach

**Agent analysis** = How does it execute?
**Document analysis** = What information does it contain?

**Key differences**:
- No workflow to trace → Map sections instead
- No tools to identify → Identify data points instead
- No gaps to find → Identify consumers instead

### 7.2: Structure Mapping Priority

**Most important**: Create accurate section map with line numbers.

**Why**: Agents need to quickly locate specific sections.

**Template**:
```markdown
## Document Structure Map
constitution.md (250 lines)
├─ ## Principles (lines 1-50)
│  ├─ Core values
│  └─ Design philosophy
├─ ## Constraints (lines 51-120)
│  ├─ MUST rules (lines 55-80)
│  └─ MUST NOT rules (lines 81-120)
└─ ## Validation (lines 121-250)
   ├─ Severity levels (lines 125-150)
   └─ Compliance checklist (lines 151-250)
```

### 7.3: Consumer Identification Strategy

**Critical**: Know which agents use this document.

**Method**:
```
grep_search(query="constitution.md", includePattern="**/*.agent.md")
```

**Document usage pattern**:
- **Lookup**: Agent reads specific sections on demand
- **Validation**: Agent checks compliance before output
- **Context**: Agent uses as reference throughout

**Add to instructions**: How each consumer uses document.

---

## 8. Iterative Refinement

### 8.1: First Draft Philosophy

**First draft should be**:
- Complete (all sections)
- Specific (cites agent)
- Honest (notes uncertainties)

**First draft should NOT be**:
- Perfect (will revise)
- Polished (focus on content)
- Exhaustive (within line budget)

**Mantra**: "Ship first draft, refine based on verification."

---

### 8.2: Revision Triggers

**Revise when verification reveals**:
- Redundancy detected (found in agent)
- Gap missing (Phase 2.7 gap not covered)
- Ungrounded instruction (no agent citation)
- Wrong applyTo pattern (doesn't match filename)

**Don't revise when**:
- Preference disagreement ("I'd word it differently")
- Style concerns ("Tables vs lists")
- Length within range ("Could be 120 lines instead of 140")

**Focus revisions**: Content accuracy, not presentation polish.

---

### 8.3: The 2-Attempt Rule

**Why 2 attempts maximum?**

1. **First attempt**: Honest effort based on analysis
2. **Second attempt**: Fix verification failures
3. **Third attempt** (if needed): ABORT - indicates fundamental misunderstanding

**If reaching 3rd attempt**:
- Report gaps clearly
- Request user clarification
- Don't guess - abort safely

**Mantra**: "Two tries and fly, or abort and report."

---

## 9. Meta-Patterns Across All Agents

### 9.1: Universal Gaps to Look For

**Regardless of agent type, check if these are covered**:

- **Error handling**: What if tool fails?
- **Input validation**: What if input malformed?
- **Output validation**: What if output empty?
- **Resource limits**: What if file too large?
- **Timeout handling**: What if execution too slow?
- **Retry logic**: How many attempts before abort?

**If agent doesn't explicitly handle** → Add to instructions.

---

### 9.2: Classification Correlation Patterns

**Observed correlations** (from many agent analyses):

- High Autonomy + High Determinism → Often needs edge case handling
- High Autonomy + Orchestrated → Often needs state checkpoints
- Low Autonomy + Adaptive → Often needs default behaviors
- Discovery + Adaptive → Often needs stopping criteria
- Synthesis + Deterministic → Often needs source validation

**Use these as hints**, not rules. Verify with evidence from THIS agent.

---

### 9.3: Instruction File Naming Consistency

**Pattern**: `{agent-base-name}.instructions.md`

**Examples**:
- `optimize.agent.md` → `optimize.instructions.md`
- `speckit.document.agent.md` → `speckit-document.instructions.md`
- `validate-output.agent.md` → `validate-output.instructions.md`

**Rule**: Preserve agent name structure, replace `.agent` with `.instructions`.

---

## 10. Final Wisdom

### The Core Questions

Before generating instructions, answer these:

1. **What does this agent assume I know?**
   → That's Context section

2. **When would this agent fail or behave inconsistently?**
   → That's Gap Coverage section

3. **How do I know when to stop this agent?**
   → That's Execution Boundaries section

4. **How do I know the agent succeeded?**
   → That's Quality Gates section

If you can't answer all four clearly → Analysis incomplete.

---

### The Golden Rule

> "The instruction file should be the agent's best friend - knows everything about it, never repeats what it says, always has its back when things go wrong."

---

### When to Report "Agent is Self-Sufficient"

**Valid reasons**:
- Agent is < 50 lines, very simple, single task
- Agent explicitly handles all error cases
- Agent has comprehensive validation
- Agent's scope is so narrow that external guidance is unnecessary

**Invalid reasons**:
- "I can't find any gaps" (look harder)
- "Analysis is hard" (not a reason)
- "Don't want to write instructions" (not acceptable)

**Genuine self-sufficient agents are rare** (< 5%). Most agents benefit from instructions.

---

### Trust the Process

**The optimize.agent.md workflow is designed to:**
- Force systematic analysis (Phases 1-2)
- Drive classification (Phase 3)
- Guide strategy (Phase 4)
- Structure generation (Phase 6)
- Ensure quality (Phase 7)

**Trust it**. Follow phases in order. Don't skip steps.

**Result**: High-quality instruction files that genuinely complement agents.

---

## Appendix: Quick Decision Trees

### Should This Go in Instructions?

```
Is it already in the agent?
├─ Yes → Is instruction adding new info?
│  ├─ Yes (edge case, detail, example) → ADD
│  └─ No (restating same thing) → SKIP (redundant)
└─ No → Is it relevant to agent execution?
   ├─ Yes → ADD
   └─ No → SKIP (out of scope)
```

### Which Section Does This Belong In?

```
What type of information?
├─ External/environmental → Context
├─ Limits/guardrails → Execution Boundaries
├─ Unhandled scenario → Gap Coverage
├─ Quality check → Quality Gates
└─ Error severity → Error Escalation (optional)
```

### Should I Abort Analysis?

```
Can I classify the input type?
├─ No → ABORT (unrecognized)
└─ Yes → Is structure clear?
   ├─ No → ABORT (malformed)
   └─ Yes → Is there enough content?
      ├─ No (< 20 lines) → ABORT (too short)
      └─ Yes → PROCEED with analysis
```

---

**End of Strategic Guide**

Use this guide alongside optimize.agent.md to produce exceptional instruction files that truly complement their agents.
