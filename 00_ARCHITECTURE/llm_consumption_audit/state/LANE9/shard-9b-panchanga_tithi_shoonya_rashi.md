# Shard 9b — panchanga_tithi_shoonya_rashi

shard_id: 9b-panchanga_tithi_shoonya_rashi
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
chart_facts existence + proven 9b 5-cell recipe (`<CAT>`=panchanga_tithi_shoonya_rashi) + duplication probe.

## Verbatim results
- chart_facts: 2 rows per chart (both).
- cell1: 10 signals per chart (both).
- cell2 (salience): `supporting=10` (both).
- cell3 (attribution): 10/10 (both) — 100%.
- cell4 (domains): `character|spirituality` (both).
- cell5 (type): `panchanga=10` (both).
- Duplication probe: 10 / 2 distinct = dup_factor 5.00.

## Five-cell verdicts
1. Consumed? YES.
2. Salience: `supporting` — proportionate.
3. Attribution: 100% resolvable.
4. Domain: `character|spirituality` — MIS-MAPPED. Tithi Shoonya Rashi (void signs by tithi) is an electional/muhurta construct; family-default domain; unreachable under a timing/electional query.
5. Emergence: 5× duplication.

## design_correctness_verdict: WEAK

## Findings
- FC-9b-tithi_shoonya-DUP (class 7 DROWNED, MED): 5.00× identical-headline duplication (2 distinct → 10). Evidence: dup probe.
- FC-9b-tithi_shoonya-DOMAIN (class 2 WRONG, MED; class-1 consequence): void-sign electional construct mapped to `character|spirituality` default; unreachable under a timing/electional query. Evidence: cell4.
