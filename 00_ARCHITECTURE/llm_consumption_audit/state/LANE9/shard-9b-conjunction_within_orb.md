# shard-9b-conjunction_within_orb

**Shard id:** 9b-conjunction_within_orb
**Charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## SQL run
Standard 5-cell recipe on fact_category='conjunction_within_orb' + chart_facts baseline.

## Verbatim results
- chart_facts baseline: 10 (Abhisek) / 15 (Abhinandan)
- cell1 signals: Abhisek=10, Abhinandan=15  (full consumption)
- cell2 salience: both `supporting`
- cell3 attribution: 10/10, 15/15
- cell4 domains: both `career|relationship|spirituality`
- cell5 type: both `composite_state`

## Cell verdicts
1. Consumed: YES — 1:1
2. Salience: uniformly supporting (proportionate)
3. Attribution: 100%
4. Domains: multi-domain (3) — reasonable spread
5. Emergence: composite_state only

## design_correctness_verdict: SOUND
Full 1:1 consumption, full attribution, proportionate supporting salience, and a plausible multi-domain (career|relationship|spirituality) mapping rather than a single collapsed default. No defect pattern present.

## Findings
- (none) PASS. Affirmative evidence: cell1=10/15 = chart_facts baseline exactly; cell3=10/10, 15/15 fully attributed; cell4 3-domain non-default mapping.
