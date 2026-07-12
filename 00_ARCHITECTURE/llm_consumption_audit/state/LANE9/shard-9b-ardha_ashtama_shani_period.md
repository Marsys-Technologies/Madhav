# shard-9b-ardha_ashtama_shani_period

**shard_id:** 9b-ardha_ashtama_shani_period
**charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## Reproducible call
Proven 9b 5-cell recipe, `fact_category='ardha_ashtama_shani_period'`, both charts; plus chart_facts denominator count.

## Verbatim results
- chart_facts denominator: Abhisek=345, Abhinandan=360
- cell1: Abhisek=240, Abhinandan=250
- cell2_salience: Abhisek `supporting=240`; Abhinandan `supporting=250`
- cell3_attr: Abhisek `240/240`; Abhinandan `250/250`
- cell4_domains: both `career|health|relationship`
- cell5_type: both `sade_sati` (=240 / =250)

## Five-cell verdicts
1. Consumed: YES.
2. Salience: all `supporting` — proportionate. PASS.
3. Attribution: full. PASS.
4. Domain: uniform `career|health|relationship`. PASS-with-note.
5. Emergence: `signal_type_class=sade_sati`.

## design_correctness_verdict: WEAK
Attribution/salience sound. Defect: Ardha-Ashtama Shani (Kantaka Shani — Saturn transiting 4th/8th from Moon) is classically DISTINCT from Sade Sati, yet collapsed to `signal_type_class=sade_sati`. Same type-collapse as anumukha/ashtama shani (cross-category pattern — flag at conductor merge).

## Findings
- summary: Ardha-Ashtama (Kantaka) Shani signals mislabeled `signal_type_class=sade_sati`; failure_class 2 (WRONG — type mislabel); severity LOW; evidence: cell5_type = `sade_sati=240`/`=250` for a Kantaka-Shani, not sade-sati, category. Suspected layer: L-writer (bo_laksana signal_type_class assignment).
