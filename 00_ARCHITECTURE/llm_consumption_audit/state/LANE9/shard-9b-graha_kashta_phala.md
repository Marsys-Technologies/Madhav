# shard-9b-graha_kashta_phala

**Shard id:** graha_kashta_phala (Lane 9b)
**Charts:** 482=Abhisek, 1c826=Abhinandan

## Exact SQL run
chart_facts: 482=35, 1c826=35. 5-cell recipe (standard 9b CTE).

## Verbatim results
- cell1: 482=35, 1c826=30
- cell2: 482=`major=35`; 1c826=`background=5, major=25`
- cell3: 482=`35/35`, 1c826=`30/30`
- cell4: both=`character|career`
- cell5: 482=`composite_state=35`, 1c826=`composite_state=30`

## 5-cell verdicts
1. Consumed? YES (35/30).
2. Salience: ALL `major` (chart 482) — a per-graha malefic-result (affliction) scalar at uniform major tier; mild inflation of a descriptive scalar.
3. Attribution: 100%. AFFIRMATIVE PASS.
4. Domain: mono-mapped `character|career` — kashta phala (malefic-result capacity) is exactly the fact a health/relationship affliction query needs, collapsed to default.
5. Type: composite_state — an affliction-effect scalar carried as generic composite_state (parallels gandanta mis-class).

## design_correctness_verdict: WEAK
Consumed + fully attributed, but (a) uniform `major` tier for a descriptive scalar (mild R-44b), and (b) domain default-collapse to character|career strips an affliction-capacity fact from the health/relationship domains where it is most decision-relevant.

## Findings
- **F1** class 2 (WRONG) — severity MED. kashta_phala (malefic-result capacity) domain always `character|career` (cell4), un-findable under health/relationship-domain affliction queries where it is precisely relevant.
- **F2** class 7 (DROWNED) — severity LOW. All 35 signals at `major` (cell2 482 `major=35`), no differentiation, over-promoting a derived scalar.
