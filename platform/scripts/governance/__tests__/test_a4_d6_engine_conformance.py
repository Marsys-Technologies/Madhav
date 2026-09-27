"""test_a4_d6_engine_conformance.py — D6 item 5 (A_REVIEW.md F11): the Earn/Cost classifier tested
against the ENGINE implementation, read-only.

D6 item 5 requires the classifier to be "tested before adoption against the engine implementation
(`asset_runner.py` at `8edba0533`+, migration 1094): failure, zero rows, skip after a prior timing,
probe-green, the legacy `ga_*` path, the absent column, an unknown NULL". The engine lives in a
separate checkout (`campaign/nirmana-engine`); this suite reads it with `git show <rev>:<path>` —
nothing in it is imported, run against a database, or written. Each scenario pins (a) what the
engine's own code does on that path and (b) that the census's `_grade_earn_cost` grades the attempt
that path produces as the ruling requires. Pure engine arithmetic (`_compute_duration_and_rate`) is
executed from the engine's own source text, so the census is checked against the engine's numbers,
not a transcription of them.

WHAT THIS CANNOT TEST (stated, not assumed): no scenario here runs the engine's write paths against
a database carrying migration 1094 and grades the rows they produce. That needs migration 1094
applied to a database and builds run against it (a migration apply and writes, both outside this
wave's constraints), and the census has no attempt query to read such rows with — `measure()` passes
`attempt=None` (attempt linkage is R42–R56, unwired; F1). The attempt dicts below are what an
adapter reading `build_run_assets` + `asset_throughput` would have to produce from each engine path.

Environment: NIKASHA_ENGINE_DIR (default /Users/Dev/madhav-engine), NIKASHA_ENGINE_REV (default
8edba0533). Skipped, with the reason, when that checkout or revision is not available.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_a4_d6_engine_conformance.py -v
"""
from __future__ import annotations

import ast
import math
import os
import pathlib
import re
import subprocess
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import asset_census as ac  # noqa: E402

ENGINE = os.environ.get("NIKASHA_ENGINE_DIR", "/Users/Dev/madhav-engine")
REV = os.environ.get("NIKASHA_ENGINE_REV", "8edba0533")
RUNNER = "platform/python-sidecar/pipeline/orchestrator/asset_runner.py"
PARALLEL_RUNNER = "platform/python-sidecar/pipeline/orchestrator/runner.py"
TELEMETRY = "platform/python-sidecar/ga_writers/_telemetry.py"
MIG_1094 = "platform/supabase/migrations/1094_asset_throughput_duration_seconds.sql"


def _show(path: str) -> str | None:
    try:
        p = subprocess.run(["git", "-C", ENGINE, "show", f"{REV}:{path}"], capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    return p.stdout if p.returncode == 0 else None


_SRC = {k: _show(v) for k, v in dict(runner=RUNNER, parallel=PARALLEL_RUNNER, telemetry=TELEMETRY,
                                      mig=MIG_1094).items()}
pytestmark = pytest.mark.skipif(any(v is None for v in _SRC.values()),
                                reason=f"engine checkout {ENGINE} at {REV} not available")


def _fn(src: str, name: str) -> ast.FunctionDef:
    return next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == name)


