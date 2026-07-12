# Shard 9b — esoteric_point_brahma

**shard_id:** `9b-esoteric_point_brahma`
**charts:** 482012f1-… (Abhisek) · 1c826d5a-… (Abhinandan)

## Exact SQL run (proven 9b 5-cell recipe, `<CAT>`=esoteric_point_brahma)
```sql
WITH sig AS (SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
  ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'esoteric_point_brahma'
    AND ms.chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
) SELECT ... (5 cells UNION ALL) ...;
```

## Verbatim results
- chart_facts denominator: 482012f1=80, 1c826d5a=80
- cell1 (signals): 482012f1=**40**, 1c826d5a=**40**
- cell2_salience: both=`supporting=40`
- cell5_type: both=`composite_state=40`
- cell3_attr: both=`40/40`
- cell4_domains: both=`character|relationship`

## 5-cell verdicts
1. **Consumed?** YES (40 signals each chart; 80 facts → 40 signals, ~50%).
2. **Salience:** uniformly `supporting` — proportionate; NO inflation.
3. **Entity attribution:** 100% (40/40) — SOUND.
4. **Domain mapping:** DEFECT — default `character|relationship` (finding).
5. **Emergence:** 40 signals per chart, all `composite_state`.

## design_correctness_verdict: WEAK
Consumed, fully attributed, salience proportionate; domain default-collapse defect.

## Findings
- **F1 (class 2 WRONG; domain mis-mapping; MED):** Brahma sphuta (a Kalachakra/spiritual deity point) maps exclusively to default `character|relationship`; no spirituality/dharma domain routing. Part of shard-wide default-collapse. Suspected layer: L-writer (bo_laksana domain-mapping). Call = SQL above, cell4.
