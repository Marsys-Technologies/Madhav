"""parser_sandbox.py: run a hash-pinned, repo-local parser in a guarded child interpreter (Nikasa N-431, worker R2).

Why: the census must PROVE a part is reproducible by re-running the committed parser over cited inputs and comparing with the stored rows. The census has never
executed repo code, so this module is the one place that does, under terms the director approved in principle: OUR OWN parser, pinned by sha256, run in an isolated
child interpreter with no DB handle and no network, read-only inputs passed in.

    run_pinned_parser(repo_root, module_root, pinned_files, file, function, inputs, *, timeout_s=120, max_output_bytes=64_000_000) -> dict

Returns {"ok": True, "outputs": [...], "loaded_repo_files": [...], "elapsed_s": float} or {"ok": False, "error": "<code>: <short detail>", "stage": "pin"|"spawn"|"run"|"output"}.
`canonical_json(obj)` is the canonical serialisation (sorted keys, no spaces, ASCII, no NaN) a caller should compare byte-for-byte.

What it does, in order
  1. PIN CHECK (engine process, before anything runs): sha256 of every pinned file is computed from the bytes on disk and compared with the declared digest. A missing file
     or a differing digest returns ok False at stage "pin" and NOTHING is executed. The same check is repeated AFTER the run (a file changed while the child ran is refused).
  2. SPAWN: `[sys.executable, -s -S -P -B, <this file>, --child-v1]`, an environment built from a tiny allowlist (nothing is inherited), cwd and HOME and TMPDIR in a fresh
     empty temp tree, stdin = the JSON request, stdout = the JSON result, stderr discarded, close_fds. The parent enforces a wall-clock timeout and an output-size cap and
     kills ONLY the child it started (by its own Popen handle).
  3. INSIDE THE CHILD, before the parser is imported: resource limits; network blocked; process spawning blocked; opening/creating/removing files outside the temp tree
     blocked; ctypes blocked; bytecode neither read from nor written to the repo (pycache_prefix points at an empty temp dir); an import recorder installed.
  4. The parser module is imported (first on sys.path: `module_root`), `function(input)` is called for each input in order, each result is serialised to canonical JSON.
     A function that returns a generator/iterator is materialised with list() inside the child.
  5. The parent checks: no guard violation was recorded (even one the parser caught and swallowed), and EVERY repo file the child loaded (every import found under repo_root,
     every repo file it opened) is in `pinned_files`. A parser that quietly imports an unpinned helper is unverifiable: ok False, "unpinned_import", even if it produced output.

Deviation from the brief, stated plainly: the interpreter flags are `-s -S -P -B`, NOT `-I`. `-I` implies `-E`, which makes the interpreter IGNORE PYTHONHASHSEED (measured: with
`-I` two runs of hash('abc') differ even with PYTHONHASHSEED=0). Determinism needs the seed honoured, so the flags are the rest of what `-I` does (-s no user site, -P no cwd/script
dir on sys.path) plus -S (no site-packages: the stdlib is still importable; a parser that needs a third-party package fails to import, loudly) and -B (no bytecode writes); the
environment is built from scratch by this module, so `-E` would add nothing (no PYTHON* variable but ours reaches the child).

Failure vocabulary (fixed; the detail never echoes a host path or a secret, only repo-relative paths the caller supplied and exception TYPE names):
  pin_missing, pin_mismatch, unpinned_import, spawn_failed, timeout, nonzero_exit, bad_output, output_too_large, parser_raised, network_attempt, write_attempt, spawn_attempt, no_inputs.
  no_inputs (stage "run"): `inputs` is an empty list. A run that compared nothing proves nothing, so it is never ok (it would be a false PASS); nothing is spawned. This is the ONLY
  empty case that fails: a parser that legitimately returns an empty list FOR AN INPUT is fine.
  parser_raised detail is "index=<i> type=<ExceptionType>"; index -1 means the parser module failed to import / the function was missing (before any input ran).
  bad_output covers a malformed result envelope and a result that is not canonical-JSON serialisable ("index=<i>").
  unpinned_import ALSO carries "unpinned_files": [sorted repo-relative paths, at most 50] (the only extra key any result has).
  Stages: pin (pin checks, before and after), spawn (bad arguments / could not start), run (child ran: timeout, exit status, parser_raised, guard violations, unpinned_import),
  output (the result: bad_output, output_too_large).

WHAT THIS DOES NOT GUARANTEE (read this before trusting a green)
  * It is NOT a kernel sandbox. There is no seccomp, no namespace, no chroot, no sandbox-exec, no container. The guards are SOFTWARE guards inside the same Python process
    as the parser. A determined or malicious parser can bypass them (import a C extension, use `socket.socket.__mro__` to reach the original `_socket.socket`, call `posix`
    functions the guard list omits, mutate the guard's own globals through `gc`/`sys.modules`, write to an inherited descriptor...).
  * The protection is therefore (a) the parser file and its entire import closure are pinned by sha256 and reviewed in git, so what runs is what was reviewed, and (b) the
    guards stop ACCIDENTS (a parser that opens a DB handle, fetches a URL, shells out, or writes a file), not attacks. Do not run unreviewed code through this.
  * READS are not restricted: the child can read any file the user can (the guard only records reads under repo_root so an unpinned repo file it reads is caught).
    Reading is not an effect, but it can leak into the returned output; the pinned, reviewed parser is what prevents that.
  * Resource limits: RLIMIT_CPU, RLIMIT_CORE, RLIMIT_FSIZE, RLIMIT_NOFILE and RLIMIT_AS are requested best-effort; a platform may refuse or ignore any of them (macOS ignores
    RLIMIT_AS for most purposes). The wall-clock timeout and the output cap are enforced by the PARENT and do not depend on them.
  * Threads started by the parser share the process; a parser that spawns a thread which outlives its call is stopped only by the timeout. os.kill and signal sending are not
    blocked (a parser could signal the parent); the parent supervises by waiting on its own child only.
  * Determinism: PYTHONHASHSEED=0, TZ=UTC, UTF-8 mode, no bytecode, inputs and outputs in order. A parser that reads the clock or `random` is not made deterministic by this module.
  * Pyc: the child never reads or writes bytecode in the repo (sys.pycache_prefix is an empty temp dir), so the code that runs is compiled from the source bytes on disk; the
    post-run re-hash closes the (tiny) window between the pre-run hash and the import.
  * Windows is not supported (the guards and the process flags assume POSIX).

The child is this very file run as a script (`--child-v1`), so the code that guards the parser is in git and syntax-checked like the rest. The census module must list this
file where it lists its subprocess users: this is a Python child process, not psql or git.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Public vocabulary and constants
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------

ERROR_CODES = (
    "pin_missing",
    "pin_mismatch",
    "unpinned_import",
    "spawn_failed",
    "timeout",
    "nonzero_exit",
    "bad_output",
    "output_too_large",
    "parser_raised",
    "network_attempt",
    "write_attempt",
    "spawn_attempt",
    "no_inputs",
)
_GUARD_CODES = ("network_attempt", "write_attempt", "spawn_attempt")
STAGES = ("pin", "spawn", "run", "output")

CHILD_FLAGS = ("-s", "-S", "-P", "-B")
CHILD_ARG = "--child-v1"
ENVELOPE_VERSION = 1

# The ONLY environment the child sees (HOME and TMPDIR are filled in per run). Nothing is inherited from the parent.
CHILD_ENV_KEYS = ("HOME", "PYTHONCOERCECLOCALE", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED", "PYTHONIOENCODING", "PYTHONNOUSERSITE", "PYTHONUTF8", "TMPDIR", "TZ")
# Keys the OS runtime itself may add to a process environment on exec (macOS CoreFoundation); they carry no parent data and are not ours to scrub.
OS_ADDED_ENV_KEYS = ("__CF_USER_TEXT_ENCODING",)

# Best-effort limits requested inside the child (see the docstring: platforms may ignore them).
CHILD_ADDRESS_SPACE_BYTES = 4 * 1024 ** 3
CHILD_MAX_FILE_BYTES = 64 * 1024 ** 2
CHILD_MAX_OPEN_FILES = 256
CHILD_CPU_GRACE_S = 2

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_MAX_DETAIL = 160


def canonical_json(obj) -> str:
    """The canonical serialisation: sorted keys, no spaces, ASCII only, NaN/Infinity refused. Compare results with this, byte for byte."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Parent side
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------


