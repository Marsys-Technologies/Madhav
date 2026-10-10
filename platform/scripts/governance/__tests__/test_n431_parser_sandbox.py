"""test_n431_parser_sandbox.py: tests for platform/scripts/governance/parser_sandbox.py (Nikasa N-431, worker R2).

Every test builds a tiny fake repo under tmp_path (a package with a parser module and a helper) and runs the REAL sandbox child over it; nothing here needs a database or a
network. The last class runs the sandbox against the real bg_rules parser (brahmagyan/l0_rules.py) through a tiny pinned adapter, and skips with a stated reason if the real
parser cannot be imported offline.

Each guard has a test that fails if the guard is removed (see the mutation list in the N-431 R2 report): the pin check, the unpinned-import check, the network guard, the
write guard, the wall-clock timeout, and the environment scrub.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_n431_parser_sandbox.py -v
"""
from __future__ import annotations

import ast
import hashlib
import os
import pathlib
import subprocess
import sys
import textwrap

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import parser_sandbox as ps  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]

PKG_INIT = ""
HELPER = textwrap.dedent(
    """
    def double(n):
        return n * 2
    """
)
PARSER = textwrap.dedent(
    """
    from pkg.helper import double

    def parse(item):
        return {"n": double(item["n"]), "echo": item}
    """
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_repo(tmp_path: pathlib.Path, parser_src: str = PARSER, extra: dict | None = None) -> pathlib.Path:
    """A fake repo: lib/pkg/{__init__,helper,parser}.py plus any extra {relpath: text}."""
    root = tmp_path / "repo"
    files = {"lib/pkg/__init__.py": PKG_INIT, "lib/pkg/helper.py": HELPER, "lib/pkg/parser.py": parser_src}
    files.update(extra or {})
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


def pins(root: pathlib.Path, rels) -> list[dict]:
    return [{"path": r, "sha256": hashlib.sha256((root / r).read_bytes()).hexdigest()} for r in rels]


CLOSURE = ["lib/pkg/__init__.py", "lib/pkg/helper.py", "lib/pkg/parser.py"]


def run(root, parser_rel="lib/pkg/parser.py", function="parse", inputs=None, pinned=None, **kw):
    if inputs is None:
        inputs = [{"n": 1}]
    if pinned is None:
        pinned = pins(root, CLOSURE)
    return ps.run_pinned_parser(str(root), "lib", pinned, parser_rel, function, inputs, **kw)


def parser_with(body: str) -> str:
    """A parser module whose parse() runs `body` (indented into the function) with `item` in scope."""
    return "import os, sys, time\n\ndef parse(item):\n" + textwrap.indent(textwrap.dedent(body).strip("\n"), "    ") + "\n"


class PopenSpy:
    """Replaces parser_sandbox.subprocess.Popen to record every child the engine starts (and lets the real one through)."""

    def __init__(self, monkeypatch):
        self.started = []
        real = subprocess.Popen
        spy = self

        class Spy(real):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                spy.started.append(self)

        monkeypatch.setattr(ps.subprocess, "Popen", Spy)


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# happy path, shape, determinism
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------


class TestHappyPath:
    def test_outputs_in_input_order_and_loaded_files_equal_the_pinned_set(self, tmp_path):
        root = make_repo(tmp_path)
        inputs = [{"n": i} for i in (5, 1, 4, 2, 3)]
        r = run(root, inputs=inputs)
        assert r["ok"] is True, r
        assert r["outputs"] == [{"n": i * 2, "echo": {"n": i}} for i in (5, 1, 4, 2, 3)]
        assert r["loaded_repo_files"] == sorted(CLOSURE)
        assert isinstance(r["elapsed_s"], float) and r["elapsed_s"] > 0
        assert set(r) == {"ok", "outputs", "loaded_repo_files", "elapsed_s"}

    def test_parser_returning_an_empty_list_for_an_input_is_still_ok(self, tmp_path):
        """Only the zero-INPUT case fails (no_inputs); a parser may legitimately yield nothing for an input."""
        r = run(make_repo(tmp_path, parser_with("return []")), inputs=[{"n": 1}, {"n": 2}])
        assert r["ok"] is True and r["outputs"] == [[], []]

    def test_two_runs_are_byte_identical(self, tmp_path):
        src = parser_with(
            """
            return {"order": list({"alpha", "beta", "gamma", "delta", "epsilon", "zeta"}), "n": item["n"], "f": 0.1 + 0.2}
            """
        )
        root = make_repo(tmp_path, src)
        inputs = [{"n": i} for i in range(6)]
        a = run(root, inputs=inputs)
        b = run(root, inputs=inputs)
        c = run(root, inputs=inputs)
        assert a["ok"] and b["ok"] and c["ok"]
        ja, jb, jc = (ps.canonical_json(x["outputs"]) for x in (a, b, c))
        assert ja == jb == jc
        assert a["loaded_repo_files"] == b["loaded_repo_files"]

    def test_generator_result_is_materialised(self, tmp_path):
        root = make_repo(tmp_path, parser_with("return (item['n'] + k for k in range(3))"))
        r = run(root, inputs=[{"n": 10}])
        assert r["ok"] and r["outputs"] == [[10, 11, 12]]

    def test_stdout_noise_from_the_parser_cannot_corrupt_the_result(self, tmp_path):
        root = make_repo(tmp_path, parser_with("print('hello'); os.write(1, b'garbage'); sys.stdout.write('x'); return item"))
        r = run(root, inputs=[{"n": 1}])
        assert r["ok"] and r["outputs"] == [{"n": 1}]

    def test_file_outside_module_root_is_loaded_by_location(self, tmp_path):
        root = make_repo(tmp_path, extra={"tools/standalone.py": "def parse(item):\n    return {'s': item['n'] + 1}\n"})
        r = ps.run_pinned_parser(str(root), "lib", pins(root, ["tools/standalone.py"]), "tools/standalone.py", "parse", [{"n": 1}])
        assert r["ok"] and r["outputs"] == [{"s": 2}] and r["loaded_repo_files"] == ["tools/standalone.py"]

    def test_allowed_scratch_write_inside_the_temp_tree_works(self, tmp_path):
        """The write guard is not a blanket ban: the parser may use its own scratch cwd."""
        src = parser_with(
            """
            with open("scratch.txt", "w") as fh:
                fh.write("hi")
            import tempfile
            with tempfile.NamedTemporaryFile("w", delete=True) as t:
                t.write("x")
            return open("scratch.txt").read()
            """
        )
        r = run(make_repo(tmp_path, src))
        assert r["ok"], r
        assert r["outputs"] == ["hi"]

    def test_scratch_tree_is_removed_after_the_run(self, tmp_path, monkeypatch):
        t = tmp_path / "tmproot"
        t.mkdir()
        monkeypatch.setattr(ps.tempfile, "tempdir", str(t))
        assert run(make_repo(tmp_path))["ok"]
        assert list(t.iterdir()) == []


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# the pin check
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------


class TestPinCheck:
    def test_edited_file_after_hashing_runs_nothing(self, tmp_path, monkeypatch):
        root = make_repo(tmp_path)
        pinned = pins(root, CLOSURE)  # hashed first
        side = tmp_path / "side_effect.txt"
        edited = PARSER + "\nopen(%r, 'w').write('ran')\n" % str(side)
        (root / "lib/pkg/parser.py").write_text(edited, encoding="utf-8")  # edited after hashing
        spy = PopenSpy(monkeypatch)
        r = run(root, pinned=pinned)
        assert r["ok"] is False and r["stage"] == "pin"
        assert r["error"].startswith("pin_mismatch: lib/pkg/parser.py")
        assert spy.started == []  # no child was even started
        assert not side.exists()

    def test_mismatch_in_the_helper_is_caught_too(self, tmp_path, monkeypatch):
        root = make_repo(tmp_path)
        pinned = pins(root, CLOSURE)
        (root / "lib/pkg/helper.py").write_text(HELPER.replace("n * 2", "n * 3"), encoding="utf-8")
        spy = PopenSpy(monkeypatch)
        r = run(root, pinned=pinned)
        assert r["ok"] is False and r["stage"] == "pin" and r["error"].startswith("pin_mismatch: lib/pkg/helper.py")
        assert spy.started == []

    def test_missing_pinned_file(self, tmp_path, monkeypatch):
        root = make_repo(tmp_path)
        pinned = pins(root, CLOSURE) + [{"path": "lib/pkg/gone.py", "sha256": "0" * 64}]
        spy = PopenSpy(monkeypatch)
        r = run(root, pinned=pinned)
        assert r["ok"] is False and r["stage"] == "pin" and r["error"].startswith("pin_missing: lib/pkg/gone.py")
        assert spy.started == []

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda p: [],  # nothing declared
            lambda p: [{"path": "lib/pkg/parser.py", "sha256": "xyz"}],  # bad digest
            lambda p: [{"path": "../outside.py", "sha256": "0" * 64}],  # escapes the repo
            lambda p: [{"path": "/etc/hosts", "sha256": "0" * 64}],  # absolute
            lambda p: [{"sha256": "0" * 64}],  # no path
            lambda p: [d for d in p if d["path"] != "lib/pkg/parser.py"],  # the parser file itself is not pinned
        ],
    )
    def test_malformed_or_incomplete_declarations_are_pin_missing(self, tmp_path, monkeypatch, mutate):
        root = make_repo(tmp_path)
        spy = PopenSpy(monkeypatch)
        r = run(root, pinned=mutate(pins(root, CLOSURE)))
        assert r["ok"] is False and r["stage"] == "pin" and r["error"].startswith("pin_missing")
        assert spy.started == []

    def test_symlink_that_escapes_the_repo_is_refused(self, tmp_path):
        root = make_repo(tmp_path)
        outside = tmp_path / "outside_helper.py"
        outside.write_text(HELPER, encoding="utf-8")
        (root / "lib/pkg/helper.py").unlink()
        (root / "lib/pkg/helper.py").symlink_to(outside)
        r = run(root)
        assert r["ok"] is False and r["stage"] == "pin" and r["error"].startswith("pin_missing")

    def test_file_changed_while_the_child_ran_is_refused(self, tmp_path, monkeypatch):
        root = make_repo(tmp_path, parser_with("time.sleep(1.0)\nreturn item"))
        pinned = pins(root, CLOSURE)
        real = subprocess.Popen

        class Racing(real):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                (root / "lib/pkg/helper.py").write_text(HELPER + "\n# touched mid-run\n", encoding="utf-8")

        monkeypatch.setattr(ps.subprocess, "Popen", Racing)
        r = run(root, pinned=pinned)
        assert r["ok"] is False and r["stage"] == "pin"
        assert r["error"].startswith("pin_mismatch: lib/pkg/helper.py") and "changed during the run" in r["error"]


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# the loaded-file closure
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------


