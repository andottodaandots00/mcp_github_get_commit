## `speckit.document` - FINAL SYNTHESIZED WORKFLOW

---

### **PHASE 1: Parse User Query**

**Input**: Raw user query
```
"Create user management API"
```

**Agent Action**: Parse and identify gaps

| Extracted | Value | Ambiguity? |
|-----------|-------|------------|
| Action | Create | ❌ Clear |
| Object | user management API | ⚠️ Vague - what operations? |
| Type | New feature | ❌ Clear (create = new) |
| Scope | Unknown | ⚠️ CRUD? Auth? Roles? |
| Tech | Unknown | ⚠️ What stack? |

**Output to Self**: Query needs enrichment from codebase context

---

### **PHASE 2: Discover Current Context**

**Tool**: `get_changed_files()`

**Purpose**: What is user currently working on?

```
┌─────────────────────────────────────────────────────────────┐
│ get_changed_files()                                         │
├─────────────────────────────────────────────────────────────┤
│ Returns:                                                    │
│ - Modified files (staged/unstaged)                          │
│ - Recent activity                                           │
│ - Current branch                                            │
│                                                             │
│ WHY FIRST:                                                  │
│ - Immediate context of current work state                   │
│ - Are there pending changes that conflict?                  │
│ - Is there already work in progress on this feature?        │
└─────────────────────────────────────────────────────────────┘
```

---

### **PHASE 3: Broad Codebase Search**

**Tool**: `semantic_search("user management API authentication CRUD")`

**Purpose**: Wide net search - find related code by meaning

```
┌─────────────────────────────────────────────────────────────┐
│ semantic_search("user management API authentication CRUD")  │
├─────────────────────────────────────────────────────────────┤
│ Returns:                                                    │
│ - Related code snippets                                     │
│ - Relevant files by semantic meaning                        │
│ - Similar implementations                                   │
│                                                             │
│ WHY SECOND:                                                 │
│ - Understands intent, not just keywords                     │
│ - Finds related code even if named differently              │
│ - Broad understanding before narrowing down                 │
└─────────────────────────────────────────────────────────────┘
```

---

### **PHASE 4: Narrow Down with Exact Matches**

**Tool**: `grep_search("user|User|auth|jwt|api|controller")`

**Purpose**: Pinpoint exact occurrences

```
┌─────────────────────────────────────────────────────────────┐
│ grep_search("user|User|auth|jwt|controller")                │
├─────────────────────────────────────────────────────────────┤
│ Returns:                                                    │
│ - Exact line matches                                        │
│ - File paths with line numbers                              │
│ - Pattern counts                                            │
│                                                             │
│ WHY THIRD:                                                  │
│ - Confirms what semantic_search found                       │
│ - Exact locations for deeper inspection                     │
│ - Narrows from broad to specific                            │
└─────────────────────────────────────────────────────────────┘
```

---

### **PHASE 5: Pinpoint (If Needed)**

**Tools**: `list_code_usages()`, `file_search()`, `list_dir()`

**Purpose**: Deep dive only if phases 2-4 need more detail

```
┌─────────────────────────────────────────────────────────────┐
│ CONDITIONAL - Only if previous phases need clarification    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ list_code_usages("User")                                    │
│ → How is User entity used across codebase?                  │
│                                                             │
│ file_search("*.controller.ts")                              │
│ → Find specific file patterns                               │
│                                                             │
│ list_dir("src/api/")                                        │
│ → Check specific directory structure                        │
│                                                             │
│ WHY FOURTH:                                                 │
│ - Only when phases 2-4 found something to investigate       │
│ - Deep dive into specific findings                          │
│ - Not always needed                                         │
└─────────────────────────────────────────────────────────────┘
```

---

### **PHASE 6: Read Governance Files**

**Tool**: `read_file()`

**Purpose**: Now apply governance to findings

```
┌─────────────────────────────────────────────────────────────┐
│ read_file("specs/memory/constitution.md")                   │
│ read_file("specs/project.md")                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ From constitution.md:                                       │
│ - What principles must this feature follow?                 │
│ - What quality standards apply?                             │
│ - What validation gates exist?                              │
│ - Is constitution populated or template?                    │
│                                                             │
│ From project.md:                                            │
│ - What tech stack is defined?                               │
│ - What code conventions apply?                              │
│ - What folder structure to follow?                          │
│ - What architecture patterns?                               │
│ - Is project.md populated or template?                      │
│                                                             │
│ WHY LAST:                                                   │
│ - Now you know WHAT exists in codebase                      │
│ - Apply governance rules to your findings                   │
│ - Determine if governance needs updating                    │
└─────────────────────────────────────────────────────────────┘
```

