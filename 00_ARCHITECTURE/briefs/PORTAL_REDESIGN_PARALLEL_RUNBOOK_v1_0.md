---
artifact: PORTAL_REDESIGN_PARALLEL_RUNBOOK
version: 1.0
status: ACTIVE
authored_by: Cowork (Opus)
authored_at: 2026-04-29
audience: Native (Marsys / Abhisek) — operational playbook
owner: Abhisek Mohanty
relates_to:
  - 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md (DRAFT v1.0.2 → CURRENT post-R0)
  - 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md (LIVING v1.0.3)
  - EXEC_BRIEF_PORTAL_REDESIGN_R0_FOUNDATION_v1_0.md (next session)
  - CLAUDECODE_BRIEF_R{1,2,4,5,6}.md — per-phase brief pool, parked at project root
purpose: >
  Step-by-step playbook for triggering the five parallel-ready redesign phases
  (R1, R2, R4, R5, R6) once R0 closes. Covers worktree setup, per-phase
  CLAUDECODE_BRIEF activation, trigger phrases, and ongoing rules for
  inter-phase coordination.
---

# Portal Redesign — Parallel Run Playbook v1.0

## §0 — When to use this runbook

Use this AFTER R0 Foundation closes. R0 is the gate — until its closure report lands and the canonical-artifact promotions (Vision → CURRENT, CANONICAL_ARTIFACTS entries, CLAUDE.md §C update) are complete, **no parallel phase should start**. The R0 session ends with its CLAUDECODE_BRIEF.md flipped to `status: COMPLETE`; that flip is the green light for this runbook.

If R0 hasn't closed, stop and finish R0 first.

## §1 — What you have ready right now

Authored at the project root (committed as part of the redesign foundation set):

| File | Purpose |
|------|---------|
| `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` | strategic doc |
| `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` | LIVING phase ledger |
| `EXEC_BRIEF_PORTAL_REDESIGN_R0_FOUNDATION_v1_0.md` | gate phase brief |
| `EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER_v1_0.md` | R1 brief |
| `EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE_v1_0.md` | R2 brief (keystone) |
| `EXEC_BRIEF_PORTAL_REDESIGN_R4_CONSUME_POLISH_v1_0.md` | R4 brief |
| `EXEC_BRIEF_PORTAL_REDESIGN_R5_TIMELINE_v1_0.md` | R5 brief |
| `EXEC_BRIEF_PORTAL_REDESIGN_R6_COCKPIT_v1_0.md` | R6 brief |
| `CLAUDECODE_BRIEF.md` | currently points at R0 |
| `CLAUDECODE_BRIEF_R1.md` | per-phase brief, ready to copy into R1 worktree |
| `CLAUDECODE_BRIEF_R2.md` | per-phase brief, ready to copy into R2 worktree |
| `CLAUDECODE_BRIEF_R4.md` | per-phase brief, ready to copy into R4 worktree |
| `CLAUDECODE_BRIEF_R5.md` | per-phase brief, ready to copy into R5 worktree |
| `CLAUDECODE_BRIEF_R6.md` | per-phase brief, ready to copy into R6 worktree |

R3 and R7 are intentionally not authored. R3 authors after R2 closes (its hook-compat audit findings shape the brief); R7 authors after R6 closes (polish pass scope follows from what shipped).

## §2 — Pre-fan-out confirmation

Before creating worktrees, verify R0 truly closed:

```bash
cd ~/Vibe-Coding/Apps/Madhav
git log --oneline -3 main                                                    # R0 merge commit should be at HEAD
grep "vision_status: CURRENT" 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md   # confirm
grep "status: closed" 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md | head -3 # R0 row should appear
grep "status: CURRENT" 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md            # Vision promoted
grep "PORTAL_REDESIGN_VISION" 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md       # added at R0 close
git status                                                                     # clean
```

All four greps must hit. If any miss, R0's closure report didn't fully execute its promotion steps; fix before proceeding.

## §3 — Create worktrees for the parallel phases

