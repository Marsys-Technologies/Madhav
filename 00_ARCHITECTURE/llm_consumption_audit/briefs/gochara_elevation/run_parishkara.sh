#!/bin/bash
# PARIṢKĀRA supervisor — relaunches the conductor on any exit until the
# ledger (as CHANGED during this run) carries a terminal marker, or the cap.
#
# Launch (from any terminal, NOT inside a Claude session):
#   nohup caffeinate -i /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/parishkara-conductor/00_ARCHITECTURE/llm_consumption_audit/briefs/gochara_elevation/run_parishkara.sh </dev/null >/dev/null 2>&1 & disown
#
# Hard-won mechanics baked in:
#   1. --model sonnet MANDATORY (native model policy — no CLI-default inheritance)
#   2. env -u CLAUDECODE (nested-session refusal)
#   3. </dev/null on claude -p (tty suspension)
#   4. cd into the conductor worktree before every launch (cwd drift)
#   5. Ledger-blob-SHA baseline: a PRE-EXISTING terminal marker never stops a
#      new run; only a marker in ledger content CHANGED during this run does.

REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
CONDUCTOR_WORKTREE="$REPO/.claude/worktrees/parishkara-conductor"
HOME_REL="00_ARCHITECTURE/llm_consumption_audit/briefs/gochara_elevation"
PROMPT_FILE="$CONDUCTOR_WORKTREE/$HOME_REL/PARISHKARA_CONDUCTOR_PROMPT.md"
LEDGER_REL="$HOME_REL/PARISHKARA_LEDGER.md"
LOG_DIR="$REPO/.claude/worktrees/parishkara-conductor-logs"
mkdir -p "$LOG_DIR"
SUP_LOG="$LOG_DIR/supervisor.log"
CAP_HOURS=14

log() { echo "[$(date +%H:%M:%S)] $*" >> "$SUP_LOG"; }

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
log "cap reached — supervisor exiting"
