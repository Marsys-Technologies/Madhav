---
artifact: CLAUDECODE_BRIEF_QP_S2.md
status: PENDING
session_id: QP-S2
phase: Pipeline Gap Closure — Code Cleanup (GAP-8, GAP-9)
executor: claude-opus-4-6 (anti-gravity VS Code)
run_from_worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-cleanup
branch: fix/cleanup-qp-s2
authored_by: Cowork (Abhisek session 2026-05-11)
authored_on: 2026-05-11
acceptance_criteria_count: 4
parallel_safe: true
parallel_siblings: QP-S1 (fix/planner-gap-qp-s1), QP-S3 (fix/golden-set-qp-s3)
depends_on: Pipeline-Transform-S1 merged to main (commit 85dfca5)
master_plan: 00_ARCHITECTURE/PIPELINE_GAP_PLAN_v1_0.md §4/QP-S2
---

# QP-S2 — Code Cleanup

## §0 — HOW TO READ THIS BRIEF

**Run from the worktree:** `/Users/Dev/Vibe-Coding/Apps/Madhav-cleanup`
(branch `fix/cleanup-qp-s2`).

**Minimal surface.** This session touches exactly three source files:
`platform/src/app/api/chat/consume/route.ts`,
`platform/src/components/consume/StreamingAnswer.tsx`, and
`platform/src/hooks/useChatSession.ts`.
Everything else is out of scope.

When all 4 ACs are GREEN, commit, push, and set `status: COMPLETE` in this
file's frontmatter. Do not emit SESSION_OPEN or SESSION_CLOSE artifacts.

---

## §1 — CONTEXT AND PROBLEM

