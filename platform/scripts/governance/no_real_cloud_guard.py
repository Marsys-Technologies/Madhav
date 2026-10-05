"""no_real_cloud_guard.py: a test-time barrier so that NO test can launch a real cloud command (gcloud, gsutil, bq, kubectl) or a write-capable `gh` call.

Why: on 2026-10-05 a test of the global-asset dispatch tool ran a REAL `gcloud run jobs execute brahma-build-pipeline-job ... NIRMANA_FORCE_EXECUTE=1`
because the code under test had bound `subprocess.run` at import time and the test patched the name too late. The random run id made it harmless; a
real one would have forced a production build. A patch inside a test cannot be the only barrier. Three layers here:

1. In-process choke points. `install()` patches `subprocess.Popen.__init__` (which run, call, check_call, check_output and every wrapper go through, however the
   caller bound them; the `executable=` argument is checked too), `os.system`, `os.popen`, `os.posix_spawn(p)`, every `os.exec*` and every `os.spawn*` (each family
   with its own real signature). A command is judged by its COMMAND POSITIONS: the argv, or the segments of a shell string (`;`, `&&`, `||`, `|`, `(`, backquote,
   `$(`, newline), looking through env assignments, wrappers (`env`, `sudo`, `nohup`, `timeout`, `time`, `nice`, `xargs`, ...) and `sh -c "..."` strings. `echo gcloud`,
   `grep gcloud`, `command -v gcloud` and `git log --grep gcloud` are NOT commands and pass.
2. Child processes. While installed, a directory of stub `gcloud`/`gsutil`/`bq`/`kubectl` scripts that exit 97 is put FIRST on PATH and `CLOUDSDK_CONFIG` points at an empty
   directory, so a Python or shell child that the in-process patch cannot see still cannot reach a real cloud (`python -c` that spawns gcloud, `docker`-less nesting, ...).
3. A blocked attempt raises `RealCloudCommandAttempt`, a BaseException (a broad `except Exception` in the code under test cannot swallow it), and is also counted in
   `ATTEMPTS`; the function-scoped autouse fixture in the conftests fails the test if the count grew, so even a swallowed attempt fails the test. A test that PROVES the
   guard blocks uses the `acknowledge_attempts` fixture / `acknowledge()` to say how many attempts it expects.

Anything else (git, psql against a local cluster, python, bash, ...) is untouched: this is a narrow barrier, not a sandbox. There is deliberately no opt-out marker.
`gh` is blocked only for WRITE patterns (workflow run, pr merge/create/close, api with a write method or a body, ...); read calls pass.

Used by the autouse fixtures in `platform/scripts/governance/__tests__/conftest.py`, `platform/conftest.py`, `platform/python-sidecar/conftest.py` and the Suvarna
executor test tree (`00_ARCHITECTURE/briefs/suvarna/exec/conftest.py`).
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time

BLOCKED_COMMANDS = frozenset({"gcloud", "gsutil", "bq", "kubectl", "gcloud.cmd", "gcloud.exe"})
_WRAPPERS = frozenset({"env", "sudo", "nohup", "timeout", "time", "command", "exec", "nice", "xargs", "stdbuf", "ionice", "setsid", "caffeinate", "builtin"})
_SHELLS = frozenset({"sh", "bash", "zsh", "dash", "ksh"})
_SEPARATORS = frozenset({";", "&&", "||", "|", "&", "(", ")", "|&", "{", "}", "!", "then", "do", "else", "elif", "if", "while", "until"})
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_DURATION = re.compile(r"^\d+(\.\d+)?[smhd]?$")

# `gh` verbs that change remote state (a workflow run, a merge, a PR, a release, ...). Reads (view, list, status, api GET) pass.
_GH_WRITE = {
    "pr": {"merge", "create", "close", "comment", "review", "edit", "ready", "reopen", "update-branch", "lock", "unlock"},
    "issue": {"create", "edit", "close", "comment", "delete", "reopen", "transfer", "lock", "unlock", "pin", "unpin"},
    "release": {"create", "delete", "edit", "upload", "delete-asset"},
    "workflow": {"run", "enable", "disable"},
    "run": {"rerun", "cancel", "delete"},
    "repo": {"create", "delete", "edit", "rename", "archive", "unarchive", "fork", "sync"},
    "secret": {"set", "delete", "remove"},
    "variable": {"set", "delete", "remove"},
    "label": {"create", "edit", "delete"},
    "cache": {"delete"},
}
_GH_WRITE_FLAGS = {"-f", "-F", "--field", "--raw-field", "--input"}


class RealCloudCommandAttempt(BaseException):
    """A test (or code under test) tried to run a real cloud CLI. A BaseException on purpose: `except Exception` cannot swallow it."""


ATTEMPTS: list[dict] = []


def attempt_count() -> int:
    return len(ATTEMPTS)


def acknowledge(n: int | None = None) -> None:
    """A guard test says the recorded attempts were expected (drops the last n, or all)."""
    if n:
        del ATTEMPTS[-n:]
    else:
        ATTEMPTS.clear()


def _fs(a) -> str:
    return os.fsdecode(a) if isinstance(a, (bytes, os.PathLike)) else str(a)


def _gh_write(words: list[str]) -> bool:
    rest = [w for w in words[1:]]
    pos = [w for w in rest if not w.startswith("-")]
    if not pos:
        return False
    if pos[0] == "api":
        for i, w in enumerate(rest):
            if w in ("-X", "--method") and i + 1 < len(rest) and rest[i + 1].upper() in ("POST", "PUT", "PATCH", "DELETE"):
                return True
            if w.startswith("--method=") and w.split("=", 1)[1].upper() in ("POST", "PUT", "PATCH", "DELETE"):
                return True
            if re.fullmatch(r"-X(POST|PUT|PATCH|DELETE)", w, re.I):
                return True
            if w in _GH_WRITE_FLAGS or w.split("=", 1)[0] in _GH_WRITE_FLAGS:
                return True
        return False
    verbs = _GH_WRITE.get(pos[0])
    return bool(verbs and len(pos) > 1 and pos[1] in verbs)


def _words_blocked(words: list[str], depth: int = 0) -> bool:
    """True when this argv (one simple command) runs a blocked command, looking through assignments, wrappers and shells."""
    if depth > 6:
        return False
    i = 0
    while i < len(words) and _ASSIGN.match(words[i]):
        i += 1
    words = words[i:]
    if not words:
        return False
    first = os.path.basename(words[0])
    if first in BLOCKED_COMMANDS:
        return True
    if first == "gh":
        return _gh_write(words)
    if first in _WRAPPERS:
        rest = words[1:]
        if first in ("command", "builtin") and any(w in ("-v", "-V", "-p") for w in rest[:1]):
            return False                                   # a lookup, not an execution
        j = 0
        while j < len(rest):
            w = rest[j]
            if w.startswith("-") or _ASSIGN.match(w) or (first == "timeout" and _DURATION.match(w)) or (first == "nice" and _DURATION.match(w)):
                j += 1
                continue
            break
        return _words_blocked(rest[j:], depth + 1)
    if first in _SHELLS:
        rest = words[1:]
        for k, w in enumerate(rest):
            if w.startswith("-") and not w.startswith("--") and "c" in w[1:] and k + 1 < len(rest):
                return _string_blocked(rest[k + 1], depth + 1)
            if not w.startswith("-"):
                return os.path.basename(w) in BLOCKED_COMMANDS                                       # `bash /x/bin/gcloud`
        return False
    return False


def _string_blocked(s: str, depth: int = 0) -> bool:
    """True when a shell command STRING has a blocked command in any command position."""
    s = s.replace("\n", " ; ").replace("`", " ; ").replace("$(", " ; ")
    try:
        lex = shlex.shlex(s, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        lex.commenters = ""
        tokens = list(lex)
    except ValueError:
        tokens = s.split()
    seg: list[str] = []
    segments: list[list[str]] = []
    for t in tokens:
        if t in _SEPARATORS or (t and set(t) <= set(";&|()<>") and t not in ("<", ">", ">>", "<<", "<&", ">&")):
            segments.append(seg)
            seg = []
        else:
            seg.append(t)
    segments.append(seg)
    for sg in segments:
        while sg and sg[0] in _SEPARATORS:
            sg = sg[1:]
        if sg and _words_blocked(sg, depth):
            return True
    return False


def is_blocked(args, shell: bool = False, executable=None) -> bool:
    """True when `args` (a command string or an argv) would run a blocked cloud command (or a write-capable gh call)."""
    try:
        if executable is not None and os.path.basename(_fs(executable)) in BLOCKED_COMMANDS:
            return True
        if isinstance(args, (bytes, os.PathLike)):
            args = _fs(args)
        if isinstance(args, str):
            return _string_blocked(args)
        return _words_blocked([_fs(a) for a in args])
    except (TypeError, ValueError):
        return False


def _record(record_path, args, via):
    entry = {"ts": time.time(), "via": via, "args": args if isinstance(args, (str, list, tuple)) else repr(args),
             "test": os.environ.get("PYTEST_CURRENT_TEST", "")}
    ATTEMPTS.append(entry)
    if not record_path:
        return
    try:
        with open(record_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except OSError:
        pass


def _make_stubs(stub_dir: str, record_path: str | None) -> None:
    for name in ("gcloud", "gsutil", "bq", "kubectl"):
        path = os.path.join(stub_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n"
                    f"echo 'no_real_cloud_guard: the cloud CLI {name} is blocked while tests run' >&2\n"
                    "[ -n \"$NO_REAL_CLOUD_RECORD\" ] && printf '{\"via\":\"stub\",\"args\":\"%s\"}\\n' \"$0 $*\" >> \"$NO_REAL_CLOUD_RECORD\"\n"
                    "exit 97\n")
        os.chmod(path, 0o755)


_ENSURED = []


def ensure_installed():
    """Install once per process (idempotent); called at conftest IMPORT time, i.e. before the tests' own modules are imported and before collection runs them."""
    if not _ENSURED:
        _ENSURED.append(install())
    return _ENSURED[0]


