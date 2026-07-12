# shard-9b-panchanga_brahma_muhurta

**shard_id:** 9b-panchanga_brahma_muhurta
**lane:** 9b

## Exact SQL run
5-cell recipe with `f.fact_category = 'panchanga_brahma_muhurta'` over both charts. Denominator query as per recipe.

## Verbatim results
- chart_facts denominator: Abhisek=3, Abhinandan=3.
- cell1 (consumed): Abhisek=15, Abhinandan=15.
- cell2_salience: both `supporting` only.
- cell3_attr: both `15/15` (100%).
- cell4_domains: both `character|spirituality`.
- cell5_type: both `panchanga`.

## Five-cell verdicts
1. Consumed? YES. Emergence multiplication 3 facts → 15 signals/chart (5×).
2. Salience: uniformly `supporting` — proportionate.
3. Attribution: 100% resolvable.
4. Domain: `character|spirituality`.
5. Emergence: 15 signals/chart from 3 facts, `panchanga` type.

## design_correctness_verdict: SOUND
Consumed, 100% attributed (`15/15`), proportionate `supporting` salience, correctly typed `panchanga`. Brahma-muhurta (the pre-dawn auspicious interval — a time-quality/spiritual-practice construct) mapping to `character|spirituality` is well-justified (this is the one panchanga category where the spirituality domain is genuinely apt). Emergence 3→15 is composite fact-reuse, fully attributed. No defect pattern.

## Findings
(none — PASS with quoted payload above)
