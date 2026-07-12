# shard-9b-special_lagna

**shard_id:** 9b-special_lagna · charts 482012f1 / 1c826d5a

## SQL: proven 9b 5-cell recipe with `<CAT>`='special_lagna' + chart_facts count.

## Verbatim results
- chart_facts rows: 482=245, 1c=245
- cell1: 482=203, 1c=180 → CONSUMED
- cell2_salience: 482=`supporting=203`, 1c=`supporting=180`
- cell5_type: 482=`composite_state=203`, 1c=`composite_state=180`
- cell3_attr: 482=`203/203`, 1c=`180/180` (100%)
- cell4_domains: `character|relationship` (both, all)

## Five-cell verdicts
1. Consumed YES. 2. Salience 100% `supporting`. 3. Attribution SOUND. 4. Fixed template `character|relationship`. Special lagnas span themes: Arudha (public image/character — fits), but Hora Lagna = WEALTH, Ghati Lagna = power/career, Indu Lagna = wealth/prosperity — these wealth/career significations are excluded. 5. All `composite_state`.

## design_correctness_verdict: WEAK
Partially defensible (Arudha→character), but the wealth-bearing special lagnas (Hora/Indu) are forced into `character|relationship` and become un-findable in wealth-domain synthesis; salience flat.

## Findings
- **F1 [class 2 WRONG, MED]** All special_lagna signals mapped to `character|relationship`; Hora/Indu Lagna wealth significations excluded → wealth query cannot reach the wealth lagna (class-1 UNREACHABLE consequence). Chart-invariant template. Evidence: cell4 identical 482 vs 1c.
- **F2 [class 7 DROWNED, LOW]** 203/180 all `supporting`. Evidence: cell2.
