#!/usr/bin/env bash
# ==============================================================================
# ekv_supervisor.sh — supervises the EKAVĀKYATĀ conductor session overnight.
#
# Re-invokes the conductor (SŪTRADHĀRA) if it drops, hangs, or the harness
# exits, until origin/campaign-coordination shows a terminal marker or budgets
# are exhausted. Adapted from the proven marsys-overnight-supervisor.sh
# pattern, fitted to how EKAVAKYATA actually reports state: the conductor's
# own progress lives in git-committed files on origin/campaign-coordination
# (LEDGER_CONDUCTOR.md, ekv_manifest.json, LEASES.json) — durable across
# relaunches by construction, no separate local run-state to reconcile.
#
# This does NOT relaunch stream sessions A-E (ekv_launch_streams.sh already
# self-relaunches each stream once on an early crash <10min; beyond that it's
# the conductor's own "Heartbeats" standing duty per its kickoff). This script
# only re-invokes the top-level conductor — nothing was watching that layer.
#
# USAGE
#   chmod +x ekv_supervisor.sh
#   caffeinate -i ./ekv_supervisor.sh            # start (or resume)
#   ./ekv_supervisor.sh --status                 # show current state, exit
#
# EXIT CODES
#   0  terminal marker seen (RUN-TERMINAL COMPLETE, or honest EKV-NIGHT1-PARTIAL)
#   1  supervisor precondition failure
#   2  budgets exhausted without a terminal marker (needs a human)
# ==============================================================================
set -uo pipefail

SHAD=/Users/Dev/shad_overnight
REPO=/Users/Dev/Vibe-Coding/Apps/Madhav
CLAUDE=/Users/Dev/.local/bin/claude
KICKOFF="$SHAD/ekv_conductor_kickoff.md"

COORD_BRANCH_REMOTE="campaign-coordination"
COORD_FILE_PATH="00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"

RUN_DIR="${RUN_DIR:-$HOME/.ekv-overnight-supervisor}"   # outside both repo and shad_overnight
LOG_DIR="$RUN_DIR/logs"

MAX_ATTEMPTS="${MAX_ATTEMPTS:-16}"
MAX_WALL_HOURS="${MAX_WALL_HOURS:-10}"
ATTEMPT_TIMEOUT_MIN="${ATTEMPT_TIMEOUT_MIN:-420}"   # hard ceiling per single invocation
STALL_MINUTES="${STALL_MINUTES:-25}"                # candidate-stall window (see stall check below)
BACKOFF_SECONDS="${BACKOFF_SECONDS:-30}"
ADOPT_PID="${ADOPT_PID:-}"                          # if set (first iteration only): attach to this
                                                     # already-running conductor instead of launching
COORD_FILE_PATH_REL="00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
COORD_BRANCH_REMOTE_NAME="campaign-coordination"

# BUG FIX (2026-08-16, post-incident): the stall check used to be "no growth in
# the attempt log for N minutes => kill." That produced a false positive against
# a real, working conductor whose stdout buffers differently when piped to a
# file instead of a TTY. A stall is now only declared when BOTH the local log
# is quiet AND the coordination branch has had no new commit in the same
# window — the conductor's actual job is to post there, so branch silence is
# the far more reliable signal. Also: killing used to target only the wrapping
# subshell, which let `timeout`+`claude` survive as orphans (reparented to
# PID 1) instead of dying — the exact bug that produced a duplicate conductor
# tonight. The child is now launched via `setsid` so kills target the whole
# process group (negative PID), not just the subshell.
coord_last_commit_epoch() {
  git -C "$REPO" fetch origin "$COORD_BRANCH_REMOTE_NAME" --quiet 2>/dev/null
  git -C "$REPO" log -1 --format=%ct "origin/${COORD_BRANCH_REMOTE_NAME}" -- "$COORD_FILE_PATH_REL" 2>/dev/null || echo 0
}

TIMEOUT_BIN="$(command -v timeout || command -v gtimeout || true)"
[[ -n "$TIMEOUT_BIN" ]] || { echo "FATAL: need coreutils (brew install coreutils for gtimeout)"; exit 1; }

