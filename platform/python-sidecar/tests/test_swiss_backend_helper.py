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


def test_jhora_import_never_takes_the_swiss_lock_and_uses_the_nowait_reassert():
    """Structural guard against the lock-order deadlock: the module body must not
    reference SWISS_STATE_LOCK (blocking) nor call ensure_swiss_backend(); it re-asserts
    through the non-blocking, never-raising helper after the jhora imports."""
    tree = ast.parse((SIDECAR / "pyjhora_adapter" / "_jhora.py").read_text())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "SWISS_STATE_LOCK" not in names and "ensure_swiss_backend" not in names
    body_calls = [n.value.func.id for n in tree.body
                  if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                  and isinstance(n.value.func, ast.Name)]
    assert "reassert_swiss_backend_nowait" in body_calls


def test_importing_pyjhora_adapter_with_an_unusable_path_does_not_break_registry_discovery(tmp_path):
    """SE_EPHE_PATH set but wrong must LOG and continue at import (not take down
    discover_all() for every writer); the fail-closed raise stays at use."""
    script = """
import json
from pipeline.orchestrator.writers import WRITER_REGISTRY, discover_all
discover_all()
import panchang_engine.swiss_backend as ss
try:
    ss.ensure_swiss_backend()
    use = "no-error"
except ss.SwissBackendError:
    use = "refused"
print("RESULT:" + json.dumps([len(WRITER_REGISTRY), use]))
"""
    count, use = json.loads(_run_script(script, extra_env={"SE_EPHE_PATH": str(tmp_path / "missing")}))
    assert count > 100 and use == "refused"


def test_first_import_of_pyjhora_adapter_cannot_deadlock_against_the_swiss_lock():
    """Lock-order inversion repro: thread A holds the Swiss lock and first-imports
    pyjhora_adapter while thread B is already first-importing it.  A blocking Swiss-lock
    wait inside the module body deadlocks; the no-wait re-assert must not."""
    script = """
import json, threading, time
from panchang_engine.swiss_state import SWISS_STATE_LOCK
started = threading.Event()
def b():
    started.set()
    import pyjhora_adapter._jhora   # slow first import (holds the module import lock)
def a():
    started.wait()
    time.sleep(0.3)                  # let B get inside the import first
    with SWISS_STATE_LOCK:
        import pyjhora_adapter._jhora
tb, ta = threading.Thread(target=b), threading.Thread(target=a)
tb.start(); ta.start()
tb.join(90); ta.join(90)
print("RESULT:" + json.dumps(not (tb.is_alive() or ta.is_alive())))
"""
    corpus = str(_CORPUS) if _CORPUS else "/nonexistent"
    assert json.loads(_run_script(script, extra_env={"SE_EPHE_PATH": corpus})) is True


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

if %(eager)r:
    import pyjhora_adapter._jhora   # strict mode: import in the main thread, before any worker

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
    """Production-like: SE_EPHE_PATH set (as in both images), PyJHora's FIRST import happens
    inside a worker thread concurrently with compute_panchang / panchanga_instant."""
    env = {"SE_EPHE_PATH": str(corpus_dir)}
    spec = {"hidden": "SE_EPHE_PATH", "eager": False}
    threaded = json.loads(_run_script(_THREAD_SCRIPT % {**spec, "single": False}, extra_env=env))
    sequential = json.loads(_run_script(_THREAD_SCRIPT % {**spec, "single": True}, extra_env=env))
    assert threaded.keys() == sequential.keys() and len(threaded) >= 27
    for key, value in sequential.items():
        assert threaded[key] == value, key


@needs_corpus
def test_threaded_mixed_callers_strict_no_env_hint_with_pyjhora_imported_first(corpus_dir):
    """Strict: the C library gets NO environment hint (only the helper's explicit set_ephe_path
    can put the process on swieph).  PyJHora is imported in the main thread first: the short
    window between jhora.const's path reset and the re-assert during a worker's FIRST import is
    by design only harmless when SE_EPHE_PATH is in the environment (covered above)."""
    env = {_HIDDEN_ENV: str(corpus_dir)}
    spec = {"hidden": _HIDDEN_ENV, "eager": True}
    threaded = json.loads(_run_script(_THREAD_SCRIPT % {**spec, "single": False}, extra_env=env))
    sequential = json.loads(_run_script(_THREAD_SCRIPT % {**spec, "single": True}, extra_env=env))
    assert threaded == sequential and len(threaded) >= 27


# ── 5. the helper really holds the lock and really probes (mutation guards) ───

def test_helpers_are_swiss_state_boundaries():
    for fn in (ensure_swiss_backend, backend_name, ss._observed_backend_name):
        assert getattr(fn, "__swiss_state_serialized__", False), fn.__name__
        assert getattr(fn, "__swiss_state_lock__", None) is SWISS_STATE_LOCK, fn.__name__


