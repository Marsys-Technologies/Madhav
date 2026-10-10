"""parser_sandbox.py: run a hash-pinned, repo-local parser in a guarded child interpreter (Nikasa N-431, worker R2).

Why: the census must PROVE a part is reproducible by re-running the committed parser over cited inputs and comparing with the stored rows. The census has never
executed repo code, so this module is the one place that does, under terms the director approved in principle: OUR OWN parser, pinned by sha256, run in an isolated
child interpreter with no DB handle and no network, read-only inputs passed in.

    run_pinned_parser(repo_root, module_root, pinned_files, file, function, inputs, *, timeout_s=120, max_output_bytes=16_000_000, allow_unpinned_runner_for_tests=False) -> dict

Pins come from a COMMITTED declaration, never from run-time discovery: `load_pin_manifest(repo_root, manifest_rel)` reads and validates a committed JSON manifest
{"pinned_files": [{"path", "sha256"}], "runner_sha256": "<64 hex>"}; in production that declaration is corpus_derived.parser.pinned_files, built with R1's pin_files when the
declaration is written. The tests build their fixture pins from a manifest the test writes; any closure-discovery helper lives in the tests only and is named as a test helper.
The manifest PINS THE RUNNER TOO (the child's own code, this file): `runner_sha256` is the sha256 of this file's bytes (= of the text the engine loaded, see RUNNER INTEGRITY).
It is REQUIRED: load_pin_manifest raises PinManifestError for a manifest without it, unless the test-only keyword `_test_only_allow_missing_runner=True` is passed, and
run_pinned_parser refuses a call whose pins carry no runner digest (a plain list, or a manifest loaded with the test-only flag) unless the test-only keyword
`allow_unpinned_runner_for_tests=True` is passed. Chosen deliberately fail-closed: a production run must name the runner it was reviewed against.

Returns {"ok": True, "outputs": [...], "loaded_repo_files": [...], "elapsed_s": float, "assurance": ASSURANCE} or
{"ok": False, "error": "<code>: <short detail>", "stage": "pin"|"spawn"|"run"|"output", "assurance": ASSURANCE}.
EVERY result, ok or failure, carries `"assurance": ASSURANCE` ("software-guarded, reviewed code only"), so the census can print that exact label on any pass derived from this tool.
`canonical_json(obj)` is the canonical serialisation (sorted keys, no spaces, ASCII, no NaN) a caller should compare byte-for-byte.

What it does, in order
  1. PIN CHECK (engine process, before anything runs): each pinned file is read from disk EXACTLY ONCE, as bytes, and the sha256 of THOSE bytes is compared with the declared
     digest. A missing file, an oversize file or a differing digest returns ok False at stage "pin" and NOTHING is executed. Those same bytes are what is sent to the child:
     the proof is "the bytes that ran are the bytes that were hashed". The disk is not consulted again for pinned content, so a file edited after the check (a TOCTOU attacker,
     or an editor) cannot change what runs, and there is deliberately NO post-run re-hash of the disk (it would reject a correct run and prove nothing the first read did not).
  1b. RUNNER PIN CHECK (engine process, before anything is spawned): the sha256 of the runner text the engine will send to the child is compared with the manifest's
     `runner_sha256`. A mismatch (or no runner digest supplied) returns ok False, "runner_unpinned", stage "pin", and NO child process is started. The digest is taken over the
     very string that is then sent (one local copy of _RUNNER_SOURCE is used for both), so the text that was compared is the text that runs.
  2. SPAWN: `[sys.executable, -s -S -P -B, -c, <bootstrap>]`, an environment built from a tiny allowlist (nothing is inherited), cwd and HOME and TMPDIR in a fresh empty temp
     tree, stdin = ONE JSON document {"runner": <this module's source>, "request": {..., "files": {path: base64 bytes}, "modules": {...}}}, stdout = the JSON result,
     stderr discarded, close_fds. The parent enforces a wall-clock timeout and an output-size cap and kills ONLY the child it started (by its own Popen handle).
     RUNNER INTEGRITY, design chosen = IN MEMORY: the runner (the child's own code, which is not pinned) is this file's text, read once at import into _RUNNER_SOURCE
     (digest published as RUNNER_SHA256) and compiled by the bootstrap from stdin. The child never opens a file of ours to get its code, so editing parser_sandbox.py on disk
     during or after the engine imported it has no effect on any run. (Residual, same class as editing the engine itself: a change between the interpreter compiling this
     module and this module reading its own text a moment later; the engine is trusted code reviewed in git.)
     DETECTION (step 1b): a runner file changed between review and run, i.e. before this process imported it, is detected at the first run by the digest in the committed manifest
     and refused before the child is spawned. REMAINING WINDOW, stated honestly: (a) the comparison is done by this same file, so an edited engine could simply omit it; the anchor
     is review in git plus the CI test that the committed manifest equals a fresh regeneration, not this check; (b) manifest and runner are changed together in one commit by whoever
     regenerates the manifest, so the check proves "the runner is the one the manifest names", not "the runner was reviewed"; (c) a runner file edited on disk AFTER this process
     imported it is neither detected nor relevant (the in-memory text is what was compared and what runs); (d) the manifest is read from disk once by load_pin_manifest, so a
     manifest edited after that is not seen by an already-loaded list.
  3. INSIDE THE CHILD, before the parser is imported: resource limits; network blocked; process spawning blocked; opening/creating/removing files outside the temp tree
     blocked; ctypes blocked; bytecode neither read from nor written to the repo (pycache_prefix points at an empty temp dir); the repo is reachable ONLY through the passed
     bytes: a sys.meta_path finder placed first serves every pinned module by compiling the passed source (module names are mapped from the paths relative to `module_root`,
     package __init__.py included), and builtins.open / io.open / io.open_code serve a pinned file (a data file such as a .json read at import) from the passed bytes.
     ANY OTHER read or import of a file inside repo_root (an unpinned module that exists on disk, an unpinned data file, a raw FileIO or os.open of a repo file) is refused
     BEFORE it executes or is read, recorded, and ends the run as "unpinned_import". Stdlib and site modules outside repo_root keep working.
  4. The parser module is imported (from the passed bytes), `function(input)` is called for each input in order, each result is serialised to canonical JSON.
     A function that returns a generator/iterator is materialised with list() inside the child.
  5. The parent checks: no guard violation was recorded (even one the parser caught and swallowed; an unpinned import or read cannot be swallowed), and, as a second layer, EVERY
     repo file the child reports as loaded is in `pinned_files`. A parser that quietly imports an unpinned helper is unverifiable: ok False, "unpinned_import".
     The run stops at the FIRST refused file (it is never executed), so unpinned_files lists what was refused, not the whole closure; pin it and retry.
     Layers, each with a test that fails when that layer alone is removed (TestEachGuardLayerIsolated): in the child, the import finder; the open_code hooks (_io.open_code,
     io.open_code); the open hooks (builtins.open, io.open, _io.open); the FileIO hooks (io.FileIO, _io.FileIO); the descriptor hooks (os.open, posix.open); in the parent, the
     honouring of recorded violations and this loaded-files check. They overlap on purpose (an unpinned `import` is refused by the finder AND by open_code); the second layer is
     a detector after the fact, not a preventer, and it sees only modules left in sys.modules, not a data file that was read.

Deviation from the brief, stated plainly: the interpreter flags are `-s -S -P -B`, NOT `-I`. `-I` implies `-E`, which makes the interpreter IGNORE PYTHONHASHSEED (measured: with
`-I` two runs of hash('abc') differ even with PYTHONHASHSEED=0). Determinism needs the seed honoured, so the flags are the rest of what `-I` does (-s no user site, -P no cwd/script
dir on sys.path) plus -S (no site-packages: the stdlib is still importable; a parser that needs a third-party package fails to import, loudly) and -B (no bytecode writes); the
environment is built from scratch by this module, so `-E` would add nothing (no PYTHON* variable but ours reaches the child).

Failure vocabulary (fixed; the detail never echoes a host path or a secret, only repo-relative paths the caller supplied and exception TYPE names):
  pin_missing, pin_mismatch, unpinned_import, spawn_failed, timeout, nonzero_exit, bad_output, output_too_large, parser_raised, network_attempt, write_attempt, spawn_attempt, no_inputs,
  runner_unpinned.
  runner_unpinned (stage "pin"): the runner text's sha256 differs from the manifest's `runner_sha256`, or the call carries no runner digest at all (see step 1b). Nothing is spawned.
  no_inputs (stage "run"): `inputs` is an empty list. A run that compared nothing proves nothing, so it is never ok (it would be a false PASS); nothing is spawned. This is the ONLY
  empty case that fails: a parser that legitimately returns an empty list FOR AN INPUT is fine.
  parser_raised detail is "index=<i> type=<ExceptionType>"; index -1 means the parser module failed to import / the function was missing (before any input ran).
  bad_output covers a malformed result envelope and a result that is not canonical-JSON serialisable ("index=<i>").
  unpinned_import ALSO carries "unpinned_files": [sorted repo-relative paths, at most 50] (the only failure-only extra key; "assurance" is on every result).
  Stages: pin (the single read-and-hash of the pinned files), spawn (bad arguments / could not start), run (child ran: timeout, exit status, parser_raised, guard violations, unpinned_import),
  output (the result: bad_output, output_too_large).

PERMITTED USE (a rule, not a suggestion)
  This tool may ONLY ever run the pinned, reviewed l0_rules parser (the bg_rules rule extractor) and its pinned adapter. It must never be pointed at any other code, at code
  that has not been reviewed in git, or at anything a user, a document or a database row supplied. A pass derived from it is evidence of "this reviewed code, run under software
  guards, reproduces the stored rows" and nothing stronger; the census prints ASSURANCE next to it.

WHAT THIS DOES NOT GUARANTEE (read this before trusting a green)
  * THE RESULT CHANNEL LIVES IN THE PARSER'S OWN PROCESS. The envelope the parent reads is written by the child runner, in the same Python process as the parser, so a HOSTILE
    pinned parser could forge an ok envelope (or edit the recorded violations / loaded list). This is a documented, accepted limit, not a bug to be fixed here. What the design
    protects against: ACCIDENTS (a parser that opens a socket, spawns a process, writes a file, reads an unpinned helper) and an UNREVIEWED CHANGE to the parser or its closure
    (the sha256 pins). What it does NOT protect against: a MALICIOUS pinned parser. The only defence against that is review in git, which is why the PERMITTED USE rule exists.
  * It is NOT a kernel sandbox. There is no seccomp, no namespace, no chroot, no sandbox-exec, no container. The guards are SOFTWARE guards inside the same Python process
    as the parser. A determined or malicious parser can bypass them (import a C extension, use `socket.socket.__mro__` to reach the original `_socket.socket`, call `posix`
    functions the guard list omits, mutate the guard's own globals through `gc`/`sys.modules`, write to an inherited descriptor...).
  * The protection is therefore (a) the parser file and its entire import closure are pinned by sha256 and reviewed in git, so what runs is what was reviewed, and (b) the
    guards stop ACCIDENTS (a parser that opens a DB handle, fetches a URL, shells out, or writes a file), not attacks. Do not run unreviewed code through this.
  * READS outside repo_root are not restricted: the child can read any file the user can. Inside repo_root only the passed pinned bytes are readable (everything else is
    refused as unpinned_import). Reading is not an effect, but it can leak into the returned output; the pinned, reviewed parser is what prevents that.
  * Resource limits: RLIMIT_CPU, RLIMIT_CORE, RLIMIT_FSIZE, RLIMIT_NOFILE and RLIMIT_AS are requested best-effort; a platform may refuse or ignore any of them (macOS ignores
    RLIMIT_AS for most purposes). The wall-clock timeout and the output cap are enforced by the PARENT and do not depend on them.
  * Threads started by the parser share the process; a parser that spawns a thread which outlives its call is stopped only by the timeout. os.kill and signal sending are not
    blocked (a parser could signal the parent); the parent supervises by waiting on its own child only.
  * Determinism: PYTHONHASHSEED=0, TZ=UTC, UTF-8 mode, no bytecode, inputs and outputs in order. A parser that reads the clock or `random` is not made deterministic by this module.
  * Pyc: the child never reads or writes bytecode in the repo (sys.pycache_prefix is an empty temp dir) and never reads repo source from disk: pinned code is compiled from
    the hashed bytes the parent sent.
  * Windows is not supported (the guards and the process flags assume POSIX).

The child's code is this very file (sent from memory, see step 2), so the code that guards the parser is in git and syntax-checked like the rest. The census module must list
this file where it lists its subprocess users: this is a Python child process, not psql or git.
"""
from __future__ import annotations

