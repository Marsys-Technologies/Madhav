---
artifact: cgm_edge_proposals_batch2_reconciled
version: 1.0
status: CURRENT
produced_by: Madhav_M2A_Exec_5 (reconciler continuation — batch 2)
phase: B.3.5
pass_type: RECONCILER_PASS_2
source_raw: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/2026-04-26_B3-5_batch2_raw.md"
source_prompt: "035_DISCOVERY_LAYER/PROMPTS/gemini/cgm_edge_proposals_v1_1.md"
l1_authority: "01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §2.1"
date: "2026-04-26"
invariants_applied: [P1, P2, P5]
summary:
  total_proposed: 22
  accepted: 22
  rejected_p2: 0
  new_vs_batch1: 1
  net_unique_accepted_across_both_batches: 22
  prompt_p2_violations: 0
---

# CGM Edge Proposals — Pass 2 Reconciler Report
## Batch 2 · 2026-04-26 · Madhav_M2A_Exec_5

---

## §1 — Batch 2 Result Summary

**22/22 edges ACCEPTED. Zero P2 violations.**

The corrected prompt (`cgm_edge_proposals_v1_1.md`) produced a clean batch — no fabricated
positions, no wrong nakshatra lords, no ghost Parivartana. This confirms the PROMPT_P2_VIOLATION
in v1_0 was the sole root cause of batch 1's 15 rejections.

Batch 2 is also the **validation pass** for the 21 corrected edges from batch 1: all 21 were
re-proposed by Gemini from correct input data and passed reconciliation again. One additional
edge was found that batch 1 missed due to wrong positions: `PLN.SATURN ASPECTS_3RD PLN.VENUS`.

---

## §2 — Per-Edge Verdict (All 22 Proposed Edges)

### 2.1 DISPOSITED_BY (8 edges)

| # | Edge | Verdict | Derivation |
|---|---|---|---|
| D1 | PLN.SUN → PLN.SATURN | **ACCEPT** | Sun in Capricorn (291.96°); Saturn rules Capricorn |
| D2 | PLN.MOON → PLN.SATURN | **ACCEPT** | Moon in Aquarius (327.05°); Saturn rules Aquarius |
| D3 | PLN.MARS → PLN.VENUS | **ACCEPT** | Mars in Libra (198.53°); Venus rules Libra |
| D4 | PLN.MERCURY → PLN.SATURN | **ACCEPT** | Mercury in Capricorn (270.84°); Saturn rules Capricorn |
| D5 | PLN.VENUS → PLN.JUPITER | **ACCEPT** | Venus in Sagittarius (259.17°); Jupiter rules Sagittarius |
| D6 | PLN.SATURN → PLN.VENUS | **ACCEPT** | Saturn in Libra (202.45°); Venus rules Libra |
| D7 | PLN.RAHU → PLN.VENUS | **ACCEPT** | Rahu in Taurus (49.03°); Venus rules Taurus |
| D8 | PLN.KETU → PLN.MARS | **ACCEPT** | Ketu in Scorpio (229.03°); Mars rules Scorpio (traditional) |

All 8 match the batch 1 corrected set identically.

---

### 2.2 NAKSHATRA_LORD_IS (9 edges)

| # | Edge | Verdict | Derivation |
|---|---|---|---|
| N1 | PLN.SUN → PLN.MOON | **ACCEPT** | Sun in Shravana; Shravana lord = Moon |
| N2 | PLN.MOON → PLN.JUPITER | **ACCEPT** | Moon in Purva Bhadrapada; lord = Jupiter ✓ (note text also correct this time) |
| N3 | PLN.MARS → PLN.RAHU | **ACCEPT** | Mars in Swati; Swati lord = Rahu |
| N4 | PLN.MERCURY → PLN.SUN | **ACCEPT** | Mercury in Uttara Ashadha; lord = Sun |
| N5 | PLN.JUPITER → PLN.KETU | **ACCEPT** | Jupiter in Moola; Moola lord = Ketu |
| N6 | PLN.VENUS → PLN.VENUS | **ACCEPT** | Venus in Purva Ashadha; lord = Venus (self-lord) |
| N7 | PLN.SATURN → PLN.JUPITER | **ACCEPT** | Saturn in Vishakha; Vishakha lord = Jupiter |
| N8 | PLN.RAHU → PLN.MOON | **ACCEPT** | Rahu in Rohini; Rohini lord = Moon |
| N9 | PLN.KETU → PLN.MERCURY | **ACCEPT** | Ketu in Jyeshtha; Jyeshtha lord = Mercury |

