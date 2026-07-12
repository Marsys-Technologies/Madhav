# Shard 9b — fact_category: bhava_bala_positional

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='bhava_bala_positional' AND ms.chart_id IN (A,B); plus cell0_cf.

## Verbatim results
- cell0_cf: A=60, B=60
- cell1: A=20, B=20
- cell2_salience: A=`supporting=20`, B=`supporting=20`
- cell5_type: A=`composite_state=20`, B=`composite_state=20`
- cell3_attr: A=`20/20`, B=`20/20`
- cell4_domains: A=`character|career`, B=`character|career`

## Five-cell verdicts
1. Consumed? YES (20 both charts).
2. Salience: 100% `supporting`.
3. Attribution: 100% (20/20).
4. Domain: fixed `character|career` — mono-map.
5. Emergence: 60 cf → 20 signals (33%), all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 2 WRONG / domain mis-map, MED):** positional bhava-strength across all houses tagged uniformly `character|career`; domain-filtered queries for other houses cannot reach these. Evidence: cell4 invariant `character|career`.
- **F2 (class 7 salience-flattening, LOW):** uniform `supporting=20`.
- **F3 (class 1 funnel-narrowing, LOW):** 60 cf → 20 signals.

completion: DONE
