#!/bin/bash
# SAMPŪRTI session gamma supervisor — relaunches its conductor on any exit
# until ITS ledger (changed during this run) carries a terminal marker,
# or the 14h cap. All FM-register mechanics baked in (impl plan §7).
# LAUNCH: nohup caffeinate -i /Users/Dev/shad_overnight/run_sm_gamma.sh </dev/null >/dev/null 2>&1 & disown

# single-instance guard (FM-11 proven form)
_OTHERS=$(pgrep -f "bash .*$(basename "$0")" | grep -vw "$$" | wc -l | tr -d ' ')
if [ "$_OTHERS" -gt 0 ]; then
  echo "[$(date +%H:%M:%S)] another $(basename "$0") running — refusing double-launch" >&2
  exit 1
fi

REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
WT="$REPO/.claude/worktrees/sampurti-vyakhya"
BR="sampurti/vyakhya"
LEDGER_REL="00_ARCHITECTURE/briefs/sampurti/SAMPURTI_STATE_GAMMA.md"
COMMON="/Users/Dev/shad_overnight/sm_common_rails.md"
KICK="/Users/Dev/shad_overnight/sm_gamma_kickoff.md"
LOG_DIR="/Users/Dev/shad_overnight/sm-gamma-logs"
CAP_HOURS=14
mkdir -p "$LOG_DIR"; SUP_LOG="$LOG_DIR/supervisor.log"
log(){ echo "[$(date +%H:%M:%S)] $*" >> "$SUP_LOG"; }

# archive previous run's logs (FM: counter-restart append confusion)
if ls "$LOG_DIR"/attempt_*.log >/dev/null 2>&1; then
  A="$LOG_DIR/archive/$(date +%Y%m%d_%H%M%S)"; mkdir -p "$A" && mv "$LOG_DIR"/attempt_*.log "$A"/
  log "archived prior attempt logs to $A"
fi

# worktree: adopt-if-branch-held-elsewhere, else create (FM-12)
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
log "supervisor started; ledger baseline $BASELINE; cap $(date -r $END_TS)"

ATTEMPT=0
while [ "$(date +%s)" -lt "$END_TS" ]; do
  ATTEMPT=$((ATTEMPT+1))
  log "attempt $ATTEMPT — launching conductor (SAMPŪRTI-γ)"
  cd "$WT" && env -u CLAUDECODE /Users/Dev/.local/bin/claude -p "$(cat "$COMMON" "$KICK")" \
    --model sonnet \
    --permission-mode bypassPermissions \
    --verbose --output-format stream-json \
    < /dev/null >> "$LOG_DIR/attempt_${ATTEMPT}.log" 2>&1
  RC=$?
  log "attempt $ATTEMPT exited ($RC) — marker recheck, 90s pause"
  CUR=$(ledger_blob)
  if [ "$CUR" != "$BASELINE" ]; then
    M=$(terminal_marker)
    [ -n "$M" ] && { log "NEW terminal marker: $M — exiting"; exit 0; }
  fi
  sleep 90
done
log "cap reached — exiting; ledger has state"
