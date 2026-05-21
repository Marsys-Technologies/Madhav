#!/usr/bin/env bash
# MCP — MARSYS-JIS Model Context Protocol Server — worktree + branch setup
# Run from a terminal on your own machine (NOT from inside the Cowork sandbox).
# Idempotent: safe to re-run; aborts cleanly if the worktree already exists.
#
# Why this is a script and not auto-run:
# - Cowork sessions are sandboxed to /Users/Dev/Vibe-Coding/Apps/Madhav only.
# - Creating a sibling worktree at /Users/Dev/Vibe-Coding/Apps/MadhavMCP
#   requires running git from outside that sandbox.
# - You retain explicit control over the worktree lifecycle for parallel
#   workstreams.

set -euo pipefail

MAIN_REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
WORKTREE="/Users/Dev/Vibe-Coding/Apps/MadhavMCP"
BRANCH="feature/mcp-server"

# Files this script needs to live in the main repo before it runs:
#   00_ARCHITECTURE/CONDUCTOR/session_queue_MCP.yaml
#   00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_MCP_v1_0.md
#   00_ARCHITECTURE/CONDUCTOR/MCP_KICKOFF_PROMPT_v1_0.md
#   00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
#   00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_0_AUTHOR_v1_0.md
#   00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
REQUIRED_FILES=(
  "00_ARCHITECTURE/CONDUCTOR/session_queue_MCP.yaml"
  "00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_MCP_v1_0.md"
  "00_ARCHITECTURE/CONDUCTOR/MCP_KICKOFF_PROMPT_v1_0.md"
  "00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md"
  "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_0_AUTHOR_v1_0.md"
  "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md"
)

echo "▶  MCP worktree setup"
echo "    Repo:     $MAIN_REPO"
echo "    Worktree: $WORKTREE"
echo "    Branch:   $BRANCH"
echo

# 1. Sanity checks
if [[ ! -d "$MAIN_REPO/.git" ]]; then
  echo "✗  $MAIN_REPO is not a git working tree. Aborting." >&2
  exit 1
fi

if [[ -e "$WORKTREE" ]]; then
  echo "✗  $WORKTREE already exists. If this is an old/stale worktree, remove it first:" >&2
  echo "    cd $MAIN_REPO && git worktree remove --force $WORKTREE" >&2
  echo "    rm -rf $WORKTREE" >&2
  exit 1
fi

# 2. Verify required files exist in main
cd "$MAIN_REPO"
for f in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "✗  Required file missing: $MAIN_REPO/$f" >&2
    echo "    Cowork should have authored these before you ran this script." >&2
    exit 1
  fi
done
echo "✓  All required governance files present"

# 3. Verify main branch exists and capture HEAD for parallel-workstream safety
if ! git rev-parse --verify main >/dev/null 2>&1; then
  echo "✗  Branch 'main' not found in $MAIN_REPO. Aborting." >&2
  exit 1
fi
MAIN_HEAD=$(git rev-parse main)
echo "✓  main HEAD = $MAIN_HEAD"

# 4. Verify the new branch doesn't already exist
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "✗  Branch '$BRANCH' already exists. Aborting." >&2
  echo "    To start fresh: git branch -D $BRANCH" >&2
  exit 1
fi

# 5. Create the worktree off main HEAD (NOT off current HEAD —
#    main has uncommitted work from parallel workstreams that should not leak in)
echo "▶  Creating worktree off main HEAD..."
git worktree add "$WORKTREE" -b "$BRANCH" "$MAIN_HEAD"
echo "✓  Worktree created at $WORKTREE on branch $BRANCH"

# 6. Confirm the governance files made it into the worktree (they should,
#    since they were committed to main before the worktree was branched).
#    If MCP_BRIEF and the kickoff/queue files aren't committed in main yet,
#    copy them across.
cd "$WORKTREE"
NEED_COPY=false
for f in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    NEED_COPY=true
    break
  fi
done

if [[ "$NEED_COPY" == "true" ]]; then
  echo "▶  Some required files are not yet committed to main. Copying from main worktree..."
  for f in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$f" ]] && [[ -f "$MAIN_REPO/$f" ]]; then
      mkdir -p "$(dirname "$f")"
      cp "$MAIN_REPO/$f" "$f"
      echo "    + $f"
    fi
  done

  git add "${REQUIRED_FILES[@]}"
  git commit -m "feat(governance): MCP workstream — master brief + conductor scaffolding

MCP — MARSYS-JIS Model Context Protocol Server. Exposes the MARSYS-JIS
retrieval and synthesis surface to Claude Chat and Cowork via hosted
HTTP/SSE MCP server (Cloud Run sidecar). Layered tool shape: ask_madhav
runs the full pipeline; 10 curated primitives + plan/execute_plan + asset
read + observability. API-key auth bound to Firebase UID + audience_tier.

9-session sequential autonomous run via Conductor:
  MCP-0-AUTHOR → authors remaining 7 briefs
  MCP-1-S1     → foundation (platform endpoint + auth + admin)
  MCP-2-S1     → MCP server scaffold + Tier 1/2 tools
  MCP-2-S2     → tool descriptions + chart-overview/house-rules resources
  MCP-3-S1     → 10 surgical primitives + dispatcher
  MCP-3-S2     → read_asset + observability + rate limiting
  MCP-4-S1     → writes (log_prediction/record_outcome/flag_disagreement)
  MCP-4-S2     → red-team pass per §IS.8(b)
  MCP-MERGE    → push, open PR, auto-merge (native override)

Branch: feature/mcp-server
Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
Base: main HEAD at setup time"
  COMMIT_SHA=$(git rev-parse HEAD)
  echo "✓  Governance files committed at $COMMIT_SHA"
else
  echo "✓  All required files already present in worktree (already committed in main)"
fi

# 7. Next steps
echo
echo "═══════════════════════════════════════════════════════════════════"
echo " MCP worktree ready."
echo
echo " Next steps (yours):"
echo "   1. Open a fresh Claude Code session inside the new worktree:"
echo "        cd $WORKTREE"
echo "        claude --dangerously-skip-permissions"
echo
echo "   2. Paste the contents of:"
echo "        $WORKTREE/00_ARCHITECTURE/CONDUCTOR/MCP_KICKOFF_PROMPT_v1_0.md"
echo "      into the Claude Code chat. The Conductor begins the autonomous"
echo "      loop and runs all 9 sessions sequentially."
echo
echo "   3. Watch from this Cowork chat. If the Conductor halts, paste the"
echo "      same kickoff prompt again in a fresh Claude Code session — the"
echo "      disk state will pick up exactly where it left off."
echo
echo " Parallel workstream note:"
echo "   This MCP worktree was created off main HEAD = $MAIN_HEAD"
echo "   so uncommitted work in $MAIN_REPO does not leak into the MCP branch."
echo "═══════════════════════════════════════════════════════════════════"
