# R11 — Claude Code SETUP Prompt

Run this ONCE in a fresh Claude Code session pointed at the **main Madhav repo
root** (`/Users/Dev/Vibe-Coding/Apps/Madhav`), BEFORE you create the MadhavR11
worktree.

It bootstraps the environment: verifies prerequisites, creates the worktree via
SETUP_WORKTREE.sh, validates the R11 queue, and prepares the Conductor logs.

## What to paste into Claude Code

```
You are setting up the R11 environment for autonomous execution.

Working directory: /Users/Dev/Vibe-Coding/Apps/Madhav
Goal: Create the MadhavR11 worktree on branch chat-v2/round11-claude-parity,
move the R11 briefs into it, commit them, validate the queue, and confirm the
Conductor is ready to launch.

Do this step by step. Run each command yourself. Show me the output.

# Step 1 — Prerequisites
which gh && gh --version
which node && node --version
which python3 && python3 --version
test -f /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/validate_queue.py && echo "validate_queue.py present" || echo "MISSING validate_queue.py"
test -f /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/chat_v2_briefs/round11/SETUP_WORKTREE.sh && echo "SETUP_WORKTREE.sh present" || echo "MISSING SETUP_WORKTREE.sh"

# Step 2 — Verify gh CLI is authenticated (needed for R11-MERGE later)
gh auth status

# Step 3 — Run the worktree setup script
# This creates /Users/Dev/Vibe-Coding/Apps/MadhavR11, moves the briefs in, commits them.
bash /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/chat_v2_briefs/round11/SETUP_WORKTREE.sh

# Step 4 — Verify the worktree and branch
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11
git status
git log --oneline -5
ls 00_ARCHITECTURE/chat_v2_briefs/round11/

# Step 5 — Install Python deps for queue validator (if not already installed)
pip3 install --break-system-packages --quiet pyyaml jsonschema || pip3 install --user --quiet pyyaml jsonschema

# Step 6 — Validate the R11 queue against the schema
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11
python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py session_queue_R11.yaml
# Should print: "All 17 entries valid" or similar and exit 0.

# Step 7 — Install Node deps inside the worktree (independent node_modules per worktree)
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11/platform
npm install --no-audit --no-fund

# Step 8 — Smoke-build to confirm the worktree is functional
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11/platform
npm run build 2>&1 | tail -20
# If build fails, halt and tell me; do NOT proceed to the Conductor kickoff.

# Step 9 — Verify the Conductor files are visible in the worktree
test -f /Users/Dev/Vibe-Coding/Apps/MadhavR11/00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11_v1_0.md && echo "Conductor prompt present"
test -f /Users/Dev/Vibe-Coding/Apps/MadhavR11/00_ARCHITECTURE/CONDUCTOR/session_queue_R11.yaml && echo "Queue present"

# Step 10 — Report readiness
echo "═══════════════════════════════════════════════════════════════════"
echo " R11 SETUP COMPLETE"
echo "─────────────────────────────────────────────────────────────────────"
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11
echo " Worktree:       $(pwd)"
echo " Branch:         $(git branch --show-current)"
echo " HEAD:           $(git rev-parse --short HEAD)"
echo " Queue entries:  $(python3 -c "import yaml; print(len(yaml.safe_load(open('00_ARCHITECTURE/CONDUCTOR/session_queue_R11.yaml'))['entries']))")"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo " Next: open a FRESH Claude Code session pointed at:"
echo "   /Users/Dev/Vibe-Coding/Apps/MadhavR11"
echo " Then paste the contents of:"
echo "   00_ARCHITECTURE/chat_v2_briefs/round11/CLAUDE_CODE_KICKOFF_PROMPT.md"
echo ""

If any step fails, stop and tell me what happened. Do not proceed past a failure.
```

## Why a fresh Claude Code session for the kickoff?

The Conductor uses its 200K-token context to manage 17 sub-agent runs. The setup
above consumes a few thousand tokens. A fresh session for the Conductor gives it
the full budget for orchestration + sub-agent FINAL_SUMMARY processing.

## After setup completes

Open a new Claude Code session inside `/Users/Dev/Vibe-Coding/Apps/MadhavR11`
and paste the contents of `CLAUDE_CODE_KICKOFF_PROMPT.md`.
