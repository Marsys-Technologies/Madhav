#!/usr/bin/env bash
# GOCHARA-UTKARṢA autonomous conductor runner (v1.2)
# Relaunches the conductor on any crash/API-drop/hang until the ledger on the
# dedicated campaign branch (utkarsha/campaign) is sealed COMPLETE or PAUSED.
#
# v1.2 fixes a real incident from the first launch: the conductor was running
# from the SHARED primary repo checkout (/Users/Dev/Vibe-Coding/Apps/Madhav), which
# collided with an unrelated autonomous campaign (SAMPURTI) also using that shared
# directory, and a relative worktree path (`../utk-i6a`) landed inside the repo tree
# instead of beside it. Fix: the conductor now runs from its OWN dedicated worktree
# (mirroring how builder lanes already work), and all paths below are absolute.
#
# Usage:  ./run_conductor.sh
# Stop:   touch the STOP file (takes effect at next relaunch boundary). To stop a
#         LIVE run immediately, kill the claude process (the loop then sees STOP).

set -u
REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
CONDUCTOR_WORKTREE="$REPO/.claude/worktrees/utkarsha-conductor"
HOME_REL="00_ARCHITECTURE/llm_consumption_audit/briefs/gochara_elevation"
PROMPT_FILE="$CONDUCTOR_WORKTREE/$HOME_REL/CONDUCTOR_PROMPT.md"
STOP_FILE="$CONDUCTOR_WORKTREE/$HOME_REL/STOP"
# Logs live OUTSIDE any git worktree's tracked tree — a plain directory, not a
# worktree, so it can never again be mistaken for repo content or fought over.
LOG_DIR="$REPO/.claude/worktrees/utkarsha-conductor-logs"
LEDGER_REF="origin/utkarsha/campaign:$HOME_REL/LEDGER.md"
mkdir -p "$LOG_DIR"

BACKOFF=30            # seconds; doubles on consecutive fast failures, caps at 900
MAX_BACKOFF=900
FAST_FAIL_SECS=120    # a run dying faster than this counts as a fast failure
RUN_TIMEOUT=21600     # 6h hard cap per conductor session: a wedged/hung session is
                      # killed and relaunched (resume is ledger-based, so this is safe)

ledger_status() {
  # Reads the sealed status from the campaign branch on origin (not any working
  # tree). Anchored sentinel per the plan's sentinel rule.
  git -C "$REPO" fetch origin utkarsha/campaign >/dev/null 2>&1 || true
  git -C "$REPO" show "$LEDGER_REF" 2>/dev/null | grep -E '^CAMPAIGN-STATUS: (COMPLETE|PAUSED\(.*\))$' | head -1
}

ensure_conductor_worktree() {
  # Idempotent: create the dedicated worktree if it doesn't exist yet. Never uses
  # a relative path — this is exactly the class of bug v1.1 hit.
  if [ ! -d "$CONDUCTOR_WORKTREE" ]; then
    echo "[runner] Dedicated conductor worktree missing — creating at $CONDUCTOR_WORKTREE"
    git -C "$REPO" fetch origin utkarsha/campaign 2>&1
    if git -C "$REPO" show-ref --verify --quiet refs/heads/utkarsha/campaign; then
      git -C "$REPO" worktree add "$CONDUCTOR_WORKTREE" utkarsha/campaign
    else
      git -C "$REPO" worktree add "$CONDUCTOR_WORKTREE" -b utkarsha/campaign origin/main
    fi
  fi
}

echo "[runner] GOCHARA-UTKARSHA conductor loop starting $(date -u +%FT%TZ)"
while true; do
  ensure_conductor_worktree
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
  echo "[runner] Launching conductor (cwd: $CONDUCTOR_WORKTREE, log: $LOG, timeout: ${RUN_TIMEOUT}s)"
  START=$(date +%s)

  # Sonnet conductor, headless, autonomous. --dangerously-skip-permissions is required
  # for zero-gate autonomy per the native's explicit ratification (plan frontmatter
  # A1). CLI permissions are NOT the safety layer: the layered rails are plan I6 -
  # restricted builder DB role, wave-boundary rail verification, corpus snapshot,
  # and the DB protection triggers.
  #
  # Logging: claude -p fully-buffers stdout when it isn't a TTY, so a plain
  # redirect produces a log that stays empty until process exit (this bit us on
  # the first launch — a killed session left zero forensic trail). `script`
  # allocates a pseudo-TTY so output is written as it's produced; it ships with
  # macOS by default. Falls back to a plain redirect if `script` is unavailable.
  if command -v gtimeout >/dev/null 2>&1; then TIMEOUT_BIN="gtimeout";
  elif command -v timeout >/dev/null 2>&1; then TIMEOUT_BIN="timeout";
  else TIMEOUT_BIN=""; fi

  run_conductor_once() {
    if command -v script >/dev/null 2>&1; then
      # macOS script syntax: script -q <logfile> <command...>
      (cd "$CONDUCTOR_WORKTREE" && script -q "$LOG" \
        claude -p "$(cat "$PROMPT_FILE")" --model sonnet --dangerously-skip-permissions)
    else
      (cd "$CONDUCTOR_WORKTREE" && \
        claude -p "$(cat "$PROMPT_FILE")" --model sonnet --dangerously-skip-permissions \
        >>"$LOG" 2>&1)
    fi
  }

  if [ -n "$TIMEOUT_BIN" ]; then
    "$TIMEOUT_BIN" --signal=TERM --kill-after=60 "$RUN_TIMEOUT" bash -c "$(declare -f run_conductor_once); run_conductor_once"
    RC=$?
  else
    run_conductor_once &
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
