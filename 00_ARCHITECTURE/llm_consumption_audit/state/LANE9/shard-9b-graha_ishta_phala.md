# shard-9b-graha_ishta_phala

**Shard id:** graha_ishta_phala (Lane 9b)
**Charts:** 482=Abhisek, 1c826=Abhinandan

## Exact SQL run
chart_facts: 482=35, 1c826=35. 5-cell recipe (standard 9b CTE).

## Verbatim results
- cell1: 482=30, 1c826=30
- cell2: 482=`major=30`; 1c826=`background=6, major=24`
- cell3: 482=`30/30`, 1c826=`30/30`
- cell4: both=`character|career`
- cell5: both=`composite_state=30`

## 5-cell verdicts
1. Consumed? YES (30/30).
2. Salience: ALL `major` (chart 482) — ishta phala (benefic-result capacity, a Shadbala-derived scalar) at uniform major tier is mild salience inflation; a per-graha benefic-points scalar is supporting-grade descriptive.
3. Attribution: 100%. AFFIRMATIVE PASS.
4. Domain: mono-mapped `character|career`.
5. Type: composite_state.

## design_correctness_verdict: WEAK
Consumed + fully attributed, but (a) uniform `major` tier for a descriptive benefic-points scalar is mild R-44b-style inflation, and (b) domain default-collapse to character|career.

## Findings
- **F1** class 7 (DROWNED) — severity LOW. All 30 ishta_phala signals at `major` (cell2 482 `major=30`), no supporting/background differentiation, for a descriptive per-graha scalar. Rationale: benefic-points is a derived scalar, not a chart-shaping event; uniform major tier over-promotes it relative to yogas/doshas at the same tier.
- **F2** class 2 (WRONG) — severity LOW. Domain invariant `character|career` (cell4).
