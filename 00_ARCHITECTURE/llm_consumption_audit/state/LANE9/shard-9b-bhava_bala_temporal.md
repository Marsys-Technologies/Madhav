# Shard 9b — fact_category: bhava_bala_temporal

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='bhava_bala_temporal' AND ms.chart_id IN (A,B); plus cell0_cf.

## Verbatim results
- cell0_cf: A=60, B=60
- cell1: A=10, B=10
- cell2_salience: A=`supporting=10`, B=`supporting=10`
- cell5_type: A=`composite_state=10`, B=`composite_state=10`
- cell3_attr: A=`10/10`, B=`10/10`
- cell4_domains: A=`character|career`, B=`character|career`

## Five-cell verdicts
1. Consumed? YES.
2. Salience: 100% `supporting`.
3. Attribution: 100% (10/10).
4. Domain: fixed `character|career` — mono-map.
5. Emergence: 60 cf → 10 signals (17% — lowest yield of the bhava_bala family), all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 1 funnel-narrowing, MED):** 60 chart_facts collapse to only 10 signals (cell0=60 vs cell1=10) — the sharpest narrowing in the bhava_bala family; 5/6 of the temporal bhava-strength facts never emerge as a distinct signal. Width loss for time-indexed house-strength queries.
- **F2 (class 2 WRONG / domain mis-map, MED):** uniform `character|career` (cell4) regardless of house — temporal wealth/health-house strength unreachable by domain filter.
- **F3 (class 7 salience-flattening, LOW):** uniform `supporting=10`.

completion: DONE
