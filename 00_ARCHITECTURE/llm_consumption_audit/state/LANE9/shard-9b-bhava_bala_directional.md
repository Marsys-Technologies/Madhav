# shard-9b-bhava_bala_directional

**Shard id:** bhava_bala_directional (Lane 9b, MSR ingestion 5-cell)

## Exact SQL run
9b 5-cell recipe with `<CAT>` = `bhava_bala_directional`, both charts. Plus chart_facts denominator.

## Verbatim results
- chart_facts denominator: 60 / 60
- cell1 (signals): 20 / 20
- cell2_salience: `supporting=20` (both)
- cell5_type: `composite_state=20` (both)
- cell3_attr: 20/20 (both)
- cell4_domains: `character|career` (both)

## 5-cell verdicts
1. Consumed? YES — but only 20/60 facts emerge as signals (~33%).
2. Salience: flat `supporting`.
3. Attribution: 20/20 — SOUND on this axis.
4. Domain: fixed `character|career` — dig-bala of the 2nd/7th/6th bhavas is domain-relevant to wealth/relationship/health, collapsed away.
5. Emergence: 60 facts → 20 signals; two-thirds not ingested.

## design_correctness_verdict: WEAK
Consumed and fully attributed on the signals that emerge, but only ~1/3 of bhava directional-strength facts become signals, salience is flat, and domain is fixed to `character|career` so per-bhava directional strength cannot surface in the domain it pertains to.

## Findings
- **F1 (class 1 UNREACHABLE-by-omission, MED):** only 20/60 bhava_bala_directional facts (both charts) emerge as MSR signals; two-thirds of per-bhava directional-strength facts are not ingested. Evidence: cell1=20 vs chart_facts=60.
- **F2 (class 2 WRONG, LOW):** fixed `character|career` domain regardless of bhava. Evidence: cell4=`character|career` both charts.
