# Shard 9b-nakshatra_co_tenancy

shard_id: 9b-nakshatra_co_tenancy
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL run
9b 5-cell recipe with f.fact_category='nakshatra_co_tenancy' over both charts → returned ZERO rows (no MSR signal resolves to this fact_category).
Confirming census:
```sql
SELECT chart_id, COUNT(*) FROM chart_facts
WHERE fact_category='nakshatra_co_tenancy'
  AND chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
GROUP BY chart_id;
```

## Verbatim results
- 5-cell recipe: [] (empty — 0 signals for BOTH charts)
- chart_facts census: 482012f1 = 1 row, 1c826d5a = 6 rows (7 combined)

## 5-cell verdicts
1. Consumed? NO — 0 MSR signals despite 7 chart_facts rows existing. The fact EXISTS in chart_facts but bo_laksana / MSR did not ingest it.
2. Salience: N/A (nothing ingested).
3. Attribution: N/A.
4. Domain: N/A.
5. Emergence: 0.

## design_correctness_verdict: NOT_CONSUMED

## Findings
- summary: nakshatra_co_tenancy exists in chart_facts (482=1, 1c8=6 rows) but produces ZERO bodha_msr_signals for either chart — the fact family is omitted from MSR entirely; a consumer can never receive nakshatra co-tenancy evidence via the signal funnel.
  failure_class: 1 (UNREACHABLE-by-omission-from-MSR — funnel narrowing to zero; the fact exists, so this is omission not nonexistence)
  severity: HIGH
  suspected_layer: L-writer (bo_laksana ingestion selection) / serving-query
  evidence: 9b 5-cell recipe returns [] (0 signals) for both charts while SELECT COUNT(*) FROM chart_facts WHERE fact_category='nakshatra_co_tenancy' returns 482=1, 1c8=6.
  reproducible_call: the 5-cell recipe SQL (returns empty) + the census SELECT above.

## Note: nakshatra_conjunction (a sibling relational nakshatra category) IS consumed 1:1; nakshatra_co_tenancy is not — an inconsistent ingestion policy across near-identical nakshatra relational families.
