#!/bin/bash
# GOCHARA-UTKARṢA supervisor (v2.0) — relaunches the conductor session on ANY
# exit (crash, API drop, terminal closure, hang) until the ledger carries a
# CAMPAIGN-STATUS: COMPLETE/PAUSED marker written DURING this run, or the
# wall-clock cap is reached.
#
# v2.0 rebuilds this on the proven pattern from /Users/Dev/shad_overnight/
# run_overnight.sh (battle-tested on the SAMPURTI/ṢAḌ-DARŚANA campaign),
# after investigating three real incidents from the v1.x line tonight:
#
#   1. Terminal closure ended the conductor (twice). v1.x launched it as a
#      plain foreground command — its life was tied to that terminal window.
#      Fixed: launch this script itself via nohup+disown+stdin-null (see the
#      launch command at the bottom of this file), and every claude
#      invocation below also gets `< /dev/null` so it never blocks on stdin.
#   2. A double-conductor collision: killing a child process without killing
#      its parent outer loop left a stale instance that auto-relaunched and
#      briefly ran alongside a freshly-fixed one. Fixed: this script no
#      longer needs to defend against that case directly — the fix lives in
#      the conductor PROMPT now (CONDUCTOR-HEARTBEAT lease, ≤10min refresh;
#      a new session exits immediately if it finds a <15min-old heartbeat).
#   3. Nested-session refusal (claude -p won't launch inside another Claude
#      Code session) — already fixed in v1.3, retained here as `env -u
#      CLAUDECODE` directly on the invocation line (matching the proven
#      pattern exactly) plus a defensive `unset` at script start.
#
# Also newly adopted: a baseline-hash guard so a PRE-EXISTING terminal
# marker (from before this run started) can never be misread as this run's
# own completion — only a marker that appears AFTER the baseline counts.
# This wasn't a live UTKARSHA incident (its ledger path isn't shared with
# another campaign) but it's the same class of bug and costs nothing to
# prevent.
#
# Launch (from a real terminal, never from inside a Claude Code session):
#   nohup caffeinate -i /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/utkarsha-conductor/00_ARCHITECTURE/llm_consumption_audit/briefs/gochara_elevation/run_conductor.sh </dev/null >/dev/null 2>&1 & disown

REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
CONDUCTOR_WORKTREE="$REPO/.claude/worktrees/utkarsha-conductor"
HOME_REL="00_ARCHITECTURE/llm_consumption_audit/briefs/gochara_elevation"
PROMPT_FILE="$CONDUCTOR_WORKTREE/$HOME_REL/CONDUCTOR_PROMPT.md"
LEDGER="$HOME_REL/LEDGER.md"
BRANCH="utkarsha/campaign"
LOG_DIR="$REPO/.claude/worktrees/utkarsha-conductor-logs"
mkdir -p "$LOG_DIR"
DEADLINE=$(( $(date +%s) + 12*3600 ))   # 12h wall-clock cap per supervisor run
ATTEMPT=0

unset CLAUDECODE 2>/dev/null

log() { echo "[$(date -u '+%H:%M:%S')] $*" | tee -a "$LOG_DIR/supervisor.log"; }

ensure_conductor_worktree() {
  if [ ! -d "$CONDUCTOR_WORKTREE" ]; then
    log "dedicated conductor worktree missing — creating at $CONDUCTOR_WORKTREE"
    git -C "$REPO" fetch origin "$BRANCH" 2>&1 | tee -a "$LOG_DIR/supervisor.log"
    if git -C "$REPO" show-ref --verify --quiet "refs/heads/$BRANCH"; then
      git -C "$REPO" worktree add "$CONDUCTOR_WORKTREE" "$BRANCH"
    else
      git -C "$REPO" worktree add "$CONDUCTOR_WORKTREE" -b "$BRANCH" origin/main
    fi
  fi
}
ensure_conductor_worktree

# Baseline: a CAMPAIGN-STATUS marker that already existed before this
# supervisor started can never be honored as THIS run's completion — only a
# ledger content-hash change during this run, carrying the marker, counts.
BASELINE_SHA=$(git -C "$REPO" rev-parse "origin/$BRANCH:$LEDGER" 2>/dev/null || echo "none")
log "ledger baseline: $BASELINE_SHA (a pre-existing terminal marker will NOT stop this run)"
log "supervisor started; cap at $(date -r "$DEADLINE" 2>/dev/null || date -d "@$DEADLINE" 2>/dev/null)"

while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  # Terminal check BEFORE (re)launching: has the campaign actually finished?
  git -C "$REPO" fetch origin "$BRANCH" --quiet 2>/dev/null
  CUR_SHA=$(git -C "$REPO" rev-parse "origin/$BRANCH:$LEDGER" 2>/dev/null || echo "none")
  if [ "$CUR_SHA" != "$BASELINE_SHA" ]; then
    MARKER=$(git -C "$REPO" show "origin/$BRANCH:$LEDGER" 2>/dev/null \
             | grep -E '^CAMPAIGN-STATUS: (COMPLETE|PAUSED\(.*\))$' | head -1)
    if [ -n "$MARKER" ]; then
      log "NEW terminal marker (ledger moved $BASELINE_SHA -> $CUR_SHA): $MARKER — exiting."
      exit 0
    fi
  fi

  ATTEMPT=$((ATTEMPT+1))
  log "attempt $ATTEMPT — launching conductor session"

  cd "$CONDUCTOR_WORKTREE" && env -u CLAUDECODE claude -p "$(cat "$PROMPT_FILE")" \
    --model sonnet \
    --permission-mode bypassPermissions \
    --verbose --output-format stream-json --include-partial-messages \
    < /dev/null >> "$LOG_DIR/attempt_${ATTEMPT}.log" 2>&1
  EXIT=$?

  log "attempt $ATTEMPT exited (code $EXIT) — rechecking terminal marker, then 90s pause"
  sleep 90
done

log "12h wall-clock cap reached — supervisor exiting. Check the ledger for final state."
