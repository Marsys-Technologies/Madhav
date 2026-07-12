# shard-9b-panchanga_vijaya_muhurta

Lane: 9b. Charts: A=482012f1, B=1c826d5a.

## Exact SQL run
5-cell recipe (charter §4) with `<CAT>`=`panchanga_vijaya_muhurta` + chart_facts count check + fan-out probe (same recipe as shard-9b-panchanga_varjyam).

## Verbatim results
- chart_facts: A=3, B=3.
- cell1: A=15, B=15.
- cell2 tiers: `supporting` only.
- cell3 attribution: A=15/15, B=15/15 (100%).
- cell4 domains: `character|spirituality`.
- cell5 by type: `panchanga=15` both charts.
- Fan-out: 3 facts → 15 single-fact signals = 5:1.

## 5-cell verdicts
1. Consumed YES. 2. `supporting` — proportionate. 3. 100% attributed — SOUND. 4. `character|spirituality` uniform-default (shared with 4 sibling panchanga categories). 5. 5:1 duplication.

## design_correctness_verdict: WEAK

## Findings
- F1 (class 7 DROWNED, MED): 3 chart_facts → 15 signals (5 per fact), single-fact, identical on tier/type/domain — 5:1 duplication. Evidence: cell1=15 vs chart_facts=3; per-fact signal count=5.
- F2 (class 2 WRONG, LOW): domain `character|spirituality` applied identically to this and 4 sibling muhurta categories (default-domain / KP-4-analog); vijaya muhurta is an electional-timing marker with weak natural character/spirituality mapping.
