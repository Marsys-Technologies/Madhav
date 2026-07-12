# Shard 9b — panchanga_rahu_kalam

shard_id: 9b-panchanga_rahu_kalam
charts: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek), 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan)

## Exact SQL run
1. chart_facts existence: `SELECT fact_category, chart_id, COUNT(*) FROM chart_facts WHERE fact_category='panchanga_rahu_kalam' AND chart_id IN (...) GROUP BY ...`
2. 5-cell recipe (proven 9b recipe, verbatim from brief, `<CAT>`=panchanga_rahu_kalam).
3. Duplication probe: `WITH sig AS (SELECT DISTINCT ms.signal_id, ms.signal_headline_text FROM bodha_msr_signals ms JOIN LATERAL unnest(constituent_facts_array) cf(fid) ON true JOIN chart_facts f ON f.fact_id=cf.fid AND f.chart_id=ms.chart_id WHERE f.fact_category='panchanga_rahu_kalam' AND ms.chart_id='482...') SELECT signal_headline_text, count(*) FROM sig GROUP BY 1;`

## Verbatim results
- chart_facts: 3 rows per chart (both charts).
- cell1 (consumed): 15 signals per chart (both).
- cell2 (salience): `supporting=15` (both charts) — uniformly supporting, NO major/chart_defining.
- cell3 (attribution): 15/15 non-empty constituent_facts_array (both) — 100% attributed.
- cell4 (domains): `character|spirituality` (both).
- cell5 (type): `panchanga=15` (both).
- Duplication probe returned 3 distinct headlines each appearing 5×:
  - "panchanga rahu kalam: duration minutes = 84.8 [ga_panchanga]" ×5
  - "panchanga rahu kalam: end iso = 1984-02-05T12:09:58+00:00 [ga_panchanga]" ×5
  - "panchanga rahu kalam: start iso = 1984-02-05T10:45:09.500000+00:00 [ga_panchanga]" ×5
  → dup_factor = 5.00 (15 signals / 3 distinct headlines).

## Five-cell verdicts
1. Consumed by bo_laksana? YES (15 signals/chart, resolving to 3 chart_facts).
2. Salience: `supporting` only — proportionate/low; NOT inflated (good).
3. Entity attribution: 15/15 resolvable — clean.
4. Domain mapping: `character|spirituality` — MIS-MAPPED. Rahu Kalam is an inauspicious muhurta/electional time-band; it has no natural character/spirituality reading and can never surface under a timing/muhurta domain query. Uniform default across the whole panchanga family.
5. Emergence: 15 signals from 3 facts = 5× duplication of identical-headline signals.

## design_correctness_verdict: WEAK

## Findings
- FC-9b-rahu_kalam-DUP (class 7 DROWNED, MED): each of the 3 rahu_kalam facts is emitted as 5 byte-identical-headline MSR signals (dup_factor 5.00). 5× volume inflation with zero added information; headlines are raw fact restatements ("duration minutes = 84.8", "start iso = ...") — descriptive trivia. Suspected layer: L2 bo_laksana writer (signal-emission multiplication). Evidence: duplication probe above.
- FC-9b-rahu_kalam-DOMAIN (class 2 WRONG, MED; class-1 consequence): all 15 signals mapped to `character|spirituality`, a family-wide default. A muhurta/timing query cannot retrieve this inauspicious-time-band category → effectively UNREACHABLE for its natural domain. Suspected layer: L2 domain-mapping. Evidence: cell4=`character|spirituality`.
