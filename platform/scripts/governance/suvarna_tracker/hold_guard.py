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
# work / changes what production serves" acts the hold is for). F4 (independent review) extends
# this list with every lane/agent launch surface named in the review: the lane launcher (by module
# name and by its own CODE-18 CLI entry point) and every CLI this campaign uses to start an agent
# session unattended.
DISPATCH_MARKERS = ("suvarna-build", "suvarna_level_wave", "nikasha_certify", "gh pr merge", "orchestrator",
                    "--apply", "lane_launch", "claude -p", "codex exec", "kimi -p",
                    "python -m suvarna_tracker.lane_launch")

# F4 (independent review): "remove the hold switch file" is never only rm/unlink — mv (rename it
# away), truncate, or any shell redirect ('>') can just as effectively destroy or empty it. Matched
# as "the hold path appears anywhere in the command, together with one of these verbs or a redirect
# anywhere in the command" — deliberately broad (never ordered, never anchored to a specific
# argument position) so a quoted/globbed path, a variable indirection, or a command reordering
# still trips it. The hold file is sacrosanct (charter §8: "only the native removes it"); a false
# positive here just means rephrasing an unrelated command to avoid mentioning the hold path next
# to a redirect, which is a small price for never under-refusing a real deletion/truncation attempt.
_HOLD_DELETE_VERB_RE = re.compile(r"\b(rm|mv|unlink|truncate)\b")


def targets_hold_delete(command: str) -> bool:
    """True if a Bash command tries to remove, rename away, truncate, or otherwise clear/replace
    the hold switch file, by any spelling."""
    command = command or ""
    if "SUVARNA_HOLD" not in command:
        return False
    return bool(_HOLD_DELETE_VERB_RE.search(command)) or ">" in command


def home_dir() -> str:
    return os.environ.get("SUVARNA_HOME", DEFAULT_HOME)


def hold_path(home: str | None = None) -> str:
    return os.path.join(home or home_dir(), "run", "SUVARNA_HOLD")


def hold_present(home: str | None = None) -> bool:
    return os.path.exists(hold_path(home))


def events_path(home: str | None = None) -> str:
    return os.environ.get("SUVARNA_EVENTS", os.path.join(home or home_dir(), "run", "EVENTS.jsonl"))


def is_dispatch_like(command: str) -> bool:
    return any(marker in (command or "") for marker in DISPATCH_MARKERS)


def matched_dispatch_marker(command: str) -> str | None:
    return next((m for m in DISPATCH_MARKERS if m in (command or "")), None)


def classify_command(tool_input: dict | None) -> tuple[str, bool]:
    """F4 (independent review): the command text to check, and whether `tool_input` actually
    provided a usable string at all ("classifiable"). A missing/non-dict `tool_input`, or a
    missing/non-string `command`, is never silently treated as "empty command, therefore not
    dispatch-like" — that is exactly the "cannot classify" case `evaluate()` must fail closed on
    while the hold is set. An explicit empty string IS classifiable (and is, correctly, not
    dispatch-like) — it is the *absence* of a command that cannot be classified, not a short one."""
    if not isinstance(tool_input, dict):
        return "", False
    cmd = tool_input.get("command")
    if not isinstance(cmd, str):
        return "", False
    return cmd, True


def evaluate(tool_name: str, tool_input: dict | None, home: str | None = None) -> tuple[bool, str]:
    """Pure function of one tool call plus the hold file's presence: (blocked, reason). Fully
    testable without ever going through stdin or a real hook invocation.

    F4: a Bash call whose command could not be classified at all (missing/malformed `tool_input`)
    is refused while the hold is set ("cannot classify → refuse" — never assumed "not dispatch-like"
    under uncertainty) and allowed through while the hold is off (a broken/incomplete payload must
    never wedge non-dispatch work when there is nothing for the hold to enforce)."""
    command, classifiable = ("", True)
    if tool_name == "Bash":
        command, classifiable = classify_command(tool_input)

    # Always refused, hold or not: only the native removes the hold switch (charter §8). Checked
    # before the classifiability gate below — a command we CAN read is checked for this
    # unconditionally, regardless of what else about the call might be uncertain.
    if tool_name == "Bash" and classifiable and targets_hold_delete(command):
        return True, ("the hold switch file may only be removed by the native (charter §8); "
                       "refused unconditionally, hold on or off")

    hold_on = hold_present(home)

    if tool_name == "Bash" and not classifiable:
        if hold_on:
            return True, ("hold is set: this Bash call's command could not be classified (missing "
                          "or malformed tool_input) — refusing under uncertainty, never assumed "
                          "safe (charter §8; F4)")
        return False, ""

    if not hold_on:
        return False, ""

    # New dispatches: the Agent tool starts a fresh subagent (charter §8: "dispatch nothing new").
    if tool_name == "Agent":
        return True, "hold is set: no new dispatch (charter §8) — Agent tool call refused"

    # Production-visible or dispatch-like Bash: the level-wave script, a build, a certification
    # write, an orchestrator run, a lane launch, or an explicit --apply. Everything else in Bash
    # (git, tests, reads, the census, emit/decide) is explicitly allowed through: "finish what is
    # running."
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


def _handle_unclassifiable(detail: str) -> int:
    """F4: the hook's own stdin (or the tool_name inside it) could not be parsed/classified at all
    — we cannot rule out that this was an Agent dispatch or a dispatch-like Bash call hiding behind
    a malformed payload. Fail closed (exit 2) while the hold is set; otherwise allow the call
    through (exit 0) — a broken hook must never wedge non-dispatch work, but must never release an
    unclassifiable call under uncertainty while there is a hold to enforce."""
    if hold_present():
        _emit_note(f"BLOCKED (cannot classify while hold is set): {detail}")
        print(f"hold is set and this tool call could not be classified from its hook payload; "
              f"refusing under uncertainty (charter §8; F4): {detail}", file=sys.stderr)
        return 2
    _emit_note(f"{detail}, allowing the tool call through (hold is off)")
    return 0


def main(argv: list[str] | None = None) -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            raise ValueError("hook payload is not a JSON object")
    except (ValueError, TypeError) as exc:
        return _handle_unclassifiable(f"malformed hook stdin: {type(exc).__name__}: {exc}")

    tool_name = payload.get("tool_name")
    if not isinstance(tool_name, str) or not tool_name:
        return _handle_unclassifiable("hook stdin parsed but named no tool_name")

    tool_input = payload.get("tool_input")
    blocked, reason = evaluate(tool_name, tool_input)
    if blocked:
        _emit_note(f"BLOCKED {tool_name or '?'}: {reason}")
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