class TestUnpinnedImport:
    def test_unpinned_helper_import_is_refused_even_though_the_parser_produced_output(self, tmp_path):
        root = make_repo(tmp_path)
        r = run(root, pinned=pins(root, ["lib/pkg/__init__.py", "lib/pkg/parser.py"]))  # helper.py is NOT pinned
        assert r["ok"] is False and r["stage"] == "run"
        assert r["error"] == "unpinned_import: lib/pkg/helper.py" and r["unpinned_files"] == ["lib/pkg/helper.py"]

    def test_many_unpinned_files_are_all_listed_in_unpinned_files(self, tmp_path):
        root = make_repo(tmp_path)
        r = run(root, pinned=pins(root, ["lib/pkg/parser.py"]))
        assert r["ok"] is False and r["unpinned_files"] == ["lib/pkg/__init__.py", "lib/pkg/helper.py"]
        assert r["error"] == "unpinned_import: lib/pkg/__init__.py, lib/pkg/helper.py"

    def test_unpinned_package_init_is_refused(self, tmp_path):
        root = make_repo(tmp_path)
        r = run(root, pinned=pins(root, ["lib/pkg/helper.py", "lib/pkg/parser.py"]))
        assert r["ok"] is False and r["error"] == "unpinned_import: lib/pkg/__init__.py"

    def test_lazy_import_inside_the_function_is_caught(self, tmp_path):
        src = parser_with("from pkg import late\nreturn late.VALUE")
        root = make_repo(tmp_path, src, extra={"lib/pkg/late.py": "VALUE = 7\n"})
        r = run(root)  # late.py never pinned
        assert r["ok"] is False and r["error"] == "unpinned_import: lib/pkg/late.py"

    def test_reading_an_unpinned_repo_data_file_is_caught(self, tmp_path):
        src = parser_with("return open(%r).read()" % str(tmp_path / "repo" / "data" / "table.txt"))
        root = make_repo(tmp_path, src, extra={"data/table.txt": "secret table\n"})
        r = run(root)
        assert r["ok"] is False and r["error"] == "unpinned_import: data/table.txt"

    def test_pinning_the_data_file_makes_the_same_parser_ok(self, tmp_path):
        src = parser_with("return open(%r).read()" % str(tmp_path / "repo" / "data" / "table.txt"))
        root = make_repo(tmp_path, src, extra={"data/table.txt": "secret table\n"})
        r = run(root, pinned=pins(root, CLOSURE + ["data/table.txt"]))
        assert r["ok"] and r["outputs"] == ["secret table\n"] and "data/table.txt" in r["loaded_repo_files"]

    def test_a_pinned_file_that_is_never_loaded_is_allowed(self, tmp_path):
        """Over-pinning is harmless: loaded_repo_files is a subset of the pinned set."""
        root = make_repo(tmp_path, extra={"lib/pkg/unused.py": "X = 1\n"})
        r = run(root, pinned=pins(root, CLOSURE + ["lib/pkg/unused.py"]))
        assert r["ok"] and "lib/pkg/unused.py" not in r["loaded_repo_files"]

    def test_stdlib_modules_are_not_reported_as_repo_files(self, tmp_path):
        r = run(make_repo(tmp_path, "import json, re, uuid, hashlib\n" + parser_with("return item")))
        assert r["ok"] and r["loaded_repo_files"] == ["lib/pkg/__init__.py", "lib/pkg/parser.py"]  # no stdlib file, and helper.py (never imported) is absent


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# the guards
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------