@needs_corpus
def test_ensure_does_not_touch_the_path_while_another_thread_holds_the_state_lock(
    hidden_env, monkeypatch
):
    """Behavioural lock check: the path MUTATION itself (not just the later probe, which
    is separately locked) must wait for the lock."""
    path_set = threading.Event()
    real_set = swe.set_ephe_path

    def recording_set(path):
        path_set.set()
        return real_set(path)

    monkeypatch.setattr(swe, "set_ephe_path", recording_set)
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
        assert not path_set.wait(0.5), "set_ephe_path ran while the Swiss state lock was held"
        assert not done.is_set()
    assert done.wait(30)
    t.join()
    assert errors == []
    assert path_set.is_set()


# ── 6. writer decorator: probe before, record after, fail closed ──────────────

class _Result:
    def __init__(self, notes: str = "", rows: int = 1):
        self.notes = notes
        self.rows_inserted = rows
        self.rows_updated = 0


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
            return _Result("", rows=3)

    assert Light().run(object()).notes == "chart_facts=12; ephemeris_backend=swieph"
    assert Heavy().run_substep(object(), "k").notes == "ephemeris_backend=swieph"


@needs_corpus
def test_decorator_does_not_claim_a_backend_on_a_noop_return(hidden_env):
    @records_swiss_backend
    class Noop:
        def run(self, ctx):
            return _Result("No convergence windows", rows=0)

    assert Noop().run(object()).notes == "No convergence windows"


@needs_corpus
def test_decorator_fails_closed_if_the_backend_drifts_during_the_body(hidden_env):
    @records_swiss_backend
    class Drifter:
        def run(self, ctx):
            swe.set_ephe_path("/nonexistent-ephe-dir")  # body leaves the process on Moshier
            return _Result("x")

    with pytest.raises(SwissBackendError, match="moseph"):
        Drifter().run(object())


@needs_corpus
def test_decorator_logs_the_probed_backend_because_notes_are_not_persisted(hidden_env, caplog):
    import logging

    @records_swiss_backend
    class Writer:
        asset_id = "ga_example"

        def run(self, ctx):
            return _Result("", rows=0)

    with caplog.at_level(logging.INFO, logger="panchang_engine.swiss_backend"):
        Writer().run(object())
    # logged even for a no-op (the log is the persistent trace; notes are in-memory only)
    assert any("ga_example ephemeris_backend=swieph rows=0" in r.getMessage() for r in caplog.records)


def test_probe_cli_fails_closed_and_reports_when_unconfigured(capsys):
    assert ss._probe_main() == 1
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report["ok"] is False and report["backend"] is None and "SE_EPHE_PATH" in report["error"]


@needs_corpus
def test_probe_cli_reports_swieph_and_the_pinned_digests(monkeypatch, capsys):
    monkeypatch.setenv("SE_EPHE_PATH", str(_CORPUS))
    assert ss._probe_main() == 0
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report["ok"] is True and report["backend"] == "swieph"
    assert set(report["files"]) == set(ss._PINNED_SHA256)
    assert all(f["pinned"] for f in report["files"].values())


# Writers that directly import swisseph / panchang_engine / pyjhora_adapter / jhora but are NOT
# decorated, each with the reason.  The test below DERIVES the importing set from the registry
# (declared source files + the class's own file) so a future swisseph-computing writer cannot
# silently escape: it must be decorated or added here with a reason.
_EXEMPT = {
    "bg_cohort": "L0: own fail-closed explicit-path backend check",
    "bg_ephemeris": "L0: own fail-closed explicit-path backend check (verified in-run)",
    "bg_muhurta_lattice": "L0: own fail-closed explicit-path backend check",
    "bg_sky_calendar": "L0: own fail-closed explicit-path backend check",
    "bg_parihara_rules": "reference data: reads panchang_engine.shastra_tables only, no ephemeris",
    "ga_ayurdaya": "imports jhora const only; positions are read from L1 facts",
    "ga_sensitive_degree": "imports jhora const only; positions are read from L1 facts",
    "ga_condition": "imports pyjhora_adapter.version only; derives from stored facts",
    "ka_gochara": "Pravaha-owned; kernel fails closed and records its backend",
    "ka_gochara_v3_century_materialize": "Pravaha-owned; kernel fails closed and records its backend",
    "ka_gochara_sweep": "retired, protected history (Pravaha-owned), outside the active set; never rebuilt",
    "ka_muhurta_seva": "self-test writer (rows=0, service_health only); its compute_panchang call fails closed",
    "ph_rectification": "swe.houses ascendant only (no planetary ephemeris); backend-independent",
}


