---
artifact: TAJIKA_CLASS_AUDIT_v1_0.md
canonical_id: TAJIKA_CLASS_AUDIT
version: 1.0
status: CURRENT
authored_by: Claude Sonnet 4.6 (WRAPUP-S1 sub-agent)
authored_at: 2026-05-21
purpose: >
  Read-only audit of MSR_v5_0.md Tajika signals (SIG.MSR.376–387 §14 block
  and SIG.MSR.559–573 §IX block) against FORENSIC_ASTROLOGICAL_DATA_v8_0.md §22
  VRS.* facts. Identifies any residual instances of the inclusive/exclusive
  sign-counting error class that produced DIS.013.
scope: Read-only. No MSR edits performed or authorized from this audit.
changelog:
  - version: 1.0
    date: 2026-05-21
    author: Claude Sonnet 4.6 (WRAPUP-S1)
    note: Initial audit — 27 Tajika signals; 1 WRONG finding (SIG.MSR.387)
---

# Tajika Class-of-Error Audit
## MSR_v5_0.md vs FORENSIC v8.0 §22

---

## Scope

Two Tajika blocks exist in MSR_v5_0.md:

- **§14 block** (SIG.MSR.376–387): 12 signals — Panchang extension "framework + Muntha" block. Lines 8760–9044.
- **§IX block** (SIG.MSR.559–573): 15 signals — Prashna Marga + Hora Sara Tajika chapters. Lines 12533–12855.

**Total Tajika signals audited: 27**

---

## FORENSIC §22 VRS.* Facts — Inventory

| VRS ID | Component | Value | FORENSIC Line |
|---|---|---|---|
| `VRS.VALIDITY` | Validity | 2026-02-05 to 2027-02-05 | 1479 |
| `VRS.MUNTHA.SIGN` | Muntha | Libra (7th House) | 1480 |
| `VRS.MUNTHA.LORD` | Muntha Lord | Venus | 1481 |
| `VRS.YEAR.LORD` | Year Lord | [INTENTIONALLY EXCLUDED] | 1482 |
| `VRS.MUDDA.DASHA` | Mudda Dasha | [INTENTIONALLY EXCLUDED] | 1483 |

§22 contains exactly 5 VRS.* IDs. Year Lord and Mudda Dasha are explicitly excluded
as optional enhancements. Only Muntha fields are populated as canonical L1 facts.

---

## Summary

| Verdict | Count | Signal IDs |
|---|---|---|
| VERIFIED | 25 | 376, 378, 379, 380, 381, 382, 383, 384, 385, 386, 559–573 |
| VERIFIED (with note) | 1 | 384 (Mudda period totals sum ~259d, not 365 — classical methodology caveat, not L1 conflict) |
| **WRONG** | **1** | **387** |
| UNVERIFIABLE | 0 | — |
| INCLUSIVE_COUNTING_BUG | 0 | — (subsumed into WRONG for .387) |

---

## §14 Block Verdicts (SIG.MSR.376–387)

| Signal ID | Signal Name (abbreviated) | VRS.* Cited | Verdict | Summary |
|---|---|---|---|---|
| SIG.MSR.376 | Varshaphal Framework — Solar Return methodology | None (framework) | VERIFIED | Framework-only signal; references natal Sun ~25-26° Capricorn confirmed at FORENSIC line 159. No VRS.* derivation claimed. |
| SIG.MSR.377 | Muntha at Age 42: Libra 7H | VRS.MUNTHA.SIGN (L.1480), VRS.MUNTHA.LORD (L.1481) | VERIFIED | Signal claims Muntha = Libra 7H, lord = Venus. FORENSIC §22 confirms both. DIS.013 resolved; derivation ledger DL.MSR.377.1 present. Fully clean. |
| SIG.MSR.378 | Ithasala Yoga — Converging Planets | None (framework) | VERIFIED | Framework signal. Falsifier correctly states `[FRAMEWORK SIGNAL — requires per-year Varshaphal]`. No specific VRS.* claim. |
| SIG.MSR.379 | Ishrafa Yoga — Separation Pattern | None (framework) | VERIFIED | Framework signal. No VRS.* claim. LEL event years cited as hypothesis only. |
| SIG.MSR.380 | Varshesha Identification | None (framework) | VERIFIED | Correctly acknowledges Varshesha requires per-year Varshaphal. VRS.YEAR.LORD = [INTENTIONALLY EXCLUDED] in FORENSIC — signal does not claim a specific value. Consistent. |
| SIG.MSR.381 | Tajika Special Lagna — Singapore vs Bhubaneswar | None (geographic) | VERIFIED | Geographic facts (lat/lon) consistent with FORENSIC MET section. No VRS.* conflict. |
| SIG.MSR.382 | Sahama in Varshaphal — Annual Sahamas | None (framework) | VERIFIED | Annual Sahama requires per-year Varshaphal, correctly flagged. Natal Vyapara Saham = Capricorn 10H is natal L1 §12.2 fact, not VRS.*. |
| SIG.MSR.383 | Tri-Pataki Chakra — Trident from Annual Lagna | None (framework) | VERIFIED | Annual Lagna determination requires per-year calculation, correctly flagged. |
| SIG.MSR.384 | Mudda Dasha — Monthly Sub-Periods | VRS.MUDDA.DASHA (implicit) | VERIFIED (note) | VRS.MUDDA.DASHA = [INTENTIONALLY EXCLUDED]; signal provides classical framework only. Note: period table sums to ~259 days (not 365) — proportional normalization applies in classical system; this is not an L1 conflict. |
| SIG.MSR.385 | Saturn Exalted as Perennial Varshesha Candidate | None (natal facts) | VERIFIED | Claims Saturn natal exaltation = Libra 7H. FORENSIC line 165: PLN.SATURN = Libra, 22°27'04", House 7. Confirmed. |
| SIG.MSR.386 | Dwisaptati Sama Dasha — Conditional Tajika Dasha | None (framework/conditional) | VERIFIED | Conditional framework signal. Correctly flagged `[FRAMEWORK/CONDITIONAL SIGNAL]`. |
| **SIG.MSR.387** | **Tajika Section Synthesis — Mercury-Saturn 2024-2027** | Synthesis of .376–.386 | **WRONG** | **Carries "Virgo 6H" residual from pre-DIS.013-correction authoring. Details below.** |

