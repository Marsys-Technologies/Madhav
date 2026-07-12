# shard-9b-graha_cheshta_bala_per_varga

**Shard id:** graha_cheshta_bala_per_varga (Lane 9b, MSR ingestion matrix)
**Charts:** 482=Abhisek `482012f1-…`, 1c826=Abhinandan `1c826d5a-…`

## Exact SQL run
chart_facts existence: `SELECT ... COUNT(*) FROM chart_facts WHERE fact_category='graha_cheshta_bala_per_varga' AND chart_id IN (…)` → 482=735, 1c826=735.
5-cell recipe: the proven 9b WITH-sig CTE (unnest constituent_facts_array JOIN chart_facts on fact_category) over bodha_msr_signals for both charts.

## Verbatim results
- cell1 (consumed): 482=105, 1c826=105
- cell2 (salience): 482=`major=39, supporting=66`; 1c826=`background=15, major=8, supporting=82`
- cell3 (attribution): 482=`105/105`, 1c826=`105/105`
- cell4 (domains): both=`character|career`
- cell5 (type): both=`composite_state=105`

## 5-cell verdicts
1. Consumed? YES (105 signals/chart; 735 chart_facts → 105 signals ≈ 7:1 narrowing, but ingested).
2. Salience: mixed supporting/major — proportionate for a shadbala sub-component (motional strength). Not inflated.
3. Attribution: 100% resolvable. No R-44a defect. AFFIRMATIVE PASS.
4. Domain: mono-mapped to `character|career` for a strength quantity relevant to every graha-governed domain. Default-domain collapse (KP-4 pattern).
5. Type: collapsed to `composite_state` — no distinct bala/strength class.

## design_correctness_verdict: WEAK
Consumed + fully attributed + proportionate salience, but domain mono-mapping to character|career makes graha motional-strength un-findable under wealth/health/relationship domain-filtered queries though it is load-bearing for whether that graha delivers in those domains.

## Findings
- **F1** class 2 (WRONG) / class 1 consequence — severity MED. Cheshta-bala signals always `domains_affected_array=character|career` regardless of the graha's house/domain significations. Evidence: cell4 both charts = `character|career`, invariant. A wealth-domain query filtering domains would never surface this graha-strength evidence.
