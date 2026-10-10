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
import json
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


def write_manifest(root: pathlib.Path, rels, name: str = "pins.json") -> str:
    """The declaration step: hash the files NOW and write a pin manifest into the fake repo (what R1's pin_files + a committed declaration do in production)."""
    entries = [{"path": r, "sha256": hashlib.sha256((root / r).read_bytes()).hexdigest()} for r in rels]
    (root / name).write_text(json.dumps({"pinned_files": entries}), encoding="utf-8")
    return name


def pins(root: pathlib.Path, rels) -> list[dict]:
    """Fixture pins, built the production way: from a manifest file the test wrote, read back through load_pin_manifest (never discovered at call time)."""
    return ps.load_pin_manifest(str(root), write_manifest(root, rels))


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
        assert set(r) == {"ok", "outputs", "loaded_repo_files", "elapsed_s", "assurance"}

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
        pinned = pins(root, CLOSURE)  # declared while helper.py was a real in-repo file (load_pin_manifest itself refuses a pin that already escapes: see TestPinManifest)
        outside = tmp_path / "outside_helper.py"
        outside.write_text(HELPER, encoding="utf-8")
        (root / "lib/pkg/helper.py").unlink()
        (root / "lib/pkg/helper.py").symlink_to(outside)
        r = run(root, pinned=pinned)
        assert r["ok"] is False and r["stage"] == "pin" and r["error"].startswith("pin_missing")


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# the loaded-file closure
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------


class TestUnpinnedImport:
    def test_unpinned_helper_import_is_refused_even_though_the_parser_produced_output(self, tmp_path):
        root = make_repo(tmp_path)
        r = run(root, pinned=pins(root, ["lib/pkg/__init__.py", "lib/pkg/parser.py"]))  # helper.py is NOT pinned
        assert r["ok"] is False and r["stage"] == "run"
        assert r["error"] == "unpinned_import: lib/pkg/helper.py" and r["unpinned_files"] == ["lib/pkg/helper.py"]

    def test_the_first_refused_file_is_listed_and_nothing_after_it_runs(self, tmp_path):
        """Changed with the TOCTOU fix (SS finding 1): an unpinned import is now refused BEFORE it executes, so the run stops at the first one (the package __init__ here) instead of
        running on to discover the whole closure. unpinned_files lists what was refused; a caller pins it and retries."""
        root = make_repo(tmp_path)
        r = run(root, pinned=pins(root, ["lib/pkg/parser.py"]))
        assert r["ok"] is False and r["unpinned_files"] == ["lib/pkg/__init__.py"]
        assert r["error"] == "unpinned_import: lib/pkg/__init__.py"

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
# each guard layer, isolated (SS N-431 R2 round 3): several layers refuse an unpinned in-repo file, so a test that only checks "the run is refused" cannot tell which layer
# did it. Here every OTHER refusal site in the child is switched off by editing the runner text the engine sends (the test-only knob: monkeypatch of _RUNNER_SOURCE, every
# edit that no longer matches makes the per-route CONTROL (every layer off must run ok) fail, so a refactor cannot silently make these tests vacuous), and the parent's second layer is switched off by a test-only wrapper.
# Only the layer under test can then refuse. Each case asserts the refusal code AND that the unpinned file's effect (a marker written into the run's temp tree) did not happen.
# A control per route (every layer off) proves the route really does execute/leak the unpinned file, so a green here is not vacuous.
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------

# name -> (text in the runner, replacement that switches that one refusal site off)
_OFF = {
    "finder": ("_refuse(in_repo)  # a repo file that was not passed as pinned bytes: never executed", "pass"),
    "open_code_fn": ('served = serve_open(path, "rb", (), {})', "served = None"),
    "io_open_code_bind": ("    io.open_code = guarded_open_code\n", "    pass\n"),
    "_io_open_code_bind": ("    _io.open_code = guarded_open_code\n", "    pass\n"),
    "open_fn": ('served = serve_open(file, mode if isinstance(mode, str) else "r", args, kw)', "served = None"),
    "builtins_open_bind": ("    builtins.open = guarded_open\n", "    pass\n"),
    "io_open_bind": ("    io.open = guarded_open\n", "    pass\n"),
    "_io_open_bind": ("    _io.open = guarded_open\n", "    pass\n"),
    "fileio_fn": ("_refuse(path)  # a raw FileIO of a repo file cannot be served from the passed bytes: fail closed", "pass"),
    "io_fileio_bind": ("    io.FileIO = GuardedFileIO\n", "    pass\n"),
    "_io_fileio_bind": ("    _io.FileIO = GuardedFileIO\n", "    pass\n"),
    "osopen_fn": ("_refuse(repo)  # a descriptor-level read of a repo file cannot be served from the passed bytes: fail closed", "pass"),
    "pinned_bytes": ("    if data is None:\n        _refuse(path)\n", "    if data is None:\n        data = b''\n"),
}
_OS_OPEN_BIND = "        mod.open = make_os_open(mod.open)\n"  # wraps os.open and posix.open, one site each
_OS_BINDS = ("os_open_bind", "posix_open_bind")


