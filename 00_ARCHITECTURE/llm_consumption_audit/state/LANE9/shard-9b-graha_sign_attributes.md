# shard-9b-graha_sign_attributes

Lane: 9b MSR ingestion coverage + fidelity. Charts: Abhisek `482012f1-710e-4a25-994a-93821f5871aa`, Abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a`.

## Reproducible call (exact SQL, read-only)
The 9b 5-cell recipe run via mcp__postgres__query with `<CAT>='graha_sign_attributes'`:
```sql
WITH sig AS (SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
  ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'graha_sign_attributes'
    AND ms.chart_id IN ('482012f1-...','1c826d5a-...'))
SELECT 'cell1', chart_id, COUNT(*) FROM sig GROUP BY chart_id
UNION ALL 'cell2_salience' (tier counts) UNION ALL 'cell5_type' UNION ALL 'cell3_attr' UNION ALL 'cell4_domains';
```
chart_facts denominator: `SELECT fact_category,chart_id,COUNT(*) FROM chart_facts WHERE fact_category='graha_sign_attributes' AND chart_id IN (...) GROUP BY 1,2;` → **100 / 100**.

## Verbatim results
- cell1 (signals consuming this category): 1c826d5a=**81**, 482012f1=**80**
- cell2_salience: 1c826d5a="background=21, major=7, supporting=53"; 482012f1="background=9, major=17, supporting=54"
- cell5_type: both "composite_state" (81 / 80)
- cell3_attr: 1c826d5a="81/81", 482012f1="80/80"
- cell4_domains: both "character|career"

## 5-cell verdicts
1. Consumed by bo_laksana? **YES** — 80–81 signals per chart (100 chart_facts rows → ~80% emergence).
2. Salience class: healthy spread, supporting-dominant (53–54 supporting), modest major (7–17), some background. **Proportionate.**
3. Entity attribution: **100% attributed** (81/81, 80/80) — every signal carries a non-empty constituent_facts_array resolving to chart_facts.fact_id. Affirmative PASS.
4. Domain mapping: uniform "character|career". For sign attributes (temperament/element/mode) → character is defensible; career less so but not egregious.
5. Emergence: composite_state=80–81. Reasonable funnel width.

## design_correctness_verdict: SOUND
Consumed, fully attributed, proportionate salience (supporting-dominant), domain mapping defensible for a temperament category. Minor note: participates in the systemic character|career default (see cross-category finding), but for THIS category the mapping is not semantically wrong.

## Findings
None rising to a category-specific defect. (Domain-default systemic pattern logged in the domain-mismapping categories.)
