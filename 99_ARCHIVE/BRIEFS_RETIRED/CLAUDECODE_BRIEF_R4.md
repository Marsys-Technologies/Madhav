---
artifact: CLAUDECODE_BRIEF.md (R4 instance)
status: COMPLETE
authored_on: 2026-04-29
authored_by: Cowork (Opus)
authored_during: "Portal Redesign — R4 Consume polish"
governing_clause: CLAUDE.md §C item #0 — overrides items 1–11 for the duration of the session
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
session_class: Portal Redesign — UX workstream inside M2 Corpus Activation
exec_brief_to_execute: EXEC_BRIEF_PORTAL_REDESIGN_R4_CONSUME_POLISH_v1_0.md
phase_id: R4
parent_artifacts:
  - 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md (CURRENT, post-R0)
  - 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md (LIVING)
worktree_path: ~/Vibe-Coding/Apps/Madhav-r4
branch: redesign/r4-consume-polish
parallelizable_with: [R1, R2, R3, R5, R6]
trace_fix_dependency: "tracker.trace_fix_status MUST be {on_hold | merged} — see VISION §4.3.2"
---

# CLAUDECODE_BRIEF — Portal Redesign R4 Consume polish

## How this file got here

Copied into the R4 worktree from the project's per-phase brief pool. Renamed to activate `CLAUDE.md §C item #0`.

## Governing scope

Polishes the existing mature Consume tab — adds report gallery, trace drawer, audience-tier picker, prediction-log action. **Additive only — does not rebuild.** Executes `EXEC_BRIEF_PORTAL_REDESIGN_R4_CONSUME_POLISH_v1_0.md`. Produces `00_ARCHITECTURE/PORTAL_REDESIGN_R4_REPORT_v1_0.md`.

## Required reads, in order

1. This file.
2. `EXEC_BRIEF_PORTAL_REDESIGN_R4_CONSUME_POLISH_v1_0.md` — pay attention to the **Critical scope note on TracePanel.tsx** in the scope declaration: R4 extracts the panel's render-body into a sub-component but does NOT modify trace data flow.
3. `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` — §3.1 Surface 5, §4.3.2 (trace-fix co-existence — verify status before proceeding).
4. `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` — §2 `trace_fix_status` field is the gate; §3 R4 row and `trace_fix_serialization_rule`.
5. Standard `CLAUDE.md §C` items 1–11.

## Pre-flight gate

In addition to the gate inside the EXEC_BRIEF:

1. R0 closed.
2. **`tracker.trace_fix_status` is `on_hold` or `merged`. If `in_flight`, HALT** — collision per VISION §4.3.2 reapplies; serialize R4 against the trace fix.
3. No other in-flight phase shares a `may_touch` glob with R4.
4. Working tree clean. Branch `redesign/r4-consume-polish`.

If any fail: emit `pre_flight_failure` and halt. The trace_fix_status check is load-bearing — do not bypass.

## Acceptance criteria

Session does not claim close until ALL of:
1. EXEC_BRIEF §1–§4 components landed (ReportGallery, TraceDrawer, TierPicker, LogPredictionAction).
2. EXEC_BRIEF §5 tests pass.
3. Closure report at `status: COMPLETE`.
4. Tracker §3 R4 row flipped to `status: closed`.
5. **If trace_fix_status flipped from on_hold → in_flight DURING R4 execution**, closure report MUST surface this in `follow_ups` so trace-fix work picks up against the new `<TraceDrawer>` rather than the retired always-on panel.
6. Governance scripts exit 0.
7. SESSION_LOG appended.
8. This file flipped to `status: COMPLETE`.

## One-line summary

Take Consume from "good v3" to "polished v3.1" with a gallery, a drawer, a tier flip, and a prediction-log shortcut — additive only.

---
