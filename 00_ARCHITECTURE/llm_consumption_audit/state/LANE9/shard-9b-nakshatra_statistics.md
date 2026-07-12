# shard-9b-nakshatra_statistics

**shard_id:** 9b-nakshatra_statistics
**lane:** 9b

## Exact SQL run
5-cell recipe with `f.fact_category = 'nakshatra_statistics'` over both charts. Denominator query as per recipe.

## Verbatim results
- chart_facts denominator: Abhisek=34, Abhinandan=35.
- cell1 (consumed): Abhisek=34, Abhinandan=35 (full ingestion).
- cell2_salience: both `supporting` only.
- cell3_attr: Abhisek `34/34`; Abhinandan `35/35` (100%).
- cell4_domains: both `character|relationship`.
- cell5_type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES (full).
2. Salience: uniformly `supporting` — proportionate.
3. Attribution: 100% resolvable.
4. Domain: uniformly `character|relationship`.
5. Emergence: 34–35 signals/chart, composite_state.

## design_correctness_verdict: WEAK
Attribution and salience are clean (all `supporting`, 100% attributed). The soft defect: `nakshatra_statistics` is an aggregate/descriptive-statistics category (counts and distributions of nakshatra occupancy) — low decision weight — yet every one of its 34–35 facts is surfaced as a signal mapped to `character|relationship`. A distributional-statistics fact is not intrinsically a relationship fact; this is category-family default mapping and mild trivia-surfacing (each aggregate stat becomes a supporting signal). Because it sits at `supporting` (not `major`), it does not drown higher-tier signals, so severity is contained.

## Findings
- **F1** — descriptive-statistics trivia surfaced as signals with default domain. class 2 (WRONG, domain) / secondary DROWNED-trivia character. severity LOW. Evidence: cell1 full ingestion (34/34, 35/35) of an aggregate-stats category, cell4 both `character|relationship`; distributional statistics given a relationship domain by family default rather than content.
