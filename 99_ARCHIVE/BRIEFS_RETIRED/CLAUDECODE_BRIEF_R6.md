---
artifact: CLAUDECODE_BRIEF.md (R6 instance)
status: COMPLETE
authored_on: 2026-04-29
authored_by: Cowork (Opus)
authored_during: "Portal Redesign — R6 Cockpit elevation"
governing_clause: CLAUDE.md §C item #0 — overrides items 1–11 for the duration of the session
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
session_class: Portal Redesign — UX workstream inside M2 Corpus Activation
exec_brief_to_execute: EXEC_BRIEF_PORTAL_REDESIGN_R6_COCKPIT_v1_0.md
phase_id: R6
parent_artifacts:
  - 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md (CURRENT, post-R0)
  - 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md (LIVING)
worktree_path: ~/Vibe-Coding/Apps/Madhav-r6
branch: redesign/r6-cockpit
parallelizable_with: [R1, R2, R3, R5]
---

# CLAUDECODE_BRIEF — Portal Redesign R6 Cockpit elevation

## How this file got here

Copied into the R6 worktree from the project's per-phase brief pool. Renamed to activate `CLAUDE.md §C item #0`.

## Governing scope

Promotes the Cockpit from "buried behind avatar dropdown" to first-class AppShell rail item; adds `<ActiveChartsWidget>` to `<CockpitGrid>`. **Cockpit internals untouched** beyond adding the new widget. Executes `EXEC_BRIEF_PORTAL_REDESIGN_R6_COCKPIT_v1_0.md`. Produces `00_ARCHITECTURE/PORTAL_REDESIGN_R6_REPORT_v1_0.md`.

## Required reads, in order

1. This file.
2. `EXEC_BRIEF_PORTAL_REDESIGN_R6_COCKPIT_v1_0.md` — short brief; read it fully.
3. `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` — §3.1 Surface 6.
4. `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` — §2 + §3 R6 row.
5. Standard `CLAUDE.md §C` items 1–11.

## Pre-flight gate

In addition to the gate inside the EXEC_BRIEF:

1. R0 closed (the `/build → /cockpit` rename and the Cockpit rail-item must already exist from R0 — R6 verifies and tightens, not from-scratch creates).
2. No in-flight phase shares a `may_touch` glob with R6. R6's `may_touch` is small (just the rail visual order, the new widget, and a one-touch BuildHeader cleanup) so collision risk is low.
3. Working tree clean. Branch `redesign/r6-cockpit`.

If any fail: emit `pre_flight_failure` and halt.

## Acceptance criteria

Session does not claim close until ALL of:
1. EXEC_BRIEF §1 rail promotion verified (or applied if R0 left it suboptimal).
2. EXEC_BRIEF §2 `<ActiveChartsWidget>` landed on `<CockpitGrid>` with click-through to `/clients/[id]`.
3. EXEC_BRIEF §3 BuildHeader cleanup verified.
4. EXEC_BRIEF §4 tests pass.
5. Closure report at `status: COMPLETE`.
6. Tracker §3 R6 row flipped to `status: closed`.
7. Governance scripts exit 0.
8. SESSION_LOG appended.
9. This file flipped to `status: COMPLETE`.

## R7 unblock signal

R6's closure report MUST include a follow-up note: "R7 brief now authorable — polish pass scope is now fully defined by what landed in R0–R6." This is the breadcrumb for the next session to author R7.

## One-line summary

Make the Cockpit a first-class destination from anywhere in the app, plus surface live links into per-chart profiles via one new widget.

---
