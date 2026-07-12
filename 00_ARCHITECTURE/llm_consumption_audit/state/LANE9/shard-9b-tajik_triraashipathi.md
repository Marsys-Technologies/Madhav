# shard-9b-tajik_triraashipathi

**shard_id:** 9b-tajik_triraashipathi
**lane:** 9b
**charts:** 482012f1, 1c826d5a

## SQL run
5-cell recipe with `f.fact_category = 'tajik_triraashipathi'`.

## Verbatim results
- chart_facts rows: 20 (both charts)
- cell1: Abhisek=10, Abhinandan=10
- cell2_salience: both `supporting=10`
- cell5_type: both `annual=10`
- cell3_attr: 10/10 both (100%)
- cell4_domains: both `character|relationship` (invariant)

## 5-cell verdicts
1. Consumed? YES (10/chart from 20 chart_facts — full ingestion).
2. Salience: uniform `supporting` — proportionate.
3. Attribution: 10/10 resolvable — PASS.
4. Domain: **INVARIANT** `character|relationship` for all 10; Tajik triraashipathi (tri-rasi lord) is an annual-strength construct, not intrinsically relational.
5. Emergence: 10 `annual` signals/chart.

## design_correctness_verdict: WEAK
Fully consumed, fully attributed, proportionate salience; sole defect is the fixed-default domain tuple.

## Findings
- **F1 (class 2 / domain mis-map):** 10/10 signals → invariant `character|relationship`. Suspected layer: L-writer domain assignment. Severity: LOW (small category). Evidence: cell4 single value `character|relationship`. Dedupe: KP-4-class.
