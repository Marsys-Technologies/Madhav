# shard-9b-nakshatra_dispositor

**shard_id:** 9b-nakshatra_dispositor
**lane:** 9b

## Exact SQL run
5-cell recipe with `f.fact_category = 'nakshatra_dispositor'` over both charts. Denominator query as per recipe.

## Verbatim results
- chart_facts denominator: Abhisek=200, Abhinandan=200.
- cell1 (consumed): Abhisek=110, Abhinandan=110.
- cell2_salience: Abhisek `background=10, major=21, supporting=79`; Abhinandan `background=30, major=11, supporting=69`.
- cell3_attr: Abhisek `110/110`; Abhinandan `110/110` (100%).
- cell4_domains: both `character|relationship`.
- cell5_type: both `composite_state=110`.

## Five-cell verdicts
1. Consumed? YES but partial (110 of 200 facts surface).
2. Salience: supporting-dominant with a proportionate `major` minority — dispositor placement is genuinely decision-relevant, so `major=21/11` is defensible.
3. Attribution: 100% resolvable (SOUND).
4. Domain: uniformly `character|relationship`.
5. Emergence: 110 signals/chart, composite_state.

## design_correctness_verdict: WEAK
Attribution and salience are sound. Two soft defects: (a) only 110 of 200 dispositor facts per chart emerge as signals (~45% funnel loss — width narrowing, though dispositor rows include internal variants so not all are independently reading-relevant); (b) uniform `character|relationship` domain — the nakshatra dispositor of a wealth/career significator should route to those domains, but every dispositor signal defaults to character|relationship (KP-4-style family-default mapping), so a wealth-domain query cannot surface dispositor evidence.

## Findings
- **F1** — domain family-default mapping. class 2 (WRONG). severity MED. Evidence: cell4 both charts `character|relationship` across all 110 signals; no domain differentiation by the dispositor's significations, blocking domain-filtered retrieval (KP-4 analog).
