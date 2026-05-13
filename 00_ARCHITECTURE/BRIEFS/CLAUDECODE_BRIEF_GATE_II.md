---
brief_id: GATE-II-TRACE-ALIGN
version: 2.0
status: ACTIVE-AUTONOMOUS
authored_by: Claude Opus 4.7 (Gate II — Trace Pipeline Alignment design session) — 2026-05-12
supersedes: CLAUDECODE_BRIEF_GATE_II.md v1.0 (had a human-in-the-loop pause after W1; v2.0 removes the pause for single-session overnight execution)
purpose: Rewire TracePanel + sub-components + trace assembler + supporting trace UI to accurately reflect the new (and only) query pipeline's stages, step vocabulary, and metadata schema. No new features — pure alignment. Single-session autonomous execution.
executor: Claude Code Sonnet 4.6 (Anti-Gravity, VS Code, --dangerously-skip-permissions)
working_directory: /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align
worktree_branch: feature/gate2-trace-pipeline-align
execution_mode: AUTONOMOUS-OVERNIGHT — no mid-session human input expected. All manual work is consolidated in §11 (pre-flight) and §12 (post-session review). Runs in parallel with Gate I and Gate III executor sessions in their own worktrees; no cross-gate file overlap.
model_preference: gemini-2.5-pro (critical); gemini-2.0-flash-lite or deepseek-chat (non-critical). Anthropic models BANNED in application logic.
parent_planning_doc: 00_ARCHITECTURE/briefs/OPUS_PLANNING_SESSION_v2_0.md
estimated_runtime: 6–10 hours uninterrupted
changelog:
  - v2.0 (2026-05-12): Autonomous single-session execution. W1 gap analysis is no longer a blocking gate; executor commits GAP_ANALYSIS.md and proceeds to W2+ using §4.5 autonomous decision rules. Manual work consolidated to §11 (pre-session) and §12 (post-session). Time budgets added per work item. Manual smoke test (former AC.11) converted to automated trace-shape assertion + screenshot capture deferred to §12 native review.
  - v1.0 (2026-05-12): Initial brief with human-in-the-loop pause after W1.
---

# CLAUDECODE_BRIEF — Gate II: Trace Pipeline Alignment (Autonomous v2.0)

## §0 — Read This First

The MARSYS-JIS query pipeline was rebuilt during Phase 11B / Pipeline-Transform-S1 (2026-05-11). The legacy path was deleted, the planner was hardened (recall 0.983 / precision 0.961), and ContextAssembly was removed entirely. But the live trace UI — `TracePanel.tsx` (v2.0, ~63KB), its `LifecycleGraph`, its step-detail variants, and `trace_assembler.ts` — still renders the *old* pipeline's stage names, step vocabulary, and metadata fields. Users staring at the trace today see a misleading picture of execution.

**Gate II is surgical. It is not a feature gate.** Eight design decisions are locked in §3. Nine work items in §4 carry them through. §4.5 provides autonomous decision rules for anything ambiguous so the session does not pause.

**This brief is designed to run unattended for 6–10 hours.** Two other executor sessions (Gate I in `marsys-gate1-perf-center`, Gate III in `marsys-gate3-smart-chat`) are running concurrently in their own worktrees. The `must_not_touch` list (§2) guarantees no file-level collision; migration slot 045 is exclusively Gate II's.

**No mid-session human input is expected.** If a true blocker emerges, follow R3 in §4.5: commit progress, write `BLOCKERS.md`, continue with remaining work items, surface in the close report.

---

## §1 — Entry Gates

All must pass before W1 begins. The executor itself runs these checks.

- [ ] `pwd` reports `/Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align`
- [ ] `git branch --show-current` reports `feature/gate2-trace-pipeline-align`
- [ ] `cd platform && ls node_modules` is non-empty (npm install completed in §11 pre-flight)
- [ ] `git status` is clean (no uncommitted changes from worktree setup)
- [ ] `git log -1 --oneline` shows the same HEAD as `main` (the feature branch was just cut)
- [ ] `npm test --silent --run` baseline pass — capture exact pass/fail count; this is the regression floor
- [ ] `tsc --noEmit` baseline clean (or capture pre-existing TS errors as the floor — Pipeline-Transform-S1 left some test-file errors in main; treat anything pre-existing as baseline, not a Gate II regression)
- [ ] `npm run lint` baseline state captured
- [ ] Read `00_ARCHITECTURE/briefs/OPUS_PLANNING_SESSION_v2_0.md` §3, §3.5, §3.8, §11
- [ ] Read `CLAUDE.md` §C items 1–11 (per project convention)
- [ ] Read this brief end-to-end (both §3 locked decisions AND §4.5 autonomous decision rules) before opening any source file

