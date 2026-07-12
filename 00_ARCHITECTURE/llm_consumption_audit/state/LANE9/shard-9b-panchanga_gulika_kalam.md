# Lane 9b shard trace — `panchanga_gulika_kalam`

- **shard_id:** shard-9b-panchanga_gulika_kalam
- **lane:** 9b (MSR ingestion coverage + fidelity)
- **charts:** Abhisek 482012f1-710e-4a25-994a-93821f5871aa + Abhinandan 1c826d5a-41cb-4450-b4dc-59d440e5f75a
- **fact_category exists in chart_facts:** YES — 3 rows/chart (both charts identical)

## Exact SQL run (proven 9b 5-cell recipe + duplication probe)
```sql
WITH sig AS (
  SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
         ms.domains_affected_array, ms.constituent_facts_array
  FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'panchanga_gulika_kalam'
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
  WHERE f.fact_category='panchanga_gulika_kalam' AND ms.chart_id='482012f1-710e-4a25-994a-93821f5871aa')
SELECT COUNT(DISTINCT signal_id) sigs, COUNT(DISTINCT fid) facts FROM pairs;
-- chart_facts existence:
SELECT fact_category, chart_id, COUNT(*) FROM chart_facts WHERE fact_category='panchanga_gulika_kalam'
  AND chart_id IN (C1,C2) GROUP BY 1,2;
```

## Verbatim query results (both charts returned IDENTICAL counts)
- **cell1 (consumed):** chart 482012f1-710e-4a25-994a-93821f5871aa = 15 signals; chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a = 15 signals.
- **cell2 (salience tiers):** `supporting=15` (both charts) — 100% at supporting tier.
- **cell5 (signal_type_class):** `panchanga=15` (both charts).
- **cell3 (attribution ratio):** `15/15` (both charts) — every signal has non-empty constituent_facts_array; all resolve to real chart_facts.fact_id.
- **cell4 (domains):** `character|spirituality` (both charts).
- **duplication probe (chart 482012f1-710e-4a25-994a-93821f5871aa):** distinct_signals=15, distinct_facts_ingested=3, cf_total=3, signals_per_fact=5.0.

## Five-cell verdicts (brief §4)
1. **Consumed by bo_laksana?** YES (both charts).
2. **Salience class:** `supporting` (uniform) — proportionate, NOT inflated. No R-44b pattern.
3. **Entity attribution:** 15/15 resolvable (3 distinct facts, = chart_facts total) — NO R-44a attribution failure; 100% width ingested.
4. **Domain mapping:** `character|spirituality` — DEFAULT-COLLAPSE (see F2).
5. **Signal-emergence count:** 15 signals/chart from 3 distinct facts (signals_per_fact=5.0) — 5x DUPLICATION WALL (see F1), all signal_type_class=panchanga.

## design_correctness_verdict: **WEAK**
Consumed, fully attributed, salience proportionate, but degraded by a systematic 5.0x exact-duplicate signal wall, plus muhurta default-domain-collapse. Not BROKEN (values correct, attribution intact, low tier); not SOUND (duplication + domain defects present).

## Findings
### Finding F1 — 5.0x exact-duplicate signal wall (class 7 DROWNED)
- **primary_failure_class:** 7 (DROWNED)
- **severity:** MED
- **suspected_layer:** L-writer (bo_laksana MSR ingestion — likely one identical signal emitted per ayanamsha pass, 5 passes)
- **reproducible_call:** duplication probe SQL above (pairs CTE: COUNT(DISTINCT signal_id) vs COUNT(DISTINCT fid))
- **verbatim_evidence:** chart 482012f1-710e-4a25-994a-93821f5871aa: distinct_signals=15, distinct_facts_ingested=3, signals_per_fact=5.0. Confirmed on `panchanga karana: name = Garaja` specimen: 5 distinct signal_ids (2c4ac102, 30a01caf, 7799ee60, 79087f02, c595ed13) ALL carry identical signature_tier=supporting, signal_type_class=panchanga, domains=character|spirituality, epistemic_tier=single, nfacts=1, and identical constituent fact cf1=496b7b5c4146c901 — differing ONLY in random signal_id.
- **rationale (charter 7.4):** 80% of this category's MSR signal volume (12 of 15 rows per chart) is exact duplication of 3 underlying fact(s) — far above any reasonable acharya tolerance for a ranked/listed surface. At supporting tier the blast radius is bounded (won't drown chart_defining top-K) hence MED not HIGH, but it 5x-inflates any panchanga-scoped retrieval and is the R-44 duplication-wall anchor pattern re-manifesting in the panchanga family.
- **dedupe:** relates to R-44a/R-44 duplication-wall family; panchanga-family manifestation appears distinct from the 298/300 top-candidate anchor — flag as candidate-new for conductor dedupe.
### Finding F2 — muhurta/electional panchanga default-mapped to character|spirituality (class 2 WRONG, pattern c)
- **primary_failure_class:** 2 (WRONG) / domain mis-mapping
- **severity:** MED
- **suspected_layer:** L-writer (bo_laksana domain-assignment)
- **reproducible_call:** cell4 domains SQL above
- **verbatim_evidence:** domains_affected_array = `character|spirituality` for 100% of this category's signals, both charts. 11 of the 12 panchanga categories in this shard map to the identical `character|spirituality` default; only panchanga_nakshatra_moon differs (character|relationship).
- **rationale:** `panchanga_gulika_kalam` is a muhurta/electional (timing-quality) construct with no natal-character or spirituality bearing; uniform assignment to character|spirituality is the default-domain-collapse (KP-4-analog) pattern — regardless of the specific element's significance it lands in the same generic pair, so it can never surface correctly under a domain-filtered query nor be excluded from character/spirituality reads where it is noise.

## Completion marker: DONE