def _clean(text, limit: int = _MAX_DETAIL) -> str:
    s = "".join(ch if 32 <= ord(ch) < 127 else "?" for ch in str(text))
    return s[:limit]


def _fail(code: str, detail: str, stage: str) -> dict:
    assert code in ERROR_CODES and stage in STAGES
    d = _clean(detail)
    return {"ok": False, "error": (code + ": " + d) if d else code, "stage": stage}


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _rel_ok(rel) -> str | None:
    """Normalise a repo-relative path (posix, no '..', not absolute); None if it is not one."""
    if not isinstance(rel, str) or not rel or "\x00" in rel or "\\" in rel or rel.startswith("/"):
        return None
    norm = os.path.normpath(rel)
    if norm in (".", "") or norm == ".." or norm.startswith("../") or os.path.isabs(norm):
        return None
    return norm.replace(os.sep, "/")


def _inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def _check_pins(root: str, pins: dict[str, str]) -> tuple[str, str] | None:
    """Hash every pinned file now. None if all match, else (code, detail)."""
    for rel in sorted(pins):
        real = os.path.realpath(os.path.join(root, rel))
        if not _inside(real, root) or not os.path.isfile(real):
            return ("pin_missing", rel)
        try:
            digest = _sha256_file(real)
        except OSError:
            return ("pin_missing", rel)
        if digest != pins[rel]:
            return ("pin_mismatch", rel)
    return None


