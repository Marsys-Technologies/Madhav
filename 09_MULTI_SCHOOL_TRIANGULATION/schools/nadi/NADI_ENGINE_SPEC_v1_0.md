---
artifact: NADI_ENGINE_SPEC_v1_0.md
version: "1.0"
status: CURRENT
produced_during: M9-B-S1
produced_on: 2026-05-14
school: nadi
engine_file: platform/src/lib/schools/nadi_engine.ts
---

# Nadi Engine Specification — M9-B-S1

## §1 — School Philosophy
Nadi Jyotish (specifically Chandra Kala Nadi and Dhruva Nadi) reads planetary positions from the planet's own position, not from the Lagna. "10H from Saturn" means the 10th sign counting from Saturn's sign — a completely different computation than Parashari's "10H from Lagna." This house-from-planet convention reveals planetary axis dynamics invisible to Lagna-based schools.

## §2 — Signal Coverage
- Primary: 7/573 (1.2%) — SIG.MSR.539–543 (CKN) + 2 Dhruva Nadi cross-source
- Secondary: 24 (BNN overlap; house-from-planet conventions sometimes converge)
- Silent: 542 (all natal Parashari/Jaimini/KP signals — different trigger mechanism)

## §3 — Engine Logic
- `nadiHouseFromPlanet(sourcePlanet, targetHouse, chartData)` computes relative house
- Signal scoring: evaluate CKN trigger conditions using planet-relative house counting
- Low signal count means Nadi reads are high-signal-density but sparse overall

## §4 — Architectural Note on Silence
Parashari natal signals (SIG.MSR.001–514) are classified as SILENT for Nadi — not because Nadi contradicts them, but because the trigger mechanism (Lagna-based house counting) is structurally different from Nadi's planet-based house counting. Both may produce the same event prediction through different mechanisms; the silence preserves the mechanistic distinction.

## §5 — Key Readings for Abhisek
- SPIRITUAL is Nadi's strongest domain: 9H-from-Moon + 12H-from-Saturn + Ketu-from-Ketu
- CAREER: 10H-from-Saturn in Capricorn contains Moon (12H from Saturn) — career-mind axis
- PRIMARY SIGNALS: SIG.MSR.539–543 (CKN), SIG.MSR.541–542 (DHR cross-source)
