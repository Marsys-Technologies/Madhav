# Shard 9b — esoteric_point_yogi

**shard_id:** `9b-esoteric_point_yogi`
**charts:** 482012f1-… (Abhisek) · 1c826d5a-… (Abhinandan)

## Exact SQL run (proven 9b 5-cell recipe, `<CAT>`=esoteric_point_yogi)
```sql
WITH sig AS (SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
  ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'esoteric_point_yogi'
    AND ms.chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
) SELECT ... (5 cells UNION ALL) ...;
```

## Verbatim results
- chart_facts denominator: 482012f1=70, 1c826d5a=70
- cell1 (signals): 482012f1=**49**, 1c826d5a=**47**
- cell2_salience: 482012f1=`supporting=49`, 1c826d5a=`supporting=47`
- cell5_type: 482012f1=`composite_state=49`, 1c826d5a=`composite_state=47`
- cell3_attr: 482012f1=`49/49`, 1c826d5a=`47/47`
- cell4_domains: both=`character|relationship`

## 5-cell verdicts
1. **Consumed?** YES (49/47 signals).
2. **Salience:** uniformly `supporting` — proportionate; NO inflation.
3. **Entity attribution:** 100% (49/49, 47/47) — SOUND.
4. **Domain mapping:** DEFECT — default `character|relationship` (finding).
5. **Emergence:** 47–49 signals per chart, all `composite_state`.

## design_correctness_verdict: WEAK
Consumed, fully attributed, salience proportionate; domain default-collapse defect.

## Findings
- **F1 (class 2 WRONG; domain mis-mapping; MED):** The yogi point (the benefic karaka-of-fortune point) maps exclusively to default `character|relationship`; no fortune/spirituality routing. Part of shard-wide default-collapse. Suspected layer: L-writer (bo_laksana domain-mapping). Call = SQL above, cell4.
