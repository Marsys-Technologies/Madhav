# shard-9b-panchanga_varjyam

Lane: 9b (MSR ingestion coverage + fidelity). Charts: A=482012f1 (Abhisek), B=1c826d5a (Abhinandan).

## Exact SQL run
5-cell recipe (charter §4) with `<CAT>`=`panchanga_varjyam`, plus chart_facts existence check:
```
SELECT fact_category, chart_id, COUNT(*) FROM chart_facts WHERE fact_category='panchanga_varjyam' AND chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a') GROUP BY 1,2;
-- 5-cell sig CTE (unnest constituent_facts_array JOIN chart_facts on fact_id+chart_id WHERE fact_category='panchanga_varjyam')
-- fan-out probe: per-fact count(DISTINCT signal_id); per-signal array_length(constituent_facts_array,1)
```

## Verbatim results
- chart_facts: A=3, B=3.
- cell1 (signals consumed): A=15, B=15.
- cell2 salience tiers: `supporting` (only) on both charts.
- cell3 attribution: A=15/15, B=15/15 (100% non-empty constituent arrays).
- cell4 domains: `character|spirituality` (single distinct value, both charts).
- cell5 emergence by type: `panchanga=15` (A), `panchanga=15` (B).
- Fan-out: every signal has csize=1 (single constituent fact); each of the 3 facts → exactly 5 distinct signal_ids. 3 facts × 5 = 15 signals = 5:1 duplication.

## 5-cell verdicts
1. Consumed: YES (15 signals/chart). 2. Salience: `supporting` — proportionate (low-decision-weight muhurta fact correctly at low tier). 3. Attribution: SOUND, 100% attributed. 4. Domain: DEFAULT/mis-map — varjyam is an inauspicious muhurta time-segment; `character|spirituality` is a default bucket shared verbatim with 4 other panchanga muhurta categories. 5. Emergence: 5:1 duplication (15 signals from 3 single-fact rows), all identical on every graded axis.

## design_correctness_verdict: WEAK

## Findings
- F1 (class 7 DROWNED, MED): 3 chart_facts fan out to 15 signals (5 per fact), each single-fact, all identical signature_tier=supporting / type=panchanga / domains=character|spirituality — systematic 5:1 signal multiplication inflating the funnel with duplicative rows. Evidence: per-fact count(DISTINCT signal_id)=5 for fact_ids a04c610d…, 41177ec3…, 2228dc62…; max csize=1.
- F2 (class 2 WRONG, LOW): domain mapping `character|spirituality` applied uniformly regardless of relevance; varjyam (inauspicious muhurta window) has no natural character/spirituality signification — identical mapping shared across varjyam/vijaya_muhurta/visha_ghati/yamaganda_kalam/yamakantaka (KP-4-analog default-domain pattern). Rationale: an inauspicious time-segment cannot surface in any domain-filtered query where it would matter, and never distinguishes from 4 sibling categories.
