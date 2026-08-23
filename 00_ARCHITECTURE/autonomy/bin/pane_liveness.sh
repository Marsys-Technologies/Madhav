#!/usr/bin/env bash
# pane_liveness.sh — the DETECTOR behind D-60 §5's restart precondition.
#
# D-60 §5 (2026-08-23, ADHIKĀRIN, power G9): "A PANE-LIVENESS CHECK IS A PRECONDITION OF A
# RESTART, NOT A CORROBORATION OF ONE. Where the pane shows an agent mid-operation, heartbeat
# silence is NOT a stall and the agent is not restarted at any silence duration — it is
# escalated. Where the pane shows an idle or dead prompt, the restart proceeds as today."
#
# Invoked by prompts/monitor.md §1 (PRAHARĪ's liveness ladder) before EVERY restart.
# Read-only: it captures panes. It never sends keys, never restarts, never writes state.
#
# WHY A SCRIPT AND NOT A JUDGEMENT CALL: on 2026-08-23 at ~14:45Z the conductor captured a
# pane reading "esc to interrupt · ← 1 agent" — an agent ACTIVELY RUNNING — and read it as
# idle-at-prompt. A precondition a reader can misread is not a precondition. This file is the
# code path that would have to run, and return RUNNING, for that call to be made correctly;
# per CLAUDE.md §N.8 a signal without such a path is null, not green.
#
# USAGE
#   pane_liveness.sh <tmux-target>              # e.g. nirmana:monitor.0 — live, 2 captures
#   pane_liveness.sh --file A.txt [B.txt]       # classify captured text (fixtures / tests)
#
# OUTPUT (stdout, one line):  <STATE> <restart_verdict> <reason>
#
# EXIT CODES — these are the decision, not the text:
#   0  RESTART_PERMITTED   precondition satisfied: pane is idle or dead
#   10 RESTART_WITHHELD    pane is mid-operation (or frozen mid-operation) — ESCALATE, per D-60 §5
#   20 RESTART_WITHHELD    indeterminate: the precondition could NOT be evaluated — ESCALATE.
#                          An unevaluated precondition is an unsatisfied one. Never restart on 20.
#   2  usage error
#
# STATES
#   RUNNING                "esc to interrupt" present, or a live spinner, or the pane redrew
#   RUNNING_FROZEN_SUSPECT running markers present but two captures were byte-identical and no
#                          elapsed counter advanced — still NOT restartable (D-60 §5 is absolute
#                          on mid-operation); report it as a real failure to ADHIKĀRIN instead
#   IDLE_AT_PROMPT         turn finished cleanly, compose box empty
#   IDLE_UNPOKED           turn finished, text stranded unsubmitted in the compose box (D-14).
#                          Remedy per D-14/FLEET-POKE-DEFECT is submit-and-verify or SendMessage;
#                          restart is permitted but is the heavier of the two.
#   DEAD                   tmux reports pane_dead=1, or the target does not exist
#   UNKNOWN                capture produced nothing
#
# MARKER PROVENANCE — measured, not assumed. Live read-only captures of all five nirmana panes
# at 2026-08-23T15:0xZ (fixtures/pane_liveness/live-*.txt):
#   * "esc to interrupt" appeared on exactly the panes that were generating, and on no idle pane.
#   * "← 1 agent" appeared on ALL FIVE panes, running and idle alike — it is an agent COUNT, not
#     a liveness signal, and must never be read as one.
#   * The past-tense spinner line ("✻ Cooked for 6m 5s", "✻ Sautéed for 45s") appeared on IDLE
#     panes. It is the RESIDUE of a finished turn, so "Crunched for 2m 14s" alone does NOT prove
#     an agent is mid-operation. The live form carries an ellipsis and a parenthesised advancing
#     counter: "✻ Pondering… (15m 4s · ↓ 52.0k tokens)".

set -uo pipefail

DELAY="${PANE_LIVENESS_DELAY:-8}"

emit() { printf '%s %s %s\n' "$1" "$2" "$3"; exit "$4"; }

has_running_marker() {   # $1 = file
  grep -q 'esc to interrupt' "$1" && return 0
  # live spinner: a spinner glyph line ending in "… (<elapsed>" — the advancing form
  grep -Eq '…[[:space:]]*\([^)]*[0-9]+(s|m|h)' "$1" && return 0
  return 1
}

compose_box_text() {     # $1 = file -> prints whatever sits in the ❯ compose box
  sed -n 's/^[[:space:]]*❯[[:space:]]*//p' "$1" | tr -d '[:space:]'
}

