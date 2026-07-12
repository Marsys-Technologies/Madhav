# shard-9b-tara_bala_natal_baseline

**shard_id:** 9b-tara_bala_natal_baseline
**lane:** 9b
**charts:** 482012f1, 1c826d5a

## SQL run
5-cell recipe with `f.fact_category = 'tara_bala_natal_baseline'`.

## Verbatim results
- chart_facts rows: 270 (both charts)
- cell1: Abhisek=45, Abhinandan=45
- cell2_salience: both `supporting=45`
- cell5_type: both `composite_state=45`
- cell3_attr: 45/45 both (100%)
- cell4_domains: both `character|spirituality` (invariant)

## 5-cell verdicts
1. Consumed? YES (45/chart).
2. Salience: uniform `supporting` — proportionate.
3. Attribution: 45/45 resolvable — PASS.
4. Domain: **INVARIANT** `character|spirituality`. Tara bala is Moon-nakshatra-relative strength; `spirituality` is a defensible-but-narrow default that would hide it from health/timing queries.
5. Emergence: 45 `composite_state` signals/chart.

## design_correctness_verdict: WEAK
Consumed, fully attributed, proportionate salience; invariant `character|spirituality` domain tuple is the sole defect (narrower than the fact's actual relevance).

## Findings
- **F1 (class 2 / domain mis-map):** 45/45 → invariant `character|spirituality`. Suspected layer: L-writer. Severity: LOW. Evidence: cell4 single value. Dedupe: KP-4-class default-domain.
