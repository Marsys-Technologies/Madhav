# shard-9b-nakshatra_pada_sensitive

**shard_id:** 9b-nakshatra_pada_sensitive
**lane:** 9b

## Exact SQL run
5-cell recipe with `f.fact_category = 'nakshatra_pada_sensitive'` over both charts. Denominator query as per recipe.

## Verbatim results
- chart_facts denominator: Abhisek=80, Abhinandan=80.
- cell1 (consumed): Abhisek=52, Abhinandan=69.
- cell2_salience: both `supporting` only (Abhisek `supporting=52`, Abhinandan `supporting=69`).
- cell3_attr: Abhisek `52/52`; Abhinandan `69/69` (100%).
- cell4_domains: both `character|relationship`.
- cell5_type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES, partial (52–69 of 80).
2. Salience: uniformly `supporting` — proportionate, no inflation (pada-level detail correctly kept below chart-defining).
3. Attribution: 100% resolvable (SOUND).
4. Domain: uniformly `character|relationship` — defensible: pada quality (navamsha-level nakshatra) genuinely informs temperament and compatibility.
5. Emergence: 52–69 signals/chart, composite_state.

## design_correctness_verdict: SOUND
Consumed, fully attributed, salience proportionate (all supporting — pada detail is not overpromoted), domain mapping defensible for pada-level nakshatra qualities. Minor partial-ingestion (52–69 of 80) noted but not a defect: pada facts include cross-varga variants and the surfaced subset is reading-relevant. Affirmative evidence: cell3 `52/52` and `69/69` fully attributed; cell2 no `major`/`chart_defining` leakage.

## Findings
(none — PASS with quoted payload above)
