# shard-9b-eclipse_proximity_natal

**Shard id:** 9b-eclipse_proximity_natal
**Charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## SQL run
Standard 5-cell recipe on fact_category='eclipse_proximity_natal' + chart_facts baseline.

## Verbatim results
- chart_facts baseline: 5 (Abhisek) / 5 (Abhinandan)
- cell1 signals: Abhisek=5, Abhinandan=5  (full 1:1)
- cell2 salience: both `supporting`
- cell3 attribution: 5/5, 5/5
- cell4 domains: both `character|spirituality`
- cell5 type: both `composite_state`

## Cell verdicts
1. Consumed: YES — full 1:1
2. Salience: uniformly supporting (proportionate)
3. Attribution: 100%
4. Domains: `character|spirituality` — defensible for eclipse proximity (Rahu/Ketu axis), though health/sudden-event relevance is arguably omitted
5. Emergence: composite_state only

## design_correctness_verdict: SOUND
Small, fully-consumed category (5/5 both charts), fully attributed, proportionate supporting salience, and a semantically plausible domain mapping. Minor note: eclipse proximity also carries health/longevity connotations not surfaced, but the mapping is not a collapsed default.

## Findings
- (none) PASS. Affirmative evidence: cell1=5/5 = chart_facts baseline; cell3=5/5 both; cell4=`character|spirituality` (non-default). Minor: health domain arguably missing — LOW, not logged as a defect.
