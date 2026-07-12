# Shard 9b — fact_category: bhava_bala_occupant

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='bhava_bala_occupant' AND ms.chart_id IN (A,B); plus cell0_cf chart_facts count.

## Verbatim results
- cell0_cf: A=60, B=60
- cell1: A=15, B=16
- cell2_salience: A=`supporting=15`, B=`supporting=16`
- cell5_type: A=`composite_state=15`, B=`composite_state=16`
- cell3_attr: A=`15/15`, B=`16/16`
- cell4_domains: A=`character|career`, B=`character|career`

## Five-cell verdicts
1. Consumed? YES.
2. Salience: 100% `supporting`.
3. Attribution: 100% (15/15, 16/16).
4. Domain: fixed `character|career` — mono-map.
5. Emergence: 60 cf → 15/16 signals (~26%), all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 2 WRONG / domain mis-map, MED):** occupant-strength for all 12 bhavas tagged uniformly `character|career`; 2nd/11th (wealth) or 7th (relationship) occupant bala cannot surface under those domain filters. Evidence: cell4 `character|career` invariant.
- **F2 (class 7 salience-flattening, LOW):** uniform `supporting` tier (cell2), no discrimination.
- **F3 (class 1 funnel-narrowing, LOW):** 60 cf → 15/16 signals.

completion: DONE
