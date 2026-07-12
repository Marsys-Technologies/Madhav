# Shard 9b — esoteric_point_yogi_system

**shard_id:** `9b-esoteric_point_yogi_system`
**charts:** 482012f1-… (Abhisek) · 1c826d5a-… (Abhinandan)

## Exact SQL run (proven 9b 5-cell recipe, `<CAT>`=esoteric_point_yogi_system)
```sql
WITH sig AS (SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
  ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'esoteric_point_yogi_system'
    AND ms.chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
) SELECT ... (5 cells UNION ALL) ...;
```

## Verbatim results
- chart_facts denominator: 482012f1=25, 1c826d5a=25
- cell1 (signals): both=**25**
- cell2_salience: both=`supporting=25`
- cell5_type: both=`composite_state=25`
- cell3_attr: both=`25/25`
- cell4_domains: both=`character|relationship`

## 5-cell verdicts
1. **Consumed?** YES (25 signals each chart; 25 facts → 25, full pass-through).
2. **Salience:** uniformly `supporting` — proportionate; NO inflation.
3. **Entity attribution:** 100% (25/25) — SOUND.
4. **Domain mapping:** DEFECT — default `character|relationship` (finding).
5. **Emergence:** 25 signals per chart, all `composite_state`.

## design_correctness_verdict: WEAK
Consumed, fully attributed, salience proportionate; domain default-collapse defect.

## Findings
- **F1 (class 2 WRONG; domain mis-mapping; MED):** yogi_system (the yogi/avayogi system-classification esoteric point) maps exclusively to default `character|relationship`; no fortune/spirituality routing. Part of shard-wide default-collapse across all 12 esoteric_point categories. Suspected layer: L-writer (bo_laksana domain-mapping). Call = SQL above, cell4.
