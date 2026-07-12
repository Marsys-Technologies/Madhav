# Shard 9b — graha_yuddha_per_varga

shard_id: 9b-graha_yuddha_per_varga
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
5-cell recipe (Lane 9b proven recipe) with `<CAT>=graha_yuddha_per_varga`, plus chart_facts existence count.

## Verbatim results
chart_facts rows: Abhinandan=77, Abhisek=16 (both >0 → category exists in L1).
- cell1 (signals): Abhinandan=77, Abhisek=16
- cell2_salience: supporting=77 / supporting=16
- cell5_type: composite_state=77 / composite_state=16
- cell3_attr: 77/77, 16/16 (100% attributed)
- cell4_domains: character|career (both charts, ONLY distinct value)

## Five-cell verdicts
1. Consumed? YES (1:1 chart_fact→signal on both charts).
2. Salience: uniformly `supporting` — proportionate for a per-varga descriptive metric. OK.
3. Attribution: 93/93 non-empty and resolving. SOUND.
4. Domain: EVERY signal maps to exactly {character, career}. Graha-yuddha (planetary war) impairs the significations of whichever planet loses — bhava lordships spanning wealth/relationship/health — yet the surface is collapsed to a single default {character,career}.
5. Emergence: 1:1 replication per varga, all one type_class.

## design_correctness_verdict: WEAK

## Findings
- summary: graha_yuddha_per_varga signals are uniformly domain-mapped to the default {character, career} regardless of which graha is at war or what it rules, so a lost planetary war never surfaces under a wealth/health/relationship domain query.
  failure_class: 2 (WRONG; class-1 UNREACHABLE consequence for domain-filtered queries)
  severity: MED
  suspected_layer: L-writer (bo_laksana domain-mapping) / serving-query
  evidence: cell4_domains = "character|career" is the ONLY distinct domain array across all 77+16 signals both charts; cell1=77/16, cell3=77/77,16/16.
  dedupe: KP-4-family (default-domain-mapping) pattern; new specimen for graha_yuddha.
