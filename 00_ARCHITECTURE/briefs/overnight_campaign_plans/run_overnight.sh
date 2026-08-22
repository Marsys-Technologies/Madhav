#!/bin/bash
# run_overnight.sh — supervisor for the ṢAḌ-DARŚANA final-arc autonomous run.
# Relaunches the conductor session on any exit (API drop, crash) until the
# ledger carries a RUN-TERMINAL marker or the 12h wall-clock cap is reached.


# ── single-instance guard (2026-08-10, after a double-launch created dual
# conductors): refuse to start if another instance of this script runs.
# Excludes self and parent (the caffeinate wrapper of THIS launch).
# NOTE: match only the SHELL running this script — `pgrep -f <name>` also
# matches the `caffeinate -i <script>` wrapper, which is neither $$ nor
# $PPID, and that false positive blocked every launch (fixed 2026-08-10).
_OTHERS=$(pgrep -f "bash .*$(basename "$0")" | grep -vw "$$" | wc -l | tr -d ' ')
if [ "$_OTHERS" -gt 0 ]; then
  echo "[$(date +%H:%M:%S)] another $(basename "$0") instance is already running — refusing to double-launch" >&2
  exit 1
fi

PROMPT_FILE="/Users/Dev/shad_overnight/shad_darshana_kickoff.md"
REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
LEDGER="00_ARCHITECTURE/briefs/sampurti/SAMPURTI_STATE.md"
BRANCH="sampurti/integration"
LOG_DIR="/Users/Dev/shad_overnight/logs"
mkdir -p "$LOG_DIR"
# Archive previous run's attempt logs: a fresh supervisor restarts its attempt
# counter at 1 and would otherwise APPEND to the prior run's attempt_1.log,
# mixing stale output with new (and confusing any `ls -t` based watcher).
if ls "$LOG_DIR"/attempt_*.log >/dev/null 2>&1; then
  _ARCH="$LOG_DIR/archive/$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$_ARCH" && mv "$LOG_DIR"/attempt_*.log "$_ARCH"/ 2>/dev/null
fi
DEADLINE=$(( $(date +%s) + 12*3600 ))   # 12h wall-clock cap
ATTEMPT=0

log() { echo "[$(date -u '+%H:%M:%S')] $*" | tee -a "$LOG_DIR/supervisor.log"; }

BASELINE_SHA=$(git -C "$REPO" rev-parse "origin/$BRANCH:$LEDGER" 2>/dev/null || echo "none")
log "ledger baseline: $BASELINE_SHA (a pre-existing RUN-TERMINAL marker will NOT stop this run)"
log "supervisor started; cap at $(date -r "$DEADLINE" 2>/dev/null || date -d "@$DEADLINE" 2>/dev/null)"

while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  # Terminal check BEFORE (re)launching: is the run already finished?
  git -C "$REPO" fetch origin "$BRANCH" --quiet 2>/dev/null
  CUR_SHA=$(git -C "$REPO" rev-parse "origin/$BRANCH:$LEDGER" 2>/dev/null || echo "none")
  if [ "$CUR_SHA" != "$BASELINE_SHA" ] \
     && git -C "$REPO" show "origin/$BRANCH:$LEDGER" 2>/dev/null \
        | grep -qE 'RUN-TERMINAL: (ARC-COMPLETE|PARKED-FINAL)'; then
    log "NEW RUN-TERMINAL marker (ledger moved $BASELINE_SHA -> $CUR_SHA) — run complete. Exiting."
    exit 0
  fi

  ATTEMPT=$((ATTEMPT+1))
  log "attempt $ATTEMPT — launching conductor session"

  # --model sonnet is MANDATORY (native model policy 2026-08-10): the conductor
  # runs on Sonnet. Without this flag the CLI inherits the user's default
  # (settings.json), which was opus[1m] — silently promoting the conductor to
  # Opus. Opus is reserved for VERIFIER / NATIVE-PRATINIDHI / GATE-EXECUTOR only.
  cd "$REPO" && env -u CLAUDECODE /Users/Dev/.local/bin/claude -p "$(cat "$PROMPT_FILE")" \
    --model sonnet \
    --permission-mode bypassPermissions \
    --verbose --output-format stream-json \
    < /dev/null >> "$LOG_DIR/attempt_${ATTEMPT}.log" 2>&1
  EXIT=$?

  log "attempt $ATTEMPT exited (code $EXIT) — rechecking terminal marker, then 90s pause"
  sleep 90
done

log "12h wall-clock cap reached — supervisor exiting. Check the ledger for final state."
