# shard-9b-graha_in_house_composite_strength

**Shard id:** graha_in_house_composite_strength (Lane 9b)
**Charts:** 482=Abhisek, 1c826=Abhinandan

## Exact SQL run
chart_facts: 482=1620, 1c826=1620. 5-cell recipe (standard 9b CTE).

## Verbatim results
- cell1: 482=851, 1c826=721
- cell2: 482=`supporting=851`; 1c826=`supporting=721`  (ALL supporting, both charts)
- cell3: 482=`851/851`, 1c826=`721/721`
- cell4: both=`character|career`
- cell5: 482=`composite_state=851`, 1c826=`composite_state=721`

## 5-cell verdicts
1. Consumed? YES, at very high volume (1620 chart_facts → 721-851 signals).
2. Salience: uniformly `supporting` (851/851) — honest low weighting, NOT inflated. Good discipline on tier.
3. Attribution: 100%. AFFIRMATIVE PASS.
4. Domain: mono-mapped `character|career`.
5. Type: composite_state, single class — 851 near-identical supporting signals from one fact_category.

## design_correctness_verdict: WEAK
Fully attributed and correctly (modestly) tiered at supporting, but 721-851 signals from a single per-house-per-varga strength category form a large-volume block that contributes to the overall duplication/drowning load, and domain is default-collapsed to character|career.

## Findings
- **F1** class 7 (DROWNED) — severity MED. One fact_category emits 851 signals (chart 482, cell1) all at supporting tier (cell2 `supporting=851`). While correctly de-prioritized, this volume of near-homogeneous per-varga strength rows swells any unranked signal pull. Rationale: 851 supporting rows exceeds what an acharya read of a single strength facet would tolerate as distinct entries. Mitigant noted: uniform `supporting` tier keeps them out of top-K.
- **F2** class 2 (WRONG) — severity LOW. Domain invariant `character|career` (cell4).
