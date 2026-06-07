---
prompt_id: gemini.cgm_edge_proposals
version: "1.0"
status: SUPERSEDED
superseded_by: "035_DISCOVERY_LAYER/PROMPTS/gemini/cgm_edge_proposals_v1_1.md"
produced_by: Madhav_M2A_Exec_5
produced_on: 2026-04-26
phase: B.3.5
pass_type: PROMISCUOUS_CONNECTOR_PASS_1
l1_source: "FORENSIC_ASTROLOGICAL_DATA_v8_0.md"
gemini_response_target: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B3-5_batch1_raw.md"
registered_in: "06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json"
erratum:
  found_by: "Madhav_M2A_Exec_5 reconciler continuation (2026-04-26)"
  severity: "HIGH — PROMPT_P2_VIOLATION"
  description: >
    INPUT DATA section contains wrong planet positions — pre-FIX_SESSION compaction-era
    values rather than authoritative FORENSIC_v8_0 §2.1. Seven planets affected:
    Moon (Gemini→Aquarius), Venus (Aquarius→Sagittarius), Mercury (Shravana→Uttara Ashadha),
    Saturn (Chitra→Vishakha), Jupiter (Purva Ashadha 261.62°→Moola 249.81°),
    Rahu (Gemini→Taurus), Ketu (Sagittarius→Scorpio). KRK.C8 Atmakaraka/Amatya also wrong.
    Caused 15 of 27 Gemini proposals to fail P2. See reconciler report for full verdict table.
  reconciler_report: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-26_B3-5_batch1_reconciled.md"
  action_required: "Produce cgm_edge_proposals_v1_1.md with corrected INPUT DATA at Exec_6."
---

> ⚠️ **ERRATUM — PROMPT_P2_VIOLATION (HIGH):** This prompt file contains wrong planet positions
> in its INPUT DATA section. Do NOT use for future Gemini runs. Use `cgm_edge_proposals_v1_1.md`
> (to be produced at Exec_6) instead. See `erratum` block in frontmatter and the reconciler
> report at `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-26_B3-5_batch1_reconciled.md`.



# Gemini Edge Proposals — CGM v9.0 (Pass 1: Promiscuous Connector)

## Role

You are operating as a **Promiscuous Connector** in a two-pass graph enrichment protocol for the MARSYS-JIS Chart Graph Model (CGM). Your mandate in Pass 1 is to propose ALL potentially valid edges that extend beyond the deterministic set — including subtle, contested, or low-confidence connections. The Claude reconciler (Pass 2) will accept or reject your proposals using P1/P2/P5 invariant checks.

**Do not self-censor in Pass 1.** Propose any edge you can support with a verifiable L1 basis, even if confidence is LOW. The reconciler is the gate, not you.

---

## Task

Propose additional CGM edges for the MARSYS-JIS natal chart of **Abhisek Mohanty (b. 1984-02-05, 10:43 IST, Bhubaneswar, Lagna = Aries)**, beyond the deterministic LORDS / OCCUPIES / ASPECTS / OWNS set already encoded.

Focus categories:
1. **Chalit-shift implications** — planets whose Chalit house differs from Rashi house (Sun Rashi H10 vs Chalit H11; Mercury Rashi H10 vs Chalit H11; Jupiter Rashi H1 vs Chalit H2)
2. **Dispositor chains** — recursive sign-lord chains ending at self-disposited or exalted nodes
3. **Navamsha overlaps** — where D9 sign-lord relationship creates an additional functional bond
4. **Mutual receptions** — planets in each other's signs or exaltation signs
5. **Graha-drishti (7th-house special aspects and additional rashi aspects)** — including Saturn's 3rd/10th, Jupiter's 5th/9th, Mars's 4th/8th
6. **Nakshatra-lord connections** — where nakshatra lord is co-present or in strong positional relationship
7. **Yoga co-activation edges** — where two YOG nodes share a common activating planet and should be linked
8. **Karaka overlap edges** — where a Chara Karaka also functions as a classical Sthira Karaka for the same significator

---

## Input Data

### Existing Node List (key nodes — CGM_v9_0 has 234 nodes total)

