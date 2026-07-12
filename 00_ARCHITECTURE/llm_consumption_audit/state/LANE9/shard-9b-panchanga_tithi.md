# Shard 9b — panchanga_tithi

shard_id: 9b-panchanga_tithi
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
chart_facts existence + proven 9b 5-cell recipe (`<CAT>`=panchanga_tithi) + duplication probe.

## Verbatim results
- chart_facts: 7 rows per chart (both).
- cell1: 35 signals per chart (both).
- cell2 (salience): `supporting=35` (both).
- cell3 (attribution): 35/35 (both) — 100%.
- cell4 (domains): `character|spirituality` (both).
- cell5 (type): `panchanga=35` (both).
- Duplication probe: 35 / 7 distinct = dup_factor 5.00.

## Five-cell verdicts
1. Consumed? YES (35/chart from 7 facts).
2. Salience: `supporting` — proportionate. (Note: janma tithi Shukla Tritiya is a FORENSIC birth anchor; arguably under-weighted at `supporting`, but not inflated — no R-44b violation.)
3. Attribution: 100% resolvable.
4. Domain: `character|spirituality` — DEFENSIBLE (janma tithi maps to nature/character in panchanga-purusha), though identical family default.
5. Emergence: 5× duplication (7 distinct → 35).

## design_correctness_verdict: WEAK

## Findings
- FC-9b-tithi-DUP (class 7 DROWNED, MED): 5.00× identical-headline duplication (7 distinct → 35). janma-tithi facts each restated as 5 byte-identical signals; 5× volume inflation. Suspected layer: L2 bo_laksana emission multiplication. Evidence: dup probe.
