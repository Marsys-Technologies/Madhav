---
artifact: BHISMA_PARALLEL_ISOLATION_SETUP
canonical_id: BHISMA_PARALLEL_ISOLATION_SETUP
version: 1.0
status: CURRENT
authored_by: Cowork (Claude Sonnet 4.6) 2026-05-02
purpose: |
  Complete isolation setup for running Project BHISMA in parallel with
  MARSYS-JIS (KARN/M3 governance) and Project Ustad — without any session
  corrupting another's working tree, git index, or commit history.
  Also contains the final merge-to-main protocol for BHISMA close.
changelog:
  - 1.0 (2026-05-02): Initial — worktree-per-session architecture, cross-project
      isolation matrix, copy-paste Antigravity prompts, merge-to-main protocol.
---

# BHISMA Parallel Isolation Setup

## Why this document exists

You are running three concurrent projects in one Antigravity (VS Code + Claude Code
extension) environment:

| Project | Repo path | Isolation level |
|---------|-----------|----------------|
| **BHISMA** (platform engineering) | `/Users/Dev/Vibe-Coding/Apps/Madhav` | Same repo as KARN/M3 — file-scope isolated |
| **KARN / M3 governance** | `/Users/Dev/Vibe-Coding/Apps/Madhav` | Same repo as BHISMA — file-scope isolated |
| **Project Ustad** | `/Users/Dev/Vibe-Coding/Apps/Ustad` | Separate repo — zero risk |

The two risks are:
1. **Git index lock** — two Claude Code sessions touching the same git repo
   simultaneously → `.git/index.lock` collision → one session crashes.
2. **File scope bleed** — a session accidentally editing a file outside its
   declared `may_touch` glob → governance corruption or test breakage.

The solution for (1) is **git worktrees**: each parallel Claude Code session
gets its own filesystem checkout at a separate path with its own git index.
The solution for (2) is the **file lock declaration** in every session's
opening handshake (already in `CLAUDECODE_BRIEF.md §3`).

---

## §1 — Cross-project isolation matrix

```
              BHISMA Eng   KARN/M3 Gov   Ustad
BHISMA Eng       ✗ (same)    ⚠ worktree    ✓ safe
KARN/M3 Gov    ⚠ worktree    ✗ (same)     ✓ safe
Ustad            ✓ safe       ✓ safe       ✗ (same)
```

**✓ safe** = different repos; run simultaneously with no setup.
**⚠ worktree** = same Madhav repo; MUST use separate worktrees.
**✗** = never run two sessions of the same domain simultaneously.

**Ustad** is always safe to run alongside anything in Madhav —
it is a completely separate git repository.

**SESSION_LOG.md and CURRENT_STATE_v1_0.md** are the only files both BHISMA
Engineering and KARN/M3 Governance touch. Rule: only one session appends to
these at a time (session-close only, never mid-session).

---

## §2 — Worktree architecture (one-time setup per wave)

Each parallel Claude Code session that touches the Madhav repo gets:
- Its own checkout directory: `../Madhav-{session-id}/`
- Its own git branch: `feature/bhisma-w{n}/{session-id}`
- Its own `.git/index` → no lock conflicts, ever

### One-time umbrella branch setup (run once before Wave 3 starts)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git pull origin main

# Create the Wave 3 umbrella branch (change w3 to the current wave number)
git checkout -b feature/bhisma-w3
git push -u origin feature/bhisma-w3
```

> **Note for Wave 2 / phase-o work:**
> `feature/phase-o-observatory` is the current umbrella branch for W2 + Phase O.
> Before starting new W3 sessions, that branch must be reviewed and merged
> (see §5 — Final merge-to-main protocol).

---

## §3 — Spawning a parallel session (per session, before each Antigravity window)

### Step 1 — Create the worktree (run in Terminal, NOT inside Antigravity)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Pull the umbrella branch to latest
git fetch origin
git checkout feature/bhisma-w3   # or the current wave umbrella
git pull

# Set SESSION_ID to match the session you're about to run
# Examples: uqe-bugs, mon-infra, trace-ui, schema-mig, eval-harness, karn-m3-a4
SESSION_ID=uqe-bugs

# Create the worktree + sub-branch in one command
git worktree add \
  "../Madhav-${SESSION_ID}" \
  -b "feature/bhisma-w3/${SESSION_ID}" \
  feature/bhisma-w3

echo "Worktree ready at: $(realpath ../Madhav-${SESSION_ID})"
```

### Step 2 — Open the worktree in Antigravity

In VS Code / Antigravity: **File → Open Folder** →
select `/Users/Dev/Vibe-Coding/Apps/Madhav-{session-id}`

