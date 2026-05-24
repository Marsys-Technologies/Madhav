# Known Pre-Existing Test Failures

**v1.4 — pre-existing failures resolved (2026-05-24)**
Branch: main
Total pre-existing failures: **0 test cases**
Test suite: **4997 passed / 0 failed / 23 skipped** (5020 test cases)

---

## Changelog

- **v1.4 (2026-05-24):** All 18 pre-existing failures from v1.3 resolved. 10 targeted edits across 10 files: deleted 8 stale citation tests (R11.B chrome arc); added 6 missing tool entries to RETRIEVAL_CAPABILITY_SPEC (M5 Coverage Campaign gap); updated RT-08a/b to new PipelinePlanSchema shape; updated PredictionsCalibration tests to current component API; fixed MuhuratFinderModal client UUID; updated e2e breakdown key filter (Phase 4C short-key format); fixed `let {` → `const {` in cost_data_part test. Final suite: **0 failures**.
- **v1.3 (2026-05-23):** Refreshed during R11.G-S4 baseline diff. 18 pre-existing failures documented across 6 source arcs (R11.B chrome, M5 Coverage Campaign, MCPT v3.1, Phase 4C, R11.F). All verified non-regression — landed via PRs that pre-dated the v1.2 capture moment but were never folded into the baseline. R11.G introduced **0 new failures**.
- **v1.2 (2026-05-20):** Post closeout-residuals triage — 0 failures, all 9 previously-failing files resolved.
- **v1.1 (2026-05-20):** Post-R10 merge — 16 failures / 9 files.
- **v1.0 (2026-05-19):** Pre-R7 baseline — 21 failures.

---

## Pre-existing failures (v1.3) — 18 failures across 10 files

### Group 1 — R11.B chrome (inline citation parity) — 8 failures, 4 files

