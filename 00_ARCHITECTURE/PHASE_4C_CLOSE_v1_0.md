---
artifact: PHASE_4C_CLOSE_v1_0.md
version: 1.0
status: CLOSED
produced_during: Phase-4C-9 (2026-05-20)
produced_by_session: 4C-9
role: >
  Phase 4C Wave 1 close artifact. Comprehensive closeout summary of the Panchang
  Module concurrent workstream. Documents all sub-phases, commits, test counts, and
  deferred work. Seals Wave 1 (4C-0 through 4C-9).
changelog:
  - v1.0 (2026-05-20, 4C-9): Initial — Wave 1 close.
---

# Phase 4C — Panchang Module — Wave 1 Close

**Date:** 2026-05-20
**Session:** 4C-9
**Branch:** `feature/phase-4c-panchang`
**Status:** WAVE_1_COMPLETE — pending split-PR merge to main

---

## §1 — Wave 1 Outcome Summary

Phase 4C delivered a production-ready Panchang instrument in 9 sessions (4C-0 through 4C-9)
running concurrently with M5-A. The `/panchang` UI surface is live on the branch with:
- Engine v1.0.0-S3 (Swiss Ephemeris via ephem; 5 angas + special yogas + planetary positions)
- `query_panchanga` RetrievalTool registered and expose_to_chat confirmed
- Personalise overlay (Tara Bala + Chandra Bala for any chart)
- Muhurat Finder (6 curated events × YAML-tunable weights × 90-day range)
- iCal export (single-day download + HMAC-signed 90-day subscribable feed)
- Ask-Madhav deep links with 10 KB context injection + planner bypass rule

Drik parity: **30/30** on engine v1.0.0-S3 (AC.4C1.2 verified session 4C-1-S2).
Red-team: IS.8(b) PASS 5/5 (RT.4C.1 WARN-acceptable; RT.4C.2-5 PASS) — session 4C-9.
Acharya review: LLM-derived CANARY PASS (4C-6-S4); real acharya panel review is M10-territory post-merge.

---

## §2 — Sub-phase close summary

| Sub-phase | Status | Close artifact | Key commit | Notes |
|---|---|---|---|---|
| 4C-0 | CLOSED | (sealed in plan) | `4ae624e` | Governance setup; plan sealed; CAPABILITY_MANIFEST entry; brief authorised |
| 4C-1 | CLOSED | `PHASE_4C_1_CLOSE_v1_0.md` | `733f77b` | panchang_engine v1.0.0; 30/30 Drik parity; 167 pytests PASS |
| 4C-2 | GATED | — | — | SQL cache layer; gated on Phase 4B (MEAN_NODE rebuild + Migration 059); deferred |
| 4C-3 | CLOSED | (in SESSION_LOG) | (4C-3 commits) | query_panchanga RetrievalTool; engine-direct runtime_path; expose_to_chat confirmed |
| 4C-4 | CLOSED | `PHASE_4C_4_CLOSE_v1_0.md` | `c1f15d1` | /panchang UI scaffolding; PrimaryStrip + PlanetaryGrid + SpecialYogasList |
| 4C-5 | CLOSED | (in SESSION_LOG) | (4C-5 commits) | Personalise overlay; Tara Bala + Chandra Bala; chart selector; 100 TS tests |
| 4C-6 | CLOSED | `PHASE_4C_6_CLOSE_v1_0.md` | `8036312` | Muhurat Finder engine + UI + scoring weights YAML; 31 engine tests; E2E 12 tests; acharya CANARY PASS |
| 4C-7 | CLOSED | (in SESSION_LOG) | `0ed5236` | iCal export; HMAC-signed 90-day subscribable feed; 39 new tests (22+17) |
| 4C-8 | CLOSED | (in SESSION_LOG) | `5a69aff` | AskMadhavLink; context injection; planner bypass rule; 20 new tests; 167 total PASS |
| 4C-9 | CLOSED | this file | `7180523` (red-team) | Polish pass; Observatory panels; IS.8(b) red-team 5/5; CLAUDE.md v2.7; queue closed |