def _module_name_for(file_rel: str, module_root_rel: str) -> str | None:
    """Dotted import name of `file_rel` relative to `module_root_rel` ('' = repo root), or None if it is not importable by name from there."""
    if module_root_rel:
        if not file_rel.startswith(module_root_rel + "/"):
            return None
        sub = file_rel[len(module_root_rel) + 1:]
    else:
        sub = file_rel
    if not sub.endswith(".py"):
        return None
    parts = sub[:-3].split("/")
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts or not all(p.isidentifier() for p in parts):
        return None
    return ".".join(parts)


def _child_env(home: str, tmp: str) -> dict[str, str]:
    env = {
        "HOME": home,
        "TMPDIR": tmp,
        "PYTHONHASHSEED": "0",
        "PYTHONCOERCECLOCALE": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONNOUSERSITE": "1",
        "TZ": "UTC",
    }
    assert set(env) == set(CHILD_ENV_KEYS)
    return env


def run_pinned_parser(repo_root, module_root, pinned_files, file, function, inputs, *, timeout_s=120, max_output_bytes=64_000_000) -> dict:
    """Run `function` from the pinned repo file `file` over `inputs` in a guarded child interpreter. See the module docstring for the contract."""
    t0 = time.perf_counter()

    # ---- argument validation (stage spawn: nothing has been hashed or run) ----
    try:
        root = os.path.realpath(os.fspath(repo_root))
    except TypeError:
        return _fail("spawn_failed", "repo_root not a path", "spawn")
    if not os.path.isdir(root):
        return _fail("spawn_failed", "repo_root not a directory", "spawn")
    if sys.version_info < (3, 11) or not sys.executable:
        return _fail("spawn_failed", "python 3.11+ interpreter required", "spawn")
    if not isinstance(function, str) or not function.isidentifier():
        return _fail("spawn_failed", "function not an identifier", "spawn")
    if not isinstance(inputs, list):
        return _fail("spawn_failed", "inputs not a list", "spawn")
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)) or timeout_s <= 0:
        return _fail("spawn_failed", "timeout_s not positive", "spawn")
    if isinstance(max_output_bytes, bool) or not isinstance(max_output_bytes, int) or max_output_bytes <= 0:
        return _fail("spawn_failed", "max_output_bytes not positive", "spawn")
    mr = "" if module_root in (None, "", ".") else _rel_ok(module_root)
    if mr is None:
        return _fail("spawn_failed", "module_root not a repo-relative path", "spawn")
    module_root_abs = os.path.realpath(os.path.join(root, mr)) if mr else root
    if not _inside(module_root_abs, root) or not os.path.isdir(module_root_abs):
        return _fail("spawn_failed", "module_root not a directory inside the repo", "spawn")
    try:
        request_inputs = canonical_json(inputs)
    except (TypeError, ValueError):
        return _fail("spawn_failed", "inputs not JSON-serialisable", "spawn")

    # ---- PIN CHECK, before anything runs ----
    if not isinstance(pinned_files, (list, tuple)) or not pinned_files:
        return _fail("pin_missing", "no pinned files declared", "pin")
    pins: dict[str, str] = {}
    for ent in pinned_files:
        if not isinstance(ent, dict) or not isinstance(ent.get("sha256"), str) or not _SHA256_RE.match(ent["sha256"]):
            return _fail("pin_missing", "malformed pinned_files entry", "pin")
        rel = _rel_ok(ent.get("path"))
        if rel is None:
            return _fail("pin_missing", "malformed pinned_files path", "pin")
        digest = ent["sha256"].lower()
        if pins.get(rel, digest) != digest:
            return _fail("pin_mismatch", rel + " declared with two digests", "pin")
        pins[rel] = digest
    file_rel = _rel_ok(file)
    if file_rel is None or file_rel not in pins:
        return _fail("pin_missing", "file is not one of pinned_files", "pin")
    bad = _check_pins(root, pins)  # NOTHING has been executed yet
    if bad is not None:
        return _fail(bad[0], bad[1], "pin")

    if not inputs:
        return _fail("no_inputs", "inputs is empty; a run over nothing proves nothing", "run")

    module_name = _module_name_for(file_rel, mr)
    file_abs = os.path.join(root, file_rel)

    # ---- spawn ----
    try:
        scratch = tempfile.mkdtemp(prefix="parser_sandbox_")
    except OSError:
        return _fail("spawn_failed", "no temp directory", "spawn")
    scratch = os.path.realpath(scratch)
    work, home, tmp, pyc = (os.path.join(scratch, n) for n in ("work", "home", "tmp", "pyc"))
    try:
        for d in (work, home, tmp, pyc):
            os.mkdir(d)
        cfg = {
            "v": ENVELOPE_VERSION,
            "root": root,
            "module_root_abs": module_root_abs,
            "module_name": module_name,
            "file_rel": file_rel,
            "file_abs": file_abs,
            "function": function,
            "write_root": scratch,
            "pycache_prefix": pyc,
            "cpu_s": int(timeout_s) + CHILD_CPU_GRACE_S,
            "as_bytes": CHILD_ADDRESS_SPACE_BYTES,
            "fsize_bytes": CHILD_MAX_FILE_BYTES,
            "nofile": CHILD_MAX_OPEN_FILES,
            "inputs_json": request_inputs,
        }
        request = canonical_json(cfg).encode("utf-8")
        return _supervise(root, pins, file_rel, len(inputs), request, work, home, tmp, float(timeout_s), int(max_output_bytes), t0)
    finally:
        _rmtree_quiet(scratch)


