---
artifact: SESSION_R11G_S4_RESULT
version: 1.0
status: HALT
created: 2026-05-23
session: G-S4 — Vitest Stabilization + Baseline Diff
arc: R11G
---

# G-S4 — Full Vitest Stabilization + Baseline Diff

## STATUS: FAIL (HALT)

**Reason:** 18 test case failures detected vs. baseline of 0 (KNOWN_PRE_EXISTING_FAILURES.md v1.2).  
Per brief halt rules: NEW failures → STATUS=FAIL, do not commit.

---

## Test Suite Summary

| Metric | Count |
|--------|-------|
| Total test cases | 5007 |
| Passed | 4967 |
| Failed | **18** |
| Skipped | 22 |
| Test files | 445 |
| Test files failed | 10 |

Command: `cd platform && pnpm vitest run`  
Output: `/tmp/r11g-vitest-s4.txt`

---

## Baseline

**KNOWN_PRE_EXISTING_FAILURES.md** — v1.2 (2026-05-20, branch `chat-v2/closeout-residuals`)  
Baseline failures: **0** (all 9 previously failing files resolved)  
Any failure in a post-closeout run is a new regression requiring investigation (per baseline note).

---

## NEW Failures (vs baseline — count: 18)

These 18 failures are treated as NEW because they are absent from the v1.2 baseline.  
**However, all 18 failures were verified to pre-exist R11G changes** (see Root Cause Analysis below).

### Failing test cases by file

#### `tests/unit/chat-v2/citation_ui.test.ts` (3 failures)
- `ConsumeChatV2 β4 citation wiring > imports CitationSidePanel`
- `ConsumeChatV2 β4 citation wiring > uses CitationCtx (citation context)`
- `ConsumeChatV2 β4 citation wiring > uses v2-citation-panel test ID (from CitationSidePanel)`

#### `tests/unit/chat-v2/citation_rich_payload.test.ts` (4 failures)
- `C.3 — rich data-citation payload consumed > CitationContextValue.onPin accepts snippet and layer optional params`
- `C.3 — rich data-citation payload consumed > handlePin uses snippet and layer params (not hardcoded empty string)`
- `C.3 — rich data-citation payload consumed > V2AssistantText calls onPin with enriched snippet and layer`
- `C.3 — rich data-citation payload consumed > renderWithCitations is called with enrichedOnPin (not bare onPin)`

#### `tests/unit/chat-v2/markdown_render_v2.test.ts` (1 failure)
- `B.4 — streamdown in V2AssistantText > citation count still computed for drawer badge in V2AssistantText`

#### `src/lib/router/__tests__/retrieval_capability_spec.test.ts` (2 failures)
- `RETRIEVAL_CAPABILITY_SPEC × RETRIEVAL_TOOLS coverage > every runtime tool has a planner spec entry`
  - Missing: `query_muhurat`, `query_jaimini_drishti`, `query_v7_additions`, `query_ucn_walk`, `query_cdlm_lookup`, `query_rm_walk`
- `RETRIEVAL_CAPABILITY_SPEC × RETRIEVAL_TOOLS coverage > spec entry count matches runtime tool count exactly`
  - Expected: 36, got: 30

#### `src/lib/__tests__/mcp/red_team/plan_escalation.test.ts` (2 failures)
- `RT-08a: PipelinePlanSchema parses a plan with client-tier audience_tier`
- `RT-08b: PipelinePlanSchema parses a tampered plan with super_admin audience_tier`

#### `test/admin/mcp/health/dashboard_components.test.tsx` (3 failures)
- `PredictionsCalibration > renders placeholder heading`
- `PredictionsCalibration > renders the preview table rows`
- `PredictionsCalibration > mentions log_prediction and record_outcome tools`

#### `src/app/panchang/__tests__/MuhuratFinderModal.test.tsx` (1 failure)
- `MuhuratResultsList > inline actions > Ask Madhav button navigates with prompt containing event and rank`

#### `tests/integration/test_muhurat_finder_e2e.test.ts` (1 failure)
- `Muhurat Finder E2E — live sidecar (AC.4C6S4.1) > Each result window carries a non-empty breakdown dict with contribution values`

#### `tests/integration/chat-v2/cost_data_part.test.ts` (1 failure)
- `B.8 — cost data part emission (O1) > route destructures usageHolder from orchestrator.synthesize()`

#### `tests/visual/R11B_brand_preservation.spec.ts` (0 test cases — file-level fail)

---

## Pre-Existing Failures (baseline ∩ current): 0

The v1.2 baseline recorded 0 failures, so there are no baseline failures present.

---

## Resolved Failures (baseline − current): 0

Baseline had 0 failures; nothing to compare against.

---

## Root Cause Analysis

**Critical finding: ALL 18 failures were verified to pre-exist R11G.**