import base64
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
    "runner_unpinned",
)
_GUARD_CODES = ("network_attempt", "write_attempt", "spawn_attempt")
STAGES = ("pin", "spawn", "run", "output")

# The label every result carries. It states the strength of the evidence honestly: software guards in the parser's own process, over reviewed code. See the docstring.
ASSURANCE = "software-guarded, reviewed code only"

# Default cap on the child's result size. It is deliberately modest: macOS ignores RLIMIT_AS, so the child's memory is bounded only by this parent-enforced output cap and the
# wall-clock timeout, and the real bg_rules output (rule rows for a few thousand chunks) is far smaller than this. A caller with a genuinely larger need passes it explicitly.
DEFAULT_MAX_OUTPUT_BYTES = 16_000_000

# Bounds for a committed pin manifest and for the files it pins.
MAX_MANIFEST_BYTES = 1 << 20
MAX_PINNED_FILES = 512
MAX_PINNED_FILE_BYTES = 8 << 20

CHILD_FLAGS = ("-s", "-S", "-P", "-B")
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


def _read_runner_source() -> str | None:
    """The child's code is THIS FILE's text, read exactly once, here, at import time. Every run sends this in-memory string to the child (see the bootstrap below); the file on
    disk is never consulted again, so editing it during or between runs changes nothing for the already-imported engine."""
    path = globals().get("__file__")  # absent when the child execs this source from memory
    if not isinstance(path, str):
        return None
    try:
        with open(path, "rb") as fh:
            return fh.read().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


