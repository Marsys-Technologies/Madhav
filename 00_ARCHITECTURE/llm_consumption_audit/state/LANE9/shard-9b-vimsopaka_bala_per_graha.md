# shard-9b-vimsopaka_bala_per_graha

**shard_id:** 9b-vimsopaka_bala_per_graha
**lane:** 9b
**charts:** 482012f1, 1c826d5a

## SQL run
5-cell recipe with `f.fact_category = 'vimsopaka_bala_per_graha'` → returned `[]` (no rows).
chart_facts denominator: 70 total (35/chart).

## Verbatim results
- chart_facts rows: 70 (35/chart)
- cell1 (consumed): **0 signals for both charts** (empty result set)
- cells 2–5: N/A

## 5-cell verdicts
1. Consumed by bo_laksana? **NO** — 70 chart_facts rows exist, 0 MSR signals.
2–5: not applicable.

## design_correctness_verdict: NOT_CONSUMED
Funnel-narrowing / omission-from-MSR.

## Findings
- **F1 (class 1 UNREACHABLE-by-omission-from-MSR):** vimsopaka_bala_per_graha (35 rows/chart) produces zero bodha_msr_signals. Vimshopaka bala is a graha's aggregate varga-based strength — a primary strength measure that downstream synthesis (dignity, yoga potency, karaka assessment) depends on. Its total absence from MSR means no LLM consumer can weigh graha strength via this metric. Not NONEXISTENCE — the L1 fact exists; MSR omitted it. Suspected layer: L-writer (bo_laksana ingestion selection). Severity: HIGH (strength assessment is load-bearing across every domain read). Evidence: cell1 empty; chart_facts 35/chart. Dedupe: funnel-narrowing / ingestion-omission (R-44 family).
