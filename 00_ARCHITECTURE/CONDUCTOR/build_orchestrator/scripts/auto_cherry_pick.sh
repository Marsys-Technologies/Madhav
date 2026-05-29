#!/bin/bash
# Auto cherry-pick session commits from worktree to main.
# Usage: auto_cherry_pick.sh <session-id> <worktree-path>
set -e
SESSION_ID="$1"
WORKTREE="$2"
REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"

[ -z "$SESSION_ID" ] && echo "ERROR: session-id required" && exit 1
[ -z "$WORKTREE" ] && echo "ERROR: worktree path required" && exit 1

LOCK="$REPO/.conductor_main_lock"

acquire_lock() {
  local i=0
  while [ -f "$LOCK" ] && [ $i -lt 60 ]; do
    echo "Waiting for main lock (${i}s)..."
    sleep 1; i=$((i+1))
  done
  [ -f "$LOCK" ] && echo "ERROR: main lock timeout" && exit 1
  echo $$ > "$LOCK"
}

release_lock() {
  rm -f "$LOCK"
}

trap release_lock EXIT

acquire_lock

cd "$REPO"
git checkout main

# Find commits in worktree with this session's BUILD-ORCH tag
COMMITS=$(git -C "$WORKTREE" log --oneline --ancestry-path origin/main..HEAD | grep "BUILD-ORCH-${SESSION_ID}" | awk '{print $1}' | tac)

if [ -z "$COMMITS" ]; then
  echo "WARN: no commits found with tag BUILD-ORCH-${SESSION_ID} in $WORKTREE"
  # Try to find any commits ahead of main
  COMMITS=$(git -C "$WORKTREE" log --oneline origin/main..HEAD | awk '{print $1}' | tac)
  [ -z "$COMMITS" ] && echo "WARN: no commits ahead of main in $WORKTREE" && exit 0
fi

echo "Cherry-picking session $SESSION_ID: $(echo $COMMITS | wc -w) commit(s)"
for COMMIT in $COMMITS; do
  HASH=$(git -C "$WORKTREE" rev-parse "$COMMIT")
  git cherry-pick "$HASH" || {
    echo "ERROR: cherry-pick failed for $HASH — aborting"
    git cherry-pick --abort 2>/dev/null || true
    exit 1
  }
  echo "OK: cherry-picked $HASH"
done

echo "OK: session $SESSION_ID cherry-picked to main"
release_lock