All 9 match the batch 1 corrected set identically.

---

### 2.3 Special Drishti Aspects (5 edges)

| # | Edge | Verdict | Derivation |
|---|---|---|---|
| A1 | PLN.SATURN ASPECTS_3RD → PLN.JUPITER | **ACCEPT** | Saturn in Libra H7; 3rd aspect = H9 (Sagittarius); Jupiter in H9 ✓ |
| A2 | PLN.SATURN ASPECTS_3RD → PLN.VENUS | **ACCEPT — NEW** | Saturn in Libra H7; 3rd aspect = H9 (Sagittarius); Venus in H9 ✓ |
| A3 | PLN.MARS ASPECTS_4TH → PLN.SUN | **ACCEPT** | Mars in Libra H7; 4th aspect = H10 (Capricorn); Sun in H10 ✓ |
| A4 | PLN.MARS ASPECTS_4TH → PLN.MERCURY | **ACCEPT** | Mars in Libra H7; 4th aspect = H10 (Capricorn); Mercury in H10 ✓ |
| A5 | PLN.MARS ASPECTS_8TH → PLN.RAHU | **ACCEPT** | Mars in Libra H7; 8th aspect = H2 (Taurus); Rahu in H2 ✓ |

**A2 is the one genuinely new edge batch 2 surfaced.** It was invisible in batch 1 because the
wrong prompt placed Venus in Aquarius H11 rather than Sagittarius H9. With Venus correctly in H9,
Saturn's 3rd drishti from H7 now hits both Jupiter and Venus.

---

## §3 — Cumulative Edge Inventory (Both Batches Combined)

This is the complete, deduplicated, reconciled edge set from the two-pass protocol.
All 22 edges are ACCEPT; source = GEMINI_PASS1 + CLAUDE_RECONCILER_PASS2.

```yaml
reconciled_edges_final:

  # DISPOSITED_BY (8 edges)
  - {source: PLN.SUN,     edge: DISPOSITED_BY,    target: PLN.SATURN,  conf: HIGH, batch: 1+2}
  - {source: PLN.MOON,    edge: DISPOSITED_BY,    target: PLN.SATURN,  conf: HIGH, batch: 1+2}
  - {source: PLN.MARS,    edge: DISPOSITED_BY,    target: PLN.VENUS,   conf: HIGH, batch: 1+2}
  - {source: PLN.MERCURY, edge: DISPOSITED_BY,    target: PLN.SATURN,  conf: HIGH, batch: 1+2}
  - {source: PLN.VENUS,   edge: DISPOSITED_BY,    target: PLN.JUPITER, conf: HIGH, batch: 1+2}
  - {source: PLN.SATURN,  edge: DISPOSITED_BY,    target: PLN.VENUS,   conf: HIGH, batch: 1+2}
  - {source: PLN.RAHU,    edge: DISPOSITED_BY,    target: PLN.VENUS,   conf: HIGH, batch: 1+2}
  - {source: PLN.KETU,    edge: DISPOSITED_BY,    target: PLN.MARS,    conf: HIGH, batch: 1+2}

  # NAKSHATRA_LORD_IS (9 edges)
  - {source: PLN.SUN,     edge: NAKSHATRA_LORD_IS, target: PLN.MOON,    conf: HIGH, batch: 1+2}
  - {source: PLN.MOON,    edge: NAKSHATRA_LORD_IS, target: PLN.JUPITER, conf: HIGH, batch: 1+2, note: "Purva Bhadrapada → Jupiter"}
  - {source: PLN.MARS,    edge: NAKSHATRA_LORD_IS, target: PLN.RAHU,    conf: HIGH, batch: 1+2}
  - {source: PLN.MERCURY, edge: NAKSHATRA_LORD_IS, target: PLN.SUN,     conf: HIGH, batch: 1+2}
  - {source: PLN.JUPITER, edge: NAKSHATRA_LORD_IS, target: PLN.KETU,    conf: HIGH, batch: 1+2}
  - {source: PLN.VENUS,   edge: NAKSHATRA_LORD_IS, target: PLN.VENUS,   conf: HIGH, batch: 1+2, note: "self-lord"}
  - {source: PLN.SATURN,  edge: NAKSHATRA_LORD_IS, target: PLN.JUPITER, conf: HIGH, batch: 1+2}
  - {source: PLN.RAHU,    edge: NAKSHATRA_LORD_IS, target: PLN.MOON,    conf: HIGH, batch: 1+2}
  - {source: PLN.KETU,    edge: NAKSHATRA_LORD_IS, target: PLN.MERCURY, conf: HIGH, batch: 1+2}

  # SPECIAL DRISHTI (5 edges)
  - {source: PLN.SATURN, edge: ASPECTS_3RD, target: PLN.JUPITER, conf: HIGH, batch: 1+2}
  - {source: PLN.SATURN, edge: ASPECTS_3RD, target: PLN.VENUS,   conf: HIGH, batch: 2_only, note: "NEW — batch 1 missed; Venus was wrongly in Aquarius"}
  - {source: PLN.MARS,   edge: ASPECTS_4TH, target: PLN.SUN,     conf: HIGH, batch: 1+2}
  - {source: PLN.MARS,   edge: ASPECTS_4TH, target: PLN.MERCURY, conf: HIGH, batch: 1+2}
  - {source: PLN.MARS,   edge: ASPECTS_8TH, target: PLN.RAHU,    conf: HIGH, batch: 1+2}
```

