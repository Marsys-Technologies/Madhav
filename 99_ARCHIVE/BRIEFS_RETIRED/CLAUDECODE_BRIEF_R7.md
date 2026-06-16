---
artifact: CLAUDECODE_BRIEF.md (R7 instance)
status: COMPLETE
authored_on: 2026-04-30
authored_by: Cowork (Opus)
authored_during: "Portal Redesign — R7 Polish (final phase)"
governing_clause: CLAUDE.md §C item #0 — overrides items 1–11 for the duration of the session
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
session_class: Portal Redesign — UX workstream inside M2 Corpus Activation (final phase)
exec_brief_to_execute: EXEC_BRIEF_PORTAL_REDESIGN_R7_POLISH_v1_0.md
phase_id: R7
parent_artifacts:
  - 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md (CURRENT)
  - 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md (LIVING)
worktree_path: ~/Vibe-Coding/Apps/Madhav-r7
branch: redesign/r7-polish
parallelizable_with: []                                  # R7 runs alone
unblocks: []                                             # final phase of the redesign
---

# CLAUDECODE_BRIEF — Portal Redesign R7 Polish (final phase)

## How this file got here

Copied into the R7 worktree from the project's per-phase brief pool. Renamed from `CLAUDECODE_BRIEF_R7.md` → `CLAUDECODE_BRIEF.md` to activate `CLAUDE.md §C item #0`.

## Governing scope

R7 is the polish pass that closes the redesign workstream. Five deliverables: accessibility audit (Lighthouse a11y ≥ 95 every surface), mobile pass (375/414/768 px), animation timings, perceived-perf, feature flag cleanup. Executes `EXEC_BRIEF_PORTAL_REDESIGN_R7_POLISH_v1_0.md`. Produces `00_ARCHITECTURE/PORTAL_REDESIGN_R7_REPORT_v1_0.md`.

**No new feature work in R7.** Every edit fixes a violation, an overflow, a timing issue, a perceived-perf observation, or removes a flag.

## Required reads, in order

1. This file.
2. `EXEC_BRIEF_PORTAL_REDESIGN_R7_POLISH_v1_0.md` — the brief. The five deliverables and their acceptance criteria are binding.
3. `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` — particularly §5 acceptance criteria (the redesign-is-DONE checklist that R7 closes against).
4. `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` — §2 to confirm R0–R6 all closed; §3 R7 row should be `status: authored`.
5. `00_ARCHITECTURE/PORTAL_REDESIGN_R{0,1,2,3,4,5,6}_REPORT_v1_0.md` — read each closure report's `follow_ups` block. R7 picks up any deferred polish items they captured.
6. Standard `CLAUDE.md §C` items 1–11.

## Pre-flight gate

Halt if any fail:

1. R0–R6 all closed (tracker §3 each row `status: closed`).
2. All five phase branches merged to `main` (the squash-merge commits are in `git log --oneline main`).
3. Vision `status: CURRENT`.
4. `npm test` passes on `main` baseline. Capture the test count for comparison at close.
5. Working tree clean. Branch `redesign/r7-polish`.

## Acceptance criteria

Session does not claim close until ALL of:

1. Lighthouse a11y ≥ 95 on every redesign surface (Roster, Chart Profile, Build, Consume, Cockpit, Timeline, Login). Capture JSON reports.
2. Mobile pass at 375 / 414 / 768 px on every surface; no overflow, no unreachable controls.
3. Animation timings audited and tuned (Mandala rotation ≥ 60 s; ProgressBar 200–400 ms ease-out; streaming dots 600–1000 ms cycle; ascend transition on Build/Consume entry ≤ 200 ms).
4. Skeletons (not spinners) on every initial-load surface. Optimistic UI on Log Prediction and Log Event.
5. All `PORTAL_REDESIGN_R*_ENABLED` flags removed from `feature_flags.ts`, env files, and `FEATURE_FLAG_STATUS.md`. Cloud Run gcloud command captured in closure report.
6. Test baseline preserved (no regressions).
7. Governance scripts exit 0.
8. Closure report at `status: COMPLETE`.
9. Tracker §3 R7 row → `status: closed`. §2 → `active_phase: null`, `redesign_workstream_status: COMPLETE`.
10. Vision changelog entry added.
11. SESSION_LOG appended.
12. This file flipped to `status: COMPLETE`.

## Special note for R7

R7 is the redesign workstream's last phase. After R7 closes, the user's next session can move the tracker from `LIVING` to `ARCHIVED` and add a sealing entry. R7 itself does NOT archive the tracker — leave that for a deliberate close-out session.

## One-line summary

Polish every surface — a11y, mobile, motion, perf, flag cleanup — and close the redesign workstream.

---
