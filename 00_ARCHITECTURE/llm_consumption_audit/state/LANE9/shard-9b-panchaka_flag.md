# shard-9b-panchaka_flag

**shard_id:** 9b-panchaka_flag
**lane:** 9b

## Exact SQL run
5-cell recipe with `f.fact_category = 'panchaka_flag'` over both charts. Denominator query as per recipe.

## Verbatim results
- chart_facts denominator: Abhisek=10, Abhinandan=5.
- cell1 (consumed): Abhisek=10, Abhinandan=5 (full ingestion).
- cell2_salience: both `supporting` only.
- cell3_attr: Abhisek `10/10`; Abhinandan `5/5` (100%).
- cell4_domains: both `character|spirituality`.
- cell5_type: both `panchanga`.

## Five-cell verdicts
1. Consumed? YES (full).
2. Salience: uniformly `supporting` — proportionate (a muhurta/panchaka flag is correctly not chart-defining).
3. Attribution: 100% resolvable.
4. Domain: uniformly `character|spirituality`.
5. Emergence: 5–10 signals/chart, `signal_type_class=panchanga`.

## design_correctness_verdict: SOUND
Full ingestion, 100% attribution, proportionate salience, correct `signal_type_class=panchanga`, and `character|spirituality` domain is defensible for a panchaka (muhurta-quality) flag. Affirmative evidence: cell3 `10/10`, `5/5`; cell5 correctly typed `panchanga` (not mis-collapsed to composite_state like the nakshatra family). No defect pattern present.

## Findings
(none — PASS with quoted payload above)
