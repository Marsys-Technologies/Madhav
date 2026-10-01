"""TI-ephemeris-fix-001: the Swiss ``.se1`` backend is a verified precondition.

SS ruling N-28: the canonical ephemeris backend is the Swiss ``.se1`` corpus
(``swieph``); Moshier is a fallback and must NEVER be silent.  These tests pin
``panchang_engine.swiss_backend.ensure_swiss_backend`` / ``backend_name`` and every
mechanism that keeps the process on that backend:

* env unset / unusable corpus  -> fail closed with ``SwissBackendError``;
* env set to the real ``.se1`` files -> ``swieph``;
* importing the PyJHora adapter (``jhora/const.py:262`` resets the path to its
  ``.se1``-free wheel directory) must not flip the backend;
* a threaded run with mixed callers (``compute_panchang``, ``panchanga_instant``,
  a PyJHora call whose FIRST import happens inside a worker) stays on ``swieph``;
* the helper really holds ``SWISS_STATE_LOCK`` and really probes (mutation-proofed).

Corpus: the three ``.se1`` files pinned (SHA-256) in ``Dockerfile.pipeline``.
Located via ``MARSYS_TEST_SE1_DIR``, ``SE_EPHE_PATH``, ``SWE_EPHE_PATH``,
``/app/ephe`` or ``/tmp/se1``; tests that need it skip with a reason otherwise
(CI's "pinned Swiss Ephemeris corpus probe" step downloads it and runs this file).

IMPORTANT test-design fact (measured, pyswisseph 2.10.3.2): when ``SE_EPHE_PATH`` is
present in the process environment the Swiss C library ALSO searches it for files
even after ``set_ephe_path(<other dir>)``.  So with the real variable set, every path
state resolves to ``swieph`` and no test could tell a missing re-assert from a present
one.  Tests that must discriminate therefore point the helper at a differently
NAMED variable (``MARSYS_TEST_SE1_DIR``, via ``ss.SE_EPHE_PATH_ENV``) so that the
C library sees no environment hint and ONLY the explicit ``set_ephe_path`` the
helper performs can put the process on ``swieph``.
"""
from __future__ import annotations

import ast
import datetime
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest
import swisseph as swe

from panchang_engine import swiss_backend as ss
from panchang_engine.swiss_backend import (
    SwissBackendError,
    backend_name,
    backend_note,
    ensure_swiss_backend,
    records_swiss_backend,
)
from panchang_engine.swiss_state import SWISS_STATE_LOCK

SIDECAR = Path(__file__).resolve().parents[1]
_HIDDEN_ENV = "MARSYS_TEST_SE1_DIR"
_NEEDED = ("sepl_18.se1", "semo_18.se1")
_OPTIONAL = ("seas_18.se1", "sefstars.txt", "seleapsec.txt")


def _find_corpus() -> Path | None:
    for cand in (
        os.environ.get(_HIDDEN_ENV),
        os.environ.get("SE_EPHE_PATH"),
        os.environ.get("SWE_EPHE_PATH"),
        "/app/ephe",
        "/tmp/se1",
    ):
        if cand and all((Path(cand) / n).is_file() for n in _NEEDED):
            return Path(cand)
    return None


_CORPUS = _find_corpus()
needs_corpus = pytest.mark.skipif(
    _CORPUS is None,
    reason=(
        "Swiss .se1 corpus (sepl_18.se1 + semo_18.se1; pinned in Dockerfile.pipeline) "
        "not found: set MARSYS_TEST_SE1_DIR or SWE_EPHE_PATH to a directory holding it"
    ),
)


@pytest.fixture(autouse=True)
def _swiss_process_state(monkeypatch):
    """Start every test with the variable unset; leave the global path neutral."""
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)
    monkeypatch.delenv(_HIDDEN_ENV, raising=False)
    yield
    swe.set_ephe_path(None)


@pytest.fixture
def corpus_dir(tmp_path) -> Path:
    """A tmp directory holding (symlinks to) the real corpus files."""
    assert _CORPUS is not None
    for name in _NEEDED + _OPTIONAL:
        src = _CORPUS / name
        if src.is_file():
            (tmp_path / name).symlink_to(src)
    return tmp_path


