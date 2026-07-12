# Shard 9b — janma_shani_period

shard_id: 9b-janma_shani_period
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
5-cell recipe with `<CAT>=janma_shani_period`, plus chart_facts existence count.

## Verbatim results
chart_facts rows: Abhinandan=100, Abhisek=100 (both >0).
- cell1 (signals): Abhinandan=70, Abhisek=70
- cell2_salience: supporting=70 / supporting=70
- cell5_type: sade_sati=70 / sade_sati=70
- cell3_attr: 70/70, 70/70 (100% attributed)
- cell4_domains: career|health|relationship (both charts)

## Five-cell verdicts
1. Consumed? YES (70 signals each).
2. Salience: uniformly `supporting` — proportionate for granular period-window rows (the aggregate sade-sati significance is carried by the classification, not each window). OK.
3. Attribution: 100%, resolving. SOUND.
4. Domain: {career, health, relationship} — canonical sade-sati impact domains. Correct, multi-domain, not a default collapse.
5. Emergence: 70 signals, cleanly typed as `sade_sati`.

## design_correctness_verdict: SOUND

## Findings
(none — affirmative PASS)
- affirmative evidence: cell5 correctly classes all 70 signals as `sade_sati` (not defaulted to composite_state); cell4=career|health|relationship is the textbook sade-sati domain triad; cell3=70/70 fully attributed. Salience proportionate, attribution complete, domain sensible → SOUND. (Volume of 70 window rows is high but window granularity is legitimate.)
