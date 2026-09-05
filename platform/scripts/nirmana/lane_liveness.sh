#!/usr/bin/env bash
# NIRMĀṆA — per-lane liveness, measured at the PUSH (charter §C2 / resume §R3).
# Conductor-owned shared campaign tooling. Read-only.
#
#   platform/scripts/nirmana/lane_liveness.sh [threshold_minutes]   # default 45
#
# WHY MEASURE AT THE PUSH
# Merges are not liveness. On 2026-09-05 the queue kept draining branches that dead
# lanes had pushed hours earlier -- #1788 merged at 04:07 while L4's last push was
# 00:40Z -- so four dead lanes looked alive and the Conductor missed it for hours.
#
# WHY EXCLUDE THE CONDUCTOR'S OWN COMMITS
# All seven sessions share one git identity, so author does not distinguish them and
# branch namespace is the only signal. But the Conductor legitimately pushes to a
# LAYER's branch when it carries an abandoned PR (C5: the evidence lib is
# Conductor-owned; #1736 was rebased by the Conductor while L1's lane was down).
# Counting that as L1 liveness reports a dead lane as alive -- which happened, and is
# exactly the failure this script exists to prevent. So commits whose subject begins
# `CONDUCTOR:` are excluded from a layer lane's attribution.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
THRESHOLD="${1:-45}"
NOW=$(date -u +%s)
git fetch origin -q

printf '%-11s %-11s %8s  %s\n' LANE LAST_PUSH AGE_MIN VERDICT
for L in l0 l1 l2 l3 l4 l5 conductor; do
  BEST_TS=0; BEST_REF=""
  while read -r TS REF; do
    [ -z "${TS:-}" ] && continue
    # Skip commits the Conductor authored on a layer lane's branch.
    if [ "$L" != "conductor" ]; then
      SUBJ=$(git log -1 --format=%s "$REF" 2>/dev/null || echo "")
      case "$SUBJ" in CONDUCTOR:*) continue ;; esac
    fi
    if [ "$TS" -gt "$BEST_TS" ]; then BEST_TS="$TS"; BEST_REF="$REF"; fi
  done < <(
    git for-each-ref --format='%(committerdate:unix) %(refname:short)' refs/remotes/origin \
      | if [ "$L" = "l0" ]; then grep -E "nirmana-l0-|fix/nirmana"
        else grep -E "nirmana-$L-"; fi || true
  )
  [ "$BEST_TS" -eq 0 ] && { printf '%-11s %-11s %8s  %s\n' "$L" "-" "-" "no branch"; continue; }
  AGE=$(( (NOW - BEST_TS) / 60 ))
  if [ "$L" = "conductor" ]; then V="";
  elif [ "$AGE" -gt "$THRESHOLD" ]; then V="*** PRESUMED DEAD -- re-paste sessions/resume/RESUME_$(echo "$L" | tr "[:lower:]" "[:upper:]").md ***";
  else V="alive"; fi
  printf '%-11s %-11s %8s  %s\n' "$L" "$(date -u -r "$BEST_TS" +%H:%M:%SZ)" "$AGE" "$V"
done
