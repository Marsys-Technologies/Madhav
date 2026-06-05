# Smriti: canon-jaimini session — PASS

## Session identity
- session_id: canon-jaimini
- source: Jaimini Sutram (Sanjay Rath commentary edition)
- branch: feature/ws3-rule-base
- date: 2026-06-05
- status: PASS

## Extraction summary

| Batch | File | Rules | Stubs | Coverage |
|---|---|---|---|---|
| 1 | jaimini_canon_batch_01.yaml | 100 | 8 | Adhyaya 1 Padas 1-4: Karakas, Rashi Drishti, Argala, Karakamsha planetary results, Rashi KL types |
| 2 | jaimini_canon_batch_02.yaml | 100 | 9 | Adhyaya 2: Chara Dasha sequence, exception rules (Scorpio/Aquarius), dasha results by planet and house, antardasha |
| 3 | jaimini_canon_batch_03.yaml | 100 | 10 | Adhyaya 3 (Navamsha, deep Karakamsha) + Adhyaya 4 Padas 1-3 (longevity, special yogas, timing) |
| 4 | jaimini_canon_batch_04.yaml | 60 | 7 | Adhyaya 4 Pada 4: Arudha Padas (AL, A10, A11, UL), Upapada, advanced yogas, synthesis principles |
| **TOTAL** | — | **360** | **34** | Full Jaimini Sutram coverage per WS-3 spec |

## Quality metrics
- Total rules extracted: 360
- Rules stubbed: 34
- Stub rate: 9.4%
- Pramana pass rate (average across batches): 91.25%
- Rules below 0.30 confidence: 0 (all below-floor cases were stubbed)
- Lowest verified confidence: 0.55 (contested compound nodal + Mars KL reading)

## Gate A improvements applied
All three Gate A improvements from bphs-pilot review applied throughout:
- R1: Rahu/Ketu confidence × 0.85 — applied to 21 rules involving Rahu or Ketu
- R2: Contested sutras noted in caveats — applied throughout; 47 rules have explicit contestation notes
- R3: Lagna-conditional assertions note "results vary by lagna" — applied to all applicable rules

## Coverage assessment (per WS-3 spec requirements)

### Adhyaya 1 — Foundation (COVERED)
- ✓ Karakas: All 7/8 Chara Karakas defined (JAIMINI.1.1.5.1 through 1.1.23.1)
- ✓ 7-vs-8 karaka dispute noted throughout
- ✓ All 12 signs as KL types (JAIMINI.1.1.10.1 through 1.1.21.1)
- ✓ All 9 planets (Sun through Ketu) in Karakamsha results (JAIMINI.1.4.5.1 through 1.4.5.9)
- ✓ Argala rules: primary argala positions (2nd, 4th, 5th, 11th), virodha argala, papargala vs subhargala
- ✓ Jaimini rashi drishti for all 3 sign types (Chara, Sthira, Dwiswabhava)
- ✓ Special Lagnas: Hora Lagna, Ghati Lagna, Varnada Lagna

### Adhyaya 2 — Chara Dasha (COVERED)
- ✓ Dasha sequence: odd/even Lagna rule, direct/reverse sequence
- ✓ Duration formula: standard count to lord's sign
- ✓ Exception rules: Scorpio uses Ketu, Aquarius uses Rahu (contested; noted)
- ✓ Antardasha rules: direction, favorable/challenging positions
- ✓ Results by planet in dasha rashi: all 9 planets
- ✓ Results by house dasha: all 12 houses
- ✓ Timing events: marriage, career, children, health, death, spiritual peaks

### Adhyaya 3 — Navamsha and Karakamsha (COVERED)
- ✓ Navamsha Lagna interpretation
- ✓ Swamsha (AK in D9 Lagna)
- ✓ Vargottama in D1 and D9
- ✓ Karakamsha as D1 reference lagna
- ✓ Houses from KL: 2nd through 12th
- ✓ Divisional charts: D9 (primary), D10, D60, D3 notes
- ✓ Multiple KL planetary combinations (Sun+Jupiter, Moon+Venus, Mars+Ketu, etc.)

