---
artifact: CLAUDECODE_BRIEF.md
status: COMPLETE
session_id: Planner-Prompt-Fix-S1
phase: PLANNER_PROMPT_v2_0 Precision Regression Fix
executor: claude-code-extension (anti-gravity VS Code)
run_from_worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-pipeline
authored_by: Cowork (Abhisek session 2026-05-11)
authored_on: 2026-05-11
acceptance_criteria_count: 10
supersedes: Planner-Eval-S1 (COMPLETE 2026-05-11, commit 58a2ad4)
---

# Planner-Prompt-Fix-S1 — Precision Regression Fix

## §0 — HOW TO READ THIS BRIEF

**Run from the worktree:** `/Users/Dev/Vibe-Coding/Apps/Madhav-pipeline`
(branch `feature/pipeline-transform-s1`). That is where `PLANNER_PROMPT_v2_0.md`,
`callPipelinePlanner`, and all eval artifacts live.

When all 10 ACs are GREEN, set `status: COMPLETE` in this frontmatter and stop.
Do not emit SESSION_OPEN or SESSION_CLOSE artifacts.

---

## §1 — CONTEXT AND PROBLEM

**Planner-Eval-S1 (2026-05-11, commit 58a2ad4) revealed a precision regression:**

| Metric | v1.7 baseline | v2.0 result | Delta |
|---|---|---|---|
| avg_tool_recall | 0.940 | 0.945 | **+0.005 ✅** |
| avg_tool_precision | 0.945 | 0.852 | **−0.093 ❌** |
| avg_asset_bundle_recall | — (new) | 0.902 | ✅ first baseline |
| floor_violations | — | 2 | ❌ GT.027, GT.028 |

**Recall held; precision dropped sharply.** Classic symptom: the v2.0 prompt causes
the planner to predict *more tools than the gold standard expects* — over-inclusion.

**What changed v1.7 → v2.0 that could cause over-inclusion:**
- Expanded `query_class` enum (8 vs 6 classes; new `discovery`, `cross_domain`, `factual`,
  `cross_native` may invoke wider tool selection rules)
- New `asset_bundle` output field (rules R21–R26) — bundle selection is separate from
  tool selection, but ambiguous rules could bleed into over-eager tool selection
- New `synthesis_guidance` output field — similarly separate, but prompts are holistic
- `discovery` and `holistic` class rules (§4.6, §4.7) historically trigger large tool sets

**Floor violations (GT.027 empty query, GT.028 single-punctuation):**
The planner returned an empty `asset_bundle` for degenerate inputs, bypassing the
FORENSIC+CGM floor. `bundle_hydrator.ts` enforces the floor at hydration time, but
the planner should still emit the floor assets. These are low-priority vs precision.

---

## §2 — MANDATORY READING BEFORE WRITING ANYTHING

```
platform/tests/eval/REGRESSION_NOTES_v2_0.md       ← READ FIRST. Per-entry breakdown,
                                                       category-level analysis, hypotheses.
platform/tests/eval/eval_results_planner_eval_s1.json ← Per-entry scores (all 29)
platform/tests/eval/planner_golden_set.json         ← v1.1 (29 entries + required_asset_ids)
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md              ← The file to fix
platform/src/lib/pipeline/pipeline_planner.ts       ← How the prompt is loaded/called
```

Do NOT touch any other source files. The eval harness is already fixed (Planner-Eval-S1).

---

## §3 — PHASE 1: Diagnose the regression

### 3A. Read REGRESSION_NOTES_v2_0.md

The executor authored this file after scoring. It contains:
- Per-entry failures: which of the 29 entries had false-positive tools (predicted but
  not in gold standard)
- Category breakdown: which query_class drove the most false positives
- Hypotheses from the executor about root cause

Build a mental model before touching the prompt. Answer:
1. Which 1–3 categories account for most of the precision loss?
2. Are the false positives concentrated on specific tools (e.g., `vector_search`,
   `get_dasha_periods`, `get_chart_data`)?
