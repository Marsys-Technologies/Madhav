---
artifact: KP_ENGINE_SPEC_v1_0.md
version: "1.0"
status: CURRENT
produced_during: M9-B-S1
produced_on: 2026-05-14
school: kp
engine_file: platform/src/lib/schools/kp_engine.ts
---

# KP Engine Specification — M9-B-S1

## §1 — School Philosophy
Krishnamurti Paddhati (KP) uses the Placidus house cusp system and the star-lord → sub-lord → sub-sub-lord chain to determine whether natal promise is activated. The sub-lord of each house cusp is the operative judge: if the sub-lord's star-lord is the significator of the relevant house, the promise is activated. KP is especially precise for timing via sub-lord transit chains.

## §2 — Signal Coverage
- Primary: 95/573 (16.6%) — KP sub-lord natal promise signals
- Secondary: 120 (natal yogas where KP sub-lord confirmation exists)
- Silent: 358 (Nadi/BNN/Yogini/Tajika signals)

## §3 — Engine Logic
- Domain-cusp mapping: CAREER→[10H,6H,2H], HEALTH→[1H,6H,8H,12H], RELATIONSHIP→[7H,2H,11H]
- Sub-lord activation weights from `KP_SUBLORD_ACTIVATION` table (derived from FORENSIC kp_sublords)
- Mean activation across relevant cusps modulates signal confidence weights

## §4 — Key Sub-lord Activations for Abhisek
| Cusp | Activation | Notes |
|---|---|---|
| 1H (Ascendant) | 0.95 | Saturn sub-lord (own sign → maximum activation) |
| 10H (Career) | 0.90 | Saturn exalted → near-maximum activation |
| 9H (Dharma) | 0.82 | Moon sub-lord — dharmic activation high |
| 2H (Income) | 0.80 | Good activation |
| 12H (Losses) | 0.55 | Lower activation — correct for loss house |

## §5 — Known Limitations
- Sub-lord chain depth limited to 1 level in M9-B; full 3-level (sub-sub-lord) in M9-D
- KR.M3.RT.LOW.1 (KP per-planet vs 0°-360° boundary table) carried from M3
