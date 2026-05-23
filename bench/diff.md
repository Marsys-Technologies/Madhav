# Bench Diff — MCPT v3.2 vs mcpt-v32-baseline

| Scenario | Metric | Baseline | Head | Delta |
|---|---|---|---|---|
| canonical_d9_workflow | round_trips | 5 | 2 | -60% |
| canonical_d9_workflow | response_bytes | est. 28400 | est. 8200 | -71% |
| portal_synthesis_floor | round_trips | 5 | 5 | 0% (floor) |
| holistic_d9 | round_trips | 1 | 1 | 0% |

**Verdict: PASS** — No regressions. canonical_d9_workflow shows significant improvement via chart_summary.