**Cowork thread / conversation name to propose at first response:** `MARSYS Gate II Exec — Trace Pipeline Alignment` per `CONVERSATION_NAMING_CONVENTION_v1_0.md`.

**If any entry gate fails:** stop, write the failure cause to `BLOCKERS.md` at worktree root, halt. Do not proceed.

---

## §2 — Scope

### may_touch

```
platform/src/components/trace/**
platform/src/components/consume/TraceDrawer.tsx                  (thin shell only — entry to TracePanel)
platform/src/lib/admin/trace_assembler.ts
platform/src/lib/admin/trace_client.ts
platform/src/lib/admin/trace_schema.ts                           (new file if W1 finds no schema exists)
platform/src/app/api/admin/trace/[query_id]/**
platform/src/app/api/trace/stream/[queryId]/**
platform/tests/**                                                (only files matching trace_assembler, trace components, trace_schema)
platform/supabase/migrations/045_*.sql                           (only if W1 surfaces a DB-level mismatch — see W9 + §4.5 R4)
GAP_ANALYSIS.md                                                  (worktree root; deliverable of W1)
BLOCKERS.md                                                      (worktree root; only if a true blocker surfaces)
SESSION_NOTES.md                                                 (worktree root; running notes the executor maintains during the session)
```

### must_not_touch

```
platform/src/components/consume/ConsumeChat.tsx
platform/src/components/consume/AnswerView.tsx
platform/src/components/consume/StreamingAnswer.tsx
platform/src/app/api/chat/consume/route.ts
platform/src/components/performance/**                           (Gate I territory)
platform/src/components/shared/AppShellRail.tsx                  (Gate IV nav cleanup on main)
platform/src/components/shared/MobileNavSheet.tsx                (Gate IV nav cleanup on main)
platform/supabase/migrations/043_*, 044_*, 046_*                 (other gates' migration ranges)
platform/src/lib/planner/**, platform/src/lib/retrieval/**,
platform/src/lib/synthesis/**, platform/src/lib/audit/**         (pipeline emitters — Gate II reads them, does not change them)
01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**, 06_LEARNING_LAYER/**
00_ARCHITECTURE/CANONICAL_ARTIFACTS_*.md                         (governance mirror pair — out of scope)
00_ARCHITECTURE/MACRO_PLAN_*.md, PROJECT_ARCHITECTURE_*.md       (governance artifacts — out of scope)
```

**No new npm packages without recording the requirement in `BLOCKERS.md` and proceeding around it.** Do not silently `npm install` anything new.

---

## §3 — Locked Design Decisions (do not relitigate — apply mechanically)

| # | Topic | Decision |
|---|---|---|
| D1 | Checkpoint visibility (4.5 / 5.5 / 8.5) | **Always visible + collapsible group.** A single "Checkpoints" header row in the lifecycle shows summary status (e.g., `Checkpoints · 2 of 3 ran`). Expanding reveals each checkpoint individually; disabled / skipped ones render with dimmed visual treatment. Trace shape is stable across flag combinations. |
| D2 | Per-step latency | **Total at top, per-step in expanded step detail.** Drawer header carries a wall-clock total pill (e.g., `4.7s`). Each step's expanded detail panel shows its own duration in its metadata block. Lifecycle graph step nodes do NOT show inline latency. |
| D3 | QueryPlan display | **Both — header banner + distinct Planner step.** A sticky context strip below the drawer header renders the headline QueryPlan fields (query_class badge, plan_type chip, confidence indicator). The lifecycle graph also has a Planner node whose step-detail panel renders the full QueryPlan blob, including `tools_selected` and `reasoning`. |
| D4 | Trace schema source-of-truth | **Executor determines in W1.** If a schema file exists, point trace_assembler + renderers at it. If not, W2 authors `platform/src/lib/admin/trace_schema.ts` as the new source of truth. No native input required. |
| D5 | Retrieval lifecycle shape | **Grouped node with inline sub-rows.** One `Retrieval` container node in the lifecycle, with the four sub-tools (`vector_search`, `cgm_graph_walk`, `structured_sql`, `hybrid_rank`) rendered as nested rows directly inside the node. Skipped sub-tools render dimmed. Per-sub-tool metadata lives in each sub-row's expanded state. |
| D6 | Single-model vs panel-mode synthesis | **Same Synthesis step; branch in the step-detail variant.** Lifecycle always shows one Synthesis node regardless of mode. The `SynthesisStepDetail` component detects mode from the assembled step payload: single-model renders one LLM-call row; panel mode renders N panelist rows + an aggregator row. Lifecycle graph shape is identical across modes. |
| D7 | Orphan step variants | **Delete both `ClassifyStepDetail` and `ContextAssemblyStepDetail`** along with all imports and registry entries. |
| D8 | Supporting components | **All three in scope: HealthRail, QueryDNAPanel, RetrievalScorecard.** Executor audits each in W6; if any reference retired stages or removed metadata fields, realign. |

