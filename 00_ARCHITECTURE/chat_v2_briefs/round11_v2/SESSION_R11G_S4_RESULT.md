---
artifact: SESSION_R11G_S4_RESULT
version: 2.0
status: PASS
created: 2026-05-23
updated: 2026-05-23
session: G-S4 — Vitest Stabilization + Baseline Diff (retry after operator-approved baseline update)
arc: R11G
baseline_version: v1.3
---

# G-S4 — Full Vitest Stabilization + Baseline Diff (Retry)

## STATUS: PASS

**Reason:** 18 failures detected; all 18 match the v1.3 baseline exactly. 0 NEW failures.  
Per brief halt rules: no new failures → STATUS=PASS.

---

## Test Suite Summary

| Metric | Count |
|--------|-------|
| Total test cases | 5007 |
| Passed | **4967** |
| Failed | 18 |
| Skipped | 22 |
| Test files total | 445 |
| Test files failed | 10 |
| Test files passed | 435 |

Command: `cd platform && pnpm vitest run`  
Output: `/tmp/r11g-vitest-s4-retry.txt`

Exact match to v1.3 baseline: `4967 passed / 18 failed / 22 skipped (5007)`.

---

## Baseline

**KNOWN_PRE_EXISTING_FAILURES.md** — v1.3 (2026-05-23, operator-approved refresh)  
Baseline failures documented: **18 failures across 10 files**  
Source arcs: R11.B chrome, M5 Coverage Campaign, MCPT v3.1, Phase 4C, R11.F

---

## NEW Failures (vs v1.3 baseline)

**COUNT: 0**

No test failure in this run is absent from the v1.3 documented list.

---

## Pre-Existing Failures Still Present (expected ≤18)

**COUNT: 18** — all 18 documented v1.3 failures confirmed present.

### Group 1 — R11.B chrome (inline citation parity) — 8 failures, 4 files

| Test name | File |
|-----------|------|
| `ConsumeChatV2 β4 citation wiring > imports CitationSidePanel` | `tests/unit/chat-v2/citation_ui.test.ts` |
| `ConsumeChatV2 β4 citation wiring > uses CitationCtx (citation context)` | `tests/unit/chat-v2/citation_ui.test.ts` |
| `ConsumeChatV2 β4 citation wiring > uses v2-citation-panel test ID (from CitationSidePanel)` | `tests/unit/chat-v2/citation_ui.test.ts` |
| `C.3 > CitationContextValue.onPin accepts snippet and layer optional params` | `tests/unit/chat-v2/citation_rich_payload.test.ts` |
| `C.3 > handlePin uses snippet and layer params (not hardcoded empty string)` | `tests/unit/chat-v2/citation_rich_payload.test.ts` |
| `C.3 > V2AssistantText calls onPin with enriched snippet and layer` | `tests/unit/chat-v2/citation_rich_payload.test.ts` |
| `C.3 > renderWithCitations is called with enrichedOnPin (not bare onPin)` | `tests/unit/chat-v2/citation_rich_payload.test.ts` |
| `B.4 > citation count still computed for drawer badge in V2AssistantText` | `tests/unit/chat-v2/markdown_render_v2.test.ts` |

Note: `tests/visual/R11B_brand_preservation.spec.ts` — 0 test cases (file-level fail, matches baseline).

### Group 2 — M5 Coverage Campaign (retrieval capability spec gap) — 2 failures, 1 file

| Test name | File |
|-----------|------|
| `RETRIEVAL_CAPABILITY_SPEC × RETRIEVAL_TOOLS coverage > every runtime tool has a planner spec entry` | `src/lib/router/__tests__/retrieval_capability_spec.test.ts` |
| `RETRIEVAL_CAPABILITY_SPEC × RETRIEVAL_TOOLS coverage > spec entry count matches runtime tool count exactly` | `src/lib/router/__tests__/retrieval_capability_spec.test.ts` |

### Group 3 — MCP Transformation v3.1 — 5 failures, 2 files

| Test name | File |
|-----------|------|
| `RT-08a: PipelinePlanSchema parses a plan with client-tier audience_tier` | `src/lib/__tests__/mcp/red_team/plan_escalation.test.ts` |
| `RT-08b: PipelinePlanSchema parses a tampered plan with super_admin audience_tier` | `src/lib/__tests__/mcp/red_team/plan_escalation.test.ts` |
| `PredictionsCalibration > renders placeholder heading` | `test/admin/mcp/health/dashboard_components.test.tsx` |
| `PredictionsCalibration > renders the preview table rows` | `test/admin/mcp/health/dashboard_components.test.tsx` |
| `PredictionsCalibration > mentions log_prediction and record_outcome tools` | `test/admin/mcp/health/dashboard_components.test.tsx` |

### Group 4 — Phase 4C (Muhurat format changes) — 2 failures, 2 files

| Test name | File |
|-----------|------|
| `MuhuratResultsList > inline actions > Ask Madhav button navigates with prompt containing event and rank` | `src/app/panchang/__tests__/MuhuratFinderModal.test.tsx` |
| `Muhurat Finder E2E > Each result window carries a non-empty breakdown dict with contribution values` | `tests/integration/test_muhurat_finder_e2e.test.ts` |

### Group 5 — R11.F (route.ts API shape change) — 1 failure, 1 file

| Test name | File |
|-----------|------|
| `B.8 — cost data part emission (O1) > route destructures usageHolder from orchestrator.synthesize()` | `tests/integration/chat-v2/cost_data_part.test.ts` |

---

## Resolved Failures (in v1.3 baseline, no longer failing)

**COUNT: 0**

All 18 v1.3 documented failures are still present. No failures resolved in this run.

---

## R11.G Regression Confirmation

R11.G modified files (G-S1 through G-S3):
- `platform/src/app/api/chat/consume/route.ts`
- `platform/src/components/consume/ConsumeChatV2.tsx`
- `platform/src/components/consume/SettingsDropdown.tsx` (NEW)
- `platform/src/lib/synthesis/mcp_tool_executor.ts` (NEW)
- `platform/tests/components/consume/SettingsDropdown.test.tsx` (NEW)
- `platform/tests/lib/chat-v2/useMultiProviderParity.test.tsx`
- `platform/tests/providers/agentic-loop-engine.test.ts`

**None of the 10 failing test files were modified by R11G.** All failures pre-date this arc.

---

## Verdict

STATUS=PASS — 0 new failures; 18 pre-existing (all in v1.3 baseline); 0 resolved.  
R11.G introduced 0 regressions across the full 5007-test suite.

---

*SESSION_R11G_S4_RESULT.md v2.0 — authored 2026-05-23 by G-S4 vitest stabilization session (retry after operator-approved v1.3 baseline update)*
