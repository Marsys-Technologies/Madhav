---
artifact: CLAUDECODE_BRIEF.md (R3 instance)
status: PENDING
authored_on: 2026-04-30
authored_by: Cowork (Opus)
authored_during: "Portal Redesign — R3 Build mode upgrade"
governing_clause: CLAUDE.md §C item #0 — overrides items 1–11 for the duration of the session
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
session_class: Portal Redesign — UX workstream inside M2 Corpus Activation
exec_brief_to_execute: EXEC_BRIEF_PORTAL_REDESIGN_R3_BUILD_UPGRADE_v1_0.md
phase_id: R3
parent_artifacts:
  - 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md (CURRENT)
  - 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md (LIVING)
worktree_path: ~/Vibe-Coding/Apps/Madhav-r3
branch: redesign/r3-build-upgrade
parallelizable_with: [R7]
unblocks: []
---

# CLAUDECODE_BRIEF — Portal Redesign R3 Build mode upgrade

## How this file got here

Copied into the R3 worktree from the project's per-phase brief pool. Renamed from `CLAUDECODE_BRIEF_R3.md` → `CLAUDECODE_BRIEF.md` to activate `CLAUDE.md §C item #0`.

## Governing scope

R3 brings the per-client Build chat to feature parity with the Consume chat shell, then composes the existing build widgets into a right pane. Two parts internally: R3a (hook-compatibility audit, the gate) and R3b (UI swap + right-pane composition). If the audit's verdict is C (substantial adapter needed), R3 splits — R3b becomes its own session.

Executes `EXEC_BRIEF_PORTAL_REDESIGN_R3_BUILD_UPGRADE_v1_0.md`. Produces `00_ARCHITECTURE/PORTAL_REDESIGN_R3_REPORT_v1_0.md`.

## Required reads, in order

1. This file.
2. `EXEC_BRIEF_PORTAL_REDESIGN_R3_BUILD_UPGRADE_v1_0.md` — the phase brief. Pay attention to §1 (R3a audit comes BEFORE any code change) and §5 (R7 coordination note — what to do if R7 is running concurrently).
3. `00_ARCHITECTURE/PORTAL_REDESIGN_R2_REPORT_v1_0.md` — R2's closure report. The Build Room's CTA in Chart Profile is the entry point R3 inherits; verify R2's CTA already points at `/clients/{id}/build`.
4. `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` — §3.1 Surface 4 (Build mode three-pane cockpit), §4.3.3 (R3 sub-phase decomposition).
5. `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` — §2 + §3 R3 row.
6. The Consume chat shell as the model: `platform/src/components/consume/ConsumeChat.tsx` and `platform/src/components/chat/ChatShell.tsx`. R3 mirrors this composition for Build.
7. The current Build chat being replaced: `platform/src/components/build/BuildChat.tsx`. R3 wholesale replaces this file.
8. The five right-pane widgets being composed (REUSE, do not modify): `JourneyStrip.tsx`, `BriefPanel.tsx`, `InsightCards.tsx`, `MirrorPairsTable.tsx`, `PyramidStatusPanel.tsx` — all in `platform/src/components/build/`.
9. Standard `CLAUDE.md §C` items 1–11.

## Pre-flight gate

In addition to the gate inside the EXEC_BRIEF:

1. R0 closed.
2. R2 closed (`PORTAL_REDESIGN_R2_REPORT_v1_0.md` exists with `status: COMPLETE`).
3. No in-flight phase shares a `may_touch` glob with R3. R7 is the only other phase that may be in flight; R3 and R7 are parallelizable per VISION §4.3 — verify R7 (if running) hasn't already touched `BuildChat.tsx`.
4. Working tree clean. Branch `redesign/r3-build-upgrade`.

## Acceptance criteria

Session does not claim close until ALL of:

1. R3a audit committed at `00_ARCHITECTURE/PORTAL_REDESIGN_R3_HOOK_COMPAT_AUDIT_v1_0.md` with one of three verdicts (A direct compat, B thin adapter ≤80 lines, C substantial — splits).
2. If verdict A or B: R3b deliverables landed (BuildChat replaced, BuildRightPane composed, build page updated).
3. If verdict C: this session closes after R3a committed; R3b is authored as a follow-up brief and committed alongside the audit. The session closes acknowledging the split.
4. EXEC_BRIEF §3 tests pass (unit + E2E + governance scripts exit 0).
5. Test baseline preserved (no Consume regressions, no chat shell regressions, no build widget regressions).
6. Closure report `00_ARCHITECTURE/PORTAL_REDESIGN_R3_REPORT_v1_0.md` at `status: COMPLETE`.
7. Tracker §3 R3 row → `status: closed`. If R3 split into R3a/R3b, the tracker row's `sub_phases` array reflects each sub-phase's status.
8. SESSION_LOG appended.
9. This file flipped to `status: COMPLETE`.

## R7 coordination

R7 is the polish phase running in `redesign/r7-polish` worktree alongside R3. Per VISION §4.3 R3+R7 are parallelizable. Two operational rules:

- If R7's worktree shows it has touched `BuildChat.tsx`, halt and reconcile with the native — that's a collision.
- After R3b lands, R3's closure report adds a `follow_ups` block listing Build-side polish items R7 should pick up (a11y on the new ChatShell instance, mobile pass on the three-pane layout, etc.). R7 picks these up as a small follow-up commit on `redesign/r7-polish` before its PR opens.

## One-line summary

Bring per-client Build to feature parity with Consume — same chat shell, same hook stack, plus the right-pane widgets composed.

---
