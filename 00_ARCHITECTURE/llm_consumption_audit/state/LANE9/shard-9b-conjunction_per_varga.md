# shard-9b-conjunction_per_varga

**Shard id:** 9b-conjunction_per_varga
**Charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## SQL run
Standard 5-cell recipe on fact_category='conjunction_per_varga' + chart_facts baseline.

## Verbatim results
- chart_facts baseline: 693 (Abhisek) / 576 (Abhinandan)  [note: Abhisek chart_facts=576, Abhinandan=693 per baseline query]
- cell1 signals: Abhisek=306, Abhinandan=361
- cell2 salience: both `supporting=306 / =361`
- cell3 attribution: 306/306, 361/361
- cell4 domains: both `career|relationship`
- cell5 type: both `composite_state`

## Cell verdicts
1. Consumed: YES, large volume
2. Salience: uniformly `supporting` (proportionate — varga conjunctions are supporting detail)
3. Attribution: 100%
4. Domains: rigid `career|relationship` on all ~300+ signals
5. Emergence: composite_state only

## design_correctness_verdict: WEAK
Salience is proportionate (all supporting), attribution perfect, but 300+ near-identical signals collapse to a single fixed domain pair `career|relationship` irrespective of which varga or graha-pair — a domain-rigidity + volume-wall (DROWNED-adjacent) pattern.

## Findings
- summary: 300+ conjunction_per_varga signals all mapped to the same career|relationship domain and same supporting tier, forming an undifferentiated wall. failure_class 7 (DROWNED). severity MED. evidence: cell1=306/361 all cell4=`career|relationship`, cell2 all `supporting`.
