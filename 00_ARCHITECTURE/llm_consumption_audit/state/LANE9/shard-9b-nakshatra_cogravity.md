# Shard 9b-nakshatra_cogravity

shard_id: 9b-nakshatra_cogravity
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL: 9b 5-cell recipe with f.fact_category='nakshatra_cogravity'. chart_facts census: 20 rows combined.

## Verbatim results
- cell1: 482=10, 1c8=10 → CONSUMED
- cell2_salience: 482=supporting=10 ; 1c8=supporting=10
- cell3_attr: 482=10/10 ; 1c8=10/10 (100%)
- cell4_domains: 482=character|relationship ; 1c8=character|relationship
- cell5_type: 482=composite_state=10 ; 1c8=composite_state=10

## 5-cell verdicts
1. Consumed? YES — 10 signals vs ~10 chart_facts rows/chart (near-1:1, healthy pass-through).
2. Salience: 100% supporting — proportionate. PASS.
3. Attribution: 100%. PASS.
4. Domain: character|relationship — plausible for a nakshatra relational/co-gravity measure. Reasonable, though uniform.
5. Emergence: 10 signals, single type class.

## design_correctness_verdict: SOUND

## Affirmative evidence of correct consumption
- Near-1:1 emergence (10 signals from ~10 facts/chart) = no funnel loss.
- 100% attributed (cell3 10/10) — every constituent_facts_array resolves to chart_facts.fact_id.
- Salience proportionate (all supporting).
- Domain (character|relationship) is defensible for a nakshatra relational co-gravity metric.

## Findings: none of material severity. Minor: domain mapping is uniform 2-domain (not per-pair), noted but not raised as a finding given small, low-weight, relational-by-nature category.