---

### **PHASE 7: Determine Feature Type & Governance Needs**

**Agent Action**: Analyze findings and decide approach

```
┌─────────────────────────────────────────────────────────────┐
│ FEATURE TYPE DECISION                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ IF no user code found:                                      │
│    → GREENFIELD (new implementation)                        │
│                                                             │
│ IF user entity exists BUT no API:                           │
│    → EXTENSION (add API layer)                              │
│                                                             │
│ IF user API exists BUT incomplete:                          │
│    → UPGRADE (add missing features)                         │
│                                                             │
│ IF user API exists, needs fixes:                            │
│    → REFACTOR (improve existing)                            │
│                                                             │
│ IF user API fully exists:                                   │
│    → ABORT (clarify what's actually needed)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ GOVERNANCE NEEDS DECISION                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ CONSTITUTION:                                               │
│ - Populated? → Check if principles cover this feature       │
│ - Template? → Must prompt full constitution setup           │
│ - Missing principles? → Prompt amendments                   │
│                                                             │
│ PROJECT.MD:                                                 │
│ - Populated? → Use tech stack for prompts                   │
│ - Template? → Must prompt setup OR ask user to choose       │
│ - New tech needed? → Prompt project.md update               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### **PHASE 8: Optimize User Query**

**Agent Action**: Rewrite vague query with discovered context

```
ORIGINAL (vague):
"Create user management API"

OPTIMIZED (enriched with discovered context):
"Create RESTful User Management API with:
- Endpoints: CRUD operations (GET/POST/PUT/DELETE /api/users)
- Auth: JWT tokens (from existing auth.ts pattern)
- Database: PostgreSQL + Prisma (from project.md)
- Structure: Controller→Service→Repository (from project.md)
- Validation: Zod schemas (from project.md)
- Testing: Vitest (from project.md)
- Security: bcrypt, rate limiting (from constitution)"
```

---

### **PHASE 9: Output to Chat**

**Agent Action**: Generate analysis + 10 sequential prompts

```
════════════════════════════════════════════════════════════
📊 FEATURE ANALYSIS: User Management API
════════════════════════════════════════════════════════════

📋 PARSED QUERY
───────────────────────────────────────────────────────────
Original: "Create user management API"
Type: NEW FEATURE
Scope: RESTful CRUD API with authentication

📂 CURRENT CONTEXT (from get_changed_files)
───────────────────────────────────────────────────────────
Branch: main
Pending changes: None
Active work: None

🔍 CODEBASE DISCOVERY (from semantic_search + grep_search)
───────────────────────────────────────────────────────────
Existing user code: None found
Existing auth code: src/middleware/auth.ts (JWT pattern)
Existing API structure: src/api/controllers/ (pattern to follow)
Related files: [list from semantic search]
Exact matches: [counts from grep search]

📖 GOVERNANCE CONTEXT (from read_file)
───────────────────────────────────────────────────────────
Constitution: ⚠️ Template only - needs setup
Project.md: ⚠️ Template only - needs tech stack

✅ CONCLUSION
───────────────────────────────────────────────────────────
Feature Type: GREENFIELD (new implementation)
Conflicts: None
Constitution: Needs setup (STEP 1 required)
Project.md: Needs tech stack definition

════════════════════════════════════════════════════════════
✨ OPTIMIZED FEATURE DESCRIPTION
════════════════════════════════════════════════════════════

RESTful User Management API with:
- CRUD endpoints at /api/users
- JWT authentication (following existing pattern)
- User entity: id, email, password, firstName, lastName, role
- RBAC: admin/user roles
- Validation: Zod schemas
- Audit logging
- Rate limiting on auth endpoints

════════════════════════════════════════════════════════════
🚀 WORKFLOW PROMPTS (Run in order)
════════════════════════════════════════════════════════════