NETWORK_BODIES = {
    "socket_ctor": "import socket\ns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\nreturn 'connected'",
    "create_connection": "import socket\nsocket.create_connection(('example.invalid', 80), timeout=1)\nreturn 'connected'",
    "getaddrinfo": "import socket\nreturn socket.getaddrinfo('example.invalid', 80)",
    "urlopen": "import urllib.request\nreturn urllib.request.urlopen('http://example.invalid/', timeout=1).read().decode()",
    "http_client": "import http.client\nc = http.client.HTTPConnection('example.invalid', 80, timeout=1)\nc.request('GET', '/')\nreturn 'sent'",
    "raw__socket": "import _socket\n_socket.socket()\nreturn 'raw'",
    "socketpair": "import socket\nsocket.socketpair()\nreturn 'pair'",
    "swallowed": "import socket\ntry:\n    socket.socket()\nexcept BaseException:\n    pass\nreturn 'carried on'",
}


class TestNetworkGuard:
    @pytest.mark.parametrize("name", sorted(NETWORK_BODIES))
    def test_network_attempt_is_blocked_and_never_a_successful_result(self, tmp_path, name):
        r = run(make_repo(tmp_path, parser_with(NETWORK_BODIES[name])))
        assert r["ok"] is False, r
        assert r["error"].startswith("network_attempt") and r["stage"] == "run"
        assert "outputs" not in r


