---
artifact: PHASE_4C_1_CLOSE_v1_0.md
version: "1.0"
status: CLOSED
canonical_id: PHASE_4C_1_CLOSE_v1_0
produced_during: 4C-1-S2
produced_on: 2026-05-19
authored_by: Claude Code sub-agent (claude-sonnet-4-6)
branch: feature/phase-4c-panchang
worktree: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §6
predecessor: 4C-1-S1 (panchang_engine scaffold; 10/10 Drik parity; 69 tests; 9 commits)
successor_gated: 4C-2 (requires phase_4b_closed external gate)
changelog:
  - v1.0 (2026-05-19): Initial authoring at 4C.1 close.
---

# Phase 4C.1 Close — `panchang_engine` v1.0.0-S2

## §1 — What 4C.1 delivered

Phase 4C.1 (two sessions: 4C-1-S1 + 4C-1-S2) built and validated the
`panchang_engine` Python computation module. As of 4C-1-S2 close:

**`panchang_engine` version: `1.0.0-S2`**
**Location:** `platform/python-sidecar/panchang_engine/`

### Core engine (delivered in 4C-1-S1)

- `types.py` — `Panchang`, `Anga`, `Timing`, `PlanetState`, `MuhuratWindow`, `NatalChart` dataclasses
- `shastra_tables.py` — 21 lookup tables (tithi/nakshatra/yoga/karana/vara names + lords; inauspicious period indices; choghadiya + hora cycles; combustion orbs; amrit_kalam + varjyam stubs)
- `ayanamsha.py` — Lahiri (project default), Raman, KP, True Chitra Paksha
- `planets.py` — 9 grahas via Swiss Ephemeris; MEAN_NODE guard for Rahu
- `timings.py` — sunrise/sunset (visible upper limb + refraction), moonrise/moonset, inauspicious periods (Rahu Kalam, Yamagandam, Gulika, Dur Muhurta), auspicious timings (Abhijit, Brahma Muhurta, Amrit Kalam, Varjyam), Choghadiya (day + night), Hora (24 planetary hours)
- `angas.py` — Tithi, Nakshatra, Yoga, Karana pair, Vara computation
- `__init__.py` — `compute_panchang()`, `panchang_range()` public API

### Special yogas (delivered in 4C-1-S2)

`special_yogas.py` implements 9 detection functions:

| Yoga | Type | Stars | Source |
|---|---|---|---|
| Sarvartha Siddhi | Auspicious | 4 | MC 5.16 + Drik |
| Amrit Siddhi | Auspicious | 5 | MC 5.17 + Drik |
| Ravi Pushya | Auspicious | 5 | MC 5.16 + Drik |
| Guru Pushya | Auspicious | 5 | MC 5.16 + Drik |
| Tripushkar | Auspicious | 4 | MC 5.11 + Drik |
| Dwipushkar | Auspicious | 3 | MC 5.11 + Drik |
| Siddha Yoga | Auspicious | 3 | MC 5.10 / BS §3 |
| Bhadra (Vishti) | Inauspicious | 0 | MC §2 / BS §2 |
| Panchaka | Inauspicious | 0 | BS §3 + Drik |

All yoga windows are clipped to `[sunrise_utc, next_sunrise_utc]`. If a
nakshatra transitions mid-day, the yoga window for the first nakshatra ends at
the transition. Returns `list[dict]` per yoga with keys: `yoga`, `start_utc`,
`end_utc`, `strength`, `stars`.

### Muhurat scaffold (delivered in 4C-1-S2)

`muhurat.py` — API signatures locked; bodies return 0.0 / `[]` until 4C.6:
- `EVENTS_MVP` = 6 events (vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation)
- `is_supported_event(event)` → bool
- `score_muhurat(date, lat, lon, event, native_chart=None)` → 0.0 (scaffold)
- `find_muhurat(event, date_from, date_to, lat, lon, native_chart=None)` → [] (scaffold)

