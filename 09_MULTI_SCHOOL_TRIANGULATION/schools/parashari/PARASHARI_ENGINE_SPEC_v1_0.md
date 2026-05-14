---
artifact: PARASHARI_ENGINE_SPEC_v1_0.md
version: "1.0"
status: CURRENT
produced_during: M9-B-S1
produced_on: 2026-05-14
school: parashari
engine_file: platform/src/lib/schools/parashari_engine.ts
---

# Parashari Engine Specification — M9-B-S1

## §1 — School Philosophy
Parashari (BPHS tradition) is the foundational Jyotish school. All 12 houses are read from Lagna (rising sign). Planetary strengths (Shad Bala), yoga formations (Raja, Dhana, Viparita yogas), and Vimshottari Dasha timing govern outcomes. Capricorn Lagna with Saturn exalted in 10H is the apex career formation in this tradition.

## §2 — Signal Coverage
- Primary signals: 514/573 (89.7%) — natal yoga signals SIG.MSR.001–514
- Secondary signals: 29 (Nadi/BNN range where Parashari provides natal context)
- Silent signals: 30 (Yogini + Tajika signals — non-Parashari framework)

## §3 — Engine Logic
- Filter: `school_signal_coverage WHERE school='parashari' AND coverage_type='primary'`
- Domain score: weighted sum of signal scores, normalized to 0.0–5.0
- Weights: signal confidence from `school_signal_coverage.confidence` column
- Pending M9-D: wire M5 calibrated DBN weights from `dbn_params_v1_0.json`

## §4 — Key Signals for Abhisek
| Signal ID | Name | Domain | Score |
|---|---|---|---|
| SIG.MSR.041 | Saturn 10H exalted yoga | CAREER | 4.8 |
| SIG.MSR.089 | Mercury-Saturn Capricorn conjunction | CAREER | 4.2 |
| SIG.MSR.401 | Ketu 12H moksha placement | SPIRITUAL | 4.5 |
| SIG.MSR.412 | Moon 9H dharmic inclination | SPIRITUAL | 4.2 |

## §5 — Direction Thresholds
- positive: domainScore ≥ 3.2
- negative: domainScore ≤ 1.8
- neutral: 1.8 < domainScore < 3.2

## §6 — Known Limitations
- Tajika/Yogini signals are SILENT — cross-classification structurally inappropriate
- KP sub-lord confirmation (secondary) not wired in M9-B; deferred to M9-D