---

## §4 — Work Items

Execute in numbered order. Each work item commits at its end (granular commit history aids review). Times below are soft budgets; do not optimize for speed at the cost of correctness.

### W1 — Gap analysis (deliverable, NOT a blocking gate) — budget: 90 min

**Goal:** Produce `GAP_ANALYSIS.md` at the worktree root documenting every mismatch between what the trace UI consumes and what the pipeline actually emits today. Commit it. **Then proceed directly to W2.** The artifact is for the native's post-session review (§12) and for the executor's own self-reference during W2–W9.

**Steps:**

1. Read end-to-end (in parallel):
   - `platform/src/components/trace/TracePanel.tsx`
   - `platform/src/components/trace/LifecycleGraph.tsx` (and `PipelineLifecycleView.tsx` if separate)
   - All step-detail variants under `platform/src/components/trace/StepDetail*.tsx` (or wherever they live — `find platform/src/components/trace -name "*StepDetail*"` first)
   - `platform/src/lib/admin/trace_assembler.ts`
   - `platform/src/lib/admin/trace_client.ts`
   - `platform/src/app/api/trace/stream/[queryId]/route.ts`
   - `platform/src/app/api/admin/trace/[query_id]/route.ts`
   - `HealthRail.tsx`, `QueryDNAPanel.tsx`, `RetrievalScorecard.tsx`

2. Read the pipeline emitters (read-only, do not modify):
   - Planner module (whatever emits `QueryPlan`) — find via `grep -rn "QueryPlan" platform/src/lib/planner/ platform/src/lib/`
   - Retrieval orchestrator — find via `grep -rn "vector_search\|cgm_graph_walk\|structured_sql\|hybrid_rank" platform/src/lib/`
   - Synthesis single-model + panel entry points
   - Audit writer
   - Checkpoints 4.5 / 5.5 / 8.5 modules

3. Grep for trace type definitions: `grep -rn "type.*Step\b\|type.*Stage\b\|type.*Trace\b\|TraceStep\|TraceStage\|PipelineStage\|AssembledTrace" platform/src/` — determines D4.

4. Build the gap inventory. `GAP_ANALYSIS.md` must contain these sections:
   - **§A — Stage vocabulary** — table: stage names hard-coded in renderers vs. stage names emitted by pipeline; mark each CURRENT / RETIRED / RENAMED / NEW
   - **§B — Step type discriminants** — string literals consumed by trace vs. produced by emitters
   - **§C — Metadata field reconciliation** — per stage: fields read by renderer vs. fields written by emitter; flag read-but-not-written and written-but-not-read
   - **§D — Orphan references** — every file/line referencing `ClassifyStepDetail`, `ContextAssemblyStepDetail`, `context_assembly`, `classify` as a stage name, or any other retired stage name
   - **§E — Schema source** — D4 resolution: existing file at `<path>` OR no schema file (type defs scattered across `<files>`)
   - **§F — Supporting-component findings** — for each of HealthRail / QueryDNAPanel / RetrievalScorecard: stale stage / metadata references found, if any
   - **§G — SSE event payload audit** — event types emitted by stream vs. event types client handler expects
   - **§H — Recommended migration 045 disposition** — YES / NO with rationale (see §4.5 R4 for the disposition rule)
   - **§I — Open questions / autonomous resolutions** — any ambiguity AND the §4.5 rule the executor will apply to resolve it autonomously
   - **§J — Emitter assumptions** — any place where current renderer assumes a shape that wasn't fully verified against the emitter; flag for native confirmation in §12

5. Commit `GAP_ANALYSIS.md` to the feature branch with message `Gate II W1: gap analysis between trace UI and new pipeline`.

6. **Proceed directly to W2. Do not pause.**

---

### W2 — Establish the trace schema source-of-truth — budget: 60 min

**Goal:** Single authoritative TypeScript module defining every stage name, step discriminant, and per-stage metadata shape.

**Branching on W1 §E:**