These tests were written for the pre-R11.B API (`CitationSidePanel`, `CitationCtx`, `enrichedOnPin`). R11.B removed `CitationSidePanel` from `ConsumeChatV2` and replaced it with inline `NumberedCitation` rendering (commit `d98bb16b`, PR #144). Tests assert the old shape.

| File | Failures | Root cause |
|------|----------|------------|
| `tests/unit/chat-v2/citation_ui.test.ts` | 3 | Asserts `CitationSidePanel`, `CitationCtx`, `v2-citation-panel` testid — removed in R11.B |
| `tests/unit/chat-v2/citation_rich_payload.test.ts` | 4 | Asserts `enrichedOnPin` / `renderWithCitations` / `onPin` signature — removed in R11.B inline rewrite |
| `tests/unit/chat-v2/markdown_render_v2.test.ts` | 1 | `citation count still computed for drawer badge in V2AssistantText` — drawer badge removed |
| `tests/visual/R11B_brand_preservation.spec.ts` | 0 test cases | File-level fail: runner finds the file but no `it()`/`test()` blocks execute (spec has 0 assertions) |

Specific failing test names:
- `ConsumeChatV2 β4 citation wiring > imports CitationSidePanel`
- `ConsumeChatV2 β4 citation wiring > uses CitationCtx (citation context)`
- `ConsumeChatV2 β4 citation wiring > uses v2-citation-panel test ID (from CitationSidePanel)`
- `C.3 — rich data-citation payload consumed > CitationContextValue.onPin accepts snippet and layer optional params`
- `C.3 — rich data-citation payload consumed > handlePin uses snippet and layer params (not hardcoded empty string)`
- `C.3 — rich data-citation payload consumed > V2AssistantText calls onPin with enriched snippet and layer`
- `C.3 — rich data-citation payload consumed > renderWithCitations is called with enrichedOnPin (not bare onPin)`
- `B.4 — streamdown in V2AssistantText > citation count still computed for drawer badge in V2AssistantText`

---

### Group 2 — M5 Coverage Campaign (retrieval capability spec gap) — 2 failures, 1 file

6 tools were added to `RETRIEVAL_TOOLS` during M5 Coverage Campaign (COV-S4/S5) without corresponding entries in `RETRIEVAL_CAPABILITY_SPEC`. The coverage test enforces 1:1 parity.

| File | Failures | Missing tools |
|------|----------|---------------|
| `src/lib/router/__tests__/retrieval_capability_spec.test.ts` | 2 | `query_muhurat`, `query_jaimini_drishti`, `query_v7_additions`, `query_ucn_walk`, `query_cdlm_lookup`, `query_rm_walk` |

Specific failing test names:
- `RETRIEVAL_CAPABILITY_SPEC × RETRIEVAL_TOOLS coverage > every runtime tool has a planner spec entry`
- `RETRIEVAL_CAPABILITY_SPEC × RETRIEVAL_TOOLS coverage > spec entry count matches runtime tool count exactly`

---

### Group 3 — MCP Transformation v3.1 (MCPT schema + component changes) — 5 failures, 2 files

MCPT v3.1 changed `PipelinePlanSchema` (audience_tier handling) and the `PredictionsCalibration` dashboard component (tool name references). Tests assert the pre-MCPT shape.

| File | Failures | Root cause |
|------|----------|------------|
| `src/lib/__tests__/mcp/red_team/plan_escalation.test.ts` | 2 | `PipelinePlanSchema` no longer parses the test's expected shape (audience_tier validation changed in MCPT) |
| `test/admin/mcp/health/dashboard_components.test.tsx` | 3 | `PredictionsCalibration` no longer renders `log_prediction`/`record_outcome` tool names in the expected DOM location |

Specific failing test names:
- `RT-08a: PipelinePlanSchema parses a plan with client-tier audience_tier`
- `RT-08b: PipelinePlanSchema parses a tampered plan with super_admin audience_tier`
- `PredictionsCalibration > renders placeholder heading`
- `PredictionsCalibration > renders the preview table rows`
- `PredictionsCalibration > mentions log_prediction and record_outcome tools`

---

### Group 4 — Phase 4C (Muhurat format changes) — 2 failures, 2 files

Phase 4C changed the Muhurat Finder navigation prompt format and the sidecar integration test's expected breakdown dict shape.

| File | Failures | Root cause |
|------|----------|------------|
| `src/app/panchang/__tests__/MuhuratFinderModal.test.tsx` | 1 | `Ask Madhav` button navigation prompt format changed in Phase 4C enrichment |
| `tests/integration/test_muhurat_finder_e2e.test.ts` | 1 | Live sidecar integration test asserts breakdown dict format that changed in 4C enrichment; also requires live sidecar without env guard |

Specific failing test names:
- `MuhuratResultsList > inline actions > Ask Madhav button navigates with prompt containing event and rank`
- `Muhurat Finder E2E — live sidecar (AC.4C6S4.1) > Each result window carries a non-empty breakdown dict with contribution values`

---

### Group 5 — R11.F (route.ts API shape change) — 1 failure, 1 file

R11.F dispatch wiring changed how `orchestrator.synthesize()` returns are destructured in route.ts. Test asserts the pre-R11.F destructuring pattern.

| File | Failures | Root cause |
|------|----------|------------|
| `tests/integration/chat-v2/cost_data_part.test.ts` | 1 | `route destructures usageHolder from orchestrator.synthesize()` — R11.F dispatch changed this path |

Specific failing test name:
- `B.8 — cost data part emission (O1) > route destructures usageHolder from orchestrator.synthesize()`

---

## Verification: R11.G introduced 0 new failures

R11.G files touched (G-S1 through G-S3):
- `platform/src/app/api/chat/consume/route.ts`
- `platform/src/components/consume/ConsumeChatV2.tsx`
- `platform/src/components/consume/SettingsDropdown.tsx` (NEW)
- `platform/src/lib/synthesis/mcp_tool_executor.ts` (NEW)
- `platform/tests/components/consume/SettingsDropdown.test.tsx` (NEW)
- `platform/tests/lib/chat-v2/useMultiProviderParity.test.tsx`
- `platform/tests/providers/agentic-loop-engine.test.ts`

**None of the 10 failing test files were modified by R11G.** Confirmed via `git log 9aa14856..HEAD --name-only` at G-S4 run time.

---

## Resolved files since v1.1 (still GREEN in v1.3)

All 9 files resolved in v1.2 remain GREEN:

| File | Fix applied |
|------|-------------|
| `src/lib/panchang/__tests__/ics_builder.test.ts` | npm install — ical-generator |
| `tests/integration/test_query_panchanga_e2e.test.ts` | env guard (requires DB creds) |
| `tests/component/chat-v2/r5/sidebar-background.test.tsx` | DELETED (stale R5 test) |
| `tests/consume/PostAnswerProvenance.test.tsx` | expand-before-assert flow fix |
| `src/components/performance/__tests__/KpiTile.test.tsx` | CSS variable assertion update |
| `src/lib/components/aiops/__tests__/AuditRail.test.tsx` | ACTION_DISPLAY label update |
| `src/lib/components/aiops/__tests__/CostConfirmDialog.test.tsx` | heading role + button text update |
| `src/lib/components/aiops/__tests__/ParamOverrideRow.test.tsx` | button label + PARAM_DISPLAY names |
| `src/scripts/etl/__tests__/msr_parser.test.ts` | MSR version string update |

---

## Historical baselines

- **v1.0** (2026-05-19, pre-R7): 21 failures
- **v1.1** (2026-05-20, post-R10 merge): 16 failures / 9 files
- **v1.2** (2026-05-20, closeout-residuals): 0 failures — all resolved
- **v1.3** (2026-05-23, R11.G-S4 refresh): 18 failures / 10 files — all pre-existing, 0 R11.G regressions

*v1.0 authored 2026-05-19 by merge-train conductor. v1.1 updated 2026-05-20 post-R10 merge. v1.2 updated 2026-05-20 closeout-residuals triage. v1.3 updated 2026-05-23 R11.G-S4 baseline refresh.*
