#!/usr/bin/env bash
# GOCHARA-UTKARṢA autonomous conductor runner (v1.3)
# Relaunches the conductor on any crash/API-drop/hang until the ledger on the
# dedicated campaign branch (utkarsha/campaign) is sealed COMPLETE or PAUSED.
#
# v1.2 fixed: the conductor was running from the SHARED primary repo checkout
# (/Users/Dev/Vibe-Coding/Apps/Madhav), which collided with an unrelated autonomous
# campaign (SAMPURTI) also using that shared directory, and a relative worktree path
# (`../utk-i6a`) landed inside the repo tree instead of beside it. Fixed: the
# conductor now runs from its OWN dedicated worktree, and all paths are absolute.
#
# v1.3 fixed: this script MUST be run from a real terminal, never from inside an
# active Claude Code session's own Bash tool — `claude -p` refuses to nest (it
# detects the inherited CLAUDECODE env var and exits immediately, every single
# time, silently burning the backoff loop forever with zero progress). `unset
# CLAUDECODE` below is a defensive belt-and-suspenders fix per the CLI's own error
# message, in case this is ever invoked from a context that leaked the var — but
# the real fix is operational: run this in your own terminal window, not through
# an agent's tool call. v1.3 also adds --verbose --output-format stream-json so a
# real terminal run shows live execution (tool calls, sub-agent dispatch,
# reasoning), not just final text blocks (the plain default -p mode's `text`
# format only prints completed responses, not the granular activity in between).
#
# Usage:  ./run_conductor.sh
# Stop:   touch the STOP file (takes effect at next relaunch boundary). To stop a
#         LIVE run immediately, kill the claude process (the loop then sees STOP).

set -u
unset CLAUDECODE 2>/dev/null || true
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
  # Logging: stream-json + verbose gives real execution visibility (tool calls,
  # sub-agent dispatch, reasoning) in place of the plain `text` format's
  # "final answer only" output, and it flushes per-event since it's designed to
  # be piped — no pty trick needed (the earlier `script` approach is no longer
  # required now that we're not using plain-text mode).
  #
  # Portability note: deliberately NOT using `timeout`/`gtimeout` + `bash -c
  # "$(declare -f ...)"` here — that pattern runs the function in a fresh child
  # process that does NOT inherit this shell's unexported variables (LOG,
  # PROMPT_FILE, CONDUCTOR_WORKTREE), a latent bug that only stayed invisible
  # because this machine happens to have neither binary installed. The manual
  # sleep+kill watcher below is fully portable and keeps everything in the same
  # shell's variable scope.
  run_conductor_once() {
    (cd "$CONDUCTOR_WORKTREE" && claude -p "$(cat "$PROMPT_FILE")" \
      --model sonnet --dangerously-skip-permissions \
      --verbose --output-format stream-json --include-partial-messages \
      >>"$LOG" 2>&1)
  }

  run_conductor_once &
  CPID=$!
  ( sleep "$RUN_TIMEOUT" && kill -TERM "$CPID" 2>/dev/null \
      && sleep 60 && kill -KILL "$CPID" 2>/dev/null ) &
  WPID=$!
  wait "$CPID"; RC=$?
  kill "$WPID" 2>/dev/null; wait "$WPID" 2>/dev/null
  ELAPSED=$(( $(date +%s) - START ))
  # 143 = 128+SIGTERM, 137 = 128+SIGKILL — the manual watcher's exit codes when it
  # had to intervene (vs. the conductor exiting on its own).
  { [ "$RC" -eq 143 ] || [ "$RC" -eq 137 ]; } && [ "$ELAPSED" -ge $((RUN_TIMEOUT - 5)) ] && \
    echo "[runner] Session hit the ${RUN_TIMEOUT}s hard cap (hang guard) - relaunching."

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
