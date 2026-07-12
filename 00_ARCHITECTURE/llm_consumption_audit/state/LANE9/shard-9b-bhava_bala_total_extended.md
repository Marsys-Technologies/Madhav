# Shard 9b — fact_category: bhava_bala_total_extended

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='bhava_bala_total_extended' AND ms.chart_id IN (A,B); plus cell0_cf.

## Verbatim results
- cell0_cf: A=60, B=60
- cell1: A=56, B=52
- cell2_salience: A=`supporting=56`, B=`supporting=52`
- cell5_type: A=`composite_state=56`, B=`composite_state=52`
- cell3_attr: A=`56/56`, B=`52/52`
- cell4_domains: A=`character|career`, B=`character|career`

## Five-cell verdicts
1. Consumed? YES (best yield in family).
2. Salience: 100% `supporting`.
3. Attribution: 100% (56/56, 52/52).
4. Domain: fixed `character|career` — mono-map.
5. Emergence: 60 cf → 56/52 signals (~90%), all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 2 WRONG / domain mis-map, MED):** the roll-up total bhava-strength for all 12 houses is tagged uniformly `character|career` (cell4). Total 2nd/11th-house strength — the single most decision-relevant input to a wealth reading — is unreachable under a wealth-domain filter.
- **F2 (class 7 salience-flattening, MED):** 56 signals all at `supporting` (cell2). The house that dominates the chart's bala profile is not lifted above the weakest house at any tier — the strongest structural signal is undifferentiated.

completion: DONE
