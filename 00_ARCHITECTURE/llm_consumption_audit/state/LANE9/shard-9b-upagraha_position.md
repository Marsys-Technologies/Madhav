# shard-9b-upagraha_position

**shard_id:** 9b-upagraha_position
**lane:** 9b
**charts:** 482012f1, 1c826d5a

## SQL run
5-cell recipe with `f.fact_category = 'upagraha_position'`.

## Verbatim results
- chart_facts rows: 420 (both charts)
- cell1: Abhisek=170, Abhinandan=159
- cell2_salience: both `supporting`
- cell5_type: both `composite_state`
- cell3_attr: 170/170 (Abhisek), 159/159 (Abhinandan) — 100%
- cell4_domains: both `character|relationship` (invariant)

## 5-cell verdicts
1. Consumed? YES (170/159 signals/chart from 210/chart chart_facts).
2. Salience: uniform `supporting` — proportionate.
3. Attribution: 100% resolvable — PASS.
4. Domain: **INVARIANT** `character|relationship`. Upagrahas (Gulika, Mandi, Dhuma, etc.) are malefic sensitive points strongly relevant to health, longevity, and obstacles — mapping all to `character|relationship` is a clear mis-classification.
5. Emergence: 170/159 `composite_state` signals/chart.

## design_correctness_verdict: WEAK
Consumed with perfect attribution; domain mapping is materially wrong for this category (malefic upagrahas defaulted to relationship domain), making them un-findable in health/longevity queries.

## Findings
- **F1 (class 2 WRONG / domain mis-map):** All upagraha_position signals (170/159) → invariant `character|relationship`, despite Gulika/Mandi's canonical health/longevity/obstacle significations. Produces a class-1 UNREACHABLE consequence for health-domain-filtered retrieval. Suspected layer: L-writer domain assignment. Severity: MED. Evidence: cell4 single value `character|relationship`; cell1 170/159. Dedupe: KP-4-class.
