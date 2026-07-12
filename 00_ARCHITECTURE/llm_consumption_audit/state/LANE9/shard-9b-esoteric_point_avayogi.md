# Shard 9b — esoteric_point_avayogi

**shard_id:** `9b-esoteric_point_avayogi`
**charts:** 482012f1-… (Abhisek) · 1c826d5a-… (Abhinandan)

## Exact SQL run (proven 9b 5-cell recipe, `<CAT>`=esoteric_point_avayogi)
```sql
WITH sig AS (
  SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
         ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'esoteric_point_avayogi'
    AND ms.chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
) SELECT ... (cell1/cell2_salience/cell5_type/cell3_attr/cell4_domains UNION ALL) ...;
-- plus: SELECT COUNT(*) FROM chart_facts WHERE fact_category=... (denominator)
```

## Verbatim results
- chart_facts denominator: 482012f1=70, 1c826d5a=70
- cell1 (signals): 482012f1=**61**, 1c826d5a=**56**
- cell2_salience: 482012f1=`supporting=61`, 1c826d5a=`supporting=56`
- cell5_type: 482012f1=`composite_state=61`, 1c826d5a=`composite_state=56`
- cell3_attr: 482012f1=`61/61`, 1c826d5a=`56/56`
- cell4_domains: both=`character|relationship`

## 5-cell verdicts
1. **Consumed?** YES (61/56 signals resolve to this category on the two charts).
2. **Salience:** uniformly `supporting` — proportionate for a low-decision-weight esoteric point; NO inflation.
3. **Entity attribution:** 100% (61/61, 56/56) — every signal carries a non-empty resolvable `constituent_facts_array`. SOUND.
4. **Domain mapping:** DEFECT — collapses to the shard-wide default `character|relationship` (see finding).
5. **Emergence:** 56–61 signals per chart, all `composite_state`. Consumed at scale; 70 facts → ~60 signals.

## design_correctness_verdict: WEAK
Consumed, fully attributed, salience proportionate — but domain mapping is the shard-wide default-collapse defect.

## Findings
- **F1 (class 2 WRONG; domain mis-mapping; MED):** avayogi signals map exclusively to default `character|relationship` domain on both charts (cell4=`character|relationship`), identical to 11 other semantically-distinct esoteric_point categories in this shard. The avayogi (the "non-yogi" malefic point) has no natural affinity confined to character/relationship; default-collapse means it can never surface under any other domain-filtered query (KP-4 analog; class-1 UNREACHABLE consequence for domain-scoped retrieval). Suspected layer: L-writer (bo_laksana domain-mapping rule). Reproducible call = SQL above, cell4.
