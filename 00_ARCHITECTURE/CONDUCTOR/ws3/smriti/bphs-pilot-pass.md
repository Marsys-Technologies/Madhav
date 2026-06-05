---
session_id: bphs-pilot
status: COMPLETE
completed_at: "2026-06-05"
merge_commit: "7a1c307c"
output_file: "00_ARCHITECTURE/CONDUCTOR/ws3/bphs_pilot_rules.yaml"
---

# WS-3 BPHS Pilot — Smriti (Session Memory)

## Session summary

This session extracted 500 BPHS rules in 5 batches of 100, following the method defined in
`WS3_EXTRACTION_METHOD_v1_0.md`. All 5 batches committed individually, then merged into
`bphs_pilot_rules.yaml`.

## Quality gate results

| Metric | Target | Actual |
|--------|--------|--------|
| Total rules | ≥ 500 | 500 |
| STUB rate | ≤ 10% | 4.8% (24/500) |
| Confidence ≥ 0.5 | ≥ 70% of non-stubs | 100% (476/476) |
| Quality bar met | true | true |

## Coverage by batch

| Batch | Rules | STUBs | Coverage area |
|-------|-------|-------|---------------|
| 01 | 100 | 5 | Graha natures, dignities, exaltation/debilitation, moolatrikona, friendships, shadbala, dig bala, planetary war, combustion, retrograde, functional benefics/malefics by lagna |
| 02 | 100 | 4 | Bhava significations (all 12 houses), planets in bhavas (selected), house lord placements, bhava strength principles, Parivartan yoga, karako bhavo nashto |
| 03 | 100 | 5 | Pancha Mahapurusha yogas, Gajakesari, Budha-Aditya, Dhana yogas, Raja yogas, Dharma-Karma, Arishta yogas, Viparita Raja, Sarpa, Kemadruma, Papakartari, Shubha Kartari, Neecha Bhanga Raja Yoga |
| 04 | 100 | 5 | Vimshottari dasha mahadasha results, antardasha combinations (key pairs), dasha of house lords, marriage/birth/career timing, Sade Sati, Ashtakavarga (principles, BAV construction, SAV thresholds, Shodhana), gochara transit rules, vedha |
| 05 | 100 | 5 | All 27 nakshatras (ruling planet, deity, nature, quality, body part), nakshatra classifications (Deva/Manushya/Rakshasa, guna types), planetary aspects (general + special), remedies (gemstones, mantras, dana, fasting, puja, Shanti ceremonies), muhurta (Abhijit, Rahu Kalam, tithi, vara, nakshatra selection principles, Ashtakuta compatibility) |

## Stub classification

All 24 stubs fall into two categories:
1. **Verse-ref APPROX** (18): specific verse location uncertain across BPHS editions; BPHS content confirmed but chapter-verse pinpoint needs verification
2. **Scope-deferred** (6): content exists but full enumeration exceeds pilot scope (e.g., all 81 antardasha combinations, full Dhana yoga list, complete BAV tables)

All stubs retain `text_excerpt` placeholders and `verse_ref: APPROX.N` markers for future resolution in the canon-extraction session.

## Key acharya-grade principles confirmed

1. Confidence rubric applied consistently: textual_strength × cross_text_corroboration with explicit rationale for every rule
2. Pramāṇa protocol satisfied: every non-stub rule has condition and assertion derivable from the text_excerpt
3. Scope vocabulary per §3.1 amendments used throughout: graha, bhava, yoga, compound_yoga, dasha, divisional, ashtakavarga, shadbala, nakshatra, transit, transit_yoga, muhurta, remedy
4. No fabricated verse numbers: approximate verse refs clearly flagged with APPROX
5. Stratified coverage: all five coverage areas per the plan addressed

## Next session

Gate A (acharya evaluation) can now proceed:
- Sample 50 rules stratified across topics + confidence tiers
- Write sample to: `00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_A/sample.md`
- Multi-model consensus re-extraction + comparison

## Commits

- Batch 01: `8edfd0e6`
- Batch 02: `54fde564`
- Batch 03: `b6db4c1f`
- Batch 04: `0e96f88d`
- Batch 05: `55ca93b3`
- Batch extensions: `c133140a`
- Merged pilot: `7a1c307c`
- Queue update: (this commit)
