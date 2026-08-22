#!/bin/bash
# Live view of the PARIṢKĀRA conductor: follows the newest attempt log and
# renders narration + tool calls + results from the stream-json output.
LOG_DIR="/Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/parishkara-conductor-logs"
f=$(ls -t "$LOG_DIR"/attempt_*.log 2>/dev/null | head -1)
[ -z "$f" ] && { echo "no attempt log yet — is the supervisor running? ($LOG_DIR)"; exit 1; }
echo "── watching: $f  (Ctrl-C to stop; re-run to attach to a newer attempt) ──"
tail -n 200 -f "$f" | python3 -u /Users/Dev/shad_overnight/watch_parishkara.py