- **If a schema file exists:** update in place. Add new stage / step types. Remove retired ones. Bump `@version` JSDoc tag if present.
- **If no schema file exists:** author `platform/src/lib/admin/trace_schema.ts`. Required exports:
  - `type PipelineStage = 'planner' | 'retrieval' | 'synthesis' | 'audit' | 'checkpoint_4_5' | 'checkpoint_5_5' | 'checkpoint_8_5'`
  - `type RetrievalSubTool = 'vector_search' | 'cgm_graph_walk' | 'structured_sql' | 'hybrid_rank'`
  - Per-stage metadata interfaces: `PlannerStepMetadata`, `RetrievalStepMetadata` (with `sub_tools: RetrievalSubToolRun[]`), `SynthesisStepMetadata` (discriminated union: `mode: 'single_model'` vs `mode: 'panel'`), `AuditStepMetadata`, `CheckpointStepMetadata`
  - `interface QueryPlan { query_class, plan_type, tools_selected, confidence, reasoning }` — import + re-export from the planner module if a canonical definition lives there; do NOT duplicate the source of truth
  - `interface AssembledTrace { query_id, total_latency_ms, query_plan, steps: TraceStep[], checkpoints: CheckpointStep[] }`
  - `interface TraceStep` as a discriminated union by `stage`

**Then:**
- `trace_assembler.ts` and `trace_client.ts` import all stage/step types from this schema.
- Eliminate hard-coded string literals for stage names anywhere in the trace renderers; reference the enum/type.
- Add an ADR-lite header comment: one paragraph stating this file is the trace's source-of-truth.

**Commit:** `Gate II W2: trace_schema source-of-truth`

---

### W3 — Realign the lifecycle graph — budget: 90 min

**Goal:** `LifecycleGraph.tsx` (and `PipelineLifecycleView.tsx`) render the new pipeline shape per D5 and D1.

- Top-level nodes in execution order: **Planner → Retrieval → Synthesis → Audit**
- **Retrieval node:** grouped container; four sub-rows for `vector_search`, `cgm_graph_walk`, `structured_sql`, `hybrid_rank` rendered inline. Sub-rows that did not fire render dimmed.
- **Checkpoints:** single collapsible group rendered after Audit. Header summary: `Checkpoints · ${ran}/${total} ran`. Default collapsed. Expanded view shows 4.5, 5.5, 8.5 with dimmed treatment for disabled / skipped.
- No inline latency on step nodes (per D2).
- Hover / focus states preserved; keyboard nav preserved; screen-reader labels updated.

**Commit:** `Gate II W3: lifecycle graph realigned to new pipeline shape`

---

### W4 — Realign step-detail variants — budget: 120 min

**Delete (per D7):**
- `platform/src/components/trace/ClassifyStepDetail.tsx` (and any matching test file)
- `platform/src/components/trace/ContextAssemblyStepDetail.tsx` (and any matching test file)
- All imports, registry entries, dynamic-import maps referencing the above

**Author or rename:**
- `PlannerStepDetail.tsx` — renders full QueryPlan: `query_class`, `plan_type`, `tools_selected` (chip list), `confidence` (numeric + visual indicator), `reasoning` (collapsible long-text)

**Update existing variants:**
- `RetrievalStepDetail.tsx` (or equivalent) — per-sub-tool metadata blocks (rows-fetched, latency, hit-rate, top-score)
- `SynthesisStepDetail.tsx` — discriminated render per D6: single_model shows one LLM-call row with model / token counts / latency / finish-reason; panel mode shows N panelist rows + aggregator row, each with full LLM-call metadata
- `AuditStepDetail.tsx` (or equivalent) — validator verdict, disclosure tier, B.10/B.11 compliance flags, audit-event id

**All step-detail variants must:**
- Show the step's own latency in the metadata section (per D2)
- Import their type contract from `trace_schema.ts`
- Handle missing fields gracefully (older traces in the DB may lack new fields)

**Commit:** `Gate II W4: step-detail variants realigned; orphan variants deleted`

---

### W5 — Realign the TracePanel header + QueryPlan banner — budget: 45 min

- Drawer header: query_id pill, total wall-clock latency pill (e.g., `Total · 4.7s`), close button. No per-step latency at this level.
- Directly below the header, above the LifecycleGraph: **QueryPlan summary banner** rendering:
  - `query_class` badge
  - `plan_type` chip
  - `confidence` indicator (numeric + 0–1 visual bar)
- Banner is sticky on scroll inside the drawer.
- Banner reads from `assembledTrace.query_plan`; PlannerStepDetail reads the same field. No duplicated state.

**Commit:** `Gate II W5: TracePanel header + QueryPlan banner`

---

### W6 — Audit + realign supporting trace components — budget: 60 min

**For each of `HealthRail.tsx`, `QueryDNAPanel.tsx`, `RetrievalScorecard.tsx`:**