mkdir -p "$LOG_DIR"
ATTEMPT_FILE="$RUN_DIR/attempt"
SUP_LOG="$RUN_DIR/supervisor.log"
[[ -f "$ATTEMPT_FILE" ]] || echo 0 > "$ATTEMPT_FILE"

ts()  { date '+%Y-%m-%d %H:%M:%S'; }
log() { printf '[%s] %s\n' "$(ts)" "$*" | tee -a "$SUP_LOG"; }

# ------------------------------------------------------------------------------
# Terminal-state check: read directly off the remote coordination branch (the
# conductor is its sole writer). Returns COMPLETE | PARTIAL | NONE.
# ------------------------------------------------------------------------------
check_terminal() {
  git -C "$REPO" fetch origin "$COORD_BRANCH_REMOTE" --quiet 2>/dev/null
  git -C "$REPO" show "origin/${COORD_BRANCH_REMOTE}:${COORD_FILE_PATH}" 2>/dev/null | python3 "$SHAD/ekv_terminal_check.py"
}

show_status() {
  echo "RUN_DIR : $RUN_DIR"
  echo "attempt : $( [[ -f "$ATTEMPT_FILE" ]] && cat "$ATTEMPT_FILE" || echo 0 )"
  echo "coordination marker: $(check_terminal)"
  if [[ -f "$SUP_LOG" ]]; then echo "--- supervisor log tail ---"; tail -n 20 "$SUP_LOG"; fi
}
case "${1:-}" in
  --status) show_status; exit 0 ;;
  --help|-h) sed -n '1,30p' "$0"; exit 0 ;;
esac

[[ -x "$CLAUDE" ]] || { echo "FATAL: claude CLI not found/executable at $CLAUDE"; exit 1; }
[[ -f "$KICKOFF" ]] || { echo "FATAL: conductor kickoff missing: $KICKOFF"; exit 1; }
[[ -d "$REPO"    ]] || { echo "FATAL: repo not found: $REPO"; exit 1; }

START_EPOCH=$(date +%s)
MAX_WALL_SECONDS=$(( MAX_WALL_HOURS * 3600 ))
elapsed_hours() { echo $(( ( $(date +%s) - START_EPOCH ) / 3600 )); }

log "=============================================================="
log "EKAVĀKYATĀ conductor supervisor starting."
log "  kickoff  : $KICKOFF"
log "  repo     : $REPO"
log "  run dir  : $RUN_DIR"
log "  coord    : origin/${COORD_BRANCH_REMOTE}:${COORD_FILE_PATH}"
log "  budgets  : ${MAX_ATTEMPTS} attempts / ${MAX_WALL_HOURS}h wall / ${ATTEMPT_TIMEOUT_MIN}m per attempt / stall ${STALL_MINUTES}m"
log "=============================================================="

while :; do
  attempt=$(( $(cat "$ATTEMPT_FILE") + 1 ))
  echo "$attempt" > "$ATTEMPT_FILE"

  if (( attempt > MAX_ATTEMPTS )); then
    log "STOP: attempt budget exhausted (${MAX_ATTEMPTS}). No terminal marker reached — needs a human."
    exit 2
  fi
  if (( $(date +%s) - START_EPOCH > MAX_WALL_SECONDS )); then
    log "STOP: wall-clock budget exhausted (${MAX_WALL_HOURS}h)."
    exit 2
  fi

  term=$(check_terminal)
  if [[ "$term" == "COMPLETE" ]]; then
    log "origin/${COORD_BRANCH_REMOTE} already shows RUN-TERMINAL COMPLETE. Nothing to do."
    exit 0
  fi
  if [[ "$term" == "PARTIAL" ]]; then
    log "origin/${COORD_BRANCH_REMOTE} shows EKV-NIGHT1-PARTIAL — honest gated close, not a crash. Not retrying."
    exit 0
  fi

  ATTEMPT_LOG="$LOG_DIR/attempt-${attempt}.log"
  ln -sfn "$ATTEMPT_LOG" "$RUN_DIR/latest.log"

  adopting=0
  if [[ -n "$ADOPT_PID" && "$attempt" == "1" ]]; then
    adopting=1
    child="$ADOPT_PID"
    log "--- attempt ${attempt}/${MAX_ATTEMPTS}: ADOPTING already-running conductor pid ${child} (not launching a new one)"
    : > "$ATTEMPT_LOG"   # adopted process's own output isn't ours to redirect; log stays supervisor-only
  else
    log "--- attempt ${attempt}/${MAX_ATTEMPTS} (elapsed $(elapsed_hours)h) -> $ATTEMPT_LOG"
    PROMPT_TEXT="$(cat "$KICKOFF")"
    if (( attempt > 1 )); then
      PROMPT_TEXT="⚠ SUPERVISED RE-INVOCATION (attempt ${attempt}) — the previous conductor session dropped, hung, or crashed. BEFORE doing anything else: check whether 00_ARCHITECTURE/briefs/ekavakyata/ already exists on origin/campaign-coordination. If it does, this is a RESUME, not a fresh start — read LEDGER_CONDUCTOR.md and ekv_manifest.json, do NOT re-seed, do NOT relaunch streams already LIVE or with a recent heartbeat, and resume your standing duties from current state. Only run the full T0 sequence below if that briefs directory genuinely does not exist yet.

