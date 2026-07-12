# shard-9b-panchanga_yoga

Lane: 9b. Charts: A=482012f1, B=1c826d5a.

## Exact SQL run
5-cell recipe (charter §4) with `<CAT>`=`panchanga_yoga` + chart_facts count + fan-out probe.

## Verbatim results
- chart_facts: A=4, B=4.
- cell1: A=20, B=20.
- cell2 tiers: `supporting` only.
- cell3 attribution: A=20/20, B=20/20 (100%).
- cell4 domains: `character|spirituality`.
- cell5 by type: `yoga=20` both charts.
- Fan-out: 4 facts → 20 signals; each of 4 facts → 5 distinct signal_ids = 5:1 duplication.

## 5-cell verdicts
1. Consumed YES. 2. `supporting` proportionate. 3. 100% attributed SOUND. 4. `character|spirituality` — defensible for a nitya (panchanga) yoga (temperament), but shared verbatim with the muhurta categories that are NOT temperament-related. 5. 5:1 duplication; also classified `signal_type_class=yoga`, conflating a panchanga nitya yoga with chart yogas (raja/dhana etc).

## design_correctness_verdict: WEAK

## Findings
- F1 (class 7 DROWNED, MED): 4 chart_facts → 20 signals (5 per fact), identical tier/type/domain — 5:1 duplication. Evidence: per-fact count(DISTINCT signal_id)=5 for fact_ids e2fc0605…, d91e1511…, 1e006562…, 03abccb3….
- F2 (class 5/taxonomy, LOW): the panchanga nitya yoga is emitted under `signal_type_class=yoga`, the same class as chart-forming yogas; a wire consumer querying chart yogas cannot distinguish a daily-panchanga yoga (Shiva) from a chart yoga. Domain `character|spirituality` is itself apt for nitya yoga (temperament) so cell4 is not penalized here.