┌─ STEP 1: CONSTITUTION ─────────────────────────────────┐
│ Status: ⚠️ REQUIRED - Constitution is template only    │
├────────────────────────────────────────────────────────┤
│                                                        │
│ /speckit.constitution                                  │
│                                                        │
│ Establish governance for [YOUR TECH STACK]:            │
│                                                        │
│ Principle I: Spec-First Development                    │
│ - All features MUST have spec before implementation    │
│                                                        │
│ Principle II: API Standards                            │
│ - RESTful conventions, OpenAPI documentation           │
│ - Versioning: /api/v1/                                │
│                                                        │
│ Principle III: Security                                │
│ - Passwords: bcrypt cost ≥12                          │
│ - Tokens: JWT ≤15min expiry                           │
│ - All inputs validated                                 │
│                                                        │
│ Principle IV: Testing                                  │
│ - Unit coverage ≥80%                                  │
│ - Integration tests for all endpoints                  │
│                                                        │
│ Tech Stack: [SPECIFY YOUR CHOICE]                      │
│ - Backend: Node.js/Python/Go/.NET?                    │
│ - Database: PostgreSQL/MySQL/MongoDB?                  │
│ - Auth: JWT/Sessions/OAuth?                           │
│                                                        │
└────────────────────────────────────────────────────────┘

┌─ STEP 2: SPECIFY ──────────────────────────────────────┐
│ Copy and run after constitution is set:                │
├────────────────────────────────────────────────────────┤
│                                                        │
│ /speckit.specify RESTful User Management API           │
│                                                        │
│ Endpoints:                                             │
│ ┌────────────────────────────────────────────────────┐ │
│ │ POST   /api/v1/auth/register    Create user        │ │
│ │ POST   /api/v1/auth/login       Authenticate       │ │
│ │ POST   /api/v1/auth/logout      End session        │ │
│ │ GET    /api/v1/users            List (admin)       │ │
│ │ GET    /api/v1/users/:id        Get details        │ │
│ │ PUT    /api/v1/users/:id        Update             │ │
│ │ DELETE /api/v1/users/:id        Soft delete        │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ Entity: User                                           │
│ ┌────────────────────────────────────────────────────┐ │
│ │ id          UUID      Primary key                  │ │
│ │ email       string    Unique, validated            │ │
│ │ password    string    bcrypt hash                  │ │
│ │ firstName   string    1-50 chars                   │ │
│ │ lastName    string    1-50 chars                   │ │
│ │ role        enum      admin | user                 │ │
│ │ isActive    boolean   Soft delete flag             │ │
│ │ createdAt   timestamp Auto-set                     │ │
│ │ updatedAt   timestamp Auto-set                     │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ Security:                                              │
│ - JWT in httpOnly cookies, 15min expiry               │
│ - Rate limit: 5 failed logins per 15min               │
│ - Password: min 8 chars, upper+lower+number+special   │
│                                                        │
└────────────────────────────────────────────────────────┘

┌─ STEP 3: CLARIFY ──────────────────────────────────────┐
│ Copy and run:                                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ /speckit.clarify                                       │
│                                                        │
│ Clarify these decisions:                               │
│                                                        │
│ 1. EMAIL VERIFICATION                                  │
│    - Required before login? [yes/no]                   │
│    - Link expiry? [24h/48h/72h]                       │
│                                                        │
│ 2. PASSWORD RESET                                      │
│    - Enable forgot password? [yes/no]                  │
│    - Reset link expiry? [1h/4h/24h]                   │
│                                                        │
│ 3. SESSION MANAGEMENT                                  │
│    - Multiple devices allowed? [yes/no]                │
│    - Show active sessions? [yes/no]                    │
│                                                        │
│ 4. USER LISTING                                        │
│    - Default page size? [10/20/50]                    │
│    - Filter by role/status? [yes/no]                  │
│                                                        │
│ 5. SOFT DELETE                                         │
│    - Retention period? [30/60/90 days]                │
│    - Admin can restore? [yes/no]                      │
│                                                        │
└────────────────────────────────────────────────────────┘

┌─ STEP 4: PLAN ─────────────────────────────────────────┐
│ Copy and run:                                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ /speckit.plan                                          │
│                                                        │
│ Generate these artifacts:                              │
│                                                        │
│ research.md:                                           │
│ - JWT library comparison                               │
│ - bcrypt vs argon2                                    │
│ - Rate limiting approach                               │
│                                                        │
│ data-model.md:                                         │
│ - User entity with constraints                         │
│ - Session entity                                       │
│ - AuditLog entity                                      │
│                                                        │
│ contracts/endpoints.yaml:                               │
│ - OpenAPI 3.0 specification                            │
│ - All endpoints with schemas                           │
│                                                        │
│ quickstart.md:                                         │
│ - Registration → Login → CRUD flow                    │
│                                                        │
│ plan.md:                                               │
│ - Architecture decisions                               │
│ - File structure                                       │
│ - Dependencies                                         │
│                                                        │
└────────────────────────────────────────────────────────┘

