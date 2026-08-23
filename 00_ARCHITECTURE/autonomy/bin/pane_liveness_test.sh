#!/usr/bin/env bash
# pane_liveness_test.sh — the BOTH-WAYS proof for pane_liveness.sh.
#
# A precondition with no detector is the defect this campaign exists to remove (CLAUDE.md §N.8,
# charter H4/I5). So the detector must be shown to return BOTH answers on real inputs: it must
# WITHHOLD a restart on a pane that is mid-operation, and PERMIT one on a pane that is genuinely
# idle. A check that can only ever say "permitted" is not a precondition; neither is one that can
# only ever say "withheld" — that would just be D-60 §4's suspended watchdog wearing a rule's
# clothes.
#
# Fixture provenance is stated per case: LIVE = verbatim `tmux capture-pane -p` output taken
# read-only on 2026-08-23; RECON = reconstructed to the shape the campaign ledger records for
# that episode (the campaign archived no raw pane text, so these are shapes, not transcripts).

set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DET="$HERE/pane_liveness.sh"
FIX="$HERE/fixtures/pane_liveness"
pass=0; fail=0

check() {  # check <label> <fixture> <expected-state> <expected-exit>
  local label="$1" fx="$2" want_state="$3" want_exit="$4"
  local out rc
  out="$("$DET" --file "$FIX/$fx" 2>&1)"; rc=$?
  local got_state="${out%% *}"
  if [ "$got_state" = "$want_state" ] && [ "$rc" = "$want_exit" ]; then
    printf 'PASS  %-46s -> %s (exit %s)\n' "$label" "$out" "$rc"; pass=$((pass+1))
  else
    printf 'FAIL  %-46s -> %s (exit %s); wanted %s exit %s\n' \
      "$label" "$out" "$rc" "$want_state" "$want_exit"; fail=$((fail+1))
  fi
}

echo "=== DIRECTION 1: pane reads mid-operation => RESTART CORRECTLY WITHHELD (exit 10) ==="
# The exact call the conductor got wrong at ~14:45Z on 2026-08-23: it captured a pane reading
# "esc to interrupt · ← 1 agent" and read it as idle-at-prompt. RECON.
check "conductor tick-7 PRAHARI (the misread)" recon-conductor-tick7-prahari-running.txt RUNNING 10
# LIVE: PARIKSAKA generating, "✻ Pondering… (15m 4s · ↓ 52.0k tokens)" + esc to interrupt.
check "LIVE PARIKSAKA mid-turn"               live-pariksaka-running.txt              RUNNING 10

echo
echo "=== DIRECTION 2: pane reads genuinely idle => RESTART CORRECTLY PROCEEDS (exit 0) ==="
# LIVE: PRAHARI itself, turn finished ("✻ Sautéed for 45s"), compose box empty, NO esc-to-interrupt.
check "LIVE PRAHARI idle at prompt"           live-prahari-idle-at-prompt.txt IDLE_AT_PROMPT 0
# RECON of the capture PRAHARI took BEFORE restarting LEKHAKA at 13:31Z ("Worked for 1m 35s",
# idle at the TUI prompt) — a restart the ledger shows was correct: LEKHAKA moved only after it.
check "LEKHAKA 13:31Z pre-restart capture"    recon-lekhaka-1331-idle-at-prompt.txt IDLE_AT_PROMPT 0
# RECON of D-14 / FLEET-POKE-DEFECT: poke text stranded unsubmitted in the compose box.
check "D-14 idle-unpoked (stranded text)"     recon-idle-unpoked-stranded-text.txt   IDLE_UNPOKED 0
# ARCHIVED VERBATIM — the only raw pane text the campaign preserved: PRAHARI quoted this capture
# inside mailbox/to_adhikarin/20260823T042804Z-pariksaka-pane-appears-stuck.md, three
# byte-identical captures over a multi-minute window. Note it carries NO "esc to interrupt" and
# the spinner line is the static past-tense form — independent, contemporaneous corroboration of
# the marker set, recorded hours before this detector existed.
check "ARCHIVED PARIKSAKA 04:28Z (D-14 origin)" archived-pariksaka-0428-idle-unpoked.txt IDLE_UNPOKED 0

