---
title: Red-Team Review Packet — Native Action Required (IS.8(b))
generated: "2026-05-30"
phase: "Phase 6 — Red-Team Auto-Checks + Packet"
chart_id: "362f9f17-95a5-490b-a5a7-027d3e0efda0"
build_workstream: "MARSYS-JIS Multi-Ayanamsha Deterministic Build"
status: AWAITING_NATIVE_REVIEW
---

# Red-Team Review Packet — Native Action Required (IS.8(b))

Generated: 2026-05-30 (operator queue run — Phase 6)
Chart ID: 362f9f17-95a5-490b-a5a7-027d3e0efda0
Native: Abhisek Mohanty (1984-02-05, 10:43 IST, Bhubaneswar, Odisha)

---

## Auto-Checks Summary

| Check | Result | Status |
|---|---|---|
| L1 spot check (sun/moon/navamsa) | See 16_red_team_l1_spot.txt | DATA PRESENT — needs human cross-check |
| Narration violations | 0 (target: 0) | PASS |
| Two-pass verification distribution | See 18_two_pass_dist.txt | NOTE: all 18,770 rows = "single" — no dual-pass rows present |
| Cross-ayanamsha coverage | See 19_ayanamsha_coverage.txt | NOTE: 18,768 rows ayanamsha_id='all'; 2 rows lahiri |
| Red-team artifact | 15_red_team_artifact.md | COPIED |

### Auto-Check Notes

**L1 Spot Check findings (from 16_red_team_l1_spot.txt):**
- MOON in D1: sign = Aries (sign_id = 1), ayanamsha_id = 'all'
- SUN in D1: sign = Aquarius (sign_id = 11), ayanamsha_id = 'all'
- LAGNA: No LAGNA/ASCENDANT rows found in chart_facts for this chart_id. Navamsa (D9) lagna also absent.
- All varga rows carry ayanamsha_id='all' (not ayanamsha-specific).
- verification_pass_status = 'single' for all varga rows.

**Two-pass verification note:** All 18,770 rows have status='single'. The multi-ayanamsha build was intended to produce dual-pass ('double') or 'triple' verification rows. Zero dual-pass rows is a potential gap — human review should confirm whether the multi-ayanamsha writer backfill (A5-S12 commit 8571787a) was applied to this chart_id.

**Cross-ayanamsha coverage note:** Only 2 lahiri-tagged rows (dasha_period). The multi-ayanamsha build should produce rows across: lahiri, kp, raman, true_citra, yukteshwar. Only lahiri and 'all' present. Human review should confirm whether per-ayanamsha streaming assets (A3, A5–A7, temporal spine) were successfully written for this chart_id.

---

## Human Gate — 9 Items (IS.8(b)) — All MUST be reviewed by native

### 1. L1 Fact Cross-Check (FORENSIC_ASTROLOGICAL_DATA_v8_0.md)

Verify the following auto-extracted values against `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`:

| Planet/Point | DB Value | FORENSIC Expected | Match? |
|---|---|---|---|
| MOON sign (D1, Lahiri) | Aries | [native to verify] | [ ] |
| SUN sign (D1, Lahiri) | Aquarius | [native to verify] | [ ] |
| LAGNA sign (D1) | NOT FOUND in chart_facts | [native to verify — gap?] | [ ] |
| Navamsa-lagna (D9) | NOT FOUND in chart_facts | [native to verify — gap?] | [ ] |

**Action:** Confirm Moon=Aries and Sun=Aquarius against FORENSIC v8.0 §L1. Flag if LAGNA absence is a known schema decision or a data gap requiring backfill.

### 2. MSR Signal Provenance

Sample 10 MSR signals from `chart_facts` (fact_category='msr_signal') and verify each has explicit FORENSIC/LEL citation.

Only 2 msr_signal rows are present for this chart_id. Both carry ayanamsha_id='all'. Native should:
- Check `citation_ref` and `citation_human` columns on both rows.
- Confirm they reference FORENSIC v8.0 fact_ids or LEL events — not generic "classical" attribution.
- Confirm whether 2 rows is expected scope for this chart build or a gap.

### 3. CDLM Linkage Formulas

162 CDLM rows present (fact_category='cdlm', ayanamsha_id='all'). Sample 5:
- Verify `provenance` JSONB contains explicit `source_fact_ids` from FORENSIC or LEL.
- Verify linkage formula version matches current `CDLM_v1_1.md` schema.
- Confirm no cross-tradition contamination (e.g. Jaimini chara dasha lords substituted for Parashari lords).

### 4. CGM Motif Library Match

18 cgm_node rows present (fact_category='cgm_node', ayanamsha_id='all'). Sample 5:
- Verify each `value_text` motif matches a canonical entry in `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md`.
- Verify no motif is fabricated or paraphrased (B.10 rule: no invented classical content).
- Verify `citation_ref` on each row.

