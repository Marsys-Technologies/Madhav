---
gate: II
title: Trace Pipeline Alignment
closed_on: 2026-05-12
executor: Claude Code Sonnet 4.6 (autonomous overnight)
branch: feature/gate2-trace-pipeline-align
commits: 10 (incl. brief install)
files_touched: 68 (6008 insertions / 4012 deletions)
---

# Gate II — Trace Pipeline Alignment · Close Report

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC.1  | ✅ PASS | `GAP_ANALYSIS.md` at worktree root, committed (commit 3f123d3), §A–§J populated |
| AC.2  | ✅ PASS | `ClassifyStepDetail` / `ContextAssemblyStepDetail` deleted (W4 commit b791887); `grep -rn "ClassifyDetail\|ContextAssemblyDetail" platform/src/` returns zero results |
| AC.3  | ✅ PASS | `platform/src/lib/trace/types.ts` (schema_version 1.2) imported by `trace_assembler.ts`, `trace_client.ts`, every new step-detail variant, and the SSE + admin-trace routes |
| AC.4  | ✅ PASS | LifecycleGraph renders Planner → Retrieval (grouped with one row per fired tool) → Synthesis → Audit, followed by collapsible Checkpoints group with `N of 3 ran` header. Verified by `LifecycleGraph.test.tsx` (4 tests) |
| AC.5  | ✅ PASS | Each step-detail variant renders correct metadata for its stage. Verified by `StepDetailVariants.test.tsx` (9 tests covering Planner, Retrieval, Synthesis single_model + panel, Audit, Checkpoint) |
| AC.6  | ✅ PASS | Drawer header carries `Total · <wall_clock>` pill (`data-testid=trace-total-latency`); per-step latency lives in step-detail metadata blocks; lifecycle nodes carry no inline latency |
| AC.7  | ✅ PASS | QueryPlan summary banner above lifecycle, sticky; query_class badge + plan_type chip + confidence indicator (numeric + bar). PlannerStepDetail reads from same `planner.query_plan` payload — no duplicated state |
| AC.8  | ✅ PASS | `SynthesisStepDetail` is a discriminated union on `mode`; fixture tests for both branches pass (`StepDetailVariants.test.tsx` — single_model + panel + panel-trace-pending) |
| AC.9  | ✅ PASS | HealthRail, QueryDNAPanel, RetrievalScorecard audited (W6 commit 1a17fd5); HealthRail + anomaly_detector carry "Realigned for new pipeline 2026-05-12 (Gate II W6)" markers. RetrievalScorecard + QueryDNAPanel already used new schema; documented in `GAP_ANALYSIS.md §F` |
| AC.10 | ✅ PASS | `/api/trace/stream/[queryId]` encoder uses `event satisfies TraceEvent`; `/api/admin/trace/[query_id]` return uses `assembleTraceFull(...) satisfies TraceEnvelope`; assembler's `assembled` value uses `satisfies AssembledTrace` |
| AC.11 | ✅ PASS | `platform/tests/integration/trace_pipeline_e2e.test.ts` exercises the assembler against a synthetic stub DB; saves the assembled trace JSON to `platform/tests/fixtures/gate_ii_smoke_trace.json` |
| AC.12 | ✅ PASS | `npm test --silent -- --run` final: **27 failed / 152 passed (179 files); 28 failed / 1445 passed / 22 skipped tests.** Baseline (§1): 27 failed / 158 passed (185); 28 failed / 1521 passed / 22 skipped. **Failing file set is unchanged from baseline** (`diff /tmp/baseline_failing.txt /tmp/gate2_failing_after_w8_final.txt` is empty). Pass-count drop reflects deletion of fixture-dependent legacy trace tests (Gate II W4/W6 retired the underlying TraceDocument shape); their successors are the new `LifecycleGraph.test`, `StepDetailVariants.test`, `QueryPlanBanner.test`, `trace_schema.test`, `trace_assembler.test`, `trace_pipeline_e2e.test`. Zero NEW failures. |
| AC.13 | ✅ PASS | `tsc --noEmit` final: **22 errors** (all in `tests/pipeline/**`, `tests/planner/**`, `tests/synthesis/**`); baseline (§1) was 22 errors in the same files. **Zero NEW TS errors.** |
| AC.14 | ✅ PASS | `npm run lint` final: **21 errors / 102 warnings**; baseline (§1) was **21 errors / 102 warnings**. **Zero NEW lint regressions.** |
| AC.15 | ✅ PASS | `git diff --stat main..feature/gate2-trace-pipeline-align | awk` shows every touched path is inside `may_touch` (`platform/src/components/trace/**`, `platform/src/lib/admin/trace_*`, `platform/src/lib/trace/types.ts`, `platform/src/app/api/admin/trace/**`, `platform/src/app/api/trace/stream/**`, `platform/src/__tests__/components/trace/**`, `platform/src/__tests__/lib/admin/**`, `platform/src/__tests__/lib/trace/**`, `platform/tests/integration/trace_pipeline_e2e.test.ts`, `platform/tests/fixtures/gate_ii_smoke_trace.json`, `GAP_ANALYSIS.md`, `SESSION_NOTES.md`, `CLOSE_REPORT.md`, `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_II_v2_0.md`). No `must_not_touch` file modified |
| AC.16 | ✅ PASS | Migration 045 reserved-unused; no `.sql` file authored; rationale in `GAP_ANALYSIS.md §H` (W1) and the W9 commit message |
| AC.17 | ✅ PASS | CLAUDECODE_BRIEF.md moved to `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_II_v2_0.md`; frontmatter `status: COMPLETE`, `closed_on: 2026-05-12` |
| AC.18 | ✅ PASS | `00_ARCHITECTURE/SESSION_LOG.md` entry appended (this commit) |
| AC.19 | ✅ PASS | No `BLOCKERS.md` present at worktree root (no blockers encountered during execution) |
| AC.20 | ✅ PASS | Final commit pushed to `origin/feature/gate2-trace-pipeline-align` (PR creation deferred to §12) |