@pytest.fixture
def hidden_env(monkeypatch, corpus_dir) -> Path:
    """Point the helper at ``MARSYS_TEST_SE1_DIR`` so the C library sees no hint."""
    monkeypatch.setenv(_HIDDEN_ENV, str(corpus_dir))
    monkeypatch.setattr(ss, "SE_EPHE_PATH_ENV", _HIDDEN_ENV)
    return corpus_dir


def _moon_and_sun(panchang) -> tuple[float, float]:
    by_name = {p.name: p.longitude_sidereal for p in panchang.planets}
    return by_name["Moon"], by_name["Sun"]


# ── 1. fail-closed configuration ──────────────────────────────────────────────

def test_env_unset_raises():
    with pytest.raises(SwissBackendError, match="SE_EPHE_PATH is not set"):
        ensure_swiss_backend()


def test_env_blank_raises(monkeypatch):
    monkeypatch.setenv("SE_EPHE_PATH", "   ")
    with pytest.raises(SwissBackendError, match="not set"):
        ensure_swiss_backend()


def test_env_pointing_at_empty_dir_raises_with_observed_backend(monkeypatch, tmp_path):
    monkeypatch.setenv("SE_EPHE_PATH", str(tmp_path))
    with pytest.raises(SwissBackendError, match="moseph"):
        ensure_swiss_backend()


def test_compute_panchang_refuses_when_unconfigured():
    from panchang_engine import compute_panchang

    with pytest.raises(SwissBackendError):
        compute_panchang(datetime.date(2026, 6, 15), 20.27, 85.84, 330)


def test_panchanga_instant_refuses_when_unconfigured():
    from panchang_engine import panchanga_instant

    with pytest.raises(SwissBackendError):
        panchanga_instant(datetime.datetime(1984, 2, 5, 10, 43), 20.2735, 85.8334, 330)


# ── 2. env set to the real corpus -> swieph ───────────────────────────────────

@needs_corpus
def test_env_set_to_real_corpus_is_swieph(monkeypatch, corpus_dir):
    from panchang_engine import compute_panchang

    monkeypatch.setenv("SE_EPHE_PATH", str(corpus_dir))
    got = ensure_swiss_backend()
    assert got.name == "swieph" and got.path == str(corpus_dir)
    assert backend_name() == "swieph"
    assert backend_note() == "ephemeris_backend=swieph"
    compute_panchang(datetime.date(2026, 6, 15), 20.27, 85.84, 330)
    assert backend_name() == "swieph"


@needs_corpus
@pytest.mark.parametrize("only", ["sepl_18.se1", "semo_18.se1"])
def test_partial_corpus_is_refused(hidden_env, tmp_path_factory, monkeypatch, only):
    """Either file alone must not pass.  Measured: with semo missing, calc_ut(MOON)
    returns the Moshier Moon with a SWIEPH flag (the Moon's flag lies), so the probe
    uses TRUE_NODE for semo; this test fails if the probe regresses to the Moon."""
    partial = tmp_path_factory.mktemp("partial_se1")
    (partial / only).symlink_to(hidden_env / only)
    monkeypatch.setenv(_HIDDEN_ENV, str(partial))
    with pytest.raises(SwissBackendError, match="moseph"):
        ensure_swiss_backend()


@needs_corpus
def test_backend_name_probes_live_state_not_configuration(hidden_env):
    ensure_swiss_backend()
    assert backend_name() == "swieph"
    swe.set_ephe_path("/nonexistent-ephe-dir")  # something else knocks the path off
    with pytest.raises(SwissBackendError, match="moseph"):
        backend_name()
    ensure_swiss_backend()  # and the helper puts it back
    assert backend_name() == "swieph"


