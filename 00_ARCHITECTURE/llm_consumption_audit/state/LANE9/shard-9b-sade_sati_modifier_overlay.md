# shard-9b-sade_sati_modifier_overlay

**shard_id:** 9b-sade_sati_modifier_overlay
**charts:** Abhisek `482012f1-...`, Abhinandan `1c826d5a-...`

## Exact SQL run (proven 9b 5-cell recipe, `<CAT>`=sade_sati_modifier_overlay)
```sql
WITH sig AS (
  SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
         ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'sade_sati_modifier_overlay'
    AND ms.chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a'))
SELECT 'cell1', chart_id, COUNT(*) FROM sig GROUP BY chart_id
UNION ALL SELECT 'cell2_salience' ... UNION ALL SELECT 'cell5_type' ...
UNION ALL SELECT 'cell3_attr' ... UNION ALL SELECT 'cell4_domains' ...;
-- plus: SELECT COUNT(*) FROM chart_facts WHERE fact_category='sade_sati_modifier_overlay' AND chart_id IN (...)
```

## Verbatim results
- chart_facts rows: 482=300, 1c=300
- cell1 (consumed): 482=25, 1c=25  → CONSUMED (funnel 300→25, ~12x narrowing)
- cell2_salience: 482=`supporting=25`, 1c=`supporting=25`
- cell5_type: 482=`sade_sati=25`, 1c=`sade_sati=25`
- cell3_attr: 482=`25/25`, 1c=`25/25` (100% non-empty & JOIN-resolvable to chart_facts.fact_id)
- cell4_domains: 482=`career|health|relationship`, 1c=`career|health|relationship`

## Five-cell verdicts
1. Consumed? YES both charts.
2. Salience: 100% `supporting` — no discrimination.
3. Attribution: 100% resolvable — SOUND (refutes R-44a for this category).
4. Domain: fixed template `career|health|relationship`, byte-identical across two distinct charts and all 25 signals — defensible for a Sade Sati modifier (Saturn transit is broad) but chart-invariant (template, not signal-derived).
5. Emergence: 25/25 as `sade_sati` type.

## design_correctness_verdict: WEAK
Consumed + fully attributed + astrologically-reasonable domain, BUT (a) salience flattened to `supporting` for every signal (no proportionality), (b) domain tuple is a per-category hardcoded template (identical across two different charts), (c) 300→25 funnel narrowing not explained.

## Findings
- **F1 [class 2 WRONG, MED]** Domain mapping `career|health|relationship` is byte-identical for all 25 signals across two distinct charts → per-category template, not derived from signal content. Suspected layer: L-writer (bo_laksana domain assignment). Evidence: cell4 identical 482 vs 1c.
- **F2 [class 7 DROWNED, LOW]** 25/25 at `supporting`; no salience discrimination. Evidence: cell2 `supporting=25` both charts.
