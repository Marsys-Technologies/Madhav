# shard-9b-anumukha_shani_period

**shard_id:** 9b-anumukha_shani_period
**charts:** Abhisek 482012f1-710e-4a25-994a-93821f5871aa · Abhinandan 1c826d5a-41cb-4450-b4dc-59d440e5f75a

## Reproducible call
Proven 9b 5-cell recipe (CTE over `bodha_msr_signals` × `unnest(constituent_facts_array)` JOIN `chart_facts` filtered `fact_category='anumukha_shani_period'`, both charts). Plus denominator: `SELECT COUNT(*) FROM chart_facts WHERE fact_category='anumukha_shani_period' AND chart_id IN (...)`.

## Verbatim results
- chart_facts denominator: Abhisek=100, Abhinandan=100
- cell1 (consumed): Abhisek=70, Abhinandan=70
- cell2_salience: Abhisek `supporting=70`; Abhinandan `supporting=70`
- cell3_attr: Abhisek `70/70`; Abhinandan `70/70`
- cell4_domains: both `career|health|relationship`
- cell5_type: both `sade_sati=70`

## Five-cell verdicts
1. Consumed: YES (70 signals each chart).
2. Salience: all `supporting` — proportionate, NOT inflated. PASS.
3. Attribution: 70/70 resolvable both charts — full. PASS.
4. Domain: uniform `career|health|relationship` — plausible for a Saturn-transit affliction; not obviously wrong. PASS-with-note.
5. Emergence: 100 facts → 70 signals, all `signal_type_class=sade_sati`.

## design_correctness_verdict: WEAK
Attribution and salience are sound. Defect: Anumukha Shani (an approaching-Saturn sub-period) is bucketed under `signal_type_class=sade_sati`. Classically the sade-sati taxon is the 7.5-yr transit of Saturn over natal Moon ±1 sign; anumukha/kantaka sub-periods are Saturn-transit afflictions but not sade-sati proper. Type-label collapse — low severity, findable/trustworthy otherwise.

## Findings
- summary: Anumukha Shani period signals mislabeled `signal_type_class=sade_sati`; failure_class 2 (WRONG — type mislabel); severity LOW; evidence: cell5_type = `sade_sati=70` for a non-sade-sati Saturn sub-period. Suspected layer: L-writer (bo_laksana signal_type_class assignment).
