---
artifact: PATTERN_2PLUS_LAUNCH_GUIDE.md
project_name: Claude Takeover
status: CURRENT
authored_on: 2026-05-22
role: >
  Step-by-step launch guide for the Pattern 2+ topology of Claude Takeover
  (R11 v2 Multi-Provider Parity active arc). Contains the Claude Code
  paste-prompts the native pastes into Antigravity sessions.
---

# Claude Takeover — Pattern 2+ Launch Guide (multi-session backup)

> **Project codename:** Claude Takeover. R11 v2 Multi-Provider Parity active arc, Pattern 2+ parallel topology.

> **⚠ Primary launch path is now the META-CONDUCTOR** (single Antigravity session orchestrates everything). See `META_CONDUCTOR_KICKOFF_PROMPT.md` for the recommended single-paste-prompt launch.

> This Pattern 2+ multi-session guide is preserved as a **backup launch path** for cases where the native prefers explicit per-phase Antigravity sessions instead of the single-session Meta-Conductor.

This guide gives you everything to launch R11.A through R11.E using the Pattern 2+ parallel topology (3 Antigravity sessions, one per stream).

## Step 1 — Commit the R11 v2 governance bundle to main + create MadhavR11A worktree

Paste into an Antigravity Claude Code session pointed at `/Users/Dev/Vibe-Coding/Apps/Madhav`:

