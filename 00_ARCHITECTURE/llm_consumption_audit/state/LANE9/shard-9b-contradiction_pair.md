# shard-9b-contradiction_pair

**Shard id:** 9b-contradiction_pair
**Charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## SQL run
Standard 5-cell recipe on fact_category='contradiction_pair' + chart_facts baseline.

## Verbatim results
- chart_facts baseline: 1740 (Abhisek) / 1740 (Abhinandan)
- cell1 signals: Abhisek=1740, Abhinandan=1740  (full 1:1)
- cell2 salience: both `supporting=1740`
- cell3 attribution: 1740/1740 both
- cell4 domains: both `character|career`
- cell5 type: both `composite_state`

## Cell verdicts
1. Consumed: YES — full 1:1 (1740 = baseline)
2. Salience: every one of 1740 at `supporting` — zero discrimination
3. Attribution: 100%
4. Domains: rigid `character|career` on all 1740
5. Emergence: composite_state only

## design_correctness_verdict: WEAK
Fully consumed and attributed, but 1740 contradiction-pair signals per chart are entirely undifferentiated — identical tier (supporting), identical type, identical domain. This is a textbook DROWNED wall: a consuming LLM cannot find the decision-relevant contradictions among 1740 identically-ranked rows.

## Findings
- summary: 1740 contradiction_pair signals per chart all at identical supporting tier + character|career domain — no ranking discrimination, a duplication/identical-score wall (charter §7.4 metric 2). failure_class 7 (DROWNED). severity HIGH. evidence: cell1=1740/1740, cell2=`supporting=1740` (single tier), cell4=`character|career` uniform on both charts.