@needs_corpus
def test_panchang_entry_points_re_pin_a_knocked_off_path(hidden_env):
    """compute_panchang / panchanga_instant must not inherit whatever path a prior
    caller left, and must not leave the process on the default (Moshier) path."""
    from panchang_engine import compute_panchang, panchanga_instant

    day = (datetime.date(2026, 6, 15), 20.27, 85.84, 330)
    instant = (datetime.datetime(1984, 2, 5, 10, 43), 20.2735, 85.8334, 330)

    ensure_swiss_backend()
    ref_day = _moon_and_sun(compute_panchang(*day))
    ref_inst = _moon_and_sun(panchanga_instant(*instant))

    swe.set_ephe_path("/nonexistent-ephe-dir")
    assert _moon_and_sun(compute_panchang(*day)) == ref_day
    assert backend_name() == "swieph"

    swe.set_ephe_path("/nonexistent-ephe-dir")
    assert _moon_and_sun(panchanga_instant(*instant)) == ref_inst
    assert backend_name() == "swieph"

    # Control: the values really are backend-sensitive (Moshier differs at the
    # sub-arcsecond-to-arcsecond level), so equality above is a real signal.
    swe.set_ephe_path("/nonexistent-ephe-dir")
    jd = swe.julday(2026, 6, 15, 12.0)
    moshier = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]
    swe.set_ephe_path(str(hidden_env))
    swiss = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]
    assert abs(moshier - swiss) > 1e-6


# ── 3. PyJHora import must not flip the backend ───────────────────────────────

def _run_script(script: str, *, extra_env: dict[str, str]) -> str:
    env = {k: v for k, v in os.environ.items() if k not in ("SE_EPHE_PATH", _HIDDEN_ENV)}
    env.update(extra_env)
    env["PYTHONPATH"] = str(SIDECAR) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=SIDECAR, env=env, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, f"subprocess failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT:")]
    assert lines, f"no RESULT line:\n{proc.stdout}\n{proc.stderr}"
    return lines[-1][len("RESULT:"):]


_PROBE_FN = """
import json, swisseph as swe
def raw_probe():
    out = set()
    for body in (swe.SUN, swe.TRUE_NODE):
        _x, rf = swe.calc_ut(2451545.0, body, swe.FLG_SWIEPH | swe.FLG_SPEED)
        out.add("swieph" if rf & swe.FLG_SWIEPH else "moseph" if rf & swe.FLG_MOSEPH else "other")
    return sorted(out)
"""


@needs_corpus
def test_control_pyjhora_import_does_flip_the_path_when_nothing_re_asserts(corpus_dir):
    """Negative control: proves the next test can discriminate.  Importing jhora
    directly (no helper) silently moves swisseph to the Moshier fallback."""
    script = _PROBE_FN + f"""
swe.set_ephe_path({str(corpus_dir)!r})
before = raw_probe()
import jhora.const  # executes swe.set_ephe_path(<wheel>/data/ephe)
after = raw_probe()
print("RESULT:" + json.dumps([before, after]))
"""
    before, after = json.loads(_run_script(script, extra_env={}))
    assert before == ["swieph"]
    assert after == ["moseph"], "PyJHora no longer resets the path; control is stale"


@needs_corpus
def test_importing_pyjhora_adapter_does_not_flip_backend(corpus_dir):
    script = f"""
import json
import panchang_engine.swiss_backend as ss
ss.SE_EPHE_PATH_ENV = {_HIDDEN_ENV!r}   # hide the hint from the C library
import pyjhora_adapter._jhora            # imports jhora.const (path reset) then re-asserts
print("RESULT:" + json.dumps(ss.backend_name()))
"""
    assert json.loads(_run_script(script, extra_env={_HIDDEN_ENV: str(corpus_dir)})) == "swieph"


@needs_corpus
def test_importing_pyjhora_adapter_with_real_variable_is_swieph(corpus_dir):
    script = """
import json
import pyjhora_adapter._jhora
import panchang_engine.swiss_backend as ss
print("RESULT:" + json.dumps(ss.backend_name()))
"""
    assert json.loads(_run_script(script, extra_env={"SE_EPHE_PATH": str(corpus_dir)})) == "swieph"


