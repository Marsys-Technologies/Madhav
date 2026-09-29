"""Suvarṇa hold guard — a Claude Code PreToolUse hook enforcing charter §8 (the hold switch) at the
tool-call boundary, for the two execution sessions running unattended (L.15 interim runtime).

    python -m suvarna_tracker.hold_guard        (reads the hook JSON from stdin; never takes flags)

The charter's own words: "``$SUVARNA_HOME/run/SUVARNA_HOLD`` present: finish the items already
running, dispatch nothing new. Production-visible actions stop at the next precondition check."
(§8). This hook is one of those precondition checks, sitting in front of the two tool calls that most
directly start new work or touch production: a new subagent dispatch (the ``Agent`` tool) and a
production-visible or dispatch-like Bash command. Everything else — reading, git commits, tests,
logging, the census — is explicitly NOT blocked: "finish the items already running" means exactly
that, not "stop everything."

Design rules (CLAUDE.md §N.8, mirrored from monitor.py):
- **Never fabricate a block.** Only the two named categories are ever blocked while the hold is on;
  nothing else is second-guessed here.
- **Never wedge the session.** Malformed or unreadable stdin is not a reason to refuse a tool call —
  that would turn a hook bug into an outage. It is logged and the call is allowed through (exit 0).
- **The hold file itself is sacrosanct.** Charter §8: "Only the native removes it." An attempt to
  delete it is refused unconditionally — hold on or off, dispatch-like or not.
- **Every block is an event**, actor ``hold-guard``, before the exit code reaches the harness — an
  action (here, a refusal) that is not logged did not happen (charter §11).
"""
from __future__ import annotations

import json
import os
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "suvarna_tracker"

from suvarna_tracker.events import append  # noqa: E402

DEFAULT_HOME = "/Users/Dev/suvarna"

# Bash substrings marking a command as production-visible or dispatch-like (charter §6, §8; arch
# §6.2's level-wave script, the certification writer, and a PR merge are exactly the "starts new
# work / changes what production serves" acts the hold is for).
DISPATCH_MARKERS = ("suvarna-build", "suvarna_level_wave", "nikasha_certify", "gh pr merge", "orchestrator",
                    "--apply")

# Matches any spelling of "remove the hold switch file": rm/unlink, with or without -f, with the
# path written out, via $SUVARNA_HOME, or via a relative "run/SUVARNA_HOLD". Deliberately loose
# (word-boundary anchored on the command name only) so a quoted or globbed path still trips it.
_HOLD_DELETE_RE = re.compile(r"\b(rm|unlink)\b.*SUVARNA_HOLD")


def home_dir() -> str:
    return os.environ.get("SUVARNA_HOME", DEFAULT_HOME)


def hold_path(home: str | None = None) -> str:
    return os.path.join(home or home_dir(), "run", "SUVARNA_HOLD")


def hold_present(home: str | None = None) -> bool:
    return os.path.exists(hold_path(home))


def events_path(home: str | None = None) -> str:
    return os.environ.get("SUVARNA_EVENTS", os.path.join(home or home_dir(), "run", "EVENTS.jsonl"))


def targets_hold_delete(command: str) -> bool:
    """True if a Bash command tries to remove the hold switch file, by any spelling."""
    return bool(_HOLD_DELETE_RE.search(command or ""))


def is_dispatch_like(command: str) -> bool:
    return any(marker in (command or "") for marker in DISPATCH_MARKERS)


def matched_dispatch_marker(command: str) -> str | None:
    return next((m for m in DISPATCH_MARKERS if m in (command or "")), None)


def evaluate(tool_name: str, tool_input: dict | None, home: str | None = None) -> tuple[bool, str]:
    """Pure function of one tool call plus the hold file's presence: (blocked, reason). Fully
    testable without ever going through stdin or a real hook invocation."""
    command = ""
    if tool_name == "Bash":
        command = str((tool_input or {}).get("command") or "")

    # Always refused, hold or not: only the native removes the hold switch (charter §8).
    if tool_name == "Bash" and targets_hold_delete(command):
        return True, ("the hold switch file may only be removed by the native (charter §8); "
                       "refused unconditionally, hold on or off")

    if not hold_present(home):
        return False, ""

    # New dispatches: the Agent tool starts a fresh subagent (charter §8: "dispatch nothing new").
    if tool_name == "Agent":
        return True, "hold is set: no new dispatch (charter §8) — Agent tool call refused"

    # Production-visible or dispatch-like Bash: the level-wave script, a build, a certification
    # write, an orchestrator run, or an explicit --apply. Everything else in Bash (git, tests,
    # reads, the census, emit/decide) is explicitly allowed through: "finish what is running."
    if tool_name == "Bash" and is_dispatch_like(command):
        marker = matched_dispatch_marker(command) or "?"
        return True, (f"hold is set: production-visible/dispatch-like Bash command refused "
                       f"(matched {marker!r}; charter §6, §8)")

    return False, ""


def _emit_note(detail: str, home: str | None = None) -> None:
    """Never let a logging failure crash the hook — a note that cannot be written is a governance
    gap to notice later (the dashboard's malformed-line counter, events.py), not a reason to fail
    open OR closed on the tool call itself."""
    try:
        append(events_path(home), {"kind": "note", "actor": "hold-guard", "detail": detail})
    except Exception:  # noqa: BLE001
        pass


def main(argv: list[str] | None = None) -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            raise ValueError("hook payload is not a JSON object")
    except (ValueError, TypeError) as exc:
        # Malformed stdin never wedges the session: allow the call through, but make the gap
        # visible rather than silent.
        _emit_note(f"malformed hook stdin, allowing the tool call through: {type(exc).__name__}: {exc}")
        return 0

    tool_name = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    blocked, reason = evaluate(tool_name, tool_input)
    if blocked:
        _emit_note(f"BLOCKED {tool_name or '?'}: {reason}")
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
