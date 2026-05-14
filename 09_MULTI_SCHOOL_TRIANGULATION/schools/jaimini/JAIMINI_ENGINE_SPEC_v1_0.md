---
artifact: JAIMINI_ENGINE_SPEC_v1_0.md
version: "1.0"
status: CURRENT
produced_during: M9-B-S1
produced_on: 2026-05-14
school: jaimini
engine_file: platform/src/lib/schools/jaimini_engine.ts
---

# Jaimini Engine Specification — M9-B-S1

## §1 — School Philosophy
Jaimini Sutras use Chara Karaka (changing significators) hierarchy instead of fixed Parashari house lordships. The Atmakaraka (highest-degree planet) reveals the soul's purpose; Amatyakaraka governs career. Rashi Dasha (sign periods) replace Vimshottari. Argala (planetary intervention) and Pada (sign footprint) are operative.

## §2 — Signal Coverage
- Primary: 181/573 (31.6%) — concentrated in Chara Karaka, Rashi Dasha, Argala signals
- Secondary: 90 (BPHS Jaimini chapters)
- Silent: 302 (Nadi/BNN/Yogini/Tajika signals)

## §3 — Engine Logic
- Chara Karaka for Abhisek: AK=Moon, AmK=Saturn, BK=Mercury, MK=Mars, PK=Sun, GK=Venus, DK=Jupiter (FORENSIC §22)
- Karaka weight modulates signal weights by domain relevance
- CAREER: AmK (Saturn) dominates → 0.85× weight amplification on career signals

## §4 — Key Signals for Abhisek
| Signal ID | Name | Domain | Score |
|---|---|---|---|
| SIG.MSR.055 | AmK Saturn exalted — career significator | CAREER | 4.6 |
| SIG.MSR.067 | AK Moon — public role aspirations | CAREER | 3.8 |
| SIG.MSR.407 | AK Moon — soul purpose dharma | SPIRITUAL | 4.0 |

## §5 — Known Limitations
- Narayana Dasha cross-check deferred (DIS.012 N3)
- Chara Dasha timing not yet wired to M9-C analysis
