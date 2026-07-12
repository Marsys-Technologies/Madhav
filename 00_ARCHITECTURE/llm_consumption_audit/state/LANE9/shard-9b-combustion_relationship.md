# Shard 9b — fact_category: combustion_relationship

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='combustion_relationship' AND ms.chart_id IN (A,B); plus cell0_cf.

## Verbatim results
- cell0_cf: A=(no row / 0), B=5
- cell1: A=(no row / 0), B=5
- cell2_salience: B=`supporting=5` (A absent)
- cell5_type: B=`composite_state=5` (A absent)
- cell3_attr: B=`5/5` (A absent)
- cell4_domains: B=`character|career` (A absent)

## Five-cell verdicts
1. Consumed? YES for chart B (5 signals). For chart A there are **zero chart_facts rows** (cell0_cf returned no A row) — nothing exists to ingest, so this is data-plane absence for A, NOT an MSR funnel-narrowing miss.
2. Salience: 100% `supporting` (B).
3. Attribution: 100% (5/5, B).
4. Domain: fixed `character|career` (B).
5. Emergence: 5 cf → 5 signals (B, 1:1), all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 1 cross-chart data asymmetry, LOW / data-plane not MSR):** combustion_relationship has 5 facts for Abhinandan (B) but 0 for Abhisek (A). cell1_consumed is TRUE at the shard level (B has signals). The A-absence is UNREACHABLE-BY-NONEXISTENCE (the Ganita writer produced no rows for A), not a bo_laksana ingestion failure — logged for coverage honesty, root-cause sits at the data plane.
- **F2 (class 2 WRONG / domain mono-map, LOW):** the 5 B-signals all tagged `character|career`; a combust-relationship finding by name suggests a relationship-domain tag would be expected — none present.
- **F3 (class 7 salience-flattening, LOW):** all 5 at `supporting`.

completion: DONE
