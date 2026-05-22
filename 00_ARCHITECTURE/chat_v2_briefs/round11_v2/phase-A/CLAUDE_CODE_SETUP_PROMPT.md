# R11.A Foundation — Claude Code SETUP Prompt

Paste this into a fresh Antigravity Claude Code session pointed at the **main Madhav repo** (`/Users/Dev/Vibe-Coding/Apps/Madhav`). It bootstraps the MadhavR11A worktree for the R11.A Foundation phase.

## What to paste

```
You are setting up the R11.A Foundation phase environment.

Context:
- The main repo is at /Users/Dev/Vibe-Coding/Apps/Madhav (current working
  directory of this session).
- R11.A is the foundation phase of the Multi-Provider Parity arc — see
  /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md
  for the arc overview.
- The R11.A brief bundle + Conductor prompt + queue are already committed
  to main's HEAD (or available as uncommitted files in main's working tree
  if they haven't been committed yet — check git status).
- Goal: create the MadhavR11A worktree on branch chat-v2/round11-a-foundation,
  copy gitignored env files, install deps, smoke-build, validate the queue.

Rules:
- Run each command yourself. Show me the output.
- STOP immediately if any step fails. Do not proceed past a failure;
  tell me what happened.
- Do not edit any source files in this session — pure environment setup.

# Step 1 — Prerequisites
which gh && gh --version
which node && node --version
which python3 && python3 --version
gh auth status

# Step 2 — Confirm R11.A files exist in the main repo
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git rev-parse --abbrev-ref HEAD
git log --oneline -1
test -d 00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-A || { echo "FAIL: phase-A dir missing"; exit 1; }
test -f 00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11V2_MASTER_PLAN_v1_0.md || { echo "FAIL: master plan missing"; exit 1; }
test -f 00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml || { echo "FAIL: R11.A queue missing"; exit 1; }
test -f 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11A_v1_0.md || { echo "FAIL: R11.A Conductor prompt missing"; exit 1; }
ls 00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-A/ | wc -l   # should be ~17 (14 briefs + master plan + 2 Claude Code prompts)
test -f 00_ARCHITECTURE/CAPABILITY_MATRIX.md || { echo "FAIL: capability matrix missing"; exit 1; }
test -f 00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md || { echo "FAIL: roadmap missing"; exit 1; }

# Step 3 — Stage any uncommitted R11 v2 files (idempotent)
if [ -n "$(git status --porcelain 00_ARCHITECTURE/chat_v2_briefs/round11_v2/ 00_ARCHITECTURE/CAPABILITY_MATRIX.md 00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11A_v1_0.md 00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml 2>/dev/null)" ]; then
  echo "INFO: R11 v2 files exist but are not committed yet."
  echo "      Either commit them to main first (recommended) OR proceed with worktree creation"
  echo "      which will inherit whatever is in main's tracked HEAD."
  echo "      Recommendation: commit on main BEFORE running worktree setup:"
  echo "        git add 00_ARCHITECTURE/chat_v2_briefs/round11_v2/ 00_ARCHITECTURE/CAPABILITY_MATRIX.md 00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11A_v1_0.md 00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml 00_ARCHITECTURE/chat_v2_briefs/round11/SUPERSESSION_NOTE.md 00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md"
  echo "        git commit -m 'gov(r11v2): scope Multi-Provider Parity arc — capability matrix, roadmap, R11.A brief bundle'"
  echo "      Then re-run this setup."
  exit 1
fi

# Step 4 — Verify no existing worktree at the target path
if [ -e /Users/Dev/Vibe-Coding/Apps/MadhavR11A ]; then
  echo "FAIL: /Users/Dev/Vibe-Coding/Apps/MadhavR11A already exists."
  echo "If stale: cd /Users/Dev/Vibe-Coding/Apps/Madhav && git worktree remove --force /Users/Dev/Vibe-Coding/Apps/MadhavR11A && rm -rf /Users/Dev/Vibe-Coding/Apps/MadhavR11A"
  exit 1
fi

# Step 5 — Verify branch doesn't exist
if git show-ref --verify --quiet refs/heads/chat-v2/round11-a-foundation; then
  echo "FAIL: branch chat-v2/round11-a-foundation already exists."
  echo "To start fresh: git branch -D chat-v2/round11-a-foundation"
  exit 1
fi

# Step 6 — Capture main HEAD (branch off this specific commit for parallel safety)
MAIN_HEAD=$(git rev-parse main)
echo "main HEAD = $MAIN_HEAD"

# Step 7 — Create the worktree off main HEAD
git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavR11A -b chat-v2/round11-a-foundation "$MAIN_HEAD"

# Step 8 — Verify the new worktree
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A
git rev-parse --abbrev-ref HEAD       # should be chat-v2/round11-a-foundation
git rev-parse HEAD                    # should equal MAIN_HEAD
git status                            # should be clean
ls 00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-A/ | wc -l  # should match main

# Step 9 — Copy gitignored env files (worktrees don't auto-receive these)
for f in /Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env*; do
  if [ -f "$f" ]; then
    cp "$f" /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform/
    echo "copied $(basename $f)"
  fi
done
for f in .npmrc firebase.json.local; do
  src="/Users/Dev/Vibe-Coding/Apps/Madhav/platform/$f"
  if [ -f "$src" ]; then
    cp "$src" /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform/$f
    echo "copied $f"
  fi
done
for f in /Users/Dev/Vibe-Coding/Apps/Madhav/serviceAccount*.json; do
  if [ -f "$f" ]; then
    cp "$f" /Users/Dev/Vibe-Coding/Apps/MadhavR11A/
    echo "copied $(basename $f)"
  fi
done
ls -la /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform/.env*

# Step 10 — Install Python deps for queue validator (idempotent)
pip3 install --break-system-packages --quiet pyyaml jsonschema 2>/dev/null || pip3 install --user --quiet pyyaml jsonschema

# Step 11 — Validate the R11.A queue
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A
python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py session_queue_R11A.yaml
# Expected: "OK — 14 entries valid (session_queue_R11A.yaml)"

# Step 12 — Install Node deps
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
npm install --no-audit --no-fund

# Step 13 — Smoke-build
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
npm run build 2>&1 | tail -20
# If this fails, STOP. Tell me. Do NOT proceed.

# Step 14 — Readiness report
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo " R11.A FOUNDATION ENVIRONMENT SETUP COMPLETE"
echo "─────────────────────────────────────────────────────────────────────"
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A
echo " Worktree:        $(pwd)"
echo " Branch:          $(git branch --show-current)"
echo " HEAD:            $(git rev-parse --short HEAD)"
echo " Base (main):     $(git log -1 --format=%h main)"
QUEUE_ENTRIES=$(python3 -c "import yaml; print(len(yaml.safe_load(open('00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml'))['entries']))")
echo " Queue entries:   $QUEUE_ENTRIES (expected: 14)"
echo " Brief files:     $(ls 00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-A/ | wc -l)"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo " NEXT STEP — kick off the R11.A Conductor in a fresh Antigravity session"
echo " pointed at /Users/Dev/Vibe-Coding/Apps/MadhavR11A:"
echo ""
echo "   1. Launch:"
echo "        cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A && claude --dangerously-skip-permissions"
echo "   2. Paste the prompt body from:"
echo "        /Users/Dev/Vibe-Coding/Apps/MadhavR11A/00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-A/CLAUDE_CODE_KICKOFF_PROMPT.md"
echo "      (the block inside the triple-backtick code fence)"
echo "   3. Conductor begins the autonomous run."
echo ""
echo " Cowork (the chat that scoped R11 v2) is watching for halt banners."
```
