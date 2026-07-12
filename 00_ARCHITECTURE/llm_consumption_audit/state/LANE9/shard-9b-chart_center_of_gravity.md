# Shard 9b — fact_category: chart_center_of_gravity

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='chart_center_of_gravity' AND ms.chart_id IN (A,B); plus cell0_cf.

## Verbatim results
- cell0_cf: A=290, B=290
- cell1: A=290, B=290
- cell2_salience: A=`supporting=290`, B=`supporting=290`
- cell5_type: A=`composite_state=290`, B=`composite_state=290`
- cell3_attr: A=`290/290`, B=`290/290`
- cell4_domains: A=`character|career`, B=`character|career`

## Five-cell verdicts
1. Consumed? YES — fully (1:1, 290 cf → 290 signals).
2. Salience: 100% `supporting`.
3. Attribution: 100% (290/290).
4. Domain: fixed `character|career`.
5. Emergence: 290 cf → 290 signals, all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 7 DROWNED / salience-deflation, MED):** "center of gravity" is by definition a chart-defining orientation concept (where the chart's weight concentrates), yet all 290 of its facts sit at `supporting` (cell2) — the single most orienting summary is deflated to a low tier and drowned among 290 co-tied rows. An orientation/top-signals surface would never lift the true center of gravity to the top. Rationale (§7.4 amendment): a concept whose whole purpose is to name the chart's dominant pole must not be tier-equal to routine background.
- **F2 (class 2 WRONG / domain mono-map, LOW):** all 290 rows `character|career` (cell4) irrespective of where the gravity centre falls.

completion: DONE
