# Shard 9b — house_bhava_bala_subscore

shard_id: 9b-house_bhava_bala_subscore
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
5-cell recipe with `<CAT>=house_bhava_bala_subscore`, plus chart_facts existence count.

## Verbatim results
chart_facts rows: Abhinandan=180, Abhisek=180 (both >0).
- cell1 (signals): Abhinandan=66, Abhisek=65
- cell2_salience: supporting=66 / supporting=65
- cell5_type: composite_state=66 / composite_state=65
- cell3_attr: 66/66, 65/65 (100% attributed)
- cell4_domains: character|career (both charts, ONLY distinct value)

## Five-cell verdicts
1. Consumed? YES (65–66 signals; not all 180 facts emit).
2. Salience: uniformly `supporting` — proportionate. OK.
3. Attribution: 100% non-empty, resolving. SOUND.
4. Domain: uniform {character, career}. Bhava-bala subscores are computed for ALL 12 houses; 4th-house strength bears on home/mother, 7th on marriage/partnership, 2nd/11th on wealth, 6th on health — none of which is character or career. Collapsing every house's strength subscore to {character,career} makes house-strength evidence un-findable for every non-career domain query.
5. Emergence: ~66 signals, one type_class.

## design_correctness_verdict: WEAK

## Findings
- summary: house_bhava_bala_subscore (strength of all 12 bhavas) is uniformly domain-mapped to the default {character, career}, so per-house strength cannot surface in wealth/health/relationship/home domain readings despite being the canonical strength evidence for exactly those houses.
  failure_class: 2 (WRONG; class-1 UNREACHABLE consequence for domain-filtered queries)
  severity: MED
  suspected_layer: L-writer (bo_laksana domain-mapping)
  evidence: cell4_domains = "character|career" ONLY distinct value across 66+65 signals both charts; chart_facts=180/180; cell3=66/66,65/65.
  dedupe: KP-4-family default-domain-mapping pattern; house-strength specimen (arguably the clearest case — strength intrinsically spans all bhavas).
