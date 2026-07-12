# Shard 9b — panchanga_nishita_kala

shard_id: 9b-panchanga_nishita_kala
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
chart_facts existence + proven 9b 5-cell recipe (`<CAT>`=panchanga_nishita_kala) + duplication probe.

## Verbatim results
- chart_facts: 3 rows per chart (both).
- cell1 (consumed): 15 signals per chart (both).
- cell2 (salience): `supporting=15` (both).
- cell3 (attribution): 15/15 (both) — 100%.
- cell4 (domains): `character|spirituality` (both).
- cell5 (type): `panchanga=15` (both).
- Duplication probe: 15 signals / 3 distinct headlines = dup_factor 5.00.

## Five-cell verdicts
1. Consumed? YES (15/chart from 3 facts).
2. Salience: `supporting` — proportionate, not inflated.
3. Attribution: 100% resolvable.
4. Domain: `character|spirituality` — MIS-MAPPED. Nishita Kala is a midnight time-band (muhurta/timing); family-default domain, not relevance-driven.
5. Emergence: 5× duplication (3 distinct → 15).

## design_correctness_verdict: WEAK

## Findings
- FC-9b-nishita-DUP (class 7 DROWNED, MED): 5.00× identical-headline duplication (3 distinct → 15). Evidence: dup probe.
- FC-9b-nishita-DOMAIN (class 2 WRONG, LOW; class-1 consequence): midnight time-band mapped to `character|spirituality` default; unreachable under a timing/muhurta query. Evidence: cell4.
