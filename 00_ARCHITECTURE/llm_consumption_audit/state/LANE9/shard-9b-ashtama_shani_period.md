# shard-9b-ashtama_shani_period

**shard_id:** 9b-ashtama_shani_period
**charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## Reproducible call
Proven 9b 5-cell recipe, `fact_category='ashtama_shani_period'`, both charts; plus chart_facts denominator count.

## Verbatim results
- chart_facts denominator: Abhisek=260, Abhinandan=220
- cell1: Abhisek=200, Abhinandan=170
- cell2_salience: Abhisek `supporting=200`; Abhinandan `supporting=170`
- cell3_attr: Abhisek `200/200`; Abhinandan `170/170`
- cell4_domains: both `career|health|relationship`
- cell5_type: both `sade_sati` (=200 / =170)

## Five-cell verdicts
1. Consumed: YES.
2. Salience: all `supporting` — proportionate. PASS.
3. Attribution: full. PASS.
4. Domain: uniform `career|health|relationship`. PASS-with-note.
5. Emergence: `signal_type_class=sade_sati`.

## design_correctness_verdict: WEAK
Attribution/salience sound. Defect: Ashtama Shani (Saturn transiting the 8th from Moon) is classically DISTINCT from Sade Sati, yet collapsed to `signal_type_class=sade_sati` — same type-collapse as anumukha/ardha-ashtama shani. Cross-category pattern (three Saturn-period categories all mislabeled `sade_sati`) — flag at conductor merge.

## Findings
- summary: Ashtama Shani period signals mislabeled `signal_type_class=sade_sati` (8th-from-Moon transit is not sade-sati); failure_class 2 (WRONG — type mislabel); severity LOW; evidence: cell5_type `sade_sati=200`/`=170`. Suspected layer: L-writer (bo_laksana signal_type_class). Cross-category: shares the mislabel with anumukha_shani_period + ardha_ashtama_shani_period — a single systematic Saturn-transit taxonomy collapse.
