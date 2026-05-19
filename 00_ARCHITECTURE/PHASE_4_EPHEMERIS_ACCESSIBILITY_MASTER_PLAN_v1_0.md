---
artifact: PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md
canonical_id: PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN
version: 1.0
status: CURRENT
authored_by: Claude Code (Sonnet 4.6, session 4C-0)
authored_on: 2026-05-19
role: >
  Governing campaign plan for Phase 4 — Ephemeris Accessibility.
  Covers sub-phases 4A through 4D. §B state tracker is the authoritative
  current-state surface for all Phase 4 sub-phases. Update §B at each
  sub-phase open/close; update §C changelog at each state change.
mirror_obligations: none (governance document; no mirror pair declared)
changelog:
  - v1.0 (2026-05-19, session 4C-0): Initial authoring. Phase 4A CLOSED;
    4B PENDING; 4C ACTIVE (brief authored, concurrent workstream declared);
    4D PENDING.
---

# Phase 4 — Ephemeris Accessibility: Campaign Master Plan v1.0

**Project:** MARSYS-JIS Jyotish Instrument
**Campaign scope:** Swiss Ephemeris infrastructure as a first-class instrument layer — queryable from the LLM pipeline, surfaced on the UI, and backing derived data assets.
**Authored:** 2026-05-19 (retroactive record; 4A closed prior to this file's creation)

---

## §A — Campaign Overview

Phase 4 makes the Swiss Ephemeris layer fully accessible to the instrument's three consumers: the LLM pipeline (retrieval tools), the Panchang UI surface, and future derived data services. It operates as a **concurrent workstream** alongside the active macro-phase (M5-A as of 2026-05-19), with each sub-phase isolated to its own branch or worktree per the two-stream policy established in 2026-05-17.

### Scope boundary

Phase 4 covers:
- Retrieval tools that wrap date-indexed ephemeris and Panchang data
- Schema migrations for date-indexed cloud SQL tables
- Python sidecar modules for deterministic astronomical computation
- UI surfaces that consume the above

Phase 4 does **not** cover:
- L2.5 synthesis layer modifications (that is M-phase territory)
- FORENSIC natal chart re-derivation (sealed at v8.0; EXTERNAL_COMPUTATION_REQUIRED if re-run needed)
- New macro-phase planning beyond the active M-phase arc (M1–M10)

### Architectural placement

```
L2.5  ──── MSR / UCN / CDLM / RM / CGM (synthesis, M-phase scope)
             ▲
             │
L1.5  ──── PANCHANG_DAILY (Phase 4C — this campaign)
             ▲          ▲
             │          │
L1    ──── EPHEMERIS_DAILY    FORENSIC
           (Phase 4A,          (natal snapshot,
            657K rows)          sealed v8.0)
             ▲          ▲
             └─ pyswisseph ─┘
```

---

## §B — Sub-Phase State Tracker

*This is the authoritative current-state surface for Phase 4. Update this table at each sub-phase open/close. Update §C changelog on each state change.*

| Sub-phase | Status | Branch / Worktree | Brief | Sessions | Notes |
|---|---|---|---|---|---|
| **4A** | **CLOSED** (2026-05-19, commit `bd41f13`) | main (merged) | — | ~1 | `query_ephemeris` RetrievalTool live; `ephemeris_daily` table backfilled (657K rows, 1900–2100) |
| **4B** | **PENDING** | TBD | TBD | ~2–3 | Sunrise derivation; Migration 059; TRUE_NODE→MEAN_NODE Rahu fix; `ephemeris_daily` rebuild. **Prerequisite for 4C.2.** |
| **4C** | **ACTIVE** (2026-05-19, session 4C-0) | `feature/phase-4c-panchang` / `/Users/Dev/Vibe-Coding/Apps/Panchang/` | `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md` | 4C-0 CLOSED; **4C-1 CLOSED** (2026-05-19, 4C-1-S2); 4C-2 GATED (phase_4b_closed); **4C-3 CLOSED** (2026-05-19) | `query_panchanga` RetrievalTool (tool 29) + `PANCHANG_DAILY` L1.5 asset + `/panchang` UI. 4C.3 closed: `query_panchanga` registered; sidecar /api/compute/panchanga live; planner R-TC rule + 10-probe routing gate (14/14 PASS); E2E smoke 3/3 PASS; engine-direct path (no SQL cache — 4C.2 gated). 4C.4 next (requires_brief_authoring). |
| **4D** | **PENDING** | TBD | TBD | ~2–3 | `query_transit_event` for ingress/aspect/conjunction/station search |

### State changelog

| Date | Change |
|---|---|
| 2026-05-19 | 4A CLOSED (commit `bd41f13`) — retroactively recorded at file creation |
| 2026-05-19 | 4B PENDING — sunrise derivation prerequisite; not yet started |
| 2026-05-19 | **4C ACTIVE** — brief authored (`PHASE_4C_PANCHANG_BRIEF_v1_0.md`); concurrent workstream declared in `CLAUDE.md §E` (Five workstreams); `PANCHANG_DAILY_v1_0` added to `CAPABILITY_MANIFEST.json`; 4C-0 governance session closed; 4C-1 next. Concurrent with M5-A. |
| 2026-05-19 | 4D PENDING — transit event search; not yet scoped |
| 2026-05-19 | **4C.1 CLOSED** — 4C-1-S2 session close. `panchang_engine` v1.0.0-S2: 9 special-yoga detectors (Sarvartha Siddhi, Amrit Siddhi, Ravi Pushya, Guru Pushya, Tripushkar, Dwipushkar, Siddha Yoga, Bhadra, Panchaka); `drik_panchang_v2.json` 30-day fixture; 30/30 Drik parity gate PASS; muhurat.py scaffold (6-event MVP); 150 tests pass; PANCHANG_DAILY status PLANNED→IN_DEVELOPMENT. 4C-1-S3 skipped (4C.1 closed cleanly). 4C.2 GATED on phase_4b_closed. |
| 2026-05-19 | **4C.3 CLOSED** — 4C-3 session close. `query_panchanga` RetrievalTool registered as tool 29 in `RETRIEVAL_TOOLS`; sidecar `routers/panchang.py` (POST /api/compute/panchanga + /range); `panchang_to_dict()` serializer (13/13 round-trip PASS); `query_panchanga.ts` (16/16 unit tests PASS, tsc 0 errors); planner R-TC routing rule + few-shot 4.25–4.27; `panchang_probe_set.json` (10 queries); `panchang_routing.test.ts` (14/14 PASS, CI-safe); E2E smoke 3/3 PASS; `CAPABILITY_MANIFEST` `expose_to_chat_confirmed=true`, `retrieval_tool=query_panchanga`, `runtime_path=engine_direct`; MP.2 mirror propagated; `mirror_enforcer` exit 0. Gate: 4C.3 CLOSED. 4C.4 next (requires_brief_authoring). |

---

## §C — Cross-Phase Dependencies

| Dependency | Affects | Detail |
|---|---|---|
| 4B closes Migration 059 (sunrise) | 4C.2 | `PANCHANG_DAILY` sunrise-anchors every anga. 4C.2 backfill cannot run until `ephemeris_daily` has correct sunrise columns from 4B. |
| 4A `ephemeris_daily` table | 4C.1, 4C.2 | `panchang_engine` reads `ephemeris_daily` for planetary positions. 4A closed → this dependency is MET. |
| 4C `panchang_daily` table | 4D scoping | Transit event search may share infrastructure with Panchang. Defer scoping until 4C.2 complete. |

---

## §D — Campaign Close Criteria

Phase 4 campaign closes when all four sub-phases close their respective acceptance gates:

- 4A: CLOSED (2026-05-19) ✓
- 4B: Migration 059 applies cleanly; `ephemeris_daily` rebuild complete; sunrise values validated
- 4C: All AC.4C.1–AC.4C.9 pass (per `PHASE_4C_PANCHANG_BRIEF_v1_0.md §8`); IS.8(b) red-team pass for Phase 4 close
- 4D: `query_transit_event` callable from planner; 10/10 probe set correct

Campaign close produces a `PHASE_4_CLOSE_v1_0.md` sealing artifact at `00_ARCHITECTURE/`.

---

*End of PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md v1.0. Live document — update §B state tracker and §C changelog at every sub-phase state change.*
