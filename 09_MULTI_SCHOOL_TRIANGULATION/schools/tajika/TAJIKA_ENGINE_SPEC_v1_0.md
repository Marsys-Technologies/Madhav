---
artifact: TAJIKA_ENGINE_SPEC_v1_0.md
version: "1.0"
status: CURRENT
produced_during: M9-B-S1
produced_on: 2026-05-14
school: tajika
engine_file: platform/src/lib/schools/tajika_engine.ts
pending_flag: CF.M9.1 [VARSHA_KUNDALI_PENDING]
---

# Tajika Engine Specification — M9-B-S1

## §1 — School Philosophy
Tajika (Persian-Arabic annual chart tradition) operates on the Varsha Kundali — the solar return chart computed when the Sun returns to its natal longitude each year (~Jan 25 for Abhisek). Ithasala (applying aspect), Ishrafa (separating aspect), Varshesha (annual lord), Muntha (annual progressed point), and Sahamas (Arabic lots) are the operative concepts.

## §2 — Signal Coverage
- Primary: 15/573 (2.6%) — SIG.MSR.559–573 (solar_return_scope:true)
- Secondary: 0 (Tajika operates on a structurally different chart)
- Silent: 558 (all natal signals)

## §3 — Critical Architectural Note
Tajika uses the Varsha Kundali (annual solar return chart), NOT the natal D1 chart that all other schools use. Cross-classification of Tajika signals against the natal chart is structurally unsound except at domain-score comparison level. Tajika is excluded from convergence count when [VARSHA_KUNDALI_PENDING] is active (schoolsTotal drops to 6 for affected domains).

## §4 — CF.M9.1 [VARSHA_KUNDALI_PENDING]
Abhisek's 2026 Varsha Kundali requires Swiss Ephemeris computation:
- Sun natal longitude: ~301.5° (Capricorn 21.5°)
- Solar return date: approximately January 25, 2026
- Location: Bhubaneswar, Odisha (20.2961°N, 85.8245°E)
- [EXTERNAL_COMPUTATION_REQUIRED: `swisseph.sol_eclipse_when_glob()` or `swisseph.calc_ut()` iterative solution]

## §5 — Known Limitations
- All Tajika scores are natal-approximated and carry reduced confidence weights (0.35–0.50)
- Domain scores marked as PENDING until Varsha Kundali computed
- Excluded from convergence schematism when pending flag is active
