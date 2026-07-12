# Shard 9b — fact_category: chandra_bala_natal_baseline

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='chandra_bala_natal_baseline' AND ms.chart_id IN (A,B); plus cell0_cf.

## Verbatim results
- cell0_cf: A=60, B=60
- cell1: A=15, B=15
- cell2_salience: A=`supporting=15`, B=`supporting=15`
- cell5_type: A=`composite_state=15`, B=`composite_state=15`
- cell3_attr: A=`15/15`, B=`15/15`
- cell4_domains: A=`character|spirituality`, B=`character|spirituality`

## Five-cell verdicts
1. Consumed? YES (15 both charts).
2. Salience: 100% `supporting`.
3. Attribution: 100% (15/15).
4. Domain: fixed `character|spirituality`.
5. Emergence: 60 cf → 15 signals (25%), all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 2 WRONG / domain mis-map, MED):** Chandra bala (Moon strength, the emotional/mental resilience baseline and a core muhurta/transit-timing input) is tagged `character|spirituality` (cell4). "spirituality" is a questionable default and, critically, health/emotional-wellbeing — the domain Chandra bala most directly informs — is absent, so a mental-health or emotional-resilience query cannot surface the Moon-strength baseline.
- **F2 (class 1 funnel-narrowing, LOW):** 60 cf → 15 signals (25%).
- **F3 (class 7 salience-flattening, LOW):** uniform `supporting=15`.

completion: DONE