_RUNNER_SOURCE = _read_runner_source()
RUNNER_SHA256 = hashlib.sha256(_RUNNER_SOURCE.encode("utf-8")).hexdigest() if _RUNNER_SOURCE is not None else None  # recorded so a census can show which runner it used

# The child interpreter is started with `-c <this bootstrap>`: it reads ONE JSON document from stdin ({"runner": <source>, "request": {...}}), compiles the runner source in
# memory and calls its _child_main(request). No file of ours is opened by the child to obtain its own code. (Passed on stdin, not in argv, to stay under ARG_MAX limits.)
_CHILD_BOOTSTRAP = (
    "import sys, json\n"
    "d = json.loads(sys.stdin.buffer.read().decode('utf-8'))\n"
    "g = {'__name__': 'parser_sandbox_child'}\n"
    "exec(compile(d['runner'], '<parser_sandbox_runner>', 'exec', dont_inherit=True), g)\n"
    "g['_child_main'](d['request'])\n"
)


def _after_pin_check() -> None:
    """Test hook, a no-op in production. Called in the engine after every pinned file has been read ONCE and hashed, and before the child is spawned. Tests monkeypatch it to
    mutate files on disk at exactly the moment a TOCTOU attacker would, and show the child still runs the hashed bytes."""
    return None


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
    return {"ok": False, "error": (code + ": " + d) if d else code, "stage": stage, "assurance": ASSURANCE}


