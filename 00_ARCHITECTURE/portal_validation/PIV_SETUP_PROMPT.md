# PIV Setup Prompt — paste into Claude Code (anti-gravity)

Open Claude Code in `~/Vibe-Coding/Apps/Madhav` and paste everything
below the `---` line. It will: triage 4 dirty files, push `main` to
origin, create the PIV worktree, stage QG.0, and stop. Then you launch
the autonomous loop in a fresh session.

---

You are operating Claude Code in autonomous mode to clean up the Madhav
repo state and set up the **Portal Integration Validation (PIV)**
worktree. The native (Abhisek) just committed the PIV plan to `main`
(commit `ddcc03a`, 12 files). Your job in this one-shot is:

1. Triage 4 dirty files on `main` that were carried over from the
   `feature/ui-improvements` sidebar work
2. Push `main` to `origin/main` (45 commits ahead at start)
3. Create the PIV worktree at `../madhav-piv-tmp` on a fresh branch
4. Stage QG.0 as the active `CLAUDECODE_BRIEF.md`
5. Stop with a clean ready-state report

Do **NOT** begin executing QG.0 — that's a separate fresh session
driven by `PIV_AUTONOMOUS_LOOP_PROMPT.md`.

## Operating principles (read before you start)

- **Preserve everything.** Default to `git stash`, never `git restore` /
  hard reset. The native has a standing rule: no silent discard of work.
- **Report at each phase.** Print a banner line before each phase so
  the user can follow along.
- **STOP and ask** if anything looks ambiguous — diff content unclear,
  origin/main has diverged, a path collision exists. Do not
  improvise around it.
- **No force pushes**, no `git reset --hard`, no `rm -rf` on any
  worktree path. Ever.
- **No `cd` into other worktrees.** Stay in `/Users/Dev/Vibe-Coding/Apps/Madhav`
  for Phase 0–4 and `/Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp` for
  Phase 5+. The other worktrees (Madhav-M9, madhav-phase-3-tmp,
  marsys-m6-prospective) are not yours.

## Known worktree map (from earlier `git worktree list`)

```
/Users/Dev/Vibe-Coding/Apps/Madhav                  →  feature/ui-improvements then main (current)
/Users/Dev/Vibe-Coding/Apps/Madhav-M9               →  feature/m9-multi-school-triangulation
/Users/Dev/Vibe-Coding/Apps/madhav-phase-3-tmp      →  feature/aiops-phase-3-consume-ui (Phase 3 closed)
/Users/Dev/Vibe-Coding/Apps/marsys-m6-prospective   →  feature/m6-prospective-testing
```

The PIV worktree will be the FIFTH entry: `../madhav-piv-tmp` on
`feature/portal-integration-validation`.

---

## Phase 0 — Sanity check

Print banner: `===== PHASE 0 — SANITY CHECK =====`

Run:

```
cd /Users/Dev/Vibe-Coding/Apps/Madhav
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --short HEAD
git status --short
git log --oneline -3
git worktree list
```

