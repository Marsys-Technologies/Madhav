#!/usr/bin/env bash
# Anti-idle sentinel (charter §11.2). Restores motion; never decides.
SESSION="prp-night"; PANE="$SESSION:conductor"; LOG="/Users/Dev/pariprashna_night/logs/sentinel.log"
KIT_DIR="/Users/Dev/pariprashna_night"; BOOT_PROMPT="/Users/Dev/pariprashna_night/CONDUCTOR_BOOT_PROMPT.md"; MODEL="opus"
still=0; last=""; n=0
while true; do
  sleep 300
  if ! tmux list-panes -t "$PANE" -F '#{pane_dead}' >/dev/null 2>&1; then
    echo "$(date -u +%FT%TZ) session gone; sentinel exiting" >> "$LOG"; exit 0
  fi
  dead=$(tmux list-panes -t "$PANE" -F '#{pane_dead}' | head -1)
  if [[ "$dead" == "1" ]]; then
    n=$((n+1))
    echo "$(date -u +%FT%TZ) conductor pane dead — respawning with --continue (resume #$n)" >> "$LOG"
    tmux respawn-pane -k -t "$PANE"       "cd '/Users/Dev/Vibe-Coding/Apps/Madhav' && caffeinate -dims claude --model $MODEL --dangerously-skip-permissions --continue 2>&1 | tee -a '/Users/Dev/pariprashna_night/logs/conductor.log'"
    sleep 30
    tmux send-keys -t "$PANE" "CRASH-RESUME #$n: you are the CONDUCTOR resuming mid-run. Per charter §11.3, re-orient from derived state (fetch, lease tail, tracker, budget vs actual spend, prod revision), then resume the queue. Charter: $KIT_DIR/PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md" Enter
    still=0; last=""; continue
  fi
  cur=$(tmux capture-pane -p -t "$PANE" | tail -40 | md5 2>/dev/null || tmux capture-pane -p -t "$PANE" | tail -40 | md5sum)
  if [[ "$cur" == "$last" ]]; then still=$((still+1)); else still=0; fi
  last="$cur"
  if [[ $still -ge 3 ]]; then
    n=$((n+1))
    echo "$(date -u +%FT%TZ) still for $still cycles — nudge #$n" >> "$LOG"
    tmux send-keys -t "$PANE" "WATCHDOG NUDGE #$n — report end-state ranking, queue depth, smoke-counter state, budget subtotals; then resume the queue. If blocked, route the blocker to the NATIVE-SURROGATE now (charter §11.2)." Enter
    still=0
  fi
done