class PinManifestError(ValueError):
    """A committed pin manifest is missing, malformed, or names something that is not a pinnable repo file. The message is short and path-free beyond repo-relative names."""


class PinManifest(list):
    """The entries [{"path","sha256"}] of a loaded manifest (it IS a list, so it compares equal to one) plus `runner_sha256`: the manifest's pin of the runner (lowercase hex), or
    None only for a manifest loaded with the test-only flag. A copy made with list() / + / slicing is a plain list and carries no runner pin, which run_pinned_parser refuses."""

    runner_sha256: str | None = None


def _no_dup_keys(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise PinManifestError("duplicate key in manifest JSON")
        d[k] = v
    return d


def load_pin_manifest(repo_root, manifest_rel, *, _test_only_allow_missing_runner: bool = False) -> PinManifest:
    """Read a COMMITTED pin manifest {"pinned_files": [{"path", "sha256"}, ...], "runner_sha256": "<64 hex>"} and return its entries as a PinManifest ([{"path","sha256"}] with
    `.runner_sha256`), validated. The runner digest is REQUIRED (a production run must pin the runner); only a test passing `_test_only_allow_missing_runner=True` may load a
    manifest without it (it then has runner_sha256 None and run_pinned_parser refuses it unless that run is itself flagged test-only).

    Pins are declarations made at review time (production: the committed declaration corpus_derived.parser.pinned_files, built with R1's pin_files when the declaration is written).
    They are NEVER discovered at run time. Raises PinManifestError unless: the manifest is a regular file inside repo_root of at most MAX_MANIFEST_BYTES; its JSON has no duplicate
    keys and is exactly {"pinned_files": [..], "runner_sha256": "<64 hex>"} with 1..MAX_PINNED_FILES entries; each entry is exactly {"path", "sha256"}; each path is a normalised repo-relative posix path
    (no '..', no absolute, no backslash, no './'); each sha256 is 64 hex digits (returned lowercase); no path repeats; and each named file exists as a regular file whose real path
    is inside repo_root and whose size is at most MAX_PINNED_FILE_BYTES. It does not hash anything (the run does, on the bytes it will execute)."""
    try:
        root = os.path.realpath(os.fspath(repo_root))
    except TypeError:
        raise PinManifestError("repo_root not a path") from None
    mrel = _rel_ok(manifest_rel)
    if mrel is None or mrel != manifest_rel:
        raise PinManifestError("manifest path is not a normalised repo-relative path")
    real = os.path.realpath(os.path.join(root, mrel))
    if not _inside(real, root) or not os.path.isfile(real):
        raise PinManifestError("manifest is not a file inside the repo: " + _clean(mrel))
    try:
        with open(real, "rb") as fh:
            raw = fh.read(MAX_MANIFEST_BYTES + 1)
    except OSError:
        raise PinManifestError("manifest unreadable: " + _clean(mrel)) from None
    if len(raw) > MAX_MANIFEST_BYTES:
        raise PinManifestError("manifest larger than %d bytes" % MAX_MANIFEST_BYTES)
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_dup_keys)
    except PinManifestError:
        raise
    except (ValueError, UnicodeDecodeError):
        raise PinManifestError("manifest is not valid JSON") from None
    if isinstance(doc, dict) and set(doc) == {"pinned_files"} and not _test_only_allow_missing_runner:
        raise PinManifestError("manifest does not pin the runner (runner_sha256 is required)")
    allowed = ({"pinned_files"}, {"pinned_files", "runner_sha256"}) if _test_only_allow_missing_runner else ({"pinned_files", "runner_sha256"},)
    if not isinstance(doc, dict) or set(doc) not in allowed or not isinstance(doc["pinned_files"], list):
        raise PinManifestError('manifest must be exactly {"pinned_files": [...], "runner_sha256": "<64 hex>"}')
    runner = doc.get("runner_sha256")
    if "runner_sha256" in doc and (not isinstance(runner, str) or not _SHA256_RE.match(runner)):
        raise PinManifestError("runner_sha256 is not 64 hex digits")
    entries = doc["pinned_files"]
    if not entries or len(entries) > MAX_PINNED_FILES:
        raise PinManifestError("pinned_files must hold 1..%d entries" % MAX_PINNED_FILES)
    out = PinManifest()
    out.runner_sha256 = runner.lower() if runner is not None else None
    seen: set[str] = set()
    for ent in entries:
        if not isinstance(ent, dict) or set(ent) != {"path", "sha256"}:
            raise PinManifestError('each entry must be exactly {"path", "sha256"}')
        path, digest = ent["path"], ent["sha256"]
        rel = _rel_ok(path)
        if rel is None or rel != path:
            raise PinManifestError("not a normalised repo-relative path: " + _clean(path))
        if not isinstance(digest, str) or not _SHA256_RE.match(digest):
            raise PinManifestError("sha256 is not 64 hex digits: " + _clean(rel))
        if rel in seen:
            raise PinManifestError("duplicate path: " + rel)
        seen.add(rel)
        target = os.path.realpath(os.path.join(root, rel))
        if not _inside(target, root) or not os.path.isfile(target):
            raise PinManifestError("pinned file missing or outside the repo: " + rel)
        try:
            size = os.path.getsize(target)
        except OSError:
            raise PinManifestError("pinned file unreadable: " + rel) from None
        if size > MAX_PINNED_FILE_BYTES:
            raise PinManifestError("pinned file larger than %d bytes: %s" % (MAX_PINNED_FILE_BYTES, rel))
        out.append({"path": rel, "sha256": digest.lower()})
    return out


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