def _rmtree_quiet(path: str) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


def _supervise(root, pins, file_rel, n_inputs, request, work, home, tmp, timeout_s, max_output_bytes, t0) -> dict:
    argv = [sys.executable, *CHILD_FLAGS, os.path.abspath(__file__), CHILD_ARG]
    try:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=work,
            env=_child_env(home, tmp),
            close_fds=True,
        )
    except (OSError, ValueError):
        return _fail("spawn_failed", "could not start the child interpreter", "spawn")

    buf = bytearray()
    state = {"overflow": False}

    def _feed():
        try:
            proc.stdin.write(request)
            proc.stdin.close()
        except (OSError, ValueError):
            pass

    def _drain():
        try:
            while True:
                block = proc.stdout.read(65536)
                if not block:
                    return
                if len(buf) + len(block) > max_output_bytes:
                    state["overflow"] = True
                    try:
                        proc.kill()
                    except OSError:
                        pass
                    return
                buf.extend(block)
        except (OSError, ValueError):
            return

    t_in = threading.Thread(target=_feed, daemon=True)
    t_out = threading.Thread(target=_drain, daemon=True)
    t_in.start()
    t_out.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()  # this child only, by its own handle
        proc.wait()
    t_out.join(timeout=10)
    t_in.join(timeout=10)
    for stream in (proc.stdout, proc.stdin):
        try:
            stream.close()
        except (OSError, ValueError):
            pass
    elapsed = time.perf_counter() - t0

    if timed_out:
        return _fail("timeout", "wall-clock limit of %ss exceeded" % _clean(timeout_s, 20), "run")
    if state["overflow"]:
        return _fail("output_too_large", "result exceeded %d bytes" % max_output_bytes, "output")
    rc = proc.returncode
    if rc != 0:
        # SIGXCPU / SIGKILL from the child's own CPU limit is a time-limit stop, anything else is an abnormal exit.
        if rc in (-24, -9):
            return _fail("timeout", "cpu limit reached", "run")
        return _fail("nonzero_exit", "rc=%d" % rc, "run")

    try:
        env = json.loads(bytes(buf).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return _fail("bad_output", "result is not JSON", "output")
    if not isinstance(env, dict) or env.get("v") != ENVELOPE_VERSION or env.get("status") not in ("ok", "error"):
        return _fail("bad_output", "malformed result envelope", "output")
    violations = env.get("violations")
    loaded = env.get("loaded")
    if not isinstance(violations, list) or not all(isinstance(x, str) for x in violations) or not isinstance(loaded, list) or not all(isinstance(x, str) for x in loaded):
        return _fail("bad_output", "malformed result envelope", "output")

    # A guard violation wins over everything, including a parser that caught the exception and carried on (the child records it independently).
    for code in violations:
        if code in _GUARD_CODES:
            return _fail(code, "blocked by the sandbox guard", "run")

    if env["status"] == "error":
        code = env.get("code")
        detail = env.get("detail", "")
        if code not in ("parser_raised", "bad_output") or not isinstance(detail, str):
            return _fail("bad_output", "malformed error envelope", "output")
        return _fail(code, detail, "run" if code == "parser_raised" else "output")

    outputs = env.get("outputs")
    if not isinstance(outputs, list) or len(outputs) != n_inputs:
        return _fail("bad_output", "outputs do not match inputs", "output")

    # Every repo file the child loaded must be pinned.
    loaded_rel: set[str] = set()
    unpinned: set[str] = set()
    for p in loaded:
        lex = os.path.abspath(p)
        real = os.path.realpath(p)
        if not _inside(lex, root) and not _inside(real, root):
            continue
        rel = os.path.relpath(lex if _inside(lex, root) else real, root).replace(os.sep, "/")
        loaded_rel.add(rel)
        if rel not in pins or not _inside(real, root):
            unpinned.add(rel)
    if unpinned:
        names = sorted(unpinned)
        res = _fail("unpinned_import", ", ".join(names[:2]) + (" (+%d more)" % (len(names) - 2) if len(names) > 2 else ""), "run")
        res["unpinned_files"] = names[:50]  # additive key on this one failure: the full list, so a caller can show or pin the whole closure
        return res
    if file_rel not in loaded_rel:
        return _fail("bad_output", "pinned parser file was not the file loaded", "output")

    # Post-run re-hash: a pinned file changed while the child ran is refused.
    bad = _check_pins(root, pins)
    if bad is not None:
        return _fail("pin_missing" if bad[0] == "pin_missing" else "pin_mismatch", bad[1] + " (changed during the run)", "pin")

    return {"ok": True, "outputs": outputs, "loaded_repo_files": sorted(loaded_rel), "elapsed_s": elapsed}


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Child side (this file run as `python -s -S -P -B parser_sandbox.py --child-v1`). Everything below runs in the guarded interpreter, never in the engine.
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------


class _GuardViolation(BaseException):
    """Raised by a guard. A BaseException on purpose: a parser's `except Exception` cannot swallow it (and the violation is recorded regardless)."""


_VIOLATIONS: list[str] = []
_G: dict = {"root": None, "write_root": None, "touched": set(), "found": set()}


def _violate(code: str):
    _VIOLATIONS.append(code)
    raise _GuardViolation(code)


def _is_write_mode(mode) -> bool:
    return isinstance(mode, str) and any(c in mode for c in "wax+")


def _real(p):
    try:
        p = os.fspath(p)
    except TypeError:
        return None
    if isinstance(p, bytes):
        p = os.fsdecode(p)
    return os.path.realpath(p)


def _write_allowed(p) -> bool:
    if isinstance(p, int):
        return False
    n = _real(p)
    if n is None:
        return False
    if n == os.path.realpath(os.devnull):
        return True
    wr = _G["write_root"]
    return n == wr or n.startswith(wr + os.sep)


def _note_read(p) -> None:
    """Remember a repo file the parser opened, so an unpinned data/helper file it reads shows up in loaded_repo_files."""
    if isinstance(p, int):
        return
    try:
        q = os.fspath(p)
        if isinstance(q, bytes):
            q = os.fsdecode(q)
        lex = os.path.abspath(q)
    except (TypeError, ValueError):
        return
    root = _G["root"]
    if root and (lex == root or lex.startswith(root + os.sep)):
        _G["touched"].add(lex)


def _install_write_guards(builtins, io, _io, posix) -> None:
    real_open = builtins.open

    def guarded_open(file, mode="r", *args, **kw):
        if "mode" in kw:
            mode = kw.pop("mode")
        if _is_write_mode(mode):
            if not _write_allowed(file):
                _violate("write_attempt")
        else:
            _note_read(file)
        return real_open(file, mode, *args, **kw)

    builtins.open = guarded_open
    io.open = guarded_open
    _io.open = guarded_open

    real_fileio = _io.FileIO

    class GuardedFileIO(real_fileio):
        def __init__(self, file, mode="r", *args, **kw):
            if _is_write_mode(mode):
                if not _write_allowed(file):
                    _violate("write_attempt")
            else:
                _note_read(file)
            super().__init__(file, mode, *args, **kw)

    _io.FileIO = GuardedFileIO
    io.FileIO = GuardedFileIO

    write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND | getattr(os, "O_TMPFILE", 0)

    # (name, [(argument name, position), ...]) of the path arguments each mutator takes.
    mutators = (
        ("mkdir", [("path", 0)]),
        ("remove", [("path", 0)]),
        ("unlink", [("path", 0)]),
        ("rmdir", [("path", 0)]),
        ("rename", [("src", 0), ("dst", 1)]),
        ("replace", [("src", 0), ("dst", 1)]),
        ("link", [("src", 0), ("dst", 1)]),
        ("symlink", [("dst", 1)]),
        ("truncate", [("path", 0)]),
        ("chmod", [("path", 0)]),
        ("chown", [("path", 0)]),
        ("lchown", [("path", 0)]),
        ("lchmod", [("path", 0)]),
        ("chflags", [("path", 0)]),
        ("lchflags", [("path", 0)]),
        ("utime", [("path", 0)]),
        ("mkfifo", [("path", 0)]),
        ("mknod", [("path", 0)]),
        ("setxattr", [("path", 0)]),
        ("removexattr", [("path", 0)]),
    )

    def make_os_open(real):
        def guarded_os_open(path, flags, *args, **kw):
            if flags & write_flags:
                if kw.get("dir_fd") is not None or not _write_allowed(path):
                    _violate("write_attempt")
            else:
                _note_read(path)
            return real(path, flags, *args, **kw)

        return guarded_os_open

    def make_mutator(orig, argspec):
        def guarded(*args, **kw):
            if kw.get("dir_fd") is not None or kw.get("src_dir_fd") is not None or kw.get("dst_dir_fd") is not None:
                _violate("write_attempt")
            for aname, pos in argspec:
                if pos < len(args):
                    val = args[pos]
                elif aname in kw:
                    val = kw[aname]
                else:
                    continue
                if not _write_allowed(val):
                    _violate("write_attempt")
            return orig(*args, **kw)

        return guarded

    for mod in (os, posix):
        if mod is None:
            continue
        mod.open = make_os_open(mod.open)
        for name, argspec in mutators:
            orig = getattr(mod, name, None)
            if orig is not None:
                setattr(mod, name, make_mutator(orig, argspec))


def _install_spawn_guards(subprocess_mod, posix, posixsubprocess) -> None:
    def deny(*args, **kw):
        _violate("spawn_attempt")

    class GuardedPopen:
        def __init__(self, *args, **kw):
            _violate("spawn_attempt")

    names = (
        "system", "popen", "fork", "forkpty", "startfile",
        "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
        "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
        "posix_spawn", "posix_spawnp",
    )
    for mod in (os, posix):
        if mod is None:
            continue
        for n in names:
            if hasattr(mod, n):
                setattr(mod, n, deny)
    subprocess_mod.Popen = GuardedPopen
    if hasattr(subprocess_mod, "_fork_exec"):
        subprocess_mod._fork_exec = deny
    if posixsubprocess is not None:
        posixsubprocess.fork_exec = deny


def _install_network_guards(socket_mod, _socket) -> None:
    def deny(*args, **kw):
        _violate("network_attempt")

    class BlockedSocket:
        def __init__(self, *args, **kw):
            _violate("network_attempt")

    funcs = (
        "create_connection", "create_server", "getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr", "getnameinfo",
        "socketpair", "fromfd", "fromshare",
    )
    for mod in (socket_mod, _socket):
        if mod is None:
            continue
        for n in ("socket", "SocketType"):
            if hasattr(mod, n):
                setattr(mod, n, BlockedSocket)
        for n in funcs:
            if hasattr(mod, n):
                setattr(mod, n, deny)


def _make_recorder():
    class Recorder:
        """First on sys.meta_path: delegates to the real finders (identical resolution) and records the file every found spec points at."""

        @classmethod
        def find_spec(cls, name, path=None, target=None):
            for finder in sys.meta_path:
                if finder is cls:
                    continue
                f = getattr(finder, "find_spec", None)
                if f is None:
                    continue
                spec = f(name, path, target)
                if spec is not None:
                    origin = getattr(spec, "origin", None)
                    if getattr(spec, "has_location", False) and isinstance(origin, str) and os.path.isabs(origin):
                        _G["found"].add(os.path.abspath(origin))
                    return spec
            return None

    return Recorder


def _collect_loaded(stdlib_roots) -> list[str]:
    root = _G["root"]
    cands = set(_G["found"]) | set(_G["touched"])
    for name, mod in list(sys.modules.items()):
        if name == "__main__":
            continue  # this runner itself (the child is this file run as a script) is not parser code
        f = getattr(mod, "__file__", None)
        if isinstance(f, str) and os.path.isabs(f):
            cands.add(os.path.abspath(f))
        spec = getattr(mod, "__spec__", None)
        origin = getattr(spec, "origin", None)
        if getattr(spec, "has_location", False) and isinstance(origin, str) and os.path.isabs(origin):
            cands.add(os.path.abspath(origin))
    out = set()
    for c in cands:
        real = os.path.realpath(c)
        if not (c.startswith(root + os.sep) or real.startswith(root + os.sep)):
            continue
        if any(real == s or real.startswith(s + os.sep) for s in stdlib_roots):
            continue  # the interpreter's own standard library happens to live under the repo (unusual); it is not a repo parser file
        out.add(c)
    return sorted(out)


def _emit(result_fd: int, payload: str) -> None:
    view = memoryview(payload.encode("utf-8"))
    while view:
        n = os.write(result_fd, view)
        view = view[n:]


def _child_main() -> None:
    # Everything the guards and the loader need is imported FIRST, before module_root is put on sys.path (so a repo file named like a stdlib module cannot shadow it).
    import builtins
    import importlib
    import importlib.util
    import io
    import socket

    import _io
    import _socket

    try:
        import resource
    except ImportError:
        resource = None
    try:
        import posix
    except ImportError:
        posix = None
    try:
        import _posixsubprocess
    except ImportError:
        _posixsubprocess = None

    sys.dont_write_bytecode = True
    cfg = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    inputs = json.loads(cfg["inputs_json"])

    # stdout becomes /dev/null for the parser; the result goes out on a private duplicate of the original pipe.
    result_fd = os.dup(1)
    null_fd = os.open(os.devnull, os.O_RDWR)
    os.dup2(null_fd, 1)
    os.dup2(null_fd, 0)
    os.close(null_fd)

    if resource is not None:
        limits = (
            ("RLIMIT_CPU", (cfg["cpu_s"], cfg["cpu_s"] + 1)),
            ("RLIMIT_CORE", (0, 0)),
            ("RLIMIT_FSIZE", (cfg["fsize_bytes"], cfg["fsize_bytes"])),
            ("RLIMIT_NOFILE", (cfg["nofile"], cfg["nofile"])),
            ("RLIMIT_AS", (cfg["as_bytes"], cfg["as_bytes"])),
        )
        for name, val in limits:
            try:
                resource.setrlimit(getattr(resource, name), val)
            except (ValueError, OSError, AttributeError):
                pass  # best effort; the parent's wall-clock timeout does not depend on these

    sys.pycache_prefix = cfg["pycache_prefix"]
    stdlib_roots = [os.path.realpath(p) for p in sys.path if p]
    _G["root"] = cfg["root"]
    _G["write_root"] = cfg["write_root"]

    _install_write_guards(builtins, io, _io, posix)
    _install_spawn_guards(subprocess, posix, _posixsubprocess)
    _install_network_guards(socket, _socket)
    sys.modules["ctypes"] = None  # `import ctypes` now raises ImportError: no route to raw syscalls through the standard library
    sys.modules["_ctypes"] = None

    sys.path.insert(0, cfg["module_root_abs"])
    sys.meta_path.insert(0, _make_recorder())

    dumps = json.dumps
    texts: list[str] = []
    error = None
    try:
        try:
            if cfg["module_name"]:
                mod = importlib.import_module(cfg["module_name"])
            else:
                spec = importlib.util.spec_from_file_location("_pinned_parser_module", cfg["file_abs"])
                mod = importlib.util.module_from_spec(spec)
                sys.modules["_pinned_parser_module"] = mod
                spec.loader.exec_module(mod)
            if os.path.realpath(getattr(mod, "__file__", "") or "") != os.path.realpath(cfg["file_abs"]):
                raise ImportError("module resolved to a different file than the pinned one")
            fn = getattr(mod, cfg["function"])
            if not callable(fn):
                raise TypeError("function is not callable")
        except _GuardViolation:
            raise
        except BaseException as exc:  # noqa: BLE001 - any failure to load the parser is reported by type only
            error = ("parser_raised", "index=-1 type=" + type(exc).__name__)
        if error is None:
            for i, item in enumerate(inputs):
                try:
                    out = fn(item)
                    if hasattr(out, "__next__"):
                        out = list(out)
                except _GuardViolation:
                    raise
                except BaseException as exc:  # noqa: BLE001
                    error = ("parser_raised", "index=%d type=%s" % (i, type(exc).__name__))
                    break
                try:
                    texts.append(dumps(out, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False))
                except (TypeError, ValueError, RecursionError):
                    error = ("bad_output", "index=%d result not JSON-serialisable" % i)
                    break
    except _GuardViolation:
        error = None
        texts = []

    loaded = _collect_loaded(stdlib_roots)
    violations = list(_VIOLATIONS)
    if violations:
        payload = dumps({"v": ENVELOPE_VERSION, "status": "error", "code": "parser_raised", "detail": "guard", "loaded": loaded, "violations": violations}, sort_keys=True)
    elif error is not None:
        payload = dumps({"v": ENVELOPE_VERSION, "status": "error", "code": error[0], "detail": error[1], "loaded": loaded, "violations": violations}, sort_keys=True)
    else:
        payload = '{"loaded":%s,"outputs":[%s],"status":"ok","v":%d,"violations":%s}' % (dumps(loaded), ",".join(texts), ENVELOPE_VERSION, dumps(violations))
    try:
        _emit(result_fd, payload)
    except OSError:
        os._exit(1)
    os._exit(0)  # no atexit handlers or finalisers the parser may have registered


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == CHILD_ARG:
        _child_main()
    else:
        sys.stderr.write("parser_sandbox is a library; the child entry point is internal\n")
        sys.exit(2)