```yaml
# PLN nodes (9 planets)
PLN.SUN: {sign: Capricorn, house_rashi: 10, house_chalit: 11, nakshatra: Shravana, pada: 4, abs_long: 291.96, lord_of: H10}
PLN.MOON: {sign: Gemini, house_rashi: 3, house_chalit: 3, nakshatra: Punarvasu, pada: 3, abs_long: 89.16, lord_of: H4}
PLN.MARS: {sign: Libra, house_rashi: 7, house_chalit: 7, nakshatra: Swati, pada: 3, abs_long: 196.74, lord_of: [H1, H8]}
PLN.MERCURY: {sign: Capricorn, house_rashi: 10, house_chalit: 11, nakshatra: Shravana, pada: 2, abs_long: 289.31, lord_of: [H3, H6]}
PLN.JUPITER: {sign: Sagittarius, house_rashi: 9, house_chalit: 9, nakshatra: Purva_Ashadha, pada: 4, abs_long: 261.62, lord_of: [H9, H12], note: "Retrograde; D9=Gemini"}
PLN.VENUS: {sign: Aquarius, house_rashi: 11, house_chalit: 11, nakshatra: Shatabhisha, pada: 3, abs_long: 318.63, lord_of: [H2, H7]}
PLN.SATURN: {sign: Libra, house_rashi: 7, house_chalit: 7, nakshatra: Chitra, pada: 3, abs_long: 191.17, lord_of: [H10, H11], dignity: exalted}
PLN.RAHU: {sign: Gemini, house_rashi: 3, house_chalit: 3, nakshatra: Ardra, pada: 4, abs_long: 81.13, note: "mean node; shadowy"}
PLN.KETU: {sign: Sagittarius, house_rashi: 9, house_chalit: 9, nakshatra: Purva_Ashadha, pada: 4, abs_long: 261.13, note: "mean node; shadowy"}

# Lagna
LAG.D1: {sign: Aries, lord: PLN.MARS, nakshatra: Ashwini, pada: 2}

# Key KRK nodes (8-karaka system, Chara)
KRK.C8.ATMA: {planet: PLN.SATURN, karaka: AtmaKaraka, degree_in_sign: 11.17, C8_rank: 1}
KRK.C8.AMATYA: {planet: PLN.SUN, karaka: AmatyaKaraka, degree_in_sign: 21.97, C8_rank: 2}
KRK.C8.BHRATRU: {planet: PLN.JUPITER, karaka: BhratruKaraka, degree_in_sign: 21.62, C8_rank: 3}
KRK.C8.MATRU: {planet: PLN.VENUS, karaka: MatruKaraka, degree_in_sign: 18.63, C8_rank: 4}
KRK.C8.PITRU: {planet: PLN.MARS, karaka: PitruKaraka_8K, degree_in_sign: 16.74, C8_rank: 5}
KRK.C8.PUTRA: {planet: PLN.RAHU, karaka: PutraKaraka_8K, degree_in_sign: 21.13, C8_rank: 6}
KRK.C8.GNATI: {planet: PLN.MERCURY, karaka: GnatiKaraka, degree_in_sign: 19.31, C8_rank: 7}
KRK.C8.DARA: {planet: PLN.MOON, karaka: DaraKaraka, degree_in_sign: 29.16, C8_rank: 8}
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

### L1 Basis Summary (key facts for edge derivation)

From `FORENSIC_ASTROLOGICAL_DATA_v8_0.md`:
- **Saturn–Mars**: both in Libra H7; Saturn exalted; Mars in own-sign for Scorpio (H8 = natural signif); mutual aspect Saturn–Mars within same sign (~5.57° separation)
- **Sun–Mercury**: both in Capricorn H10 (rashi); both shift to H11 in Chalit; within ~2.65° — Budha-Aditya yoga candidate
- **Moon–Rahu**: both in Gemini H3 (rashi and chalit); within ~8.03° — Rahu intensifies Moon themes
- **Jupiter–Ketu**: both in Sagittarius H9; Jupiter debilitated in Capricorn by D9 (Gemini navamsha sign = H3)
- **Mars**: lagna lord (Aries lagna) + 8th lord + occupies 7th; disposited by Venus (Venus rules Libra)
- **Saturn**: 10th lord + 11th lord + AtmaKaraka (C8 system) + exalted in Libra; disposited by Venus
- **Venus**: 2nd lord + 7th lord + occupies 11th (Chalit also H11); disposited by Saturn (Saturn rules Aquarius)
- **Saturn–Venus mutual reception**: Saturn in Venus's sign (Libra) + Venus in Saturn's sign (Aquarius) = classical Parivartana Yoga
- **Jupiter**: 9th lord + 12th lord, retrograde, in own sign (Sagittarius), Purva Ashadha; with Ketu
- **Sun**: AmatyaKaraka (C8), in Shravana nakshatra (lord = Moon), Capricorn (Saturn's sign — Sun in enemy's sign), H10 rashi but shifts to H11 Chalit
- **Shadbala ranks**: Saturn H5=rank1 (highest), Moon H5=rank4; Sun JH rank=2; Jupiter JH rank=3
- **Special lagnas (JH corrected)**: Hora Lagna=Aquarius, Ghati Lagna=Virgo, Bhava Lagna=Sagittarius, Drekkana Lagna=Sagittarius, Navamsha Lagna=Cancer, Saptamsha Lagna=Cancer
- **Upagrahas**: Gulika=Gemini H3 (near Moon+Rahu axis); Mandi=Cancer H4

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
6. **Parivartana (mutual reception) edges** are a priority — propose both directions (A→B and B→A) as `PARIVARTANA_WITH` type.
7. **Dispositor chain edges** — propose as `DISPOSITED_BY` type (e.g., `PLN.MARS` → `PLN.VENUS` because Mars occupies Libra, sign of Venus).
8. **Yoga activation edges** — propose as `ACTIVATES_YOGA` type (e.g., `PLN.MERCURY` → `YOG.BUDHA_ADITYA`).
9. **Nakshatra-lord edges** — propose as `NAKSHATRA_LORD_IS` type (e.g., `PLN.SUN` → `PLN.MOON` because Shravana's lord is Moon).
10. **Do not produce prose explanations** — the YAML block is the complete response.

---

*Prompt registered in: `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json` (entry: gemini.cgm_edge_proposals, version 1.0)*  
*Reconciler script: Claude reconciler per B.3.5 Task 4b. Invariant checks: P1 (L1_basis must resolve), P2 (no fabricated positions), P5 (SIG.MSR references must be valid).*  
*Two-pass protocol: This is Pass 1 (promiscuous). Pass 2 (reconciler) runs AFTER human pastes Gemini raw response to `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B3-5_batch1_raw.md`.*
