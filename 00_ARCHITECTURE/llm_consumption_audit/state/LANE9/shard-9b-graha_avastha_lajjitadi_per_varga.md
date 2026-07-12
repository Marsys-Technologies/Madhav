# Shard 9b — graha_avastha_lajjitadi_per_varga

**Shard id:** `9b-graha_avastha_lajjitadi_per_varga`
**Charts:** Abhisek `482012f1`, Abhinandan `1c826d5a`

## Exact SQL run
9b 5-cell recipe with `f.fact_category = 'graha_avastha_lajjitadi_per_varga'`; plus chart_facts COUNT.

## Verbatim results
- chart_facts rows: both 45.
- cell1: Abhisek 5, Abhinandan 5 → CONSUMED.
- cell2 salience: both `supporting=5`.
- cell3 attribution: both 5/5 → 100%.
- cell4 domains: both `character|career`.
- cell5 type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES (funnel narrowing 45→5).
2. Salience: all `supporting` — proportionate. PASS.
3. Attribution: 100%. PASS.
4. Domain: `character|career` — but the base `graha_avastha_lajjitadi` maps to `character|relationship`. Same underlying avastha type, DIFFERENT domain.
5. Emergence: 5 signals from 45 chart_facts rows.

## design_correctness_verdict: WEAK
Domain inconsistency (defect c/class 3): the per-varga variant of lajjitadi drops the `relationship` domain its own base category carries, reverting to the default `character|career`. This means a relationship-domain query surfaces the summary lajjitadi but not the per-varga detail — a differentiated mapping applied inconsistently across the same avastha family.

## Findings
- **F1 (class 3 INCONSISTENT — domain mapping) — LOW.** `graha_avastha_lajjitadi` → `character|relationship` but `graha_avastha_lajjitadi_per_varga` → `character|career` for the same avastha type. Evidence: cell4 here `character|career` vs sibling shard `character|relationship`. Repro: compare cell4 across the two lajjitadi shards. Suspected layer: L-writer (bo_laksana domain-mapping table applies the relationship tag only to the summary, not per-varga).
- **F2 (class 1 funnel narrowing) — LOW.** 45 chart_facts → 5 signals.