```
You are launching R11 v2 Pattern 2+ topology. First, commit the governance
bundle (capability matrix + roadmap + R11.A/B/CDE bundles + Conductor prompts
+ queues + Claude Code prompts) to main, then create the MadhavR11A worktree
for the foundation phase.

Do this step by step. Show each command's output. STOP on any failure.

# Step 1.1 — Verify governance bundle is on disk and uncommitted
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git status --short 00_ARCHITECTURE/CAPABILITY_MATRIX.md \
                  00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md \
                  00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md \
                  00_ARCHITECTURE/chat_v2_briefs/round11_v2/ \
                  00_ARCHITECTURE/chat_v2_briefs/round11/SUPERSESSION_NOTE.md \
                  00_ARCHITECTURE/chat_v2_briefs/round11/R11_MASTER_PLAN_v1_0.md \
                  00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md \
                  00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11A_v1_0.md \
                  00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11B_v1_0.md \
                  00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11CDE_v1_0.md \
                  00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml \
                  00_ARCHITECTURE/CONDUCTOR/session_queue_R11B.yaml \
                  00_ARCHITECTURE/CONDUCTOR/session_queue_R11CDE.yaml

# Step 1.2 — Stage and commit
git add 00_ARCHITECTURE/CAPABILITY_MATRIX.md \
        00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md \
        00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md \
        00_ARCHITECTURE/chat_v2_briefs/round11_v2/ \
        00_ARCHITECTURE/chat_v2_briefs/round11/SUPERSESSION_NOTE.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/R11_MASTER_PLAN_v1_0.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md \
        00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11A_v1_0.md \
        00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11B_v1_0.md \
        00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11CDE_v1_0.md \
        00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml \
        00_ARCHITECTURE/CONDUCTOR/session_queue_R11B.yaml \
        00_ARCHITECTURE/CONDUCTOR/session_queue_R11CDE.yaml

git commit -m "gov(claude-takeover): scope Multi-Provider Parity arc (R11.A-E active, Pattern 2+ parallel topology)

Project codename: Claude Takeover. Active arc R11 v2 R11.A through R11.E.

CAPABILITY_MATRIX.md + MULTI_PROVIDER_PARITY_ROADMAP.md + USER_INTERACTION_PREFERENCES.md.

R11 v1 SUPERSEDED. Claude Takeover active arc:
- R11.A foundation (14 entries; A-S2..A-S6 parallel_group: provider-adapters)
- R11.B look-and-feel (10 entries) parallel with
- R11.CDE composite (27 entries: C+R11C-MERGE + D+R11D-MERGE + E+R11E-MERGE)

Total: 49 sessions across 3 phase queues, ~38-54h wall-clock, ~3.5-4.5 weeks.

R11.F-K deferred to future arc. Hide-and-hint fallback policy locked.
NATIVE_RULINGS §1-8 carry forward."

git log --oneline -1
MAIN_HEAD=$(git rev-parse main)
echo "main HEAD now at $MAIN_HEAD"

# Step 1.3 — Prerequisites
which gh && gh --version
which node && node --version
gh auth status
test -f /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/validate_queue.py || { echo "FAIL"; exit 1; }

# Step 1.4 — Verify no existing MadhavR11A worktree
if [ -e /Users/Dev/Vibe-Coding/Apps/MadhavR11A ]; then
  echo "FAIL: MadhavR11A already exists. Remove first: git worktree remove --force /Users/Dev/Vibe-Coding/Apps/MadhavR11A && rm -rf /Users/Dev/Vibe-Coding/Apps/MadhavR11A"; exit 1
fi
if git show-ref --verify --quiet refs/heads/chat-v2/round11-a-foundation; then
  echo "FAIL: branch exists. git branch -D chat-v2/round11-a-foundation"; exit 1
fi

# Step 1.5 — Create MadhavR11A worktree off main HEAD
git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavR11A -b chat-v2/round11-a-foundation "$MAIN_HEAD"

# Step 1.6 — Verify
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD

# Step 1.7 — Copy gitignored env files
for f in /Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env*; do
  [ -f "$f" ] && cp "$f" /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform/ && echo "copied $(basename $f)"
done

# Step 1.8 — Python deps + validate queue
pip3 install --break-system-packages --quiet pyyaml jsonschema 2>/dev/null || pip3 install --user --quiet pyyaml jsonschema
python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py session_queue_R11A.yaml

# Step 1.9 — npm install + smoke build
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
npm install --no-audit --no-fund
npm run build 2>&1 | tail -20
# If build fails: STOP. Tell me. Do NOT proceed.

# Step 1.10 — Readiness banner
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo " R11.A FOUNDATION READY"
echo " Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11A"
echo " Branch:   $(git -C /Users/Dev/Vibe-Coding/Apps/MadhavR11A branch --show-current)"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo " NEXT: Open a fresh Antigravity session pointed at MadhavR11A and paste"
echo "       the R11.A KICKOFF prompt from:"
echo "       /Users/Dev/Vibe-Coding/Apps/MadhavR11A/00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-A/CLAUDE_CODE_KICKOFF_PROMPT.md"
```

## Step 2 — Kick off R11.A Conductor

Open a fresh Antigravity Claude Code session pointed at `/Users/Dev/Vibe-Coding/Apps/MadhavR11A`. Launch with:

```
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A
claude --dangerously-skip-permissions
```

Paste the contents of `00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-A/CLAUDE_CODE_KICKOFF_PROMPT.md` (the prompt body inside the triple-backtick code fence). The R11.A Conductor runs autonomously. A-S2..A-S6 will be spawned concurrently per the parallel_group marker.

When R11A-MERGE auto-merges to main, proceed to Step 3.

## Step 3 — Phase-2 parallel launch (after R11A-MERGE lands in main)

Open a fresh Antigravity Claude Code session pointed at `/Users/Dev/Vibe-Coding/Apps/Madhav` (back at the main repo). Paste:

