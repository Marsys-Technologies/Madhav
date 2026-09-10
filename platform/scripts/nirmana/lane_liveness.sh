#!/usr/bin/env bash
# NIRMĀṆA — per-lane liveness, MULTI-SIGNAL (charter §C2 / resume §R3).
# Conductor-owned shared campaign tooling. Read-only.
#
#   platform/scripts/nirmana/lane_liveness.sh [stale_minutes]   # default 45
#
# WHY THREE SIGNALS AND NOT ONE
#
# Push-only was wrong twice, in opposite directions, within one night:
#
#   1. FALSE ALIVE. Merges are not liveness -- the queue kept draining branches dead
#      lanes had pushed hours earlier (#1788 merged at 04:07 while L4's last push was
#      00:40Z), so four dead lanes looked busy. Fixed by measuring at the push.
#   2. FALSE DEAD. A lane deep in a long W3 task does not push for an hour. L2 was
#      reported DEAD at 57 minutes while its worktree had files modified 3 minutes
#      earlier -- it was working the whole time, and the Conductor told the native to
#      re-paste a live session.
#
# So: WORKTREE FILE MTIME is the fastest signal (a session touches files constantly),
# PUSH is the durable one (survives a worktree being moved or cleaned), and GH ACTIVITY
# catches a lane that is thinking and commenting rather than editing.
#
# A THIRD SIGNAL WAS TRIED AND REMOVED: GitHub comment activity. All seven sessions
# authenticate as ONE GitHub account, so gh activity cannot distinguish a lane's own
# comments from the Conductor's comments ABOUT that lane -- the first run scored L1
# "active 41m ago" when that 41m was the Conductor commenting on L1's issues. That is
# the same one-identity-across-seven-sessions root cause as the branch-name attribution
# bug, and unlike that one it is not fixable by filtering. A contaminated signal that
# reports the observer as the observed is worse than no signal, so there are two.
#
# The three verdicts are deliberately distinct, because they need different responses:
#
#   WORKING   -- files changing. Leave it alone.
#   IDLE?     -- no file changes, but pushed or commented recently. The process is very
#                likely alive and between tasks. THIS is the case worth nudging: a live
#                session with nothing queued is the one thing the campaign cannot afford
#                (§R2 says the ladder always has work).
#   DEAD      -- nothing on any signal. Re-paste its resume prompt; a dead CLI cannot be
#                resurrected remotely (charter C7).
set -euo pipefail
STALE="${1:-45}"
ROOT="$HOME/nirmana-s"
REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
NOW=$(date -u +%s)
git -C "$REPO" fetch origin -q || true

printf '%-6s %-10s %-11s %s\n' LANE FILES PUSH VERDICT
for L in l0 l1 l2 l3 l4 l5; do
  # --- signal 1: worktree file mtime (any worktree whose name starts with the lane) ---
  FMIN=99999
  for D in "$ROOT/$L" "$ROOT/$L-"*; do
    [ -d "$D" ] || continue
    if find "$D" -type f -mmin -"$STALE" -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null | head -1 | grep -q .; then
      FMIN=0; break
    fi
  done
  # --- signal 2: last push on the lane's branches, excluding Conductor-authored commits ---
  BEST=0
  while read -r TS REF; do
    [ -z "${TS:-}" ] && continue
    SUBJ=$(git -C "$REPO" log -1 --format=%s "$REF" 2>/dev/null || echo "")
    case "$SUBJ" in CONDUCTOR:*) continue ;; esac
    [ "$TS" -gt "$BEST" ] && BEST="$TS"
  done < <(
    git -C "$REPO" for-each-ref --format='%(committerdate:unix) %(refname:short)' refs/remotes/origin \
      | if [ "$L" = "l0" ]; then grep -E "nirmana-l0-|fix/nirmana"; else grep -E "nirmana-$L-"; fi || true
  )
  PMIN=$([ "$BEST" -gt 0 ] && echo $(( (NOW - BEST) / 60 )) || echo 99999)
  fmt() { [ "$1" -ge 99999 ] && echo "-" || echo "${1}m"; }
  if [ "$FMIN" -eq 0 ]; then V="WORKING"
  elif [ "$PMIN" -lt "$STALE" ]; then V="IDLE? -- alive but not editing; NUDGE with available work"
  else V="DEAD -- re-paste sessions/resume/RESUME_$(echo "$L" | tr '[:lower:]' '[:upper:]').md"
  fi
  printf '%-6s %-10s %-11s %s\n' "$L" \
    "$([ "$FMIN" -eq 0 ] && echo "<${STALE}m" || echo "none")" "$(fmt "$PMIN")" "$V"
done
