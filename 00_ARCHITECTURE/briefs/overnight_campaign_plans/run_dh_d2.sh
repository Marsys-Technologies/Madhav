#!/bin/bash
# SAMPŪRTI stream d2 supervisor (DHĀRĀ phase). Relaunches its conductor on
# any exit until ITS ledger (changed during this run) carries a terminal
# marker, or the cap. Full FM-register mechanics (impl plan §7, amended).
# LAUNCH: nohup caffeinate -i /Users/Dev/shad_overnight/run_dh_d2.sh </dev/null >/dev/null 2>&1 & disown

_OTHERS=$(pgrep -f "bash .*$(basename "$0")" | grep -vw "$$" | wc -l | tr -d ' ')
[ "$_OTHERS" -gt 0 ] && { echo "another $(basename "$0") running — refusing double-launch" >&2; exit 1; }

REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
WT="$REPO/.claude/worktrees/sm-d2"
BR="sampurti/pramana"
LEDGER_REL="00_ARCHITECTURE/briefs/sampurti/SAMPURTI_STATE_D2.md"
COMMON="/Users/Dev/shad_overnight/sm_common_rails.md"
KICK="/Users/Dev/shad_overnight/dh2_kickoff.md"
LOG_DIR="/Users/Dev/shad_overnight/dh-d2-logs"
CAP_HOURS=24
mkdir -p "$LOG_DIR"; SUP_LOG="$LOG_DIR/supervisor.log"
log(){ echo "[$(date +%H:%M:%S)] $*" >> "$SUP_LOG"; }

# ── PREFLIGHT (fail loudly BEFORE launching a conductor that cannot work) ───
preflight_fail(){ log "FATAL-PREFLIGHT: $1"; echo "FATAL-PREFLIGHT: $1" >&2; exit 1; }
command -v gh >/dev/null 2>&1 || preflight_fail "gh CLI missing"
gh auth status >/dev/null 2>&1 || preflight_fail "gh auth invalid/expired — PRs would fail silently all night"
gcloud auth print-access-token >/dev/null 2>&1 || preflight_fail "gcloud auth invalid/expired — secrets+CloudRun would fail"
[ -x /Users/Dev/.local/bin/claude ] || preflight_fail "claude CLI not executable"
[ -f "$COMMON" ] && [ -f "$KICK" ] || preflight_fail "prompt files missing ($COMMON / $KICK)"
log "preflight OK (gh auth, gcloud auth, claude, prompts)"


if ls "$LOG_DIR"/attempt_*.log >/dev/null 2>&1; then
  A="$LOG_DIR/archive/$(date +%Y%m%d_%H%M%S)"; mkdir -p "$A" && mv "$LOG_DIR"/attempt_*.log "$A"/
  log "archived prior logs to $A"
fi

if [ ! -d "$WT" ]; then
  EXISTING=$(git -C "$REPO" worktree list --porcelain | awk -v b="refs/heads/$BR" '/^worktree /{w=$2} $0=="branch "b{print w}')
  if [ -n "$EXISTING" ] && [ "$EXISTING" != "$WT" ]; then
    log "adopting existing $BR worktree: $EXISTING -> $WT"
    git -C "$REPO" worktree move "$EXISTING" "$WT" >>"$SUP_LOG" 2>&1
  else
    log "creating worktree $WT on $BR"
    git -C "$REPO" fetch origin --quiet 2>>"$SUP_LOG"
    git -C "$REPO" worktree add "$WT" "$BR" >>"$SUP_LOG" 2>&1 \
      || git -C "$REPO" worktree add "$WT" -b "$BR" origin/main >>"$SUP_LOG" 2>&1
  fi
fi
[ -d "$WT" ] || { log "FATAL: worktree unavailable"; exit 1; }

ledger_blob(){ git -C "$WT" rev-parse ":$LEDGER_REL" 2>/dev/null || git -C "$WT" hash-object "$WT/$LEDGER_REL" 2>/dev/null || echo absent; }
terminal_marker(){ tail -5 "$WT/$LEDGER_REL" 2>/dev/null | grep -E '^RUN-TERMINAL: (SESSION-.*-COMPLETE|ARC-COMPLETE|PARKED-FINAL.*)$' | head -1; }

