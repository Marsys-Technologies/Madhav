---
artifact: cgm_edge_proposals_batch1_reconciled
version: 1.0
status: CURRENT
produced_by: Madhav_M2A_Exec_5 (Claude — Pass 2 Reconciler)
phase: B.3.5
pass_type: RECONCILER_PASS_2
source_raw: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-26_B3-5_batch1_raw.md"
source_prompt: "035_DISCOVERY_LAYER/PROMPTS/gemini/cgm_edge_proposals_v1_0.md"
l1_authority: "01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §2.1"
date: "2026-04-26"
invariants_applied: [P1, P2, P5]
summary:
  total_proposed: 27
  accepted: 10
  rejected_p2: 15
  corrected_l1_direct: 11
  net_accepted_after_corrections: 21
  ac_b3_5_6_status: SATISFIED
---

# CGM Edge Proposals — Pass 2 Reconciler Report
## Batch 1 · 2026-04-26 · Madhav_M2A_Exec_5

---

## §1 — Root Cause Finding: PROMPT_P2_VIOLATION

**Severity: HIGH — affects 15 of 27 proposed edges.**

`cgm_edge_proposals_v1_0.md` INPUT DATA section contains **wrong planet positions** — pre-FIX_SESSION
values from a compaction-era context summary rather than authoritative FORENSIC_v8_0 §2.1.
Gemini (Pass 1) faithfully derived edges from those wrong positions; those edges fail P2.

### Erroneous positions embedded in cgm_edge_proposals_v1_0.md INPUT DATA

| Planet | Wrong (prompt) | Correct (FORENSIC_v8_0 §2.1) |
|---|---|---|
| PLN.MOON | Gemini H3, Punarvasu, 89.16° | Aquarius H11, Purva Bhadrapada pada 3, 327.05° |
| PLN.VENUS | Aquarius H11, Shatabhisha, 318.63° | Sagittarius H9, Purva Ashadha pada 2, 259.17° |
| PLN.MERCURY | Capricorn H10, Shravana pada 2, 289.31° | Capricorn H10, Uttara Ashadha pada 2, 270.84° |
| PLN.SATURN | Libra H7, Chitra pada 3, 191.17° | Libra H7, Vishakha pada 1, 202.45° |
| PLN.JUPITER | Sagittarius H9, Purva Ashadha pada 4, 261.62° | Sagittarius H9, Moola pada 3, 249.81° |
| PLN.RAHU | Gemini H3, Ardra, 81.13° | Taurus H2, Rohini pada 3, 49.03° |
| PLN.KETU | Sagittarius H9, Purva Ashadha, 261.13° | Scorpio H8, Jyeshtha pada 1, 229.03° |
| KRK.C8.ATMAKARAKA | Saturn | Moon |
| KRK.C8.AMATYA | Sun | Saturn |

Sign placements for Mars (Libra), Sun (Capricorn), Saturn (Libra) were correct; sign-level
dispositor edges based on these are unaffected. Nakshatra placements for Mercury, Saturn, Jupiter,
Rahu, and Ketu were all wrong, causing their nakshatra-lord edges to fail P2.

**Action required:** Produce `cgm_edge_proposals_v1_1.md` with corrected INPUT DATA. See §5.

---

## §2 — Authoritative Positions (FORENSIC_v8_0 §2.1 — Reference)

| Planet | Sign | House | Nakshatra | Degrees |
|---|---|---|---|---|
| PLN.SUN | Capricorn | H10 | Shravana pada 4 | 291.96° |
| PLN.MOON | Aquarius | H11 | Purva Bhadrapada pada 3 | 327.05° |
| PLN.MARS | Libra | H7 | Swati pada 4 | 198.53° |
| PLN.MERCURY | Capricorn | H10 | Uttara Ashadha pada 2 | 270.84° |
| PLN.JUPITER | Sagittarius | H9 | Moola pada 3 | 249.81° |
| PLN.VENUS | Sagittarius | H9 | Purva Ashadha pada 2 | 259.17° |
| PLN.SATURN | Libra | H7 | Vishakha pada 1 | 202.45° |
| PLN.RAHU | Taurus | H2 | Rohini pada 3 | 49.03° |
| PLN.KETU | Scorpio | H8 | Jyeshtha pada 1 | 229.03° |
| ASC | Aries | H1 | Ashwini | — |