def test_importing_pyjhora_adapter_unconfigured_is_importable_but_writers_refuse():
    """No corpus configured: import stays possible (pure-function users, CI), but the
    backend is NOT swieph and the helper refuses -- the Moshier state is never silent."""
    script = """
import json
import pyjhora_adapter._jhora
import panchang_engine.swiss_backend as ss
try:
    ss.ensure_swiss_backend()
    out = "no-error"
except ss.SwissBackendError:
    out = "refused"
print("RESULT:" + json.dumps(out))
"""
    assert json.loads(_run_script(script, extra_env={})) == "refused"


def test_jhora_reassert_is_inside_the_state_lock_with_the_import():
    """Structural guard: the jhora imports and the re-assert share one
    ``with SWISS_STATE_LOCK`` block (no window where another serialized caller can
    observe the wheel directory)."""
    tree = ast.parse((SIDECAR / "pyjhora_adapter" / "_jhora.py").read_text())
    blocks = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.With)
        and any(isinstance(i.context_expr, ast.Name) and i.context_expr.id == "SWISS_STATE_LOCK"
                for i in n.items)
    ]
    assert len(blocks) == 1
    inner = ast.dump(blocks[0])
    assert "'jhora.panchanga'" in inner and "'jhora.horoscope.chart'" in inner
    assert "ensure_swiss_backend" in inner


# ── 4. threaded run, mixed callers ────────────────────────────────────────────

_THREAD_SCRIPT = """
import datetime, json, sys, threading
from concurrent.futures import ThreadPoolExecutor
import panchang_engine.swiss_backend as ss
ss.SE_EPHE_PATH_ENV = %(hidden)r              # hide the hint from the C library
import swisseph as swe
from panchang_engine import compute_panchang, panchanga_instant

def pan():
    p = compute_panchang(datetime.date(2026, 6, 15), 20.27, 85.84, 330)
    return {"pan:" + pl.name: pl.longitude_sidereal for pl in p.planets}

def inst():
    p = panchanga_instant(datetime.datetime(1984, 2, 5, 10, 43), 20.2735, 85.8334, 330)
    return {"inst:" + pl.name: pl.longitude_sidereal for pl in p.planets}

def jhora():
    # First jhora import in the process happens HERE, inside a worker thread,
    # concurrently with the panchang callers.
    from pyjhora_adapter.positions import compute_positions
    jd = swe.julday(1984, 2, 5, 5 + 13 / 60.0)
    g = compute_positions(jd, "lahiri", lat=20.2735, lon=85.8334, tz=5.5)
    return {"jh:" + x["name"]: x["longitude_deg"] for x in g}

TASKS = [jhora, pan, inst, jhora, pan, jhora, inst, pan]
gate = threading.Barrier(4)

def run(fn):
    try:
        gate.wait(timeout=30)
    except threading.BrokenBarrierError:
        pass
    out = fn()
    ss.backend_name()          # still swieph right after the call (raises otherwise)
    return fn.__name__, out

if %(single)r:
    results = [(fn.__name__, fn()) for fn in TASKS]
else:
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, TASKS))
ss.backend_name()
merged = {}
for name, out in results:
    for k, v in out.items():
        merged.setdefault(k, set()).add(v)
assert all(len(v) == 1 for v in merged.values()), "same call gave different values across threads"
print("RESULT:" + json.dumps({k: next(iter(v)) for k, v in sorted(merged.items())}))
"""


@needs_corpus
def test_threaded_mixed_callers_stay_on_swieph_and_match_single_threaded(corpus_dir):
    env = {_HIDDEN_ENV: str(corpus_dir)}
    threaded = json.loads(_run_script(
        _THREAD_SCRIPT % {"hidden": _HIDDEN_ENV, "single": False}, extra_env=env))
    sequential = json.loads(_run_script(
        _THREAD_SCRIPT % {"hidden": _HIDDEN_ENV, "single": True}, extra_env=env))
    assert threaded.keys() == sequential.keys() and len(threaded) >= 27
    for key, value in sequential.items():
        assert threaded[key] == value, key


# ── 5. the helper really holds the lock and really probes (mutation guards) ───

