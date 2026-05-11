---
artifact: CLAUDECODE_BRIEF.md
status: COMPLETE
session_id: Planner-Eval-S1
phase: PLANNER_PROMPT_v2_0 Golden-Set Eval
executor: claude-code-extension (anti-gravity VS Code)
run_from_worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-pipeline
authored_by: Cowork (Abhisek session 2026-05-11)
authored_on: 2026-05-11
acceptance_criteria_count: 12
supersedes: Pipeline-Transform-S1 (COMPLETE 2026-05-11)
---

# Planner-Eval-S1 — PLANNER_PROMPT_v2_0 Golden-Set Eval

## §0 — HOW TO READ THIS BRIEF

**Run from the worktree:** `/Users/Dev/Vibe-Coding/Apps/Madhav-pipeline`
(branch `feature/pipeline-transform-s1`). That is where `callPipelinePlanner`
and `PLANNER_PROMPT_v2_0.md` live. Do NOT run from the main `Madhav/` folder —
`manifest_planner.ts` no longer exists there.

When all 12 ACs are GREEN, set `status: COMPLETE` in this frontmatter and stop.
Do not emit SESSION_OPEN or SESSION_CLOSE artifacts.

---

## §1 — CONTEXT

**Pipeline-Transform-S1 is COMPLETE (2026-05-11).** `callPipelinePlanner` now
uses `PLANNER_PROMPT_v2_0.md`. The eval harness (3 files) still imports the
deleted `manifest_planner.ts` / `router/router.ts` and will fail on import.

**v1.7 baseline** (last scored run, BHISMA-W2-S-D):
- `avg_tool_recall: 0.940`
- `avg_tool_precision: 0.945`
- golden set: 29 entries across 6 categories
- prompt: `PLANNER_PROMPT_v1_0.md` v1.7

**What changed in v2.0:**
- 8-class `query_class` enum (was 6; added `factual`, `cross_domain`, `discovery`,
  `cross_native`; removed `planetary`, `single_answer`)
- New `asset_bundle[]` output field (6 canonical docs: FORENSIC, CGM, UCN,
  CDLM, RM, LEL)
- New `synthesis_guidance` output field
- New eval criterion: `asset_bundle_accuracy` (§5 rubric, 6th criterion)

**Goal:** verify recall + precision at or above v1.7 baseline, plus establish
the first `asset_bundle_recall` baseline score.

---

## §2 — MANDATORY READING BEFORE WRITING ANY CODE

```
platform/tests/eval/planner_smoke_runner.ts        (fix imports — primary target)
platform/tests/eval/planner_regression_gate.test.ts (fix mock path)
platform/tests/eval/planner_ab_compare.ts           (repurpose — classify side dead)
platform/tests/eval/planner_golden_set.json         (extend with required_asset_ids)
platform/src/lib/pipeline/pipeline_planner.ts       (the function being called)
platform/src/lib/pipeline/types.ts                  (PipelinePlan + PlannerFn compat check)
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md §2 + §5      (new schema fields + rubric)
```

---

## §3 — PHASE 1: Fix broken eval imports (surgical — 3 files)

### 3A. planner_smoke_runner.ts

Two lines to change in the `main()` function at the bottom of the file:

**Change 1** — swap import (line ~248):
```ts
// REMOVE:
const { callLlmPlanner } = await import('@/lib/pipeline/manifest_planner')
// ADD:
const { callPipelinePlanner } = await import('@/lib/pipeline/pipeline_planner')
```

**Change 2** — swap function name in the wrapper (line ~251):
```ts
// REMOVE:
const plannerFn: PlannerFn = (query, history, modelIdArg, chartIdArg) =>
  callLlmPlanner(query, history, modelIdArg, chartIdArg)
// ADD:
const plannerFn: PlannerFn = (query, history, modelIdArg, chartIdArg) =>
  callPipelinePlanner(query, history, modelIdArg, chartIdArg)
```

