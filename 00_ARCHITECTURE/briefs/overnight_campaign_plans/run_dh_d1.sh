#!/bin/bash
# SAMPŪRTI stream d1 supervisor (DHĀRĀ phase). Relaunches its conductor on
# any exit until ITS ledger (changed during this run) carries a terminal
# marker, or the cap. Full FM-register mechanics (impl plan §7, amended).
# LAUNCH: nohup caffeinate -i /Users/Dev/shad_overnight/run_dh_d1.sh </dev/null >/dev/null 2>&1 & disown

_OTHERS=$(pgrep -f "bash .*$(basename "$0")" | grep -vw "$$" | wc -l | tr -d ' ')
[ "$_OTHERS" -gt 0 ] && { echo "another $(basename "$0") running — refusing double-launch" >&2; exit 1; }

REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
WT="$REPO/.claude/worktrees/sampurti-conductor"
BR="sampurti/integration"
LEDGER_REL="00_ARCHITECTURE/briefs/sampurti/SAMPURTI_STATE.md"
COMMON="/Users/Dev/shad_overnight/sm_common_rails.md"
KICK="/Users/Dev/shad_overnight/dh1_kickoff.md"
LOG_DIR="/Users/Dev/shad_overnight/dh-d1-logs"
CAP_HOURS=24
mkdir -p "$LOG_DIR"; SUP_LOG="$LOG_DIR/supervisor.log"
log(){ echo "[$(date +%H:%M:%S)] $*" >> "$SUP_LOG"; }

# ── PREFLIGHT (fail loudly BEFORE launching a conductor that cannot work) ───
preflight_fail(){ log "FATAL-PREFLIGHT: $1"; echo "FATAL-PREFLIGHT: $1" >&2; exit 1; }
command -v gh >/dev/null 2>&1 || preflight_fail "gh CLI missing"
gh auth status >/dev/null 2>&1 || preflight_fail "gh auth invalid/expired — PRs would fail silently all night"
gcloud auth print-access-token >/dev/null 2>&1 || preflight_fail "gcloud auth invalid/expired — secrets+CloudRun would fail"
[ -x /Users/Dev/.local/bin/claude ] || preflight_fail "claude CLI not executable"
_AUTHPROBE=$(env -u CLAUDECODE /Users/Dev/.local/bin/claude -p "Reply with exactly: AUTH_OK" \
  --model sonnet --permission-mode bypassPermissions </dev/null 2>&1 | tail -3)
echo "$_AUTHPROBE" | grep -q "AUTH_OK" || preflight_fail "claude CLI auth probe FAILED (run \`claude\` then /login). Without this every attempt burns ~60s at \$0 and dies — the 2026-08-14 Δ3 incident. Probe said: $_AUTHPROBE"
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