class TestWriteGuard:
    def _case(self, tmp_path, body):
        r = run(make_repo(tmp_path, parser_with(body)))
        assert r["ok"] is False, r
        assert r["error"].startswith("write_attempt") and r["stage"] == "run"

    def test_open_for_writing_outside_the_temp_tree(self, tmp_path):
        target = tmp_path / "evil.txt"
        self._case(tmp_path, "open(%r, 'w').write('x')\nreturn 1" % str(target))
        assert not target.exists()

    @pytest.mark.parametrize("mode", ["a", "x", "r+", "wb", "ab"])
    def test_other_write_modes(self, tmp_path, mode):
        target = tmp_path / "evil2.txt"
        target.write_text("keep", encoding="utf-8")
        self._case(tmp_path, "open(%r, %r)\nreturn 1" % (str(target), mode))
        assert target.read_text(encoding="utf-8") == "keep"

    def test_os_open_with_create_flag(self, tmp_path):
        target = tmp_path / "evil3.txt"
        self._case(tmp_path, "os.open(%r, os.O_WRONLY | os.O_CREAT)\nreturn 1" % str(target))
        assert not target.exists()

    def test_pathlib_write_text(self, tmp_path):
        target = tmp_path / "evil4.txt"
        self._case(tmp_path, "import pathlib\npathlib.Path(%r).write_text('x')\nreturn 1" % str(target))
        assert not target.exists()

    def test_mkdir_remove_rename_of_outside_paths(self, tmp_path):
        victim = tmp_path / "victim.txt"
        victim.write_text("keep", encoding="utf-8")
        newdir = tmp_path / "newdir"
        for body in (
            "os.mkdir(%r)\nreturn 1" % str(newdir),
            "os.remove(%r)\nreturn 1" % str(victim),
            "os.rename(%r, %r)\nreturn 1" % (str(victim), str(tmp_path / "moved.txt")),
            "import shutil\nshutil.copy(%r, %r)\nreturn 1" % (str(victim), str(tmp_path / "copied.txt")),
        ):
            self._case(tmp_path, body)
        assert victim.read_text(encoding="utf-8") == "keep"
        assert not newdir.exists() and not (tmp_path / "moved.txt").exists() and not (tmp_path / "copied.txt").exists()

    def test_write_inside_the_repo_is_refused(self, tmp_path):
        root_dir = tmp_path / "repo"
        self._case(tmp_path, "open(%r, 'w').write('x')\nreturn 1" % str(root_dir / "lib" / "pkg" / "dropped.py"))
        assert not (root_dir / "lib" / "pkg" / "dropped.py").exists()

    def test_io_fileio_write(self, tmp_path):
        target = tmp_path / "evil5.txt"
        self._case(tmp_path, "import io\nio.FileIO(%r, 'w')\nreturn 1" % str(target))
        assert not target.exists()

    def test_swallowed_write_attempt_still_fails(self, tmp_path):
        target = tmp_path / "evil6.txt"
        self._case(tmp_path, "try:\n    open(%r, 'w')\nexcept BaseException:\n    pass\nreturn 'carried on'" % str(target))

    def test_dev_null_is_writable(self, tmp_path):
        r = run(make_repo(tmp_path, parser_with("open(os.devnull, 'w').write('x')\nreturn 'ok'")))
        assert r["ok"] and r["outputs"] == ["ok"]


