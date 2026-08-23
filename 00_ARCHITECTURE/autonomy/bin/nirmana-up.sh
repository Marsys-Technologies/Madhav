#!/usr/bin/env bash
# ── Nirmāṇa autonomous fleet · tmux launcher ────────────────────────────────
# Usage:  NIRMANA_REPO=/path/to/Madhav ./nirmana-up.sh [--dry-run]
#
# Creates tmux session "nirmana" with one window per long-lived agent.
# KĀRAKA agents are spawned by SŪTRADHĀRA as subagents, not as panes.
set -euo pipefail

REPO="${NIRMANA_REPO:?set NIRMANA_REPO to the Madhav repo root}"
A="$REPO/00_ARCHITECTURE/autonomy"
P="$A/prompts"
SESSION="${NIRMANA_SESSION:-nirmana}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
# If CLAUDE_BIN is a bare command name, resolve it to an absolute path now.
# Reason: each tmux pane runs an interactive zsh, and this machine's ~/.zshrc
# aliases `claude` to `claude --permission-mode bypassPermissions`. Sending the
# bare word "claude" into a pane re-triggers that alias and duplicates the flag
# we already pass explicitly below. An absolute path doesn't match the alias.
case "$CLAUDE_BIN" in
  */*) : ;;
  *)
    RESOLVED_CLAUDE_BIN="$(command -v "$CLAUDE_BIN" 2>/dev/null || true)"
    [ -n "$RESOLVED_CLAUDE_BIN" ] && CLAUDE_BIN="$RESOLVED_CLAUDE_BIN"
    ;;
esac
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

# Fallback only: if the calling shell didn't export a real DATABASE_URL, load one
# from a local, gitignored .env so tmux panes spawned below inherit it (panes get
# this process's environment at spawn time). Reads only the DATABASE_URL= line,
# never sources the file, so its content can't run as shell.
ENV_FILE="$A/.env"
if { [ -z "${DATABASE_URL:-}" ] || printf '%s' "${DATABASE_URL:-}" | grep -qE '…|\.\.\.|<|>|user:pass|example\.com'; } \
   && [ -f "$ENV_FILE" ]; then
  LOADED="$(grep -m1 '^DATABASE_URL=' "$ENV_FILE" | cut -d= -f2-)"
  [ -n "$LOADED" ] && DATABASE_URL="$LOADED" && export DATABASE_URL
fi

# Stamp the campaign window before anything reads the meter. Without this the meter counts
# every historical session in the repo and every token ceiling reads as breached at launch.
PYBIN="$REPO/.venv/bin/python"; [ -x "$PYBIN" ] || PYBIN="$(command -v python3)"
"$PYBIN" - "$A/state/CAMPAIGN_STATE.json" <<'PYS'
import json,sys,datetime
p=sys.argv[1]; st=json.load(open(p))
if not st.get("campaign_started_ts"):
    st["campaign_started_ts"]=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    json.dump(st,open(p,"w"),indent=2,ensure_ascii=False)
    print("[nirmana-up] campaign window opened at "+st["campaign_started_ts"])
else:
    print("[nirmana-up] campaign window already open since "+st["campaign_started_ts"])
PYS
# Baseline reading inside the new window, so preflight compares campaign spend, not history.
"$PYBIN" "$A/bin/spend_meter.py" >/dev/null 2>&1 || echo "[nirmana-up] WARNING: spend meter produced no reading"

"$A/bin/preflight.sh" || exit 1

# Build one agent's kickoff prompt: common ground + role prompt + standing order.
kick() {  # kick <role-file>
  cat "$P/_common.md" "$P/$1"
  cat <<EOF

---
## Standing order

You are running unattended in tmux window \`$SESSION:$2\`. Repo root: \`$REPO\`.
Work continuously. Do not ask a human anything — ADHIKĀRIN is your authority.
Heartbeat with: \`$A/bin/heartbeat.sh <YOUR-NAME> <status> "<detail>"\`
Begin now by reading CAMPAIGN_STATE.json and reporting your understanding of where the
campaign stands, then enter your loop.
EOF
}

# Poll a pane's rendered output for the TUI's steady-state footer marker, so we
# don't send the kick prompt before claude has finished starting up and is
# actually reading keystrokes as chat input. Falls back to a fixed sleep if the
# marker never shows up (e.g. footer text changes in a future CLI version).
wait_for_tui_ready() {  # wait_for_tui_ready <window>
  local win="$1" tries=0 max_tries=60
  while [ "$tries" -lt "$max_tries" ]; do
    if tmux capture-pane -p -t "$SESSION:$win" 2>/dev/null | grep -qE 'for shortcuts|bypass permissions on'; then
      sleep 0.3  # small settle margin past first paint
      return 0
    fi
    sleep 0.5
    tries=$((tries + 1))
  done
  echo "[nirmana-up] WARNING: TUI readiness marker not seen in window $win after ${max_tries}x0.5s; sending kick prompt anyway"
  sleep 2
  return 1
}

launch() {  # launch <window> <role-file> <model> <agent-name>
  local win="$1" role="$2" model="$3" name="$4"
  local pf="$A/.kick-$name.md"
  kick "$role" "$win" > "$pf"
  if [ "$DRY" -eq 1 ]; then echo "[dry-run] $name → window $win, model $model"; return; fi
  tmux new-window -t "$SESSION" -n "$win" -c "$REPO"
  # Step 1: start claude with flags only — no positional prompt. A positional
  # prompt only pre-fills/loads the TUI's compose box on this CLI version, it
  # does not auto-submit; the single C-m below just runs this shell command line.
  tmux send-keys -t "$SESSION:$win" \
    "$CLAUDE_BIN --model $model --permission-mode bypassPermissions --add-dir '$REPO'" C-m
  # Step 2: wait for the TUI to actually be up and accepting input.
  wait_for_tui_ready "$win"
  # Step 3: send the kick prompt as literal keystrokes (-l — not re-parsed by
  # the shell, so quotes/backticks/newlines in the prompt can't break anything),
  # then submit it with its own, separate Enter.
  tmux send-keys -t "$SESSION:$win" -l "$(cat "$pf")"
  tmux send-keys -t "$SESSION:$win" C-m
}

if [ "$DRY" -eq 0 ]; then
  tmux has-session -t "$SESSION" 2>/dev/null && { echo "Session '$SESSION' already exists. Attach with: tmux attach -t $SESSION"; exit 1; }
  tmux new-session -d -s "$SESSION" -n ops -c "$REPO"
  # `watch` isn't installed on this machine (macOS, no Homebrew watch) — use a
  # portable while-loop instead of adding a new dependency.
  tmux send-keys -t "$SESSION:ops" \
    "while true; do clear; date; echo; tail -n 12 $A/state/HEARTBEAT.jsonl; echo; echo PARKED:; tail -n 5 $A/state/PARKED.jsonl; sleep 30; done" C-m
fi

#        window      role          model   agent-name
launch   adhikarin   adhikarin.md  opus    ADHIKARIN
launch   verifier    verifier.md   opus    PARIKSAKA
launch   monitor     monitor.md    sonnet  PRAHARI
launch   scribe      scribe.md     sonnet  LEKHAKA
launch   conductor   conductor.md  opus    SUTRADHARA

if [ "$DRY" -eq 0 ]; then
  tmux select-window -t "$SESSION:conductor"
  echo
  echo "Fleet up. Attach with:  tmux attach -t $SESSION"
  echo "Windows: ops · adhikarin · verifier · monitor · scribe · conductor(active)"
  echo
  echo "IMPORTANT — set reasoning effort to HIGH in each Opus window (adhikarin,"
  echo "verifier, conductor): focus the window and run  /model  then pick effort high."
fi
