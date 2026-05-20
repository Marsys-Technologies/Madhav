---
artifact: RT_4C_2_FINDING.md
probe_id: RT.4C.2
probe_question: >
  B.10 discipline — does any displayed value lack provenance back to engine + ephemeris?
session_id: 4C-9
authored_on: 2026-05-20
verdict: PASS
---

# RT.4C.2 — B.10 Provenance Finding

## §1 — Probe question

Does any value displayed in the Panchang UI lack traceable provenance back to
the Python engine + pyswisseph ephemeris computation?

## §2 — Evidence examined

All 12 UI components in `platform/src/app/panchang/components/` and the
`usePanchangDay` hook chain.

## §3 — Data flow audit

Every value displayed on `/panchang` follows this chain:

```
pyswisseph (Swiss Ephemeris C library)
  ↓
panchang_engine (Python — angas.py, planets.py, timings.py, special_yogas.py, muhurat.py)
  ↓
/api/compute/panchanga or /api/compute/muhurat (FastAPI sidecar)
  ↓
PanchangClientView (React) → individual display components
```

### Values verified by category:

| Category | Values | Source | PASS/WARN |
|---|---|---|---|
| Panchang angas | Tithi, Nakshatra, Yoga, Karana, Vara | Engine → sidecar → UI | PASS |
| Timings | Sunrise, Sunset, Rahu Kalam, Gulika, Yamagandam, Dur Muhurta | Engine → sidecar → UI | PASS |
| Planetary positions | Longitude (sidereal), Sign, Nakshatra, Pada, Retrograde, Combust | pyswisseph → engine → sidecar → UI | PASS |
| Special Yogas | Sarvartha Siddhi, Amrit Siddhi, Ravi Pushya, Guru Pushya, Dwipushkar, Tripushkar, Siddha | Engine (compound detection) → sidecar → UI | PASS |
| Choghadiya | 8 daytime + 8 nighttime segments with quality labels | Engine (muhurta Shastra tables) → sidecar → UI | PASS |
| Hora | Planetary hora sequence | Engine (static table, day-of-week anchored) → UI | PASS |
| Muhurat results | score, star_rating, breakdown (per-factor) | muhurat.py → /api/compute/muhurat → UI | PASS |
| DMS formatting | degrees°min'sec display of longitude | lonWithinSign(engine_value) — formatting only | PASS |
| Tara Bala label | Personalise overlay annotation | computeTaraBala(engine.nakshatra_id) — table lookup on engine value | PASS |
| Chandra Bala badge | Personalise overlay annotation | computeChandraBala(engine.moon_sign_id) — table lookup on engine value | PASS |

### No hardcoded astrological values found

Inspection of all 12 components confirms:
- No planetary positions are hardcoded in TypeScript
- No tithi, nakshatra, or yoga values are computed client-side
- The only client-side computation is DMS formatting (modular arithmetic)
  and Tara/Chandra Bala table lookup (on engine-provided IDs)

## §4 — Verdict

**PASS** — All displayed values trace to engine + ephemeris. No B.10 violation.
The Tara/Chandra Bala functions apply static lookup tables to engine-computed
nakshatra/sign IDs — inputs come from pyswisseph, not from fabrication.