def _read_pinned(root: str, pins: dict[str, str]) -> tuple[dict[str, bytes] | None, tuple[str, str] | None]:
    """Read EVERY pinned file exactly once and hash THOSE bytes against the declared digest. Returns ({rel: bytes}, None) or (None, (code, detail)).
    The bytes returned here are the bytes sent to the child and executed; nothing is read from disk again, so there is no window between "checked" and "used"."""
    sources: dict[str, bytes] = {}
    total = 0
    for rel in sorted(pins):
        real = os.path.realpath(os.path.join(root, rel))
        if not _inside(real, root) or not os.path.isfile(real):
            return None, ("pin_missing", rel)
        try:
            with open(real, "rb") as fh:
                data = fh.read(MAX_PINNED_FILE_BYTES + 1)
        except OSError:
            return None, ("pin_missing", rel)
        total += len(data)
        if len(data) > MAX_PINNED_FILE_BYTES or total > 4 * MAX_PINNED_FILE_BYTES:
            return None, ("pin_missing", rel + " (too large to pin)")
        if hashlib.sha256(data).hexdigest() != pins[rel]:
            return None, ("pin_mismatch", rel)
        sources[rel] = data
    return sources, None


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


def run_pinned_parser(repo_root, module_root, pinned_files, file, function, inputs, *, timeout_s=120, max_output_bytes=DEFAULT_MAX_OUTPUT_BYTES, allow_unpinned_runner_for_tests=False) -> dict:
    """Run `function` from the pinned repo file `file` over `inputs` in a guarded child interpreter. See the module docstring for the contract.
    `pinned_files` should be the PinManifest from load_pin_manifest: its runner_sha256 is checked against the runner text before anything is spawned. `allow_unpinned_runner_for_tests`
    is a TEST-ONLY escape (skips that check for hand-built pins); production never passes it."""
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
    sources, bad = _read_pinned(root, pins)  # NOTHING has been executed yet; each file is read once and these bytes are what will run
    if bad is not None:
        return _fail(bad[0], bad[1], "pin")

    if not inputs:
        return _fail("no_inputs", "inputs is empty; a run over nothing proves nothing", "run")

    modules: dict[str, str] = {}
    for rel in sorted(pins):
        name = _module_name_for(rel, mr)
        if name is not None:
            if name in modules:
                return _fail("spawn_failed", "two pinned files map to the module " + name, "spawn")
            modules[name] = rel
    module_name = _module_name_for(file_rel, mr)
    file_abs = os.path.join(root, file_rel)
    runner_src = _RUNNER_SOURCE  # ONE local copy: the text digested below is the text sent to the child
    if runner_src is None:
        return _fail("spawn_failed", "runner source unavailable", "spawn")
    if not allow_unpinned_runner_for_tests:
        pinned_runner = getattr(pinned_files, "runner_sha256", None)
        if not isinstance(pinned_runner, str) or not _SHA256_RE.match(pinned_runner):
            return _fail("runner_unpinned", "the pins carry no runner digest (load them with load_pin_manifest)", "pin")
        if hashlib.sha256(runner_src.encode("utf-8")).hexdigest() != pinned_runner.lower():
            return _fail("runner_unpinned", "the loaded runner source does not match the manifest's runner_sha256", "pin")
    _after_pin_check()

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
            "files": {rel: base64.b64encode(data).decode("ascii") for rel, data in sources.items()},  # the hashed bytes themselves
            "modules": modules,
        }
        request = canonical_json({"runner": runner_src, "request": cfg}).encode("utf-8")
        return _supervise(root, pins, file_rel, len(inputs), request, work, home, tmp, float(timeout_s), int(max_output_bytes), t0)
    finally:
        _rmtree_quiet(scratch)


