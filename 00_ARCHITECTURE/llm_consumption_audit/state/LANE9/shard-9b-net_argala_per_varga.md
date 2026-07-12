# shard-9b-net_argala_per_varga

**shard_id:** 9b-net_argala_per_varga
**lane:** 9b

## Exact SQL run
5-cell recipe with `f.fact_category = 'net_argala_per_varga'` over both charts. Denominator query as per recipe.

## Verbatim results
- chart_facts denominator: Abhisek=1740, Abhinandan=1740.
- cell1 (consumed): Abhisek=1740, Abhinandan=1740 (full ingestion).
- cell2_salience: both `supporting` only (Abhisek `supporting=1740`, Abhinandan `supporting=1740`).
- cell3_attr: both `1740/1740` (100%).
- cell4_domains: both `career|character`.
- cell5_type: both `composite_state=1740`.

## Five-cell verdicts
1. Consumed? YES — fully, 1740 signals/chart.
2. Salience: uniformly `supporting`.
3. Attribution: 100% resolvable.
4. Domain: uniformly `career|character` for ALL 1740.
5. Emergence: **1740 signals/chart** — by far the largest single-category contributor in this shard.

## design_correctness_verdict: WEAK
Attribution is clean, but two defects. (a) **DROWNED / flooding:** one fact_category emits 1740 signals per chart — a duplication wall of net-argala-per-varga configs at a single tier. Even at `supporting`, 1740 near-uniform rows from one category dominate the signal population and make individual argala evidence un-findable by browse; a consumer cannot distinguish the decisive argala (e.g. on the 7th/10th lord) from the 1739 others. (b) **Domain collapse:** argala is intrinsically house-target-specific — argala on the 2nd/11th is wealth, on the 7th is relationship — yet all 1740 collapse to `career|character` regardless of target bhava, so no wealth/relationship query can surface the relevant argala.

## Findings
- **F1** — DROWNED / funnel-flooding. class 7 (DROWNED). severity HIGH. Evidence: cell1 & cell5 `1740` signals per chart, all cell2 `supporting`, all cell5 `composite_state` — a single category floods the funnel with a uniform wall; rationale for exceeding acharya tolerance (charter §7.4 amendment): no top-K discrimination is possible across 1740 co-tier rows, so the decision-relevant argala is not findable within the surface.
- **F2** — domain collapse / default mapping. class 2 (WRONG). severity MED. Evidence: cell4 both charts `career|character` for all 1740 argala configs irrespective of the target bhava's significations; blocks domain-filtered retrieval (KP-4 analog) despite argala being one of the most domain-specific structures in the canon.
