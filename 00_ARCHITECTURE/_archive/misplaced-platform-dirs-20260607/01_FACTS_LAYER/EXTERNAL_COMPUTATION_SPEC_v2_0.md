---
artifact: EXTERNAL_COMPUTATION_SPEC_v2_0.md
version: 2.0
status: CLOSED
date: 2026-04-18
supersedes: "EXTERNAL_COMPUTATION_SPEC (Session 3 v1.0) for Facts Layer v8.0 upgrade scope"
scope: "Specification of external computations (Jagannatha Hora exports) required for Facts Layer v8.0 upgrade. Resolves 3 still-open gaps post AUDIT_REPORT_v1_0 and FIX_SESSION_002."
execution_owner: Native (Abhisek Mohanty)
execution_tool: Jagannatha Hora (already installed per Session 3 bootstrap)
estimated_effort: "2-3 days native effort + 1-2 Claude sessions to incorporate"
expose_to_chat: false
native_id: "abhisek"
layer: "L1"
category: source
---

# EXTERNAL_COMPUTATION_SPEC v2.0 — Facts Layer v8.0 Source Data
### 2026-04-18 | CLOSED

---

## §0 — EXECUTION STATUS (2026-04-19)

**Facts Layer v8.0 is built** (`FORENSIC_ASTROLOGICAL_DATA_v8_0.md`). **GAP.01 (Birth Yoga)** and **core lagna/saham corrections** are **RESOLVED** via JH transcription and reconciliation sessions. **LONGEVITY.GAP.01** is **CLOSED by policy** (Kalachakra 85 years per **GOVERNANCE_STACK**); §2 Export 3 (Ayurdasaya trio) is **optional** unless the native wants Parashari parity rows populated.

**Still valuable native exports:** **GAP.03** (D9 degree-level 12H stellium), **Varshphal / Varshesha** (requires **exact solar-return time**), optional **Moola/Narayana/Kalachakra sub-rows** marked `[EXTERNAL_COMPUTATION_REQUIRED]` in FORENSIC §25+.

---

## §1 — PURPOSE

This spec originally listed all JHora exports needed to stand up FORENSIC v8.0. With v8.0 **shipped**, treat §2 as a **checklist for remaining optional cells** — not blocking items except where a Domain Report explicitly depends on a still-empty L1 row.

**Remaining high-leverage exports (if not yet done):**

- **GAP.03** — D9 12H stellium precise degree composition (degree-level verification)
- **Varshphal detail** — Varshesha / Year Lord — **requires exact solar return timestamp**
- **Optional** — Ayurdasaya trio (Pindayu/Nisargayu/Amsayu) for §24.2 optional rows only

This spec defines exactly what JHora exports are needed for those cells. Native executes against this spec; Claude incorporates outputs into FORENSIC patch releases.

---

## §2 — EXPORT CHECKLIST

### Export 1: Birth Panchang Yoga

**JHora menu**: Panchang → Daily Panchang at time of birth

**Required data**:
- Yoga name (e.g., Vishkambha, Priti, Ayushman, Saubhagya, Shobhana, Atiganda, Sukarma, Dhriti, Shula, Ganda, Vriddhi, Dhruva, Vyaghata, Harshana, Vajra, Siddhi, Vyatipata, Variyan, Parigha, Shiva, Siddha, Sadhya, Shubha, Shukla, Brahma, Indra, Vaidhriti)
- Yoga start time and end time
- Whether birth time 10:43 IST falls within the yoga window
- Ruler/deity of the yoga

**Resolves**: GAP.01 (v6.0 §9 Birth Yoga)

**Integration target**: FORENSIC v8.0 §9 + UCN §I.1 FS5 refresh

---

### Export 2: D9 Navamsa Full Degree Detail

**JHora menu**: Divisional Charts → D9 Navamsa → Detail view

**Required data**: For each of 9 planets + Lagna:
- D9 Sign (already verified in audit)
- D9 Degree (currently not in FORENSIC v6.0)
- D9 Nakshatra
- D9 Pada
- Specifically for 12H in D9: what planets occupy it and at what degrees (for GAP.03 stellium composition)

**Resolves**: GAP.03 (D9 12H stellium composition); upgrades GAP.02/02b/02c/02d from "sign-level resolved" to "degree-level resolved"

**Integration target**: FORENSIC v8.0 §3.1 (Navamsa detail)

---

### Export 3: Ayurdasaya (Longevity)

**JHora menu**: Longevity → Ayurdasaya calculation