```
You are setting up R11 v2 Phase 2 — the Pattern 2+ parallel launch. R11.A
has merged to main. Now create MadhavR11B (stream-1) and MadhavR11CDE
(stream-2) worktrees, copy env files, install deps, smoke-build both.

After both are ready, the native will open TWO simultaneous Antigravity
sessions — one per worktree — and paste their respective KICKOFF prompts.

Do this step by step. STOP on any failure.

# Step 3.1 — Verify R11.A merged
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin main
git log --oneline -10 main | head -10
# Confirm a recent commit references "R11.A" or "round11-a-foundation".

MAIN_HEAD=$(git rev-parse main)
echo "main HEAD = $MAIN_HEAD"

# Step 3.2 — Verify no existing R11.B or R11.CDE worktrees
for w in MadhavR11B MadhavR11CDE; do
  if [ -e /Users/Dev/Vibe-Coding/Apps/$w ]; then
    echo "FAIL: /Users/Dev/Vibe-Coding/Apps/$w exists. Remove first."; exit 1
  fi
done
for b in chat-v2/round11-b-look-and-feel chat-v2/round11-cde; do
  if git show-ref --verify --quiet refs/heads/$b; then
    echo "FAIL: branch $b exists. git branch -D $b"; exit 1
  fi
done

# Step 3.3 — Create MadhavR11B worktree (stream-1)
git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavR11B -b chat-v2/round11-b-look-and-feel "$MAIN_HEAD"
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B
git rev-parse --abbrev-ref HEAD
for f in /Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env*; do
  [ -f "$f" ] && cp "$f" /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform/ && echo "R11B: copied $(basename $f)"
done
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform
npm install --no-audit --no-fund
npm run build 2>&1 | tail -10
# If build fails: STOP.

# Step 3.4 — Create MadhavR11CDE worktree (stream-2)
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE -b chat-v2/round11-cde "$MAIN_HEAD"
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE
git rev-parse --abbrev-ref HEAD
for f in /Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env*; do
  [ -f "$f" ] && cp "$f" /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform/ && echo "R11CDE: copied $(basename $f)"
done
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
npm install --no-audit --no-fund
npm run build 2>&1 | tail -10
# If build fails: STOP.

# Step 3.5 — Validate queues
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B
python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py session_queue_R11B.yaml
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE
python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py session_queue_R11CDE.yaml

# Step 3.6 — Readiness banner
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo " R11.B + R11.CDE BOTH READY — Pattern 2+ parallel launch is GO"
echo "─────────────────────────────────────────────────────────────────────"
echo " Stream-1 (R11.B):"
echo "   Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11B"
echo "   Branch:   $(git -C /Users/Dev/Vibe-Coding/Apps/MadhavR11B branch --show-current)"
echo " Stream-2 (R11.CDE):"
echo "   Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE"
echo "   Branch:   $(git -C /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE branch --show-current)"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo " NEXT: Open TWO simultaneous Antigravity sessions:"
echo ""
echo " Session A (stream-1):"
echo "   cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B && claude --dangerously-skip-permissions"
echo "   Paste KICKOFF body from:"
echo "   /Users/Dev/Vibe-Coding/Apps/MadhavR11B/00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-B/CLAUDE_CODE_KICKOFF_PROMPT.md"
echo ""
echo " Session B (stream-2):"
echo "   cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE && claude --dangerously-skip-permissions"
echo "   Paste KICKOFF body from:"
echo "   /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-CDE/CLAUDE_CODE_KICKOFF_PROMPT.md"
echo ""
echo " Both Conductors run autonomously. Cowork watches for halts."
```

## Step 4 — Launch both KICKOFF Conductors simultaneously

Open two Antigravity sessions side-by-side. Paste R11.B KICKOFF into the R11B-pointed session; paste R11.CDE KICKOFF into the R11CDE-pointed session. Both run concurrently from this moment.

## Halt + complete handling

If either Conductor halts, the native opens Cowork (this chat), pastes the halt banner, Cowork triages and provides a paste-prompt to resume in a fresh Antigravity session for that stream. The other stream continues independently.

When R11B-MERGE auto-merges AND R11E-MERGE auto-merges, the active R11 v2 arc is COMPLETE. Cowork then updates governance docs + opens a closing conversation about R12.

---

*End of PATTERN_2PLUS_LAUNCH_GUIDE.md.*
