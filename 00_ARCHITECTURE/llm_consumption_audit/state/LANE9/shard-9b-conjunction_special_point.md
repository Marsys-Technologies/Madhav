# shard-9b-conjunction_special_point

**Shard id:** 9b-conjunction_special_point
**Charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## SQL run
Standard 5-cell recipe on fact_category='conjunction_special_point' + chart_facts baseline.

## Verbatim results
- chart_facts baseline: 198 (Abhisek) / 159 (Abhinandan)
- cell1 signals: Abhisek=198, Abhinandan=159  (full consumption)
- cell2 salience: both `supporting`
- cell3 attribution: 198/198, 159/159
- cell4 domains: both `character|career`
- cell5 type: both `composite_state`

## Cell verdicts
1. Consumed: YES — 1:1 with chart_facts
2. Salience: uniformly supporting (proportionate)
3. Attribution: 100%
4. Domains: rigid `character|career`
5. Emergence: composite_state only

## design_correctness_verdict: WEAK
Full consumption, full attribution, proportionate supporting tier — sound on those axes. Sole defect: uniform `character|career` domain regardless of which special point (Gulika/Mandi/upagraha, Arudha, etc.), which can suppress e.g. health/longevity relevance of certain special points.

## Findings
- summary: All conjunction_special_point signals mapped uniformly to character|career, ignoring domain-specific meaning of individual special points. failure_class 2 (WRONG-mapping). severity LOW. evidence: cell4 `character|career` for all 198/159.
