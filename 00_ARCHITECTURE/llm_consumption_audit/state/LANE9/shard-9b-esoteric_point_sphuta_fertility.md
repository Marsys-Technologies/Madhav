# Shard 9b — esoteric_point_sphuta_fertility

**shard_id:** `9b-esoteric_point_sphuta_fertility`
**charts:** 482012f1-… (Abhisek) · 1c826d5a-… (Abhinandan)

## Exact SQL run (proven 9b 5-cell recipe, `<CAT>`=esoteric_point_sphuta_fertility)
```sql
WITH sig AS (SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
  ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'esoteric_point_sphuta_fertility'
    AND ms.chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
) SELECT ... (5 cells UNION ALL) ...;
```

## Verbatim results
- chart_facts denominator: 482012f1=70, 1c826d5a=70
- cell1 (signals): 482012f1=**64**, 1c826d5a=**65**
- cell2_salience: 482012f1=`supporting=64`, 1c826d5a=`supporting=65`
- cell5_type: 482012f1=`composite_state=64`, 1c826d5a=`composite_state=65`
- cell3_attr: 482012f1=`64/64`, 1c826d5a=`65/65`
- cell4_domains: both=`character|relationship`

## 5-cell verdicts
1. **Consumed?** YES (64/65 signals).
2. **Salience:** uniformly `supporting` — proportionate; NO inflation.
3. **Entity attribution:** 100% (64/64, 65/65) — SOUND.
4. **Domain mapping:** DEFECT (egregious) — default `character|relationship` (finding).
5. **Emergence:** 64–65 signals per chart, all `composite_state`.

## design_correctness_verdict: WEAK
Consumed, fully attributed, salience proportionate; but domain mis-map is egregious (2nd-most in shard after mrityu).

## Findings
- **F1 (class 2 WRONG; domain mis-mapping; HIGH):** The fertility sphuta — the santана/beeja progeny-timing point — maps exclusively to default `character|relationship` on both charts (cell4=`character|relationship`), NOT to a children/progeny domain. A children/fertility/conception-timing query can never retrieve the fertility point (KP-4 analog; class-1 UNREACHABLE consequence for the children domain). Alongside mrityu, the sharpest instance of the shard-wide default-collapse. Suspected layer: L-writer (bo_laksana domain-mapping rule). Call = SQL above, cell4.