def test_helpers_are_swiss_state_boundaries():
    for fn in (ensure_swiss_backend, backend_name, ss._observed_backend_name):
        assert getattr(fn, "__swiss_state_serialized__", False), fn.__name__
        assert getattr(fn, "__swiss_state_lock__", None) is SWISS_STATE_LOCK, fn.__name__


@needs_corpus
def test_ensure_blocks_while_another_thread_holds_the_state_lock(hidden_env):
    done = threading.Event()
    errors: list[BaseException] = []

    def worker():
        try:
            ensure_swiss_backend()
        except BaseException as exc:  # pragma: no cover - reported below
            errors.append(exc)
        finally:
            done.set()

    with SWISS_STATE_LOCK:
        t = threading.Thread(target=worker)
        t.start()
        assert not done.wait(0.5), "ensure_swiss_backend ran while the Swiss state lock was held"
    assert done.wait(30)
    t.join()
    assert errors == []


# ── 6. writer decorator: probe before, record after, fail closed ──────────────

class _Result:
    def __init__(self, notes: str = ""):
        self.notes = notes


def test_decorator_refuses_to_run_the_body_when_unconfigured():
    ran: list[int] = []

    @records_swiss_backend
    class W:
        def run(self, ctx):
            ran.append(1)
            return _Result()

    with pytest.raises(SwissBackendError):
        W().run(object())
    assert ran == []


@needs_corpus
def test_decorator_appends_the_probed_backend_to_notes(hidden_env):
    @records_swiss_backend
    class Light:
        def run(self, ctx):
            return _Result("chart_facts=12")

    @records_swiss_backend
    class Heavy:
        def run_substep(self, ctx, step):
            return _Result("")

    assert Light().run(object()).notes == "chart_facts=12; ephemeris_backend=swieph"
    assert Heavy().run_substep(object(), "k").notes == "ephemeris_backend=swieph"


@needs_corpus
def test_decorator_fails_closed_if_the_backend_drifts_during_the_body(hidden_env):
    @records_swiss_backend
    class Drifter:
        def run(self, ctx):
            swe.set_ephe_path("/nonexistent-ephe-dir")  # body leaves the process on Moshier
            return _Result("x")

    with pytest.raises(SwissBackendError, match="moseph"):
        Drifter().run(object())


_DECORATED_ASSETS = {
    "ga_positions", "ga_dashas", "ga_vargas", "ga_strength", "ga_structural",
    "ga_tajaka", "ga_sensitive", "ga_nakshatra", "ga_panchanga", "ga_sade_sati",
    "ph_muhurta", "ka_vighnakara", "ka_sangam", "ka_kshetra", "ka_tithi_pravesha",
}


def test_every_swisseph_computing_writer_records_the_backend():
    from pipeline.orchestrator.writers import WRITER_REGISTRY, discover_all

    discover_all()
    missing = sorted(a for a in _DECORATED_ASSETS
                     if not getattr(WRITER_REGISTRY.get(a), "records_swiss_backend", False))
    assert missing == []


# ── 7. no silent default-path reset reintroduced in the routed call sites ─────

def test_no_default_path_reset_or_dead_ephe_dir_in_routed_modules():
    roots = [SIDECAR / "panchang_engine", SIDECAR / "pyjhora_adapter",
             SIDECAR / "ga_writers", SIDECAR / "brahmagyan" / "ganita",
             SIDECAR / "routers" / "pyhora.py"]
    offenders: list[str] = []
    for root in roots:
        files = [root] if root.is_file() else sorted(root.rglob("*.py"))
        for path in files:
            rel = path.relative_to(SIDECAR)
            if "tests" in rel.parts or "__tests__" in rel.parts or path.name.startswith("test_"):
                continue
            source = path.read_text()
            if "/usr/share/ephe" in source:
                offenders.append(f"{rel}: dead /usr/share/ephe path")
            for node in ast.walk(ast.parse(source)):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "set_ephe_path" and node.args
                        and isinstance(node.args[0], ast.Constant) and node.args[0].value is None):
                    offenders.append(f"{rel}:{node.lineno}: set_ephe_path(None)")
    assert offenders == []