**Change 3** — extend `PlannerFn` return type to carry `asset_bundle` for Phase 2
scoring. Find the `PlannerFn` type declaration and change:
```ts
// REMOVE:
) => Promise<{ tool_calls: Array<{ tool_name: string }> }>
// ADD:
) => Promise<{
  tool_calls: Array<{ tool_name: string }>
  asset_bundle?: Array<{ asset_id: string }>
}>
```
This is backward-compatible: the regression gate mock only provides `tool_calls`
and the optional `asset_bundle` will be `undefined` there (skip scoring for mock runs).

**Change 4** — extend `EvalResult` interface with optional asset_bundle fields:
```ts
// Add to EvalResult:
asset_bundle_ids?: string[]        // what the planner actually emitted
asset_bundle_recall?: number       // |predicted ∩ required| / |required|
asset_bundle_floor_ok?: boolean    // FORENSIC + CGM both present
```

**Change 5** — extend `AggregateResult` interface:
```ts
// Add to AggregateResult:
avg_asset_bundle_recall?: number   // undefined if golden set has no required_asset_ids
asset_bundle_floor_violations?: number  // entries where FORENSIC or CGM missing
```

**Change 6** — extend `scoreEntry` to accept and score `asset_bundle`:
```ts
export function scoreEntry(
  entry: GoldenEntry,       // GoldenEntry will gain required_asset_ids in Phase 2
  predicted: string[],
  error?: string,
  predictedAssets?: string[],  // NEW optional arg
): EvalResult {
  // ... existing recall/precision scoring unchanged ...

  // Asset bundle scoring (only when both args present):
  let asset_bundle_ids: string[] | undefined
  let asset_bundle_recall: number | undefined
  let asset_bundle_floor_ok: boolean | undefined

  if (predictedAssets !== undefined) {
    asset_bundle_ids = predictedAssets
    const floor = ['FORENSIC', 'CGM']
    asset_bundle_floor_ok = floor.every(id => predictedAssets.includes(id))
    const required = (entry as GoldenEntry & { required_asset_ids?: string[] })
      .required_asset_ids ?? floor
    const hit = required.filter(id => predictedAssets.includes(id)).length
    asset_bundle_recall = required.length > 0 ? hit / required.length : 1
  }

  return {
    ...existingReturn,
    asset_bundle_ids,
    asset_bundle_recall,
    asset_bundle_floor_ok,
  }
}
```

**Change 7** — in `runSmoke`, extract `asset_bundle` from the planner response
and pass to `scoreEntry`:
```ts
// After extracting predicted tools, also extract asset_bundle:
const predictedAssets = plan.asset_bundle?.map(a => a.asset_id)
const scored = scoreEntry(entry, predicted, error, predictedAssets)
```

**Change 8** — in `aggregateResults`, compute `avg_asset_bundle_recall` and
`asset_bundle_floor_violations` from the results array.

**Change 9** — in `formatSummary`, add an asset_bundle section after the
existing per-entry table:
```
ASSET BUNDLE RECALL
  avg_asset_bundle_recall: X.XXX   (threshold: ≥ 0.90)
  floor_violations (missing FORENSIC or CGM): N
```

**AC-P1-1:** `npx tsc --noEmit` from `platform/` — zero errors in `src/` and
`tests/eval/planner_smoke_runner.ts` after changes.

---

### 3B. planner_regression_gate.test.ts

One change — swap the vi.mock path:
```ts
// REMOVE:
vi.mock('@/lib/pipeline/manifest_planner', () => ({
  callLlmPlanner: vi.fn(),
}))
// ADD:
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  callPipelinePlanner: vi.fn(),
}))
```

No other changes needed — the test uses `runSmoke` with a mock `PlannerFn`
directly; it never calls `callLlmPlanner` after the import fix.

**AC-P1-2:** `npx vitest run platform/tests/eval/planner_regression_gate.test.ts`
— 2/2 tests pass.

---

### 3C. planner_ab_compare.ts

`classify()` is deleted. Repurpose this script: replace the "classify" side
with a **perfect oracle** (returns `entry.expected_tools` directly from the
golden set, representing a theoretical perfect recall=1.0 / precision=1.0
baseline). This makes the comparison "oracle perfect vs v2.0 actual" — a useful
signal for seeing how far v2.0 is from the gold standard.