def _directly_importing_assets() -> set[str]:
    from pipeline.orchestrator.asset_runner import _writer_source_paths
    from pipeline.orchestrator.writers import WRITER_REGISTRY, discover_all
    import inspect

    discover_all()
    roots = {"swisseph", "panchang_engine", "pyjhora_adapter", "jhora"}
    found: set[str] = set()
    for asset, cls in WRITER_REGISTRY.items():
        files: set[Path] = set()
        for raw in _writer_source_paths(asset):
            p = Path(raw)
            p = p if p.is_absolute() else SIDECAR.parents[1] / p
            if p.is_file():
                files.add(p)
            elif p.is_dir():
                files.update(x for x in p.rglob("*.py") if "tests" not in x.parts)
        try:
            files.add(Path(inspect.getfile(cls)))
        except (TypeError, OSError):
            pass
        for f in files:
            if not f.is_file():
                continue
            for node in ast.walk(ast.parse(f.read_text())):
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                    mods = [node.module]
                else:
                    mods = []
                if any(m.split(".")[0] in roots for m in mods):
                    found.add(asset)
    return found


def test_every_swisseph_computing_writer_records_the_backend():
    from pipeline.orchestrator.writers import WRITER_REGISTRY

    importing = _directly_importing_assets()
    assert importing, "derivation found nothing: the scan itself is broken"
    undecorated = {a for a in importing if not getattr(WRITER_REGISTRY[a], "records_swiss_backend", False)}
    unclassified = sorted(undecorated - set(_EXEMPT))
    assert unclassified == [], (
        "swisseph-importing writers must be @records_swiss_backend or listed in _EXEMPT with a "
        f"reason: {unclassified}")
    # the registry is import-order dependent (other tests register retired writers), so only
    # exemptions that CONTRADICT reality (an exempt writer that is in fact decorated) are stale.
    contradicted = sorted(a for a in _EXEMPT if getattr(WRITER_REGISTRY.get(a), "records_swiss_backend", False))
    assert contradicted == [], f"_EXEMPT lists decorated writers: {contradicted}"


# ── 6b. corpus window: never report swieph outside 1800-2400 ──────────────────

JD_1750 = 2360386.0
JD_2450 = 2616056.0


def test_window_error_is_named_and_is_both_a_swiss_backend_and_an_out_of_range_error():
    from panchang_engine import OutOfRangeError

    assert issubclass(ss.OutOfCorpusRangeError, ss.SwissBackendError)
    assert issubclass(ss.OutOfCorpusRangeError, OutOfRangeError)
    assert ss.OutOfCorpusRangeError.code == "out_of_corpus_range"


@pytest.mark.parametrize("jd", [JD_1750, JD_2450, 2378496.4, 2597641.6])
def test_helpers_refuse_a_date_outside_the_window_before_any_configuration_check(jd):
    # unset SE_EPHE_PATH: the window error still comes first and is the named one
    with pytest.raises(ss.OutOfCorpusRangeError, match="out_of_corpus_range"):
        ensure_swiss_backend(jd)
    with pytest.raises(ss.OutOfCorpusRangeError, match="out_of_corpus_range"):
        backend_name(jd)


@needs_corpus
def test_window_edges_are_inside_and_the_limit_the_guard_exists_for_is_real(hidden_env):
    lo, hi = ss.SWIEPH_WINDOW_JD
    assert ensure_swiss_backend(lo, hi, 2451545.0).name == "swieph"
    assert backend_name(lo, hi) == "swieph"
    # Why the guard exists (measured): the J2000 probe passes, yet outside the window the
    # library computes with Moshier and says so only in the flag.
    assert backend_name() == "swieph"
    _x, retflag = swe.calc_ut(JD_1750, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)
    assert retflag & swe.FLG_MOSEPH


@needs_corpus
def test_panchang_entry_points_disclose_out_of_corpus_dates(hidden_env):
    from panchang_engine import compute_panchang, panchanga_instant

    for year in (1750, 2450):
        with pytest.raises(ss.OutOfCorpusRangeError, match="out_of_corpus_range"):
            compute_panchang(datetime.date(year, 6, 1), 20.27, 85.84, 330)
        with pytest.raises(ss.OutOfCorpusRangeError, match="out_of_corpus_range"):
            panchanga_instant(datetime.datetime(year, 6, 1, 10, 0), 20.27, 85.84, 330)


