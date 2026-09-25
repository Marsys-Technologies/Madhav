#!/usr/bin/env bash
# ==============================================================================
# test_progress_and_backoff.sh — the before-fail / after-pass proof for
# Phase 1.4a (progress detector) and 1.4b (idle backoff).
#
#   ./test_progress_and_backoff.sh legacy   -> MUST FAIL  (today's behaviour)
#   ./test_progress_and_backoff.sh new      -> MUST PASS  (after the fix)
#
# Same fixture, same assertions, only the detector/backoff implementation swaps.
# The fixture simulates a GENUINELY STUCK session: it polls, it logs, it
# heartbeats, it rewrites the state file's timestamp header, it drops a scratch
# note in _work/ — and it commits nothing, moves no counter, and changes no
# substantive state.  That is exactly the cycle the audit run repeated five
# times at ~$0.80 each while the supervisor logged progress=yes.
#
# Assertions:
#   A1  three consecutive stuck cycles produce a no-progress streak of 3
#       (i.e. the existing 3-strikes halt can actually fire).
#   A2  a genuine-progress cycle resets the streak to 0
#       (i.e. the detector is not simply always-false — §N.8 cuts both ways).
#   A3  the backoff over that stall is 30s, 300s, 900s — not 30s, 30s, 30s.
# ==============================================================================
set -uo pipefail
MODE="${1:-new}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/../lib/progress.sh"

T="$(mktemp -d "${TMPDIR:-/tmp}/p14test.XXXXXX")"
trap 'rm -rf "$T"' EXIT
WT="$T/wt"; LOGD="$T/logs"        # logs live OUTSIDE the worktree, as in the real rig
A="$WT/00_ARCHITECTURE/briefs/nirmana/l3_autonomous"
STATE="$A/KALA_ELEVATION_STATE.md"
mkdir -p "$A/_work" "$WT/00_ARCHITECTURE/autonomy/state" "$WT/platform/python-sidecar/ka_writers" "$LOGD"

git -C "$WT" init -q -b main
git -C "$WT" config user.email t@example.invalid
git -C "$WT" config user.name "P14 Test"

cat > "$STATE" <<'EOF'
# KĀLA ELEVATION STATE
last_supervisor_cycle: 0
updated: 2026-09-22T00:00:00+05:30

Accepted 0/22

## Position
packet: E1 — ka_graha_sancara — BLOCKED_STRUCTURAL(native decision item 4)
next: native ruling on the CASCADE remediation
## End
EOF
echo "def build(): return 1" > "$WT/platform/python-sidecar/ka_writers/ka_graha_sancara.py"
: > "$A/EVENTS.jsonl"
: > "$WT/00_ARCHITECTURE/autonomy/state/HEARTBEAT.jsonl"
git -C "$WT" add -A >/dev/null && git -C "$WT" commit -qm "fixture: initial campaign state"

fp() {  # the detector under test
  if [ "$MODE" = legacy ]; then legacy_fingerprint "$WT" "$STATE" "$A" "$A/_work"
  else                          progress_fingerprint "$WT" "$STATE"; fi
}
bo() {  # the backoff under test
  if [ "$MODE" = legacy ]; then legacy_backoff_secs "$1" "$2"
  else                          backoff_secs "$1" "$2"; fi
}

stuck_cycle() {   # everything a stalled-but-alive session still does
  local n="$1"
  echo "[sup] cycle $n polling CI, nothing eligible" >> "$LOGD/supervisor.log"
  echo '{"type":"result","num_turns":12,"total_cost_usd":0.81}' >> "$LOGD/cycle_$n.ndjson"
  echo "{\"ts\":\"$(date -u +%FT%TZ)\",\"cycle\":$n,\"event\":\"heartbeat\"}" >> "$A/EVENTS.jsonl"
  echo "{\"ts\":\"$(date -u +%FT%TZ)\",\"alive\":true}" >> "$WT/00_ARCHITECTURE/autonomy/state/HEARTBEAT.jsonl"
  echo "cycle $n: re-checked PR queue, still red" > "$A/_work/cycle_${n}_scratch.md"
  # rewrites the state file every cycle, as the cycle prompt demands — but only
  # its timestamp header; the substantive sections are byte-identical.
  perl -0pi -e "s/^last_supervisor_cycle: .*/last_supervisor_cycle: $n/m; s/^updated: .*/updated: 2026-09-22T0$n:00:00+05:30/m" "$STATE"
  touch "$WT/platform/python-sidecar/ka_writers/ka_graha_sancara.py"
}

