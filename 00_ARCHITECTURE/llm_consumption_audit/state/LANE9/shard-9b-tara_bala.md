# shard-9b-tara_bala

**shard_id:** 9b-tara_bala
**lane:** 9b
**charts:** 482012f1, 1c826d5a

## SQL run
5-cell recipe with `f.fact_category = 'tara_bala'` → returned `[]` (no rows).
Confirmation: `SELECT ... chart_facts WHERE fact_category='tara_bala'` → Abhisek=43, Abhinandan=45.

## Verbatim results
- chart_facts rows: 88 total (Abhisek=43, Abhinandan=45)
- cell1 (consumed): **0 signals for both charts** (empty result set)
- cells 2–5: N/A (no signals)

## 5-cell verdicts
1. Consumed by bo_laksana? **NO** — 88 chart_facts rows exist, 0 MSR signals resolve to them.
2–5: not applicable (funnel emitted nothing).

## design_correctness_verdict: NOT_CONSUMED
Funnel-narrowing / omission-from-MSR: the fact exists in chart_facts but bo_laksana did not ingest it.

## Findings
- **F1 (class 1 UNREACHABLE-by-omission-from-MSR):** tara_bala (43/45 chart_facts rows per chart) produces zero bodha_msr_signals. Not UNREACHABLE-BY-NONEXISTENCE — the L1 fact exists; MSR failed to ingest it, so it is invisible to every downstream LLM consumer. Suspected layer: L-writer (bo_laksana ingestion selection). Severity: MED (tara_bala is primarily a transit/muhurta strength tool, lower natal-synthesis decision weight; note the related natal-baseline variant `tara_bala_natal_baseline` IS consumed at 45 signals/chart). Evidence: cell1 empty; chart_facts count 43/45. Dedupe: funnel-narrowing (R-44 family, ingestion-omission variant).