def only_layers(monkeypatch, keep) -> None:
    """Switch off every child refusal site except those named in `keep` (a set of names from _OFF plus _OS_BINDS), by editing the runner text the engine sends."""
    src = ps._RUNNER_SOURCE
    assert src is not None
    for name, (old, new) in _OFF.items():
        if name in keep:
            continue
        src = src.replace(old, new)  # deliberately lenient: if a refusal site is renamed the control test (every layer off must run ok) fails; if it is mutated away it is already off
    wanted = [n for n in _OS_BINDS if n in keep]
    cond = "False" if not wanted else " or ".join("mod is " + ("os" if n == "os_open_bind" else "posix") for n in wanted)
    src = src.replace(_OS_OPEN_BIND, "        if %s:\n            mod.open = make_os_open(mod.open)\n" % cond)
    ast.parse(src, feature_version=(3, 11))
    monkeypatch.setattr(ps, "_RUNNER_SOURCE", src)


def no_parent_second_layer(monkeypatch) -> None:
    """Test-only: the parent's loaded-files check (_repo_rel_split over the child's `loaded`) reports nothing unpinned. The refused-files path (called with no pins) is untouched."""
    real = ps._repo_rel_split

    def wrapper(root, pins, paths):
        in_repo, unpinned = real(root, pins, paths)
        return (in_repo, unpinned) if not pins else (in_repo, set())

    monkeypatch.setattr(ps, "_repo_rel_split", wrapper)


class ScratchSpy:
    """Records what the run left in its own temp tree (marker files) just before the engine deletes it."""

    def __init__(self, monkeypatch):
        self.files: dict[str, bytes] = {}
        real = ps._rmtree_quiet
        spy = self

        def spy_rmtree(path):
            for dp, _dn, fns in os.walk(path):
                for fn in fns:
                    p = os.path.join(dp, fn)
                    with open(p, "rb") as fh:
                        spy.files[os.path.relpath(p, path)] = fh.read()
            real(path)

        monkeypatch.setattr(ps, "_rmtree_quiet", spy_rmtree)

    @property
    def effect(self):
        return [v for k, v in self.files.items() if os.path.basename(k) == "EFFECT"]


_MARK = "open(os.path.join(os.environ['TMPDIR'], 'EFFECT'), 'w').write(%s)\n"
_LATE = "import os\n" + (_MARK % "'late imported'") + "VALUE = 7\n"
_SECRET = "secret table\n"


# route name -> (parser body given the repo base path, the unpinned repo file it reaches, layers (a set of _OFF names / _OS_BINDS) that are the layer under test)
_ROUTES = {
    "import_finder": ("import pkg.late\nreturn pkg.late.VALUE", "lib/pkg/late.py", {"finder"}),
    "_io.open_code (importlib loader by location)": (
        "import importlib.util\nspec = importlib.util.spec_from_file_location('late_x', %(base)r + '/lib/pkg/late.py')\nm = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(m)\nreturn m.VALUE",
        "lib/pkg/late.py", {"open_code_fn", "_io_open_code_bind", "pinned_bytes"}),
    "io.open_code (runpy.run_path)": ("import runpy\nreturn runpy.run_path(%(base)r + '/lib/pkg/late.py')['VALUE']", "lib/pkg/late.py", {"open_code_fn", "io_open_code_bind", "pinned_bytes"}),
    "builtins.open": ("d = open(%(base)r + '/data/table.txt').read()\n" + _MARK % "d" + "return d", "data/table.txt", {"open_fn", "builtins_open_bind", "pinned_bytes"}),
    "io.open": ("import io\nd = io.open(%(base)r + '/data/table.txt').read()\n" + _MARK % "d" + "return d", "data/table.txt", {"open_fn", "io_open_bind", "pinned_bytes"}),
    "_io.open": ("import _io\nd = _io.open(%(base)r + '/data/table.txt').read()\n" + _MARK % "d" + "return d", "data/table.txt", {"open_fn", "_io_open_bind", "pinned_bytes"}),
    "io.FileIO": ("import io\nd = io.FileIO(%(base)r + '/data/table.txt').read()\n" + _MARK % "d.decode()" + "return d.decode()", "data/table.txt", {"fileio_fn", "io_fileio_bind"}),
    "_io.FileIO": ("import _io\nd = _io.FileIO(%(base)r + '/data/table.txt').read()\n" + _MARK % "d.decode()" + "return d.decode()", "data/table.txt", {"fileio_fn", "_io_fileio_bind"}),
    "os.open": ("fd = os.open(%(base)r + '/data/table.txt', os.O_RDONLY)\nd = os.read(fd, 100).decode()\n" + _MARK % "d" + "return d", "data/table.txt", {"osopen_fn", "os_open_bind"}),
    "posix.open": ("import posix\nfd = posix.open(%(base)r + '/data/table.txt', os.O_RDONLY)\nd = os.read(fd, 100).decode()\n" + _MARK % "d" + "return d", "data/table.txt", {"osopen_fn", "posix_open_bind"}),
}


def _route_run(tmp_path, monkeypatch, route, keep, second_layer):
    body, rel, _ = _ROUTES[route]
    root = make_repo(tmp_path, parser_with(body % {"base": str(pathlib.Path(tmp_path / "repo").resolve())}), extra={"lib/pkg/late.py": _LATE, "data/table.txt": _SECRET})
    only_layers(monkeypatch, keep)
    if not second_layer:
        no_parent_second_layer(monkeypatch)
    spy = ScratchSpy(monkeypatch)
    return run(root), spy, rel


