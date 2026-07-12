# Shard 9b-karakatva_strength_per_significance

shard_id: 9b-karakatva_strength_per_significance
stream: 9b (MSR ingestion coverage + fidelity)
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run (proven 9b 5-cell recipe)
```sql
WITH sig AS (
  SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
         ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'karakatva_strength_per_significance'
    AND ms.chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
)
SELECT 'cell1', chart_id, COUNT(*) ... [full 5-cell UNION as per recipe]
```
chart_facts census: 600 rows combined both charts (fact exists).

## Verbatim results
- cell1 (consumed): 482=65, 1c8=56 → CONSUMED
- cell2_salience: 482=supporting=65 ; 1c8=supporting=56
- cell3_attr: 482=65/65 ; 1c8=56/56 (100% attributed, all resolve to chart_facts.fact_id)
- cell4_domains: 482=character|career ; 1c8=character|career
- cell5_type: 482=karaka_alignment=65 ; 1c8=karaka_alignment=56

## 5-cell verdicts
1. Consumed? YES (65/56 signals).
2. Salience: 100% supporting — proportionate, NOT inflated. PASS.
3. Attribution: 100% attributed. PASS.
4. Domain: uniform character|career for ALL signals. DEFECT — karakatva strength PER SIGNIFICANCE spans significations across wealth/health/relationship/progeny (Venus=relationship, Jupiter=wealth/progeny, etc.). Collapsing every significance to character|career means wealth/health/relationship queries cannot surface karaka strength.
5. Emergence: 65/56, single type class (karaka_alignment).

## design_correctness_verdict: WEAK

## Findings
- summary: karakatva_strength_per_significance signals uniformly domain-mapped to character|career regardless of which significance/karaka, blocking domain-filtered retrieval (wealth/health/relationship).
  failure_class: 2 (WRONG — domain mis-mapping; class-1 UNREACHABLE consequence for domain-filtered queries)
  severity: MED
  suspected_layer: L-writer (bo_laksana domain mapping)
  evidence: cell4 = "character|career" is the ONLY distinct domains_affected_array across all 65 (482) and 56 (1c8) signals; a category named "…_per_significance" covering all bhava/karaka significations reduced to 2 static domains.
  reproducible_call: the SQL above, cell4_domains row.
