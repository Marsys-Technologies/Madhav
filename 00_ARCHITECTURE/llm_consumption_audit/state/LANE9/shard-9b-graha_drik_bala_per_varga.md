# shard-9b-graha_drik_bala_per_varga

**Shard id:** graha_drik_bala_per_varga (Lane 9b)
**Charts:** 482=Abhisek, 1c826=Abhinandan

## Exact SQL run
chart_facts: 482=735, 1c826=735. 5-cell recipe (standard 9b CTE).

## Verbatim results
- cell1: 482=105, 1c826=105
- cell2: 482=`major=31, supporting=74`; 1c826=`background=25, major=11, supporting=69`
- cell3: 482=`105/105`, 1c826=`105/105`
- cell4: both=`character|career`
- cell5: both=`composite_state=105`

## 5-cell verdicts
1. Consumed? YES (105/chart; 735→105 ≈ 7:1 narrowing).
2. Salience: supporting-dominant with some major — proportionate for an aspectual shadbala component.
3. Attribution: 100%. AFFIRMATIVE PASS.
4. Domain: mono-mapped `character|career`.
5. Type: composite_state.

## design_correctness_verdict: WEAK
Consumed + fully attributed + proportionate salience; single defect = domain default-collapse to character|career for an aspectual-strength quantity relevant to all graha-governed domains.

## Findings
- **F1** class 2 (WRONG) — severity MED. drik-bala signals always `domains_affected_array=character|career` (cell4 invariant both charts), un-findable under other domain filters.