real_cycle() {    # a cycle that actually moved the campaign
  perl -0pi -e 's/Accepted 0\/22/Accepted 1\/22/; s/BLOCKED_STRUCTURAL\(native decision item 4\)/ACCEPTED via freeze event 8c11d2/' "$STATE"
  echo "def build(): return 2  # elevated" > "$WT/platform/python-sidecar/ka_writers/ka_graha_sancara.py"
  git -C "$WT" add -A >/dev/null && git -C "$WT" commit -qm "E1: ka_graha_sancara accepted" >/dev/null
}

fail=0
note() { printf '%s\n' "$*"; }
assert() { # <desc> <actual> <expected>
  if [ "$2" = "$3" ]; then printf '  PASS  %-52s got=%s\n' "$1" "$2"
  else printf '  FAIL  %-52s got=%s want=%s\n' "$1" "$2" "$3"; fail=1; fi
}

note "=============================================================="
note " PHASE 1.4a/1.4b proof — detector/backoff mode: $MODE"
note "=============================================================="
note ""
note "-- A1: three consecutive genuinely-stuck cycles ---------------"
noprog=0; sched=()
for n in 1 2 3; do
  before="$(fp)"
  stuck_cycle "$n"
  after="$(fp)"
  if [ "$before" = "$after" ]; then noprog=$((noprog+1)); else noprog=0; fi
  slp="$(bo 0 "$noprog")"; sched+=("$slp")
  printf '  cycle %d  progress=%-3s  streak=%d  sleep=%ss\n' \
     "$n" "$([ "$before" = "$after" ] && echo NO || echo yes)" "$noprog" "$slp"
  printf '            before=%s\n            after =%s\n' "$before" "$after"
done
assert "no-progress streak after 3 stuck cycles" "$noprog" "3"
assert "3-strikes halt fires" "$([ "$noprog" -ge 3 ] && echo HALT || echo never)" "HALT"
note ""
note "-- A2: a cycle that really moved the campaign -----------------"
before="$(fp)"; real_cycle; after="$(fp)"
if [ "$before" = "$after" ]; then noprog=$((noprog+1)); else noprog=0; fi
printf '            before=%s\n            after =%s\n' "$before" "$after"
assert "genuine progress resets the streak" "$noprog" "0"
note ""
note "-- A3: idle backoff actually spent over that stall -------------"
printf '            schedule = %s (total %ss)\n' "${sched[*]}" \
   "$(( ${sched[0]} + ${sched[1]} + ${sched[2]} ))"
assert "sleep after stuck cycle 1" "${sched[0]}" "300"
assert "sleep after stuck cycle 2" "${sched[1]}" "900"
assert "sleep after stuck cycle 3" "${sched[2]}" "900"
note ""
note "-- A3b: backoff function in isolation (independent of detector) -"
for pair in "0 0 30" "0 1 300" "0 2 900" "0 3 900" "3 0 300" "5 2 300"; do
  set -- $pair
  assert "backoff crash=$1 noprog=$2" "$(bo "$1" "$2")" "$3"
done
note ""
note "-- A4: the tracked-content term is live, not permanently empty --"
note "     (A1 showed it ignores EVENTS/HEARTBEAT churn; this shows it does"
note "      fire for an UNCOMMITTED edit to a real deliverable — so the term"
note "      has a real detector behind it, not a constant. CLAUDE.md §N.8.)"
before="$(fp)"
echo "def build(): return 3  # wip, not yet committed" > "$WT/platform/python-sidecar/ka_writers/ka_graha_sancara.py"
after="$(fp)"
printf '            before=%s\n            after =%s\n' "$before" "$after"
assert "uncommitted deliverable edit counts as progress" \
   "$([ "$before" = "$after" ] && echo NO || echo yes)" "yes"

note ""
if [ "$fail" -eq 0 ]; then note "RESULT: ALL ASSERTIONS PASS ($MODE)"; else note "RESULT: FAILURES PRESENT ($MODE)"; fi
exit "$fail"