BASELINE=$(ledger_blob)
END_TS=$(( $(date +%s) + CAP_HOURS*3600 ))
log "supervisor started; baseline $BASELINE; cap $(date -r $END_TS)"


TOTAL_COST=0
CONSEC_NOPROG=0
touch "$LOG_DIR/supervisor.alive"

ATTEMPT=0
while [ "$(date +%s)" -lt "$END_TS" ]; do
  ATTEMPT=$((ATTEMPT+1))
  touch "$LOG_DIR/supervisor.alive"          # liveness beacon (detect supervisor death)
  PRE_BLOB=$(ledger_blob)
  START_TS=$(date +%s)
  log "attempt $ATTEMPT — launching conductor ($IDENT)"
  cd "$WT" && env -u CLAUDECODE /Users/Dev/.local/bin/claude -p "$(cat "$COMMON" "$KICK")" \
    --model sonnet \
    --permission-mode bypassPermissions \
    --verbose --output-format stream-json \
    < /dev/null >> "$LOG_DIR/attempt_${ATTEMPT}.log" 2>&1 &
  CPID=$!
  echo "$CPID" > "$LOG_DIR/current_conductor.pid"   # self-exclusion token for liveness
  wait $CPID
  RC=$?
  rm -f "$LOG_DIR/current_conductor.pid"
  DUR=$(( $(date +%s) - START_TS ))
  POST_BLOB=$(ledger_blob)

  # cost telemetry (visible burn tracking)
  C=$(grep -o '"total_cost_usd":[0-9.]*' "$LOG_DIR/attempt_${ATTEMPT}.log" 2>/dev/null | tail -1 | cut -d: -f2)
  TOTAL_COST=$(awk -v a="$TOTAL_COST" -v b="${C:-0}" 'BEGIN{printf "%.2f", a+b}')
  log "attempt $ATTEMPT exited rc=$RC after ${DUR}s; cost=\$${C:-?} cumulative=\$$TOTAL_COST"

  # terminal marker (only if the ledger CHANGED during this run)
  if [ "$POST_BLOB" != "$BASELINE" ]; then
    M=$(terminal_marker)
    [ -n "$M" ] && { log "terminal marker: $M — exiting"; rm -f "$LOG_DIR/supervisor.alive"; exit 0; }
  fi

  # crash-loop / zero-progress detection with exponential backoff
  if [ "$DUR" -lt 150 ] && [ "$POST_BLOB" = "$PRE_BLOB" ]; then
    CONSEC_NOPROG=$((CONSEC_NOPROG+1))
  else
    CONSEC_NOPROG=0
  fi
  PAUSE=90
  if [ "$CONSEC_NOPROG" -ge 3 ]; then
    PAUSE=$(( 90 * (1 << (CONSEC_NOPROG-2)) )); [ "$PAUSE" -gt 1800 ] && PAUSE=1800
    log "WARN: $CONSEC_NOPROG consecutive short no-progress attempts — backing off ${PAUSE}s (rc=$RC)"
  fi
  if [ "$CONSEC_NOPROG" -ge 8 ]; then
    log "FATAL: 8 consecutive no-progress attempts — halting to avoid burn. Inspect $LOG_DIR/attempt_${ATTEMPT}.log"
    rm -f "$LOG_DIR/supervisor.alive"; exit 2
  fi

  # log-disk guard (stream-json is verbose; keep the dir bounded)
  SZ=$(du -sm "$LOG_DIR" 2>/dev/null | cut -f1)
  if [ "${SZ:-0}" -gt 3000 ]; then
    find "$LOG_DIR" -name 'attempt_*.log' -mmin +180 -delete 2>/dev/null
    log "log dir ${SZ}MB > 3GB — pruned attempt logs older than 3h"
  fi

  sleep "$PAUSE"
done
log "wall-clock cap reached after $ATTEMPT attempts (cumulative \$$TOTAL_COST) — exiting; ledger holds state"
rm -f "$LOG_DIR/supervisor.alive"
