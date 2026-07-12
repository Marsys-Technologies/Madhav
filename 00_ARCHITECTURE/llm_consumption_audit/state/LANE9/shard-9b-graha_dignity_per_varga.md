# shard-9b-graha_dignity_per_varga

**Shard id:** graha_dignity_per_varga (Lane 9b)
**Charts:** 482=Abhisek, 1c826=Abhinandan

## Exact SQL run
chart_facts: 482=1305, 1c826=1305. 5-cell recipe (standard 9b CTE).

## Verbatim results
- cell1: 482=1084, 1c826=1065
- cell2: 482=`background=6, chart_defining=148, major=704, supporting=226`; 1c826=`background=234, chart_defining=87, major=593, supporting=151`
- cell3: 482=`1084/1084`, 1c826=`1065/1065`
- cell4: both=`career|character ;; character|career`
- cell5: 482=`composite_state=1039, varga_pattern=45`; 1c826=`composite_state=1020, varga_pattern=45`

## 5-cell verdicts
1. Consumed? YES, heavily (1305 chart_facts → ~1065-1084 signals ≈ near-1:1). Highest-volume category in shard.
2. Salience: **INFLATED** — 148 signals at `chart_defining` and 704 at `major` for chart 482. Per-varga dignity spans obscure divisionals (D-45, D-60 etc.); dignity in a minor varga is low-decision-weight yet promoted to chart_defining/major tiers. R-44b pattern.
3. Attribution: 100%. AFFIRMATIVE PASS.
4. Domain: mono-mapped `career|character` — dignity governs whichever bhava the graha rules (wealth/relationship/health), collapsed to a default.
5. Type: composite_state + varga_pattern(45). Reasonable.

## design_correctness_verdict: WEAK
Consumed and fully attributed, but two defects: (a) salience inflation — 148 chart_defining + 704 major dignity-per-varga signals contribute a duplication/inflation wall (per-varga dignity of minor divisionals ranked at chart-defining tier); (b) domain default-collapse to career|character.

## Findings
- **F1** class 7 (DROWNED) — severity HIGH. 852 of 1084 signals (chart 482) sit at chart_defining/major tier. Evidence: cell2 482 `chart_defining=148, major=704`. Per-varga dignity across ~29 vargas × 9 grahas restated at top salience tiers buries genuinely chart-defining findings under a dignity-per-varga wall. Rationale for exceeding acharya tolerance: no acharya treats D-45/D-60 dignity as chart_defining alongside a Rajayoga.
- **F2** class 2 (WRONG) — severity MED. Domain always `career|character` (cell4 invariant) regardless of the dignified graha's actual house rulership.