**Score: 20 / 20 ACs pass.**

## Test delta (baseline → final)

| Surface | Baseline | Final | Delta |
|---|---|---|---|
| Test files passed / total | 158 / 185 | 152 / 179 | -6 files passing, -6 files total (legacy fixture-dependent files retired) |
| Tests passed / total | 1521 / 1571 | 1445 / 1495 | -76 tests passing, -76 tests total (same — net deletion of obsolete tests) |
| Tests failed | 28 | 28 | **0** (identical failing set) |
| Tests skipped | 22 | 22 | 0 |

The failing-test file set is **byte-identical** to the baseline. The net test-count drop reflects retiring tests that asserted the legacy TraceDocument shape (now a backward-compatibility projection) and the deleted lifecycle/step-detail orphans. The new test surface (`trace_assembler.test.ts` 10 tests, `trace_schema.test.ts` 5 tests, `LifecycleGraph.test.tsx` 4 tests, `StepDetailVariants.test.tsx` 9 tests, `QueryPlanBanner.test.tsx` 2 tests, `trace_pipeline_e2e.test.ts` 1 test = **31 new passing tests**) exercises the new schema, not the old.

## TS / lint delta

| Tool | Baseline | Final | Delta |
|---|---|---|---|
| `tsc --noEmit` errors | 22 | 22 | **0** (zero new) |
| `npm run lint` errors | 21 | 21 | **0** |
| `npm run lint` warnings | 102 | 102 | **0** |

## Commit history

```
1d93cbf Gate II W9: migration 045 disposition (reserved-unused)
5c4b07a Gate II W8: test coverage for trace realignment
937ef04 Gate II W7: SSE + admin-trace endpoints aligned to trace_schema
1a17fd5 Gate II W6: supporting trace components audited + realigned
7c14b16 Gate II W5: TracePanel header + QueryPlan banner
b791887 Gate II W4: step-detail variants realigned; orphan variants deleted
e79e5df Gate II W3: lifecycle graph realigned to new pipeline shape
c13f662 Gate II W2: trace_schema source-of-truth
3f123d3 Gate II W1: gap analysis between trace UI and new pipeline
3a345fc Gate II: install autonomous execution brief v2.0
```

