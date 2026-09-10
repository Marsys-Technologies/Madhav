#!/usr/bin/env bash
# =============================================================================
# overnight_p3p4.sh — launch the Paripraśna P3+P4 combined overnight autonomous
# run inside tmux, per PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md §11.
#
# Usage:   bash overnight_p3p4.sh            # launch
#          bash overnight_p3p4.sh status     # one-shot health readout
#          bash overnight_p3p4.sh stop       # graceful stop (asks conductor to halt clean)
#
# Run this FROM the directory containing the charter + boot prompt files
# (recommended: ~/pariprashna_night — NOT inside the repo, per X-4).
# =============================================================================
set -euo pipefail

# ----------------------------- configuration ---------------------------------
SESSION="prp-night"
REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHARTER="$KIT_DIR/PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md"
BOOT_PROMPT="$KIT_DIR/CONDUCTOR_BOOT_PROMPT.md"
LOG_DIR="$KIT_DIR/logs"
CONDUCTOR_MODEL="opus"        # conductor runs Opus-class; charter assigns per-role models
PROD_URL="${PROD_URL:-}"      # OPTIONAL: set to the amjis-web Cloud Run URL for pulse probes
NUDGE_INTERVAL=300            # sentinel capture cadence, seconds
NUDGE_AFTER=3                 # identical captures before a nudge (3 x 300s = 15 min still)
PULSE_INTERVAL=1800           # pulse cadence, seconds

mkdir -p "$LOG_DIR"

# ------------------------------- subcommands ---------------------------------
if [[ "${1:-}" == "status" ]]; then
  tmux has-session -t "$SESSION" 2>/dev/null || { echo "No $SESSION session running."; exit 1; }
  echo "--- windows ---"; tmux list-windows -t "$SESSION"
  echo "--- last pulse ---"; tail -n 12 "$LOG_DIR/pulse.log" 2>/dev/null || echo "(no pulse yet)"
  echo "--- conductor tail ---"; tmux capture-pane -p -t "$SESSION:conductor" | tail -n 15
  exit 0
fi
if [[ "${1:-}" == "stop" ]]; then
  tmux send-keys -t "$SESSION:conductor" \
    "NATIVE DIRECTIVE: stop the run now via the charter's clean-halt path (§7) — park in-flight lanes, pin rollback, write resume state, finalize the morning report, release leases. Do not start new lanes." Enter
  echo "Clean-halt directive sent. Watch: tmux attach -t $SESSION"
  exit 0
fi

# ------------------------------ pre-flight -----------------------------------
fail=0
for c in tmux claude git gh; do
  command -v "$c" >/dev/null || { echo "MISSING: $c"; fail=1; }
done
[[ -d "$REPO/.git" ]] || { echo "MISSING: repo at $REPO"; fail=1; }
[[ -f "$CHARTER" ]] || { echo "MISSING: charter at $CHARTER"; fail=1; }
[[ -f "$BOOT_PROMPT" ]] || { echo "MISSING: boot prompt at $BOOT_PROMPT"; fail=1; }
gh auth status >/dev/null 2>&1 || { echo "MISSING: gh auth (run: gh auth login)"; fail=1; }
git -C "$REPO" --no-optional-locks fetch origin --quiet \
  || { echo "FAILED: git fetch origin from $REPO"; fail=1; }
