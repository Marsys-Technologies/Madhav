---
prompt_id: gemini.cgm_edge_proposals
version: "1.1"
status: CURRENT
supersedes: "035_DISCOVERY_LAYER/PROMPTS/gemini/cgm_edge_proposals_v1_0.md"
produced_by: Madhav_M2A_Exec_5 (reconciler continuation)
produced_on: 2026-04-26
phase: B.3.5
pass_type: PROMISCUOUS_CONNECTOR_PASS_1
l1_source: "FORENSIC_ASTROLOGICAL_DATA_v8_0.md §2.1"
gemini_response_target: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B3-5_batch2_raw.md"
registered_in: "06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json"
changelog:
  - v1.1 (2026-04-26): Corrected ALL INPUT DATA to match FORENSIC_v8_0 §2.1.
      v1.0 had PROMPT_P2_VIOLATION — wrong positions for Moon, Venus, Mercury, Saturn,
      Jupiter, Rahu, Ketu (7 of 9 planets), and wrong KRK.C8 assignments.
      Also corrected Chalit houses, L1 Basis Summary, and focus-category Chalit notes.
      No prompt logic changed — only data corrected.
---

# Gemini Edge Proposals — CGM v9.0 (Pass 1: Promiscuous Connector)

## Role

You are operating as a **Promiscuous Connector** in a two-pass graph enrichment protocol for the MARSYS-JIS Chart Graph Model (CGM). Your mandate in Pass 1 is to propose ALL potentially valid edges that extend beyond the deterministic set — including subtle, contested, or low-confidence connections. The Claude reconciler (Pass 2) will accept or reject your proposals using P1/P2/P5 invariant checks.

**Do not self-censor in Pass 1.** Propose any edge you can support with a verifiable L1 basis, even if confidence is LOW. The reconciler is the gate, not you.

---

## Task

Propose additional CGM edges for the MARSYS-JIS natal chart of **Abhisek Mohanty (b. 1984-02-05, 10:43 IST, Bhubaneswar, Lagna = Aries)**, beyond the deterministic LORDS / OCCUPIES / ASPECTS / OWNS set already encoded.

Focus categories:
1. **Chalit-shift implications** — planets whose Chalit house differs from Rashi house: **Sun Rashi H10 → Chalit H11; Moon Rashi H11 → Chalit H12** (only two planets shift in this chart)
2. **Dispositor chains** — recursive sign-lord chains ending at self-disposited or exalted nodes
3. **Navamsha overlaps** — where D9 sign-lord relationship creates an additional functional bond
4. **Mutual receptions / Parivartana** — planets in each other's signs or exaltation signs (evaluate carefully against actual positions)
5. **Graha-drishti** — Saturn's 3rd/10th, Jupiter's 5th/9th, Mars's 4th/8th special aspects
6. **Nakshatra-lord connections** — where nakshatra lord is co-present or in strong positional relationship
7. **Yoga co-activation edges** — where two YOG nodes share a common activating planet and should be linked
8. **Karaka overlap edges** — where a Chara Karaka also functions as a classical Sthira Karaka for the same significator

---

## Input Data

### Existing Node List (key nodes — CGM_v9_0 has 234 nodes total)

