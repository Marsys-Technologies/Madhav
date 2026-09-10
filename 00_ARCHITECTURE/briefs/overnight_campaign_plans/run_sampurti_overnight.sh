#!/bin/bash
# run_sampurti_overnight.sh — supervisor for the SAMPŪRTI overnight autonomous
# run (rebase plan, CONFIRMED 2026-08-12). Relaunches the conductor on any
# exit until the ledger (as CHANGED during this run) carries a terminal
# marker, or the wall-clock cap.
#
# LAUNCH (any terminal, NOT inside a Claude session):
#   nohup caffeinate -i /Users/Dev/shad_overnight/run_sampurti_overnight.sh </dev/null >/dev/null 2>&1 & disown
#
# Every hard-won mechanic baked in:
#  1. single-instance guard (caffeinate-safe form — the earlier form false-
#     positived on its own wrapper and blocked every launch)
#  2. --model sonnet MANDATORY (no CLI-default inheritance)
#  3. env -u CLAUDECODE (nested-session refusal)
#  4. </dev/null (tty suspension) + disown pattern at launch
#  5. dedicated conductor WORKTREE (never the main checkout — a parallel
#     campaign's interactive sessions use it); created here if absent
#  6. stream-json logs, one file per attempt, previous run's logs archived
#  7. ledger-blob-SHA baseline: a PRE-EXISTING terminal marker never stops a
#     new run; only a marker in ledger content CHANGED during this run does

# ── single-instance guard ────────────────────────────────────────────────────
_OTHERS=$(pgrep -f "bash .*$(basename "$0")" | grep -vw "$$" | wc -l | tr -d ' ')
if [ "$_OTHERS" -gt 0 ]; then
  echo "[$(date +%H:%M:%S)] another $(basename "$0") instance is already running — refusing to double-launch" >&2
  exit 1
fi

REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
CONDUCTOR_WORKTREE="$REPO/.claude/worktrees/sampurti-conductor"
PROMPT_FILE="/Users/Dev/shad_overnight/sampurti_overnight_kickoff.md"
LEDGER_REL="00_ARCHITECTURE/briefs/sampurti/SAMPURTI_STATE.md"
LOG_DIR="/Users/Dev/shad_overnight/sampurti-overnight-logs"
CAP_HOURS=14

mkdir -p "$LOG_DIR"
SUP_LOG="$LOG_DIR/supervisor.log"
log() { echo "[$(date +%H:%M:%S)] $*" >> "$SUP_LOG"; }

# ── archive previous run's attempt logs (fresh counter would append to them) ─
if ls "$LOG_DIR"/attempt_*.log >/dev/null 2>&1; then
  _ARCH="$LOG_DIR/archive/$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$_ARCH" && mv "$LOG_DIR"/attempt_*.log "$_ARCH"/ 2>/dev/null
  log "archived previous attempt logs to $_ARCH"
fi

# ── ensure the dedicated conductor worktree exists on sampurti/integration ──
if [ ! -d "$CONDUCTOR_WORKTREE" ]; then
  # If some other worktree already holds the branch (e.g. a prior conductor's
  # leftover under another name), ADOPT it by moving it here — git forbids two
  # worktrees on one branch, which killed the 2026-08-12 first launch.
  EXISTING=$(git -C "$REPO" worktree list --porcelain | awk '/^worktree /{w=$2} /^branch refs\/heads\/sampurti\/integration$/{print w}')
  if [ -n "$EXISTING" ] && [ "$EXISTING" != "$CONDUCTOR_WORKTREE" ]; then
    log "adopting existing sampurti/integration worktree: $EXISTING -> $CONDUCTOR_WORKTREE"
    git -C "$REPO" worktree move "$EXISTING" "$CONDUCTOR_WORKTREE" >>"$SUP_LOG" 2>&1
  else
    log "creating conductor worktree at $CONDUCTOR_WORKTREE"
    git -C "$REPO" fetch origin sampurti/integration --quiet 2>>"$SUP_LOG"
    git -C "$REPO" worktree add "$CONDUCTOR_WORKTREE" sampurti/integration >>"$SUP_LOG" 2>&1 \
      || git -C "$REPO" worktree add "$CONDUCTOR_WORKTREE" -b sampurti/integration origin/sampurti/integration >>"$SUP_LOG" 2>&1
  fi
fi
if [ ! -d "$CONDUCTOR_WORKTREE" ]; then
  log "FATAL: conductor worktree could not be created — aborting"
  exit 1
fi

ledger_blob() {
  git -C "$CONDUCTOR_WORKTREE" rev-parse ":$LEDGER_REL" 2>/dev/null \
    || git -C "$CONDUCTOR_WORKTREE" hash-object "$CONDUCTOR_WORKTREE/$LEDGER_REL" 2>/dev/null \
    || echo "absent"
}
terminal_marker() {
  tail -5 "$CONDUCTOR_WORKTREE/$LEDGER_REL" 2>/dev/null \
    | grep -E '^RUN-TERMINAL: (ARC-COMPLETE|PARKED-FINAL.*)$' | head -1
}

BASELINE=$(ledger_blob)
END_TS=$(( $(date +%s) + CAP_HOURS*3600 ))
log "supervisor started; ledger baseline: $BASELINE (pre-existing terminal markers will NOT stop this run); cap at $(date -r $END_TS)"

ATTEMPT=0
while [ "$(date +%s)" -lt "$END_TS" ]; do
  ATTEMPT=$((ATTEMPT+1))
  log "attempt $ATTEMPT — launching conductor session"
  cd "$CONDUCTOR_WORKTREE" && env -u CLAUDECODE /Users/Dev/.local/bin/claude -p "$(cat "$PROMPT_FILE")" \
    --model sonnet \
    --permission-mode bypassPermissions \
    --verbose --output-format stream-json \
    < /dev/null >> "$LOG_DIR/attempt_${ATTEMPT}.log" 2>&1
  RC=$?
  log "attempt $ATTEMPT exited (code $RC) — rechecking terminal marker, then 90s pause"
  CURRENT=$(ledger_blob)
  if [ "$CURRENT" != "$BASELINE" ]; then
    MARKER=$(terminal_marker)
    if [ -n "$MARKER" ]; then
      log "NEW terminal marker (ledger moved $BASELINE -> $CURRENT): $MARKER — supervisor exiting"
      exit 0
    fi
  fi
  sleep 90
done
log "wall-clock cap reached — supervisor exiting; check the ledger for state"
