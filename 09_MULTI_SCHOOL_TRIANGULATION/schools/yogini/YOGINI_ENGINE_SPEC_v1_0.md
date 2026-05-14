---
artifact: YOGINI_ENGINE_SPEC_v1_0.md
version: "1.0"
status: CURRENT
produced_during: M9-B-S1
produced_on: 2026-05-14
school: yogini
engine_file: platform/src/lib/schools/yogini_engine.ts
current_yogini: bhramari
current_lord: mars
years_elapsed: 0.27
years_remaining: 3.73
---

# Yogini Engine Specification — M9-B-S1

## §1 — School Philosophy
Yogini Dasha is a 36-year repeating cycle of 8 Yoginis (divine feminine energy forms), each governed by a planetary lord. Unlike Vimshottari (which measures PERIOD character relative to individual birth), Yogini measures UNIVERSAL PERIOD character — what quality of energy is active in the cosmos during this window. All five domains are coloured by the Yogini's planetary lord signature.

## §2 — Signal Coverage
- Primary: 15/573 (2.6%) — SIG.MSR.544–558
- Secondary: 0 (Yogini Dasha measures period character, not natal planetary strength)
- Silent: 558 (cross-classification of natal signals into Yogini is structurally inappropriate)

## §3 — Yogini Cycle for Abhisek at 2026-05-14
- Birth: 1984-02-05 → Elapsed: 42.27 years
- Cycle position: 42.27 mod 36 = 6.27 years
- Cycle map: Mangala(0–1), Pingala(1–3), Dhanya(3–6), Bhramari(6–10), Bhadrika(10–15), Ulka(15–21), Siddha(21–28), Sankata(28–36)
- **Active Yogini: Bhramari (Mars-lord)** — 0.27 years in; 3.73 years remaining

## §4 — Domain Character of Bhramari/Mars
| Domain | Modifier | Character |
|---|---|---|
| CAREER | 1.1× | Driven action; professional ambition amplified |
| HEALTH | 0.9× | Mild challenge; inflammation risk; energy management needed |
| RELATIONSHIP | 0.8× | Directness over diplomacy; partnership requires navigation |
| SPIRITUAL | 0.7× | Challenging; outer action dominates inner retreat |
| PSYCHOLOGICAL | 1.1× | Constructive drive; intensity toward goals |

## §5 — Engine Logic
- `getCurrentYogini(yoginiState)`: reads yogini from ChartData.yoginiDasha or computes from birth date
- `domainCharacter[domain]`: modifier multiplies base signal scores
- Scores clamped to [0.0, 5.0] even with modifier > 1.0
