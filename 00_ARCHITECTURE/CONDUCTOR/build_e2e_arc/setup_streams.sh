#!/usr/bin/env bash
# setup_streams.sh — create 4 worktrees + branches for the build E2E arc
# Invoked by the Conductor session ONCE after pre-flight smoke succeeds.
# Idempotent: if a worktree already exists, prints a warning and continues.
#
# Resulting layout:
#   /Users/Dev/Vibe-Coding/Apps/MadhavHardeningCI  on feat/hardening-ci   (base: main)
#   /Users/Dev/Vibe-Coding/Apps/MadhavDataPlumbing on feat/data-plumbing  (base: feature/ux-workflow-overhaul)
#   /Users/Dev/Vibe-Coding/Apps/MadhavVisualV2     on feat/visual-v2      (base: feature/ux-workflow-overhaul)
#   /Users/Dev/Vibe-Coding/Apps/MadhavFunnelPolish on feat/funnel-polish  (base: feature/ux-workflow-overhaul)
set -euo pipefail

REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
cd "$REPO"
git fetch origin --prune

mkw() {
  local path="$1" branch="$2" base="$3"
  if [ -d "$path" ]; then
    echo "==> worktree already exists at $path — skipping"
    return 0
  fi
  if git show-ref --verify --quiet "refs/heads/$branch"; then
    echo "==> branch $branch exists locally; binding worktree to it"
    git worktree add "$path" "$branch"
  elif git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
    echo "==> branch $branch exists on origin; checking out"
    git worktree add "$path" -b "$branch" "origin/$branch"
  else
    echo "==> creating $branch off $base"
    git worktree add "$path" -b "$branch" "origin/$base"
  fi
}

mkw "/Users/Dev/Vibe-Coding/Apps/MadhavHardeningCI"  "feat/hardening-ci"  "main"
mkw "/Users/Dev/Vibe-Coding/Apps/MadhavDataPlumbing" "feat/data-plumbing" "feature/ux-workflow-overhaul"
mkw "/Users/Dev/Vibe-Coding/Apps/MadhavVisualV2"     "feat/visual-v2"     "feature/ux-workflow-overhaul"
mkw "/Users/Dev/Vibe-Coding/Apps/MadhavFunnelPolish" "feat/funnel-polish" "feature/ux-workflow-overhaul"

echo ""
git worktree list
echo ""
echo "==> 4 worktrees ready. Conductor: print the 4 kickoff prompts next."