# ── MECHANICAL BUILD WATCHDOG (SM-R-11 F4a — FM-21 as bash, not prose) ──────
# No LLM in this loop: while a Cloud Run build execution is RUNNING, poll the
# substep ledger; zero progress >60min => stop-flag + cancel + strike (60min = net for STUCK, sized 2x+ above any plausible healthy substep incl. first-ever stage6/6.5/8 runs; the 30-min idle-in-txn GUC already catches transport hangs faster). After
# 2 strikes the strike file blocks further dispatches (the ratified dispatch
# script must refuse when strikes>=2) — the 3rd improvisation is impossible,
# not merely forbidden (RC-3/RC-4).
STRIKES_FILE="$LOG_DIR/build_strikes"
CHART="482012f1-710e-4a25-994a-93821f5871aa"
wd_log(){ echo "[$(date +%H:%M:%S)] WATCHDOG: $*" >> "$LOG_DIR/watchdog.log"; }
build_watchdog(){
  while true; do
    sleep 300
    EXECROW=$(gcloud run jobs executions list --job=brahma-build-pipeline-job \
      --region=asia-south1 --limit=1 \
      --format="value(name,status.runningCount,status.startTime)" 2>/dev/null)
    RUNNING=$(echo "$EXECROW" | awk '{print $2}')
    [ "$RUNNING" = "1" ] || continue
    EXECNAME=$(echo "$EXECROW" | awk '{print $1}')
    EXECSTART=$(echo "$EXECROW" | awk '{print $3}')
    pgrep -f "cloud-sql-proxy.*5433" >/dev/null || { nohup cloud-sql-proxy \
      --address 127.0.0.1 --port 5433 madhav-astrology:asia-south1:amjis-postgres \
      >/dev/null 2>&1 & sleep 4; }
    DBURL=$(gcloud secrets versions access latest --secret=amjis-pipeline-db-url 2>/dev/null | python3 -c "
import sys, urllib.parse as u
s=sys.stdin.read().strip(); p=u.urlsplit(s)
print(u.urlunsplit((p.scheme, f'{p.username}:{p.password}@127.0.0.1:5433', p.path, '', '')))
")
    [ -n "$DBURL" ] || { wd_log "no DBURL; skip cycle"; continue; }
    AGE=$(psql "$DBURL" -t -A -c "SELECT EXTRACT(EPOCH FROM (now() - GREATEST(COALESCE(MAX(completed_at), 'epoch'::timestamptz), '$EXECSTART'::timestamptz)))::int FROM build_substep_progress WHERE chart_id='$CHART' AND asset_id='ka_kshetra';" 2>/dev/null)
    case "$AGE" in (*[!0-9]*|"") wd_log "bad AGE '$AGE'; skip"; continue;; esac
    if [ "$AGE" -gt 3600 ]; then
      N=$(( $(cat "$STRIKES_FILE" 2>/dev/null || echo 0) + 1 ))
      echo "$N" > "$STRIKES_FILE"
      wd_log "STRIKE $N — $EXECNAME zero substep progress for ${AGE}s (>60min). Recovering mechanically."
      psql "$DBURL" -c "UPDATE build_runs SET stop_requested_at=now() WHERE state='running';" >/dev/null 2>&1
      sleep 30
      gcloud run jobs executions cancel "$EXECNAME" --region=asia-south1 --quiet >/dev/null 2>&1
      sleep 5
      psql "$DBURL" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename='amjis_app' AND pid<>pg_backend_pid() AND state='idle in transaction';" >/dev/null 2>&1
      wd_log "STRIKE $N recovery complete: run stop-flagged, $EXECNAME cancelled, idle-in-txn sessions terminated. Checkpoints intact. strikes=$N $( [ "$N" -ge 2 ] && echo '— DISPATCH NOW BLOCKED until strike file cleared with a written PARIKSAKA diagnosis' )"
    fi
  done
}
build_watchdog &
WDPID=$!
trap 'kill $WDPID 2>/dev/null' EXIT

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

  # HARD COST CAP (SM-R-11 — a 3am thrash loop must hit a wall, not a wallet)
  if awk -v t="$TOTAL_COST" 'BEGIN{exit !(t>100 && t<=150)}'; then
    log "BUDGET-WARN: cumulative \$$TOTAL_COST past \$100 (halt at \$150) — healthy overnight work may reach here; this is a flag, not a stop."
  fi
  if awk -v t="$TOTAL_COST" 'BEGIN{exit !(t>150)}'; then
    log "FATAL-BUDGET: cumulative \$$TOTAL_COST exceeds the \$150 runaway cap — supervisor halting. State is checkpointed; ledger holds NEXT-ACTION; inspect in the morning."
    rm -f "$LOG_DIR/supervisor.alive"; exit 3
  fi

  # AUTH TRANSIENT (2026-08-14): a network/token blip yields rc=1, $0, ~60s.
  # That is NOT a crash loop and must not consume the no-progress budget —
  # nor (d3) burn the 2h gate wait. Retry shortly instead.
  if grep -q "Not logged in" "$LOG_DIR/attempt_${ATTEMPT}.log" 2>/dev/null; then
    log "AUTH-TRANSIENT in attempt $ATTEMPT — retry in 120s (not counted as no-progress)"
    CONSEC_NOPROG=0
    sleep 120
    continue
  fi

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
