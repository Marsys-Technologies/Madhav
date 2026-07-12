# shard-9b-tajik_vargottama_specific

**shard_id:** 9b-tajik_vargottama_specific
**lane:** 9b
**charts:** 482012f1, 1c826d5a

## SQL run
5-cell recipe with `f.fact_category = 'tajik_vargottama_specific'`.

## Verbatim results
- chart_facts rows: 30 (both charts)
- cell1: Abhisek=15, Abhinandan=15
- cell2_salience: both `supporting=15`
- cell5_type: both `varga_pattern=15`
- cell3_attr: 15/15 both (100%)
- cell4_domains: both `character|relationship` (invariant)

## 5-cell verdicts
1. Consumed? YES (15/chart from 30 chart_facts — full ingestion).
2. Salience: uniform `supporting` — proportionate.
3. Attribution: 15/15 resolvable — PASS.
4. Domain: **INVARIANT** `character|relationship`.
5. Emergence: 15 `varga_pattern` signals/chart.

## design_correctness_verdict: WEAK
Consumed and attributed; fixed-default domain tuple is the sole defect.

## Findings
- **F1 (class 2 / domain mis-map):** 15/15 → invariant `character|relationship`. Suspected layer: L-writer. Severity: LOW. Evidence: cell4 single value. Dedupe: KP-4-class.