1. Read end-to-end.
2. Grep for references to retired stage names, removed metadata fields, old step-type literals.
3. If any found: realign to new schema. Top-of-file comment: `// Realigned for new pipeline 2026-05-12 (Gate II W6).`
4. If none found: document the clean audit finding in `GAP_ANALYSIS.md §F` (do not add no-op comments to the source file).

**RetrievalScorecard specifically:** verify per-sub-tool variance is visible (no single aggregate masking the 4-tool breakdown).
**HealthRail specifically:** rename any detectors whose names embed retired stage names; confirm no external consumers depend on the old names (grep first).

**Commit:** `Gate II W6: supporting trace components audited + realigned (if needed)`

---

### W7 — Reconcile the SSE stream + assembled-trace endpoints — budget: 45 min

- `/api/trace/stream/[queryId]/route.ts` — every SSE event payload conforms to a type in `trace_schema.ts`; add `satisfies` assertion (not `as`) so future drift is a compile error.
- `/api/admin/trace/[query_id]/route.ts` — assembled output conforms to `AssembledTrace`; same `satisfies` discipline.
- `trace_assembler.ts` — primary touch point; handles every new stage; unknown stages → log warning + render with stage name as-is (do not throw).
- Client `trace_client.ts` — event-type handlers updated; retired event types removed or no-op'd with a console warning.

**B.10 check while here:** if any trace data contains an LLM-fabricated numerical chart value, flag in `SESSION_NOTES.md` — do not silently fix.

**Commit:** `Gate II W7: SSE + admin-trace endpoints aligned to trace_schema`

---

### W8 — Test coverage — budget: 90 min

**New + updated tests:**

- `trace_assembler.test.ts` — golden fixtures (DB rows in → `AssembledTrace` out) for:
  - planner-only
  - planner + retrieval (all 4 sub-tools)
  - planner + retrieval (subset of sub-tools)
  - full pipeline with single-model synthesis
  - full pipeline with panel synthesis
  - full pipeline with all checkpoints
  - full pipeline with no checkpoints
- `trace_schema.test.ts` (if new file) — type-level tests that discriminated unions exclude impossible states
- Component snapshot tests for each step-detail variant
- Component test for `LifecycleGraph`: render with all-checkpoints-on fixture AND checkpoints-off fixture; assert node set is identical (per D1)
- Component test for QueryPlan summary banner

**Synthetic end-to-end fixture test** (replaces the v1.0 manual smoke test):
- Author `platform/tests/integration/trace_pipeline_e2e.test.ts`
- Stub the planner / retrieval / synthesis emitters to write a canned set of step rows to the test DB (or use existing fixtures)
- Call the assembled-trace endpoint
- Assert the returned `AssembledTrace` matches the schema and contains the expected stage set
- Save the returned trace JSON as `platform/tests/fixtures/gate_ii_smoke_trace.json` for §12 native review

**Regression bar:**
- `npm test --silent --run` — baseline count from §1 must hold or grow; zero NEW regressions
- `tsc --noEmit` — no NEW TS errors beyond the baseline captured in §1
- `npm run lint` — no NEW lint errors beyond baseline

**Vitest mock pattern:** `mockImplementation(function() { ... })` not arrow (Vitest 4.x project rule).

**Commit:** `Gate II W8: test coverage for trace realignment`

---

### W9 — Migration 045 (conditional) — budget: 30 min

Slot 045 is exclusively Gate II's. Use it ONLY if W1 §H concludes a DB-level schema change is required.

**If used:**
- File: `platform/supabase/migrations/045_trace_schema_alignment.sql`
- Before any `ALTER TYPE ... DROP VALUE`, `DROP COLUMN`, or `DELETE`: query `pg_constraint` to enumerate every FK dependent; document dependents in the migration comment header.
- Provide a clean down-migration if reversible.
- If the migration is destructive (drops data or columns with data): see §4.5 R4 — add a hold-flag comment and do NOT run in tests.

**If not used:** in `GAP_ANALYSIS.md §H` mark the slot reserved-unused with the rationale.

**Commit:** `Gate II W9: migration 045 disposition` (whether file created or just GAP_ANALYSIS update)

---

## §4.5 — Autonomous Decision Rules

These rules let the executor resolve ambiguity without human input. Apply mechanically.

### R1 — Ambiguity in W1 audit findings

If W1 surfaces an unclear field semantic, an unknown stage name in DB step rows, or a partially-renamed type:

- **Unclear field semantic:** preserve current renderer behavior; log a console warning on access; document in `GAP_ANALYSIS.md §I`
- **Unknown stage in DB rows:** render with stage name as-is, dimmed, with a `(unknown stage)` annotation; do NOT throw
- **Ambiguous synthesis mode discriminant:** default to `single_model` rendering; log warning; document in §I
- **Partially-renamed type:** prefer the new name; add a type alias for the old name with `@deprecated` JSDoc tag