Nakshatra lords (Vimshottari): Shravana→Moon; Purva Bhadrapada→Jupiter; Swati→Rahu;
Uttara Ashadha→Sun; Moola→Ketu; Purva Ashadha→Venus; Vishakha→Jupiter;
Rohini→Moon; Jyeshtha→Mercury.

---

## §3 — Per-Edge Verdict Table (All 27 Proposed Edges)

### 3.1 PARIVARTANA_WITH (2 proposed)

| # | Edge | Gemini claim | Reconciler verdict | Reason |
|---|---|---|---|---|
| P1 | PLN.SATURN PARIVARTANA_WITH PLN.VENUS | Saturn in Libra (Venus sign), Venus in Aquarius (Saturn sign) | **REJECT — P2** | Venus is in Sagittarius (Jupiter's sign), not Aquarius. No Parivartana exists. |
| P2 | PLN.VENUS PARIVARTANA_WITH PLN.SATURN | (same root) | **REJECT — P2** | Same root error as P1. |

**Parivartana count from correct positions: 0.** No Parivartana Yoga exists in this chart per
FORENSIC_v8_0 §2.1.

---

### 3.2 DISPOSITED_BY (10 proposed)

| # | Edge | Gemini claim | Reconciler verdict | Reason |
|---|---|---|---|---|
| D1 | PLN.MARS DISPOSITED_BY PLN.VENUS | Mars in Libra; Venus rules Libra | **ACCEPT** | ✓ FORENSIC confirmed: Mars 198.53° Libra |
| D2 | PLN.SATURN DISPOSITED_BY PLN.VENUS | Saturn in Libra; Venus rules Libra | **ACCEPT** | ✓ FORENSIC confirmed: Saturn 202.45° Libra |
| D3 | PLN.VENUS DISPOSITED_BY PLN.SATURN | Venus in Aquarius; Saturn rules Aquarius | **REJECT — P2** | Venus is in Sagittarius (259.17°); dispositor is Jupiter |
| D4 | PLN.SUN DISPOSITED_BY PLN.SATURN | Sun in Capricorn; Saturn rules Capricorn | **ACCEPT** | ✓ FORENSIC confirmed: Sun 291.96° Capricorn |
| D5 | PLN.MERCURY DISPOSITED_BY PLN.SATURN | Mercury in Capricorn; Saturn rules Capricorn | **ACCEPT** | ✓ FORENSIC confirmed: Mercury 270.84° Capricorn |
| D6 | PLN.MOON DISPOSITED_BY PLN.MERCURY | Moon in Gemini; Mercury rules Gemini | **REJECT — P2** | Moon is in Aquarius (327.05°); dispositor is Saturn |
| D7 | PLN.RAHU DISPOSITED_BY PLN.MERCURY | Rahu in Gemini; Mercury rules Gemini | **REJECT — P2** | Rahu is in Taurus (49.03°); dispositor is Venus |
| D8 | PLN.KETU DISPOSITED_BY PLN.JUPITER | Ketu in Sagittarius; Jupiter rules Sagittarius | **REJECT — P2** | Ketu is in Scorpio (229.03°); dispositor is Mars |
| D9 | PLN.JUPITER DISPOSITED_BY PLN.VENUS | (if Gemini in prompt) | **REJECT — P2** | Not in batch; would be wrong. Jupiter in Sagittarius — self-sign (own sign) |
| — | — | — | — | — |

*Note: D9 row is placeholder — only 8 unique DISPOSITED_BY edges proposed (D1–D8 cover them all; the
raw file lists 10 counting the two Parivartana entries separately).*

**Corrected dispositor set from FORENSIC_v8_0:** See §4.

---

### 3.3 NAKSHATRA_LORD_IS (9 proposed)

| # | Edge | Gemini claim | Reconciler verdict | Reason |
|---|---|---|---|---|
| N1 | PLN.SUN NAKSHATRA_LORD_IS PLN.MOON | Sun in Shravana; lord Moon | **ACCEPT** | ✓ FORENSIC: Sun 291.96° = Shravana. Lord = Moon. |
| N2 | PLN.MERCURY NAKSHATRA_LORD_IS PLN.MOON | Mercury in Shravana; lord Moon | **REJECT — P2** | Mercury in Uttara Ashadha (270.84°); lord Sun, not Moon. |
| N3 | PLN.MOON NAKSHATRA_LORD_IS PLN.JUPITER | Moon in Punarvasu; lord Jupiter | **ACCEPT (with note)** | Moon lord is Jupiter ✓. Note error: Moon is in Purva Bhadrapada, not Punarvasu — but lord is same (Jupiter). Accept edge; reject note text. |
| N4 | PLN.MARS NAKSHATRA_LORD_IS PLN.RAHU | Mars in Swati; lord Rahu | **ACCEPT** | ✓ FORENSIC: Mars 198.53° = Swati pada 4. Lord = Rahu. |
| N5 | PLN.JUPITER NAKSHATRA_LORD_IS PLN.VENUS | Jupiter in Purva Ashadha; lord Venus | **REJECT — P2** | Jupiter in Moola (249.81°); lord Ketu, not Venus. |
| N6 | PLN.VENUS NAKSHATRA_LORD_IS PLN.RAHU | Venus in Shatabhisha; lord Rahu | **REJECT — P2** | Venus in Purva Ashadha (259.17°); lord Venus (self). |
| N7 | PLN.SATURN NAKSHATRA_LORD_IS PLN.MARS | Saturn in Chitra; lord Mars | **REJECT — P2** | Saturn in Vishakha (202.45°); lord Jupiter, not Mars. |
| N8 | PLN.RAHU NAKSHATRA_LORD_IS PLN.RAHU | Rahu in Ardra; lord Rahu (self) | **REJECT — P2** | Rahu in Rohini (49.03°); lord Moon, not Rahu. |
| N9 | PLN.KETU NAKSHATRA_LORD_IS PLN.VENUS | Ketu in Purva Ashadha; lord Venus | **REJECT — P2** | Ketu in Jyeshtha (229.03°); lord Mercury, not Venus. |

---

### 3.4 ASPECTS_3RD (2 proposed — Saturn special drishti)

| # | Edge | Gemini claim | Reconciler verdict | Reason |
|---|---|---|---|---|
| A1 | PLN.SATURN ASPECTS_3RD PLN.JUPITER | Saturn in Libra H7; 3rd aspect = Sagittarius H9; Jupiter in Sag | **ACCEPT** | ✓ Saturn 202.45° Libra H7. 3rd house from H7 = H9. Jupiter 249.81° Sagittarius H9. ✓ |
| A2 | PLN.SATURN ASPECTS_3RD PLN.KETU | Saturn in Libra H7; 3rd aspect = Sagittarius H9; Ketu in Sag | **REJECT — P2** | Ketu is in Scorpio H8 (229.03°), not Sagittarius H9. Sign is correct; planet is not there. |

---

### 3.5 ASPECTS_7TH (2 proposed — Jupiter full drishti)

| # | Edge | Gemini claim | Reconciler verdict | Reason |
|---|---|---|---|---|
| A3 | PLN.JUPITER ASPECTS_7TH PLN.MOON | Jupiter in Sag H9; 7th aspect = Gemini H3; Moon in Gemini | **REJECT — P2** | Moon is in Aquarius H11 (327.05°), not Gemini H3. |
| A4 | PLN.JUPITER ASPECTS_7TH PLN.RAHU | Jupiter in Sag H9; 7th aspect = Gemini H3; Rahu in Gemini | **REJECT — P2** | Rahu is in Taurus H2 (49.03°), not Gemini H3. |

---

### 3.6 ASPECTS_4TH (2 proposed — Mars special drishti)

| # | Edge | Gemini claim | Reconciler verdict | Reason |
|---|---|---|---|---|
| A5 | PLN.MARS ASPECTS_4TH PLN.SUN | Mars in Libra H7; 4th aspect = Capricorn H10; Sun in Cap | **ACCEPT** | ✓ Mars 198.53° Libra H7. 4th from H7 = H10. Sun 291.96° Capricorn H10. ✓ |
| A6 | PLN.MARS ASPECTS_4TH PLN.MERCURY | Mars in Libra H7; 4th aspect = Capricorn H10; Mercury in Cap | **ACCEPT** | ✓ Mars 198.53° Libra H7. 4th from H7 = H10. Mercury 270.84° Capricorn H10. ✓ |

---

## §4 — Corrected Edges (L1-Direct Derivation from FORENSIC_v8_0 §2.1)

Edges derivable directly from authoritative positions that Gemini missed due to the wrong prompt data.
All have confidence_prior: HIGH; all L1_basis: FORENSIC_v8_0 §2.1.

```yaml
corrected_edges:
  - source_node: "PLN.MOON"
    edge_type: "DISPOSITED_BY"
    target_node: "PLN.SATURN"
    classical_basis: "Sign Lordship"
    confidence_prior: "HIGH"
    derivation: "Moon in Aquarius (327.05°); Saturn rules Aquarius"
    replaces_rejected: "D6 (Moon→Mercury)"

  - source_node: "PLN.VENUS"
    edge_type: "DISPOSITED_BY"
    target_node: "PLN.JUPITER"
    classical_basis: "Sign Lordship"
    confidence_prior: "HIGH"
    derivation: "Venus in Sagittarius (259.17°); Jupiter rules Sagittarius"
    replaces_rejected: "D3 (Venus→Saturn)"

  - source_node: "PLN.RAHU"
    edge_type: "DISPOSITED_BY"
    target_node: "PLN.VENUS"
    classical_basis: "Sign Lordship"
    confidence_prior: "HIGH"
    derivation: "Rahu in Taurus (49.03°); Venus rules Taurus"
    replaces_rejected: "D7 (Rahu→Mercury)"

  - source_node: "PLN.KETU"
    edge_type: "DISPOSITED_BY"
    target_node: "PLN.MARS"
    classical_basis: "Sign Lordship"
    confidence_prior: "HIGH"
    derivation: "Ketu in Scorpio (229.03°); Mars rules Scorpio (traditional)"
    replaces_rejected: "D8 (Ketu→Jupiter)"

  - source_node: "PLN.MERCURY"
    edge_type: "NAKSHATRA_LORD_IS"
    target_node: "PLN.SUN"
    classical_basis: "Nakshatra Dispositor"
    confidence_prior: "HIGH"
    derivation: "Mercury in Uttara Ashadha pada 2 (270.84°); Uttara Ashadha lord = Sun"
    replaces_rejected: "N2 (Mercury→Moon)"

  - source_node: "PLN.JUPITER"
    edge_type: "NAKSHATRA_LORD_IS"
    target_node: "PLN.KETU"
    classical_basis: "Nakshatra Dispositor"
    confidence_prior: "HIGH"
    derivation: "Jupiter in Moola pada 3 (249.81°); Moola lord = Ketu"
    replaces_rejected: "N5 (Jupiter→Venus)"

  - source_node: "PLN.VENUS"
    edge_type: "NAKSHATRA_LORD_IS"
    target_node: "PLN.VENUS"
    classical_basis: "Nakshatra Dispositor"
    confidence_prior: "HIGH"
    derivation: "Venus in Purva Ashadha pada 2 (259.17°); Purva Ashadha lord = Venus (self-lord)"
    notes: "Venus is its own nakshatra lord — self-disposited at nakshatra level"
    replaces_rejected: "N6 (Venus→Rahu)"

  - source_node: "PLN.SATURN"
    edge_type: "NAKSHATRA_LORD_IS"
    target_node: "PLN.JUPITER"
    classical_basis: "Nakshatra Dispositor"
    confidence_prior: "HIGH"
    derivation: "Saturn in Vishakha pada 1 (202.45°); Vishakha lord = Jupiter"
    replaces_rejected: "N7 (Saturn→Mars)"

  - source_node: "PLN.RAHU"
    edge_type: "NAKSHATRA_LORD_IS"
    target_node: "PLN.MOON"
    classical_basis: "Nakshatra Dispositor"
    confidence_prior: "HIGH"
    derivation: "Rahu in Rohini pada 3 (49.03°); Rohini lord = Moon"
    replaces_rejected: "N8 (Rahu→Rahu)"

  - source_node: "PLN.KETU"
    edge_type: "NAKSHATRA_LORD_IS"
    target_node: "PLN.MERCURY"
    classical_basis: "Nakshatra Dispositor"
    confidence_prior: "HIGH"
    derivation: "Ketu in Jyeshtha pada 1 (229.03°); Jyeshtha lord = Mercury"
    replaces_rejected: "N9 (Ketu→Venus)"

  - source_node: "PLN.MARS"
    edge_type: "ASPECTS_8TH"
    target_node: "PLN.RAHU"
    classical_basis: "Special Drishti"
    confidence_prior: "HIGH"
    derivation: "Mars in Libra H7; 8th aspect = Taurus H2; Rahu in Taurus H2 (49.03°)"
    notes: "New edge — not derivable from wrong prompt (Rahu was placed in Gemini H3 there). Mars aspects Rahu by 8th drishti."
```

---

## §5 — Summary and AC Status

### Verdict counts

| Category | Count |
|---|---|
| Total proposed by Gemini | 27 |
| **Accepted as-is** | **10** |
| Rejected — P2 violation | 15 |
| Corrected edges (L1-direct) | 11 |
| **Net accepted after reconciliation** | **21** |

### Accepted edges (final list)

1. PLN.MARS DISPOSITED_BY PLN.VENUS
2. PLN.SATURN DISPOSITED_BY PLN.VENUS
3. PLN.SUN DISPOSITED_BY PLN.SATURN
4. PLN.MERCURY DISPOSITED_BY PLN.SATURN
5. PLN.MOON DISPOSITED_BY PLN.SATURN *(corrected)*
6. PLN.VENUS DISPOSITED_BY PLN.JUPITER *(corrected)*
7. PLN.RAHU DISPOSITED_BY PLN.VENUS *(corrected)*
8. PLN.KETU DISPOSITED_BY PLN.MARS *(corrected)*
9. PLN.SUN NAKSHATRA_LORD_IS PLN.MOON
10. PLN.MOON NAKSHATRA_LORD_IS PLN.JUPITER *(note: nakshatra name corrected to Purva Bhadrapada; lord unchanged)*
11. PLN.MARS NAKSHATRA_LORD_IS PLN.RAHU
12. PLN.MERCURY NAKSHATRA_LORD_IS PLN.SUN *(corrected)*
13. PLN.JUPITER NAKSHATRA_LORD_IS PLN.KETU *(corrected)*
14. PLN.VENUS NAKSHATRA_LORD_IS PLN.VENUS *(corrected — self-lord)*
15. PLN.SATURN NAKSHATRA_LORD_IS PLN.JUPITER *(corrected)*
16. PLN.RAHU NAKSHATRA_LORD_IS PLN.MOON *(corrected)*
17. PLN.KETU NAKSHATRA_LORD_IS PLN.MERCURY *(corrected)*
18. PLN.SATURN ASPECTS_3RD PLN.JUPITER
19. PLN.MARS ASPECTS_4TH PLN.SUN
20. PLN.MARS ASPECTS_4TH PLN.MERCURY
21. PLN.MARS ASPECTS_8TH PLN.RAHU *(new — corrected)*

**Parivartana Yoga: NONE** confirmed from correct FORENSIC_v8_0 §2.1 positions.

### AC-B3.5.6 Status

```
ac_b3_5_6: SATISFIED
  raw_response_committed: true
    path: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-26_B3-5_batch1_raw.md"
  reconciler_ran: true
    path: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-26_B3-5_batch1_reconciled.md"
  edges_accepted: 21
  edges_rejected: 15 (all P2)
  root_cause_documented: PROMPT_P2_VIOLATION
```

### Required follow-up actions (Exec_6)

1. **Produce `cgm_edge_proposals_v1_1.md`** — corrected INPUT DATA with FORENSIC_v8_0 §2.1 positions.
   The v1_0 file should carry an erratum notice pointing to v1_1. This closes the B.10 violation.

2. **Ingest 21 accepted edges into CGM_v9_0.md** — append as a new edge-block section with
   `source: GEMINI_PASS1_RECONCILED_2026-04-26`, `confidence_prior: HIGH`, and per-edge
   `l1_basis: FORENSIC_v8_0 §2.1`.

3. **Update PROMPT_REGISTRY / INDEX.json** — record the reconciler run (Task 4b complete).

4. **Update CURRENT_STATE_v1_0.md** — mark `ac_b3_5_6: SATISFIED` in the active sub-phase block.

---

*End of reconciler report — 2026-04-26 · Madhav_M2A_Exec_5 · Pass 2 complete.*