class TestEachGuardLayerIsolated:
    @pytest.mark.parametrize("route", sorted(_ROUTES))
    def test_control_with_every_refusal_off_the_unpinned_file_does_run_or_leak(self, tmp_path, monkeypatch, route):
        """Not vacuous: with all child layers and the parent's second layer off, the same parser succeeds and the unpinned file's effect is there."""
        r, spy, _rel = _route_run(tmp_path, monkeypatch, route, set(), second_layer=False)
        assert r["ok"] is True, r
        assert spy.effect, "route %s did not reach the unpinned file: the isolation tests for it would prove nothing" % route

    @pytest.mark.parametrize("route", sorted(_ROUTES))
    def test_that_layer_alone_refuses_before_the_unpinned_file_has_any_effect(self, tmp_path, monkeypatch, route):
        keep = _ROUTES[route][2]
        r, spy, rel = _route_run(tmp_path, monkeypatch, route, keep, second_layer=False)
        assert r["ok"] is False and r["stage"] == "run", r
        assert r["error"] == "unpinned_import: " + rel and r["unpinned_files"] == [rel], r
        assert spy.effect == [], "the unpinned file took effect before the layer refused it"
        assert "outputs" not in r

    def test_parent_second_layer_alone_catches_an_unpinned_module_the_child_let_through(self, tmp_path, monkeypatch):
        """Every child refusal off, the parent's loaded-files check ON: the run is rejected after the fact. (It is a detector, not a preventer: the module did execute. It only sees
        modules left in sys.modules, so it covers the import route, not a data read.)"""
        r, spy, rel = _route_run(tmp_path, monkeypatch, "import_finder", set(), second_layer=True)
        assert r["ok"] is False and r["stage"] == "run", r
        assert r["error"] == "unpinned_import: " + rel and r["unpinned_files"] == [rel], r
        assert spy.effect, "control: the child really did execute the unpinned module, so only the parent could stop the result"

    def test_without_any_layer_the_parent_check_is_the_only_thing_standing_between_the_module_and_ok(self, tmp_path, monkeypatch):
        """The same configuration with the parent's check also off is ok True: proves the test above is decided by the parent layer and nothing else."""
        r, _spy, _rel = _route_run(tmp_path, monkeypatch, "import_finder", set(), second_layer=False)
        assert r["ok"] is True


