# Shard 9b-kp_cuspal_significators

shard_id: 9b-kp_cuspal_significators
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL: 9b 5-cell recipe with f.fact_category='kp_cuspal_significators'. chart_facts census: 600 rows combined.

## Verbatim results
- cell1: 482=140, 1c8=140 → CONSUMED
- cell2_salience: 482=supporting=140 ; 1c8=supporting=140
- cell3_attr: 482=140/140 ; 1c8=140/140 (100%)
- cell4_domains: 482=career|relationship|wealth|spirituality ; 1c8=career|relationship|wealth|spirituality
- cell5_type: 482=tradition_specific=140 ; 1c8=tradition_specific=140

## 5-cell verdicts
1. Consumed? YES (140/140).
2. Salience: 100% supporting — proportionate. PASS.
3. Attribution: 100%. PASS.
4. Domain: career|relationship|wealth|spirituality. AFFIRMATIVE — KP cuspal significators DO reach the wealth domain (contra KP-4 anchor's "domain-mapped to a default so they can never surface in wealth queries"). KP-4 harm REFUTED for this category. HOWEVER the array is a single fixed 4-domain blob identical across all 140 signals (12 cusps × grahas): a 7th-cusp significator and a 10th-cusp significator receive the same domain blob, so mapping is over-broad rather than per-cusp precise. Also omits health/progeny.
5. Emergence: 140 signals, single type class (tradition_specific).

## design_correctness_verdict: WEAK

## Findings
- summary: kp_cuspal_significators domain mapping is a fixed 4-domain blob (career|relationship|wealth|spirituality) identical for every cusp/graha combination — over-broad rather than cusp-specific; wealth IS reachable (KP-4 harm refuted here) but domain filtering gives no discrimination and drops health/progeny cusps.
  failure_class: 2 (WRONG — over-broad default domain mapping)
  severity: LOW
  suspected_layer: L-writer
  evidence: cell4 single distinct value "career|relationship|wealth|spirituality" for all 140 signals both charts; per-cusp KP significators should differentiate (2nd/11th→wealth, 7th→relationship, 10th→career, 6th→health).
  reproducible_call: SQL recipe, cell4_domains row.

## Anchor note (KP-4): REFUTED for kp_cuspal_significators — wealth domain present in mapping; these CAN surface under a wealth-domain query today. Affirmative evidence: cell4 contains "wealth".
