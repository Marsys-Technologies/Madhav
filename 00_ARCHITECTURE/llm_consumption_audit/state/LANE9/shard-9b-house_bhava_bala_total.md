# Shard 9b — house_bhava_bala_total

shard_id: 9b-house_bhava_bala_total
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
5-cell recipe with `<CAT>=house_bhava_bala_total`, plus chart_facts existence count.

## Verbatim results
chart_facts rows: Abhinandan=60, Abhisek=60 (both >0).
- cell1 (signals): Abhinandan=55, Abhisek=50
- cell2_salience: supporting=55 / supporting=50
- cell5_type: composite_state=55 / composite_state=50
- cell3_attr: 55/55, 50/50 (100% attributed)
- cell4_domains: character|career (both charts, ONLY distinct value)

## Five-cell verdicts
1. Consumed? YES.
2. Salience: uniformly `supporting` — proportionate. OK.
3. Attribution: 100%, resolving. SOUND.
4. Domain: uniform {character, career}. Total bhava-bala is the aggregate strength of each of the 12 houses — the single most decision-relevant number for judging any bhava's domain. Collapsing to {character,career} strips it from every other domain read.
5. Emergence: ~55 signals, one type_class.

## design_correctness_verdict: WEAK

## Findings
- summary: house_bhava_bala_total (aggregate strength per bhava) is uniformly domain-mapped to default {character, career}, un-findable in wealth/health/relationship/home domain queries where per-house total strength is the primary evidence.
  failure_class: 2 (WRONG; class-1 UNREACHABLE consequence)
  severity: MED
  suspected_layer: L-writer (bo_laksana domain-mapping)
  evidence: cell4_domains = "character|career" ONLY distinct value across 55+50 signals; chart_facts=60/60; cell3=55/55,50/50.
  dedupe: KP-4-family default-domain-mapping; house-strength specimen (with subscore + rollup siblings).
