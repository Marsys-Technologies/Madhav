# shard-9b-cusp_kp_lords

**Shard id:** 9b-cusp_kp_lords  (KP-4 anchor re-derivation)
**Charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## SQL run
Standard 5-cell recipe on fact_category='cusp_kp_lords' + chart_facts baseline.

## Verbatim results
- chart_facts baseline: 240 (Abhisek) / 240 (Abhinandan)
- cell1 signals: Abhisek=87, Abhinandan=89   (only 87–89 of 240 facts feed signals)
- cell2 salience: both `supporting`
- cell3 attribution: 87/87, 89/89
- cell4 domains: both `character|relationship`
- cell5 type: both `tradition_specific`

## Cell verdicts
1. Consumed: PARTIAL — 87–89 signals from 240 KP cusp-lord facts (funnel narrowing)
2. Salience: uniformly supporting
3. Attribution: 100%
4. Domains: rigid `character|relationship` — NO wealth/finance domain despite KP cusp significators governing 2nd/11th (wealth), 10th (career), etc.
5. Emergence: tradition_specific only

## design_correctness_verdict: WEAK  (KP-4 CONFIRMED)
KP cusp-lord significators are inherently house-domain-specific (2nd/11th = wealth, 6th = health/debt, 7th = marriage). Mapping ALL of them to a fixed `character|relationship` default means a wealth-domain query can never surface the KP wealth significators that live in this category — exactly the KP-4 anchor. Compounded by only ~37% of the 240 facts producing any signal at all.

## Findings
- summary: KP cusp-lord signals uniformly domain-mapped to character|relationship, so KP wealth/finance significators (2nd/11th cusps) can never surface under a wealth-domain query (KP-4 anchor re-derived). failure_class 2 (WRONG-mapping, producing a class-1 UNREACHABLE consequence for domain-filtered queries). severity HIGH. evidence: cell4=`character|relationship` on all 87/89 signals both charts; cell1 87–89 of 240 chart_facts consumed.
