# Shard 9b — panchanga_sashtighati

shard_id: 9b-panchanga_sashtighati
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
chart_facts existence + proven 9b 5-cell recipe (`<CAT>`=panchanga_sashtighati) + duplication probe.

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
4. Domain: `character|spirituality` — MIS-MAPPED. Sashtighati (60-ghati day division) is a pure timing/structural construct; family-default domain.
5. Emergence: 5× duplication.

## design_correctness_verdict: WEAK

## Findings
- FC-9b-sashtighati-DUP (class 7 DROWNED, MED): 5.00× identical-headline duplication (3 distinct → 15). Evidence: dup probe.
- FC-9b-sashtighati-DOMAIN (class 2 WRONG, LOW; class-1 consequence): 60-ghati timing structure mapped to `character|spirituality` default; unreachable under a timing query. Evidence: cell4.