@needs_corpus
def test_decorator_checks_the_chart_lifetime_before_the_body_and_any_write(hidden_env):
    ran: list[int] = []

    @records_swiss_backend
    class W:
        def run(self, ctx):
            ran.append(1)
            return _Result("x")

    class Ctx:
        def __init__(self, iso):
            self.config = {"birth_params": {"datetime_iso": iso}}

    assert W().run(Ctx("1984-02-05T10:43:00")).notes.endswith("ephemeris_backend=swieph")
    for iso in ("1790-01-01T00:00:00", "2290-01-01T00:00:00"):   # before 1800 / lifetime past 2400
        with pytest.raises(ss.OutOfCorpusRangeError):
            W().run(Ctx(iso))
    assert ran == [1]            # the body ran only for the in-window chart


# ── 6c. the two WRITE routes raise BEFORE any write when the backend check fails ─

def _no_db(monkeypatch):
    """psycopg.connect must never be reached; returns the list of attempts."""
    import psycopg

    attempts: list[str] = []

    def boom(*a, **k):
        attempts.append("connect")
        raise AssertionError("a DB connection was opened before the backend check")

    monkeypatch.setattr(psycopg, "connect", boom)
    return attempts


def test_panchanga_daily_writer_raises_before_connecting_or_writing(monkeypatch):
    from scripts.panchanga_daily_writer import write_window

    attempts = _no_db(monkeypatch)
    with pytest.raises(SwissBackendError, match="SE_EPHE_PATH is not set"):
        write_window(datetime.date(2026, 6, 15), datetime.date(2026, 6, 17), dry_run=False)
    with pytest.raises(ss.OutOfCorpusRangeError):
        write_window(datetime.date(1750, 6, 15), datetime.date(1750, 6, 16), dry_run=False)
    assert attempts == []


def test_panchanga_refresh_route_writes_nothing_when_the_backend_check_fails(monkeypatch):
    from fastapi.testclient import TestClient
    from main import app

    attempts = _no_db(monkeypatch)
    monkeypatch.delenv("PYTHON_SIDECAR_API_KEY", raising=False)
    resp = TestClient(app, raise_server_exceptions=False).post("/api/compute/panchanga/refresh", json={})
    assert resp.status_code == 500 and "SE_EPHE_PATH is not set" in resp.text
    assert attempts == []


def test_prashna_cast_raises_before_the_prashna_charts_insert(monkeypatch):
    from unittest.mock import MagicMock

    from ga_writers.ga_prashna_cast import cast_prashna_chart

    conn = MagicMock()
    kwargs = dict(conn=conn, build_id="b", question_text="q", question_class="career",
                  prashna_lagna_method="question_instant", question_lat=20.27, question_lon=85.84,
                  question_instant="2026-06-15T10:00:00+05:30")
    from ga_writers.ga_prashna_cast import VALID_QUESTION_CLASSES

    kwargs["question_class"] = sorted(VALID_QUESTION_CLASSES)[0]
    with pytest.raises(SwissBackendError, match="SE_EPHE_PATH is not set"):
        cast_prashna_chart(**kwargs)
    with pytest.raises(ss.OutOfCorpusRangeError):
        cast_prashna_chart(**{**kwargs, "question_instant": "1750-06-15T10:00:00+00:00"})
    conn.cursor.assert_not_called()
    conn.execute.assert_not_called()


def test_prashna_cast_route_opens_no_cursor_and_commits_nothing_when_the_backend_check_fails(monkeypatch):
    from unittest.mock import MagicMock

    import psycopg
    from fastapi.testclient import TestClient
    from ga_writers.ga_prashna_cast import VALID_QUESTION_CLASSES
    from main import app

    conn = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = conn
    ctx.__exit__.return_value = False
    monkeypatch.setattr(psycopg, "connect", lambda *a, **k: ctx)
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused")
    monkeypatch.delenv("PYTHON_SIDECAR_API_KEY", raising=False)
    monkeypatch.setattr("ga_writers.ga_prashna_cast.validate_prashna_question",
                        lambda text: {"valid": True, "reason": ""})
    body = {"question_text": "will it work", "question_class": sorted(VALID_QUESTION_CLASSES)[0],
            "prashna_lagna_method": "question_instant", "question_instant": "2026-06-15T10:00:00+05:30",
            "question_lat": 20.27, "question_lon": 85.84}
    resp = TestClient(app, raise_server_exceptions=False).post("/api/compute/prashna/cast", json=body)
    assert resp.status_code == 500 and "SE_EPHE_PATH is not set" in resp.text
    conn.cursor.assert_not_called()
    conn.commit.assert_not_called()
    resp = TestClient(app, raise_server_exceptions=False).post(
        "/api/compute/prashna/cast", json={**body, "question_instant": "1750-06-15T10:00:00+00:00"})
    assert resp.status_code == 422 and "out_of_corpus_range" in resp.text
    conn.cursor.assert_not_called()


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
