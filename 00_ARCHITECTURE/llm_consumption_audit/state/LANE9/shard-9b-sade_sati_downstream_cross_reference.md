# shard-9b-sade_sati_downstream_cross_reference

Lane: 9b. Charts: A=482012f1, B=1c826d5a.

## Exact SQL run
5-cell recipe (charter §4) with `<CAT>`=`sade_sati_downstream_cross_reference` + chart_facts count.

## Verbatim results
- chart_facts: A=60, B=60.
- cell1: A=15, B=15.
- cell2 tiers: `supporting` only.
- cell3 attribution: A=15/15, B=15/15 (100%).
- cell4 domains: `career|health|relationship`.
- cell5 by type: `sade_sati=15` both.

## 5-cell verdicts
1. Consumed YES (60→15; narrowed to ~25%, consistent with a cross-reference roll-up rather than 1:1). 2. `supporting` — proportionate for a cross-reference meta-fact. 3. 100% attributed — SOUND. 4. `career|health|relationship` — apt classical sade sati significations, not a default. 5. 15 signals.

## design_correctness_verdict: SOUND

## Findings
(none — affirmative PASS)
- Affirmative evidence: 100% attribution; apt domain array (`career|health|relationship`); `supporting` tier appropriate for a downstream cross-reference. Note (not a finding): 60 chart_facts → 15 signals (funnel narrowing to 25%) — acceptable for a cross-reference category that consolidates many raw rows, and no evidence the dropped rows carry independent decision weight; flagged for the conductor's cross-sub-lane view but not itself a defect given the meta nature of the category.
