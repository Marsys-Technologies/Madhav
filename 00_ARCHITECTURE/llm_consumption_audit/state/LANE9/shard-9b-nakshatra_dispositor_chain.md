# shard-9b-nakshatra_dispositor_chain

**shard_id:** 9b-nakshatra_dispositor_chain
**lane:** 9b

## Exact SQL run
5-cell recipe with `f.fact_category = 'nakshatra_dispositor_chain'` over both charts — returned `[]` (empty). Confirmed absence with:
`SELECT COUNT(*) FROM chart_facts WHERE fact_category='nakshatra_dispositor_chain' AND chart_id IN (...)`.

## Verbatim results
- chart_facts denominator: Abhisek=50, Abhinandan=50.
- cell1 (consumed): **0 rows for both charts** — no MSR signal's `constituent_facts_array` resolves to any `nakshatra_dispositor_chain` fact.
- cells 2–5: N/A (nothing consumed).

## Five-cell verdicts
1. Consumed? **NO** — 50 chart_facts rows/chart exist, 0 MSR signals ingest them.
2–5. N/A.

## design_correctness_verdict: NOT_CONSUMED
The nakshatra dispositor **chain** (the multi-hop sign→nakshatra→navamsha dispositor traversal — exactly the structure charter §3 / plan Appendix B §B-V.32 names as depth-critical) is fully computed in L1 (50 facts/chart) but is entirely omitted from MSR. bo_laksana ingests the single-hop `nakshatra_dispositor` (110 signals) but drops the CHAIN category wholesale.

## Findings
- **F1** — funnel-narrowing by omission. class 1 (UNREACHABLE / UNREACHABLE-by-omission-from-MSR). severity HIGH. Evidence: 50 chart_facts rows per chart, cell1=0 signals. The fact exists in chart_facts but MSR did not ingest it, so no downstream consumer can reach the dispositor-chain via the signal funnel.
- **F2** — corroborates anchor **G-6** (no multi-hop chain signal class in MSR). class 1. severity HIGH. Evidence: the one L1 category that IS a materialized multi-hop chain is precisely the one MSR drops; consistent with G-6's claim that MSR has no chain-class signal path. Cross-sub-lane note for conductor: this is independent 9b confirmation of G-6.
