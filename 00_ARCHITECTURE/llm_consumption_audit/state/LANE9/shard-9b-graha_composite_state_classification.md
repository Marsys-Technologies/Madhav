# shard-9b-graha_composite_state_classification

**Shard id:** graha_composite_state_classification (Lane 9b)
**Charts:** 482=Abhisek, 1c826=Abhinandan

## Exact SQL run
chart_facts: 482=45, 1c826=45. 5-cell recipe (standard 9b CTE).

## Verbatim results
- cell1: 482=10, 1c826=20
- cell2: 482=`major=9, supporting=1`; 1c826=`background=6, major=12, supporting=2`
- cell3: 482=`10/10`, 1c826=`20/20`
- cell4: both=`character|career|wealth`
- cell5: 482=`composite_state=10`, 1c826=`composite_state=20`

## 5-cell verdicts
1. Consumed? YES (10/20; chart-specific count is sensible — composite avastha per graph).
2. Salience: major-heavy — appropriate; the graha's overall composite-state classification is high decision weight.
3. Attribution: 100%. AFFIRMATIVE PASS.
4. Domain: `character|career|wealth` — DIFFERENTIATED (includes wealth, not a bare default). Better than the shard's mono-mapped norm.
5. Type: composite_state — correct for this category by name.

## design_correctness_verdict: SOUND
Consumed, fully attributed, proportionate high-value salience, and domain mapping is differentiated (character|career|wealth). No defect pattern present.

## Findings
- None. Affirmative PASS: cell3 `10/10` & `20/20` (full attribution); cell4 `character|career|wealth` (differentiated); salience concentrated at major for a genuinely chart-shaping fact.
