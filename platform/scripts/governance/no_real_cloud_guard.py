"""no_real_cloud_guard.py: a test-time barrier so that NO test can launch a real cloud command (gcloud, gsutil, bq, kubectl).

Why: on 2026-10-05 a test of the global-asset dispatch tool ran a REAL `gcloud run jobs execute brahma-build-pipeline-job ... NIRMANA_FORCE_EXECUTE=1`
because the code under test had bound `subprocess.run` at import time and the test patched the name too late. The random run id made it harmless; a
real one would have forced a production build. A patch inside a test cannot be the only barrier.

`install()` patches the process-wide choke points: `subprocess.Popen.__init__` (which run, call, check_call, check_output and every wrapper go through, however
the caller bound them), and `os.system`, `os.popen`, `os.posix_spawn(p)`, `os.exec*`, `os.spawn*` where they exist. A blocked attempt raises AssertionError
(and, when `record_path` or $NO_REAL_CLOUD_RECORD is set, appends one JSON line with the argv first, for audits). Anything else (git, psql against a
local cluster, python, bash, ...) is untouched: this is a narrow barrier for cloud CLIs, not a sandbox. There is deliberately no opt-out marker.

Used by the autouse fixtures in `platform/scripts/governance/__tests__/conftest.py` and `platform/python-sidecar/conftest.py`.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import time

BLOCKED_COMMANDS = frozenset({"gcloud", "gsutil", "bq", "kubectl", "gcloud.cmd", "gcloud.exe"})
_SHELL_RE = re.compile(r"(^|[\s;&|(`$])(" + "|".join(sorted(re.escape(c) for c in BLOCKED_COMMANDS)) + r")(\s|$|;|&|\||\))")


class RealCloudCommandAttempt(AssertionError):
    """A test (or code under test) tried to run a real cloud CLI."""


def _text_and_argv0(args) -> tuple[str, str]:
    if isinstance(args, (bytes, os.PathLike)):
        args = os.fsdecode(args)
    if isinstance(args, str):
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.split()
        return args, os.path.basename(parts[0]) if parts else ""
    items = [os.fsdecode(a) if isinstance(a, (bytes, os.PathLike)) else str(a) for a in args]
    return " ".join(items), os.path.basename(items[0]) if items else ""


def is_blocked(args, shell: bool = False) -> bool:
    """True when `args` (a command string or argv) would run a blocked cloud CLI."""
    try:
        text, argv0 = _text_and_argv0(args)
    except TypeError:
        return False
    if argv0 in BLOCKED_COMMANDS:
        return True
    if argv0 in ("env", "sudo", "nohup", "timeout", "time", "command", "exec") and any(os.path.basename(w) in BLOCKED_COMMANDS for w in text.split()):
        return True
    if shell or isinstance(args, str) or argv0 in ("sh", "bash", "zsh", "dash"):
        return bool(_SHELL_RE.search(text))
    return False


def _record(record_path, args, via):
    if not record_path:
        return
    try:
        with open(record_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "via": via, "args": args if isinstance(args, (str, list, tuple)) else repr(args),
                                "test": os.environ.get("PYTEST_CURRENT_TEST", "")}, default=str) + "\n")
    except OSError:
        pass


def install(record_path: str | None = None):
    """Patch the choke points; returns a no-argument function that restores everything."""
    record_path = record_path or os.environ.get("NO_REAL_CLOUD_RECORD") or None
    saved = []
    orig_init = subprocess.Popen.__init__

    def guarded_init(self, args, *a, **kw):
        if is_blocked(args, bool(kw.get("shell"))):
            _record(record_path, args, "subprocess.Popen")
            raise RealCloudCommandAttempt(f"a test tried to run a real cloud command: {args!r}")
        return orig_init(self, args, *a, **kw)

    subprocess.Popen.__init__ = guarded_init
    saved.append((subprocess.Popen, "__init__", orig_init))
    for mod, name in ((os, "system"), (os, "popen")):
        orig = getattr(mod, name, None)
        if orig is None:
            continue

        def make(orig, name):
            def guarded(cmd, *a, **kw):
                if is_blocked(cmd, True):
                    _record(record_path, cmd, "os." + name)
                    raise RealCloudCommandAttempt(f"a test tried to run a real cloud command via os.{name}: {cmd!r}")
                return orig(cmd, *a, **kw)
            return guarded
        setattr(mod, name, make(orig, name))
        saved.append((mod, name, orig))
    for name in ("execv", "execve", "execvp", "execvpe", "posix_spawn", "posix_spawnp", "spawnv", "spawnve", "spawnvp", "spawnvpe"):
        orig = getattr(os, name, None)
        if orig is None:
            continue

        def make2(orig, name):
            def guarded(path, argv, *a, **kw):
                first = argv[0] if argv else path
                if is_blocked([path] + list(argv or []), False) or os.path.basename(str(first)) in BLOCKED_COMMANDS:
                    _record(record_path, [str(path)] + [str(x) for x in (argv or [])], "os." + name)
                    raise RealCloudCommandAttempt(f"a test tried to run a real cloud command via os.{name}: {path!r} {argv!r}")
                return orig(path, argv, *a, **kw)
            return guarded
        setattr(os, name, make2(orig, name))
        saved.append((os, name, orig))

    def uninstall():
        for owner, attr, original in reversed(saved):
            setattr(owner, attr, original)
    return uninstall
