---
artifact: CLAUDECODE_BRIEF.md (R1 instance)
status: COMPLETE
authored_on: 2026-04-29
authored_by: Cowork (Opus)
authored_during: "Portal Redesign — R1 Roster modernization"
governing_clause: CLAUDE.md §C item #0 — overrides items 1–11 for the duration of the session
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
session_class: Portal Redesign — UX workstream inside M2 Corpus Activation
exec_brief_to_execute: EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER_v1_0.md
phase_id: R1
parent_artifacts:
  - 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md (CURRENT, post-R0)
  - 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md (LIVING)
worktree_path: ~/Vibe-Coding/Apps/Madhav-r1
branch: redesign/r1-roster
parallelizable_with: [R2, R4, R5, R6]
---

# CLAUDECODE_BRIEF — Portal Redesign R1 Roster modernization

## How this file got here

This file was copied into the R1 worktree from the project's central pool of per-phase CLAUDECODE_BRIEFs (see `PORTAL_REDESIGN_PARALLEL_RUNBOOK_v1_0.md` at the parent repo root). One worktree, one CLAUDECODE_BRIEF, one Claude Code session. Renaming this file from `CLAUDECODE_BRIEF_R1.md` to `CLAUDECODE_BRIEF.md` is what activates it for `CLAUDE.md §C item #0`.

## Governing scope

Executes `EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER_v1_0.md` end-to-end. Produces `00_ARCHITECTURE/PORTAL_REDESIGN_R1_REPORT_v1_0.md` as closure.

## Required reads, in order

1. This file — orientation.
2. `EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER_v1_0.md` — the brief. `may_touch` / `must_not_touch` are binding per `GOVERNANCE_INTEGRITY_PROTOCOL §F`.
3. `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` — §3.1 Surface 2 (Roster) for the design intent; §4.3 for parallelism rules.
4. `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` — §2 to confirm R0 closed, R1 in `post_r0_parallel_ready`; §3 R1 row to confirm `status: authored`. Read §3 rows for any other phase currently `in_flight` and verify their `may_touch` does not intersect R1's.
5. Standard `CLAUDE.md §C` items 1–11.

## Pre-flight gate

In addition to the gate inside the EXEC_BRIEF:

1. R0 closed (tracker §2 `vision_status: CURRENT`, §3 R0 row `status: closed`).
2. No in-flight phase shares a `may_touch` glob with R1. Specifically R1 must not run alongside R7 (R7 hasn't started yet anyway).
3. Working tree clean. Branch `redesign/r1-roster` checked out.
4. AppShell + ZoneRoot from R0 are imported and working in `/dashboard`.

If any fail: emit `pre_flight_failure` and halt.

## Acceptance criteria

Session does not claim close until ALL of:
1. EXEC_BRIEF §1–§5 deliverables landed.
2. EXEC_BRIEF §6 tests pass.
3. Closure report `00_ARCHITECTURE/PORTAL_REDESIGN_R1_REPORT_v1_0.md` at `status: COMPLETE`.
4. Tracker §3 R1 row flipped to `status: closed` with session_id, closed_at, follow_ups.
5. `mirror_enforcer.py`, `drift_detector.py`, `schema_validator.py` exit 0.
6. SESSION_LOG.md appended.
7. This file flipped to `status: COMPLETE`.

## One-line summary

Modernize the Roster — stats ribbon, filters, grid/table toggle, upgraded ClientCard, zero-state wizard — composed atop existing primitives.

---