**Assert:**
- `pwd` ends with `/Madhav`
- branch is `main` (NOT `feature/ui-improvements`)
- top of `git log` is `ddcc03a docs(piv): author master plan + 9 briefs + launchers`
  (if it's not — the native may have committed something more since; REPORT the actual HEAD and STOP)
- `git status --short` shows roughly:
  ```
   M platform/src/components/chat/AssistantMessage.tsx
   M platform/src/components/consume/ConsumeChat.tsx
   M platform/src/components/consume/PostAnswerProvenance.tsx
   M platform/src/components/consume/StreamingAnswer.tsx
  ```
  (or fewer, if user already cleaned up; or empty)

If branch is NOT `main`: STOP and REPORT.
If working tree is already clean: skip directly to **Phase 4**.

---

## Phase 1 — Diagnose the 4 dirty files

Print banner: `===== PHASE 1 — DIAGNOSE DIRTY FILES =====`

For each of the 4 files, capture diff content:

```
for F in platform/src/components/chat/AssistantMessage.tsx \
         platform/src/components/consume/ConsumeChat.tsx \
         platform/src/components/consume/PostAnswerProvenance.tsx \
         platform/src/components/consume/StreamingAnswer.tsx; do
  echo "--- $F ---"
  git diff --stat "$F"
  echo
  git diff "$F" | head -60
  echo
done
```

Also fetch context on what `feature/ui-improvements` recently changed
in these files (this is a separate branch in the same repo):

```
git log --oneline -10 feature/ui-improvements -- platform/src/components/chat/AssistantMessage.tsx
git log --oneline -10 feature/ui-improvements -- platform/src/components/consume/ConsumeChat.tsx
git log --oneline -10 feature/ui-improvements -- platform/src/components/consume/PostAnswerProvenance.tsx
git log --oneline -10 feature/ui-improvements -- platform/src/components/consume/StreamingAnswer.tsx
```

**Write a 1-line summary per file** to stdout describing the diff:
- approximate +/- line counts
- nature of the change (e.g., "added sidebar overlay prop", "wrapped JSX in conditional", "tweaked className")
- whether it looks related to the sidebar/hover-expand work landed in
  commits `dc37f4b` / `0402e70` / `07f521a` / `a18a7e7` / `96a35c4`
  on `feature/ui-improvements`

**Hypothesis (most likely):** these are working-tree changes that
carried over when the native switched the Madhav worktree from
`feature/ui-improvements` to `main` (git's default: uncommitted
modifications follow the working tree across `git checkout`). They
likely belong on `feature/ui-improvements`.

---

## Phase 2 — Triage decision

Print banner: `===== PHASE 2 — TRIAGE =====`

Pick ONE of these paths based on your Phase 1 diagnosis. Default is
**PATH A**. Only deviate if Phase 1 evidence clearly contradicts.

### PATH A — Stash on main, recover later on feature/ui-improvements (DEFAULT)

If the diffs look like sidebar/UI work (matches the recent
`feature/ui-improvements` commit topics), stash them:

```
git stash push -m "WIP-from-feature-ui-improvements: 4 component files carried over to main" \
  platform/src/components/chat/AssistantMessage.tsx \
  platform/src/components/consume/ConsumeChat.tsx \
  platform/src/components/consume/PostAnswerProvenance.tsx \
  platform/src/components/consume/StreamingAnswer.tsx

git stash list
git status
```

Note the stash ref (typically `stash@{0}`). Print a recovery hint:

```
STASH SAVED: stash@{0}
RECOVERY (after PIV completes):
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git checkout feature/ui-improvements
  git stash pop stash@{0}
```

Do NOT pop the stash here on main. Working tree must end CLEAN.

### PATH B — Discard (only if diffs are obviously noise)

If diffs look accidental (whitespace, formatter noise, no real
content): STOP and ask the user before doing anything. Print:

```
DIFFS LOOK MINIMAL. PROPOSED ACTION: git restore on these 4 files (DISCARD).
Confirm? [Y/N]
Showing 1-line summary per file again:
  <summary 1>
  <summary 2>
  <summary 3>
  <summary 4>
```

Wait for the user. Do NOT proceed without explicit Y.

### PATH C — Commit to main directly (only if diffs are clearly main work)

If diffs look like a genuine fix that belongs on `main` (e.g., a
typo fix unrelated to sidebar): STOP and ask. Print:

```
DIFFS LOOK INTENDED FOR MAIN. PROPOSED ACTION:
  git add <files>
  git commit -m "fix(consume): <propose-based-on-diff>"
Confirm? [Y/N]
```

Wait for user. Do NOT proceed without explicit Y.

---

## Phase 3 — Verify clean state

Print banner: `===== PHASE 3 — VERIFY CLEAN =====`

```
git status
git rev-parse --short HEAD
```

**Assert:** `git status` ends with "nothing to commit, working tree clean".

If not clean, STOP and REPORT what's still dirty.

---

## Phase 4 — Push main to origin

Print banner: `===== PHASE 4 — PUSH MAIN =====`

Fetch first to learn the divergence:

```
git fetch origin
AHEAD=$(git rev-list --count origin/main..main)
BEHIND=$(git rev-list --count main..origin/main)
echo "ahead=$AHEAD behind=$BEHIND"
```

**Decision matrix:**
- `ahead=0 behind=0` → no-op, nothing to push, print "main matches origin"
- `ahead>0 behind=0` → safe to fast-forward push:
  ```
  git push origin main
  git rev-parse origin/main
  git rev-parse main
  ```
  Confirm both SHAs match.
- `behind>0` → origin has commits we lack. **STOP**, do NOT push, do NOT
  rebase. Print:
  ```
  ORIGIN/MAIN IS AHEAD BY <N> COMMITS WE DON'T HAVE.
  This is unusual — investigate before pushing.
  Showing the divergent commits on origin:
  ```
  Then run `git log --oneline main..origin/main` and STOP for user
  decision.

If push fails for auth or network: REPORT the exact error and
**continue to Phase 5** anyway. Pushing is hygiene, not required.

---

## Phase 5 — Create PIV worktree

Print banner: `===== PHASE 5 — CREATE PIV WORKTREE =====`

Pre-flight: check for collisions.

```
git branch --list 'feature/portal-integration-validation'
ls -la /Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp 2>/dev/null || echo "PATH-FREE"
git worktree list
```

**Decision matrix:**
- If branch `feature/portal-integration-validation` exists AND path
  `../madhav-piv-tmp` exists AND `git worktree list` shows them paired:
  the worktree was already created in a prior attempt. Print this
  fact and SKIP to Phase 6 (assume the worktree is reusable).
- If only the BRANCH exists (no path, or path not in worktree list):
  delete the orphan branch first:
  `git branch -D feature/portal-integration-validation`
  Then create fresh.
- If only the PATH exists (orphan directory):
  STOP and ask the user — don't auto-remove a directory.
- If neither exists: create fresh.

Fresh creation:

```
cd /Users/Dev/Vibe-Coding/Apps
git -C Madhav worktree add ../madhav-piv-tmp -b feature/portal-integration-validation main
cd madhav-piv-tmp
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --short HEAD
git status
```

**Assert:**
- `pwd` = `/Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp`
- branch = `feature/portal-integration-validation`
- HEAD = same SHA as Madhav's `main` (the PIV plan commit)
- working tree clean

---

## Phase 6 — Verify briefs are in place

Print banner: `===== PHASE 6 — VERIFY BRIEFS =====`

```
ls -la 00_ARCHITECTURE/portal_validation/
ls -la 00_ARCHITECTURE/portal_validation/briefs/
wc -l 00_ARCHITECTURE/portal_validation/PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0.md
wc -l 00_ARCHITECTURE/portal_validation/PIV_PRELAUNCH_PROMPT.md
wc -l 00_ARCHITECTURE/portal_validation/PIV_AUTONOMOUS_LOOP_PROMPT.md
wc -l 00_ARCHITECTURE/portal_validation/briefs/PHASE_QG_*.md
```

**Assert all present** (12 files total):
- `PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0.md`
- `PIV_PRELAUNCH_PROMPT.md`
- `PIV_AUTONOMOUS_LOOP_PROMPT.md`
- `PIV_SETUP_PROMPT.md` (this file — optional, may or may not be present)
- `briefs/PHASE_QG_0_BRIEF.md` through `briefs/PHASE_QG_8_BRIEF.md`
  (9 briefs)
- Each brief should be at least ~100 lines

If anything missing or suspiciously short, STOP and REPORT.

---

## Phase 7 — Stage QG.0 as the active brief

Print banner: `===== PHASE 7 — STAGE QG.0 =====`

```
cp 00_ARCHITECTURE/portal_validation/briefs/PHASE_QG_0_BRIEF.md CLAUDECODE_BRIEF.md
head -15 CLAUDECODE_BRIEF.md
git status
```

**Assert:** `head` shows frontmatter with `session_id: PIV_QG_0` and
`phase: QG.0`.

Commit:

```
git add CLAUDECODE_BRIEF.md
git commit -m "chore(piv): bootstrap PIV worktree — stage QG.0 as active CLAUDECODE_BRIEF"
git log --oneline -5
```

---

## Phase 8 — Optional: push PIV branch to origin

Print banner: `===== PHASE 8 — PUSH PIV BRANCH (OPTIONAL) =====`

```
git push -u origin feature/portal-integration-validation
```

If push fails (auth, network, branch protection), REPORT but do NOT
treat as fatal — local PIV setup is complete and usable for autonomous
execution. The native can push later.

---

## Phase 9 — Ready-state report

Print banner: `===== PHASE 9 — READY =====`

Then print this exact block to stdout, with `<>` placeholders filled
with real values you captured along the way:

```
============================================================
PIV WORKTREE READY FOR AUTONOMOUS LOOP
============================================================
Worktree path:    /Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp
Branch:           feature/portal-integration-validation
HEAD short SHA:   <sha>
Origin push:      <pushed | local-only | skipped: <reason>>
Madhav main:      <sha> — clean, on branch main
                  <pushed to origin/main | local-only>

Active brief: CLAUDECODE_BRIEF.md = PHASE_QG_0 (inventory + M1-M10 map)

Stashed work (if Phase 2 took PATH A):
  Ref:      stash@{0}
  Message:  WIP-from-feature-ui-improvements: 4 component files carried over to main
  Recover:
    cd /Users/Dev/Vibe-Coding/Apps/Madhav
    git checkout feature/ui-improvements
    git stash pop stash@{0}

------------------------------------------------------------
TO START THE PIV AUTONOMOUS EXECUTION:
------------------------------------------------------------
  1. Open a FRESH Claude Code (anti-gravity) session.
  2. Set the working directory to:
        /Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp
     (do NOT use the Madhav directory for this)
  3. Paste the contents of:
        00_ARCHITECTURE/portal_validation/PIV_AUTONOMOUS_LOOP_PROMPT.md
  4. The session will execute QG.0 → QG.8 autonomously and stop
     at QG.8 close, with a final report at:
        00_ARCHITECTURE/portal_validation/PORTAL_INTEGRATION_VALIDATION_REPORT_v1_0.md

------------------------------------------------------------
WHILE PIV RUNS (parallel-safe):
------------------------------------------------------------
You can keep working in /Users/Dev/Vibe-Coding/Apps/Madhav on any
branch (e.g., feature/ui-improvements). The PIV loop never touches
the Madhav worktree; it only reads HEAD via `git -C` for an
independent-activity note in the final report.

------------------------------------------------------------
EXPECTED PIV RUN PROFILE:
------------------------------------------------------------
  Sub-phases:  QG.0 → QG.8 (9 total)
  Cost:        under $1.00 LLM spend (hard budget; BAILs at $0.95)
  Models:      gemini-2.5-flash-lite / deepseek-chat / gpt-4.1-nano
               / nemotron / marsys=gemini-flash-lite
               (Anthropic BANNED per standing native rule)
  Output:      9 sub-phase deliverables + final report + findings register
  Duration:    a few hours of autonomous execution (network + DB-proxy bound)
============================================================
```

**STOP.** Do NOT execute QG.0. Do NOT paste the autonomous loop prompt
yourself. The native runs that in a fresh session.

---

## Global BAIL OUT rules

STOP and REPORT immediately if any of these conditions hit:

- Phase 0 finds you on the wrong branch (not `main`)
- Phase 2 produces ambiguous diff content and you can't confidently
  pick PATH A/B/C
- Phase 3 finds the working tree still dirty after triage
- Phase 4 finds origin/main has diverged (`behind > 0`)
- Phase 5 finds a path collision and the user must decide cleanup
- Phase 6 finds any of the 12 PIV files missing or truncated
- Phase 7 finds the QG.0 brief doesn't have the expected frontmatter
- Any git command exits non-zero without an obvious recoverable cause

On BAIL: print the exact command run, exit code, full stderr, and
current `git status` + `git rev-parse HEAD` + `git worktree list`.
Do NOT attempt corrective commands. Wait for the native.

---

Begin with Phase 0.
