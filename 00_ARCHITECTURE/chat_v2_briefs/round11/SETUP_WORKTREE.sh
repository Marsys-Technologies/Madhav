#!/usr/bin/env bash
# R11 — Chat V2 Claude Parity — worktree + branch setup
# Run from a terminal on your own machine (NOT from inside the Cowork sandbox).
# Idempotent: safe to re-run; aborts cleanly if the worktree already exists.
#
# Why this is a script and not auto-run:
# - Cowork sessions are sandboxed to /Users/Dev/Vibe-Coding/Apps/Madhav only.
# - Creating a sibling worktree at /Users/Dev/Vibe-Coding/Apps/MadhavR11
#   requires running git from outside that sandbox.
# - You retain explicit control over the worktree lifecycle for the three
#   parallel projects (#1 R11, #2 ?, #3 ?).

set -euo pipefail

MAIN_REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
WORKTREE="/Users/Dev/Vibe-Coding/Apps/MadhavR11"
BRANCH="chat-v2/round11-claude-parity"
BRIEFS_REL="00_ARCHITECTURE/chat_v2_briefs/round11"

echo "▶  R11 worktree setup"
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

if [[ ! -d "$MAIN_REPO/$BRIEFS_REL" ]]; then
  echo "✗  R11 briefs not found at $MAIN_REPO/$BRIEFS_REL. Aborting." >&2
  exit 1
fi

# 2. Verify main exists and capture its HEAD for parallel-workstream safety
cd "$MAIN_REPO"
if ! git rev-parse --verify main >/dev/null 2>&1; then
  echo "✗  Branch 'main' not found in $MAIN_REPO. Aborting." >&2
  exit 1
fi
MAIN_HEAD=$(git rev-parse main)
echo "✓  main HEAD = $MAIN_HEAD"

# 3. Verify the new branch doesn't already exist
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "✗  Branch '$BRANCH' already exists. Aborting." >&2
  echo "    To start fresh: git branch -D $BRANCH" >&2
  exit 1
fi

# 4. Create the worktree off main HEAD (NOT off current HEAD —
#    main has uncommitted work from parallel projects that should not leak in)
echo "▶  Creating worktree off main HEAD..."
git worktree add "$WORKTREE" -b "$BRANCH" "$MAIN_HEAD"
echo "✓  Worktree created at $WORKTREE on branch $BRANCH"

# 5. Move the round11 briefs from main's working dir to the new worktree
echo "▶  Moving R11 briefs from main worktree to R11 worktree..."
TARGET="$WORKTREE/$BRIEFS_REL"
mkdir -p "$(dirname "$TARGET")"

# rsync would handle this most cleanly but isn't always installed; use cp + rm
cp -R "$MAIN_REPO/$BRIEFS_REL" "$TARGET"
rm -rf "$MAIN_REPO/$BRIEFS_REL"
echo "✓  Briefs now live at $TARGET"
echo "✓  Removed from main worktree (they belong on the branch only until PR merges)"

# 6. Commit the briefs on the new branch
cd "$WORKTREE"
git add "$BRIEFS_REL"
git commit -m "feat(governance): R11 (Chat V2 Claude Parity) — master plan + 16 sub-briefs

Round 11 of the Chat V2 workstream brings the consume surface to Claude.ai
parity on three axes:
  V (Visual): typography, palette, message shape, composer, sidebar, markdown.
  S (Streaming): pre-token indicator, smooth-stream v3, ext-thinking collapse,
                 inline tool cards, stop-and-retain.
  O (Orchestration): system-prompt layout, prompt-cache breakpoints, agentic
                     tool loop, inline citations, adaptive thinking effort.

16 sub-briefs at 00_ARCHITECTURE/chat_v2_briefs/round11/.
Master plan declares 4 open native-input items that gate V-S1, V-S2, O-S2, O-S4.

Branch: chat-v2/round11-claude-parity
Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11
Base: main HEAD at setup time"
COMMIT_SHA=$(git rev-parse HEAD)
echo "✓  Briefs committed at $COMMIT_SHA"

# 7. Next steps
echo
echo "═══════════════════════════════════════════════════════════════════"
echo " R11 worktree ready."
echo
echo " Next steps (yours):"
echo "   1. Open a Cowork session inside the new worktree directory:"
echo "        $WORKTREE"
echo "   2. In the session, rule on the 4 Open Native-Input Items in"
echo "        $WORKTREE/$BRIEFS_REL/R11_MASTER_PLAN_v1_0.md"
echo "        (Decision Log section)."
echo "   3. Then begin V-S1. Sequential single-stream execution per master plan."
echo
echo " Parallel workstream note:"
echo "   Two other projects are reportedly running in parallel worktrees."
echo "   This R11 worktree was created off main HEAD = $MAIN_HEAD"
echo "   so uncommitted work in $MAIN_REPO does not leak into the R11 branch."
echo
echo " Optional governance step (not done automatically):"
echo "   Amend CLAUDE.md §E to declare R11 as the 10th concurrent workstream."
echo "   Recommended to do this AFTER the three parallel projects have all set"
echo "   up their worktrees, in a single coordinated amendment, to avoid"
echo "   merge conflicts on CLAUDE.md."
echo "═══════════════════════════════════════════════════════════════════"