class TestSpawnGuard:
    @pytest.mark.parametrize(
        "body",
        [
            "import subprocess\nsubprocess.run(['echo', 'hi'])\nreturn 1",
            "import subprocess\nsubprocess.Popen(['echo', 'hi'])\nreturn 1",
            "import subprocess\nreturn subprocess.check_output(['echo', 'hi']).decode()",
            "os.system('echo hi')\nreturn 1",
            "os.popen('echo hi')\nreturn 1",
            "os.fork()\nreturn 1",
            "os.execv('/bin/echo', ['echo', 'hi'])\nreturn 1",
            "os.posix_spawn('/bin/echo', ['echo', 'hi'], {})\nreturn 1",
            "os.spawnv(os.P_NOWAIT, '/bin/echo', ['echo', 'hi'])\nreturn 1",
            "import subprocess\ntry:\n    subprocess.run(['echo'])\nexcept BaseException:\n    pass\nreturn 'carried on'",
        ],
    )
    def test_process_spawning_is_blocked(self, tmp_path, body):
        r = run(make_repo(tmp_path, parser_with(body)))
        assert r["ok"] is False, r
        assert r["error"].startswith("spawn_attempt") and r["stage"] == "run"

    def test_ctypes_is_not_importable(self, tmp_path):
        r = run(make_repo(tmp_path, parser_with("import ctypes\nreturn 1")))
        assert r["ok"] is False and r["error"] == "parser_raised: index=0 type=ModuleNotFoundError"  # an ImportError subclass


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# limits, failure vocabulary
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------


class TestTimeout:
    def test_sleeping_parser_is_killed_by_the_wall_clock_and_only_that_child(self, tmp_path, monkeypatch):
        sibling = subprocess.Popen(["sleep", "60"])
        try:
            spy = PopenSpy(monkeypatch)
            r = run(make_repo(tmp_path, parser_with("time.sleep(20)\nreturn 1")), timeout_s=1.5)
            assert r["ok"] is False and r["stage"] == "run" and r["error"].startswith("timeout")
            assert len(spy.started) == 1
            assert spy.started[0].poll() is not None  # the child we started is dead
            assert sibling.poll() is None  # an unrelated process is untouched
        finally:
            sibling.kill()
            sibling.wait()

    def test_busy_loop_is_stopped_too(self, tmp_path):
        r = run(make_repo(tmp_path, parser_with("while True:\n    pass")), timeout_s=1)
        assert r["ok"] is False and r["error"].startswith("timeout")

    def test_returns_promptly_after_the_limit(self, tmp_path):
        import time

        t0 = time.monotonic()
        r = run(make_repo(tmp_path, parser_with("time.sleep(20)\nreturn 1")), timeout_s=1)
        assert r["ok"] is False and time.monotonic() - t0 < 10


class TestNoInputs:
    """SS N-431 R2 finding (3): zero inputs used to return ok True, a false-PASS route (nothing compared, nothing proved)."""

    def test_empty_inputs_is_a_failure_with_the_fixed_code_at_stage_run(self, tmp_path):
        r = run(make_repo(tmp_path), inputs=[])
        assert r["ok"] is False and r["stage"] == "run" and r["error"].startswith("no_inputs")
        assert "outputs" not in r and "loaded_repo_files" not in r

    def test_nothing_is_spawned_for_zero_inputs(self, tmp_path, monkeypatch):
        spy = PopenSpy(monkeypatch)
        assert run(make_repo(tmp_path), inputs=[])["error"].startswith("no_inputs")
        assert spy.started == []

    def test_a_pin_problem_is_still_reported_first(self, tmp_path):
        root = make_repo(tmp_path)
        r = run(root, inputs=[], pinned=pins(root, CLOSURE)[:1])  # parser.py not pinned
        assert r["stage"] == "pin" and r["error"].startswith("pin_missing")

    def test_no_inputs_is_in_the_error_vocabulary(self):
        assert "no_inputs" in ps.ERROR_CODES


