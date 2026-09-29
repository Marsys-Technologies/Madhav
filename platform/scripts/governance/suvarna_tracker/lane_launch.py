"""Suvarṇa lane launcher (CODE-18, S18) — starts one lane's Claude Code session, detached, under
the campaign's own settings file.

    python3 -m suvarna_tracker.lane_launch --qid <qid> --role <role> --model <model> --effort <effort> \\
        [--prompt-file <path>] [--home DIR]

Refuses (before any process is launched, before anything is emitted) if:
- the hold switch (``$SUVARNA_HOME/run/SUVARNA_HOLD``) is set — charter §8: "dispatch nothing new";
- the lane's worktree (``$SUVARNA_HOME/lanes/<qid>``) does not exist yet — nothing to launch into;
- there is no prompt to launch with: ``--prompt-file``, if given, must exist and be readable; if
  omitted, this looks for the lane's own ``PROMPT.md`` and refuses if that is not there either.

On success, launches::

    claude -p <prompt text> --settings $SUVARNA_HOME/config/claude-settings.json \\
        --permission-mode dontAsk --model <model>

detached (own session, stdio redirected, never waited on), with ``cwd`` the lane worktree, stdout
and stderr appended to ``evidence/<qid>/agent.log``, and its pid recorded at
``run/lanes/<qid>.pid``. **Never** passes ``--dangerously-skip-permissions`` or any
``bypassPermissions`` mode — ``--permission-mode dontAsk`` plus the settings file's own
``defaultMode`` (also ``dontAsk``, never ``bypassPermissions`` — see ``runtime/settings.template.json``)
are the only permission controls this launcher ever uses. ``--effort`` is never passed to ``claude``
itself (it has no such flag); it is recorded only in the emitted event, for the Conductor/Monitor's
own bookkeeping (arch §3.1's model·effort table).

On a successful launch this emits one ``kind: item, state: running`` event for the queue id (so the
tracker shows the lane as running the moment it starts) via ``events.append`` — the same log every
other role writes through.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "suvarna_tracker"

from suvarna_tracker.events import append  # noqa: E402
from suvarna_tracker.hold_guard import hold_present  # noqa: E402

DEFAULT_HOME = "/Users/Dev/suvarna"
DEFAULT_PROMPT_BASENAME = "PROMPT.md"


class LaunchRefused(ValueError):
    pass


def home_dir() -> str:
    return os.environ.get("SUVARNA_HOME", DEFAULT_HOME)


def lane_dir(home: str, qid: str) -> str:
    return os.path.join(home, "lanes", qid)


def evidence_log_path(home: str, qid: str) -> str:
    return os.path.join(home, "evidence", qid, "agent.log")


def pid_path(home: str, qid: str) -> str:
    return os.path.join(home, "run", "lanes", f"{qid}.pid")


def claude_settings_path(home: str) -> str:
    return os.path.join(home, "config", "claude-settings.json")


def resolve_prompt(home: str, qid: str, prompt_file: str | None) -> str:
    """The prompt text to launch with. `--prompt-file`, if given, must exist; otherwise the lane's
    own `PROMPT.md` is used. Raises `LaunchRefused` (never a bare `OSError`) if neither is readable —
    a lane with nothing to say is not a lane to launch."""
    path = prompt_file or os.path.join(lane_dir(home, qid), DEFAULT_PROMPT_BASENAME)
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        raise LaunchRefused(f"no readable prompt at {path}: {exc}") from exc
    if not text.strip():
        raise LaunchRefused(f"prompt file {path} is empty")
    return text


def check_refusal(home: str, qid: str) -> str | None:
    """Pure precondition check (no side effects): the reason this launch must be refused, or `None`
    to proceed. Checked before the prompt is even read, so the cheapest, most decisive refusals
    (hold, missing lane) never touch the filesystem beyond `os.path.exists`."""
    if hold_present(home):
        return "hold is set (charter §8): dispatch nothing new — refusing to launch a lane"
    if not os.path.isdir(lane_dir(home, qid)):
        return f"lane worktree does not exist yet: {lane_dir(home, qid)}"
    return None


def build_argv(prompt: str, model: str, settings_path: str) -> list[str]:
    """The exact `claude` invocation — never `--dangerously-skip-permissions`, never a
    `bypassPermissions` mode; `--permission-mode dontAsk` plus the settings file's own `defaultMode`
    are the only permission controls a launched lane ever gets."""
    return ["claude", "-p", prompt, "--settings", settings_path, "--permission-mode", "dontAsk",
            "--model", model]


def launch(home: str, qid: str, role: str, model: str, effort: str, prompt_file: str | None = None,
          launch_fn=None) -> dict:
    """Check preconditions, read the prompt, start the lane's `claude` session detached, record its
    pid, and emit a `running` event. Raises `LaunchRefused` for every precondition failure — never
    launches a partial or silently-skipped process. `launch_fn` (real default: a detached
    `subprocess.Popen`) is injectable so tests never spawn a real `claude` process."""
    reason = check_refusal(home, qid)
    if reason:
        raise LaunchRefused(reason)
    prompt = resolve_prompt(home, qid, prompt_file)

    lane = lane_dir(home, qid)
    log_path = evidence_log_path(home, qid)
    pid_file = pid_path(home, qid)
    settings_path = claude_settings_path(home)
    argv = build_argv(prompt, model, settings_path)

    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    os.makedirs(os.path.dirname(pid_file), exist_ok=True)

    if launch_fn is None:
        launch_fn = _default_launch
    pid = launch_fn(argv, cwd=lane, log_path=log_path)

    tmp = f"{pid_file}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(str(pid))
    os.replace(tmp, pid_file)

    events_path = os.environ.get("SUVARNA_EVENTS", os.path.join(home, "run", "EVENTS.jsonl"))
    append(events_path, {"kind": "item", "actor": role, "item": qid, "state": "running",
                         "detail": f"lane launched: role={role} model={model} effort={effort}"})

    return {"qid": qid, "pid": pid, "argv": argv, "log_path": log_path, "pid_path": pid_file}


def _default_launch(argv: list[str], cwd: str, log_path: str) -> int:
    """Start a detached `claude` process; never waits on it. Returns its pid."""
    log_fh = open(log_path, "ab")
    try:
        p = subprocess.Popen(argv, cwd=cwd, stdout=log_fh, stderr=log_fh, stdin=subprocess.DEVNULL,
                             start_new_session=True, close_fds=True)
        return p.pid
    finally:
        log_fh.close()


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Launch one Suvarṇa lane's Claude Code session, detached")
    ap.add_argument("--qid", required=True, help="the queue id (also the lane worktree's directory name)")
    ap.add_argument("--role", required=True, help="the role this lane runs as (for the emitted event)")
    ap.add_argument("--model", required=True)
    ap.add_argument("--effort", required=True, help="recorded in the emitted event only; never passed to claude")
    ap.add_argument("--prompt-file", default=None, metavar="PATH",
                    help="the prompt text to launch with (default: <lane>/PROMPT.md)")
    ap.add_argument("--home", default=None, help="override $SUVARNA_HOME")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_arg_parser().parse_args(argv)
    home = a.home or home_dir()
    try:
        result = launch(home, a.qid, a.role, a.model, a.effort, prompt_file=a.prompt_file)
    except LaunchRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"launched {result['qid']}: pid {result['pid']}, log {result['log_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
