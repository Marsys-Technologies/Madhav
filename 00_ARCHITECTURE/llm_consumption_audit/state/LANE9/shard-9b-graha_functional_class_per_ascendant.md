# shard-9b-graha_functional_class_per_ascendant

**Shard id:** graha_functional_class_per_ascendant (Lane 9b)
**Charts:** 482=Abhisek, 1c826=Abhinandan

## Exact SQL run
chart_facts: 482=70, 1c826=70. 5-cell recipe (standard 9b CTE).

## Verbatim results
- cell1: 482=40, 1c826=40
- cell2: 482=`chart_defining=2, major=38`; 1c826=`background=8, chart_defining=2, major=30`
- cell3: 482=`40/40`, 1c826=`40/40`
- cell4: both=`character|career`
- cell5: both=`composite_state=40`

## 5-cell verdicts
1. Consumed? YES (40/40).
2. Salience: major-dominant (38/40) — defensible; functional benefic/malefic class per lagna is high decision weight.
3. Attribution: 100%. AFFIRMATIVE PASS.
4. Domain: mono-mapped `character|career`. Functional class GOVERNS every domain (a functional malefic ruling the 7th damages relationships; ruling the 2nd/11th damages wealth) — collapsing to character|career defeats the purpose.
5. Type: composite_state.

## design_correctness_verdict: WEAK
Consumed + fully attributed + proportionate salience, but the domain default-collapse is especially damaging here: functional class is precisely the fact a domain-filtered query most needs (is the lord of THIS domain's house a functional benefic?), yet it is un-findable outside character|career.

## Findings
- **F1** class 2 (WRONG) / class 1 consequence — severity HIGH. Functional-class signals always `domains_affected_array=character|career` (cell4 invariant). A wealth/relationship/health query cannot retrieve whether that domain's house-lord is a functional benefic or malefic — the single most decision-relevant fact for the query. Rationale: functional class is domain-defining by construction, so a static character|career mapping is a structural mis-map, not a rounding error.