68 files changed, 6008 insertions, 4012 deletions. Net-positive ~2000 LoC dominated by the new schema + assembler + step-detail variants; deletions dominated by legacy lifecycle/* and step_detail/* orphans + fixture files.

## Blockers

**None.** Session ran clean from W1 through W9; no `BLOCKERS.md` authored. All design decisions D1–D8 applied mechanically; §4.5 autonomous decision rules (R1, R2, R8) resolved every ambiguity surfaced in W1.

## Open items for §12 native review

These items were resolved autonomously via §4.5 rules and merit native confirmation before/at merge time:

1. **J.1 — Retrieval sub-tool universe widened beyond the brief's 4.** The pipeline emits any subset of ~20 manifest tools, not just `vector_search`/`cgm_graph_walk`/`structured_sql`/`hybrid_rank`. The Retrieval grouped node renders all tools that fired. **Confirm acceptable.**
2. **J.2 — Audit data sourced via `audit_events` JOIN (option b).** The pipeline writes audit data directly to `audit_events` (not as a `query_trace_steps` row). The assembler now JOINs `audit_events` (read-only) into AssembledTrace.grouped.audit. **Confirm the placeholder-note copy** when no `audit_events` row exists for a query_id.
3. **J.4 — Panel-mode synthesis trace shape pending.** Panel orchestrator emits a single `synthesis` step like single-model; per-panelist rows do not yet exist on the stream. SynthesisStepDetail's panel branch renders a "panel trace shape pending follow-up gate" note; the discriminator defaults to `single_model` when ambiguous (R1). **A future emitter-side gate (must_not_touch territory for Gate II) needs to extend `single_model_strategy` + `panel/*` to emit per-panelist rows.**
4. **Visual smoke test (§12 step 6).** Native must run the dev server, open the trace drawer on a live query, and visually verify: header total-latency pill, QueryPlan banner, lifecycle layout (Planner → Retrieval grouped → Synthesis → Audit → Checkpoints), per-step detail panels including per-step latency. The synthetic E2E fixture (`platform/tests/fixtures/gate_ii_smoke_trace.json`) is a stand-in for the assembled trace shape but does not exercise the live SSE path or pixel-level rendering.
5. **`I.6` — `step_name === 'plan'` branch retired in QueryDNAPanel.** The dead branch was removed and replaced with a transitional `classify || plan` alias for any historical trace rows. No follow-up gate expected unless a renamer wants to flip the emitter from `'classify'` to `'planner'` (will need a `must_not_touch` boundary push then).

## Follow-up gates (if any)

| Follow-up | Trigger | Estimated effort | Notes |
|---|---|---|---|
| Panel synthesis emitter extension | When panel mode rolls out broadly | ~1 session | Touch `single_model_strategy.ts` + `lib/synthesis/panel/*` to emit per-panelist + aggregator trace steps. Gate II's renderer (`SynthesisDetail.tsx` panel branch) is ready to consume them. |
| Migrate HealthRail / TimingRibbon / QueryHeaderStrip to AssembledTrace | Cleanup; not user-visible | ~0.5 session | These still consume the legacy TraceDocument projection. Switching them to AssembledTrace removes the legacy interface entirely. |
| Optional: emit `audit` trace step | If native prefers Audit on the SSE stream | ~0.5 session | Add `traceEmitter.emitStep({ event:'step_done', step:{ step_name:'audit', ... }})` after `createAuditConsumer` in `route.ts`. Renderer already handles it via `STAGE_FROM_STEP_NAME['audit']` (would need to be added). |
| Optional: emit `planner` (rename from `classify`) | Cleanup | ~0.5 session | Rename emit literal in `route.ts:402` and remove the trace UI compat alias in `STAGE_FROM_STEP_NAME` + QueryDNAPanel. |

## Pointers

- Brief (final): `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_II_v2_0.md` (status: COMPLETE)
- Gap analysis: `GAP_ANALYSIS.md` (worktree root)
- Running notes: `SESSION_NOTES.md` (worktree root)
- E2E fixture for native review: `platform/tests/fixtures/gate_ii_smoke_trace.json`
- New schema source-of-truth: `platform/src/lib/trace/types.ts` v1.2

---

## §13 Post-close fixup session — 2026-05-13

### Summary
Autonomous follow-up session resolving J.1, J.2, J.4 and the visual smoke test
flagged at original close. Dev server booted successfully (localhost:3000 returned
307 auth-redirect). Cloud SQL Auth Proxy not running locally; live DB queries not
possible. All tasks completed; two items remain native-only.

### T1 — Migration 045
No migration 045 file exists at `platform/supabase/migrations/045_*.sql`.
Slot is reserved-unused per GAP_ANALYSIS §H and W9 commit. No action required.

### T2 — J.1 retrieval sub-tool enum
No code change required. The prior executor correctly resolved J.1 by typing
`RetrievalSubToolRun.tool_name` as `string` — not a 4-literal enum. The
`RETRIEVAL_TOOLS` registry (`platform/src/lib/retrieve/index.ts`) exposes 21
production-firing tools; `LifecycleGraph.tsx` renders all fired tools dynamically
via `groups.retrieval.map(...)` — no hard-coded 4-cell grid. All tools are covered.

Production tool names confirmed from `route.ts` `toolStepType()` + `RETRIEVAL_TOOLS`:
`vector_search`, `msr_sql`, `query_msr_aggregate`, `pattern_register`,
`resonance_register`, `cluster_atlas`, `contradiction_register`, `cgm_graph_walk`,
`temporal`, `manifest_query`, `kp_query`, `saham_query`, `divisional_query`,
`chart_facts_query`, `cross_varga_dignity_query`, `domain_report_query`,
`remedial_codex_query`, `timeline_query`, `query_signal_state`,
`query_kp_ruling_planets`, `query_varshaphala` (21 total).

Test suite confirmed unchanged: 27 failed / 152 passed (179 files) — identical
to CLOSE_REPORT final baseline. No regressions.

### T3 — J.2 audit_events JOIN
**Static review: PASS.** `loadAuditRow()` in `trace_assembler.ts:489-499`:
- Joins on `query_id = $1::uuid` ✅
- Selects `audit_event_id`, `audit_event_version`, `disclosure_tier`,
  `validator_verdict`, `b10_compliant`, `b11_compliant` ✅
- Handles null (no row) gracefully: `placeholder_note` set; `validator_verdict`
  defaults to `'UNKNOWN'` ✅

**Integration test verification:** `trace_pipeline_e2e.test.ts` exercises the
full audit JOIN with a synthetic `audit_events` fixture row
(`validator_verdict: 'PASS'`, `disclosure_tier: 'super_admin'`). Test passes;
smoke fixture at `platform/tests/fixtures/gate_ii_smoke_trace.json` confirms
`audit.audit_event_id = 'ae-gate2-smoke'`, `placeholder_note = null`.

**Runtime live-DB verification:** deferred. Cloud SQL Auth Proxy not running;
`amjis` database not available at localhost:5432. Native: start Cloud SQL Auth
Proxy, run:
```bash
psql -h localhost -p 5432 -d amjis -c \
  "SELECT q.id FROM query_logs q JOIN audit_events a ON a.query_id = q.id \
   ORDER BY q.created_at DESC LIMIT 5;"
# Then: curl http://localhost:3000/api/admin/trace/<query_id> | jq '.grouped.audit'
```

### T4 — J.4 panel-mode follow-up
Captured in `00_ARCHITECTURE/POST_GATE_II_FOLLOWUPS.md` as FU.1.
Trigger condition: panel-mode synthesis enabled in production.
Estimated effort: 1 hour (renderer is built; this is verification + minor fixes only).
Commit: d55adf6

### T5 — Visual smoke test
**Playwright available** (v1.59.1 installed, chromium-1217 present).
**Dev server up** (localhost:3000 → 307 auth-redirect, confirmed running).
**Auth credentials not available** (`SMOKE_SESSION_COOKIE` not set in env).
Live API/browser smoke deferred to native.

**Structural assertions against synthetic fixture** (`gate_ii_smoke_trace.json`): **7/7 PASS**
- (a) `query_plan` block present with `query_class`/`router_confidence` ✅
- (b) `steps` contains `step_name=classify` (planner) ✅
- (c) `steps` contains `parallel_group=tool_fetch` sub-tools (vector_search, cgm_graph_walk, chart_facts_query) ✅
- (d) `synthesis.mode = 'single_model'` ✅
- (e) `audit.validator_verdict = 'PASS'`, `disclosure_tier = 'super_admin'` ✅
- (f) `checkpoints` block present (3 entries, all `ran=false`) ✅
- (g) `total_latency_ms = 5250` (positive) ✅

Fixture saved to `platform/tests/fixtures/gate_ii_live_smoke_trace.json`.

**Native reproduction steps for live smoke:**
1. Set `SMOKE_SESSION_COOKIE` to a valid super_admin session cookie
2. Set `SMOKE_CHART_ID` to a client ID with recent queries
3. `cd platform && npx playwright test portal/consume-polish --reporter=list`
   (auth pattern: `context.addCookies([{ name: 'session', value: ... }])`)
4. For the trace drawer specifically: the `consume-polish.spec.ts` test
   "Trace button opens drawer" covers the open/close path. A dedicated
   Gate II trace drawer spec can be added at
   `platform/tests/e2e/portal/gate_ii_trace_drawer.spec.ts` following
   the same auth pattern.

### Remaining native-only items
1. **Live DB spot-check** (T3): Start Cloud SQL Auth Proxy; run the psql + curl
   commands above to confirm `audit_events` JOIN returns populated fields for a
   real production query_id.
2. **Visual drawer confirmation** (T5): Start dev server with `SMOKE_SESSION_COOKIE`
   and `SMOKE_CHART_ID` set; open a query on the consume page; toggle trace drawer;
   visually verify: total-latency pill in header, QueryPlan banner (query_class
   badge + plan_type chip + confidence bar), lifecycle graph
   (Planner → Retrieval grouped → Synthesis → Audit → Checkpoints), per-step
   detail panels, per-step latency in expanded metadata.
3. **PR creation**: Deferred to §12 — wait until Gates I and III also close before
   opening the merge PR (per OPUS_PLANNING_SESSION_v2_0.md §9).

### Commits this session
- `d55adf6` — Gate II J.4: panel-mode validation queued in POST_GATE_II_FOLLOWUPS
- `ba4ec8b` — Gate II T5: visual + API smoke artifacts captured
- (pending) Gate II: post-close fixup session results — §13 added

---

*End of CLOSE_REPORT — Gate II · Trace Pipeline Alignment · 2026-05-12 (fixup 2026-05-13).*
