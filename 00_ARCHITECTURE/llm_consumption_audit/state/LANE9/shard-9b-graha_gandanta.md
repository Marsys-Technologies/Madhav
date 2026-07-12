# shard-9b-graha_gandanta

**Shard id:** graha_gandanta (Lane 9b)
**Charts:** 482=Abhisek, 1c826=Abhinandan

## Exact SQL run
chart_facts: 482=50, 1c826=53. 5-cell recipe (standard 9b CTE).

## Verbatim results
- cell1: 482=5, 1c826=9
- cell2: 482=`major=1, supporting=4`; 1c826=`background=2, major=1, supporting=6`
- cell3: 482=`5/5`, 1c826=`9/9`
- cell4: both=`character|relationship`
- cell5: both=`composite_state` (482=5, 1c826=9)

## 5-cell verdicts
1. Consumed? YES (5/9; chart-specific — gandanta is a placement-contingent affliction).
2. Salience: supporting-dominant — arguably UNDER-weighted; gandanta (junction affliction) is a notable vulnerability, mostly at supporting.
3. Attribution: 100%. AFFIRMATIVE PASS.
4. Domain: `character|relationship` — differentiated (not the career default), sensible for a nakshatra-junction affliction.
5. Type: **composite_state** — gandanta is a classical AFFLICTION/dosha-class phenomenon but is ingested as generic composite_state, not as a dosha/affliction signal_type_class. It cannot surface under a dosha-oriented query.

## design_correctness_verdict: WEAK
Consumed + fully attributed + reasonable domain, but two softer defects: (a) an affliction phenomenon collapsed to `composite_state` rather than a dosha/affliction class (findability gap for dosha queries); (b) mild salience under-weighting (mostly supporting for a genuine vulnerability marker).

## Findings
- **F1** class 6 (UNUSABLE FORM) / mis-classification — severity MED. Gandanta ingested as `signal_type_class=composite_state` (cell5), not dosha/affliction. Cross-check note for conductor R-42 merge: this is an affliction-type category NOT carried under the dosha class — relevant to whether the dosha slice is complete.
