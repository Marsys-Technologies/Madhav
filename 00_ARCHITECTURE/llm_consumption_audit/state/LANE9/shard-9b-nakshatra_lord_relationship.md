# shard-9b-nakshatra_lord_relationship

**shard_id:** 9b-nakshatra_lord_relationship
**lane:** 9b

## Exact SQL run
5-cell recipe with `f.fact_category = 'nakshatra_lord_relationship'` over both charts — returned `[]`. Confirmed absence with the chart_facts COUNT query.

## Verbatim results
- chart_facts denominator: Abhisek=45, Abhinandan=45.
- cell1 (consumed): **0 rows for both charts.**
- cells 2–5: N/A.

## Five-cell verdicts
1. Consumed? **NO** — 45 chart_facts rows/chart, 0 MSR signals.
2–5. N/A.

## design_correctness_verdict: NOT_CONSUMED
`nakshatra_lord_relationship` (the friendship/enmity relationship between a graha and the lord of the nakshatra it occupies — a genuinely reading-relevant dignity dimension) is computed at L1 (45 facts/chart) but never ingested by bo_laksana. Zero MSR signals.

## Findings
- **F1** — funnel-narrowing by omission. class 1 (UNREACHABLE-by-omission-from-MSR). severity HIGH. Evidence: 45 chart_facts rows per chart, cell1=0 signals. A dignity/relationship dimension (naisargika-style graha↔nakshatra-lord relationship) that an acharya weighs is unreachable through the signal funnel. Note the contrast with `nakshatra_dispositor` (consumed, 110 signals): the lord-*relationship* facet is dropped while the bare dispositor identity is kept — an incomplete depth ingestion of the same entity.
