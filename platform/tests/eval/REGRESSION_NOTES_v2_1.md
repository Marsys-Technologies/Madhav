---
artifact: REGRESSION_NOTES_v2_1.md
version: 1.0
status: CURRENT
produced_during: QP-S4 (Pipeline Gap Closure — Eval + Governance Close)
produced_on: 2026-05-12
eval_run: eval_results_pipeline_gap_s1.json
prompt_version: "2.1"
golden_set_version: "1.2"
total_entries: 46
planner_model: gemini-2.5-pro
---

# Regression Notes — PLANNER_PROMPT v2.1 against Golden Set v1.2

## Summary

Final eval (round 1, post-R14d patch) — `tests/eval/eval_results_pipeline_gap_s1.json`.

| metric | value | gate | met? |
|---|---:|---:|:---:|
| total entries | 46 | — | — |
| passed | 38 | — | — |
| failed | 8 | — | — |
| avg_tool_recall | 0.983 | ≥ 0.963 | ✓ |
| avg_tool_precision | 0.961 | ≥ 0.986 | ✗ residual |
| avg_asset_bundle_recall | 1.000 | ≥ 0.971 | ✓ |
| asset_bundle_floor_violations | 0 | = 0 | ✓ |
| forbidden_violations | 2 | informational | — |

**Convergence decision.** Three of four numeric gates met. Precision gate at
0.961 (vs target 0.986) is a residual on GT.030-GT.046 new entries, not a
GT.001-GT.029 baseline regression. Per session brief: *"Do NOT block close on
residuals that don't regress the existing GT.001-GT.029 baseline."* Close
authorized.

## GT.001-GT.029 baseline — preserved (no regressions)

Prior baseline (`eval_results_planner_prompt_fix_s1.json`, 29 entries, v2.1
pre-R14d-patch): 25/29 pass. Failures: GT.017, GT.021, GT.025, GT.029.

Current run on GT.001-GT.029 subset: **26/29 pass.** Failures: GT.017, GT.021,
GT.029. **Net: +1 (GT.011 confirmed fixed by R14d patch; GT.025 also recovered).**
No new regressions.

| id | prior | now | notes |
|---|:---:|:---:|---|
| GT.011 | (pass-then-regress in v2.1.0 run) | **PASS** | Fixed by R14d "Do NOT add pattern_register" amendment |
| GT.017 | FAIL | FAIL | Unchanged — model adds extra `msr_sql` |
| GT.021 | FAIL | FAIL | Unchanged — model omits `cgm_graph_walk` |
| GT.025 | FAIL | **PASS** | Recovered (LLM-variance + R14d helped) |
| GT.029 | FAIL | FAIL | Unchanged — model adds `contradiction_register` instead of `vector_search` |

## GT.030-GT.046 new entries — per-entry scoreboard

| id | result | recall | precision | forbidden_viol |
|---|:---:|---:|---:|:---:|
| GT.030 | PASS | 1.00 | 1.00 | — |
| GT.031 | PASS | 1.00 | 1.00 | — |
| GT.032 | PASS | 1.00 | 1.00 | — |
| GT.033 | PASS | 1.00 | 1.00 | — |
| GT.034 | PASS | 1.00 | 1.00 | — |
| GT.035 | PASS | 1.00 | 1.00 | — |
| GT.036 | PASS | 1.00 | 1.00 | — |
| GT.037 | PASS | 1.00 | 1.00 | — |
| GT.038 | FAIL | 1.00 | 0.75 | — |
| GT.039 | PASS | 1.00 | 1.00 | — |
| GT.040 | PASS | 1.00 | 1.00 | — |
| GT.041 | PASS | 1.00 | 1.00 | — |
| GT.042 | FAIL | 1.00 | 0.75 | — |
| GT.043 | FAIL | 1.00 | 0.67 | ! |
| GT.044 | FAIL | 1.00 | 0.67 | ! |
| GT.045 | FAIL | 0.75 | 0.75 | — |
| GT.046 | PASS | 1.00 | 1.00 | — |

**12/17 PASS** (70.6%). Recall is 100% on 16/17 — failures are precision-mode
(model adds extra tools) or one recall miss (GT.045).

## Diagnostic round log

### Round 1 — R14d amendment (D9-domain-read pattern_register suppression)

**Trigger:** GT.011 regression in initial run. Model added `pattern_register`
for "Read my D9 Navamsha for marriage indications" because R17(b) interprets
"navamsha" as a divisional → triggers `pattern_register`. R14d already blocked
`cgm_graph_walk` for this query class but did not block `pattern_register`.

**Edit:** Extended R14d to also exclude `pattern_register`, with explicit
override note vs R17(b).

```
R14d. ... use `msr_sql` + `vector_search` ONLY. Do NOT add
      cgm_graph_walk. Do NOT add pattern_register (this rule overrides
      R17b for single-divisional or single-house domain-read queries —
      a divisional chart used to interpret one domain is NOT the
      "chart-level multi-layer scope" R17b targets).
```

**Result:** GT.011 → PASS. No new GT.001-GT.029 regressions. GT.025 also
recovered. No further diagnostic rounds taken; remaining failures are
GT.030+ residuals (per session brief, do not block close).

### Rounds 2-3 — not taken

Per session brief, up to 3 rounds were authorized. Rounds 2-3 were not taken
because the GT.001-GT.029 baseline was preserved after round 1 and remaining
failures live entirely in the GT.030+ residual band.

## Residuals (do not block close)

Candidates for a future patch session — these are documented for the next
prompt-iteration session, not for QP-S4:

1. **GT.043 / GT.044 — predictive timing queries with domain words trigger
   `vector_search` (forbidden).** Both queries contain a domain keyword
   ("career", "health") plus an explicit time window. The model treats them
   like remedial queries and pulls `vector_search` per R18-pattern
   generalization. Rule gap: no explicit "PREDICTIVE queries: vector_search
   is forbidden when domain words appear" rule.
2. **GT.038 / GT.042 — multi-domain or yoga-interaction queries add extra
   `cluster_atlas`.** Likely a precision-only issue; the gold's `cluster_atlas`
   omission for these is debatable.
3. **GT.045 — life-arc query omits `pattern_register`.** Recall miss; the
   model selected `vector_search` instead of `pattern_register` for a
   "comprehensive arc" query.

All three are precision/forbidden-violation issues on GT.030+ entries. None
regress the GT.001-GT.029 baseline. None block close.