**Required data**:
- **Pindayu** (body-longevity years)
- **Nisargayu** (natural-longevity years)
- **Amsayu** (combined/graded longevity years)
- **Dvadasottari** variant if JHora presents
- Reduction factors applied (Chakra Payu reduction, etc.)
- Final estimated lifespan (years from birth)

**Resolves**: LONGEVITY.GAP.01

**Integration target**: FORENSIC v8.0 §22 (new longevity subsection) + REPORT_HEALTH_LONGEVITY v1.1 refresh

---

### Export 4: Varshphal 2026-2027 Complete

**JHora menu**: Varshaphal → Year 2026 (solar return)

**Required data**:
- **Solar return precise time** (when Sun returns to natal degree 291.96° Capricorn)
- **Varsha Lagna** (solar-return ascendant)
- **Muntha sign** for this year (progressed Lagna)
- **Muntha lord**
- **Muntha placement** (house in the Varsha chart)
- **Varshesha (Year Lord)** — lord of the strongest among 5 official candidates (Lagna-lord, Muntha-lord, Aaditya-yogi-lord, etc.)
- **Mudda Dasha** sequence for the year
- **Hadda lords** for key planetary points
- **Pancha-Vargeeya Bala** per planet (5-fold annual strength)

**Resolves**: Varshphal detail gap; partial remediation for HEATMAP_VARSHPHAL §3 (2027-2028)

**Integration target**: FORENSIC v8.0 §23 refresh + HEATMAP_VARSHPHAL v1.1

---

### Export 5: Varshphal 2027-2028 Complete

**JHora menu**: Same as Export 4, year 2027

**Required data**: Same as Export 4

**Resolves**: Full Varshphal coverage for 36-month horizon

**Integration target**: HEATMAP_VARSHPHAL v1.1

---

### Export 6: D7 Saptamsha Degree Detail (upgrade GAP.05 resolution)

**JHora menu**: Divisional Charts → D7 Saptamsha → Detail

**Required data**: D7 Lagna degree + planetary D7 positions with degrees (sign-level already in AUDIT WS-1b).

**Resolves**: GAP.05 upgraded from "sign-confirmed" to "degree-confirmed"

**Integration target**: FORENSIC v8.0 §3.4

---

## §3 — NAMED EXPORT FILES

When executing exports via JHora, save with these filenames for incorporation clarity:

```
JHora/v8.0_source/
  panchang_yoga.txt
  d9_navamsa_detail.txt
  ayurdasaya.txt
  varshphal_2026.txt
  varshphal_2027.txt
  d7_saptamsha_detail.txt
```

Text exports preferred over .docx (easier to parse); PDF acceptable if text not available.

---

## §4 — POST-EXPORT WORKFLOW

1. **Native executes** Exports 1-6 via JHora
2. **Native places** files in `JHora/v8.0_source/` directory
3. **Native signals** Claude to start incorporation session
4. **Claude incorporation session (1-2 days of work)**:
   - Parse all 6 exports via `textutil -convert txt`
   - Build `FORENSIC_ASTROLOGICAL_DATA_v8.0.md` as successor to v6.0 + v7.0 supplement
   - Update all downstream gaps status (GAP.01 → RESOLVED, GAP.03 → RESOLVED, LONGEVITY.GAP.01 → RESOLVED, Varshphal → RESOLVED)
   - Refresh `UCN_v1_1.md` §I.1 FS5 with Birth Yoga data
   - Refresh `REPORT_HEALTH_LONGEVITY_v1_0.md` with Ayurdasaya
   - Refresh `HEATMAP_VARSHPHAL_v1_0.md` with actual Varshphal data (replacing current L1 Muntha-only reference)
5. **Red-team** Facts Layer v8.0 before marking CLOSED

---

## §5 — DEPENDENCIES

Before this spec can execute:
- Native must have Jagannatha Hora installed with native's chart loaded (verified: installed per Session 3 bootstrap)
- Native must have ~2-3 days availability to execute all exports
- Claude must have 1-2 uninterrupted incorporation sessions available

---

## §6 — DEFERRED UNTIL v8.0

Items deferred until Facts Layer v8.0 is complete:
- UCN v2.0 close (currently DRAFT)
- MSR v2.0 (pending)
- External acharya review packet refresh (to include v8.0 data)
- Next quarterly HEATMAP refresh (uses v8.0 data if available)

---

*End of EXTERNAL_COMPUTATION_SPEC_v2_0.md — 2026-04-18 — CLOSED*
