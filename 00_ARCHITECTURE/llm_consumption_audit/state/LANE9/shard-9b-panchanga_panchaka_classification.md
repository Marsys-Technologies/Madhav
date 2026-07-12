# Shard 9b — panchanga_panchaka_classification

shard_id: 9b-panchanga_panchaka_classification
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
chart_facts existence + proven 9b 5-cell recipe (`<CAT>`=panchanga_panchaka_classification) + duplication probe (distinct headline count vs signal count).

## Verbatim results
- chart_facts: 80 rows per chart (both).
- cell1 (consumed): 65 signals (482) / 60 signals (1c826d5a).
- cell2 (salience): `supporting=65` (482) / `supporting=60` (1c) — uniformly supporting.
- cell3 (attribution): 65/65 (482), 60/60 (1c) — 100% attributed.
- cell4 (domains): `character|spirituality` (both).
- cell5 (type): `panchanga=65` (482) / `panchanga=60` (1c).
- Duplication probe (482): 65 signals / 13 distinct headlines = dup_factor 5.00.

## Five-cell verdicts
1. Consumed? YES. Note 80 chart_facts collapse to 13 distinct signals (×5 dup = 65); many panchaka facts do not surface as distinct signals.
2. Salience: `supporting` only — proportionate.
3. Attribution: 100% resolvable.
4. Domain: `character|spirituality` — MIS-MAPPED. Panchaka classification is an activity-timing/electional construct (inauspicious windows for construction, travel, etc.); character/spirituality is the family default, not relevance-driven. Unreachable under a muhurta/electional query.
5. Emergence: 5× duplication (13 distinct → 65 signals).

## design_correctness_verdict: WEAK

## Findings
- FC-9b-panchaka-DUP (class 7 DROWNED, MED): 5.00× identical-headline duplication (13 distinct → 65 signals). Suspected layer: L2 bo_laksana emission multiplication. Evidence: dup probe.
- FC-9b-panchaka-DOMAIN (class 2 WRONG, MED; class-1 consequence): uniform `character|spirituality` default; electional-timing category unreachable in its natural query domain. Evidence: cell4.
- FC-9b-panchaka-COLLAPSE (class 1 UNREACHABLE, LOW): 80 chart_facts rows collapse to only 13 distinct signal headlines — funnel narrowing; ~67 panchaka facts do not emerge as distinct MSR signals. Evidence: cf=80 vs distinct_headlines=13.