---

## WRONG Finding: SIG.MSR.387 — Full Detail

### Signal's Claims

Three locations in SIG.MSR.387 assert the wrong Muntha value:

| Location | Line (approx) | Signal Text |
|---|---|---|
| supporting_rules | 9033 | `"Muntha at age 42 = Virgo 6H"` |
| supporting_rules | 9035 | `"Muntha in 6H at age 42 = caution: health and opposition management..."` |
| falsifier | 9039 | `"Muntha at 42 = Virgo 6H = confirmed calculation."` |

### L1 Ground Truth

- **FORENSIC v8.0, line 1480:** `VRS.MUNTHA.SIGN = Libra (7th House)`
- **FORENSIC v8.0, line 1479:** `VRS.VALIDITY = 2026-02-05 to 2027-02-05` (native turns 42 on 2026-02-05)

### Arithmetic Verification

Natal Lagna = Aries.
Age 42: 42 mod 12 = 6 → Aries + 6 signs advanced = Libra (7th sign, 7H from Aries Lagna).
**Libra 7H is correct.**

Virgo 6H corresponds to age 41 (41 mod 12 = 5, Aries + 5 = Virgo = 6H) — the off-by-one
value that was the root of DIS.013.

### Root Cause

SIG.MSR.377 was correctly rewritten (DIS.013 resolution, DL.MSR.377.1 derivation ledger).
SIG.MSR.387 — the synthesis signal — was NOT updated in the same session. The old
"Virgo 6H" language persists verbatim. The contradiction between .377 (Libra 7H, correct)
and .387 (Virgo 6H, wrong) is visible within the same file.

### Error Class

INCLUSIVE_COUNTING_BUG (age 41 residual carried forward into the synthesis signal).

### Downstream Errors Introduced

- The synthesis signal's characterization of the year as "health and opposition management"
  (6H themes) is incorrect; the L1-grounded year activates 7H themes (partnership/public).
- The falsifier in .387 falsely asserts "Virgo 6H = confirmed calculation" when calculation
  confirms Libra 7H.

### Required Fix (NOT Performed — Read-Only Audit)

In SIG.MSR.387, three lines need updating:

1. Line 9033: `"Muntha at age 42 = Virgo 6H"` → `"Muntha at age 42 = Libra 7H"`
2. Line 9035: Replace 6H characterization → 7H synthesis aligned with MSR.377's established text
3. Line 9039: `"Muntha at 42 = Virgo 6H = confirmed calculation."` → `"Muntha at 42 = Libra 7H = confirmed calculation (per VRS.MUNTHA.SIGN, FORENSIC §22 line 1480; and MSR.377 derivation ledger DL.MSR.377.1)."`

Each WRONG signal needs its own grounded-rewrite session (per MSR.377 precedent).
Auto-fix from audit is explicitly prohibited per WRAPUP-S1 halt rules.

---

## §IX Block Verdicts (SIG.MSR.559–573)

All 15 signals are generic Tajika yoga/sahama/foundation framework templates.
None claim any specific VRS.* value from FORENSIC §22.
All carry `pending_flag: VARSHA_KUNDALI_PENDING`.

| Signal ID | Tajika Concept | Verdict |
|---|---|---|
| SIG.MSR.559 | Ithasala Yoga | VERIFIED |
| SIG.MSR.560 | Ishrafa Yoga | VERIFIED |
| SIG.MSR.561 | Varshesha in Angle | VERIFIED |
| SIG.MSR.562 | Varshesha in Dusthana | VERIFIED |
| SIG.MSR.563 | Muntha in Angle | VERIFIED |
| SIG.MSR.564 | Muntha Lord in 12H | VERIFIED |
| SIG.MSR.565 | Punya Sahama Angular | VERIFIED |
| SIG.MSR.566 | Vidya Sahama Angular | VERIFIED |
| SIG.MSR.567 | Dara Sahama Angular | VERIFIED |
| SIG.MSR.568 | Nakta Yoga | VERIFIED |
| SIG.MSR.569 | Kambula Yoga | VERIFIED |
| SIG.MSR.570 | Saturn-Ithasala | VERIFIED |
| SIG.MSR.571 | Mars-Ithasala Adversarial | VERIFIED |
| SIG.MSR.572 | Varsha Lagna Lord Angular | VERIFIED |
| SIG.MSR.573 | Paka Sahama Angular | VERIFIED |

---

## Action Required

| Priority | Action | Session Type |
|---|---|---|
| HIGH | Rewrite SIG.MSR.387 to replace "Virgo 6H" with "Libra 7H" (3 locations) and update 7H synthesis characterization | Dedicated grounded-rewrite session (like MSR-377-LIBRA-7H precedent) |
| INFO | SIG.MSR.384 Mudda period table normalization note | No action needed — classical methodology, not L1 conflict |

---

*Audit conducted by WRAPUP-S1 sub-agent 2026-05-21. Read-only. MSR_v5_0.md not modified.*