case "$KIT_DIR/" in "$REPO"/*) echo "REFUSING: kit dir is inside the repo (X-4). Move it out (e.g. ~/pariprashna_night)."; fail=1;; esac
[[ $fail -eq 0 ]] || { echo "Pre-flight failed — fix the above and relaunch."; exit 1; }
tmux has-session -t "$SESSION" 2>/dev/null && { echo "$SESSION already exists. Attach: tmux attach -t $SESSION"; exit 1; }

# --------------------------- helper scripts ----------------------------------
cat > "$KIT_DIR/sentinel.sh" <<SENTINEL
#!/usr/bin/env bash
# Anti-idle sentinel (charter §11.2). Restores motion; never decides.
SESSION="$SESSION"; PANE="\$SESSION:conductor"; LOG="$LOG_DIR/sentinel.log"
KIT_DIR="$KIT_DIR"; BOOT_PROMPT="$BOOT_PROMPT"; MODEL="$CONDUCTOR_MODEL"
still=0; last=""; n=0
while true; do
  sleep $NUDGE_INTERVAL
  if ! tmux list-panes -t "\$PANE" -F '#{pane_dead}' >/dev/null 2>&1; then
    echo "\$(date -u +%FT%TZ) session gone; sentinel exiting" >> "\$LOG"; exit 0
  fi
  dead=\$(tmux list-panes -t "\$PANE" -F '#{pane_dead}' | head -1)
  if [[ "\$dead" == "1" ]]; then
    n=\$((n+1))
    echo "\$(date -u +%FT%TZ) conductor pane dead — respawning with --continue (resume #\$n)" >> "\$LOG"
    tmux respawn-pane -k -t "\$PANE" \
      "cd '$REPO' && caffeinate -dims claude --model \$MODEL --dangerously-skip-permissions --continue 2>&1 | tee -a '$LOG_DIR/conductor.log'"
    sleep 30
    tmux send-keys -t "\$PANE" "CRASH-RESUME #\$n: you are the CONDUCTOR resuming mid-run. Per charter §11.3, re-orient from derived state (fetch, lease tail, tracker, budget vs actual spend, prod revision), then resume the queue. Charter: \$KIT_DIR/PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md" Enter
    still=0; last=""; continue
  fi
  cur=\$(tmux capture-pane -p -t "\$PANE" | tail -40 | md5 2>/dev/null || tmux capture-pane -p -t "\$PANE" | tail -40 | md5sum)
  if [[ "\$cur" == "\$last" ]]; then still=\$((still+1)); else still=0; fi
  last="\$cur"
  if [[ \$still -ge $NUDGE_AFTER ]]; then
    n=\$((n+1))
    echo "\$(date -u +%FT%TZ) still for \$still cycles — nudge #\$n" >> "\$LOG"
    tmux send-keys -t "\$PANE" "WATCHDOG NUDGE #\$n — report end-state ranking, queue depth, smoke-counter state, budget subtotals; then resume the queue. If blocked, route the blocker to the NATIVE-SURROGATE now (charter §11.2)." Enter
    still=0
  fi
done
SENTINEL

cat > "$KIT_DIR/pulse.sh" <<PULSE
#!/usr/bin/env bash
# Agent-free external health record (charter §11.4). No agent writes here.
LOG="$LOG_DIR/pulse.log"; REPO="$REPO"; PROD_URL="$PROD_URL"
while true; do
  {
    echo "=== \$(date -u +%FT%TZ) ==="
    git -C "\$REPO" --no-optional-locks fetch origin --quiet 2>/dev/null \
      && echo "origin/main: \$(git -C "\$REPO" --no-optional-locks rev-parse --short origin/main)" \
      || echo "origin/main: FETCH FAILED"
    gh run list --repo "\$(git -C "\$REPO" config --get remote.origin.url | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git\$##')" -L 5 \
      --json name,status,conclusion,createdAt \
      --template '{{range .}}{{.name}} {{.status}} {{.conclusion}} {{.createdAt}}{{"\n"}}{{end}}' 2>/dev/null \
      || echo "gh runs: UNAVAILABLE"
    if [[ -n "\$PROD_URL" ]]; then
      echo "prod: HTTP \$(curl -s -o /dev/null -m 20 -w '%{http_code}' "\$PROD_URL" || echo FAIL)"
    fi
    echo "disk: \$(df -h / | awk 'NR==2{print \$4" free"}')"
    echo ""
  } >> "\$LOG"
  sleep $PULSE_INTERVAL
done
PULSE
chmod +x "$KIT_DIR/sentinel.sh" "$KIT_DIR/pulse.sh"

# ------------------------------- launch --------------------------------------
printf '%s' "You are the CONDUCTOR. Read $CHARTER in full and execute it. Boot orientation: $BOOT_PROMPT. Begin with the charter's run-open sequence, then open Wave P3-1 plus the P4 filler lanes simultaneously. The native is asleep; the NATIVE-SURROGATE answers everything." > "$KIT_DIR/boot_line.txt"

tmux new-session -d -s "$SESSION" -n conductor -c "$REPO"
tmux new-window  -t "$SESSION" -n sentinel -c "$KIT_DIR"
tmux new-window  -t "$SESSION" -n pulse    -c "$KIT_DIR"
tmux new-window  -t "$SESSION" -n logs     -c "$KIT_DIR"

# conductor: caffeinate keeps the Mac (and this process tree) awake all night
tmux send-keys -t "$SESSION:conductor" \
  "caffeinate -dims claude --model $CONDUCTOR_MODEL --dangerously-skip-permissions \"\$(cat '$KIT_DIR/boot_line.txt')\" 2>&1 | tee -a '$LOG_DIR/conductor.log'" Enter

tmux send-keys -t "$SESSION:sentinel" "bash '$KIT_DIR/sentinel.sh'" Enter
tmux send-keys -t "$SESSION:pulse"    "bash '$KIT_DIR/pulse.sh'" Enter
tmux send-keys -t "$SESSION:logs" \
  "touch '$LOG_DIR/sentinel.log'; tail -F '$LOG_DIR/sentinel.log' '$LOG_DIR/pulse.log' 2>/dev/null" Enter

echo "Launched. Attach:  tmux attach -t $SESSION    (detach: Ctrl-b d)"
echo "Health:            bash $0 status"
echo "Graceful stop:     bash $0 stop"