**Changes:**
1. Remove `await import('@/lib/router/router')` entirely.
2. Change `await import('@/lib/pipeline/manifest_planner')` →
   `await import('@/lib/pipeline/pipeline_planner')` and rename `callLlmPlanner`
   → `callPipelinePlanner`.
3. Replace the classify side stub and live-classify path with a single oracle stub:
```ts
// Oracle side always returns the golden set's expected_tools (perfect recall/precision)
const oracleSide: SideResult = {
  side: 'oracle',
  predicted_tools: entry.expected_tools,
}
```
4. Update header comments + `--help` output to reflect "oracle vs v2.0".
5. Remove `CLASSIFY_AUDIENCE` env var reference.

**AC-P1-3:** `npx tsc --noEmit` — zero errors in `tests/eval/planner_ab_compare.ts`.

---

## §4 — PHASE 2: Extend golden set with required_asset_ids

Read `platform/tests/eval/planner_golden_set.json` fully. Add `required_asset_ids`
to every entry using the mapping rules below. Do NOT change any existing field.

**Mapping rules (derived from PLANNER_PROMPT_v2_0.md §3 rules R21–R26):**

| query_class | required_asset_ids |
|---|---|
| factual | `["FORENSIC", "CGM"]` |
| interpretive | `["FORENSIC", "CGM", "UCN"]` |
| predictive | `["FORENSIC", "CGM", "LEL"]` |
| cross_domain | `["FORENSIC", "CGM", "UCN", "CDLM"]` |
| discovery | `["FORENSIC", "CGM", "UCN"]` |
| holistic | `["FORENSIC", "CGM", "UCN", "CDLM"]` |
| remedial | `["FORENSIC", "CGM", "RM"]` |
| cross_native | `["FORENSIC", "CGM"]` |

For the 3 entries whose `category` is `"planetary"` (which map to `factual`
query_class): use `["FORENSIC", "CGM"]`.

For edge_case entries (GT.027 empty-query, GT.028 single-punctuation): use
`["FORENSIC", "CGM"]` — degenerate inputs should still floor-load the chart.

Also update `$schema_version` from `"1.0"` → `"1.1"` and add to `field_notes`:
```json
"required_asset_ids": "Minimum set of canonical document IDs (asset_id values
  from CAPABILITY_MANIFEST.json) that a correct planner MUST include in
  asset_bundle[]. Grounded in PLANNER_PROMPT_v2_0.md rules R21–R26.
  FORENSIC and CGM are floor assets required for every entry."
```

**AC-P2-1:** `jq '.entries | length' platform/tests/eval/planner_golden_set.json`
returns 29 (no entries added or removed).

**AC-P2-2:** `jq '[.entries[] | select(.required_asset_ids == null)] | length'
platform/tests/eval/planner_golden_set.json` returns 0 (every entry has the field).

**AC-P2-3:** `jq '[.entries[] | select(.required_asset_ids | index("FORENSIC") == null)] | length'
platform/tests/eval/planner_golden_set.json` returns 0 (FORENSIC in every entry).

---

## §5 — PHASE 3: Run the eval and report

**Before running:** confirm the CHART_ID environment variable is set to the
production chart ID for Abhisek Mohanty. Check `platform/.env.local` or
`platform/.env` for `CHART_ID` or look at how `callPipelinePlanner` resolves
the chart. If not found, check the golden set's `native_context` — the chart
ID is not stored there. The eval can run with `CHART_ID=test-native` for
scoring purposes (the planner uses chart context to parameterise tool calls but
the golden-set scoring only measures tool selection, not param values).

**Run command:**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-pipeline/platform
PLANNER_MODEL_ID=nvidia/llama-3.3-nemotron-super-49b-v1 \
  npx tsx --conditions=react-server \
  tests/eval/planner_smoke_runner.ts \
  2>eval_stderr.log | tee eval_results.json
