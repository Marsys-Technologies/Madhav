# Shard 9b — karaka_house_lord_overlap_flag

shard_id: 9b-karaka_house_lord_overlap_flag
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
5-cell recipe with `<CAT>=karaka_house_lord_overlap_flag`, plus chart_facts existence count.

## Verbatim results
chart_facts rows: Abhinandan=60, Abhisek=60 (both >0).
- cell1 (signals): Abhinandan=10, Abhisek=10
- cell2_salience: supporting=10 / supporting=10
- cell5_type: karaka_alignment=10 / karaka_alignment=10
- cell3_attr: 10/10, 10/10 (100% attributed)
- cell4_domains: character|career (both charts, ONLY distinct value)

## Five-cell verdicts
1. Consumed? YES (10 signals each; 60 facts → 10 signals).
2. Salience: uniformly `supporting` — proportionate for a flag category. OK.
3. Attribution: 100%, resolving. SOUND.
4. Domain: uniform {character, career}. A karaka↔house-lord overlap flag is inherently about whichever house is involved — 7th-lord/DK overlap → relationship, 2nd/11th → wealth — yet collapsed to the {character,career} default.
5. Emergence: 10 signals, one type_class.

## design_correctness_verdict: WEAK

## Findings
- summary: karaka_house_lord_overlap_flag is uniformly domain-mapped to default {character, career} regardless of which house-lord overlaps which karaka, so a DK/7th-lord or dhana-karaka/2nd-lord overlap never surfaces under relationship or wealth domain queries.
  failure_class: 2 (WRONG; class-1 UNREACHABLE consequence for domain-filtered queries)
  severity: LOW
  suspected_layer: L-writer (bo_laksana domain-mapping)
  evidence: cell4_domains = "character|career" ONLY distinct value across 10+10 signals both charts; cell3=10/10.
  dedupe: KP-4-family default-domain-mapping pattern (low volume specimen).
