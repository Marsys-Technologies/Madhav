---
artifact: SCHOOL_COVERAGE_AUDIT_v1_0.md
version: "1.0"
status: CURRENT
produced_during: M9-A-S1
produced_on: 2026-05-18
signal_count_audited: 514
---

# School Coverage Audit — M9-A-S1

Per-school classification of all MSR signals as primary / secondary / silent.
Source: classical_attributions JOIN classical_texts (tradition field) + signal range heuristics.

## Coverage Table

| School | Primary | Secondary | Silent | Total | Primary% |
|---|---|---|---|---|---|
| parashari | 51 | 448 | 15 | 514 | 9.9% |
| jaimini | 7 | 45 | 462 | 514 | 1.4% |
| tajika | 31 | 0 | 483 | 514 | 6.0% |
| kp | 0 | 0 | 514 | 514 | 0.0% |
| nadi | 0 | 0 | 514 | 514 | 0.0% |
| bnn | 0 | 0 | 514 | 514 | 0.0% |
| yogini | 0 | 51 | 463 | 514 | 0.0% |

## Coverage Notes

- **Parashari**: Broadest coverage — BPHS + Saravali + Phaladeepika + Brihat Jataka + Brihat Samhita + Uttara Kalamrita all contributing. Most base yogas (SIG.MSR.001–300 range) are primary Parashari signals.
- **Jaimini**: Coverage concentrated in Chara Karaka signals and Rashi Dasha sequences. SIG.MSR.001–200 has secondary Jaimini coverage via BPHS Jaimini chapters.
- **Tajika**: Dedicated signals SIG.MSR.600+ (M9-A extraction); SIG.MSR.001–543 range is silent for Tajika as these are natal-framework signals.
- **KP**: Sub-lord signals clustered in the KP-specific range. Many natal signals are silent from KP perspective (different trigger mechanism).
- **Nadi**: CKN-specific signals SIG.MSR.539–543 are primary. BNN signals SIG.MSR.515–538 are secondary (related Nadi school). SIG.MSR.001–514 mostly silent (different trigger convention).
- **BNN**: SIG.MSR.515–538 are primary BNN signals (sequential transit analysis). SIG.MSR.539–543 are secondary (related Nadi framework). SIG.MSR.001–514 mostly silent.
- **Yogini**: Dedicated signals SIG.MSR.544+ (M9-A extraction); SIG.MSR.001–543 range is silent for Yogini as these are natal-position signals, not period-character signals.

## Gap Analysis

| Gap | Details |
|---|---|
| Tajika signals in MSR v4.0 | None — gap filled by M9-A extraction → TAJIKA_SIGNAL_EXTRACTION_v1_0.md |
| Yogini signals in MSR v4.0 | None — gap filled by M9-A extraction → YOGINI_SIGNAL_EXTRACTION_v1_0.md |
| KP sub-lord table | KP engine uses KP-specific trigger from FORENSIC; direct signal attribution is secondary for most natal signals |

*Produced M9-A-S1 (2026-05-14). 514 signals × 7 schools = 3598 classification decisions.*