### Skipped sub-phases
- **4C-1-S3** — skipped (4C-1 completed in 2 sessions, S3 not needed)
- **4C-2** — gated (SQL cache layer pending Phase 4B; status `CURRENT_ENGINE_DIRECT` in CAPABILITY_MANIFEST)

---

## §3 — Test totals at Wave 1 close

| Suite | Count | Status |
|---|---|---|
| panchang_engine pytest (Python sidecar) | 230 | PASS |
| TypeScript panchang UI tests (Jest) | 151 | PASS (as of 4C-9 Item 2) |
| Muhurat Finder E2E tests | 12 | PASS |
| iCal builder tests | 22 | PASS |
| HMAC sign_url tests | 17 | PASS |
| **Total** | **432** | **PASS** |

---

## §4 — Drik parity bottom line

Engine v1.0.0-S3: **30/30** verified against Drik Panchang reference.
All 5 angas (Tithi, Vara, Nakshatra, Yoga, Karana) + Sunrise/Sunset/Moonrise/Moonset
correct for the 30-day sample set (Bhubaneswar, January–February 2026).

---

## §5 — Red-team (IS.8(b)) summary

Conducted in session 4C-9. 5 probes, 5 verdicts:

| Probe | Topic | Verdict |
|---|---|---|
| RT.4C.1 | Layer purity — UI derivations vs engine ownership | WARN (acceptable — minor UI formatting, not engine logic) |
| RT.4C.2 | B.10 discipline — displayed values traceable to engine + ephemeris | PASS |
| RT.4C.3 | Personalise overlay classical correctness | PASS |
| RT.4C.4 | Muhurat scoring acharya validity (canary) | PASS |
| RT.4C.5 | iCal / feed URL PII surface | PASS |

Finding docs: `00_ARCHITECTURE/RED_TEAM/RT_4C_1_FINDING.md` through `RT_4C_5_FINDING.md`.

---

## §6 — Telemetry baseline

From Observatory panels (4C-9 Item 2; populated from session runs):
- Panchang sidecar latency: see `PanchangLatencyPanel` in Observatory dashboard
- Cache layer: pending Phase 4B (panel shows "Cache layer pending Phase 4B" placeholder)
- Muhurat 90-day range: 0.68s (4C-6-S1 Item 9 — 44× faster than 30s estimate)

---

## §7 — Deferred work

| Item | Reason | Resolution path |
|---|---|---|
| 4C-2 SQL cache + backfill | Phase 4B (MEAN_NODE rebuild + Migration 059) not yet landed | After Phase 4B closes, 4C-2 can run; flip CAPABILITY_MANIFEST to `CURRENT` with `runtime_path: cached` |
| UI polish v2 items | 2-hour budget cap in 4C-9 Item 1 | `00_ARCHITECTURE/PHASE_4C_FOLLOWUPS_v1_0.md` enumerates deferred items |
| Acharya panel real review | M10-territory (post-merge) | Archangel-grade acharya review of Muhurat scoring after production use data available |
| CLAUDE.md amendment timing | Applied on branch (pre cherry-pick) | Wave 2 note: amendment already applied on feature branch; will arrive on main via Phase 4C PR |

---

## §8 — CAPABILITY_MANIFEST status

`PANCHANG_DAILY_v1_0` status flipped to `CURRENT_ENGINE_DIRECT` in `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
(4C-9 Item 7). Will become plain `CURRENT` with `runtime_path: cached` after 4C-2 lands.

---

## §9 — Next steps for native

1. **Run split-PR procedure** per `HANDOFF_WAVE_1.md` at worktree root.
2. **PR 1:** Cherry-pick Conductor commits → `feature/conductor-to-main` → merge to main.
3. **PR 2:** Phase 4C close → `feature/phase-4c-panchang` → merge to main.
4. Optionally: start Wave 2 queue (M5-A, Phase 4B, Phase 4D) after PR 1 merges.

---

*End of PHASE_4C_CLOSE_v1_0.md v1.0 — authored 2026-05-20, session 4C-9.*
*Phase 4C Wave 1 COMPLETE. Pending: split-PR merge to main.*