Pipeline-Transform-S1 (PR #15, commit 85dfca5) converted the query pipeline
to use `PipelinePlan` exclusively. The refactor left two residual housekeeping
items in source code:

| Gap | Problem | Location |
|-----|---------|----------|
| GAP-8 | Debug `console.log` calls left in from development | `route.ts` line 314 (confirmed); `StreamingAnswer.tsx` and `useChatSession.ts` (verify clean) |
| GAP-9 | `route.ts` imports `QueryPlan` from `@/lib/router/types` — a legacy module. The router module was only partially cleaned up. The adapter at line 320 creates a `QueryPlan`-shaped object from `PipelinePlan` data to feed downstream validators and orchestrator. This coupling should be resolved. |

**Note on GAP-10:** The `.gitignore` patterns for eval scratch files were
already committed at `7b8aa61`. GAP-10 is CLOSED. Do not re-add them.

**Pre-confirmed state (verified by the brief author before authoring):**
- `route.ts` line 314: `console.log('[consume:v3] B.11 enforcement: added msr_sql + cgm_graph_walk')` — confirmed present, to be removed.
- `StreamingAnswer.tsx`: grep shows **zero** `console.log` calls — already clean.
- `useChatSession.ts`: grep shows **zero** `console.log` calls — already clean.
- `@/lib/router/types.ts` **still exists** (types.ts, errors.ts, retrieval_capability_spec.ts
  were not deleted in Pipeline-Transform-S1 — only `router.ts` and `prompt.ts` were removed).
  The TypeScript compiler does not error on the import at line 41 today.

---

## §2 — MANDATORY READING BEFORE WRITING ANYTHING

```
platform/src/app/api/chat/consume/route.ts       ← PRIMARY file to edit
platform/src/lib/router/types.ts                 ← Read to understand QueryPlan shape (read-only)
platform/src/lib/pipeline/types.ts               ← PipelinePlan schema (read-only)
platform/src/lib/validators/index.ts             ← Verify validator accepts QueryPlan shape
00_ARCHITECTURE/PIPELINE_GAP_PLAN_v1_0.md §4/QP-S2  ← Master spec (read-only)
```

Do NOT touch any other file.

---

## §3 — WORK TO DO (3 items)

### 3A. Remove debug console.log from route.ts (GAP-8)

**Confirmed target:** route.ts line 314:
```ts
console.log('[consume:v3] B.11 enforcement: added msr_sql + cgm_graph_walk')
```

**Action:** Delete this line. It is a development-mode debug print — the B.11
enforcement logic itself (the `.push()` calls above it) must be preserved.

**Scan for additional console.logs:** After removing line 314, grep route.ts
for any other `console.log` calls introduced in or after commit `b3fcb77`.
Use `git log --oneline platform/src/app/api/chat/consume/route.ts` to identify
which commits are relevant. Remove any debug-level logs that are not intentional
monitoring calls (i.e., not part of the `[MON-*]` or `[audit:*]` patterns).

**Verify StreamingAnswer.tsx + useChatSession.ts are clean:**
```bash
grep -n "console\.log" platform/src/components/consume/StreamingAnswer.tsx
grep -n "console\.log" platform/src/hooks/useChatSession.ts
```
Both should return zero matches (pre-confirmed clean; verify hasn't regressed).

### 3B. Resolve the QueryPlan adapter coupling in route.ts (GAP-9)

**Current state:**
- Line 41: `import type { QueryPlan } from '@/lib/router/types'`
- Line 320: `const queryPlan: QueryPlan & { tool_calls?: PipelinePlan['tool_calls'] } = { ... }`

The adapter at line 317–340 constructs a `QueryPlan`-shaped object from a
`PipelinePlan` to satisfy downstream consumers (validators, audit, orchestrator)
that were written before the new pipeline. `@/lib/router/types` still exists, so
the compiler does not error today — but it is a legacy dependency coupling the
new pipeline to the old router namespace.

**Resolution path — choose the lowest-risk correct fix:**

**Option A (preferred if downstream types permit):** Check whether `PipelinePlan`
from `@/lib/pipeline/types` is a structural superset of `QueryPlan`. If every
field on `QueryPlan` also exists on `PipelinePlan` (possibly optional vs required
differences), replace the adapter's type annotation:
```ts
// Before
const queryPlan: QueryPlan & { tool_calls?: PipelinePlan['tool_calls'] } = { ... }

// After
const queryPlan: PipelinePlan & { query_plan_id: string; schema_version: string } = {
  ...plan,
  query_plan_id: queryId,
  schema_version: '1.0',
  tools_authorized: toolsAuthorized,
  tool_calls: plan.tool_calls,
}
```
Then remove the `import type { QueryPlan } from '@/lib/router/types'` line.
Run `tsc --noEmit` immediately after. If it passes → you're done.

**Option B (fallback if Option A produces type errors):** Define a minimal
inline interface in route.ts that replaces `QueryPlan` as a local structural
type, removing the external import dependency:
```ts
// Replace the import with a local definition capturing only what route.ts uses:
interface LegacyQueryPlanShape {
  query_plan_id: string
  query_text: string
  query_class: string
  domains: string[]
  forward_looking: boolean
  audience_tier: string
  tools_authorized: string[]
  history_mode: string
  panel_mode: boolean
  expected_output_shape: string
  manifest_fingerprint: string
  schema_version: string
  planets?: string[]
  houses?: number[]
  dasha_context_required?: boolean
  graph_seed_hints?: string[]
  vector_search_filter?: Record<string, unknown>
  time_window?: { start: string; end: string }
  tool_calls?: PipelinePlan['tool_calls']
}
```
Use `LegacyQueryPlanShape` in place of `QueryPlan &` at line 320. Run
`tsc --noEmit` to confirm.

**Decision rule:** Pick whichever option compiles cleanly with `tsc --noEmit`
returning exit 0. Do **not** leave downstream consumers with broken types.
Do **not** modify `@/lib/router/types.ts` — that is a shared module; its
cleanup is a separate task.

### 3C. Run TypeScript check

After all edits:
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-cleanup/platform
npx tsc --noEmit
```

Exit code must be `0`. If it is not, iterate on 3B until it is.

---

## §4 — ACCEPTANCE CRITERIA (4 items)

- [ ] **AC-1** `grep -n "console\.log" platform/src/app/api/chat/consume/route.ts` returns zero lines that are debug prints from b3fcb77 or later (intentional `[MON-*]`/`[audit:*]` monitoring patterns are exempt if any exist).
- [ ] **AC-2** `grep -rn "console\.log" platform/src/components/consume/StreamingAnswer.tsx platform/src/hooks/useChatSession.ts` returns zero matches.
- [ ] **AC-3** `grep -rn "@/lib/router/types" platform/src/app/api/chat/consume/route.ts` returns zero matches — the stale import is removed.
- [ ] **AC-4** `cd platform && npx tsc --noEmit` exits `0` with no TypeScript errors in the consume route or any files it imports.

---

## §5 — MAY TOUCH / MUST NOT TOUCH

### may_touch
```
platform/src/app/api/chat/consume/route.ts        (all edits go here)
platform/src/components/consume/StreamingAnswer.tsx (verify-only unless console.logs found)
platform/src/hooks/useChatSession.ts               (verify-only unless console.logs found)
CLAUDECODE_BRIEF.md                                (set status: COMPLETE at end)
```

### must_not_touch
```
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md             (QP-S1 owns this)
platform/tests/eval/planner_golden_set.json        (QP-S3 owns this)
platform/src/lib/router/types.ts                   (shared module — do NOT edit)
platform/src/lib/pipeline/types.ts                 (schema frozen)
platform/src/lib/validators/**                     (do NOT edit validators)
platform/src/lib/synthesis/**                      (do NOT edit orchestrator)
.gitignore                                         (GAP-10 already closed at 7b8aa61)
00_ARCHITECTURE/CURRENT_STATE_v1_0.md              (QP-S4 owns governance)
00_ARCHITECTURE/SESSION_LOG.md                     (QP-S4 owns governance)
```

---

## §6 — KNOWN OUT-OF-SCOPE

1. **Full router module deletion** — `@/lib/router/types.ts`, `errors.ts`, and
   `retrieval_capability_spec.ts` still exist. Their complete removal would
   require updating all their consumers. That is a separate planned cleanup, not
   this session.
2. **Eval run** — QP-S4 runs the full eval after S1+S3 are merged.
3. **Planner prompt** — QP-S1 owns `PLANNER_PROMPT_v2_0.md`.
4. **Golden set** — QP-S3 owns `planner_golden_set.json`.
5. **Governance close** — SESSION_LOG + CURRENT_STATE are QP-S4's responsibility.

---

## §7 — COMPLETION SEQUENCE

When all 4 ACs are PASS:

1. Set `status: COMPLETE` in this file's frontmatter.
2. Commit:
   ```bash
   git add platform/src/app/api/chat/consume/route.ts \
           platform/src/components/consume/StreamingAnswer.tsx \
           platform/src/hooks/useChatSession.ts \
           CLAUDECODE_BRIEF.md
   git commit -m "fix(cleanup): remove debug console.logs; drop QueryPlan legacy import in route.ts

   GAP-8: remove console.log at route.ts:314 (B.11 enforcement debug print)
   GAP-9: replace QueryPlan import from @/lib/router/types with local type or PipelinePlan
   GAP-10: already closed at 7b8aa61 (gitignore patterns committed)
   tsc --noEmit: exit 0 confirmed"
   git push -u origin fix/cleanup-qp-s2
   ```
3. Notify: session QP-S2 COMPLETE on branch `fix/cleanup-qp-s2`.

---

*CLAUDECODE_BRIEF_QP_S2.md · Pipeline Gap Plan QP-S2 · 2026-05-11*
*4 acceptance criteria: debug log removal + legacy import elimination → tsc clean*
*Parallel with: QP-S1 (planner prompt), QP-S3 (golden set)*