Each window now has a completely independent working tree and git index.
No two windows will ever fight over `.git/index.lock`.

### Step 3 — Paste the session prompt

In that Antigravity window, open Claude Code and paste the session brief
prompt (see §4 below for templates).

### Step 4 — Teardown after session closes

```bash
SESSION_ID=uqe-bugs   # same value as above

# 1. Merge sub-branch back to umbrella (in the main Madhav directory)
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout feature/bhisma-w3
git merge --no-ff "feature/bhisma-w3/${SESSION_ID}" \
  -m "merge: bhisma-w3/${SESSION_ID} — [one-line summary]"

# 2. Remove the worktree
git worktree remove "../Madhav-${SESSION_ID}"

# 3. Delete the sub-branch (local + remote)
# Use -D not -d: sub-branches are only reachable from the umbrella, not from main,
# so -d will always refuse. The merge in step 1 above ensures no work is lost.
git branch -D "feature/bhisma-w3/${SESSION_ID}"
git push origin --delete "feature/bhisma-w3/${SESSION_ID}" 2>/dev/null || true

# 4. Push updated umbrella
git push origin feature/bhisma-w3
```

---

## §4 — Claude Code prompt templates (paste into Antigravity)

Copy the relevant block verbatim. Change only the fields in `[SQUARE BRACKETS]`.

---

### Template A — BHISMA Engineering session

```
BHISMA Engineering session — [W3-S1-UQE-BUGS or similar]

Working directory: /Users/Dev/Vibe-Coding/Apps/Madhav-[SESSION_ID]
Branch: feature/bhisma-w3/[SESSION_ID]

# Required reading before any work
1. Read PROJECT_BHISMA_BOOTSTRAP.md (00_ARCHITECTURE/)
2. Read CLAUDECODE_BRIEF.md (root) → §1 domain map, §3 BHISMA Engineering file locks
3. Read platform/briefs/[BRIEF_FILE].md → confirm scope and ACs

# Check git lock before starting
ls .git/*.lock 2>/dev/null && echo "LOCK EXISTS — remove before proceeding" || echo "no locks"

# File scope declaration (mandatory)
SESSION SCOPE: [one sentence describing the session]
DOMAIN: Engineering
MAY_TOUCH:
  - platform/src/**
  - platform/tests/**
  - platform/briefs/**
  - platform/scripts/**
MUST_NOT_TOUCH:
  - 00_ARCHITECTURE/**
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**
  - CLAUDE.md
  - .geminirules

# Execute the brief
[Paste the specific brief instructions here]

# Session close — final checks
npx tsc --noEmit
npx vitest run
# If both pass, commit and signal worktree teardown.
```

---

### Template B — KARN / M3 Governance session

```
KARN / MARSYS-JIS Governance session — [M3-W1-A4-DIS009-DISPOSITION or similar]

Working directory: /Users/Dev/Vibe-Coding/Apps/Madhav-[SESSION_ID]
Branch: feature/karn-[SESSION_ID]   # or feature/m3-[SESSION_ID]

# Required reading
1. Read CLAUDE.md §C items 1–11
2. Read 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2
3. Read 00_ARCHITECTURE/PHASE_M3_PLAN_v1_0.md (relevant sub-phase section)

# File scope declaration (mandatory)
SESSION SCOPE: [one sentence]
DOMAIN: Governance
MAY_TOUCH:
  - 00_ARCHITECTURE/**
  - 01_FACTS_LAYER/**           # if corpus work
  - 025_HOLISTIC_SYNTHESIS/**   # if synthesis work
  - .geminirules
  - .gemini/project_state.md
MUST_NOT_TOUCH:
  - platform/src/**
  - platform/tests/**
  - platform/scripts/**

# Execute the session
[Paste the specific M3/governance brief here]
```

---

### Template C — Project Ustad session

```
Project Ustad session — [USTAD-SESSION-NAME]

Working directory: /Users/Dev/Vibe-Coding/Apps/Ustad
(This is a SEPARATE repository — zero file overlap with Madhav)

# No worktree needed — Ustad is a separate repo with its own .git/
# Open /Users/Dev/Vibe-Coding/Apps/Ustad directly in Antigravity.

# Read Ustad's own orientation files first:
1. Read CLAUDE.md or equivalent in the Ustad workspace
2. Read the active brief

# File scope declaration
SESSION SCOPE: [one sentence]
DOMAIN: Ustad (fully isolated)
MAY_TOUCH:   everything under /Users/Dev/Vibe-Coding/Apps/Ustad/
MUST_NOT_TOUCH: /Users/Dev/Vibe-Coding/Apps/Madhav/** (never cross repos)
```

---