### 5. RM Prescription Sources

18 rm_remedy rows present (fact_category='rm_remedy', ayanamsha_id='all'). Sample 3:
- Verify classical source text cited (e.g. BPHS chapter + verse, or KP text reference).
- Verify counter-indication or dosage note present (RM schema requirement).
- Verify no generic "consult an astrologer" catch-all language.

### 6. Per-Tradition Internal Consistency

Dasha data spans multiple systems: vimshottari (14,760 rows), ashtottari (1,168), mudda (2,106), kalachakra (24), yogini (144), jaimini_chara (36), naisargika (112).

Native should verify:
- Vimshottari dasha sequence for native birth date is internally consistent (no impossible sub-period dates).
- Jaimini chara dasha lords are derived from chara karakas, not Parashari planet periods.
- Kalachakra navamsa-based derivation does not use tropical zodiac positions.

### 7. Cross-Ayanamsha Stability Ranges

OBSERVATION: The multi-ayanamsha build produced only 2 per-ayanamsha rows (lahiri dasha_period). Expected multi-ayanamsha coverage (lahiri/kp/raman/true_citra/yukteshwar) for structural assets (A3-A13) appears absent for this chart_id.

Native should confirm:
- Is the per-ayanamsha streaming build for chart 362f9f17 complete? (Check `build_orchestrator` state.json for this chart's per-chart job status.)
- If cross_ayanamsha_divergence_arcsec values were backfilled (commit 8571787a — A5-S12 `_finalize_rows`), are they present in the varga rows?
- Current status: `ucn_digest` shows "0 of 5 ayanamshas agree" for system_convergence — native should verify this is a data value (not schema error).

### 8. META-alpha LATTICE (Active Patterns 2026-05-30)

The multi-ayanamsha build includes META-alpha through META-epsilon synthesis layers.

Native should:
- Query `chart_facts` for `fact_category` rows matching 'meta_lattice', 'meta_catalog', 'meta_divergence', 'meta_negative_space', 'meta_derivation_trail' — verify presence.
- Spot-check the LATTICE snapshot for current date 2026-05-30. Verify active patterns reflect current planetary positions (Sun in Taurus, Saturn retrograde in Pisces area as of late May 2026).
- If META rows are absent, flag as gap for native's build-job verification.

### 9. META-epsilon DERIVATION_TRAIL

Walk back one MSR signal through its derivation trail:
- Start: a msr_signal row for this chart_id.
- Step 1: `provenance` JSONB — find `source_fact_ids` list.
- Step 2: For each source_fact_id, verify corresponding row exists in `chart_facts` with that `fact_id`.
- Step 3: For L1 terminal facts, verify `citation_ref` traces to a FORENSIC v8.0 fact_id.
- Confirm no "orphaned" derivation step (a `source_fact_id` that resolves to nothing in the DB).

---

## Gaps Identified by Auto-Checks

The following items were flagged by automated queries and require native decision before ACC3 can be declared PASS:

| Gap | Severity | Decision Needed |
|---|---|---|
| LAGNA row absent from chart_facts | HIGH | Schema decision or data gap? |
| Navamsa-lagna row absent | HIGH | Schema decision or data gap? |
| All verification_pass_status = 'single' (no dual-pass rows) | MEDIUM | Multi-ayanamsha _finalize_rows applied? |
| Only 2 ayanamsha_id='lahiri' rows (expected 5 ayanamshas) | HIGH | Per-ayanamsha build complete for this chart? |
| Only 2 msr_signal rows | MEDIUM | Expected scope or MSR backfill needed? |
| META synthesis rows not found in auto-query | MEDIUM | Check if in separate fact_category names |

---

## Verdict (to be filled by native)

```
Verdict: [ PASS / PASS_WITH_FINDINGS / FAIL ]
Date reviewed:
Findings (if any):

Gap resolution notes:
  - LAGNA absence:
  - Dual-pass status:
  - Per-ayanamsha coverage:
  - MSR signal count:
  - META layers:
```

After completing this review, append verdict to:
`00_ARCHITECTURE/RED_TEAM_MULTI_AYANAMSHA_BUILD_v1_0.md`

---

## Supporting Files

| File | Contents |
|---|---|
| `15_red_team_artifact.md` | Copy of RED_TEAM_MULTI_AYANAMSHA_BUILD_v1_0.md |
| `16_red_team_l1_spot.txt` | SQL output: sun/moon/navamsa L1 spot check |
| `17_narration_count.txt` | Narration violations count (0) |
| `18_two_pass_dist.txt` | verification_pass_status distribution |
| `19_ayanamsha_coverage.txt` | Per-ayanamsha row counts |

---

*Packet generated by build_orchestrator Phase 6. ACC3 is NEVER auto-passed. Human review required.*