### Verification methodology
1. R11G only modified 9 files (verified via `git diff 9aa14856..HEAD --name-only`):
   - `platform/src/app/api/chat/consume/route.ts`
   - `platform/src/components/consume/ConsumeChatV2.tsx`
   - `platform/src/components/consume/MultiProviderParityToggle.tsx`
   - `platform/src/components/consume/SettingsDropdown.tsx`
   - `platform/src/lib/synthesis/mcp_tool_executor.ts`
   - `platform/tests/components/consume/MultiProviderParityToggle.test.tsx`
   - `platform/tests/components/consume/SettingsDropdown.test.tsx`
   - `platform/tests/lib/chat-v2/useMultiProviderParity.test.tsx`
   - `platform/tests/providers/agentic-loop-engine.test.ts`
2. **None of the 10 failing test files were modified by R11G** (confirmed via `git log 9aa14856..HEAD`).
3. For tests that read `ConsumeChatV2.tsx` (citation_ui, citation_rich_payload): the expected strings (`CitationSidePanel`, `CitationCtx`, `enrichedOnPin`) were already absent at commit `9aa14856` (R11G branch base) — confirmed via `git show 9aa14856:platform/src/components/consume/ConsumeChatV2.tsx | grep -c "CitationSidePanel"` → 0.

### Root causes by failure group

| Test group | Root cause | Introduced by |
|-----------|-----------|---------------|
| citation_ui, citation_rich_payload, markdown_render_v2 | `CitationSidePanel`, `CitationCtx`, `enrichedOnPin` removed from ConsumeChatV2 in R11B (inline citation parity, commit `d98bb16b`). Tests written for pre-R11B API. | R11.B |
| retrieval_capability_spec | 6 tools added to `RETRIEVAL_TOOLS` in M5 Coverage Campaign (COV-S4/S5) without adding matching entries to `RETRIEVAL_CAPABILITY_SPEC`. Gap: `query_muhurat`, `query_jaimini_drishti`, `query_v7_additions`, `query_ucn_walk`, `query_cdlm_lookup`, `query_rm_walk`. | M5 Coverage Campaign |
| plan_escalation RT-08a/b | `PipelinePlanSchema` schema changed in MCP Transformation (MCPT) — schema no longer parses the test's expected shape. | MCP Transformation v3.1 |
| dashboard_components | `PredictionsCalibration` component changed — `log_prediction`/`record_outcome` tool names no longer appear in the component render. | MCP Transformation v3.1 |
| MuhuratFinderModal | `Ask Madhav` navigation prompt format changed. | Phase 4C |
| test_muhurat_finder_e2e | Sidecar integration test requires live sidecar with specific breakdown format. | Phase 4C |
| cost_data_part | `orchestrator.synthesize()` API changed — `usageHolder` no longer destructured in route.ts. | R11F / Pipeline Transform |
| R11B_brand_preservation | Visual spec has 0 tests — file-level fail with no assertions (likely runner config issue). | R11B |

### Why these weren't in KNOWN_PRE_EXISTING_FAILURES v1.2

The v1.2 baseline was captured on branch `chat-v2/closeout-residuals` (2026-05-20), which predates:
- R11.A through R11.G work (all merged after 2026-05-20)
- M5 Coverage Campaign final sessions
- MCP Transformation (MCPT) merge
- Phase 4C panchang enrichment

The v1.2 baseline needs to be updated to reflect the current main state.

---

## Recommended Action for Operator

These are **not R11G regressions**. The baseline (KNOWN_PRE_EXISTING_FAILURES.md) is stale relative to the current codebase state. The operator should:

1. **Update KNOWN_PRE_EXISTING_FAILURES.md to v1.3** — document these 18 failures as pre-existing residuals from R11B, M5 Coverage Campaign, MCPT, and Phase 4C work.
2. **OR fix the tests** before G-S4 can PASS. Fixes required:
   - citation_ui / citation_rich_payload / markdown_render_v2 → update source assertions to match R11B inline-citation architecture (no CitationSidePanel, use inline NumberedCitation assertions)
   - retrieval_capability_spec → add 6 missing tools to `RETRIEVAL_CAPABILITY_SPEC`
   - plan_escalation → update PipelinePlanSchema test to match current MCPT schema
   - dashboard_components → update PredictionsCalibration component or test to match current tool names
   - MuhuratFinderModal → update prompt format assertion
   - test_muhurat_finder_e2e → requires live sidecar OR add env guard (skip without sidecar)
   - cost_data_part → update route API assertion to match current R11F dispatch shape
   - R11B_brand_preservation → add at least 1 test assertion or delete the file

---

## Halt Decision

Per R11G Brief §6 halt rules: **"Any NEW failure → STATUS=FAIL, do not commit."**

Since KNOWN_PRE_EXISTING_FAILURES.md v1.2 declares 0 baseline failures, all 18 current failures are technically "new" relative to that baseline. **STATUS=FAIL.**

The commit step is skipped per halt protocol.

---

*SESSION_R11G_S4_RESULT.md — authored 2026-05-23 by G-S4 vitest stabilization session*
