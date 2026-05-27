---
canonical_id: CLAUDECODE_BRIEF_SRP_A1
version: 1.0
status: CURRENT
phase: SRP-A-1
session_type: analysis
authored: 2026-05-25
worktree: MadhavSRP-A1
branch: arch/srp-a1-tech-debt
parallel_safe_with: fix/srp-f1-portal-fixes, fix/srp-f2-mcp-fixes
deploy_target: none (report only)
may_touch:
  - 00_ARCHITECTURE/TECH_DEBT_AUDIT_v1_0.md (create)
must_not_touch:
  - platform/src/**  (read-only analysis)
  - platform-mcp/src/**  (read-only analysis)
  - platform/src/app/**
---

# CLAUDECODE BRIEF: SRP-A-1 — Technical Debt Audit

## Context

You are performing a **read-only technical debt audit** of the MARSYS-JIS portal codebase
(`platform/` and `platform-mcp/`). No production code is modified. The output is a single
structured document: `00_ARCHITECTURE/TECH_DEBT_AUDIT_v1_0.md`.

Working directory: `/Users/Dev/Vibe-Coding/Apps/MadhavSRP-A1`
Branch: `arch/srp-a1-tech-debt`

This session is **parallel-safe** with SRP-F-1 and SRP-F-2. Run concurrently with Phase 1
fix sessions if desired.

---

## Audit Scope

### Category A: Dead Code (CRITICAL / HIGH)

**A.1 — Legacy orchestrator pipeline (unreachable when USE_ADAPTERS=true)**

`MARSYS_FLAG_R11V2_USE_ADAPTERS=true` is set in Cloud Run and defaults in `deploy.yml`.
When this flag is true, ALL portal traffic goes through the adapter path in the route handler.
The legacy `createOrchestrator()` / `single_model_strategy` path is never reached.

Find and catalog:
```bash
grep -rn "createOrchestrator\|single_model_strategy\|createSingleModelStrategy" platform/src/ --include="*.ts"
```

For each match: file path, line range, function/class name, estimated LoC.

**A.2 — Deprecated and unused symbols**

```bash
grep -rn "@deprecated" platform/src/ platform-mcp/src/ --include="*.ts"
```

For each: is it actually called anywhere? Check with:
```bash
grep -rn "PRIMARY_TOOL_NAMES" platform/src/ --include="*.ts"
# PRIMARY_TOOL_NAMES is known @deprecated — confirm it has zero call sites
```

**A.3 — Dead feature flag branches**

Read `platform/src/lib/feature_flags.ts` (or equivalent). For each flag defined there:
- Is it still referenced in `deploy.yml`?
- Is it still referenced in any `if (flag)` branch in the codebase?
- Flags known to be removed: `NEW_QUERY_PIPELINE_ENABLED`, `LLM_FIRST_PLANNER_ENABLED`,
  `CONTEXT_ASSEMBLY_ENABLED`, `CHAT_V2_ENABLED`.
- Check whether their removal was clean or left dead `if (false)` branches.

```bash
grep -rn "NEW_QUERY_PIPELINE\|LLM_FIRST_PLANNER\|CONTEXT_ASSEMBLY_ENABLED\|CHAT_V2_ENABLED" \
  platform/src/ --include="*.ts"
```

**A.4 — consume-tools.ts remnants**

Per CLAUDE.md §F, `consume-tools.ts` was deleted in Phase 11B (2026-05-11). Confirm deletion
and check for any remaining imports or references:
```bash
find platform/src -name "consume-tools*"
grep -rn "consume-tools" platform/src/ --include="*.ts"
```

---

### Category B: Orphaned Feature Flags (HIGH / MEDIUM)

Read `platform/src/lib/feature_flags.ts` in full. For each flag:
1. Where is it set? (`deploy.yml`, Cloud Run env, `.env.local`)
2. Where is it read? (`grep -rn "FLAG_NAME" platform/src/`)
3. Is it a NEXT_PUBLIC flag? (client-side, baked at build time)
4. Is the flag's guarded code path still alive?

**Known orphaned flags to check**:
- `MARSYS_FLAG_R11V2_USE_ADAPTERS` — if classic orchestrator is dead, does this flag
  have any remaining `false` branch that does something non-trivial?
- Any R10 flags (`SCROLL_DISCIPLINE`, `INTERACTIVE_TABLES`, `MERMAID`, `CITATION_FRESHNESS`,
  `VALIDATOR_GATES`, `SMOOTH_STREAM_V2`, `REASONING_STEPS`) — still active features or
  can any be promoted to always-on and the flag removed?
- `MARSYS_FLAG_OBSERVATORY_ENABLED` — observatory is live; is the `false` branch maintained?
- AIOps flags per `project_aiops_phase_3.md` memory: `ADAPTERS_ENABLED`,
  `CONSUME_UI_V2_ENABLED` — flag-removal was scheduled for ~2026-05-28.

For each orphaned flag, note: (a) safe to remove? (b) requires `--remove-env-vars` step?
(c) estimated LoC removed.

---

### Category C: Duplicate / Inconsistent Type Definitions (HIGH)

**C.1 — Valence enum**

The audit confirmed `valence` is defined in at least two places with different vocabularies:
- `platform-mcp/src/tools/query_signals.ts` — was `'positive'/'negative'/'neutral'` (now fixed)
- `platform/src/lib/retrieve/msr_sql.ts` — DB stores `'benefic'/'malefic'/'context-dependent'`

Search for all valence-related type definitions:
```bash
grep -rn "valence" platform/src/ platform-mcp/src/ --include="*.ts" -l
```
For each file, note what vocabulary it uses. Identify if there is a single canonical
type definition or if each file rolls its own.

**C.2 — Significance enum**

Same analysis for significance:
```bash
grep -rn "significance\|tier_1\|tier_2\|tier_3" platform/src/ platform-mcp/src/ --include="*.ts" -l
```

**C.3 — Domain enum**

```bash
grep -rn "domain.*career\|domain.*health\|domain.*relationship\|DomainType\|QueryDomain" \
  platform/src/ platform-mcp/src/ --include="*.ts" -l
```

**C.4 — QueryPlan type**

`primitives/[tool]/route.ts` builds a hardcoded `QueryPlan` inline. Is `QueryPlan` defined
as a shared type? How many places construct QueryPlan objects? Are they consistent?
```bash
grep -rn "QueryPlan\|query_plan_id" platform/src/ --include="*.ts" -l
```

---

### Category D: Logging Debt (MEDIUM)

**D.1 — params_json mismatches** (partially fixed in SRP-F-1, but check for similar patterns):
```bash
grep -rn "params_json" platform/src/ --include="*.ts"
```
For each occurrence: does the logged value match what's sent to SQL?

**D.2 — Missing trace fields**:
Read the query trace structure from `platform/src/lib/pipeline/` or similar. Are there
fields defined in the trace schema that are never populated (always null/undefined)?
```bash
grep -rn "query_trace\|tool_executions\|trace_id" platform/src/ --include="*.ts" -l
```

**D.3 — invocation_params logging** (noted in the audit — `query_dasha_periods` logs
`plan.domains` which may be misleading):
```bash
grep -rn "invocation_params" platform/src/ --include="*.ts"
```

---

### Category E: Test Coverage Gaps (MEDIUM)

Run the coverage report if available:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavSRP-A1/platform
npx vitest run --coverage 2>/dev/null | tail -40
```
Or simply:
```bash
npx vitest run --reporter=verbose 2>&1 | grep -E "^(PASS|FAIL|platform/src/lib/retrieve)"
```

For each retrieval tool in `platform/src/lib/retrieve/`:
- Does a test file exist?
- What is the approximate branch coverage?

Known gaps (from audit): `msr_sql.ts`, `lel_query.ts`, `query_ephemeris.ts` had zero filter
tests before SRP-T-1. Catalog remaining gaps after T-1/T-2 (this session runs in parallel,
so catalog the state before T-1/T-2 fixes are merged).

---

### Category F: Primitive Dispatcher Hardcoding (HIGH)

The dispatcher at `platform/src/app/api/mcp/primitives/[tool]/route.ts` hardcodes:
```typescript
domains: [],
forward_looking: false,
```
in the QueryPlan. FIX-2 fixes `forward_looking` but leaves `domains: []` hardcoded.

**F.1**: Is `domains: []` appropriate? When should the dispatcher pass domains to the
QueryPlan? Read the F.2 fix (domain reads from `params.domain`) — is there a path where
`plan.domains` is non-empty and matters?

**F.2**: What other fields in the hardcoded QueryPlan could be incorrectly defaulted?
Audit every field in the QueryPlan construction and note whether it should be dynamic.

---

## Output Format

Create `00_ARCHITECTURE/TECH_DEBT_AUDIT_v1_0.md` with the following structure:

```markdown
---
canonical_id: TECH_DEBT_AUDIT
version: 1.0
status: CURRENT
authored: 2026-05-25
---

# Technical Debt Audit v1.0

## Executive Summary

| Category | Items | Est. LoC Removable | Priority |
|----------|-------|-------------------|----------|
| A: Dead Code | N | ~XXX | CRITICAL/HIGH |
| B: Orphaned Flags | N | ~XXX | HIGH/MEDIUM |
| C: Type Inconsistencies | N | ~XXX | HIGH |
| D: Logging Debt | N | ~XXX | MEDIUM |
| E: Test Coverage | N | ~XXX | MEDIUM |
| F: Dispatcher Hardcoding | N | ~XXX | HIGH |
| **Total** | **N** | **~XXX** | |

## A: Dead Code

### A.1 — Legacy Orchestrator Pipeline

[Catalog each file + line range + LoC count]

...
```

Each entry must include:
- **File**: exact path relative to project root
- **Symbol / line range**: function name or lines N-M
- **Reason**: why it's dead (flag, deleted caller, etc.)
- **LoC**: approximate line count
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Safe to delete?**: YES / NO / NEEDS_HUMAN_REVIEW

---

## Acceptance Criteria

- [ ] Audit covers categories A through F.
- [ ] Every dead-code entry has file path + line range + reason + LoC.
- [ ] Every orphaned flag entry has flag name + set location + read location + LoC impact.
- [ ] Total deletable LoC estimated (should be ≥ 500 based on R11 + Phase 11B context).
- [ ] `00_ARCHITECTURE/TECH_DEBT_AUDIT_v1_0.md` committed.
- [ ] PR opened from `arch/srp-a1-tech-debt`.
- [ ] NO production code files modified.

## Session Close

Commit message:
```
arch(srp-a1): technical debt audit v1.0 — dead code, orphaned flags, type inconsistencies

Catalogs: legacy orchestrator (unreachable), deprecated symbols, orphaned feature flags,
valence/significance/domain enum duplication, logging debt, test coverage gaps,
dispatcher QueryPlan hardcoding. Est. Xk+ deletable LoC identified.
```
