# Shard 9b — esoteric_point_mrityu

**shard_id:** `9b-esoteric_point_mrityu`
**charts:** 482012f1-… (Abhisek) · 1c826d5a-… (Abhinandan)

## Exact SQL run (proven 9b 5-cell recipe, `<CAT>`=esoteric_point_mrityu)
```sql
WITH sig AS (SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
  ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'esoteric_point_mrityu'
    AND ms.chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
) SELECT ... (5 cells UNION ALL) ...;
```

## Verbatim results
- chart_facts denominator: 482012f1=105, 1c826d5a=105
- cell1 (signals): 482012f1=**97**, 1c826d5a=**97**
- cell2_salience: both=`supporting=97`
- cell5_type: both=`composite_state=97`
- cell3_attr: both=`97/97`
- cell4_domains: both=`character|relationship`

## 5-cell verdicts
1. **Consumed?** YES (97 signals each chart).
2. **Salience:** uniformly `supporting` — proportionate; NO inflation.
3. **Entity attribution:** 100% (97/97) — SOUND.
4. **Domain mapping:** DEFECT (egregious) — default `character|relationship` (finding).
5. **Emergence:** 97 signals per chart, all `composite_state`.

## design_correctness_verdict: WEAK
Consumed, fully attributed, salience proportionate; but the domain mis-map is the most egregious in the shard.

## Findings
- **F1 (class 2 WRONG; domain mis-mapping; HIGH):** The mrityu (death/longevity) sphuta — an explicitly longevity-domain marana point — maps exclusively to default `character|relationship` on both charts (cell4=`character|relationship`). A longevity/health/marana query can NEVER retrieve the death point because it is domain-mapped away from longevity entirely (KP-4 analog; class-1 UNREACHABLE consequence for the longevity domain). This is the sharpest instance of the shard-wide default-collapse: a point whose entire classical purpose is timing of death is filed under character. Suspected layer: L-writer (bo_laksana domain-mapping rule). Call = SQL above, cell4.
