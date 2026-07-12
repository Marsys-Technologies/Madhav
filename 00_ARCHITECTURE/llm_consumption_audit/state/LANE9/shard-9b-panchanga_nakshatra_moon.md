# Lane 9b shard trace — `panchanga_nakshatra_moon`

- **shard_id:** shard-9b-panchanga_nakshatra_moon
- **lane:** 9b (MSR ingestion coverage + fidelity)
- **charts:** Abhisek 482012f1-710e-4a25-994a-93821f5871aa + Abhinandan 1c826d5a-41cb-4450-b4dc-59d440e5f75a
- **fact_category exists in chart_facts:** YES — 25 rows/chart (both charts identical)

## Exact SQL run (proven 9b 5-cell recipe + duplication probe)
```sql
WITH sig AS (
  SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
         ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'panchanga_nakshatra_moon'
    AND ms.chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a')
)
SELECT 'cell1' AS cell, chart_id::text, COUNT(*)::text FROM sig GROUP BY chart_id
UNION ALL SELECT 'cell2_salience', ... (signature_tier tally)
UNION ALL SELECT 'cell5_type', ... (signal_type_class tally)
UNION ALL SELECT 'cell3_attr', ... (SUM(array_length>0)/COUNT)
UNION ALL SELECT 'cell4_domains', ... (distinct domains);
-- plus duplication probe:
WITH pairs AS (SELECT DISTINCT ms.signal_id, cf.fid FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) cf(fid) ON true
  JOIN chart_facts f ON f.fact_id=cf.fid AND f.chart_id=ms.chart_id
  WHERE f.fact_category='panchanga_nakshatra_moon' AND ms.chart_id='482012f1-710e-4a25-994a-93821f5871aa')
SELECT COUNT(DISTINCT signal_id) sigs, COUNT(DISTINCT fid) facts FROM pairs;
-- chart_facts existence:
SELECT fact_category, chart_id, COUNT(*) FROM chart_facts WHERE fact_category='panchanga_nakshatra_moon'
  AND chart_id IN (C1,C2) GROUP BY 1,2;
```

## Verbatim query results (both charts returned IDENTICAL counts)
- **cell1 (consumed):** chart 482012f1-710e-4a25-994a-93821f5871aa = 25 signals; chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a = 25 signals.
- **cell2 (salience tiers):** `supporting=25` (both charts) — 100% at supporting tier.
- **cell5 (signal_type_class):** `panchanga=25` (both charts).
- **cell3 (attribution ratio):** `25/25` (both charts) — every signal has non-empty constituent_facts_array; all resolve to real chart_facts.fact_id.
- **cell4 (domains):** `character|relationship` (both charts).
- **duplication probe (chart 482012f1-710e-4a25-994a-93821f5871aa):** distinct_signals=25, distinct_facts_ingested=25, cf_total=25, signals_per_fact=1.0.

## Five-cell verdicts (brief §4)
1. **Consumed by bo_laksana?** YES (both charts).
2. **Salience class:** `supporting` (uniform) — proportionate, NOT inflated. No R-44b pattern.
3. **Entity attribution:** 25/25 resolvable (25 distinct facts, = chart_facts total) — NO R-44a attribution failure; 100% width ingested.
4. **Domain mapping:** `character|relationship` — defensible for a core panchanga limb.
5. **Signal-emergence count:** 25 signals/chart from 25 distinct facts (signals_per_fact=1.0) — clean 1:1, all signal_type_class=panchanga.

## design_correctness_verdict: **SOUND**
Consumed, 100% width ingested, 100% attributed, proportionate salience, sensible domain, clean 1:1 signal:fact ratio (no duplication). No defect pattern present.

## Findings
### PASS — SOUND, affirmative evidence
- **cell1 consumed:** YES both charts — distinct_signals=25/chart.
- **attribution:** 25/25 signals carry non-empty constituent_facts_array; distinct_facts_ingested=25 = chart_facts total (25) → 100% width ingested, no omission.
- **no duplication:** signals_per_fact=1.0 (clean 1:1, 25 facts -> 25 signals). Unlike the other 11 panchanga categories this shows NO 5x wall.
- **salience:** all `supporting` — proportionate for a descriptive panchanga fact, no inflation.
- **domain:** `character|relationship` — sensible (Moon-nakshatra governs manas/relational temperament).

## Completion marker: DONE