cat eval_stderr.log
```

If NIM is unavailable, retry with the Anthropic stack:
```bash
PLANNER_MODEL_ID=claude-haiku-4-5-20251001 \
  npx tsx --conditions=react-server \
  tests/eval/planner_smoke_runner.ts \
  2>eval_stderr.log | tee eval_results.json
```

**AC-P3-1:** Eval runs to completion (all 29 entries scored, zero entries with
`"error"` field set to a non-null value caused by import failures).

**AC-P3-2:** `avg_tool_recall ≥ 0.940` (v1.7 baseline — must match or exceed).

**AC-P3-3:** `avg_tool_precision ≥ 0.945` (v1.7 baseline — must match or exceed).

**AC-P3-4:** `avg_asset_bundle_recall ≥ 0.90` (first baseline — floor + class-specific assets).

**AC-P3-5:** `asset_bundle_floor_violations = 0` (FORENSIC + CGM present in
every non-error plan).

**If AC-P3-2 or AC-P3-3 fail** (recall or precision regresses vs v1.7):
- Print the full per-entry results from `eval_results.json`.
- Group failing entries by category.
- Do NOT attempt to fix the prompt in this session. Record the regression
  findings as a file: `platform/tests/eval/eval_results_planner_eval_s1.json`
  (copy of `eval_results.json`) + `platform/tests/eval/REGRESSION_NOTES_v2_0.md`
  (structured findings: which categories regressed, what the planner produced
  vs expected). The prompt fix is a separate session (Planner-Prompt-Fix-S1).
  Still set `status: COMPLETE` on this brief — the eval ran and findings are
  recorded.

---

## §6 — PHASE 4: Persist results and update governance

### 6A. Save eval results

Write the eval output to a permanent file:
```
platform/tests/eval/eval_results_planner_eval_s1.json
```
Content: the full JSON from `eval_results.json` (aggregate + per-entry results).

### 6B. Update regression_baseline.json if needed

If any golden-set entries were updated (none should be — Phase 2 only adds
`required_asset_ids`), verify `fixtures/regression_baseline.json` still covers
all 29 entry IDs. The coverage check is AC-P1-2's first assertion.

### 6C. Update CURRENT_STATE_v1_0.md

In `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`, find the `pipeline_transform_s1`
concurrent workstream block. Add below it:
```yaml
    planner_eval_s1:
      date: 2026-05-11
      phase_status: COMPLETE
      prompt_version: PLANNER_PROMPT_v2_0.md
      golden_set_version: "1.1"
      entries_scored: 29
      avg_tool_recall: <actual value>
      avg_tool_precision: <actual value>
      avg_asset_bundle_recall: <actual value>
      asset_bundle_floor_violations: <actual value>
      vs_v1_7_baseline: recall_delta=<+/−X.XXX> precision_delta=<+/−X.XXX>
      regression: <NONE | list of failing entry IDs>
      result_artifact: platform/tests/eval/eval_results_planner_eval_s1.json
```

### 6D. Append to SESSION_LOG.md

```
session_id: Planner-Eval-S1
date: 2026-05-11
summary: >
  PLANNER_PROMPT_v2_0 golden-set eval. 29 entries scored.
  recall=<X.XXX> precision=<X.XXX> asset_bundle_recall=<X.XXX>.
  v1.7 baseline: recall=0.940 precision=0.945.
  Delta: recall<+/−X.XXX> precision<+/−X.XXX>.
  <PASS | REGRESSION — see REGRESSION_NOTES_v2_0.md>
