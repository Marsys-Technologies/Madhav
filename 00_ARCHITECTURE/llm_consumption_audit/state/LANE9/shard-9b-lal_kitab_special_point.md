# Shard 9b-lal_kitab_special_point

shard_id: 9b-lal_kitab_special_point
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL: 9b 5-cell recipe with f.fact_category='lal_kitab_special_point'. chart_facts census: 200 rows combined.

## Verbatim results
- cell1: 482=10, 1c8=10 → CONSUMED
- cell2_salience: 482=supporting=10 ; 1c8=supporting=10
- cell3_attr: 482=10/10 ; 1c8=10/10 (100%)
- cell4_domains: 482=character|relationship ; 1c8=character|relationship
- cell5_type: 482=composite_state=10 ; 1c8=composite_state=10

## 5-cell verdicts
1. Consumed? YES but thin (10 signals) vs 200 chart_facts rows (~100/chart) → ~10:1 funnel narrowing.
2. Salience: 100% supporting — proportionate. PASS.
3. Attribution: 100%. PASS.
4. Domain: uniform character|relationship. Lal Kitab special points (rin/debts, blind/sleeping planets, artificial planets) carry strong wealth/health/ancestral-karma significations; character|relationship-only mapping drops those domains.
5. Emergence: 10 signals from ~100 chart_facts rows/chart.

## design_correctness_verdict: WEAK

## Findings
- summary: lal_kitab_special_point narrows from ~100 chart_facts rows/chart to only 10 MSR signals (~10:1), and those 10 map only to character|relationship — dropping wealth/health/ancestral-karma domains Lal Kitab is specifically consulted for.
  failure_class: 1 (UNREACHABLE — funnel-narrowing at ingestion + domain omission)
  severity: MED
  suspected_layer: L-writer / serving-query (ingestion selectivity + domain mapping)
  evidence: chart_facts=200 (combined) vs cell1=10/10; cell4="character|relationship" only.
  reproducible_call: SQL recipe cell1/cell4 rows + census SELECT COUNT(*) FROM chart_facts WHERE fact_category='lal_kitab_special_point'.