class TestFailureVocabulary:
    def test_parser_raising_on_input_3_reports_index_and_type_only(self, tmp_path):
        src = parser_with("if item['n'] == 3:\n    raise ValueError('secret /etc/passwd token=abc')\nreturn item")
        r = run(make_repo(tmp_path, src), inputs=[{"n": i} for i in range(6)])
        assert r == {"ok": False, "error": "parser_raised: index=3 type=ValueError", "stage": "run"}
        assert "secret" not in r["error"] and "/etc" not in r["error"]

    def test_exception_in_the_parser_at_import_time_has_index_minus_one(self, tmp_path):
        r = run(make_repo(tmp_path, "raise RuntimeError('boom')\n"))
        assert r["ok"] is False and r["error"] == "parser_raised: index=-1 type=RuntimeError"

    def test_missing_function(self, tmp_path):
        r = run(make_repo(tmp_path), function="nope")
        assert r["ok"] is False and r["error"] == "parser_raised: index=-1 type=AttributeError"

    def test_parser_calling_sys_exit_is_a_parser_raised(self, tmp_path):
        r = run(make_repo(tmp_path, parser_with("sys.exit(0)")))
        assert r["ok"] is False and r["error"] == "parser_raised: index=0 type=SystemExit"

    def test_abnormal_exit_is_nonzero_exit(self, tmp_path):
        r = run(make_repo(tmp_path, parser_with("os._exit(3)")))
        assert r["ok"] is False and r["error"] == "nonzero_exit: rc=3" and r["stage"] == "run"

    def test_oversized_output_is_refused(self, tmp_path):
        r = run(make_repo(tmp_path, parser_with("return 'x' * 1_000_000")), max_output_bytes=10_000)
        assert r["ok"] is False and r["stage"] == "output" and r["error"].startswith("output_too_large")
        assert "outputs" not in r

    def test_output_under_the_cap_is_fine(self, tmp_path):
        r = run(make_repo(tmp_path, parser_with("return 'x' * 1000")), max_output_bytes=10_000)
        assert r["ok"] and len(r["outputs"][0]) == 1000

    @pytest.mark.parametrize("expr", ["{1, 2}", "float('nan')", "object()", "{(1, 2): 3, 'a': 1, 2: 'b'}"])
    def test_result_that_is_not_canonical_json_is_bad_output(self, tmp_path, expr):
        r = run(make_repo(tmp_path, parser_with("return " + expr)))
        assert r["ok"] is False and r["stage"] == "output" and r["error"].startswith("bad_output: index=0")

    def test_spawn_failed_when_the_interpreter_cannot_start(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ps.sys, "executable", str(tmp_path / "no_such_python"))
        r = run(make_repo(tmp_path))
        assert r["ok"] is False and r["stage"] == "spawn" and r["error"].startswith("spawn_failed")
        assert str(tmp_path) not in r["error"]

    @pytest.mark.parametrize(
        "kw",
        [
            {"function": "not an identifier"},
            {"inputs": "nope"},
            {"inputs": [{"a": {1, 2}}]},
            {"timeout_s": 0},
            {"max_output_bytes": 0},
        ],
    )
    def test_bad_arguments_are_spawn_failed(self, tmp_path, kw):
        r = run(make_repo(tmp_path), **kw)
        assert r["ok"] is False and r["stage"] == "spawn" and r["error"].startswith("spawn_failed")

    def test_bad_repo_root_and_module_root(self, tmp_path):
        root = make_repo(tmp_path)
        r = ps.run_pinned_parser(str(tmp_path / "nowhere"), "lib", pins(root, CLOSURE), CLOSURE[2], "parse", [])
        assert r["ok"] is False and r["error"].startswith("spawn_failed")
        r = ps.run_pinned_parser(str(root), "../escape", pins(root, CLOSURE), CLOSURE[2], "parse", [])
        assert r["ok"] is False and r["error"].startswith("spawn_failed")

    def test_every_error_code_in_the_contract_exists(self):
        assert set(ps.ERROR_CODES) == {
            "pin_missing", "pin_mismatch", "unpinned_import", "spawn_failed", "timeout", "nonzero_exit",
            "bad_output", "output_too_large", "parser_raised", "network_attempt", "write_attempt", "spawn_attempt", "no_inputs",
        }


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# isolation of the environment and cwd
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------