┌─ STEP 5: TASKS ────────────────────────────────────────┐
│ Copy and run:                                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ /speckit.tasks                                         │
│                                                        │
│ Generate tasks.md:                                     │
│                                                        │
│ Phase 1: SETUP                                         │
│ - T001: Initialize project                             │
│ - T002: Configure database                             │
│ - T003: Create User schema                             │
│                                                        │
│ Phase 2: AUTH                                          │
│ - T004: POST /auth/register                            │
│ - T005: Email verification                             │
│ - T006: POST /auth/login                               │
│ - T007: JWT generation                                 │
│ - T008: Rate limiting                                  │
│                                                        │
│ Phase 3: CRUD                                          │
│ - T009: GET /users (list)                             │
│ - T010: GET /users/:id                                │
│ - T011: PUT /users/:id                                │
│ - T012: DELETE /users/:id                             │
│                                                        │
│ Phase 4: TESTING                                       │
│ - T013: Unit tests                                     │
│ - T014: Integration tests                              │
│ - T015: E2E tests                                      │
│                                                        │
│ Phase 5: POLISH                                        │
│ - T016: Error handling                                 │
│ - T017: Audit logging                                  │
│ - T018: API documentation                              │
│                                                        │
│ Each task: file path, dependencies, effort (1-4h)      │
│                                                        │
└────────────────────────────────────────────────────────┘

┌─ STEP 6: CHECKLIST ────────────────────────────────────┐
│ Copy and run:                                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ /speckit.checklist security                            │
│                                                        │
│ Validate requirements for:                             │
│ - Password hashing specified?                          │
│ - JWT expiration defined?                              │
│ - Rate limiting documented?                            │
│ - Input validation complete?                           │
│ - RBAC permissions clear?                              │
│ - Audit scope defined?                                 │
│                                                        │
└────────────────────────────────────────────────────────┘

┌─ STEP 7: TASKSTOISSUES (Optional) ─────────────────────┐
│ Copy and run:                                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ /speckit.taskstoissues                                 │
│                                                        │
│ Create GitHub issues:                                  │
│ - Milestone: User Management API                       │
│ - Labels: feature, security, api                       │
│                                                        │
└────────────────────────────────────────────────────────┘

┌─ STEP 8: ANALYZE ──────────────────────────────────────┐
│ Copy and run:                                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ /speckit.analyze                                       │
│                                                        │
│ Verify:                                                │
│ - All REQ-XXX have tasks                               │
│ - All tasks have file paths                            │
│ - Terminology consistent                               │
│ - Constitution followed                                │
│                                                        │
└────────────────────────────────────────────────────────┘

┌─ STEP 9: IMPLEMENT ────────────────────────────────────┐
│ Copy and run:                                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ /speckit.implement                                     │
│                                                        │
│ Execute:                                               │
│ - Process tasks in order                               │
│ - Create files at specified paths                      │
│ - Run tests after each phase                           │
│ - Mark tasks [x] complete                              │
│                                                        │
└────────────────────────────────────────────────────────┘

┌─ STEP 10: ARCHIVE ─────────────────────────────────────┐
│ Copy and run:                                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ /speckit.archive                                       │
│                                                        │
│ Finalize:                                              │
│ - Verify all tasks [x]                                 │
│ - Run validate.ps1 -Strict                            │
│ - Promote to specs/user-management/                   │
│ - Archive to specs/changes/archive/                   │
│                                                        │
└────────────────────────────────────────────────────────┘

════════════════════════════════════════════════════════════
▶ NEXT: Copy STEP 1 (CONSTITUTION) and run it
════════════════════════════════════════════════════════════
```

---

## SUMMARY: Final Tool Order + Phases

| Phase | Tool | Purpose |
|-------|------|---------|
| 1 | (none) | Parse user query, identify gaps |
| 2 | `get_changed_files()` | Current context - what's user working on? |
| 3 | `semantic_search()` | Broad codebase search by meaning |
| 4 | `grep_search()` | Narrow down with exact matches |
| 5 | `list_code_usages()` / `file_search()` / `list_dir()` | Pinpoint (only if needed) |
| 6 | `read_file()` | Read constitution.md + project.md |
| 7 | (none) | Determine feature type + governance needs |
| 8 | (none) | Optimize query with discovered context |
| 9 | (none) | Output analysis + 10 prompts to chat |

**Flow**: `Parse → get_changed_files → semantic_search → grep_search → (pinpoint) → read_file → analyze → optimize → output`