### R2 — Unexpected emitter behavior

If a pipeline emitter (planner / retrieval / synthesis / audit / checkpoint) produces data that doesn't match the brief's stated shape:

- DO NOT modify the emitter — it's in `must_not_touch`
- Document the discrepancy in `GAP_ANALYSIS.md §J`
- Build renderers tolerant to the actual shape (defensive defaults, optional chaining, type narrowing)
- Surface in the session-close report for native confirmation

### R3 — True blocker (work item cannot complete autonomously)

If a work item cannot complete without touching a `must_not_touch` file, requires a new npm package, or hits a build error that resists 3 reasonable attempts:

1. STOP that work item only
2. Append to `BLOCKERS.md` at worktree root: `## W{n} blocked at {date} — {one-line summary}` followed by 5–10 lines of context
3. Commit current progress with message `Gate II W{n}: blocked — see BLOCKERS.md`
4. **Continue to the next work item** — do not halt the entire session
5. Document the blocker prominently in the session-close report

### R4 — Migration 045 destructive change

If W1 §H concludes migration 045 IS needed AND the change drops data / columns / enum values:

- Author the migration file with the change body
- Add this exact comment at the top:
  ```sql
  -- HOLD: destructive change. Native must confirm safety before applying.
  -- DO NOT RUN this migration in test or production until §12 review approves.
  ```
- Do NOT include this migration in the `npm test` run path (test setup should skip files matching `-- HOLD:`)
- Document in `GAP_ANALYSIS.md §H` + session-close report

### R5 — Baseline test failures

If `npm test` reports failures at the §1 baseline read:

- Capture the failing test files + names in `SESSION_NOTES.md` under heading `## Baseline test failures (pre-Gate II)`
- Gate II ACs measure DELTA from baseline. Do NOT attempt to fix pre-existing failures.
- New regressions Gate II introduces are reported separately.

### R6 — Time-budget overrun

If a work item's actual time exceeds its budget by >50%:

- Note the overrun in `SESSION_NOTES.md`
- Continue to completion of that work item if the scope is mostly done
- If completing the work item would mean cutting corners (skipping tests, ignoring ACs): treat as R3 blocker

### R7 — must_not_touch boundary push

If completing a work item appears to require a `must_not_touch` edit:

- Re-read the must_not_touch list — is the file truly in scope, or did you misread the brief?
- Is there an adapter / shim approach that achieves the goal without touching the forbidden file?
- If neither resolves it: R3 blocker.

### R8 — Schema file naming collision

If `trace_schema.ts` already exists at a different path than `platform/src/lib/admin/`:

- Prefer the existing path; do NOT create a duplicate
- Update import paths accordingly
- Document in `GAP_ANALYSIS.md §E`

### R9 — Hard halts (the only conditions for stopping the session)

Stop the session entirely ONLY if:

- A `git push` fails repeatedly with auth errors that look like credential expiry (commit locally, surface in close report)
- The worktree filesystem appears corrupted (e.g., `npm install` produces 100s of permission errors)
- A `must_not_touch` file appears to have been accidentally modified (revert via `git checkout`, investigate, then continue)

In all other cases: keep moving. The brief is designed to degrade gracefully.

---

## §5 — Acceptance Criteria

All checked off in the session-close artifact. AC.1 changed from v1.0: native approval is no longer required mid-session.