def _sql(src: str, name: str) -> list[str]:
    """Every string literal inside engine function `name` (its SQL)."""
    return [n.value for n in ast.walk(_fn(src, name)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _engine_fn(src: str, name: str):
    """Execute one pure engine function from its own source text."""
    ns = {"math": math}
    exec(compile(ast.Module(body=[_fn(src, name)], type_ignores=[]), f"<engine {REV} {name}>", "exec"), ns)
    return ns[name]


def _writes(sqls: list[str], table: str) -> list[str]:
    return [s for s in sqls if re.search(rf"\b(UPDATE|INSERT INTO)\s+{table}\b", s)]


def _engine_dispositions() -> set[str]:
    return set(re.findall(r"disposition\s*=\s*'([a-z_]+)'", _SRC["runner"] + _SRC["parallel"]))


def _grade(attempt, baseline=None):
    return ac._grade_earn_cost(attempt=attempt, instrument_present=True, baseline=baseline)


_BASELINE = dict(rate=120.0, attempt_id="run-prior", age_days=3)


# ── the absent column: the census probes exactly the column the engine probes and 1094 adds ──

def _probe_triple(sql: str) -> dict:
    return dict(re.findall(r"(table_schema|table_name|column_name)\s*=\s*'([^']+)'", sql))


def test_d6_absent_column_census_probes_what_the_engine_probes_and_1094_adds(monkeypatch):
    """F11 finding: the engine's `_duration_columns_present` is schema-qualified (`table_schema =
    'public'`, gate review R-7: a same-named table in another schema must never read as present); the
    census's probe was not. Fails without the census fix: its probe lacks `table_schema`."""
    seen = []
    monkeypatch.setattr(ac, "scalar", lambda sql: seen.append(sql) or "f")
    assert ac.duration_instrument_present() is False
    census = _probe_triple(seen[0])
    engine = _probe_triple(next(s for s in _sql(_SRC["runner"], "_duration_columns_present")
                                if "information_schema.columns" in s))
    assert census == engine, (census, engine)
    added = re.search(r"ALTER TABLE\s+(\w+)\s+ADD COLUMN IF NOT EXISTS\s+(\w+)", _SRC["mig"])
    assert (engine["table_name"], engine["column_name"]) == added.groups()


# ── zero rows: the engine records a real rate of 0.0; the census grades it PASS with that rate ──

def test_d6_zero_rows_engine_rate_zero_is_graded_pass_not_suppressed():
    rate_fn = _engine_fn(_SRC["runner"], "_compute_duration_and_rate")
    duration, rate = rate_fn(0, 2.5)
    assert (duration, rate) == (2.5, 0.0)
    earn, _cost = _grade(dict(state="complete", disposition="build", reached_completion_write=True,
                              duration_seconds=duration, rows_written=0))
    assert earn["v"] == ac.PASS and f"rate={rate}" in earn["measured"], earn


# ── an unknown NULL: every duration the engine refuses to persist grades NO_DETECTOR, never PASS ──

@pytest.mark.parametrize("raw", [None, 0, -1.0, float("nan"), float("inf"), "not-a-number"])
def test_d6_unknown_null_engine_refused_duration_is_never_pass(raw):
    rate_fn = _engine_fn(_SRC["runner"], "_compute_duration_and_rate")
    duration, _rate = rate_fn(10, raw)
    assert duration is None
    earn, _cost = _grade(dict(state="complete", disposition="build", reached_completion_write=True,
                              duration_seconds=duration, rows_written=10))
    assert earn["v"] == ac.NO_DET and "unclassified NULL" in earn["measured"], earn


# ── the completion write: the ONE site that records a duration, and the one that marks 'build' ──

def test_d6_only_the_completion_write_records_a_duration_and_it_marks_disposition_build():
    """The adapter contract this pins: `reached_completion_write` is `disposition = 'build'` on the
    attempt's build_run_assets row — no other engine path writes duration_seconds."""
    tree = ast.parse(_SRC["runner"])
    writers = sorted({f.name for f in ast.walk(tree) if isinstance(f, ast.FunctionDef)
                      for s in _sql(_SRC["runner"], f.name) if "duration_seconds = %s" in s})
    assert writers == ["_run_data_writer"], writers
    assert any("disposition = 'build'" in s for s in _writes(_sql(_SRC["runner"], "_run_data_writer"), "build_run_assets"))


# ── skip after a prior timing: the engine leaves the old duration in place; the census ignores it ──

def test_d6_skip_after_prior_timing_stale_duration_is_not_a_pass_and_baseline_survives():
    sqls = _sql(_SRC["runner"], "_skip_no_delta")
    assert not any("duration_seconds" in s for s in _writes(sqls, "asset_throughput")), \
        "engine skip path leaves asset_throughput.duration_seconds as the PRIOR build's value"
    assert any("disposition = 'skip_no_delta'" in s for s in _writes(sqls, "build_run_assets"))
    # A naive join to asset_throughput hands the census the prior build's duration: it must not count.
    earn, cost = _grade(dict(state="complete", disposition="skip_no_delta", reached_completion_write=False,
                             duration_seconds=4.0, rows_written=500), baseline=_BASELINE)
    assert earn["v"] == ac.NA and "skip_no_delta" in earn["measured"], earn
    assert cost["v"] == ac.PASS and "run-prior" in cost["measured"], cost


# ── failure: the engine's error path never reaches the completion write ──

def test_d6_failure_engine_error_path_is_not_a_timing_defect():
    sqls = _sql(_SRC["runner"], "mark_asset_error")
    assert not any("duration_seconds" in s for s in sqls)
    assert any("SET state = 'error'" in s for s in _writes(sqls, "build_run_assets"))
    assert not any("disposition" in s for s in sqls)
    earn, cost = _grade(dict(state="error", disposition="", reached_completion_write=False,
                             duration_seconds=None, rows_written=None), baseline=_BASELINE)
    assert earn["v"] == ac.NA and "before completion" in earn["measured"], earn
    assert cost["v"] == ac.PASS, cost


# ── probe-green: the engine writes NO disposition — the adapter must derive it ──

def test_d6_probe_green_has_no_engine_disposition_so_the_adapter_must_derive_it():
    """F11 finding (adapter obligation for R42–R56, not a census defect): the census classifier keys
    healthy non-execution on `disposition in ("skip_no_delta", "probe_green")`, but the engine's
    `_mark_probe_green` marks build_run_assets `state = 'complete'` with NO disposition, and never
    touches duration_seconds. Engine dispositions are 'build' and 'skip_no_delta' at 8edba0533, plus
    'blocked_dependency' from Packet B1 on; if the engine ever writes 'probe_green' this test fails
    and the adapter note below can be retired."""
    dispositions = _engine_dispositions()
    assert {"build", "skip_no_delta"} <= dispositions <= {"build", "skip_no_delta", "blocked_dependency"}, dispositions
    assert "probe_green" not in dispositions
    sqls = _sql(_SRC["runner"], "_mark_probe_green")
    bra = _writes(sqls, "build_run_assets")
    assert bra and all("SET state = 'complete'" in s and "disposition" not in s for s in bra)
    assert not any("duration_seconds" in s for s in _writes(sqls, "asset_throughput"))
    # What a correct adapter must hand the classifier for this row (complete, disposition NULL,
    # probe receipt present) — and what it grades:
    earn, cost = _grade(dict(state="complete", disposition="probe_green", reached_completion_write=False,
                             duration_seconds=4.0, rows_written=500), baseline=_BASELINE)
    assert earn["v"] == ac.NA and "probe_green" in earn["measured"], earn
    assert cost["v"] == ac.PASS, cost


# ── the legacy ga_* path: the L1 telemetry helper persists its caller's duration, default None ──

def test_d6_legacy_ga_telemetry_path_writes_null_duration_and_is_graded_fail():
    fn = _fn(_SRC["telemetry"], "update_asset_throughput")
    kw = {a.arg: d for a, d in zip(fn.args.kwonlyargs, fn.args.kw_defaults)}
    assert "duration_seconds" in kw and isinstance(kw["duration_seconds"], ast.Constant) \
        and kw["duration_seconds"].value is None
    assert "duration_seconds        = EXCLUDED.duration_seconds" in _SRC["telemetry"]
    duration, _rate = _engine_fn(_SRC["telemetry"], "_compute_duration_and_rate")(25, None)
    assert duration is None
    earn, _cost = _grade(dict(state="complete", disposition="build", reached_completion_write=True,
                              duration_seconds=duration, rows_written=25, is_legacy_telemetry=True))
    assert earn["v"] == ac.FAIL and "_telemetry" in earn["measured"], earn