class TestRanBytesAreHashedBytes:
    """SS N-431 R2 finding (1), TOCTOU: the parent reads each pinned file ONCE, hashes THOSE bytes and sends them to the child, which serves every module and every pinned data
    read from them. Whatever happens to the disk after the hash cannot change what runs."""

    MARK = "def parse(item):\n    return {'n': 2 * item['n'], 'src': %r}\n"

    def _mutate_after_check(self, monkeypatch, edits: dict):
        calls = []

        def hook():
            calls.append(1)
            for path, text in edits.items():
                pathlib.Path(path).write_text(text, encoding="utf-8")

        monkeypatch.setattr(ps, "_after_pin_check", hook)
        return calls

    def test_pinned_module_edited_on_disk_after_the_hash_still_runs_the_hashed_bytes(self, tmp_path, monkeypatch):
        root = make_repo(tmp_path, self.MARK % "hashed")
        pinned = pins(root, CLOSURE)
        calls = self._mutate_after_check(monkeypatch, {str(root / "lib/pkg/parser.py"): self.MARK % "EVIL-on-disk"})
        r = run(root, pinned=pinned)
        assert calls == [1]
        assert (root / "lib/pkg/parser.py").read_text().count("EVIL-on-disk") == 1  # the disk really did change after the check
        assert r["ok"] is True, r
        assert r["outputs"] == [{"n": 2, "src": "hashed"}]  # ...and the child ran the hashed source

    def test_helper_and_package_init_edited_after_the_hash_are_not_what_runs(self, tmp_path, monkeypatch):
        parser = "from pkg import FLAG\nfrom pkg.helper import double\n\ndef parse(item):\n    return {'flag': FLAG, 'n': double(item['n'])}\n"
        root = make_repo(tmp_path, parser)
        (root / "lib/pkg/__init__.py").write_text("FLAG = 'init-hashed'\n", encoding="utf-8")
        pinned = pins(root, CLOSURE)
        self._mutate_after_check(monkeypatch, {str(root / "lib/pkg/__init__.py"): "FLAG = 'init-EVIL'\n", str(root / "lib/pkg/helper.py"): "def double(n):\n    return -1\n"})
        r = run(root, pinned=pinned)
        assert r["ok"] is True and r["outputs"] == [{"flag": "init-hashed", "n": 2}]

    def test_without_the_edit_hook_the_same_disk_state_is_a_pin_mismatch_before_anything_runs(self, tmp_path):
        """Control: an edit made BEFORE the parent hashes is still caught by the pin check (the hash is the gate; serving from bytes is what closes the window after it)."""
        root = make_repo(tmp_path, self.MARK % "hashed")
        pinned = pins(root, CLOSURE)
        (root / "lib/pkg/parser.py").write_text(self.MARK % "edited-before", encoding="utf-8")
        assert run(root, pinned=pinned)["error"].startswith("pin_mismatch: lib/pkg/parser.py")

    def test_pinned_file_loaded_by_location_is_also_served_from_bytes(self, tmp_path, monkeypatch):
        root = make_repo(tmp_path, extra={"tools/standalone.py": "def parse(item):\n    return 'hashed'\n"})
        pinned = pins(root, ["tools/standalone.py"])
        self._mutate_after_check(monkeypatch, {str(root / "tools/standalone.py"): "def parse(item):\n    return 'EVIL'\n"})
        r = ps.run_pinned_parser(str(root), "lib", pinned, "tools/standalone.py", "parse", [{"n": 1}])
        assert r["ok"] is True and r["outputs"] == ["hashed"]

    def test_the_engine_opens_each_pinned_file_exactly_once(self, tmp_path, monkeypatch):
        """The hash and the bytes sent to the child must come from the same single read (a second read would reopen the window)."""
        import collections

        root = make_repo(tmp_path)
        pinned = pins(root, CLOSURE)
        opened = []
        real = open

        def counting(path, *a, **k):
            opened.append(os.path.realpath(path))
            return real(path, *a, **k)

        monkeypatch.setattr(ps, "open", counting, raising=False)
        assert run(root, pinned=pinned)["ok"] is True
        wanted = {os.path.realpath(str(root / r)) for r in CLOSURE}
        assert collections.Counter(p for p in opened if p in wanted) == {p: 1 for p in wanted}

    def test_hook_is_a_noop_by_default(self):
        assert ps._after_pin_check() is None

    # ---- (c) data files ----

    DATA_PARSER = (
        "import json, pathlib\n"
        "P = %r\n"
        "TEXT = open(P).read()\n"
        "RAW = open(P, 'rb').read()\n"
        "LATIN = open(P, encoding='latin-1').read()\n"
        "PATHLIB = pathlib.Path(P).read_text()\n"
        "with open(P) as fh:\n    JSON = json.load(fh)\n"
        "NAME = open(P).name\n\n"
        "def parse(item):\n    return {'text': TEXT, 'raw': RAW.decode(), 'latin': LATIN, 'pathlib': PATHLIB, 'json': JSON, 'name': NAME, 'again': open(P).read()}\n"
    )

    def test_data_file_read_at_import_is_served_from_the_passed_bytes(self, tmp_path, monkeypatch):
        data_path = tmp_path / "repo" / "data" / "table.json"
        root = make_repo(tmp_path, self.DATA_PARSER % str(data_path), extra={"data/table.json": '{"k": "hashed"}'})
        pinned = pins(root, CLOSURE + ["data/table.json"])
        self._mutate_after_check(monkeypatch, {str(data_path): '{"k": "EVIL"}'})
        r = run(root, pinned=pinned)
        assert r["ok"] is True, r
        out = r["outputs"][0]
        assert out["json"] == {"k": "hashed"} and out["text"] == out["raw"] == out["latin"] == out["pathlib"] == out["again"] == '{"k": "hashed"}'
        assert out["name"] == str(data_path)
        assert "data/table.json" in r["loaded_repo_files"]
        assert "EVIL" in data_path.read_text()  # disk changed, output did not

    def test_text_mode_translates_newlines_and_binary_mode_does_not(self, tmp_path):
        data_path = tmp_path / "repo" / "data" / "crlf.txt"
        src = parser_with("return [open(%r).read(), open(%r, 'rb').read().decode()]" % (str(data_path), str(data_path)))
        root = make_repo(tmp_path, src, extra={})
        (root / "data").mkdir()
        data_path.write_bytes(b"a\r\nb\r\n")
        r = run(root, pinned=pins(root, CLOSURE + ["data/crlf.txt"]))
        assert r["ok"] and r["outputs"] == [["a\nb\n", "a\r\nb\r\n"]]

    def test_binary_mode_with_an_encoding_argument_is_the_same_valueerror_as_open(self, tmp_path):
        data_path = tmp_path / "repo" / "data" / "t.txt"
        root = make_repo(tmp_path, parser_with("return open(%r, 'rb', encoding='utf-8').read()" % str(data_path)), extra={"data/t.txt": "x"})
        r = run(root, pinned=pins(root, CLOSURE + ["data/t.txt"]))
        assert r["error"] == "parser_raised: index=0 type=ValueError"

    def test_write_to_a_pinned_data_file_is_still_a_write_attempt(self, tmp_path):
        data_path = tmp_path / "repo" / "data" / "t.txt"
        root = make_repo(tmp_path, parser_with("open(%r, 'w').write('x')\nreturn 1" % str(data_path)), extra={"data/t.txt": "keep"})
        r = run(root, pinned=pins(root, CLOSURE + ["data/t.txt"]))
        assert r["error"].startswith("write_attempt")
        assert data_path.read_text() == "keep"

    # ---- (b) unpinned in-repo code and data is refused even though it exists on disk ----

    def test_unpinned_module_that_exists_on_disk_is_refused_and_never_executed(self, tmp_path):
        """If the unpinned module had run, os._exit(7) would have made this a nonzero_exit; unpinned_import proves it was refused before executing."""
        src = parser_with("from pkg import rogue\nreturn rogue.X")
        root = make_repo(tmp_path, src, extra={"lib/pkg/rogue.py": "import os\nos._exit(7)\nX = 1\n"})
        assert (root / "lib/pkg/rogue.py").is_file()
        r = run(root)
        assert r["ok"] is False and r["stage"] == "run" and r["error"] == "unpinned_import: lib/pkg/rogue.py" and r["unpinned_files"] == ["lib/pkg/rogue.py"]

    def test_unpinned_module_import_cannot_be_swallowed_by_the_parser(self, tmp_path):
        src = parser_with("try:\n    from pkg import rogue\nexcept BaseException:\n    pass\nreturn 'carried on'")
        root = make_repo(tmp_path, src, extra={"lib/pkg/rogue.py": "X = 1\n"})
        r = run(root)
        assert r["ok"] is False and r["error"] == "unpinned_import: lib/pkg/rogue.py"

    def test_unpinned_module_at_module_import_time_is_refused(self, tmp_path):
        root = make_repo(tmp_path, "from pkg import rogue\n" + parser_with("return 1"), extra={"lib/pkg/rogue.py": "X = 1\n"})
        assert run(root)["error"] == "unpinned_import: lib/pkg/rogue.py"

    @pytest.mark.parametrize(
        "body",
        [
            "return open(P).read()",
            "return open(P, 'rb').read()",
            "import pathlib\nreturn pathlib.Path(P).read_text()",
            "import pathlib\nreturn pathlib.Path(P).read_bytes()",
            "import io\nreturn io.open_code(P).read()",
            "import io\nreturn io.FileIO(P).read()",
            "fd = os.open(P, os.O_RDONLY)\nreturn os.read(fd, 100)",
            "import importlib.util\nspec = importlib.util.spec_from_file_location('m', P)\nm = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(m)\nreturn 1",
            "import importlib.machinery\nreturn importlib.machinery.SourceFileLoader('m', P).get_data(P)",
        ],
    )
    def test_every_way_of_reading_an_unpinned_repo_file_is_refused(self, tmp_path, body):
        p = tmp_path / "repo" / "data" / "secret.py"
        root = make_repo(tmp_path, parser_with("P = %r\n" % str(p) + body), extra={"data/secret.py": "VALUE = 1\n"})
        r = run(root)
        assert r["ok"] is False and r["error"] == "unpinned_import: data/secret.py", r

    def test_a_pinned_file_reachable_only_by_os_open_fails_closed(self, tmp_path):
        """A descriptor-level read cannot be served from bytes, so it is refused rather than allowed to hit the disk."""
        p = tmp_path / "repo" / "data" / "t.txt"
        root = make_repo(tmp_path, parser_with("fd = os.open(%r, os.O_RDONLY)\nreturn os.read(fd, 10)" % str(p)), extra={"data/t.txt": "x"})
        r = run(root, pinned=pins(root, CLOSURE + ["data/t.txt"]))
        assert r["ok"] is False and r["error"] == "unpinned_import: data/t.txt"

    def test_reading_files_outside_the_repo_still_works(self, tmp_path):
        outside = tmp_path / "outside.txt"
        outside.write_text("visible", encoding="utf-8")
        r = run(make_repo(tmp_path, parser_with("import pathlib\nreturn [open(%r).read(), pathlib.Path(%r).read_text(), open(%r, 'rb').read().decode()]" % ((str(outside),) * 3))))
        assert r["ok"] and r["outputs"] == [["visible"] * 3]

    def test_symlink_inside_the_repo_to_an_unpinned_file_is_refused(self, tmp_path):
        p = tmp_path / "repo" / "data" / "link.txt"
        root = make_repo(tmp_path, parser_with("return open(%r).read()" % str(p)), extra={"data/real.txt": "x"})
        p.symlink_to(root / "data" / "real.txt")
        r = run(root)
        assert r["ok"] is False and r["error"].startswith("unpinned_import")

    # ---- module-system behaviour that must survive the in-memory loader ----

    def test_relative_import_package_attributes_and_dunder_file(self, tmp_path):
        parser = "from . import helper\nfrom .helper import double\n\ndef parse(item):\n    return [__name__, __package__, __file__.rsplit('/', 3)[-3:], helper.__name__, double(2), __spec__.origin == __file__]\n"
        root = make_repo(tmp_path, parser)
        r = run(root)
        assert r["ok"], r
        assert r["outputs"] == [["pkg.parser", "pkg", ["lib", "pkg", "parser.py"], "pkg.helper", 4, True]]

    def test_implicit_namespace_package_with_pinned_submodule_works(self, tmp_path):
        root = make_repo(tmp_path, extra={"lib/ns/mod.py": "def parse(item):\n    return 'ns'\n"})
        r = ps.run_pinned_parser(str(root), "lib", pins(root, ["lib/ns/mod.py"]), "lib/ns/mod.py", "parse", [{"n": 1}])
        assert r["ok"] is True and r["outputs"] == ["ns"] and r["loaded_repo_files"] == ["lib/ns/mod.py"]

    def test_module_root_is_the_repo_root(self, tmp_path):
        root = make_repo(tmp_path, extra={"top.py": "def parse(item):\n    return 'top'\n"})
        r = ps.run_pinned_parser(str(root), ".", pins(root, ["top.py"]), "top.py", "parse", [{"n": 1}])
        assert r["ok"] is True and r["outputs"] == ["top"]

    def test_a_pinned_file_with_a_syntax_error_is_parser_raised_not_a_crash(self, tmp_path):
        r = run(make_repo(tmp_path, "def parse(item:\n"))
        assert r["ok"] is False and r["error"] == "parser_raised: index=-1 type=SyntaxError"

    def test_future_import_in_the_runner_does_not_leak_into_pinned_code(self, tmp_path):
        """The runner uses `from __future__ import annotations`; compile(..., dont_inherit=True) keeps pinned code on the default semantics."""
        r = run(make_repo(tmp_path, "def parse(item):\n    def f(x: int) -> int:\n        return x\n    return repr(f.__annotations__)\n"))
        assert r["ok"] and "<class 'int'>" in r["outputs"][0]

    def test_pinned_file_over_the_size_bound_is_refused_at_the_pin_stage(self, tmp_path, monkeypatch):
        root = make_repo(tmp_path)
        pinned = pins(root, CLOSURE)
        monkeypatch.setattr(ps, "MAX_PINNED_FILE_BYTES", 10)
        r = run(root, pinned=pinned)
        assert r["ok"] is False and r["stage"] == "pin" and r["error"].startswith("pin_missing") and "too large" in r["error"]

    def test_two_pinned_files_mapping_to_one_module_name_are_refused(self, tmp_path):
        root = make_repo(tmp_path, extra={"lib/pkg.py": "X = 1\n"})
        r = run(root, pinned=pins(root, CLOSURE + ["lib/pkg.py"]))
        assert r["ok"] is False and r["stage"] == "spawn" and "two pinned files" in r["error"]


