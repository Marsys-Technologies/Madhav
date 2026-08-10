#!/usr/bin/env bash
# GOCHARA-UTKARṢA autonomous conductor runner (v1.1)
# Relaunches the conductor on any crash/API-drop/hang until the ledger on the
# dedicated campaign branch (utkarsha/campaign) is sealed COMPLETE or PAUSED.
# Usage:  ./run_conductor.sh
# Stop:   touch the STOP file (takes effect at next relaunch boundary). To stop a
#         LIVE run immediately, kill the claude process (the loop then sees STOP).

set -u
REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
HOME_REL="00_ARCHITECTURE/llm_consumption_audit/briefs/gochara_elevation"
PROMPT_FILE="$REPO/$HOME_REL/CONDUCTOR_PROMPT.md"
STOP_FILE="$REPO/$HOME_REL/STOP"
LOG_DIR="$REPO/$HOME_REL/conductor_logs"
LEDGER_REF="origin/utkarsha/campaign:$HOME_REL/LEDGER.md"
mkdir -p "$LOG_DIR"

BACKOFF=30            # seconds; doubles on consecutive fast failures, caps at 900
MAX_BACKOFF=900
FAST_FAIL_SECS=120    # a run dying faster than this counts as a fast failure
RUN_TIMEOUT=21600     # 6h hard cap per conductor session: a wedged/hung session is
                      # killed and relaunched (resume is ledger-based, so this is safe)

ledger_status() {
  # Reads the sealed status from the campaign branch on origin (not the working tree,
  # which may sit on another branch). Anchored sentinel per the plan's sentinel rule.
  git -C "$REPO" fetch origin utkarsha/campaign >/dev/null 2>&1 || true
  git -C "$REPO" show "$LEDGER_REF" 2>/dev/null | grep -E '^CAMPAIGN-STATUS: (COMPLETE|PAUSED\(.*\))$' | head -1
}

echo "[runner] GOCHARA-UTKARSHA conductor loop starting $(date -u +%FT%TZ)"
while true; do
  if [ -f "$STOP_FILE" ]; then
    echo "[runner] STOP file present - exiting."; exit 0
  fi
  STATUS=$(ledger_status)
  case "$STATUS" in
    "CAMPAIGN-STATUS: COMPLETE")
      echo "[runner] Ledger sealed COMPLETE - campaign done. Exiting."; exit 0 ;;
    CAMPAIGN-STATUS:\ PAUSED*)
      echo "[runner] Ledger sealed: $STATUS - awaiting native. Exiting."; exit 2 ;;
  esac

  TS=$(date -u +%Y%m%dT%H%M%SZ)
  LOG="$LOG_DIR/run_$TS.log"
  echo "[runner] Launching conductor (log: $LOG, timeout: ${RUN_TIMEOUT}s)"
  START=$(date +%s)

  # Sonnet conductor, headless, autonomous. --dangerously-skip-permissions is required
  # for zero-gate autonomy per the native's explicit ratification (plan frontmatter
  # A1). CLI permissions are NOT the safety layer: the layered rails are plan I6 -
  # restricted builder DB role, wave-boundary rail verification, corpus snapshot,
  # and the DB protection triggers.
  # timeout: a hung session (stalled stream, wedged wait) is killed, not waited on.
  # macOS ships no GNU timeout; prefer gtimeout (brew coreutils), else a watchdog.
  if command -v gtimeout >/dev/null 2>&1; then TIMEOUT_BIN="gtimeout";
  elif command -v timeout >/dev/null 2>&1; then TIMEOUT_BIN="timeout";
  else TIMEOUT_BIN=""; fi

  if [ -n "$TIMEOUT_BIN" ]; then
    "$TIMEOUT_BIN" --signal=TERM --kill-after=60 "$RUN_TIMEOUT" \
      claude -p "$(cat "$PROMPT_FILE")" \
        --model sonnet \
        --dangerously-skip-permissions \
        >>"$LOG" 2>&1
    RC=$?
  else
    claude -p "$(cat "$PROMPT_FILE")" \
      --model sonnet \
      --dangerously-skip-permissions \
      >>"$LOG" 2>&1 &
    CPID=$!
    ( sleep "$RUN_TIMEOUT" && kill -TERM "$CPID" 2>/dev/null \
        && sleep 60 && kill -KILL "$CPID" 2>/dev/null ) &
    WPID=$!
    wait "$CPID"; RC=$?
    kill "$WPID" 2>/dev/null; wait "$WPID" 2>/dev/null
  fi
  ELAPSED=$(( $(date +%s) - START ))
  [ "$RC" -eq 124 ] && echo "[runner] Session hit the ${RUN_TIMEOUT}s hard cap (hang guard) - relaunching."

  STATUS=$(ledger_status)
  case "$STATUS" in
    "CAMPAIGN-STATUS: COMPLETE")
      echo "[runner] Conductor exited (rc=$RC) with sealed ledger - done."; exit 0 ;;
    CAMPAIGN-STATUS:\ PAUSED*)
      echo "[runner] Conductor sealed: $STATUS - awaiting native. Exiting."; exit 2 ;;
  esac

  if [ "$ELAPSED" -lt "$FAST_FAIL_SECS" ]; then
    BACKOFF=$(( BACKOFF * 2 )); [ "$BACKOFF" -gt "$MAX_BACKOFF" ] && BACKOFF=$MAX_BACKOFF
  else
    BACKOFF=30
  fi
  echo "[runner] Conductor exited rc=$RC after ${ELAPSED}s; relaunching in ${BACKOFF}s $(date -u +%FT%TZ)"
  sleep "$BACKOFF"
done