${PROMPT_TEXT}"
    fi

    setsid bash -c '
      cd "$1" || exit 90
      exec "$2" "$3"m env -u CLAUDECODE "$4" -p "$5" --model sonnet --permission-mode bypassPermissions
    ' _ "$REPO" "$TIMEOUT_BIN" "$ATTEMPT_TIMEOUT_MIN" "$CLAUDE" "$PROMPT_TEXT" >>"$ATTEMPT_LOG" 2>&1 &
    child=$!
  fi
  ADOPT_PID=""   # only ever adopt once

  # Watch it: finish, or stall. A stall now requires BOTH signals to be quiet —
  # local log AND coordination-branch commits — not local log alone (see fix note above).
  last_size=-1
  stall_ticks=0
  coord_baseline=$(coord_last_commit_epoch)
  while kill -0 "$child" 2>/dev/null; do
    sleep 60
    cur_size=$(stat -f %z "$ATTEMPT_LOG" 2>/dev/null || stat -c %s "$ATTEMPT_LOG" 2>/dev/null || echo 0)
    coord_now=$(coord_last_commit_epoch)
    if [[ "$cur_size" == "$last_size" && "$coord_now" == "$coord_baseline" ]]; then
      stall_ticks=$(( stall_ticks + 1 ))
    else
      stall_ticks=0
      coord_baseline=$coord_now
    fi
    last_size=$cur_size
    if (( stall_ticks >= STALL_MINUTES )); then
      log "STALL: no attempt-log growth AND no new coordination-branch commit for ${stall_ticks}m (limit ${STALL_MINUTES}m). Killing attempt ${attempt} (whole process group)."
      kill -TERM -"$child" 2>/dev/null; kill -TERM "$child" 2>/dev/null
      sleep 10
      kill -KILL -"$child" 2>/dev/null; kill -KILL "$child" 2>/dev/null
      break
    fi
  done
  if (( adopting == 1 )); then
    while kill -0 "$child" 2>/dev/null; do sleep 5; done
    rc=$?
  else
    wait "$child" 2>/dev/null; rc=$?
  fi
  log "attempt ${attempt} exited/ended (rc=${rc} where applicable)"

  term=$(check_terminal)
  if [[ "$term" == "COMPLETE" ]]; then
    log "origin/${COORD_BRANCH_REMOTE} shows RUN-TERMINAL COMPLETE after attempt ${attempt}."
    exit 0
  fi
  if [[ "$term" == "PARTIAL" ]]; then
    log "origin/${COORD_BRANCH_REMOTE} shows EKV-NIGHT1-PARTIAL after attempt ${attempt} — honest gated close. Not retrying."
    exit 0
  fi

  pause=$(( BACKOFF_SECONDS + attempt * 10 ))
  log "No terminal marker yet (dropped, hung, or timed out). Resuming in ${pause}s — conductor picks up from the coordination branch."
  sleep "$pause"
done
