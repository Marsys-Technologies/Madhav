#!/bin/bash
# parisesa_launch.sh — spawn the five PARIŚEṢA stream sessions in parallel.
# Run BY THE CONDUCTOR at T0 step 4 (not by the human; the human runs only the
# conductor). Pattern lifted from run_pp2.sh (proven CLI invocation + auth probe).
#
# Each stream: own detached claude session · own worktree · own log · one relaunch
# on early crash (<10 min) — beyond that, SENTINEL/conductor decide.
set -u
SHAD=/Users/Dev/shad_overnight
REPO=/Users/Dev/Vibe-Coding/Apps/Madhav
LOGS=$SHAD/par-logs; mkdir -p "$LOGS"
CLAUDE=/Users/Dev/.local/bin/claude
PLAN=$SHAD/PARISESA_EXECUTION_PLAN_v1_0.md

[ -x "$CLAUDE" ] || { echo "FATAL: claude CLI missing"; exit 1; }
[ -f "$PLAN" ]   || { echo "FATAL: plan of record missing"; exit 1; }

# Auth probe (the 2026-08-14 Δ3 lesson: without this every attempt dies at ~60s)
AUTH=$(env -u CLAUDECODE "$CLAUDE" -p "Reply with exactly: AUTH_OK" \
  --model sonnet --permission-mode bypassPermissions </dev/null 2>&1 | tail -3)
echo "$AUTH" | grep -q AUTH_OK || { echo "FATAL: claude auth probe failed: $AUTH"; exit 1; }

# DB proxy (read paths + C-lane migration verify need 5433)
pgrep -f "cloud-sql-proxy.*5433" >/dev/null || echo "WARN: cloud-sql-proxy :5433 not running — conductor must start it before C/E lanes need the DB"

launch_stream() {  # $1=letter  $2=worktree-name  $3=branchless(worktree cut at launch)
  local S=$1 WTN=par-lead-$2
  local WT="$REPO/.claude/worktrees/$WTN"
  local KICK="$SHAD/parisesa_stream_$S.md"
  [ -f "$KICK" ] || { echo "FATAL: missing $KICK"; return 1; }
  # Lead worktree on a lead-scratch branch; builders make their own lane worktrees.
  if [ ! -d "$WT" ]; then
    git -C "$REPO" fetch origin main --quiet
    git -C "$REPO" worktree add -b "par/lead-$2" "$WT" origin/main >/dev/null 2>&1 \
      || git -C "$REPO" worktree add "$WT" "par/lead-$2" >/dev/null 2>&1
  fi
  (
    for ATTEMPT in 1 2; do
      START=$(date +%s)
      echo "── stream $S attempt $ATTEMPT $(date -u +%H:%M:%SZ) ──" >> "$LOGS/stream_${S}.log"
      cd "$WT" && env -u CLAUDECODE "$CLAUDE" -p "$(cat "$KICK")" \
        --model sonnet \
        --permission-mode bypassPermissions \
        >> "$LOGS/stream_${S}.log" 2>&1
      DUR=$(( $(date +%s) - START ))
      echo "── stream $S attempt $ATTEMPT exited after ${DUR}s ──" >> "$LOGS/stream_${S}.log"
      # Relaunch once only on an early crash; a long run that ends is a session end,
      # not a crash — conductor/SENTINEL own that judgment.
      [ $DUR -ge 600 ] && break
    done
  ) </dev/null >/dev/null 2>&1 &
  disown
  echo "launched stream $S (log: $LOGS/stream_${S}.log)"
}

launch_stream S1 dvara
launch_stream S2 matra
launch_stream S3 satya
launch_stream S4 vaca
launch_stream S5 mula
launch_stream S6 adhara

echo "All six streams launched $(date -u +%H:%M:%SZ). Watch: tail -f $LOGS/stream_*.log"
