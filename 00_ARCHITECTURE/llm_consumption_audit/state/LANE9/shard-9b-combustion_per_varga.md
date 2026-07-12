# Shard 9b — fact_category: combustion_per_varga

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='combustion_per_varga' AND ms.chart_id IN (A,B); plus cell0_cf.

## Verbatim results
- cell0_cf: A=725, B=725
- cell1: A=725, B=725
- cell2_salience: A=`supporting=725`, B=`supporting=725`
- cell5_type: A=`composite_state=725`, B=`composite_state=725`
- cell3_attr: A=`725/725`, B=`725/725`
- cell4_domains: A=`health|career`, B=`health|career`

## Five-cell verdicts
1. Consumed? YES — fully (1:1, 725 cf → 725 signals).
2. Salience: 100% `supporting`.
3. Attribution: 100% (725/725).
4. Domain: fixed `health|career`.
5. Emergence: 725 cf → 725 signals, all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 7 DROWNED, MED):** 725 per-varga combustion facts each emit one signal, all at the identical `supporting` tier (cell1=725, cell2=`supporting=725`). Combustion in the D1/D9/D10 of a functional benefic is a materially different weight than combustion in an obscure sub-varga, yet all 725 are co-tied — a §7.4 metric-2 identical-score wall. The few decision-relevant combustions are drowned in per-varga granularity.
- **F2 (class 2 WRONG / domain mono-map, MED):** combustion's domain should follow the COMBUST graha (combust Shukra → relationship, combust Budha → communication/career), but every row is tagged `health|career` (cell4). A relationship query cannot retrieve a combust-Venus finding.

completion: DONE
