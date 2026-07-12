# Shard 9b — house_strength_classification_rollup

shard_id: 9b-house_strength_classification_rollup
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
5-cell recipe with `<CAT>=house_strength_classification_rollup`, plus chart_facts existence count.

## Verbatim results
chart_facts rows: Abhinandan=60, Abhisek=60 (both >0).
- cell1 (signals): Abhinandan=15, Abhisek=15
- cell2_salience: supporting=15 / supporting=15
- cell5_type: composite_state=15 / composite_state=15
- cell3_attr: 15/15, 15/15 (100% attributed)
- cell4_domains: character|career (both charts, ONLY distinct value)

## Five-cell verdicts
1. Consumed? YES (15 signals each chart; note 60 facts → 15 signals, moderate narrowing).
2. Salience: uniformly `supporting` — proportionate. OK.
3. Attribution: 100%, resolving. SOUND.
4. Domain: uniform {character, career}. A rollup classifying each house strong/weak is domain-agnostic by construction — it should fan out to each classified house's domain, not default to {character,career}.
5. Emergence: 15 signals, one type_class.

## design_correctness_verdict: WEAK

## Findings
- summary: house_strength_classification_rollup (per-house strong/weak classification) is uniformly domain-mapped to default {character, career}, so the strong/weak verdict for the 2nd/4th/6th/7th/11th houses never reaches wealth/home/health/relationship domain readings.
  failure_class: 2 (WRONG; class-1 UNREACHABLE consequence)
  severity: MED
  suspected_layer: L-writer (bo_laksana domain-mapping)
  evidence: cell4_domains = "character|career" ONLY distinct value across 15+15 signals; chart_facts=60/60; cell3=15/15,15/15.
  dedupe: KP-4-family default-domain-mapping; third house-strength specimen alongside subscore/total.
