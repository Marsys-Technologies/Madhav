# shard-9b-panchanga_abhijit_muhurta

**shard_id:** 9b-panchanga_abhijit_muhurta
**lane:** 9b

## Exact SQL run
5-cell recipe with `f.fact_category = 'panchanga_abhijit_muhurta'` over both charts. Denominator query as per recipe.

## Verbatim results
- chart_facts denominator: Abhisek=3, Abhinandan=3.
- cell1 (consumed): Abhisek=15, Abhinandan=15.
- cell2_salience: both `supporting` only.
- cell3_attr: both `15/15` (100%).
- cell4_domains: both `character|spirituality`.
- cell5_type: both `panchanga`.

## Five-cell verdicts
1. Consumed? YES. Note **emergence multiplication**: 3 chart_facts rows → 15 signals/chart (5×), each fact reused across 5 composite signals.
2. Salience: uniformly `supporting` — proportionate.
3. Attribution: 100% resolvable.
4. Domain: `character|spirituality`.
5. Emergence: 15 signals/chart from 3 facts, `panchanga` type.

## design_correctness_verdict: SOUND
Consumed, 100% attributed, proportionate `supporting` salience, correctly typed `panchanga`. The 3→15 emergence is fact-reuse across composite panchanga signals, not fabrication (cell3 fully attributes each). `character|spirituality` for an abhijit-muhurta (auspicious-timing) fact is a defensible, if generous, mapping — abhijit muhurta is a time-quality construct, mildly loose as a natal `character` fact but within tolerance and not a mis-map worth a finding.

## Findings
(none — PASS with quoted payload above)