# Elapsed seconds shown by the LIVE spinner form, e.g. "✻ Pondering… (15m 4s · ↓ 52.0k tokens)".
# Prints nothing when the pane shows no parseable live counter — in which case "frozen" has no
# detector and must NOT be claimed (CLAUDE.md §N.8: no detector, no signal).
spinner_elapsed() {      # $1 = file
  grep -Eo '…[[:space:]]*\([^)]*' "$1" | head -1 | awk '{
    h=0;m=0;s=0
    if (match($0,/[0-9]+h/)) { h=substr($0,RSTART,RLENGTH-1)+0 }
    if (match($0,/[0-9]+m/)) { m=substr($0,RSTART,RLENGTH-1)+0 }
    if (match($0,/[0-9]+s/)) { s=substr($0,RSTART,RLENGTH-1)+0 }
    if (h==0 && m==0 && s==0) exit
    print h*3600+m*60+s
  }'
}

classify() {             # $1 = capture A, $2 = capture B (may equal $1)
  local a="$1" b="$2"
  if [ ! -s "$a" ]; then
    emit UNKNOWN RESTART_WITHHELD "capture-empty:precondition-not-evaluable" 20
  fi
  if has_running_marker "$a" || has_running_marker "$b"; then
    if [ "$a" != "$b" ] && ! cmp -s "$a" "$b"; then
      emit RUNNING RESTART_WITHHELD "mid-operation:running-marker+pane-redrew" 10
    fi
    if [ "$a" = "$b" ]; then
      emit RUNNING RESTART_WITHHELD "mid-operation:running-marker(single-capture)" 10
    fi
    # Two captures, byte-identical. That alone does not prove FROZEN: a running pane can redraw
    # nothing in a short window. Only claim frozen when the pane's own live elapsed counter
    # parsed in BOTH captures and did NOT advance across the delay. Otherwise say RUNNING.
    ea="$(spinner_elapsed "$a")"; eb="$(spinner_elapsed "$b")"
    if [ -n "$ea" ] && [ -n "$eb" ] && [ "$ea" = "$eb" ] && [ "$DELAY" -ge 8 ]; then
      emit RUNNING_FROZEN_SUSPECT RESTART_WITHHELD \
           "mid-operation:elapsed-counter-stuck-at-${ea}s-across-${DELAY}s;escalate-do-not-restart" 10
    fi
    emit RUNNING RESTART_WITHHELD "mid-operation:running-marker;no-frozen-detector-fired" 10
  fi
  # No running marker. If the pane still redrew, something is alive — refuse to restart.
  if [ "$a" != "$b" ] && ! cmp -s "$a" "$b"; then
    emit RUNNING RESTART_WITHHELD "mid-operation:pane-redrew-without-running-marker" 10
  fi
  if [ -n "$(compose_box_text "$a")" ]; then
    emit IDLE_UNPOKED RESTART_PERMITTED "turn-finished:text-stranded-in-compose-box(D-14)" 0
  fi
  emit IDLE_AT_PROMPT RESTART_PERMITTED "turn-finished:compose-box-empty" 0
}

case "${1:-}" in
  --file)
    [ -n "${2:-}" ] || { echo "usage: $0 --file A.txt [B.txt]" >&2; exit 2; }
    classify "$2" "${3:-$2}"
    ;;
  ""|-h|--help)
    sed -n '2,40p' "$0"; exit 2
    ;;
  *)
    TARGET="$1"
    # Resolve the target explicitly. A target tmux cannot resolve is NOT a dead pane and must
    # not authorise a restart — it is most likely a typo, and "restart what you could not find"
    # is how a watchdog restarts the wrong thing. Fail closed: UNKNOWN, withhold, escalate.
    dead="$(tmux list-panes -a -F '#{session_name}:#{window_name}.#{pane_index} #{pane_dead}' 2>/dev/null \
            | awk -v t="$TARGET" '$1==t {print $2; found=1} END{if(!found) print ""}')"
    if [ -z "$dead" ]; then
      dead="$(tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} #{pane_dead}' 2>/dev/null \
              | awk -v t="$TARGET" '$1==t {print $2}')"
    fi
    if [ -z "$dead" ]; then
      emit UNKNOWN RESTART_WITHHELD "tmux-target-unresolvable:$TARGET" 20
    fi
    if [ "$dead" = "1" ]; then
      emit DEAD RESTART_PERMITTED "tmux-reports-pane_dead=1" 0
    fi
    A="$(mktemp -t paneliv.XXXXXX)"; B="$(mktemp -t paneliv.XXXXXX)"
    trap 'rm -f "$A" "$B"' EXIT
    tmux capture-pane -p -t "$TARGET" > "$A" 2>/dev/null
    sleep "$DELAY"
    tmux capture-pane -p -t "$TARGET" > "$B" 2>/dev/null
    classify "$A" "$B"
    ;;
esac