### Drik validation gate

| Fixture | Days | Gate | Status |
|---|---|---|---|
| `drik_panchang_v1.json` | 10 | 10/10 | Superseded by v2 |
| `drik_panchang_v2.json` | 30 | 30/30 | **PASS — 4C.1 close gate** |

v2 fixture covers 2020–2026, all 7 vara IDs, 20 days with active special yogas,
1 Delhi sensitivity day. Special yoga start/end times validated at ±120s.

### Test suite

| Test file | Cases | Status |
|---|---|---|
| `test_angas.py` | 27 | PASS |
| `test_timings.py` | 26 | PASS |
| `test_planets.py` | 6 | PASS |
| `test_drik_parity.py` | 30 | **PASS (30/30 gate)** |
| `test_special_yogas.py` | 55 | PASS |
| `test_muhurat.py` | 6 | PASS |
| **Total** | **150** | **ALL PASS** |

---

## §2 — Acceptance criteria status

All acceptance criteria from `PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §6` Phase 4C.1:

| AC | Description | Status |
|---|---|---|
| AC.4C1S2.1 | Pre-flight integrity OK | PASS |
| AC.4C1S2.2 | shastra_tables.py populated | PASS |
| AC.4C1S2.3 | special_yogas.py detection logic | PASS |
| AC.4C1S2.4 | compute_panchang wired + version bump | PASS |
| AC.4C1S2.5 | test_special_yogas.py 55 cases | PASS |
| AC.4C1S2.6 | drik_panchang_v2.json 30 days | PASS |
| AC.4C1S2.7 | 30/30 parity gate PASS | **PASS** |
| AC.4C1S2.8 | muhurat.py scaffold | PASS |
| AC.4C1S2.9 | README updated | PASS |
| AC.4C1S2.10 | PANCHANG_DAILY status flip | PASS |
| AC.4C1S2.11 | MP.2 mirror propagation | PASS |
| AC.4C1S2.12 | Phase 4C.1 close protocol | PASS |
| AC.4C1S2.13 | Brief COMPLETE; FINAL_SUMMARY | PASS |

---

## §3 — What is NOT yet delivered (deferred to 4C.6+)

- `muhurat.py` body implementation (score_muhurat + find_muhurat full scoring)
- `AMRIT_KALAM_TABLE` + `VARJYAM_TABLE` population in shastra_tables.py (stubs)
- Amrit Siddhi MC 5.17 Visha Yoga exclusions in detect_amrit_siddhi()
- Cloud SQL `panchang_daily` table wiring (4C.2 — gated on Phase 4B)
- `query_panchanga` RetrievalTool (4C.3)
- `/panchang` UI surface (4C.5)
- Full Muhurat Finder scoring (4C.6)
- iCal export + Ask-Madhav deep links (4C.7)

---

## §4 — Gate summary

The 4C.1 close gate is the **30/30 Drik parity test** (`pytest tests/test_drik_parity.py`).

```
pytest platform/python-sidecar/panchang_engine/tests/test_drik_parity.py -v
# 30 passed — GATE PASS
```

Gate passed at commit `0f309f9` (4C-1-S2 Item 7).

---

## §5 — What comes next

4C.2 (Cloud SQL cache wiring + `panchang_daily` backfill) is **GATED** on
Phase 4B closing (sunrise derivation, Migration 059, MEAN_NODE rebuild).
The Conductor will halt at 4C-2 with `phase_4b_closed` external-gate blocker.

Native options:
1. Prioritize Phase 4B to unblock 4C.2.
2. Skip to 4C.3 (`query_panchanga` RetrievalTool — engine-direct, no SQL dependency).

Either path requires Cowork brief authoring before Conductor resumes.

---

*End of PHASE_4C_1_CLOSE_v1_0.md v1.0 — 4C.1 CLOSED 2026-05-19.*
*panchang_engine v1.0.0-S2 | 30/30 Drik gate PASS | 150 tests PASS*
