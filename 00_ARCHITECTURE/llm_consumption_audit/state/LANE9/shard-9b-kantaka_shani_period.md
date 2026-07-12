# Shard 9b — kantaka_shani_period

shard_id: 9b-kantaka_shani_period
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
5-cell recipe with `<CAT>=kantaka_shani_period`, plus chart_facts existence count.

## Verbatim results
chart_facts rows: Abhinandan=260, Abhisek=200 (both >0).
- cell1 (signals): Abhinandan=200, Abhisek=155
- cell2_salience: supporting=200 / supporting=155
- cell5_type: sade_sati=200 / sade_sati=155
- cell3_attr: 200/200, 155/155 (100% attributed)
- cell4_domains: career|health|relationship (both charts)

## Five-cell verdicts
1. Consumed? YES (200/155 signals).
2. Salience: uniformly `supporting` — proportionate for granular window rows. OK.
3. Attribution: 100%, resolving. SOUND.
4. Domain: {career, health, relationship} — appropriate for kantaka/ashtama-shani affliction periods, multi-domain, not defaulted.
5. Emergence: 155–200 window signals, typed `sade_sati` (kantaka is a Saturn-transit affliction, grouped with the sade-sati family — defensible).

## design_correctness_verdict: SOUND

## Findings
(none — affirmative PASS)
- affirmative evidence: cell4=career|health|relationship correctly maps Saturn-affliction impact; cell5 correctly typed `sade_sati` not defaulted; cell3=200/200,155/155 fully attributed; salience proportionate. SOUND.
- observation (not a finding): 200 window rows at a single tier is high volume; window granularity is legitimate but borders the identical-score-wall pattern — noted for conductor cross-check, verdict remains SOUND on the five axes.