```yaml
# PLN nodes (9 planets) — AUTHORITATIVE from FORENSIC_ASTROLOGICAL_DATA_v8_0.md §2.1
PLN.SUN:     {sign: Capricorn,  house_rashi: 10, house_chalit: 11, nakshatra: Shravana,         pada: 4, abs_long: 291.96, degree_in_sign: 21.96, lord_of: [H5]}
PLN.MOON:    {sign: Aquarius,   house_rashi: 11, house_chalit: 12, nakshatra: PurvaBhadrapada,  pada: 3, abs_long: 327.05, degree_in_sign: 27.05, lord_of: [H4]}
PLN.MARS:    {sign: Libra,      house_rashi: 7,  house_chalit: 7,  nakshatra: Swati,            pada: 4, abs_long: 198.53, degree_in_sign: 18.53, lord_of: [H1, H8]}
PLN.MERCURY: {sign: Capricorn,  house_rashi: 10, house_chalit: 10, nakshatra: UttaraAshadha,   pada: 2, abs_long: 270.84, degree_in_sign: 0.84,  lord_of: [H3, H6]}
PLN.JUPITER: {sign: Sagittarius,house_rashi: 9,  house_chalit: 9,  nakshatra: Moola,           pada: 3, abs_long: 249.81, degree_in_sign: 9.81,  lord_of: [H9, H12], note: "Retrograde; D9=Gemini; adj_degree_for_C8=20.19"}
PLN.VENUS:   {sign: Sagittarius,house_rashi: 9,  house_chalit: 9,  nakshatra: PurvaAshadha,   pada: 2, abs_long: 259.17, degree_in_sign: 19.17, lord_of: [H2, H7]}
PLN.SATURN:  {sign: Libra,      house_rashi: 7,  house_chalit: 7,  nakshatra: Vishakha,        pada: 1, abs_long: 202.45, degree_in_sign: 22.45, lord_of: [H10, H11], dignity: exalted}
PLN.RAHU:    {sign: Taurus,     house_rashi: 2,  house_chalit: 2,  nakshatra: Rohini,          pada: 3, abs_long: 49.03,  degree_in_sign: 19.03, note: "mean node; always retrograde; shadowy"}
PLN.KETU:    {sign: Scorpio,    house_rashi: 8,  house_chalit: 8,  nakshatra: Jyeshtha,        pada: 1, abs_long: 229.03, degree_in_sign: 19.03, note: "mean node; always retrograde; shadowy"}

# Lagna
LAG.D1: {sign: Aries, lord: PLN.MARS, nakshatra: Ashwini, pada: 2}

# Key KRK nodes (8-karaka Chara system, sorted by degree_in_sign descending; retrograde adjusted)
KRK.C8.ATMA:    {planet: PLN.MOON,    karaka: AtmaKaraka,      degree_in_sign: 27.05, C8_rank: 1}
KRK.C8.AMATYA:  {planet: PLN.SATURN,  karaka: AmatyaKaraka,    degree_in_sign: 22.45, C8_rank: 2}
KRK.C8.BHRATRU: {planet: PLN.SUN,     karaka: BhratruKaraka,   degree_in_sign: 21.96, C8_rank: 3}
KRK.C8.MATRU:   {planet: PLN.JUPITER, karaka: MatruKaraka,     degree_in_sign: 20.19, C8_rank: 4, note: "retrograde-adjusted"}
KRK.C8.PITRU:   {planet: PLN.VENUS,   karaka: PitruKaraka_8K,  degree_in_sign: 19.17, C8_rank: 5}
KRK.C8.PUTRA:   {planet: PLN.RAHU,    karaka: PutraKaraka_8K,  degree_in_sign: 19.03, C8_rank: 6}
KRK.C8.GNATI:   {planet: PLN.MARS,    karaka: GnatiKaraka,     degree_in_sign: 18.53, C8_rank: 7}
KRK.C8.DARA:    {planet: PLN.MERCURY, karaka: DaraKaraka,      degree_in_sign: 0.84,  C8_rank: 8}
```

### Existing Edge Types (deterministic set already in CGM_v9_0)

```yaml
existing_edge_types:
  - OCCUPIES        # planet → house (rashi placement)
  - OCCUPIES_CHALIT # planet → house (chalit placement, where different)
  - RULES           # planet → house (sign lordship)
  - ASPECTS         # planet → house (7th-house full aspect)
  - EXALTED_IN      # planet → sign (dignity marker)
  - DEBILITATED_IN  # planet → sign (dignity marker)
  - IN_SIGN         # planet → sign (placement)
  - IN_NAKSHATRA    # planet → nakshatra
  - HAS_ATMAKARAKA  # chart → KRK.C8.ATMA
  - FUNCTIONS_AS    # KRK node → planet
  - CO_OCCUPIES     # planet → planet (co-tenancy in same house)
  - CONJUNCT        # planet → planet (within 10° orb in same sign)
```

### L1 Basis Summary (key facts for edge derivation — corrected per FORENSIC_v8_0 §2.1)

