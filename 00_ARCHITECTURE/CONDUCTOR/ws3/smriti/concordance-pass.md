# Smriti: concordance-build PASS
# Session: concordance-build
# Date: 2026-06-05
# Branch: feature/ws3-rule-base

## Status: PASS

## Output
- File: `00_ARCHITECTURE/CONDUCTOR/ws3/brahmagyan_concordance.yaml`
- Version: 1.0
- Total topics: 210
- Rule corpus: 1,637 rules (BPHS 761 + Jaimini 360 + KP 280 + Tajaka 236)

## Pattern Distribution
| Pattern   | Count |
|-----------|-------|
| AGREE     | 47    |
| QUALIFY   | 90    |
| CONFLICT  | 13    |
| ORTHOGONAL| 57    |
| SILENT    | 3     |
| **TOTAL** | **210** |

## C1–C7 Flags Embedded
- C1 (Karaka frameworks PARALLEL): TC.015, TC.093–TC.096, TC.136, TC.153–TC.156, TC.192–TC.196, TC.203
- C2 (Aspect systems ORTHOGONAL): TC.052–TC.062
- C3 (House cusp SYSTEM-DEFINING): TC.019–TC.031, TC.143, TC.158–TC.160
- C4 (Strength systems NON-COMPARABLE): TC.063–TC.066, TC.198
- C5 (Timing systems NON-COMPARABLE): TC.073–TC.085, TC.151–TC.152, TC.197, TC.206
- C6 (Rahu/Ketu per-system treatment): TC.008–TC.009, TC.086–TC.092, TC.172, TC.180–TC.181, TC.200, TC.210
- C7 (Retrograde CONFLICT Parashari vs KP): TC.067–TC.072

## Key Conflicts Found (C7 + additional)
1. **TC.067–TC.072 (C7)**: Retrograde planets — Parashari says exalted-like strength;
   KP says previous nakshatra sub correction (no dignity implication).
   This is a genuine CONFLICT for any retrograde placement. Both frameworks must
   be applied independently; never blended.
2. **TC.162**: Sign-primacy (Parashari) vs. nakshatra-primacy (KP) — a fundamental
   methodological conflict on the hierarchy of analysis.
3. **TC.143**: Bhava madhya (Parashari) vs. cusp-boundary (KP) — house assignment
   for planets near boundaries conflicts between the two systems.
4. **TC.170**: KP ayanamsha vs. Lahiri ayanamsha — practically significant for
   sub-lord assignments; concurrent multi-school analysis must maintain separate
   position tables.

## Most Important AGREE Findings
- Planetary exaltation degrees (TC.001–TC.007): universal agreement across all four schools.
- Natural planetary significations (TC.013–TC.018): agreed karaka assignments.
- 27-nakshatra framework (TC.100–TC.101): shared structural foundation.
- 11th house as fulfillment (TC.178): universal across all four schools.
- Panchanga five limbs (TC.183): universally used for muhurta.
- Vara (weekday) planetary lordship (TC.168): complete agreement.

## Most Important ORTHOGONAL Findings (C1–C5)
- TC.015: Three karaka frameworks (Parashari natural/Jaimini Chara/KP sub-lord) are
  parallel axes — never flatten or merge.
- TC.031: Four house cusp systems (equal-house/rashi/Placidus/solar-return) are
  system-defining — inter-system planet positions can differ materially.
- TC.052: Four aspect systems (graha drishti/rashi drishti/sub-lord/Itthasala) are
  orthogonal — all multi-school assessments must tag which aspect system is being applied.
- TC.063: Four strength systems (Shadbala/AK-degree/sub-lord-connectivity/Panchadhikara)
  are non-comparable — a "strong" planet in one system may be "weak" in another.
- TC.073: Four timing systems (Vimshottari/Chara+Sthira+Shoola/KP-triple/Mudda+Patyayini)
  are non-comparable — cross-system convergence increases probability but systems
  must remain methodologically distinct.
- TC.116–TC.118: Marriage/child/career timing assessments are orthogonal across all
  four schools; multi-school convergence is the MARSYS multi-school triangulation method.

## Coverage by Section
| Section | Topics | TC Range |
|---------|--------|----------|
| Exaltation (9 grahas) | 9 | TC.001–TC.009 |
| Debilitation + neecha-bhanga | 3 | TC.010–TC.012 |
| Natural significators (karakas) | 6 | TC.013–TC.018 |
| House significations (12 houses) | 14 | TC.019–TC.031 |
| Planet-in-house (select) | 5 | TC.032–TC.036 |
| Major yogas | 10 | TC.042–TC.051 |
| Aspect systems (C2) | 12 | TC.052–TC.062 |
| Strength systems (C4) | 4 | TC.063–TC.066 |
| Retrograde (C7 CONFLICT) | 6 | TC.067–TC.072 |
| Timing systems (C5) | 8 | TC.073–TC.080 |
| Dasha results | 8 | TC.081–TC.085, TC.138–TC.142 |
| Rahu/Ketu (C6) | 7 | TC.086–TC.092 |
| Karaka frameworks (C1) | 5 | TC.093–TC.096 |
| Planetary friendships | 5 | TC.097–TC.099 |
| Nakshatras | 4 | TC.100–TC.103 |
| Remedies | 4 | TC.104–TC.107 |
| Divisional charts | 12 | TC.108–TC.115 |
| Special topics | 16 | TC.116–TC.131 |
| Advanced yogas | 8 | TC.132–TC.140 |
| Jaimini-specific | 10 | TC.151–TC.157, TC.193–TC.196 |
| KP-specific | 5 | TC.158–TC.162 |
| Tajaka-specific | 6 | TC.163–TC.166 |
| Shared principles | 27 | TC.167–TC.210 |

## Gate B Carry-Forward Notes
The following Gate B concordance flags (C1–C7) are fully embedded in the concordance
structure as designed in the session brief. All seven flags have dedicated meta-entries
and are cross-referenced in individual topic entries via the `flag:` field.

## Commits
- Batch 1 (TC.001–TC.100): 0d0a3b71
- Batch 2 (TC.101–TC.210): 126063bc