def install(record_path: str | None = None, stubs: bool = True):
    """Patch the choke points; returns a no-argument function that restores everything."""
    record_path = record_path or os.environ.get("NO_REAL_CLOUD_RECORD") or None
    saved = []
    env_saved = {k: os.environ.get(k) for k in ("PATH", "CLOUDSDK_CONFIG")}
    tmp_dirs: list[str] = []
    if stubs:
        stub_dir = tempfile.mkdtemp(prefix="no_real_cloud_stubs_")
        cfg_dir = tempfile.mkdtemp(prefix="no_real_cloud_cfg_")
        tmp_dirs += [stub_dir, cfg_dir]
        _make_stubs(stub_dir, record_path)
        os.environ["PATH"] = stub_dir + os.pathsep + (os.environ.get("PATH") or "")
        os.environ["CLOUDSDK_CONFIG"] = cfg_dir
    orig_init = subprocess.Popen.__init__

    def guarded_init(self, args, *a, **kw):
        if is_blocked(args, bool(kw.get("shell")), kw.get("executable")):
            _record(record_path, args, "subprocess.Popen")
            raise RealCloudCommandAttempt(f"a test tried to run a real cloud command: {args!r}")
        return orig_init(self, args, *a, **kw)

    subprocess.Popen.__init__ = guarded_init
    saved.append((subprocess.Popen, "__init__", orig_init))

    def patch(mod, name, extract):
        orig = getattr(mod, name, None)
        if orig is None:
            return

        def guarded(*a, **kw):
            try:
                argv = extract(a)
            except (IndexError, TypeError):
                argv = None
            if argv is not None and is_blocked(argv, False):
                _record(record_path, argv if isinstance(argv, str) else [_fs(x) for x in argv], f"os.{name}")
                raise RealCloudCommandAttempt(f"a test tried to run a real cloud command via os.{name}: {argv!r}")
            return orig(*a, **kw)
        setattr(mod, name, guarded)
        saved.append((mod, name, orig))

    def as_argv(path, argv):
        return [_fs(path)] + [_fs(x) for x in (argv or [])]

    patch(os, "system", lambda a: a[0])
    patch(os, "popen", lambda a: a[0])
    # exec*: (path, argv[, env]) for the v-forms, (path, *args) for the l-forms
    for name in ("execv", "execve", "execvp", "execvpe"):
        patch(os, name, lambda a: as_argv(a[0], a[1]))
    for name in ("execl", "execle", "execlp", "execlpe"):
        patch(os, name, lambda a: as_argv(a[0], a[1:]))
    # spawn*: (mode, path, argv[, env]) for the v-forms, (mode, path, *args) for the l-forms
    for name in ("spawnv", "spawnve", "spawnvp", "spawnvpe"):
        patch(os, name, lambda a: as_argv(a[1], a[2]))
    for name in ("spawnl", "spawnle", "spawnlp", "spawnlpe"):
        patch(os, name, lambda a: as_argv(a[1], a[2:]))
    for name in ("posix_spawn", "posix_spawnp"):
        patch(os, name, lambda a: as_argv(a[0], a[1]))

    def uninstall():
        for owner, attr, original in reversed(saved):
            setattr(owner, attr, original)
        for k, v in env_saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for d in tmp_dirs:
            shutil.rmtree(d, ignore_errors=True)
    return uninstall
