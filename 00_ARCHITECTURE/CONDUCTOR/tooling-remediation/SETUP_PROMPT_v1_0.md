# MARSYS-JIS Tooling Remediation — Setup Prompt v1.0

**Paste this into a Claude Code session in Antigravity, pointed at the main Madhav checkout:**
`/Users/Dev/Vibe-Coding/Apps/Madhav` on branch `main`

Enable `--dangerously-skip-permissions` before running.

---

## What this prompt does

Creates the `feature/tooling-remediation` branch, commits all pre-authored conductor
infrastructure files (already written by Cowork to `00_ARCHITECTURE/CONDUCTOR/tooling-remediation/`
and `00_ARCHITECTURE/BRIEFS/`), creates the `MadhavToolingFix` git worktree, and pushes.
After this prompt completes, switch to the worktree and paste the Conductor Kickoff Prompt.

---

## Prompt (paste below this line into Antigravity)

---

You are doing a one-time setup for the MARSYS-JIS Tooling Remediation workstream.
Do not read CLAUDE.md or any governance files — this is purely a git setup session.
Execute all steps in order. Commit once at the end. Do not touch any application code.

**Step 1 — Confirm you are in the main Madhav checkout on main:**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git status
git branch --show-current
```

Expected: `main`, working tree clean (or only untracked files from the Cowork session).
If working tree has staged changes, stash them before proceeding: `git stash`.

**Step 2 — Create the branch:**

```bash
git checkout -b feature/tooling-remediation
```

If the branch already exists: `git checkout feature/tooling-remediation`

**Step 3 — Copy the plan file into the conductor directory (plan was uploaded by Cowork):**

The plan file `MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md` may be in the uploads directory
or at the project root. Move/copy it to the conductor directory:

```bash
# Check if it's at root
ls /Users/Dev/Vibe-Coding/Apps/Madhav/MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md 2>/dev/null

# If found at root, move it
mv /Users/Dev/Vibe-Coding/Apps/Madhav/MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md \
   /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/tooling-remediation/MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md 2>/dev/null || true

# If not at root, it may already be in the conductor directory — check:
ls /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/tooling-remediation/
```

**Step 4 — Stage the pre-authored infrastructure files:**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

git add \
  00_ARCHITECTURE/CONDUCTOR/tooling-remediation/session_queue.yaml \
  00_ARCHITECTURE/CONDUCTOR/tooling-remediation/MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md \
  00_ARCHITECTURE/CONDUCTOR/tooling-remediation/SETUP_PROMPT_v1_0.md \
  00_ARCHITECTURE/CONDUCTOR/tooling-remediation/CONDUCTOR_KICKOFF_PROMPT_v1_0.md \
  00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_TOOLING_REMEDIATION_PHASE_0_v1_0.md

git status
# Verify: 5 files staged as new files
```

**Step 5 — Create an empty CONDUCTOR_LOG.md and CONDUCTOR_HALT_LOG.md for this workstream:**

```bash
cat > /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/tooling-remediation/CONDUCTOR_LOG.md << 'EOF'
# CONDUCTOR_LOG — Tooling Remediation v1.0

Queue: 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/session_queue.yaml
Branch: feature/tooling-remediation
Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
Started: not yet

## Entries

EOF

cat > /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/tooling-remediation/CONDUCTOR_HALT_LOG.md << 'EOF'
# CONDUCTOR_HALT_LOG — Tooling Remediation v1.0

## Open halts

none yet

EOF

git add \
  00_ARCHITECTURE/CONDUCTOR/tooling-remediation/CONDUCTOR_LOG.md \
  00_ARCHITECTURE/CONDUCTOR/tooling-remediation/CONDUCTOR_HALT_LOG.md
```

**Step 6 — Commit:**

```bash
git commit -m "chore: tooling-remediation conductor setup — session_queue (26 sessions), Phase 0 brief, conductor prompt, logs"
```

**Step 7 — Push the branch:**

```bash
git push -u origin feature/tooling-remediation
```

**Step 8 — Create the worktree:**

```bash
git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix feature/tooling-remediation

# Verify
git worktree list
# Expected: both Madhav (main) and MadhavToolingFix (feature/tooling-remediation) listed

ls /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix/00_ARCHITECTURE/CONDUCTOR/tooling-remediation/
# Expected: session_queue.yaml, CONDUCTOR_KICKOFF_PROMPT_v1_0.md, etc.
```

**Step 9 — Activate the Phase 0 brief in the worktree:**

```bash
cp /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix/00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_TOOLING_REMEDIATION_PHASE_0_v1_0.md \
   /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix/CLAUDECODE_BRIEF.md

cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git add CLAUDECODE_BRIEF.md
git commit -m "chore: activate Phase 0 brief as CLAUDECODE_BRIEF.md in worktree"
git push origin feature/tooling-remediation
```

**Step 10 — Confirm setup is complete:**

```bash
echo "=== Worktree list ==="
git worktree list

echo "=== Branch on worktree ==="
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && git branch --show-current

echo "=== Session queue exists ==="
ls -la 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/session_queue.yaml

echo "=== Phase 0 brief active ==="
head -5 CLAUDECODE_BRIEF.md
```

**Setup complete.** Report a summary: worktrees created, files staged, branch pushed.
Then stop — do not proceed into any implementation work. The next step is for the user
to open the MadhavToolingFix worktree in Antigravity and paste the Conductor Kickoff Prompt.

---

*End of SETUP_PROMPT_v1_0.md*
*Authored: 2026-05-24, Cowork session (Tooling Remediation kickoff).*