From inside the main repo at `~/Vibe-Coding/Apps/Madhav`, create one worktree per phase you want to run in parallel. Each worktree gets its own branch, branched from `main` (which now contains R0's foundation).

**Full fan-out (all five phases at once):**

```bash
cd ~/Vibe-Coding/Apps/Madhav
git fetch origin
git checkout main
git pull

git worktree add ../Madhav-r1 -b redesign/r1-roster main
git worktree add ../Madhav-r2 -b redesign/r2-chart-profile main
git worktree add ../Madhav-r4 -b redesign/r4-consume-polish main
git worktree add ../Madhav-r5 -b redesign/r5-timeline main
git worktree add ../Madhav-r6 -b redesign/r6-cockpit main

git worktree list
```

**Partial fan-out (only the phases you're starting):** pick the subset and skip the rest. You can always add more worktrees later as previously-started phases close.

Recommended starting subset if you don't want all five at once:

| Concurrency | Recommended subset | Rationale |
|-------------|-------------------|-----------|
| 1 phase | R2 | Keystone surface; R3 unblocks from R2 |
| 2 phases | R2 + R1 | Keystone + Roster polish; both customer-facing |
| 3 phases | R2 + R1 + R6 | Add Cockpit elevation for super-admin parity |
| 4 phases | R2 + R1 + R5 + R6 | Add Timeline (LEL surface); leave R4 for later |
| 5 phases | All | Maximum parallel; need 5 Claude Code instances |

## §4 — Activate each worktree's brief

For each worktree you created in §3, copy the per-phase CLAUDECODE_BRIEF into the worktree as `CLAUDECODE_BRIEF.md` (which is the file `CLAUDE.md §C item #0` reads). The activation pattern:

```bash
# R1 worktree
cp ~/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF_R1.md ~/Vibe-Coding/Apps/Madhav-r1/CLAUDECODE_BRIEF.md

# R2 worktree
cp ~/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF_R2.md ~/Vibe-Coding/Apps/Madhav-r2/CLAUDECODE_BRIEF.md

# R4 worktree
cp ~/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF_R4.md ~/Vibe-Coding/Apps/Madhav-r4/CLAUDECODE_BRIEF.md

# R5 worktree
cp ~/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF_R5.md ~/Vibe-Coding/Apps/Madhav-r5/CLAUDECODE_BRIEF.md

# R6 worktree
cp ~/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF_R6.md ~/Vibe-Coding/Apps/Madhav-r6/CLAUDECODE_BRIEF.md
```

**Important:** copy, don't move. The original `CLAUDECODE_BRIEF_RN.md` files at the parent repo root are the canonical pool — they stay put so you can re-copy if needed (e.g., a worktree gets corrupted) and so anyone reading the repo knows what the parallel set looks like.

## §5 — Open each worktree in its own IDE window

Open each worktree as a separate Anti-Gravity / VS Code window:

```bash
code ~/Vibe-Coding/Apps/Madhav-r1
code ~/Vibe-Coding/Apps/Madhav-r2
code ~/Vibe-Coding/Apps/Madhav-r4
code ~/Vibe-Coding/Apps/Madhav-r5
code ~/Vibe-Coding/Apps/Madhav-r6
```

Each window has its own working directory, its own branch, its own `CLAUDECODE_BRIEF.md`. Claude Code instances running in different windows are fully independent.

## §6 — Trigger each Claude Code session

In each window, start a Claude Code session and paste the trigger phrase:

| Window | Trigger phrase |
|--------|---------------|
| Madhav-r1 | `Read EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER_v1_0.md and execute it.` |
| Madhav-r2 | `Read EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE_v1_0.md and execute it.` |
| Madhav-r4 | `Read EXEC_BRIEF_PORTAL_REDESIGN_R4_CONSUME_POLISH_v1_0.md and execute it.` |
| Madhav-r5 | `Read EXEC_BRIEF_PORTAL_REDESIGN_R5_TIMELINE_v1_0.md and execute it.` |
| Madhav-r6 | `Read EXEC_BRIEF_PORTAL_REDESIGN_R6_COCKPIT_v1_0.md and execute it.` |

Each Claude Code session reads `CLAUDECODE_BRIEF.md` first (per `CLAUDE.md §C item #0`), follows its required-reads list, and executes the EXEC_BRIEF.

## §7 — Ongoing rules during parallel run

**A. The tracker is the single source of truth for phase status.** Before any session opens a phase, it reads `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md §2` and confirms its phase is in `post_r0_parallel_ready` and `trace_fix_status` is on_hold or merged. If a session detects a state inconsistency (e.g., R4 brief says trace_fix_status is on_hold but tracker says in_flight), it halts.

**B. Tracker writes serialize via the active session that's closing.** When a phase closes, that session updates the tracker §2 + §3 atomically as part of its close-checklist. Two sessions never write the tracker concurrently because closes happen one at a time. If two sessions finish at the same instant, one waits.

**C. Mirror discipline applies per session.** Each phase's closure report runs `mirror_enforcer.py`. Phases that touch governance files (R0 only, in this redesign) trigger `.geminirules` / `.gemini/project_state.md` updates. R1/R2/R4/R5/R6 don't touch governance files, so mirror_enforcer is a no-op assertion for those.

**D. R3 unblocks the moment R2 closes.** Watch R2's closure report for the follow-up note "R3 brief now authorable." When that lands, you can author R3's EXEC_BRIEF in a Cowork session, set up `~/Vibe-Coding/Apps/Madhav-r3` as a worktree, drop in a fresh `CLAUDECODE_BRIEF.md`, and start R3 — even while R1/R4/R5/R6 are still running. R3 is parallelizable with all of {R1, R4, R5, R6}.

**E. R7 unblocks the moment R6 closes.** Same pattern. R7 is the polish pass and runs alone after everything else lands.

**F. If trace-fix work resumes mid-redesign**, flip `tracker.trace_fix_status` from `on_hold` to `in_flight`. R4 must be either not-yet-started or already-merged at that moment. If R4 is in flight, halt R4 and serialize.

**G. Conflict resolution if a worktree won't merge.** Each worktree's `may_touch` was authored to be disjoint from every other phase's. If you hit merge conflicts on a final merge to main, the conflict is in code R0 left ambiguous (e.g., layout boilerplate that R1 and R6 both touched in slightly different ways). Resolve manually; capture the resolution as a follow-up in the closing phase's report.

## §8 — Closing each phase

When a Claude Code session in a worktree finishes its phase:

1. Closure report at `00_ARCHITECTURE/PORTAL_REDESIGN_RN_REPORT_v1_0.md` (`status: COMPLETE`).
2. Tracker `§3 RN row` flipped to `status: closed` with `session_id`, `closed_at`, `follow_ups`.
3. Tracker `§2` refreshed (`active_phase` adjusted, `last_redesign_session_id`, etc.).
4. Governance scripts exit 0.
5. SESSION_LOG.md appended.
6. Worktree's `CLAUDECODE_BRIEF.md` flipped to `status: COMPLETE`.
7. PR opened from `redesign/rN-{slug}` to `main`. PR description references the closure report.

After PR merge, the worktree can be removed:

```bash
cd ~/Vibe-Coding/Apps/Madhav
git worktree remove ../Madhav-rN
git branch -d redesign/rN-{slug}      # local branch cleanup if not auto-deleted
```

## §9 — End-state check

The redesign workstream is complete when:

| Phase | Closure report present? | Tracker row closed? | PR merged? |
|-------|------------------------|---------------------|------------|
| R0 | ✓ | ✓ | ✓ |
| R1 | ✓ | ✓ | ✓ |
| R2 | ✓ | ✓ | ✓ |
| R3 | ✓ | ✓ | ✓ |
| R4 | ✓ | ✓ | ✓ |
| R5 | ✓ | ✓ | ✓ |
| R6 | ✓ | ✓ | ✓ |
| R7 | ✓ | ✓ | ✓ |

Plus: VISION acceptance criteria §5 (all 8 items) satisfied. Tracker §2 `active_phase: null`, `deferred_briefs: []`, `post_r0_parallel_ready: []`. Mirror discipline clean across all sessions. Feature flags `PORTAL_REDESIGN_R*_ENABLED` removed in R7.

That's the redesign done.

---

*End of PORTAL_REDESIGN_PARALLEL_RUNBOOK_v1_0.md (ACTIVE, 2026-04-29).*