def _repo_rel_split(root: str, pins: dict[str, str], paths) -> tuple[set[str], set[str]]:
    """Of the absolute paths the child reports, those under repo_root as repo-relative names: (all of them, the ones that are not pinned)."""
    in_repo: set[str] = set()
    unpinned: set[str] = set()
    for p in paths:
        lex = os.path.abspath(p)
        real = os.path.realpath(p)
        if not _inside(lex, root) and not _inside(real, root):
            continue
        rel = os.path.relpath(lex if _inside(lex, root) else real, root).replace(os.sep, "/")
        in_repo.add(rel)
        if rel not in pins or not _inside(real, root):
            unpinned.add(rel)
    return in_repo, unpinned


def _unpinned_failure(root: str, refused=(), unpinned_rel=None) -> dict:
    names = sorted(unpinned_rel) if unpinned_rel is not None else sorted(_repo_rel_split(root, {}, refused)[1])
    if not names:
        names = ["(path not reported)"]
    res = _fail("unpinned_import", ", ".join(names[:2]) + (" (+%d more)" % (len(names) - 2) if len(names) > 2 else ""), "run")
    res["unpinned_files"] = names[:50]  # additive key on this one failure: the refused files, so a caller can show or pin them
    return res


def _rmtree_quiet(path: str) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


def _supervise(root, pins, file_rel, n_inputs, request, work, home, tmp, timeout_s, max_output_bytes, t0) -> dict:
    argv = [sys.executable, *CHILD_FLAGS, "-c", _CHILD_BOOTSTRAP]
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
    refused = env.get("unpinned", [])
    if (not isinstance(violations, list) or not all(isinstance(x, str) for x in violations) or not isinstance(loaded, list) or not all(isinstance(x, str) for x in loaded)
            or not isinstance(refused, list) or not all(isinstance(x, str) for x in refused)):
        return _fail("bad_output", "malformed result envelope", "output")

    # A guard violation wins over everything, including a parser that caught the exception and carried on (the child records it independently).
    for code in violations:
        if code == "unpinned_import":
            return _unpinned_failure(root, refused)
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

    # Second layer: every repo file the child reports as loaded must be pinned. (The first layer is the child refusing an unpinned import or read before it happens.)
    loaded_rel, unpinned = _repo_rel_split(root, pins, loaded)
    if unpinned:
        return _unpinned_failure(root, unpinned_rel=unpinned)
    if file_rel not in loaded_rel:
        return _fail("bad_output", "pinned parser file was not the file loaded", "output")

    return {"ok": True, "outputs": outputs, "loaded_repo_files": sorted(loaded_rel), "elapsed_s": elapsed, "assurance": ASSURANCE}


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Child side (this source is sent on stdin to `python -s -S -P -B -c <bootstrap>` and compiled there). Everything below runs in the guarded interpreter, never in the engine.
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------