class TestRunnerIsNotReReadFromDisk:
    """SS N-431 R2 finding (1), part 2: the runner (the child's own code) is not pinned, so it must not be re-read from disk either. DESIGN CHOSEN: in-memory. The engine reads
    its own source once at import (_RUNNER_SOURCE) and sends it to `python -c <bootstrap>` on stdin; the child never opens a file to obtain its code."""

    def _load_copy(self, tmp_path):
        import importlib.util

        copy = tmp_path / "parser_sandbox_copy.py"
        copy.write_text(pathlib.Path(ps.__file__).read_text(encoding="utf-8"), encoding="utf-8")
        spec = importlib.util.spec_from_file_location("parser_sandbox_copy", str(copy))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["parser_sandbox_copy"] = mod
        spec.loader.exec_module(mod)
        return mod, copy

    def test_editing_the_runner_file_on_disk_between_the_pin_check_and_the_spawn_has_no_effect(self, tmp_path, monkeypatch):
        mod, copy = self._load_copy(tmp_path)
        try:
            root = make_repo(tmp_path)
            pinned = pins(root, CLOSURE)
            seen = []

            def hook():
                seen.append(1)
                copy.write_text("raise SystemExit('the runner was re-read from disk')\n", encoding="utf-8")

            monkeypatch.setattr(mod, "_after_pin_check", hook)
            r = mod.run_pinned_parser(str(root), "lib", pinned, "lib/pkg/parser.py", "parse", [{"n": 3}])
            assert seen == [1] and "re-read" in copy.read_text()
            assert r["ok"] is True, r
            assert r["outputs"] == [{"n": 6, "echo": {"n": 3}}]
        finally:
            sys.modules.pop("parser_sandbox_copy", None)

    def test_editing_the_runner_file_on_disk_while_the_child_runs_has_no_effect(self, tmp_path, monkeypatch):
        mod, copy = self._load_copy(tmp_path)
        try:
            root = make_repo(tmp_path, parser_with("time.sleep(0.5)\nreturn item"))
            pinned = pins(root, CLOSURE)
            real = subprocess.Popen

            class Racing(real):
                def __init__(self, *a, **k):
                    super().__init__(*a, **k)
                    copy.write_text("raise SystemExit('edited during the run')\n", encoding="utf-8")

            monkeypatch.setattr(mod.subprocess, "Popen", Racing)
            r = mod.run_pinned_parser(str(root), "lib", pinned, "lib/pkg/parser.py", "parse", [{"n": 1}])
            assert r["ok"] is True and r["outputs"] == [{"n": 1}]
        finally:
            sys.modules.pop("parser_sandbox_copy", None)

    def test_the_child_command_line_names_no_file_of_ours(self, tmp_path, monkeypatch):
        spy = PopenSpy(monkeypatch)
        assert run(make_repo(tmp_path))["ok"]
        argv = spy.started[0].args
        assert argv[:5] == [sys.executable, "-s", "-S", "-P", "-B"] and argv[5] == "-c" and argv[6] == ps._CHILD_BOOTSTRAP and len(argv) == 7
        assert not any(ps.__file__ in a for a in argv)
        assert "open(" not in ps._CHILD_BOOTSTRAP and "__file__" not in ps._CHILD_BOOTSTRAP  # the bootstrap opens nothing

    def test_runner_source_is_this_file_read_once_and_its_digest_is_published(self):
        assert ps._RUNNER_SOURCE == pathlib.Path(ps.__file__).read_text(encoding="utf-8")
        assert ps.RUNNER_SHA256 == hashlib.sha256(ps._RUNNER_SOURCE.encode("utf-8")).hexdigest()

    def test_the_child_really_runs_the_in_memory_runner_not_the_file(self, tmp_path, monkeypatch):
        """Swap the in-memory source for a runner whose envelope is recognisably different: that is what the child must execute."""
        stub = (
            "import os, json\n"
            "def _child_main(cfg):\n"
            "    os.write(1, json.dumps({'v': 1, 'status': 'ok', 'outputs': ['from-memory-stub'], 'loaded': [cfg['file_abs']], 'violations': []}).encode())\n"
            "    os._exit(0)\n"
        )
        monkeypatch.setattr(ps, "_RUNNER_SOURCE", stub)
        r = run(make_repo(tmp_path))
        assert r["ok"] is True and r["outputs"] == ["from-memory-stub"]

    def test_missing_runner_source_is_spawn_failed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ps, "_RUNNER_SOURCE", None)
        r = run(make_repo(tmp_path))
        assert r["ok"] is False and r["stage"] == "spawn" and r["error"].startswith("spawn_failed")


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


