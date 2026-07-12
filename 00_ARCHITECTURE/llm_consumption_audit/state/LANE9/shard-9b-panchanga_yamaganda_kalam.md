# shard-9b-panchanga_yamaganda_kalam

Lane: 9b. Charts: A=482012f1, B=1c826d5a.

## Exact SQL run
5-cell recipe (charter §4) with `<CAT>`=`panchanga_yamaganda_kalam` + chart_facts count + fan-out probe.

## Verbatim results
- chart_facts: A=3, B=3.
- cell1: A=15, B=15.
- cell2 tiers: `supporting` only.
- cell3 attribution: A=15/15, B=15/15 (100%).
- cell4 domains: `character|spirituality`.
- cell5 by type: `panchanga=15` both.
- Fan-out: 3 facts → 15 single-fact signals = 5:1.

## 5-cell verdicts
1. Consumed YES. 2. `supporting` proportionate. 3. 100% attributed SOUND. 4. `character|spirituality` uniform-default. 5. 5:1 duplication.

## design_correctness_verdict: WEAK

## Findings
- F1 (class 7 DROWNED, MED): 3 chart_facts → 15 signals (5/fact), single-fact, identical on all graded axes — 5:1 duplication.
- F2 (class 2 WRONG, LOW): yamaganda kalam (inauspicious daily period) mapped to `character|spirituality` identically to 4 sibling panchanga categories — default-domain mis-map.
