#!/bin/bash
# Suvarṇa hold-guard wrapper (S14, review pass 3).
#
# The PreToolUse hook used to invoke `python3 -m suvarna_tracker.hold_guard` directly. If the
# module cannot even be imported — e.g. PYTHONPATH points at a worktree the swarm user cannot read
# under N-25 — the hook exits with whatever the interpreter's own uncaught-exception code is
# (typically 1, never 0 or 2), and a Claude Code PreToolUse hook that exits anything other than 2 is
# treated as "no objection": the guard's whole purpose (finish what's running, dispatch nothing new
# while the hold is on) silently stops applying. Review pass 3 finding S14.
#
# This wrapper runs the real guard first. If it exits 0 (allow) or 2 (blocked — a real decision from
# the guard itself), that exit code is passed straight through, unchanged. Only when the guard could
# not even run does this wrapper make its own call — and it fails CLOSED (exit 2) for exactly the
# two tool-call categories the guard exists to protect (a new Agent dispatch, or a dispatch-like Bash
# command), exit 0 for everything else. The classification below deliberately does not import
# suvarna_tracker (a broken PYTHONPATH must not break this fallback too) — it re-reads the same hook
# JSON with a bare `python3 -c` and a small, self-contained mirror of hold_guard.py's own
# DISPATCH_MARKERS list.
set -u

payload="$(cat)"

guard_out="$(printf '%s' "$payload" | python3 -m suvarna_tracker.hold_guard 2>&1)"
guard_rc=$?

if [ "$guard_rc" -eq 0 ] || [ "$guard_rc" -eq 2 ]; then
  if [ -n "$guard_out" ]; then
    printf '%s\n' "$guard_out" >&2
  fi
  exit "$guard_rc"
fi

# The real guard failed to load or run at all (import error, missing interpreter, etc.) — never
# treat that as "no problem". Classify the tool call independently, with no dependency on
# suvarna_tracker or PYTHONPATH.
classification="$(printf '%s' "$payload" | python3 -c '
import json, re, sys

# F4 (independent review): mirrors hold_guard.py'"'"'s own DISPATCH_MARKERS and hold-delete
# detection — a broken PYTHONPATH must not narrow this fallback classifier'"'"'s coverage versus
# the real guard it stands in for.
DISPATCH_MARKERS = ("suvarna-build", "suvarna_level_wave", "nikasha_certify", "gh pr merge",
                    "orchestrator", "--apply", "lane_launch", "claude -p", "codex exec", "kimi -p",
                    "python -m suvarna_tracker.lane_launch")
HOLD_DELETE_VERB_RE = re.compile(r"\b(rm|mv|unlink|truncate)\b")

try:
    d = json.load(sys.stdin)
    if not isinstance(d, dict):
        d = {}
except Exception:
    d = {}

tool_name = d.get("tool_name") or ""
tool_input = d.get("tool_input")
command = ""
if tool_name == "Bash" and isinstance(tool_input, dict):
    c = tool_input.get("command")
    command = c if isinstance(c, str) else ""

if command and "SUVARNA_HOLD" in command and (HOLD_DELETE_VERB_RE.search(command) or ">" in command):
    print("hold_delete")
elif tool_name == "Agent" or any(m in command for m in DISPATCH_MARKERS):
    print("dispatch")
else:
    print("other")
' 2>/dev/null)"

if [ "$classification" = "hold_delete" ]; then
  echo "hold-guard: the real guard failed to load or run (exit $guard_rc); the hold switch file may only be removed by the native (charter §8) — refused unconditionally (F4)" >&2
  exit 2
fi

if [ "$classification" = "dispatch" ]; then
  echo "hold-guard: the real guard failed to load or run (exit $guard_rc); failing closed for a dispatch-like tool call (S14)" >&2
  exit 2
fi

echo "hold-guard: the real guard failed to load or run (exit $guard_rc); allowing a non-dispatch-like tool call through (S14)" >&2
exit 0