class _GuardViolation(BaseException):
    """Raised by a guard. A BaseException on purpose: a parser's `except Exception` cannot swallow it (and the violation is recorded regardless)."""


_VIOLATIONS: list[str] = []
_G: dict = {"root": None, "write_root": None, "touched": set(), "found": set(), "files": {}, "modules": {}, "unpinned": set()}


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


def _under(p: str, root: str) -> bool:
    return p == root or p.startswith(root + os.sep)


def _repo_path(p):
    """The absolute path of `p` if it is (lexically, or after resolving symlinks) inside repo_root; None for a descriptor, a non-path, or a path outside the repo."""
    if isinstance(p, int):
        return None
    try:
        q = os.fspath(p)
        if isinstance(q, bytes):
            q = os.fsdecode(q)
        if "\x00" in q:
            return None
        lex = os.path.abspath(q)
    except (TypeError, ValueError):
        return None
    root = _G["root"]
    if not root:
        return None
    if _under(lex, root):
        return lex
    real = os.path.realpath(lex)
    return real if _under(real, root) else None


def _refuse(path: str):
    """An in-repo path that was not passed to us as pinned bytes: record it and stop. BaseException, so the parser cannot swallow it."""
    _G["unpinned"].add(path)
    _violate("unpinned_import")


def _pinned_bytes(path: str):
    """The passed (hashed) bytes for an in-repo path, or refuse. `path` came from _repo_path."""
    files = _G["files"]
    data = files.get(path)
    if data is None:
        data = files.get(os.path.realpath(path))
        if data is not None:
            path = os.path.realpath(path)
    if data is None:
        _refuse(path)
    _G["touched"].add(path)
    return path, data


def _install_write_guards(builtins, io, _io, posix) -> None:
    real_open = builtins.open

    class _PinnedBytes(io.BytesIO):
        """A read-only file object over the passed bytes of a pinned file."""

        def __init__(self, data, name):
            super().__init__(data)
            self.name = name
            self.mode = "rb"

        def writable(self):
            return False

    def serve_open(file, mode, args, kw):
        """open() of an in-repo path for reading: the passed bytes for a pinned file, a refusal for anything else. None if `file` is not in the repo."""
        path = _repo_path(file)
        if path is None:
            return None
        key, data = _pinned_bytes(path)
        names = ("buffering", "encoding", "errors", "newline", "closefd", "opener")
        opts = dict(zip(names, args))
        opts.update(kw)
        if "b" in mode:
            if any(opts.get(n) is not None for n in ("encoding", "errors", "newline")):
                raise ValueError("binary mode doesn't take an encoding, errors or newline argument")
            return _PinnedBytes(data, key)
        text = io.TextIOWrapper(_PinnedBytes(data, key), encoding=opts.get("encoding") or "utf-8", errors=opts.get("errors") or "strict", newline=opts.get("newline"))
        return text

    def guarded_open(file, mode="r", *args, **kw):
        if "mode" in kw:
            mode = kw.pop("mode")
        if _is_write_mode(mode):
            if not _write_allowed(file):
                _violate("write_attempt")
        else:
            served = serve_open(file, mode if isinstance(mode, str) else "r", args, kw)
            if served is not None:
                return served
        return real_open(file, mode, *args, **kw)

    builtins.open = guarded_open
    io.open = guarded_open
    _io.open = guarded_open

    real_open_code = _io.open_code

    def guarded_open_code(path):
        served = serve_open(path, "rb", (), {})
        if served is not None:
            return served
        return real_open_code(path)

    _io.open_code = guarded_open_code
    io.open_code = guarded_open_code

    real_fileio = _io.FileIO

    class GuardedFileIO(real_fileio):
        def __init__(self, file, mode="r", *args, **kw):
            if _is_write_mode(mode):
                if not _write_allowed(file):
                    _violate("write_attempt")
            else:
                path = _repo_path(file)
                if path is not None:
                    _refuse(path)  # a raw FileIO of a repo file cannot be served from the passed bytes: fail closed
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
            elif kw.get("dir_fd") is None:
                repo = _repo_path(path)
                if repo is not None:
                    _refuse(repo)  # a descriptor-level read of a repo file cannot be served from the passed bytes: fail closed
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