echo
echo "=== DIRECTION 3: precondition not evaluable => WITHHELD, never a default-permit (exit 20) ==="
check "capture returned nothing"              empty-capture.txt                      UNKNOWN 20

echo
echo "=== DIRECTION 4: unrecognised TUI => FAIL LOUD, never a silent permit (exit 20) ==="
# The dangerous direction. Without a shape check, a TUI that drops "esc to interrupt" would fall
# through to IDLE_AT_PROMPT and PERMIT restarting a RUNNING agent — the detector would break
# silently, in the one direction that costs something. Raised by SUTRADHARA at 15:09Z: "a
# detector that keys on one string in a TUI status line is keying on an implementation detail of
# a version, and it will break silently when that changes."
check "unrecognised status line fails closed"  unrecognised-status-line.txt           UNKNOWN 20

echo
echo "=== NEGATIVE CONTROL: the marker that is NOT a liveness signal ==="
# "← 1 agent" appeared on ALL FIVE live panes, running and idle alike. If the detector were
# keying off it, the two LIVE fixtures above could not have come out differently. They did.
a=$(grep -c '← 1 agent' "$FIX/live-pariksaka-running.txt" || true)
b=$(grep -c '← 1 agent' "$FIX/live-prahari-idle-at-prompt.txt" || true)
if [ "$a" -ge 1 ] && [ "$b" -ge 1 ]; then
  echo "PASS  '← 1 agent' present on BOTH the running and the idle live pane (counts $a/$b)"
  echo "      -> it is an agent count, not liveness; the detector's split above is not keyed on it"
  pass=$((pass+1))
else
  echo "FAIL  negative control: '← 1 agent' counts $a/$b — expected >=1 on both"; fail=$((fail+1))
fi

echo
echo "=== DEAD branch, proven on a THROWAWAY tmux session (never the fleet) ==="
# The DEAD state is the one branch no fixture can exercise: it is tmux's own verdict, not text.
# So prove it against a pane this harness creates and destroys itself. It never touches the
# nirmana session — a test that poked a live fleet pane would be the very thing D-60 forbids.
if command -v tmux >/dev/null 2>&1; then
  TS="paneliv-selftest-$$"
  tmux kill-session -t "$TS" 2>/dev/null
  tmux new-session -d -s "$TS" -n dead 'true' 2>/dev/null
  tmux set-option -t "$TS" remain-on-exit on 2>/dev/null
  tmux respawn-pane -k -t "$TS:dead.0" 'exit 0' 2>/dev/null
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    [ "$(tmux display-message -p -t "$TS:dead.0" '#{pane_dead}' 2>/dev/null)" = "1" ] && break
    sleep 0.3
  done
  out="$(PANE_LIVENESS_DELAY=1 "$DET" "$TS:dead.0" 2>&1)"; rc=$?
  if [ "${out%% *}" = "DEAD" ] && [ "$rc" = "0" ]; then
    printf 'PASS  %-46s -> %s (exit %s)\n' "throwaway pane_dead=1" "$out" "$rc"; pass=$((pass+1))
  else
    printf 'FAIL  %-46s -> %s (exit %s); wanted DEAD exit 0\n' "throwaway pane_dead=1" "$out" "$rc"
    fail=$((fail+1))
  fi
  tmux kill-session -t "$TS" 2>/dev/null
  # And an unresolvable target must NOT be read as dead — fail closed, never restart a typo.
  out="$("$DET" "$TS:doesnotexist.0" 2>&1)"; rc=$?
  if [ "${out%% *}" = "UNKNOWN" ] && [ "$rc" = "20" ]; then
    printf 'PASS  %-46s -> %s (exit %s)\n' "unresolvable target fails closed" "$out" "$rc"; pass=$((pass+1))
  else
    printf 'FAIL  %-46s -> %s (exit %s); wanted UNKNOWN exit 20\n' "unresolvable target" "$out" "$rc"
    fail=$((fail+1))
  fi
else
  echo "SKIP  tmux not available — DEAD branch unproven in this run (reported as unproven, not as pass)"
fi

echo
echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