```

**AC-P4-1:** `eval_results_planner_eval_s1.json` exists and is valid JSON with
`aggregate` + `results` fields.

**AC-P4-2:** `CURRENT_STATE_v1_0.md` `planner_eval_s1` block present with all
numeric fields filled in.

---

## §7 — ACCEPTANCE CRITERIA (complete checklist — 12 items)

### Phase 1 — Fix imports (3 criteria)
- [ ] **AC-P1-1** `npx tsc --noEmit` — 0 errors in `planner_smoke_runner.ts`
- [ ] **AC-P1-2** `planner_regression_gate.test.ts` — 2/2 vitest pass
- [ ] **AC-P1-3** `npx tsc --noEmit` — 0 errors in `planner_ab_compare.ts`

### Phase 2 — Golden set extension (3 criteria)
- [ ] **AC-P2-1** 29 entries, none added/removed
- [ ] **AC-P2-2** Every entry has `required_asset_ids`
- [ ] **AC-P2-3** FORENSIC present in every `required_asset_ids`

### Phase 3 — Eval run (5 criteria)
- [ ] **AC-P3-1** 29 entries scored, 0 import-failure errors
- [ ] **AC-P3-2** `avg_tool_recall ≥ 0.940`
- [ ] **AC-P3-3** `avg_tool_precision ≥ 0.945`
- [ ] **AC-P3-4** `avg_asset_bundle_recall ≥ 0.90`
- [ ] **AC-P3-5** `asset_bundle_floor_violations = 0`

### Phase 4 — Governance (1 criterion)
- [ ] **AC-P4-1** `eval_results_planner_eval_s1.json` exists with full results

---

## §8 — MAY TOUCH / MUST NOT TOUCH

### may_touch
```
platform/tests/eval/planner_smoke_runner.ts
platform/tests/eval/planner_regression_gate.test.ts
platform/tests/eval/planner_ab_compare.ts
platform/tests/eval/planner_golden_set.json
platform/tests/eval/eval_results_planner_eval_s1.json   (CREATE)
platform/tests/eval/REGRESSION_NOTES_v2_0.md            (CREATE — only if regression found)
00_ARCHITECTURE/CURRENT_STATE_v1_0.md                   (planner_eval_s1 block only)
00_ARCHITECTURE/SESSION_LOG.md                          (append only)
```

### must_not_touch
```
platform/tests/eval/fixtures/regression_baseline.json   (read-only; update only if coverage breaks)
platform/src/**                                         (platform source is FROZEN for this session)
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md                  (read-only; prompt fix is a separate session)
platform/tests/eval/planner_golden_set.json             (only add required_asset_ids — no other field changes)
CLAUDE.md
```

---

## §9 — KNOWN OUT-OF-SCOPE

1. **Prompt fixes** — if AC-P3-2 or AC-P3-3 fail, record the regression and
   stop. Do not edit `PLANNER_PROMPT_v2_0.md` in this session.
2. **PR merge** — `feature/pipeline-transform-s1` is awaiting native PR review.
   Do not merge in this session.
3. **M5 open** — PHASE_M5_PLAN_v1_0.md authoring is the session after this one.
4. **Varga CPB** — D12–D19 are running in parallel on `feature/varga-etl-full-s1`.

---

## §10 — COMPLETION SEQUENCE

When all 12 ACs are PASS:

1. Set `status: COMPLETE` in this file's frontmatter.
2. Commit all changes to `feature/pipeline-transform-s1`:
   ```bash
   git add platform/tests/eval/ 00_ARCHITECTURE/CURRENT_STATE_v1_0.md \
     00_ARCHITECTURE/SESSION_LOG.md CLAUDECODE_BRIEF.md
   git commit -m "eval(Planner-Eval-S1): PLANNER_PROMPT_v2_0 golden-set eval COMPLETE

   recall=<X.XXX> precision=<X.XXX> asset_bundle_recall=<X.XXX>
   v1.7 delta: recall<+/−X.XXX> precision<+/−X.XXX>
   29/29 entries scored. eval_results_planner_eval_s1.json written.
   golden_set.json v1.0→v1.1 (required_asset_ids added).
   eval harness: callLlmPlanner→callPipelinePlanner; classify→oracle."
   ```
3. Print the final 12-item AC checklist with PASS/FAIL.

---

*CLAUDECODE_BRIEF.md · Planner-Eval-S1 · 2026-05-11*
*12 acceptance criteria: eval harness repair + golden-set extension + eval run*
*Supersedes Pipeline-Transform-S1 (COMPLETE 2026-05-11)*