From `FORENSIC_ASTROLOGICAL_DATA_v8_0.md`:
- **Saturn–Mars co-occupancy**: both in Libra H7; Saturn exalted (22.45°), Mars at 18.53°; ~3.92° separation — within tight orb; Saturn aspects Mars by 7th drishti (same sign = 0° = mutual)
- **Jupiter–Venus co-occupancy**: both in Sagittarius H9; Jupiter at 9.81° (retro), Venus at 19.17°; ~9.36° separation — within 10° orb; Jupiter in own sign, Venus in mutual friend's sign
- **Sun–Mercury in Capricorn H10**: Sun 21.96°, Mercury 0.84°; ~21.12° separation — outside conjunction orb; Budha-Aditya yoga requires proximity (flag as LOW confidence only)
- **Moon in Aquarius H11**: disposited by Saturn (Saturn rules Aquarius); Moon shifts to Chalit H12
- **Rahu in Taurus H2**: disposited by Venus (Venus rules Taurus); Ketu in Scorpio H8, disposited by Mars (Mars rules Scorpio)
- **Venus in Sagittarius**: disposited by Jupiter (Jupiter rules Sagittarius); **NO Parivartana Yoga** in this chart — Venus is NOT in Saturn's sign
- **Mars**: lagna lord (H1) + 8th lord + in H7; disposited by Venus (Venus rules Libra)
- **Saturn**: 10th lord + 11th lord + AtmaKaraka (C8) + exalted; disposited by Venus (Venus rules Libra)
- **Moon = AtmaKaraka** (highest degree in sign 27.05°); **Saturn = AmatyaKaraka** (second 22.45°)
- **Sun shifts to Chalit H11** (from Rashi H10); **Moon shifts to Chalit H12** (from Rashi H11) — only two Chalit shifts
- **Special lagnas (JH)**: Hora Lagna=Aquarius, Ghati Lagna=Virgo, Bhava Lagna=Sagittarius, Drekkana Lagna=Sagittarius, Navamsha Lagna=Cancer, Saptamsha Lagna=Cancer
- **Upagrahas**: Gulika=Gemini H3; Mandi=Cancer H4
- **Saturn's special drishti**: 3rd from Libra H7 = Sagittarius H9 (Jupiter + Venus there); 10th from Libra H7 = Cancer H4 (empty)
- **Mars's special drishti**: 4th from Libra H7 = Capricorn H10 (Sun + Mercury there); 8th from Libra H7 = Taurus H2 (Rahu there)
- **Jupiter's special drishti**: 5th from Sagittarius H9 = Aries H1 (Lagna, empty); 7th from Sagittarius H9 = Gemini H3 (empty); 9th from Sagittarius H9 = Leo H5 (empty)

---

## Output Schema (STRICT YAML — no prose, no markdown headers within)

Respond with ONLY a YAML block in the following structure. Do not wrap in markdown fences. Do not add commentary outside the YAML block.

```yaml
proposed_edges:
  - source_node: "<node_id from input list>"
    edge_type: "<edge_type_name>"
    target_node: "<node_id>"
    L1_basis: "<specific section ID from FORENSIC_v8_0, e.g., '§2.1 Planet Positions' or '§5.1 Vimshottari Dasha'>"
    classical_basis: "<classical rule name if applicable, else NONE>"
    confidence_prior: "LOW|MED|HIGH"
    notes: "<optional; use [EXTERNAL_COMPUTATION_REQUIRED] if position cannot be confirmed from L1 v8.0; use [EXTERNAL_CORPUS_REQUIRED] if classical rule requires text outside current corpus>"
```

---

## Constraints

1. **L1 v8.0 only** — every `L1_basis` must cite a specific section of `FORENSIC_ASTROLOGICAL_DATA_v8_0.md`. Do not cite v6.0, v7.0, or any other source.
2. **No invented positions** — if you are uncertain whether a position is confirmed in v8.0, write `[EXTERNAL_COMPUTATION_REQUIRED]` in the `notes` field, not in the `L1_basis` field.
3. **If a classical rule requires a text (Brihat Parashara Hora Shastra, Jaimini sutras, etc.) not in the current corpus**, write `[EXTERNAL_CORPUS_REQUIRED]` in `classical_basis`.
4. **All node IDs must match the input list exactly** (e.g., `PLN.SATURN`, `PLN.VENUS`, `KRK.C8.ATMA`). Do not invent new node IDs.
5. **Propose edges the reconciler will consider** — bias toward HIGH and MED confidence. LOW confidence edges should still be proposed if they have L1 support; the reconciler handles rejection.
6. **Parivartana (mutual reception) edges** — verify that BOTH planets are actually in each other's signs before proposing. Use the Input Data above, not assumed positions.
7. **Dispositor chain edges** — propose as `DISPOSITED_BY` type (e.g., `PLN.MARS` → `PLN.VENUS` because Mars occupies Libra, sign of Venus).
8. **Yoga activation edges** — propose as `ACTIVATES_YOGA` type (e.g., `PLN.MERCURY` → `YOG.BUDHA_ADITYA`).
9. **Nakshatra-lord edges** — propose as `NAKSHATRA_LORD_IS` type (e.g., `PLN.SUN` → `PLN.MOON` because Shravana's lord is Moon).
10. **Do not produce prose explanations** — the YAML block is the complete response.

---

*Prompt registered in: `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json` (entry: gemini.cgm_edge_proposals, version 1.1)*
*Supersedes: `cgm_edge_proposals_v1_0.md` (PROMPT_P2_VIOLATION — wrong planet positions in INPUT DATA)*
*Reconciler script: Claude reconciler per B.3.5 Task 4b. Invariant checks: P1 (L1_basis must resolve), P2 (no fabricated positions), P5 (SIG.MSR references must be valid).*
*Two-pass protocol: This is Pass 1 (promiscuous). Pass 2 (reconciler) runs AFTER human pastes Gemini raw response to `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B3-5_batch2_raw.md`.*