class TestAssuranceLabel:
    """SS N-431 R2 finding (2): the result channel lives in the parser's own process, so a hostile pinned parser could forge an ok envelope. Documented limit; the
    census must be able to print the strength of the evidence on every pass, so EVERY result carries the label."""

    def test_constant_value(self):
        assert ps.ASSURANCE == "software-guarded, reviewed code only"

    def test_ok_result_carries_it(self, tmp_path):
        r = run(make_repo(tmp_path))
        assert r["ok"] is True and r["assurance"] == ps.ASSURANCE

    @pytest.mark.parametrize(
        "case",
        ["pin_mismatch", "pin_missing", "unpinned_import", "spawn_failed_args", "spawn_failed_exe", "timeout", "nonzero_exit", "bad_output", "output_too_large",
         "parser_raised", "network_attempt", "write_attempt", "spawn_attempt", "no_inputs"],
    )
    def test_every_failure_carries_it(self, tmp_path, monkeypatch, case):
        kw: dict = {}
        src = PARSER
        pinned = None
        inputs = None
        if case == "pin_mismatch":
            root = make_repo(tmp_path)
            pinned = pins(root, CLOSURE)
            (root / "lib/pkg/helper.py").write_text(HELPER + "# x\n", encoding="utf-8")
            r = run(root, pinned=pinned)
        else:
            if case == "timeout":
                src, kw = parser_with("time.sleep(20)\nreturn 1"), {"timeout_s": 1}
            elif case == "nonzero_exit":
                src = parser_with("os._exit(3)")
            elif case == "bad_output":
                src = parser_with("return {1, 2}")
            elif case == "output_too_large":
                src, kw = parser_with("return 'x' * 100000"), {"max_output_bytes": 1000}
            elif case == "parser_raised":
                src = parser_with("raise ValueError('x')")
            elif case == "network_attempt":
                src = parser_with("import socket\nsocket.socket()\nreturn 1")
            elif case == "write_attempt":
                src = parser_with("open(%r, 'w')\nreturn 1" % str(tmp_path / "w.txt"))
            elif case == "spawn_attempt":
                src = parser_with("os.system('echo')\nreturn 1")
            elif case == "no_inputs":
                inputs = []
            elif case == "spawn_failed_args":
                kw = {"timeout_s": 0}
            elif case == "spawn_failed_exe":
                monkeypatch.setattr(ps.sys, "executable", str(tmp_path / "no_such_python"))
            root = make_repo(tmp_path, src)
            if case == "pin_missing":
                pinned = pins(root, CLOSURE)[:1]
            elif case == "unpinned_import":
                pinned = pins(root, ["lib/pkg/__init__.py", "lib/pkg/parser.py"])
            r = run(root, pinned=pinned, inputs=inputs, **kw)
        assert r["ok"] is False, r
        assert r["error"].split(":")[0] == case.replace("_args", "").replace("_exe", ""), r
        assert r["assurance"] == ps.ASSURANCE

    def test_docstring_states_the_forgery_limit_and_the_permitted_use(self):
        doc = ps.__doc__
        assert "HOSTILE" in doc and "forge an ok envelope" in doc and "MALICIOUS pinned parser" in doc
        assert "PERMITTED USE" in doc and "l0_rules" in doc