### Adhyaya 4 — Timing and Special Yogas (COVERED)
- ✓ Longevity: alpayu/madhyayu/purnayu framework
- ✓ Three assessment pairs (Lagna+HL, their lords, Saturn+AK)
- ✓ Rudra and Maheshwara death lords
- ✓ Badhaka rashi by Lagna type
- ✓ Rajayogas: AK+AmK, 5L+9L mutual aspect, AK+5L, AK+9L
- ✓ Bandhana yoga, Shrapit yoga, Guru Chandala in Jaimini context
- ✓ Arudha Pada system: AL, UL, A7, A10, A11, A2, A3
- ✓ Upapada Lagna and marriage indicators
- ✓ Paka Lagna, Niryaana Dvadashaamsha
- ✓ Trikuta synthesis principle

## Key contested areas documented

### Sutra-level contestations (highest priority for future verification)
1. **7 vs 8 Chara Karakas** (JAIMINI.1.1.5.1): Rath uses 8 (includes Pitrukaraka); K.N. Rao and Iranganti use 7. This fundamentally changes every karaka calculation. Confidence 0.85 with explicit caveat.

2. **Scorpio and Aquarius exceptions** (JAIMINI.2.1.3.1 and 2.1.3.2): Rahu as Aquarius lord and Ketu as Scorpio lord is the Rath/PJC lineage reading. Iranganti Rangacharya does NOT use these exceptions. Confidence reduced to 0.72 and 0.61 respectively.

3. **Chara Dasha duration formula** (JAIMINI.2.1.2.1): K.N. Rao uses longer arc in some cases; Rath uses shorter arc consistently. Results for any specific nativity may differ significantly between these two methods.

4. **Jaimini graha drishti** (JAIMINI.1.2.3.1): The separate planetary aspect list is Rath's system. Iranganti and K.N. Rao use only rashi drishti. Confidence reduced to 0.72 with explicit contestation.

5. **Rahu/Ketu as karakas** (multiple rules): All nodal rules carry × 0.85 per Gate A R1, plus explicit contestation notes. Many traditional commentators exclude Rahu and Ketu from the Chara Karaka scheme entirely.

## Stub analysis (34 stubs = 9.4%)
Stubs cluster in five areas:
- Exact mathematical formulas (longevity calculation, dasha duration edge cases): 6 stubs
- Navamsha degree-specific rules (Pushkara Navamsha, Pushkara Bhaga): 2 stubs
- Multi-exception conditional chains (retrograde exceptions, twin birth rules): 4 stubs
- Advanced timing refinements (D12 mortality, D7 in Jaimini): 4 stubs
- Cross-system integration rules (Brahma-Maheshwara pairs, systematic 12-house analyses): 8 stubs
- Minor remaining categories: 10 stubs

All stubs have minimum confidence 0.30, retain text_excerpt and verse_ref, and are marked stub: true with explicit stub_reason for future resolution.

## Commentary edition notes
This extraction used the Sanjay Rath commentary edition, which represents the PJC (Parampara Jyotish Chakra) lineage. Key characteristics of this edition:
- Includes 8-karaka scheme (Pitrukaraka added)
- Uses Ketu as Scorpio lord and Rahu as Aquarius lord
- Introduces Brahma, Rudra, Maheshwara classification
- Adds planetary aspects (Graha Drishti) alongside rashi aspects
- Integrates Arudha Pada system extensively (AL, UL, A2-A12)
- Emphasizes dual KL reading (D1 and D9 separately)

The Iranganti Rangacharya edition (different lineage) would produce a meaningfully different extraction, particularly for karakas, dasha calculations, and aspect rules. Cross-edition verification is recommended for any high-stakes interpretation.

## Files produced
- 00_ARCHITECTURE/CONDUCTOR/ws3/jaimini_canon_batch_01.yaml (100 rules, 8 stubs)
- 00_ARCHITECTURE/CONDUCTOR/ws3/jaimini_canon_batch_02.yaml (100 rules, 9 stubs)
- 00_ARCHITECTURE/CONDUCTOR/ws3/jaimini_canon_batch_03.yaml (100 rules, 10 stubs)
- 00_ARCHITECTURE/CONDUCTOR/ws3/jaimini_canon_batch_04.yaml (60 rules, 7 stubs)

## Commits
- Batch 1: 0d1ec456
- Batch 2: 6fe6d963
- Batch 3: b3f86df6
- Batch 4: ebdd1b3d

*End of smriti — canon-jaimini session, 2026-06-05*