3. Do the false positives follow a pattern (e.g., "planner adds vector_search to
   every query" or "discovery-class gets too many retrieval tools")?

### 3B. Cross-reference with PLANNER_PROMPT_v2_0.md

For each false-positive pattern identified, locate the rule(s) in the prompt that
could cause it. Candidate sections:
- §4.6 discovery class rules (B.11 whole-chart-read may be triggering extra tools)
- §4.7 holistic class rules
- §4.3 factual class (if factual entries were previously `single_answer` and are
  now getting a broader tool set)
- §4.5 cross_domain rules
- The few-shot examples in §6 (if a few-shot shows a wide tool set, the model
  generalises it too broadly)

**AC-P1-1:** Before any prompt edit, write a brief diagnosis comment at the top
of your first edit explaining: (a) which categories drove the regression; (b) which
specific prompt rules/few-shots are implicated. This is for audit trail.

---

## §4 — PHASE 2: Fix PLANNER_PROMPT_v2_0.md

**Precision-targeted edits only.** Do not change rules that did not regress.
Do not change asset_bundle rules (R21–R26) unless they are the root cause.
Do not change the output schema.

Guiding constraint: **For every edit, state the hypothesis: "This edit reduces
false positives in [category] by [mechanism]."** If you cannot state this,
do not make the edit.

### Permitted categories of fix

1. **Tighten over-broad rules** — if `§4.6 discovery` says "always include
   `vector_search` + `get_chart_data` + `get_dasha_periods`", and the gold standard
   for discovery queries only expects 2 of those 3, narrow the rule.

2. **Add negative constraints** — add a `DO NOT include [tool_X] unless [condition]`
   rule if the planner is systematically adding a tool when it shouldn't.

3. **Fix few-shot contamination** — if a few-shot example in §6 shows a wider
   tool set than the gold standard implies, tighten the few-shot to match
   actual gold expectations.

4. **Floor violation fix (secondary)** — for GT.027/GT.028: add a rule in §2 or §3
   that even for empty/malformed queries, the planner must emit
   `asset_bundle: [{asset_id:"FORENSIC"}, {asset_id:"CGM"}]`. This is defensive;
   `bundle_hydrator.ts` already enforces it at runtime, so this is belt-and-suspenders.

### Prohibited categories of change

- Do NOT change `query_class` enum values (8 classes are correct).
- Do NOT change the output JSON schema.
- Do NOT change rules for categories that did NOT regress (preserves recall).
- Do NOT add new few-shot examples — existing 11 are sufficient.

---

## §5 — PHASE 3: Re-run the eval

After each round of prompt edits, re-run the full 29-entry eval:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-pipeline/platform
PLANNER_MODEL_ID=nvidia/llama-3.3-nemotron-super-49b-v1 \
  npx tsx --conditions=react-server \
  tests/eval/planner_smoke_runner.ts \
  2>eval_stderr.log | tee eval_results_fix_attempt.json
cat eval_stderr.log
```

If NIM unavailable:
```bash
PLANNER_MODEL_ID=claude-haiku-4-5-20251001 \
  npx tsx --conditions=react-server \
  tests/eval/planner_smoke_runner.ts \
  2>eval_stderr.log | tee eval_results_fix_attempt.json
```

**Convergence target (all three must hold simultaneously):**
- `avg_tool_recall ≥ 0.940`
- `avg_tool_precision ≥ 0.945`
- `avg_asset_bundle_recall ≥ 0.90`

**Allowed iterations:** up to 3 rounds of edit+eval. If precision target is not
reached in 3 rounds, record findings and stop — do not keep iterating without
native review. See §8 escape clause.

---

## §6 — PHASE 4: Persist final results and update governance

### 6A. Save final eval results

Write final eval output to:
```
platform/tests/eval/eval_results_planner_prompt_fix_s1.json
```

### 6B. Update REGRESSION_NOTES_v2_0.md

Append a `## Resolution` section at the bottom with:
- What rules were changed and why (one line per rule)
- Final aggregate scores
- Floor violation status (GT.027/GT.028 — fixed or still failing)

### 6C. Append to SESSION_LOG.md (00_ARCHITECTURE/SESSION_LOG.md)

```
session_id: Planner-Prompt-Fix-S1
date: 2026-05-11
summary: >
  Precision regression fix for PLANNER_PROMPT_v2_0.md.
  Pre-fix: recall=0.945 precision=0.852.
  Post-fix: recall=<X.XXX> precision=<X.XXX> asset_bundle_recall=<X.XXX>.
  Rules changed: <list>.
  Floor violations: <0 | 2 (GT.027/GT.028 still failing)>.
```

### 6D. Update CURRENT_STATE_v1_0.md

In `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`, find the `planner_eval_s1`
concurrent workstream block. Add immediately after it:

```yaml
    planner_prompt_fix_s1:
      date: 2026-05-11
      phase_status: COMPLETE
      prompt_version: PLANNER_PROMPT_v2_0.md (in-place patch)
      pre_fix_precision: 0.852
      post_fix_precision: <actual value>
      post_fix_recall: <actual value>
      post_fix_asset_bundle_recall: <actual value>
      floor_violations_resolved: <true|false>
      rules_changed: <list of rule IDs or section references>
      result_artifact: platform/tests/eval/eval_results_planner_prompt_fix_s1.json
```

---

## §7 — ACCEPTANCE CRITERIA (10 items)

### Phase 1 — Diagnosis (1 criterion)
- [ ] **AC-P1-1** Diagnosis comment written before first edit (category + rule cause)

### Phase 2 — Prompt fix (2 criteria)
- [ ] **AC-P2-1** Every edit has a stated hypothesis ("reduces FP in X by Y")
- [ ] **AC-P2-2** No changes to: output schema, query_class enum, asset_bundle schema,
      rules for non-regressing categories, or new few-shot additions

### Phase 3 — Eval convergence (3 criteria)
- [ ] **AC-P3-1** `avg_tool_recall ≥ 0.940` (must not regress recall)
- [ ] **AC-P3-2** `avg_tool_precision ≥ 0.945` (target: recover to baseline)
- [ ] **AC-P3-3** `avg_asset_bundle_recall ≥ 0.90`

### Phase 4 — Governance (4 criteria)
- [ ] **AC-P4-1** `eval_results_planner_prompt_fix_s1.json` written
- [ ] **AC-P4-2** `REGRESSION_NOTES_v2_0.md` has `## Resolution` section
- [ ] **AC-P4-3** `SESSION_LOG.md` entry appended
- [ ] **AC-P4-4** `CURRENT_STATE_v1_0.md` `planner_prompt_fix_s1` block added

---

## §8 — ESCAPE CLAUSE

If after 3 rounds of edit+eval, `avg_tool_precision < 0.945`:
1. Do NOT keep iterating.
2. Record the best result achieved (even if below threshold) in
   `eval_results_planner_prompt_fix_s1.json`.
3. Append to `REGRESSION_NOTES_v2_0.md §Resolution`:
   "3 rounds exhausted. Best precision achieved: X.XXX. Remaining gap: X.XXX.
    Hypothesis for continued regression: [your analysis]. Recommend native review
    before proceeding to Planner-Prompt-Fix-S2."
4. Still mark ACs P4-1 through P4-4 as PASS (governance artifacts created).
5. Mark AC-P3-2 as FAIL.
6. Set `status: COMPLETE` with a note in this frontmatter:
   `status_note: Escape clause invoked — precision recovered to X.XXX (target 0.945)`
7. The overall brief is still COMPLETE per escape clause; Planner-Prompt-Fix-S2
   is the next session.

---

## §9 — MAY TOUCH / MUST NOT TOUCH

### may_touch
```
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md              (precision-targeted edits only)
platform/tests/eval/eval_results_planner_prompt_fix_s1.json  (CREATE)
platform/tests/eval/REGRESSION_NOTES_v2_0.md        (append §Resolution section)
00_ARCHITECTURE/CURRENT_STATE_v1_0.md               (planner_prompt_fix_s1 block only)
00_ARCHITECTURE/SESSION_LOG.md                      (append only)
CLAUDECODE_BRIEF.md                                 (set status: COMPLETE at end)
```

### must_not_touch
```
platform/src/**                                     (platform source FROZEN)
platform/tests/eval/planner_smoke_runner.ts         (already fixed — do not touch)
platform/tests/eval/planner_regression_gate.test.ts (already fixed — do not touch)
platform/tests/eval/planner_golden_set.json         (v1.1 is final — do not touch)
platform/tests/eval/eval_results_planner_eval_s1.json (Planner-Eval-S1 artifact — read-only)
platform/src/lib/pipeline/types.ts                  (schema frozen)
CLAUDE.md
```

---

## §10 — KNOWN OUT-OF-SCOPE

1. **PR merge** — `feature/pipeline-transform-s1` is awaiting native review. Do not
   merge in this session.
2. **M5 open** — PHASE_M5_PLAN_v1_0.md authoring follows after this session.
3. **Varga CPB** — D12–D19 running in parallel on `feature/varga-etl-full-s1`.
4. **Planner model upgrade** — if scores differ substantially between NIM and Haiku,
   record in REGRESSION_NOTES but do not change model selection; that is Planner-Prompt-Fix-S2 scope.

---

## §11 — COMPLETION SEQUENCE

When all 10 ACs are PASS (or escape clause invoked):

1. Set `status: COMPLETE` in this file's frontmatter.
2. Commit all changes to `feature/pipeline-transform-s1`:
   ```bash
   git add 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md \
     platform/tests/eval/eval_results_planner_prompt_fix_s1.json \
     platform/tests/eval/REGRESSION_NOTES_v2_0.md \
     00_ARCHITECTURE/CURRENT_STATE_v1_0.md \
     00_ARCHITECTURE/SESSION_LOG.md \
     CLAUDECODE_BRIEF.md
   git commit -m "fix(planner): PLANNER_PROMPT_v2_0 precision regression remediation

   Pre-fix: recall=0.945 precision=0.852 (Planner-Eval-S1 baseline)
   Post-fix: recall=<X.XXX> precision=<X.XXX> asset_bundle_recall=<X.XXX>
   Rules changed: <list>
   Floor violations: <resolved|still failing GT.027/GT.028>
   29/29 entries scored. eval_results_planner_prompt_fix_s1.json written."
   ```
3. Print the final 10-item AC checklist with PASS/FAIL.

---

*CLAUDECODE_BRIEF.md · Planner-Prompt-Fix-S1 · 2026-05-11*
*10 acceptance criteria: diagnosis + precision-targeted prompt fix + eval convergence*
*Supersedes Planner-Eval-S1 (COMPLETE 2026-05-11, commit 58a2ad4)*
