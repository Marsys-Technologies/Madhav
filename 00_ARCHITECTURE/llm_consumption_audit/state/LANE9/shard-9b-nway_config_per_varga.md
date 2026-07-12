# shard-9b-nway_config_per_varga

**shard_id:** 9b-nway_config_per_varga
**lane:** 9b

## Exact SQL run
5-cell recipe with `f.fact_category = 'nway_config_per_varga'` over both charts. Denominator query as per recipe.

## Verbatim results
- chart_facts denominator: Abhisek=83, Abhinandan=85.
- cell1 (consumed): Abhisek=83, Abhinandan=85 (full ingestion).
- cell2_salience: both `supporting` only.
- cell3_attr: Abhisek `83/83`; Abhinandan `85/85` (100%).
- cell4_domains: both `character|career`.
- cell5_type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES (full).
2. Salience: uniformly `supporting` — proportionate.
3. Attribution: 100% resolvable.
4. Domain: uniformly `character|career`.
5. Emergence: 83–85 signals/chart, composite_state.

## design_correctness_verdict: SOUND
Full ingestion, 100% attribution, proportionate `supporting` salience (multi-graha varga-configuration patterns correctly kept below chart-defining), and `character|career` domain is defensible for association/conjunction configuration patterns. Affirmative evidence: cell3 `83/83`, `85/85`; cell2 no tier inflation. Minor note: domain is a category-family default (character|career for all), but for generic n-way varga configs this is a reasonable neutral mapping rather than a mis-map, so it does not rise to a finding.

## Findings
(none — PASS with quoted payload above)