def _make_finder(importlib_machinery):
    """First on sys.meta_path. A module the parent passed as pinned bytes is served from those bytes (the disk copy is never read). Every other name is resolved by the real
    finders exactly as usual, but a result that lands on a FILE inside the repo is an unpinned import and is refused BEFORE it can execute."""

    class PinnedLoader:
        def __init__(self, fullname, path, data, is_pkg):
            self.name, self.path, self.data, self.is_pkg = fullname, path, data, is_pkg

        def create_module(self, spec):
            return None

        def exec_module(self, module):
            exec(self.get_code(self.name), module.__dict__)

        def get_code(self, fullname):
            return compile(self.data, self.path, "exec", dont_inherit=True)

        def get_source(self, fullname):
            return self.data.decode("utf-8", "replace")

        def get_filename(self, fullname):
            return self.path

        def is_package(self, fullname):
            return self.is_pkg

        def get_data(self, path):
            return _pinned_bytes(os.path.abspath(path))[1]

    def spec_for(name, path, data, is_pkg):
        spec = importlib_machinery.ModuleSpec(name, PinnedLoader(name, path, data, is_pkg), origin=path, is_package=is_pkg)
        spec.has_location = True
        if is_pkg:
            spec.submodule_search_locations = [os.path.dirname(path)]
        return spec

    class Finder:
        @classmethod
        def find_spec(cls, name, path=None, target=None):
            rel = _G["modules"].get(name)
            if rel is not None:
                abs_path = _G["root"] + os.sep + rel.replace("/", os.sep)
                data = _G["files"][abs_path]
                _G["found"].add(abs_path)
                return spec_for(name, abs_path, data, rel.rsplit("/", 1)[-1] == "__init__.py")
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
                        in_repo = _repo_path(origin)
                        if in_repo is not None:
                            _refuse(in_repo)  # a repo file that was not passed as pinned bytes: never executed
                    return spec
            return None

    Finder.spec_for = staticmethod(spec_for)
    Finder.PinnedLoader = PinnedLoader
    return Finder


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


def _child_main(cfg) -> None:
    """Entry point of the guarded child. `cfg` is the request the bootstrap parsed from stdin (the runner source itself arrived on the same stdin)."""
    # Everything the guards and the loader need is imported FIRST, before module_root is put on sys.path (so a repo file named like a stdlib module cannot shadow it).
    import builtins
    import importlib
    import importlib.machinery
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
    # The pinned files, as the bytes the parent hashed: keyed by lexical absolute path. This table is the ONLY source of repo code and repo data in this process.
    _G["files"] = {cfg["root"] + os.sep + rel.replace("/", os.sep): base64.b64decode(b64) for rel, b64 in cfg["files"].items()}
    _G["modules"] = dict(cfg["modules"])

    _install_write_guards(builtins, io, _io, posix)
    _install_spawn_guards(subprocess, posix, _posixsubprocess)
    _install_network_guards(socket, _socket)
    sys.modules["ctypes"] = None  # `import ctypes` now raises ImportError: no route to raw syscalls through the standard library
    sys.modules["_ctypes"] = None

    sys.path.insert(0, cfg["module_root_abs"])
    finder = _make_finder(importlib.machinery)
    sys.meta_path.insert(0, finder)

    dumps = json.dumps
    texts: list[str] = []
    error = None
    try:
        try:
            if cfg["module_name"]:
                mod = importlib.import_module(cfg["module_name"])
            else:
                # a pinned file outside module_root: not importable by name, so it is loaded by location, still from the passed bytes
                spec = finder.spec_for("_pinned_parser_module", cfg["file_abs"], _G["files"][cfg["file_abs"]], False)
                _G["found"].add(cfg["file_abs"])
                mod = importlib.util.module_from_spec(spec)
                sys.modules["_pinned_parser_module"] = mod
                spec.loader.exec_module(mod)
            if getattr(mod, "__file__", None) != cfg["file_abs"]:
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
    unpinned = sorted(_G["unpinned"])
    if violations:
        payload = dumps({"v": ENVELOPE_VERSION, "status": "error", "code": "parser_raised", "detail": "guard", "loaded": loaded, "violations": violations, "unpinned": unpinned}, sort_keys=True)
    elif error is not None:
        payload = dumps({"v": ENVELOPE_VERSION, "status": "error", "code": error[0], "detail": error[1], "loaded": loaded, "violations": violations, "unpinned": unpinned}, sort_keys=True)
    else:
        payload = '{"loaded":%s,"outputs":[%s],"status":"ok","unpinned":[],"v":%d,"violations":%s}' % (dumps(loaded), ",".join(texts), ENVELOPE_VERSION, dumps(violations))
    try:
        _emit(result_fd, payload)
    except OSError:
        os._exit(1)
    os._exit(0)  # no atexit handlers or finalisers the parser may have registered


if __name__ == "__main__":
    # The child is NOT started by running this file: it is started with -c and receives this file's source (read once at import by the parent) on stdin.
    sys.stderr.write("parser_sandbox is a library; the child entry point is internal\n")
    sys.exit(2)
