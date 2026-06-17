---
artifact: CLAUDECODE_BRIEF.md (R2 instance)
status: COMPLETE
authored_on: 2026-04-29
authored_by: Cowork (Opus)
authored_during: "Portal Redesign — R2 Chart Profile (keystone surface)"
governing_clause: CLAUDE.md §C item #0 — overrides items 1–11 for the duration of the session
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
session_class: Portal Redesign — UX workstream inside M2 Corpus Activation
exec_brief_to_execute: EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE_v1_0.md
phase_id: R2
parent_artifacts:
  - 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md (CURRENT, post-R0)
  - 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md (LIVING)
worktree_path: ~/Vibe-Coding/Apps/Madhav-r2
branch: redesign/r2-chart-profile
parallelizable_with: [R1, R4, R5, R6]
unblocks: [R3]                          # R3 brief authors after R2 closes
---

# CLAUDECODE_BRIEF — Portal Redesign R2 Chart Profile

## How this file got here

Copied into the R2 worktree from the project's per-phase brief pool. Renamed from `CLAUDECODE_BRIEF_R2.md` → `CLAUDECODE_BRIEF.md` to activate `CLAUDE.md §C item #0`.

## Governing scope

R2 is the **keystone** of the redesign — it lands the Chart Profile page that turns the silent redirect at `/clients/[id]` into the most legible surface in the portal. Executes `EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE_v1_0.md` end-to-end. Produces `00_ARCHITECTURE/PORTAL_REDESIGN_R2_REPORT_v1_0.md` as closure.

R2 has internal sub-phase decomposition (R2a renderer, R2b rooms+rail, R2c page composition) — see VISION §4.3.3. Single Claude Code session typically lands R2a + R2b in parallel internally and R2c as the composition step. If session-time is tight, R2 splits across two sessions: first R2a + R2b, second R2c.

## Required reads, in order

1. This file.
2. `EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE_v1_0.md` — the brief. Pay attention to §2.1 RasiChartSVG (B.10 visual verification is required and not optional) and §4.5 manual acharya-grade visual verification.
3. `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` — §3.1 Surface 3 (the keystone), §3.2 (theme zones — R2 is the only Bridge zone), §4.3.3 (sub-phase decomposition).
4. `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §1` — the canonical placements the rasi renderer must match. Visual verification compares the rendered chart against this file's L1 facts.
5. `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` — §2 + §3 R2 row.
6. Standard `CLAUDE.md §C` items 1–11.

## Pre-flight gate

In addition to the gate inside the EXEC_BRIEF:

1. R0 closed.
2. No in-flight phase shares a `may_touch` glob with R2.
3. Working tree clean. Branch `redesign/r2-chart-profile`.
4. Phase 14C `l1_structured_*` tables are populated for at least the test chart (Abhisek Mohanty) — the renderer reads from them, NOT from raw markdown.

If any fail: emit `pre_flight_failure` and halt.

## Acceptance criteria

Session does not claim close until ALL of:
1. EXEC_BRIEF §2 components landed (RasiChartSVG, ChartHero, RoomCard, ProfileSideRail, DashaCountdown, page composition).
2. EXEC_BRIEF §3 subtle ClientCard href edit landed.
3. EXEC_BRIEF §4 tests pass — Playwright + unit + visual diff.
4. **EXEC_BRIEF §4.5 acharya-grade visual verification PASSED** — the rendered Abhisek chart matches `FORENSIC_ASTROLOGICAL_DATA_v8_0.md §1` placements. This is a B.10 compliance check; do not skip.
5. Closure report at `status: COMPLETE`.
6. Tracker §3 R2 row flipped to `status: closed`.
7. Governance scripts exit 0.
8. SESSION_LOG appended.
9. This file flipped to `status: COMPLETE`.

## R3 unblock signal

R2's closure report MUST include a follow-up note: "R3 brief now authorable — Build mode hook-compatibility audit can proceed." This is the breadcrumb the next session uses to know R3 is unblocked.

## One-line summary

Land the keystone Chart Profile page — hero with rasi chart, three rooms, side rail, mandala backdrop — using only L1 facts and the existing brand spine.

---
