# Shard 9b — fact_category: chart_cluster

Charts: 482012f1 (A), 1c826d5a (B)

## Exact SQL run
9b 5-cell recipe with WHERE f.fact_category='chart_cluster' AND ms.chart_id IN (A,B); plus cell0_cf.

## Verbatim results
- cell0_cf: A=1305, B=1305
- cell1: A=212, B=254
- cell2_salience: A=`chart_defining=6, major=146, supporting=60`, B=`background=66, chart_defining=14, major=137, supporting=37`
- cell5_type: A=`composite_state=212`, B=`composite_state=254`
- cell3_attr: A=`212/212`, B=`254/254`
- cell4_domains: A=`character|career`, B=`character|career`

## Five-cell verdicts
1. Consumed? YES (212 / 254).
2. Salience: **DIFFERENTIATED** — the only category in this shard whose signals span chart_defining / major / supporting / background. Proportionate tiering is actually working here.
3. Attribution: 100% (212/212, 254/254).
4. Domain: fixed `character|career` — mono-map (the one defect).
5. Emergence: 1305 cf → 212/254 signals (~16-19%), all `composite_state`.

## design_correctness_verdict: WEAK

## Findings
- **F1 (class 2 WRONG / domain mono-map, MED):** planetary clusters/stelliums carry the domain of the HOUSE they occupy (a 7th-house cluster → relationship, a 2nd/11th cluster → wealth), yet every one of the 212/254 signals is tagged `character|career` (cell4). Cluster-driven domain reads (e.g. a wealth stellium) cannot surface under their proper domain filter. This is the sole reason the category is graded WEAK rather than SOUND.
- **NOTE (affirmative / positive):** salience IS proportionate here — cell2 shows a real distribution (`chart_defining=6, major=146, supporting=60` for A; four tiers for B), and attribution is 100%. This category is the shard's counter-example proving MSR CAN differentiate tier when its writer chooses to; the flat-`supporting` collapse seen in the bhava_bala/combustion/center_of_gravity categories is therefore a design choice, not a platform limitation.

completion: DONE