class TestEnvironmentScrub:
    def test_child_environment_is_exactly_the_allowlist(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PGPASSWORD", "hunter2")
        monkeypatch.setenv("PGHOST", "db.internal")
        monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret")
        monkeypatch.setenv("SECRET_TOKEN", "s3cr3t")
        monkeypatch.setenv("HOME", "/parent/home/dir")
        monkeypatch.setenv("PYTHONPATH", str(tmp_path))
        r = run(make_repo(tmp_path, parser_with("return dict(os.environ)")))
        assert r["ok"], r
        env = r["outputs"][0]
        assert set(env) - set(ps.OS_ADDED_ENV_KEYS) == set(ps.CHILD_ENV_KEYS)
        assert not [k for k in env if k.startswith("PG")] and "DATABASE_URL" not in env
        assert env["HOME"] != "/parent/home/dir" and os.path.basename(env["HOME"]) == "home"
        assert env["PYTHONHASHSEED"] == "0" and env["TZ"] == "UTC"
        blob = repr(env)
        for secret in ("hunter2", "db.internal", "postgres://", "ghp_secret", "s3cr3t", "/parent/home/dir", str(tmp_path / "repo")):
            assert secret not in blob

    def test_hash_seed_is_honoured_and_bytecode_is_not_written(self, tmp_path):
        root = make_repo(tmp_path, parser_with("return {'h': hash('abc'), 'dwb': sys.dont_write_bytecode, 'isolated_flags': [sys.flags.no_user_site, sys.flags.no_site, sys.flags.safe_path]}"))
        a, b = run(root), run(root)
        assert a["ok"] and a["outputs"] == b["outputs"]
        assert a["outputs"][0]["dwb"] is True and a["outputs"][0]["isolated_flags"] == [1, 1, True]
        assert not list(root.rglob("__pycache__"))

    def test_cwd_is_a_fresh_empty_dir_and_the_parents_files_are_invisible(self, tmp_path, monkeypatch):
        pcwd = tmp_path / "parent_cwd"
        pcwd.mkdir()
        (pcwd / "marker.txt").write_text("parent", encoding="utf-8")
        monkeypatch.chdir(pcwd)
        src = parser_with("return {'cwd': os.getcwd(), 'ls': sorted(os.listdir('.')), 'rel': os.path.exists('marker.txt'), 'home_ls': sorted(os.listdir(os.environ['HOME']))}")
        r = run(make_repo(tmp_path, src))
        assert r["ok"], r
        out = r["outputs"][0]
        assert out["ls"] == [] and out["rel"] is False and out["home_ls"] == []
        assert os.path.realpath(out["cwd"]) != os.path.realpath(str(pcwd))
        assert not os.path.exists(out["cwd"])  # gone after the run

    def test_documented_limit_absolute_reads_are_not_restricted(self, tmp_path):
        """Honest limit (module docstring): READS are not confined; only writes, spawns and sockets are guarded."""
        outside = tmp_path / "readable.txt"
        outside.write_text("visible", encoding="utf-8")
        r = run(make_repo(tmp_path, parser_with("return open(%r).read()" % str(outside))))
        assert r["ok"] and r["outputs"] == ["visible"]

    def test_inherited_descriptors_are_not_passed(self, tmp_path):
        leak = open(tmp_path / "leak.txt", "w")
        try:
            fd = leak.fileno()
            os.set_inheritable(fd, True)
            src = parser_with("fds = []\nfor n in range(3, 64):\n    try:\n        os.fstat(n)\n        fds.append(n)\n    except OSError:\n        pass\nreturn fds")
            r = run(make_repo(tmp_path, src))
            assert r["ok"], r
            assert fd not in r["outputs"][0]
        finally:
            leak.close()


class TestModuleHygiene:
    def test_module_parses_under_the_311_grammar(self):
        src = pathlib.Path(ps.__file__).read_text(encoding="utf-8")
        ast.parse(src, feature_version=(3, 11))

    def test_interpreter_flags_do_not_include_E_or_I(self):
        """-I/-E would make the interpreter ignore PYTHONHASHSEED (see the module docstring)."""
        assert "-I" not in ps.CHILD_FLAGS and "-E" not in ps.CHILD_FLAGS
        assert {"-s", "-S", "-P", "-B"} <= set(ps.CHILD_FLAGS)

    def test_canonical_json_is_sorted_compact_ascii(self):
        assert ps.canonical_json({"b": 1, "a": ["é", 2.5]}) == '{"a":["\\u00e9",2.5],"b":1}'
        with pytest.raises(ValueError):
            ps.canonical_json({"a": float("nan")})


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# the real bg_rules parser (offline smoke test, adapter-based)
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------

SIDECAR = "platform/python-sidecar"
ADAPTER_REL = "platform/scripts/governance/__tests__/_n431_rules_adapter.py"
REAL_IDS = ["bphs", "saravali"]
REAL_CHUNKS = [
    {"id": "11111111-1111-4111-8111-111111111111", "text_id": "bphs", "verse_ref": "1.1",
     "content_en": "If Jupiter is placed in the seventh house from the Lagna, the native will be learned and wealthy. Saturn in the tenth house gives power to the native."},
    {"id": "22222222-2222-4222-8222-222222222222", "text_id": "saravali", "verse_ref": "2.3",
     "content_en": "If the Moon is in the tenth house from the Lagna, the native will be famous and honoured by kings."},
    {"id": "33333333-3333-4333-8333-333333333333", "text_id": "bphs", "verse_ref": "3.4",
     "content_en": "A note about the weather with no astrological content at all."},
]


def _close_over_real_parser(repo_root: pathlib.Path, inputs):
    """Discover the real parser's repo-local import closure by running it and pinning what the sandbox reports as unpinned, until it is accepted. Returns (result, pinned)."""
    pinned: list[dict] = []
    for _ in range(60):
        r = ps.run_pinned_parser(str(repo_root), SIDECAR, pinned, ADAPTER_REL, "run_chunk", inputs, timeout_s=120)
        if r["ok"]:
            return r, pinned
        if r["error"].startswith("unpinned_import: "):
            new = r["unpinned_files"]
        elif r["error"].startswith("pin_missing: file is not one of pinned_files") or not pinned:
            new = [ADAPTER_REL]
        else:
            return r, pinned
        pinned = pinned + [{"path": n, "sha256": hashlib.sha256((repo_root / n).read_bytes()).hexdigest()} for n in new if n not in {d["path"] for d in pinned}]
    return r, pinned


class TestRealParser:
    @pytest.fixture()
    def inputs(self):
        if not (REPO_ROOT / SIDECAR / "brahmagyan" / "l0_rules.py").is_file() or not (REPO_ROOT / ADAPTER_REL).is_file():
            pytest.skip("real bg_rules parser or the adapter is not present in this checkout")
        return [{"chunk": c, "valid_text_ids": REAL_IDS} for c in REAL_CHUNKS]

    def test_real_parser_runs_offline_in_the_sandbox_and_is_reproducible(self, inputs):
        r, pinned = _close_over_real_parser(REPO_ROOT, inputs)
        if not r["ok"] and r["error"].startswith("parser_raised: index=-1"):
            pytest.skip("the real parser cannot be imported offline in this environment: " + r["error"])
        assert r["ok"], r
        assert [len(o) for o in r["outputs"]] == [3, 2, 0]  # two chunks with rules, one with none
        assert {row["text_id"] for row in r["outputs"][0]} == {"bphs"} and {row["text_id"] for row in r["outputs"][1]} == {"saravali"}
        assert all(row["extracted_by"] == "python_regex_v2" for row in r["outputs"][0])
        # the closure the sandbox saw is exactly what had to be pinned (nothing pinned for nothing)
        assert r["loaded_repo_files"] == sorted(d["path"] for d in pinned)
        assert f"{SIDECAR}/brahmagyan/l0_rules.py" in r["loaded_repo_files"]
        assert f"{SIDECAR}/brahmagyan/l0_semantic_release_v1.json" in r["loaded_repo_files"]  # a DATA file the parser reads at import is part of the closure
        assert not any(f.endswith("parser_sandbox.py") for f in r["loaded_repo_files"])  # the runner itself is not "loaded repo code"
        # reproducible: a second run, byte for byte
        again = ps.run_pinned_parser(str(REPO_ROOT), SIDECAR, pinned, ADAPTER_REL, "run_chunk", inputs, timeout_s=120)
        assert again["ok"] and ps.canonical_json(again["outputs"]) == ps.canonical_json(r["outputs"])

    def test_real_parser_matches_the_parser_run_in_process(self, inputs):
        """The sandboxed rows equal the rows the same function yields in this process (same code, same answer), apart from the child's fixed hash seed."""
        r, _ = _close_over_real_parser(REPO_ROOT, inputs)
        if not r["ok"]:
            pytest.skip("real parser not runnable offline here: " + r["error"])
        sidecar = str(REPO_ROOT / SIDECAR)
        sys.path.insert(0, sidecar)
        try:
            from brahmagyan.l0_rules import extract_rules_from_chunk  # noqa: E402
        finally:
            sys.path.remove(sidecar)
        local = [list(extract_rules_from_chunk(c, set(REAL_IDS))) for c in REAL_CHUNKS]
        assert ps.canonical_json(local) == ps.canonical_json(r["outputs"])
