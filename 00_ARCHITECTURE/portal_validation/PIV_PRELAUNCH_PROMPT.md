# PIV Pre-Launch Prompt — paste into Claude Code (anti-gravity)

Paste this entire block into Claude Code in `~/Vibe-Coding/Apps/Madhav`.
It creates the `madhav-piv-tmp` worktree, points it at a fresh branch
off `main`, and stages QG.0 as the first session.

---

You are operating Claude Code in autonomous mode for the
**Portal Integration Validation (PIV)** workstream. Your job in
this one-shot is to set up the worktree and stage QG.0 — nothing
more. Subsequent execution loops are run by the native triggering
your QG.0–QG.8 sequence.

## Step 1 — Pre-flight (read-only)

Run these commands and capture output:

```
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git status
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
git worktree list
```

If you are not on `main` OR the working tree is dirty:
**STOP and REPORT** the state. Do not proceed.

## Step 2 — Create the PIV worktree

```
cd /Users/Dev/Vibe-Coding/Apps
git -C Madhav worktree add ../madhav-piv-tmp -b feature/portal-integration-validation main
cd madhav-piv-tmp
git status
git rev-parse HEAD
```

Confirm:
- Worktree path: `/Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp`
- Branch: `feature/portal-integration-validation`
- HEAD = same commit as `main`

## Step 3 — Verify briefs are in place

The PIV master plan + 9 briefs were authored on `main` and should be
visible in the new worktree (since the worktree was branched off main).

```
ls 00_ARCHITECTURE/portal_validation/
ls 00_ARCHITECTURE/portal_validation/briefs/
```

Expected:
```
00_ARCHITECTURE/portal_validation/
  PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0.md
  PIV_PRELAUNCH_PROMPT.md
  PIV_AUTONOMOUS_LOOP_PROMPT.md
  briefs/
    PHASE_QG_0_BRIEF.md
    PHASE_QG_1_BRIEF.md
    PHASE_QG_2_BRIEF.md
    PHASE_QG_3_BRIEF.md
    PHASE_QG_4_BRIEF.md
    PHASE_QG_5_BRIEF.md
    PHASE_QG_6_BRIEF.md
    PHASE_QG_7_BRIEF.md
    PHASE_QG_8_BRIEF.md
```

If any file is missing: **STOP and REPORT.**

## Step 4 — Stage QG.0 as the active brief

Copy `PHASE_QG_0_BRIEF.md` to `CLAUDECODE_BRIEF.md` (the root governing
brief read by every session per CLAUDE.md §C item 0):

```
cp 00_ARCHITECTURE/portal_validation/briefs/PHASE_QG_0_BRIEF.md CLAUDECODE_BRIEF.md
git add CLAUDECODE_BRIEF.md
git status
```

## Step 5 — Initial commit on the PIV branch

```
git add -A
git commit -m "chore(piv): bootstrap PIV worktree — stage QG.0 as active CLAUDECODE_BRIEF"
git log --oneline -5
```

## Step 6 — Report ready state

Print, to stdout:

```
=== PIV WORKTREE READY ===
Path:    /Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp
Branch:  feature/portal-integration-validation
HEAD:    <commit short SHA>
Active:  CLAUDECODE_BRIEF.md → PHASE_QG_0_BRIEF
Next:    paste PIV_AUTONOMOUS_LOOP_PROMPT.md to begin QG.0 execution
=========================
```

STOP after step 6. Do NOT begin executing QG.0; that requires the
autonomous loop prompt.
