#!/usr/bin/env bash
# setup_streams.sh — One-shot worktree creation for 4-stream parallel Conductor run.
# Run once from main repo root BEFORE opening 4 Antigravity windows.
#
# Usage:
#   bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/setup_streams.sh
#
# Creates:
#   /Users/Dev/Vibe-Coding/Apps/MadhavStream-A on feature/build-orch/stream-a
#   /Users/Dev/Vibe-Coding/Apps/MadhavStream-B on feature/build-orch/stream-b
#   /Users/Dev/Vibe-Coding/Apps/MadhavStream-C on feature/build-orch/stream-c
#   /Users/Dev/Vibe-Coding/Apps/MadhavStream-D on feature/build-orch/stream-d
#
# After setup completes, open 4 Antigravity windows — each in one of the 4 worktrees —
# and paste the corresponding KICKOFF_STREAM_<X>.md prompt.

set -euo pipefail

MAIN_DIR="/Users/Dev/Vibe-Coding/Apps/Madhav"
PARENT_DIR="/Users/Dev/Vibe-Coding/Apps"

cd "$MAIN_DIR"

echo "==> Pre-flight: confirm clean main branch + up-to-date"
git checkout main
git pull origin main

# Detect uncommitted changes that would be inherited by worktrees
if ! git diff-index --quiet HEAD --; then
  echo ""
  echo "⚠️  WARNING: Uncommitted changes detected on main:"
  git status --short
  echo ""
  echo "These will be reflected in every new worktree."
  echo "Recommendation: commit or stash before continuing."
  read -r -p "Continue anyway? [y/N] " ANS
  case "$ANS" in
    y|Y|yes|YES) echo "Proceeding with dirty tree..." ;;
    *) echo "Aborted. Commit/stash changes and re-run."; exit 1 ;;
  esac
fi

echo ""
echo "==> Creating 4 stream branches + worktrees"

for STREAM in A B C D; do
  # Portable lowercase (bash 3.2 compat — macOS ships bash 3.2)
  STREAM_LOWER="$(echo "$STREAM" | tr '[:upper:]' '[:lower:]')"
  BRANCH="feature/build-orch/stream-${STREAM_LOWER}"
  WORKTREE="${PARENT_DIR}/MadhavStream-${STREAM}"

  echo ""
  echo "--- Stream ${STREAM} ---"

  # Create branch from main if not exists
  if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
    echo "Branch ${BRANCH} already exists locally"
  else
    git branch "${BRANCH}" main
    echo "Branch ${BRANCH} created from main"
  fi

  # Push branch to origin
  git push --set-upstream origin "${BRANCH}" 2>/dev/null || echo "Branch already pushed"

  # Create worktree
  if [ -d "${WORKTREE}" ]; then
    echo "Worktree ${WORKTREE} already exists — skipping (use git worktree remove + re-run if needed)"
  else
    git worktree add "${WORKTREE}" "${BRANCH}"
    echo "Worktree created: ${WORKTREE}"
  fi
done

echo ""
echo "==> Initializing CLAIM_LEDGER.yaml on main if absent"
if [ ! -f "00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CLAIM_LEDGER.yaml" ]; then
  echo "CLAIM_LEDGER.yaml missing — should have been authored by Cowork; halt"
  exit 1
fi

echo ""
echo "==> Pre-flight CHECK on each worktree"
for STREAM in A B C D; do
  WORKTREE="${PARENT_DIR}/MadhavStream-${STREAM}"
  cd "${WORKTREE}"
  echo ""
  echo "--- ${WORKTREE} ---"
  git status --short
  git log --oneline -3
done

cd "$MAIN_DIR"

echo ""
echo "============================================================"
echo "SETUP COMPLETE. 4 worktrees ready."
echo ""
echo "NEXT: Open 4 Antigravity windows (one per worktree) and paste:"
echo "  Window 1 (Stream A): cd ${PARENT_DIR}/MadhavStream-A"
echo "                      paste 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/streams/KICKOFF_STREAM_A.md"
echo "  Window 2 (Stream B): cd ${PARENT_DIR}/MadhavStream-B"
echo "                      paste 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/streams/KICKOFF_STREAM_B.md"
echo "  Window 3 (Stream C): cd ${PARENT_DIR}/MadhavStream-C"
echo "                      paste 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/streams/KICKOFF_STREAM_C.md"
echo "  Window 4 (Stream D): cd ${PARENT_DIR}/MadhavStream-D"
echo "                      paste 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/streams/KICKOFF_STREAM_D.md"
echo ""
echo "Each Conductor runs fully autonomously with --dangerously-skip-permissions."
echo "Monitor at https://storage.googleapis.com/marsys-tracker-public/index.html"
echo "============================================================"
