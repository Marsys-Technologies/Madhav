# Shard 9b — panchanga_special_yoga_combinations

shard_id: 9b-panchanga_special_yoga_combinations
charts: 482012f1 (Abhisek) ONLY; 1c826d5a has 0 chart_facts rows for this category (data-plane absence, not a consumption gap).

## Exact SQL run
chart_facts existence + proven 9b 5-cell recipe (`<CAT>`=panchanga_special_yoga_combinations) + duplication probe.

## Verbatim results
- chart_facts: 15 rows (482 only); 0 rows for 1c826d5a.
- cell1: 15 signals (482 only).
- cell2 (salience): `supporting=15` (482).
- cell3 (attribution): 15/15 (482) — 100%.
- cell4 (domains): `spirituality|character` (482).
- cell5 (type): `yoga=15` (482) — correctly typed as yoga (not generic panchanga).
- Duplication probe (482): 15 / 3 distinct headlines = dup_factor 5.00.

## Five-cell verdicts
1. Consumed? YES on 482 (15 signals from 3 distinct signal facts). N/A on 1c826d5a (no source facts).
2. Salience: `supporting` — proportionate.
3. Attribution: 100% resolvable.
4. Domain: `spirituality|character` — defensible for janma-context panchanga yogas (though these are also muhurta constructs); typed correctly as `yoga`.
5. Emergence: 5× duplication; 15 chart_facts collapse to only 3 distinct signal headlines.

## design_correctness_verdict: WEAK

## Findings
- FC-9b-special_yoga-DUP (class 7 DROWNED, MED): 5.00× identical-headline duplication (3 distinct → 15). Evidence: dup probe.
- FC-9b-special_yoga-COLLAPSE (class 1 UNREACHABLE, LOW): 15 chart_facts rows collapse to 3 distinct signal headlines — ~12 special-yoga facts do not emerge as distinct MSR signals. Evidence: cf=15 vs distinct_headlines=3.