class TestPinManifest:
    """SS N-431 R2 finding (5): pins come from a COMMITTED manifest, validated, never discovered at run time."""

    def _manifest(self, root, doc, name="m.json"):
        (root / name).write_text(doc if isinstance(doc, str) else json.dumps(doc), encoding="utf-8")
        return name

    def test_valid_manifest_round_trips_and_feeds_the_runner(self, tmp_path):
        root = make_repo(tmp_path)
        entries = [{"path": r, "sha256": hashlib.sha256((root / r).read_bytes()).hexdigest().upper()} for r in CLOSURE]
        got = ps.load_pin_manifest(str(root), self._manifest(root, {"pinned_files": entries}))
        assert got == [{"path": e["path"], "sha256": e["sha256"].lower()} for e in entries]  # digests come back lowercase
        assert run(root, pinned=got)["ok"] is True

    def test_manifest_in_a_subdirectory(self, tmp_path):
        root = make_repo(tmp_path)
        (root / "decl").mkdir()
        entries = [{"path": "lib/pkg/helper.py", "sha256": hashlib.sha256((root / "lib/pkg/helper.py").read_bytes()).hexdigest()}]
        assert ps.load_pin_manifest(str(root), self._manifest(root, {"pinned_files": entries}, "decl/m.json")) == entries

    def _good(self, root):
        return {"path": "lib/pkg/helper.py", "sha256": hashlib.sha256((root / "lib/pkg/helper.py").read_bytes()).hexdigest()}

    @pytest.mark.parametrize(
        "case",
        [
            "not_json", "not_object", "missing_key", "extra_top_key", "pinned_files_not_list", "empty_list", "entry_not_object", "entry_extra_key", "entry_missing_sha",
            "abs_path", "dotdot", "backslash", "unnormalised", "empty_path", "path_not_str", "short_digest", "nonhex_digest", "digest_not_str", "duplicate_path",
            "duplicate_json_key", "missing_file", "directory", "too_many", "pinned_file_too_large",
        ],
    )
    def test_malformed_manifests_are_refused(self, tmp_path, monkeypatch, case):
        root = make_repo(tmp_path)
        g = self._good(root)
        docs = {
            "not_json": "{nope",
            "not_object": [g],
            "missing_key": {"files": [g]},
            "extra_top_key": {"pinned_files": [g], "note": "x"},
            "pinned_files_not_list": {"pinned_files": g},
            "empty_list": {"pinned_files": []},
            "entry_not_object": {"pinned_files": ["lib/pkg/helper.py"]},
            "entry_extra_key": {"pinned_files": [dict(g, extra=1)]},
            "entry_missing_sha": {"pinned_files": [{"path": g["path"]}]},
            "abs_path": {"pinned_files": [dict(g, path="/etc/hosts")]},
            "dotdot": {"pinned_files": [dict(g, path="../repo/lib/pkg/helper.py")]},
            "backslash": {"pinned_files": [dict(g, path="lib\\pkg\\helper.py")]},
            "unnormalised": {"pinned_files": [dict(g, path="lib/./pkg/helper.py")]},
            "empty_path": {"pinned_files": [dict(g, path="")]},
            "path_not_str": {"pinned_files": [dict(g, path=7)]},
            "short_digest": {"pinned_files": [dict(g, sha256="abc123")]},
            "nonhex_digest": {"pinned_files": [dict(g, sha256="z" * 64)]},
            "digest_not_str": {"pinned_files": [dict(g, sha256=12345)]},
            "duplicate_path": {"pinned_files": [g, dict(g)]},
            "duplicate_json_key": '{"pinned_files": [], "pinned_files": [%s]}' % json.dumps(g),
            "missing_file": {"pinned_files": [dict(g, path="lib/pkg/gone.py")]},
            "directory": {"pinned_files": [dict(g, path="lib/pkg")]},
            "too_many": {"pinned_files": [dict(g, path="lib/pkg/helper.py")] * 1},
        }
        if case == "too_many":
            monkeypatch.setattr(ps, "MAX_PINNED_FILES", 1)
            docs["too_many"] = {"pinned_files": [g, dict(self._good(root), path="lib/pkg/parser.py")]}
        if case == "pinned_file_too_large":
            monkeypatch.setattr(ps, "MAX_PINNED_FILE_BYTES", 5)
            docs[case] = {"pinned_files": [g]}
        with pytest.raises(ps.PinManifestError):
            ps.load_pin_manifest(str(root), self._manifest(root, docs[case]))

    def test_manifest_too_large(self, tmp_path, monkeypatch):
        root = make_repo(tmp_path)
        monkeypatch.setattr(ps, "MAX_MANIFEST_BYTES", 20)
        with pytest.raises(ps.PinManifestError):
            ps.load_pin_manifest(str(root), self._manifest(root, {"pinned_files": [self._good(root)]}))

    def test_manifest_path_must_be_a_file_inside_the_repo(self, tmp_path):
        root = make_repo(tmp_path)
        outside = tmp_path / "outside.json"
        outside.write_text(json.dumps({"pinned_files": [self._good(root)]}), encoding="utf-8")
        (root / "linked.json").symlink_to(outside)
        for rel in ("nope.json", "../outside.json", "/etc/hosts", "linked.json", "lib", ""):
            with pytest.raises(ps.PinManifestError):
                ps.load_pin_manifest(str(root), rel)

    def test_pinned_file_that_is_a_symlink_out_of_the_repo_is_refused(self, tmp_path):
        root = make_repo(tmp_path)
        outside = tmp_path / "outside_helper.py"
        outside.write_text(HELPER, encoding="utf-8")
        (root / "lib/pkg/linked.py").symlink_to(outside)
        doc = {"pinned_files": [dict(self._good(root), path="lib/pkg/linked.py")]}
        with pytest.raises(ps.PinManifestError):
            ps.load_pin_manifest(str(root), self._manifest(root, doc))

    def test_bad_repo_root_type(self):
        with pytest.raises(ps.PinManifestError):
            ps.load_pin_manifest(None, "m.json")

    def test_loader_does_not_hash_so_a_wrong_digest_is_caught_by_the_run_not_the_loader(self, tmp_path):
        root = make_repo(tmp_path)
        doc = {"pinned_files": [dict(self._good(root), sha256="0" * 64)]}
        got = ps.load_pin_manifest(str(root), self._manifest(root, doc))
        assert got[0]["sha256"] == "0" * 64  # declaration is syntactically fine; the run refuses it (pin_mismatch)

    def test_fixture_pins_in_these_tests_come_from_a_manifest_file(self, tmp_path):
        root = make_repo(tmp_path)
        got = pins(root, CLOSURE)
        assert (root / "pins.json").is_file() and json.loads((root / "pins.json").read_text())["pinned_files"] == got


