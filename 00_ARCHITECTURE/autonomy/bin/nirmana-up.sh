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
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

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

launch() {  # launch <window> <role-file> <model> <agent-name>
  local win="$1" role="$2" model="$3" name="$4"
  local pf="$A/.kick-$name.md"
  kick "$role" "$win" > "$pf"
  if [ "$DRY" -eq 1 ]; then echo "[dry-run] $name → window $win, model $model"; return; fi
  tmux new-window -t "$SESSION" -n "$win" -c "$REPO"
  tmux send-keys -t "$SESSION:$win" \
    "$CLAUDE_BIN --model $model --permission-mode bypassPermissions --add-dir '$REPO' \"\$(cat '$pf')\"" C-m
}

if [ "$DRY" -eq 0 ]; then
  tmux has-session -t "$SESSION" 2>/dev/null && { echo "Session '$SESSION' already exists. Attach with: tmux attach -t $SESSION"; exit 1; }
  tmux new-session -d -s "$SESSION" -n ops -c "$REPO"
  tmux send-keys -t "$SESSION:ops" "watch -n 30 'tail -n 12 $A/state/HEARTBEAT.jsonl; echo; echo PARKED:; tail -n 5 $A/state/PARKED.jsonl'" C-m
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
