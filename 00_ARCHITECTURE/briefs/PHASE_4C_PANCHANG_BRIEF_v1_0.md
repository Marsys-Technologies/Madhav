---
artifact: PHASE_4C_PANCHANG_BRIEF_v1_0.md
canonical_id: PHASE_4C_PANCHANG_BRIEF
version: 1.0
status: CURRENT
authored_by: Claude Code (Sonnet 4.6, session 4C-0)
authored_on: 2026-05-19
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md
parent_phase: 00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md
mirror_obligations: >
  MP.1: Any change to §3 settled decisions must adapt-parity update .geminirules.
  MP.2: Phase 4C state changes must be reflected in .gemini/project_state.md.
changelog:
  - v1.0 (2026-05-19, session 4C-0): Initial authored. Governs Phase 4C.1–4C.9.
    4C.0 CLOSED IN THIS SESSION (8-item governance setup complete).
---

# Phase 4C — Panchang Module: Operational Brief v1.0

**Workstream:** Phase 4C (Panchang) — concurrent with M5-A
**Date:** 2026-05-19
**Governing plan:** `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md`
**Parent campaign:** Phase 4 Ephemeris Accessibility Master Plan

---

## §1 — Workstream Identity

Phase 4C is a **concurrent workstream** alongside active macro-phase M5-A. Precedent: Phase O Observatory (2026-05-04) and Chat V2 Big Bang (2026-05-16).

| Field | Value |
|---|---|
| Worktree | `/Users/Dev/Vibe-Coding/Apps/Panchang/` |
| Branch | `feature/phase-4c-panchang` |
| Base | `main` |
| Declared in | `CLAUDE.md §E` (Five workstreams) |
| Concurrent with | M5-A (PHASE_M5_PLAN_v1_0.md) |
| Isolation rule | Do not touch M5-A `may_touch` files from this branch |
| Parent Phase 4 plan | `00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md` |

**Prerequisite dependency:**
- Phase 4B (sunrise derivation, Migration 059, MEAN_NODE rebuild) must close before **4C.2** (schema + backfill anchors on sunrise).
- Phases 4C.0 and 4C.1 are 4B-independent and may proceed immediately.

---

## §2 — Phase Enumeration

| Sub-phase | Status | Sessions | Description |
|---|---|---|---|
| **4C.0** | **CLOSED** (2026-05-19, session 4C-0) | 1 | Brief & governance: seal plan, author brief, manifest, CLAUDE.md §E, schema doc |
| 4C.1 | NEXT | 3–4 | `panchang_engine` Python library: 5 angas, timings, special yogas, Drik validation gate |
| 4C.2 | PENDING (4B dep) | 2 | Schema migration, sidecar wiring, Bhubaneswar+Delhi backfill (~292K rows) |
| 4C.3 | PENDING | 1 | `query_panchanga` RetrievalTool: register, planner prompt, R-TC rule extension |
| 4C.4 | PENDING | 3–4 | `/panchang` page MVP: shell, primary strip, timings panel, planetary grid |
| 4C.5 | PENDING | 1–2 | Personalise dropdown: Tara Bala / Chandra Bala badges, localStorage persistence |
| 4C.6 | PENDING | 3–4 | Action 1: Muhurat Finder modal, YAML scoring rubric, star ratings, breakdown |
| 4C.7 | PENDING | 1–2 | Action 2: Calendar Export (.ics) — one-off export + subscribable feed |
| 4C.8 | PENDING | 1 | Action 3: Ask-Madhav prompt suggestions with Panchang context injection |
| 4C.9 | PENDING | 1 | Polish, Observatory panels, IS.8(b) red-team, Phase 4C close |

**Total estimate:** ~16–22 sessions concurrent with M5-A.

---

## §3 — Settled Decisions

Three native decisions settled 2026-05-19 at authoring session. These are **locked** — do not re-open without explicit native instruction.

### D1 — Default location: Bhubaneswar

The `/panchang` page loads with Bhubaneswar pre-selected on first visit. Location picker shows Bhubaneswar highlighted; user may override. Geographic IP detection not used. Consistency with project-canonical convention takes precedence.

### D2 — Muhurat MVP event scope: curated 6 events

Full §4.4.1 event set deferred to v2. MVP curated set:

| Category | Event |
|---|---|
| Life-cycle | Vivah (marriage) |
| Property | Griha Pravesh (housewarming), Property Purchase |
| Commerce | Vyapara (business start) |
| Travel | Yatra (travel) |
| Spiritual | Mantra Initiation |

All 6 have established Muhurta Shastra criteria. Extension events (Namakarana, Mundan, etc.) require additional research and land in v2.

### D3 — Calendar feed auth: signed time-boxed URLs

HMAC-signed URLs with 90-day expiry. Per-user token in query string. URL carries only `location` + `personalise=<chart_alias>` (hash of chart ID — no raw UUID, no PII). Rotation: native can revoke any subscription from Settings → Calendar Feeds. Re-issue on each "Subscribe" click supersedes prior tokens.

---

## §4 — Per-Phase Scope Summary

**4C.0 — Brief & governance (CLOSED)**
- Seal DRAFT plan → canonical (frontmatter flip, §10 decisions, git mv)
- Author this brief; add PANCHANG_DAILY_v1_0 to CAPABILITY_MANIFEST.json
- Update Phase 4 master plan §B state tracker; update CLAUDE.md §E (Four→Five)
- Create `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` schema document
- Update CURRENT_STATE + SESSION_LOG; propagate MP.1 + MP.2

**4C.1 — `panchang_engine` Python library**
- Pure Python module at `platform/sidecar/panchang_engine/`
- Modules: `angas.py`, `timings.py`, `special_yogas.py`, `planets.py`, `muhurat.py`, `shastra_tables.py`, `ayanamsha.py`
- Test suite: 30-day Drik Panchang validation fixture
- Gate: all 30 days match Drik to within tolerance (§5.3 of master plan)

**4C.2 — Schema + cache + sidecar**
- Migration: `panchang_daily` table (Cloud SQL)
- Extend `/api/compute/[type]` route with `panchanga` type
- Backfill: Bhubaneswar + Delhi for 1900–2100 (~292K rows, ~6hr batch)
- Gate: 100 sampled rows match fresh recomputation byte-for-byte

**4C.3 — `query_panchanga` RetrievalTool**
- `platform/src/lib/retrieve/query_panchanga.ts` registered in `RETRIEVAL_TOOLS`
- Update `PLANNER_PROMPT_v2_0.md §4` with few-shot example
- Extend R-TC rule to differentiate from `query_ephemeris`
- Gate: 10/10 curated probe set picks correct tool

**4C.4 — `/panchang` page MVP**
- Page shell + auth gate; date picker + location selector
- Primary strip (5 angas + Vara), timings panel, planetary grid
- Active special yogas list
- Gate: visual review vs Drik Panchang for 5 sample days; native sign-off

**4C.5 — Personalise dropdown + native overlay**
- Chart list dropdown from `Chart` table (filtered by user access)
- Tara Bala / Chandra Bala badges; native-aware yoga annotations
- localStorage persistence; "Clear personalisation" option
- Gate: switching personalisation correctly hydrates from FORENSIC

**4C.6 — Action 1: Muhurat Finder**
- `find_muhurat()` in `panchang_engine` with auditable YAML scoring rubric
- Frontend: modal form + results list with star ratings + breakdown
- Inline export + Ask-Madhav actions on each result
- Gate: 5 events × 30-day range, results pass acharya-grade review

**4C.7 — Action 2: Calendar Export**
- `/api/panchang/ics` route (one-off export)
- `/api/panchang/feed.ics` subscribable feed with signed URLs (D3)
- Per-event categorisation (auspicious/avoid) for colour-coding in calendar apps
- Gate: round-trip test through Google Calendar

**4C.8 — Action 3: Ask-Madhav prompt suggestions**
- Inline "💬" affordances on every Panchang element
- Pre-loaded prompt with hidden Panchang context block
- Deep link into `/clients/[id]/consume`
- Gate: chat receives Panchang context; planner references without extra tool call

**4C.9 — Polish, telemetry, close**
- Observatory panels: sidecar latency (p50/p95/p99) + cache hit ratio
- IS.8(b) red-team pass for Phase 4 close
- PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN §B → 4C CLOSED
- CLAUDE.md §E Phase 4C entry → COMPLETE
- SESSION_LOG Phase 4C close entry

---

## §5 — Per-Phase Acceptance Gates

Gates are specified in `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §6` (per sub-phase) and `§8` (whole-workstream ACs). Summary:

| Sub-phase | Gate condition |
|---|---|
| 4C.1 | 30/30 Drik validation days pass within tolerance (§5.3) |
| 4C.2 | 100 sampled cache rows byte-match fresh recomputation |
| 4C.3 | 10/10 planner probe set correct tool selection |
| 4C.4 | Visual review ≥5 days; native layout sign-off |
| 4C.5 | Personalise switch verifiably hydrates from FORENSIC |
| 4C.6 | Acharya-grade review ≥5 event types |
| 4C.7 | Google Calendar round-trip test passes |
| 4C.8 | Panchang context received in chat planner |
| 4C.9 | IS.8(b) red-team pass; Phase 4 state tracker CLOSED |

Whole-workstream ACs (AC.4C.1–AC.4C.9) are the final acceptance evidence per master plan §8.

---

## §6 — Hard Constraints

All Phase 4C sessions inherit these non-negotiable constraints from governing architecture:

- **B.1 — Layer separation:** `panchang_engine` returns computed facts only (L1.5). Any interpretation (e.g., "today is auspicious because...") goes through the LLM synthesis layer at L2.5+, never from the engine itself.
- **B.10 — No fabricated computation:** Engine values derive from `pyswisseph` + static classical tables. No value is invented or interpolated without an explicit computation trace. `[EXTERNAL_COMPUTATION_REQUIRED]` marks any value that needs Swiss Ephemeris but isn't yet computed.
- **B.11 — Whole-Chart-Read protocol:** Panchang personalisation reads FORENSIC read-only. It does not synthesise from FORENSIC — that is L2.5 territory.
- **Sealed engine discipline:** `panchang_engine` is a facts-computation module. It must never contain LLM calls, probabilistic inference, or interpretive logic. Shastra lookup tables are deterministic; scoring rubric weights are configured in YAML, not inferred.
- **FORENSIC isolation:** Panchang reads FORENSIC only on personalise overlay (birth Nakshatra + Lagna + active Dasha). It never writes to, reshapes, or caches FORENSIC data.

---

## §7 — Mirror Discipline

Phase 4C touches two active mirror pairs per `manifest_overrides.yaml`:

- **MP.1 (CLAUDE.md ↔ .geminirules):** Any change to CLAUDE.md §E (workstream status, description, sessions) must adapt-parity update `.geminirules` in the same session.
- **MP.2 (CAPABILITY_MANIFEST.json ↔ .gemini/project_state.md):** Any change to `CAPABILITY_MANIFEST.json` (e.g., adding `PANCHANG_DAILY_v1_0`, promoting its status from PLANNED→CURRENT) must adapt-parity update `.gemini/project_state.md` in the same session.

`mirror_enforcer.py` (manifest mode) exit 0 is required at every Phase 4C session close.

---

## §8 — Close Criteria for the Whole Phase 4C Campaign

| AC | Criterion | Evidence |
|---|---|---|
| AC.4C.1 | `panchang_engine` Drik validation: 30/30 days | `tests/fixtures/drik_panchang_30_days.json` all pass |
| AC.4C.2 | `panchang_daily` covers Bhubaneswar + Delhi 1900–2100 | `SELECT COUNT(*) FROM panchang_daily` ≥ 292,000 |
| AC.4C.3 | `query_panchanga` planner selection correct | 10/10 probe set |
| AC.4C.4 | `/panchang` page correct + Drik-parity for 5 days | Screenshots + native sign-off |
| AC.4C.5 | Personalise overlay correct from FORENSIC | Manual switch test |
| AC.4C.6 | Muhurat Finder acharya-grade for 5 event types | Native + acharya review |
| AC.4C.7 | Calendar export round-trips through Google Calendar | Manual test |
| AC.4C.8 | Ask-Madhav prompts carry Panchang context | Chat planner test |
| AC.4C.9 | IS.8(b) red-team pass; Phase 4 close artifact authored | Red-team report |

Phase 4C does not claim COMPLETE until all 9 ACs pass and `SESSION_LOG.md` contains the Phase 4C close entry with master plan §B state → CLOSED.

---

*End of PHASE_4C_PANCHANG_BRIEF_v1_0.md. Authored 2026-05-19, session 4C-0. Governing plan: `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md`. Next session: 4C-1 (panchang_engine Python module).*