class TestDefaultOutputCap:
    """SS N-431 R2 finding (4): default cap lowered to 16 MB (macOS ignores RLIMIT_AS; the real bg_rules output is small)."""

    def test_default_is_16_million(self):
        import inspect

        assert ps.DEFAULT_MAX_OUTPUT_BYTES == 16_000_000
        assert inspect.signature(ps.run_pinned_parser).parameters["max_output_bytes"].default == 16_000_000

    def test_default_cap_is_enforced(self, tmp_path):
        r = run(make_repo(tmp_path, parser_with("return 'x' * 17_000_000")))
        assert r["ok"] is False and r["stage"] == "output" and r["error"].startswith("output_too_large")


class TestFailureVocabulary:
    def test_parser_raising_on_input_3_reports_index_and_type_only(self, tmp_path):
        src = parser_with("if item['n'] == 3:\n    raise ValueError('secret /etc/passwd token=abc')\nreturn item")
        r = run(make_repo(tmp_path, src), inputs=[{"n": i} for i in range(6)])
        assert r == {"ok": False, "error": "parser_raised: index=3 type=ValueError", "stage": "run", "assurance": ps.ASSURANCE}
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


def _TEST_HELPER_discover_closure_by_running(repo_root: pathlib.Path, inputs):
    """TEST HELPER ONLY, never production: discover the real parser's repo-local import closure by running it and pinning what the sandbox reports as unpinned, until it is
    accepted. Production pins come from a committed declaration (load_pin_manifest); the sandbox itself never discovers pins. Returns (result, pinned)."""
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
        r, pinned = _TEST_HELPER_discover_closure_by_running(REPO_ROOT, inputs)
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
        r, _ = _TEST_HELPER_discover_closure_by_running(REPO_ROOT, inputs)
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