---

## §4 — Protocol Closure

### Two-pass status

| Pass | Batch | Prompt version | Total proposed | Accepted | Rejected P2 |
|---|---|---|---|---|---|
| Pass 1 + Pass 2 | Batch 1 | v1_0 (VIOLATION) | 27 | 10 | 15 |
| Pass 1 + Pass 2 | Batch 2 | v1_1 (corrected) | 22 | 22 | 0 |
| **Combined unique** | — | — | **22** | **22** | **0** |

Batch 2 fully supersedes batch 1 as the canonical reconciled set. The 21 edges from batch 1's
corrected set are all present in batch 2 (confirmed independently), plus one additional edge
(SATURN ASPECTS_3RD VENUS) that batch 1 could not surface from wrong data.

### What is NOT in this edge set (correctly absent)

- **No PARIVARTANA_WITH** — Venus in Sagittarius (Jupiter's sign), not Saturn's sign; Saturn in
  Libra (Venus's sign) but Venus is NOT in Saturn's sign. No mutual reception exists. ✓ Correct.
- **No Jupiter 7th-drishti edges** — Jupiter 7th from H9 = H3 (Gemini); H3 is empty (no planets
  in Gemini). ✓ Correctly absent.
- **No Saturn 10th-drishti edges** — Saturn 10th from H7 = H4 (Cancer); H4 is empty. ✓ Correct.
- **No Jupiter 5th/9th-drishti edges** — H1 and H5 are empty. ✓ Correct.
- **No Chalit-shift edges proposed yet** — Sun H10→H11 and Moon H11→H12 Chalit shifts are
  deterministic and should be encoded as OCCUPIES_CHALIT (already in the existing edge set per
  CGM_v9_0 schema). No additional non-deterministic edges were flagged for these shifts.

### Recommendation for Exec_6

1. **Ingest all 22 edges into CGM_v9_0.md** — append as a new `gemini_enrichment_edges` block
   with `source: GEMINI_B3.5_TWO_PASS_FINAL`, `reconciled_by: Claude_Pass2`, `date: 2026-04-26`.
2. **Run cgm_node.py** after edge ingestion to verify chunk count increases from 234 nodes.
3. **Mark B.3.5 fully closed** — both batches reconciled, edge set canonical.

---

*End of batch 2 reconciler report — 2026-04-26 · Madhav_M2A_Exec_5 · Two-pass protocol COMPLETE.*
