---
artifact: 09_MULTI_SCHOOL_TRIANGULATION/README.md
version: "1.0"
status: CURRENT
produced_during: M9-A-S1
produced_on: 2026-05-14
governing_phase: M9 — Multi-School Triangulation
---

# 09_MULTI_SCHOOL_TRIANGULATION — Layer 9

## Purpose

This layer holds the outputs of M9 (Multi-School Triangulation) — the phase where all seven
classical Jyotish schools operate simultaneously on the shared MSR signal set (543+ signals),
producing cross-school convergence metrics and a formal inter-school disagreement register.

No human astrologer can hold all seven schools in working memory simultaneously across 500+
signals. This layer makes that comparison structural, deterministic, and auditable.

## The Seven Schools

| School | Framework | Chart Type | Primary Signal Range |
|---|---|---|---|
| Parashari | BPHS — Brihat Parashara Hora Shastra | Natal (D1–D16) | Core yogas, strength, timing |
| Jaimini | Jaimini Sutra — Chara Karaka + Chara Dasha | Natal | Pada, Karaka, Argala |
| Tajika | Varshapha — Solar Return (Varsha Kundali) | **Varsha Kundali** | Annual Sahamas, Ithasala |
| KP | Krishnamurti Paddhati — Sub-lord system | Natal | Star-lord → Sub-lord chain |
| Nadi | Chandra Kala Nadi (CKN) — house-from-planet | Natal | Sequential planetary triggers |
| BNN | Bhrigu Nandi Nadi — sequential transit analysis | Natal + Transit | Transit trigger chains |
| Yogini | Yogini Dasha — 8-Yogini 36-year cycle | Natal | Period character × domain |

## Convergence Protocol (NAP.M9.2)

- HIGH: ≥5/7 schools affirm same direction
- MEDIUM: 4/7 schools agree
- LOW: <4/7 schools agree
- Tajika excluded from count if [VARSHA_KUNDALI_PENDING] → denominator drops to 6
- BNN excluded from directional weight if [TRANSIT_DATA_PENDING]

## Folder Structure

```
09_MULTI_SCHOOL_TRIANGULATION/
├── README.md                              ← this file
├── SCHOOL_COVERAGE_AUDIT_v1_0.md          ← M9-A: per-school signal coverage table
├── YOGINI_SIGNAL_EXTRACTION_v1_0.md       ← M9-A: Yogini signals from BPHS
├── TAJIKA_SIGNAL_EXTRACTION_v1_0.md       ← M9-A: Tajika signals from Prashna Marga + Hora Sara
├── schools/
│   ├── parashari/PARASHARI_ENGINE_SPEC_v1_0.md
│   ├── jaimini/JAIMINI_ENGINE_SPEC_v1_0.md
│   ├── tajika/TAJIKA_ENGINE_SPEC_v1_0.md   ← includes Varsha Kundali architecture note
│   ├── kp/KP_ENGINE_SPEC_v1_0.md
│   ├── nadi/NADI_ENGINE_SPEC_v1_0.md
│   ├── bnn/BNN_ENGINE_SPEC_v1_0.md         ← includes TRANSIT_DATA_PENDING protocol
│   └── yogini/YOGINI_ENGINE_SPEC_v1_0.md   ← includes current Yogini computation
├── convergence/
│   ├── CONVERGENCE_METRICS_v1_0.md         ← M9-D: tabular convergence data
│   └── convergence_scores.json             ← M9-D: machine-readable
├── disagreements/
│   ├── SCHOOL_DISAGREEMENT_REGISTER_v1_0.md  ← M9-E: ≥10 worked examples
│   └── school_disagreement_register.json    ← M9-E: machine-readable
├── analysis/
│   ├── MULTI_SCHOOL_ANALYSIS_v1_0.md        ← M9-C: per-school run on Abhisek's chart
│   └── CONVERGENCE_FINDINGS_v1_0.md         ← M9-D: convergence hotspots narrative
└── M9_CLOSE_v1_0.md                         ← M9-E: sealing artifact
```

## Carry-Forwards Declared at M9 Open

- **CF.M9.1 — [VARSHA_KUNDALI_PENDING]**: Tajika engine requires 2026 Varsha Kundali chart
  (Swiss Ephemeris external computation: Sun return to natal longitude ~Jan 25 2026,
  Bhubaneswar). Not blocking M9 close.
- **CF.M9.2 — [TRANSIT_DATA_PENDING]**: BNN engine requires live transit positions for
  2026-05-14 (Swiss Ephemeris external computation). Not blocking M9 close.

---

*L9 produced during M9-A-S1 (2026-05-14). Governed by PHASE_M9_PLAN_v1_0.md.*
