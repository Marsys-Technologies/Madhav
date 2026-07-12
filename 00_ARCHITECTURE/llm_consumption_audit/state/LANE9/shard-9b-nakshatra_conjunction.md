# Shard 9b-nakshatra_conjunction

shard_id: 9b-nakshatra_conjunction
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL: 9b 5-cell recipe with f.fact_category='nakshatra_conjunction'. chart_facts census: 7 rows combined (482=1, 1c8=6).

## Verbatim results
- cell1: 482=1, 1c8=6 → CONSUMED
- cell2_salience: 482=supporting=1 ; 1c8=supporting=6
- cell3_attr: 482=1/1 ; 1c8=6/6 (100%)
- cell4_domains: 482=character|relationship ; 1c8=character|relationship
- cell5_type: 482=composite_state=1 ; 1c8=composite_state=6

## 5-cell verdicts
1. Consumed? YES — emergence tracks the (small) fact count per chart (482 has 1 nakshatra_conjunction fact → 1 signal; 1c8 has 6 → 6). Healthy 1:1 pass-through.
2. Salience: 100% supporting — proportionate. PASS.
3. Attribution: 100%. PASS.
4. Domain: character|relationship — plausible for a nakshatra-conjunction relational measure.
5. Emergence: tracks fact count (1 / 6), single type class.

## design_correctness_verdict: SOUND

## Affirmative evidence
- 1:1 emergence proportional to chart_facts count per chart (contrast the per-varga inflation categories) — no funnel loss, no fabrication.
- 100% attributed (cell3 1/1, 6/6).
- Salience proportionate.
- Asymmetry (482=1 vs 1c8=6) is CORRECT — it mirrors the underlying chart_facts asymmetry (482=1, 1c8=6), i.e. faithful ingestion, not a defect.

## Findings: none of material severity.
