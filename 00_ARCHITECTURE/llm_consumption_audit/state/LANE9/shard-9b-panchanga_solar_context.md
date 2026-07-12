# Shard 9b — panchanga_solar_context

shard_id: 9b-panchanga_solar_context
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
chart_facts existence + proven 9b 5-cell recipe (`<CAT>`=panchanga_solar_context) + duplication probe.

## Verbatim results
- chart_facts: 3 rows per chart (both).
- cell1: 15 signals per chart (both).
- cell2 (salience): `supporting=15` (both).
- cell3 (attribution): 15/15 (both) — 100%.
- cell4 (domains): `character|spirituality` (both).
- cell5 (type): `panchanga=15` (both).
- Duplication probe: 15 / 3 distinct = dup_factor 5.00.

## Five-cell verdicts
1. Consumed? YES.
2. Salience: `supporting` — proportionate.
3. Attribution: 100% resolvable.
4. Domain: `character|spirituality` — MIS-MAPPED (family default). Solar context is calendrical/positional; mapping is not relevance-driven but the family default (identical to every other panchanga category).
5. Emergence: 5× duplication.

## design_correctness_verdict: WEAK

## Findings
- FC-9b-solar_context-DUP (class 7 DROWNED, MED): 5.00× identical-headline duplication (3 distinct → 15). Evidence: dup probe.
- FC-9b-solar_context-DOMAIN (class 2 WRONG, LOW): uniform `character|spirituality` family default applied without relevance discrimination. Evidence: cell4 identical to all 12 panchanga categories.