## §5 — Final merge-to-main protocol (BHISMA wave close)

Run this sequence at the end of each BHISMA wave to safely merge to `main`.
Never merge directly from a stream branch — always go through an integration step.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# 1. Ensure umbrella is up to date (all stream branches merged in)
git checkout feature/bhisma-w3
git pull origin feature/bhisma-w3

# 2. Pull latest main (may have KARN/M3 commits since the wave started)
git fetch origin main

# 3. Rebase umbrella onto latest main (or merge — choose one)
git rebase origin/main
# If rebase conflicts arise on 00_ARCHITECTURE files → use merge instead:
# git merge origin/main

# 4. Run full quality gates
cd platform
npm ci
npx tsc --noEmit          # must exit 0 (excluding pre-existing 9 errors in test files)
npx vitest run            # must exit 0
npm run cutover:stage1-smoke 2>/dev/null || echo "smoke needs SMOKE_SESSION_COOKIE"

# 5. Governance scripts
python3 platform/scripts/governance/mirror_enforcer.py   # must exit 0
python3 platform/scripts/governance/schema_validator.py  # exit 0 or 2 (no new CRITICALs)

# 6. If all pass → merge to main with --no-ff
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git merge --no-ff feature/bhisma-w3 \
  -m "merge: bhisma-w3 — [wave summary, e.g. UQE + MON + TRACE complete]"

# 7. Push main
git push origin main

# 8. Delete umbrella branch (local + remote) after confirming main is clean
git branch -d feature/bhisma-w3
git push origin --delete feature/bhisma-w3

# 9. Update PROJECT_BHISMA_SESSION_LOG.md + CURRENT_STATE_v1_0.md
#    Mark the wave CLOSED and point next_session_objective forward.
```

---

## §6 — What to do about the current W2 / phase-o-observatory branch

**Situation (as of 2026-05-02):**
- `feature/phase-o-observatory` has 226 commits ahead of `main` containing:
  - All Wave 2 code (UQE, MON, TRACE, SCHEMA, EVAL, CTX-ASSEMBLY)
  - Phase O Observatory governance work (S0.1 opened)
- `w2-bugs`, `w2-eval-a`, `w2-manifest`, `w2-schema` are all identical to
  each other (all point to `eeb65d9`) and are superseded by phase-o-observatory.

**Recommended sequence (one-time, native authorizes each step):**

```
Step 1 — Verify phase-o-observatory compiles cleanly:
  git checkout feature/phase-o-observatory
  cd platform && npm ci && npx tsc --noEmit && npx vitest run

Step 2 — If clean: merge feature/phase-o-observatory → main
  git checkout main
  git merge --no-ff feature/phase-o-observatory \
    -m "merge: bhisma-w2 + phase-o-s0.1 — Wave 2 complete, Phase O opened"
  git push origin main

Step 3 — Delete the 4 stale identical w2-* branches:
  # Use -D (force), not -d. git branch -d checks reachability against the
  # *current branch* (main), not all branches. Since eeb65d9 lives only on
  # feature/phase-o-observatory and not yet in main, -d will refuse.
  # -D is safe here because the commits ARE reachable from phase-o-observatory
  # — no work is lost.
  git branch -D w2-bugs w2-eval-a w2-manifest w2-schema
  git push origin --delete w2-bugs w2-eval-a w2-manifest w2-schema

Step 4 — Continue Phase O sessions using worktrees from main or
  cut a new umbrella branch for Wave 3 engineering.
```

> ⚠️ Do NOT merge until Step 1 passes. If `tsc` or `vitest` fail,
> open a `BHISMA-W2-INTEGRATION-FIX` session to repair before merging.

---

## §7 — Quick reference: parallel session combinations

| What you're running | Setup needed |
|---------------------|-------------|
| BHISMA stream A + BHISMA stream B | 2 worktrees in Madhav |
| BHISMA + KARN/M3 governance | 2 worktrees in Madhav |
| BHISMA + Ustad | 1 worktree in Madhav + open Ustad directly |
| KARN/M3 + Ustad | 1 worktree in Madhav + open Ustad directly |
| BHISMA + KARN/M3 + Ustad (all 3) | 2 worktrees in Madhav + open Ustad directly |
| 3 parallel BHISMA streams | 3 worktrees in Madhav |

**Rule of thumb:** count how many concurrent sessions touch the Madhav repo.
That number = number of worktrees needed. Ustad always gets its own Antigravity
window pointed directly at `/Users/Dev/Vibe-Coding/Apps/Ustad` — no worktree setup required.

---

*End of BHISMA_PARALLEL_ISOLATION_SETUP.md v1.0 — 2026-05-02*
