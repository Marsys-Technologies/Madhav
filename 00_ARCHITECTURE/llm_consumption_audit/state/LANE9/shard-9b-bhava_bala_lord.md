# Shard 9b — fact_category: bhava_bala_lord

Charts: 482012f1 (Abhisek / A), 1c826d5a (Abhinandan / B)

## Exact SQL run
The proven 9b 5-cell recipe (CHARTER §7.4 / brief §4), plus cell0_cf = raw chart_facts count.
`WITH sig AS (SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class, ms.domains_affected_array, ms.constituent_facts_array FROM bodha_msr_signals ms JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id WHERE f.fact_category = 'bhava_bala_lord' AND ms.chart_id IN (A,B)) SELECT ... cell1/cell2_salience/cell5_type/cell3_attr/cell4_domains ...; plus SELECT COUNT(*) FROM chart_facts WHERE fact_category='bhava_bala_lord' AND chart_id IN (A,B) GROUP BY chart_id`

## Verbatim results
- cell0_cf (chart_facts rows): A=60, B=60
- cell1 (signals consuming category): A=15, B=15
- cell2_salience: A=`supporting=15`, B=`supporting=15`
- cell5_type: A=`composite_state=15`, B=`composite_state=15`
- cell3_attr: A=`15/15`, B=`15/15`
- cell4_domains: A=`character|career`, B=`character|career`

## Five-cell verdicts
1. Consumed by bo_laksana? YES (15 signals both charts).
2. Salience class: 100% `supporting` — no differentiation.
3. Entity attribution: 15/15 non-empty (100% attributed) — clean.
4. Domain mapping: fixed `character|career` for every signal regardless of which of the 12 bhava-lords is at issue — mono-mapping.
5. Emergence count: 60 chart_facts → 15 signals (25%), all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 2 WRONG / domain mis-map, MED):** bhava_bala_lord spans all 12 houses' lord-strength yet every signal is domain-tagged `character|career` on both charts. A wealth (2nd/11th-lord bala) or health (6th/8th) query cannot surface these — the fixed default starves domain-filtered retrieval (KP-4 generalization). Evidence: cell4 = `character|career` for A and B, invariant across all 15 signals.
- **F2 (class 7 DROWNED / salience-flattening, LOW):** all 15 signals sit at uniform `supporting` tier (cell2 `supporting=15`); the tier does no discriminating work, so a strong bhava-lord (e.g. exalted lagnesha) is indistinguishable from a weak one at retrieval time.
- **F3 (class 1 funnel-narrowing, LOW):** 60 chart_facts collapse to 15 signals (cell0=60 vs cell1=15); narrowing is plausibly legitimate roll-up into bhava_bala_total_extended but is logged for width tracking.

completion: DONE