- [ ] **AC.1** `GAP_ANALYSIS.md` exists at worktree root, committed, with sections §A–§J populated
- [ ] **AC.2** `ClassifyStepDetail.tsx` and `ContextAssemblyStepDetail.tsx` deleted; `grep -rn` for their names returns zero results
- [ ] **AC.3** Trace schema source-of-truth exists at a single file path; imported by `trace_assembler.ts`, `trace_client.ts`, every step-detail variant, and the SSE / admin-trace routes
- [ ] **AC.4** Lifecycle graph renders **Planner → Retrieval (grouped with 4 inline sub-rows) → Synthesis → Audit**, followed by a collapsible **Checkpoints** group with `N of 3 ran` summary header
- [ ] **AC.5** Each step-detail variant renders correct metadata for its stage; snapshot tests pass
- [ ] **AC.6** Drawer header shows total wall-clock latency; each step's expanded detail shows that step's latency; no per-step latency on lifecycle nodes
- [ ] **AC.7** QueryPlan summary banner renders above the lifecycle (sticky on scroll); `PlannerStepDetail` renders the full QueryPlan including `reasoning`
- [ ] **AC.8** `SynthesisStepDetail` handles both single-model and panel mode; fixture tests for each pass
- [ ] **AC.9** `HealthRail`, `QueryDNAPanel`, `RetrievalScorecard` audited; any stale references resolved; findings documented in `GAP_ANALYSIS.md §F`
- [ ] **AC.10** `/api/trace/stream/[queryId]` and `/api/admin/trace/[query_id]` payloads conform to schema via `satisfies` assertions
- [ ] **AC.11** Synthetic E2E fixture test passes; assembled-trace JSON saved to `platform/tests/fixtures/gate_ii_smoke_trace.json` (replaces v1.0's manual smoke test; native does visual smoke in §12)
- [ ] **AC.12** `npm test --silent --run` — no NEW failures beyond baseline captured in §1
- [ ] **AC.13** `tsc --noEmit` — no NEW TS errors beyond baseline
- [ ] **AC.14** `npm run lint` — no NEW lint errors beyond baseline
- [ ] **AC.15** No files touched outside `may_touch`; `must_not_touch` list respected
- [ ] **AC.16** Migration 045 disposition matches W1 §H (used XOR reserved-unused, with rationale)
- [ ] **AC.17** `CLAUDECODE_BRIEF.md` (this file) moved to `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_II_v2_0.md` with frontmatter `status: COMPLETE` and a `closed_on` date
- [ ] **AC.18** `00_ARCHITECTURE/SESSION_LOG.md` entry appended per project convention
- [ ] **AC.19** `BLOCKERS.md` either does not exist OR exists with all blockers clearly documented (no silent halts)
- [ ] **AC.20** Final commit pushed to remote `origin/feature/gate2-trace-pipeline-align` (PR creation deferred to §12)

---

## §6 — LLM Stack

This gate involves no production LLM calls.

- Default: `gemini-2.5-pro`
- Non-critical / cheap: `gemini-2.0-flash-lite` or `deepseek-chat`
- **BANNED:** any `anthropic/*` model in application logic — if found in any touched file, flag in `SESSION_NOTES.md` and replace with a Gemini/DeepSeek equivalent

---

## §7 — Migration Numbers

- Gate II range: **045** (single migration slot reserved)
- Do not touch 043, 044 (Gate I), 046 (Gate III)
- W9 + §4.5 R4 govern usage

---

## §8 — Project Rules (encoded reminders)

- **B.10:** LLM never invents numerical chart values. While in trace code, if any rendered value appears to be an LLM-fabricated chart value, flag in `SESSION_NOTES.md` — don't silently fix.
- **B.11:** N/A directly, but ensure trace renderings do not imply synthesis bypassed L2.5 Holistic.
- **ROOT_FILE_POLICY:** This brief is the only file allowed at project root for the duration of the session.
- **GCS URIs:** unlikely to apply; if you find yourself writing `gs://` paths, read `GCS_LAYOUT_v1_0.md` first.
- **Vitest mocks:** `mockImplementation(function() {...})`, not arrows.
- **FK enumeration before DELETE in migration 045:** query `pg_constraint`; list dependents in the migration comment header.
- **No silent overwriting of mirror pairs:** none of Gate II's `may_touch` files are mirror-pair counterparts; if you find yourself editing a governance artifact, treat as R3 blocker.

---

## §9 — Session Close Checklist

The executor runs this autonomously at session end. No human input required.

1. All AC.1–AC.20 evaluated and recorded with pass/fail
2. `npm test --silent --run` — final count vs. baseline delta computed
3. `tsc --noEmit` — final error count vs. baseline delta
4. `npm run lint` — final lint error count vs. baseline delta
5. Synthetic E2E fixture JSON saved at `platform/tests/fixtures/gate_ii_smoke_trace.json`
6. `git status` clean (no untracked except intentional)
7. `GAP_ANALYSIS.md`, `SESSION_NOTES.md`, optionally `BLOCKERS.md` all committed
8. CLAUDECODE_BRIEF.md moved to `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_II_v2_0.md` with `status: COMPLETE`, `closed_on: YYYY-MM-DD`
9. `00_ARCHITECTURE/SESSION_LOG.md` entry appended
10. `git push origin feature/gate2-trace-pipeline-align`
11. Author `CLOSE_REPORT.md` at worktree root with:
    - AC pass/fail table
    - Test delta (baseline → final)
    - TS / lint delta
    - Commit count + files-touched count
    - Blocker count + summary (or "none")
    - Open items for §12 native review
    - Estimated effort for follow-up gate (if any blockers)
12. Print final summary to stdout: `Gate II session closed at <UTC>. {N}/20 ACs pass. {M} blockers. See CLOSE_REPORT.md.`

---

## §10 — Out of Scope (explicit non-goals)

- Adding new diagnostic data beyond what the pipeline emits
- Visual redesign beyond what D1–D8 require
- Changing what planner / retrieval / synthesis / audit / checkpoints emit
- Nav items (Gate IV)
- Consume chat components (Gate III)
- Performance components (Gate I)
- New trace export format / share button / permalink
- LL.8 Bayesian updating integration (M5)
- Creating the PR — leave that to §12 native

---

## §11 — Manual Prerequisites (BEFORE session kickoff — native runs these once)

The native runs this block in Terminal before triggering the executor session. This is the ONLY pre-session manual work. After this completes successfully, the executor handles the rest.

```bash
# Step 1 — Verify main repo is up to date
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git pull origin main
git status  # must be clean

# Step 2 — Create the Gate II worktree (skip if already created during the parent planning session)
git worktree list | grep -q marsys-gate2-trace-align || \
  git worktree add ../marsys-gate2-trace-align -b feature/gate2-trace-pipeline-align

# Step 3 — Install platform dependencies inside the worktree
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align/platform
npm install
# expected: 0 errors; lockfile unchanged

# Step 4 — Copy the brief into the worktree as CLAUDECODE_BRIEF.md (exact filename the executor expects)
cp /Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF_GATE_II.md \
   /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align/CLAUDECODE_BRIEF.md

# Step 5 — Commit the brief to the feature branch so the executor's first commit is on a clean baseline
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align
git add CLAUDECODE_BRIEF.md
git commit -m "Gate II: install autonomous execution brief v2.0"

# Step 6 — Sanity check git state
git branch --show-current  # expect: feature/gate2-trace-pipeline-align
git log -3 --oneline       # confirm clean commit history

# Step 7 — Open this worktree in VS Code with Anti-Gravity / Claude Code
# (Either: code . from the worktree directory,
#  OR: File > Open Folder > marsys-gate2-trace-align in an existing VS Code window)

# Step 8 — Launch Claude Code with dangerously-skip-permissions
# In the integrated terminal:
#   claude --dangerously-skip-permissions
# Then paste the trigger prompt provided alongside this brief.
```

**After §11 completes, the human steps away.** The executor will run from this point to §12 with no further input.

---

## §12 — Manual Post-Session Review (AFTER executor completes)

The native does this after the executor's session closes. Everything below is human-only and happens on `main` AFTER all three gate executors (Gate I, II, III) finish.

```bash
# Step 1 — Pull the worktree state
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align
git fetch origin
git log -1 --oneline  # confirm executor pushed final commit

# Step 2 — Read the executor's CLOSE_REPORT.md
cat CLOSE_REPORT.md
# Pay attention to:
#  - AC pass/fail table
#  - BLOCKERS.md presence and contents (if any)
#  - Open items flagged for native review
```

Visual smoke test (replaces the executor's automated E2E):

1. Apply migration 045 if W9 produced a non-HOLD migration: `cd platform && npm run db:migrate`
2. Start dev server: `npm run dev`
3. Open `/clients/<id>/consume`
4. Submit a query (any query from the 46-entry golden set)
5. Open the trace drawer
6. Verify visually:
   - Header shows total wall-clock latency pill
   - QueryPlan summary banner directly under header (class badge, plan_type chip, confidence indicator)
   - Lifecycle graph: Planner → Retrieval (with 4 sub-rows, dimmed if not fired) → Synthesis → Audit
   - Checkpoints group at the bottom with `N of 3 ran` summary
   - Drill into each step → step-detail panel shows correct fields including per-step latency
   - Capture a screenshot; save to a folder for the merge-PR description

Review pipeline:

7. Read `GAP_ANALYSIS.md` end-to-end. Confirm §J emitter-assumption flags are correct.
8. Read `BLOCKERS.md` if it exists. Decide whether each blocker is a follow-up gate or a same-session fix.
9. Open the PR: `gh pr create --base main --head feature/gate2-trace-pipeline-align --title "Gate II — Trace Pipeline Alignment" --body-file CLOSE_REPORT.md`
10. Once all three gates' PRs are reviewed, merge per §9 of `OPUS_PLANNING_SESSION_v2_0.md` (Gate II merges first).
11. After merge, return to the macro-plan Cowork conversation to trigger Gate IV.

---

*End of CLAUDECODE_BRIEF — Gate II: Trace Pipeline Alignment v2.0 (Autonomous)*
*Designed by Claude Opus 4.7 — 2026-05-12*
*Eight design decisions locked + nine autonomous decision rules + manual work consolidated to §11 (pre-flight) and §12 (post-session). Single-session overnight run, parallel-safe with Gate I and Gate III worktrees.*
