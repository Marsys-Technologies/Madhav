"""C37 — stubbed-connection unit tests for platform/scripts/dispatch_v5_small_test_job.py.

No database, no production: `psycopg` is replaced by a recording fake, so the
real statement order of main() is exercised end-to-end. Covered: the steward
flag refusal, the slice marker (one small function), the frozen manifest +
slice-marker digest, the ONE-transaction staging (flip true → stage → flip
false → single commit), --dry-run (same transaction, ROLLBACK, prints the
plan), the dependents refusal, and the registry-row validation.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
DISPATCH = REPO / "platform/scripts/dispatch_v5_small_test_job.py"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

sys.path.insert(0, str(DISPATCH.parent))
import dispatch_v5_small_test_job as dispatch  # noqa: E402


def _load_fresh():
    return importlib.reload(dispatch)


# ── the steward flag refusal (before ANY import of psycopg / DB touch) ───────

def test_refuses_without_both_steward_flags(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    common = ["--run", "all_classes_1y", "--classes", "solar",
              "--horizon-start", "2026-01-01", "--horizon-end", "2026-02-01"]
    for argv in (common, ["--i-am-steward"] + common, ["--after-settled-1"] + common):
        with pytest.raises(SystemExit) as exc:
            _load_fresh().main(argv)
        assert exc.value.code == 2


# ── build_slice_marker ────────────────────────────────────────────────────────

MARKER = {"schema": "gochara_v5_test_slice/1", "run": "all_classes_1y",
          "horizon": ["2026-01-01", "2026-02-01"], "classes": ["solar", "lunar", "eclipse"]}


def test_slice_marker_shape_is_stream_as_definition():
    m = dispatch.build_slice_marker(run="all_classes_1y", classes="solar, lunar ,eclipse",
                                    horizon_start="2026-01-01", horizon_end="2026-02-01")
    assert m == MARKER
    assert set(m) == {"schema", "run", "horizon", "classes"}   # no extra fields, ever


def test_slice_marker_rejects_an_unknown_run():
    with pytest.raises(RuntimeError):
        dispatch.build_slice_marker(run="everything", classes="solar",
                                    horizon_start="2026-01-01", horizon_end="2026-02-01")


def test_slice_marker_rejects_bad_horizons():
    with pytest.raises(RuntimeError):
        dispatch.build_slice_marker(run="one_class_full", classes="solar",
                                    horizon_start="jan", horizon_end="2026-02-01")
    with pytest.raises(RuntimeError):
        dispatch.build_slice_marker(run="one_class_full", classes="solar",
                                    horizon_start="2026-02-01", horizon_end="2026-01-01")
    with pytest.raises(RuntimeError):
        dispatch.build_slice_marker(run="one_class_full", classes=" , ",
                                    horizon_start="2026-01-01", horizon_end="2026-02-01")


def test_manifest_carries_the_slice_marker_and_digests_it():
    candidate = {"asset_id": "ka_gochara_v5", "scope": "per_chart", "depends_on": [],
                 "natural_key_partition": None, "has_cowriters": False}
    marker = dispatch.build_slice_marker(run="all_classes_1y", classes="solar,lunar,eclipse",
                                         horizon_start="2026-01-01", horizon_end="2026-02-01")
    manifest, digest = dispatch.build_small_test_manifest(candidate=candidate, slice_marker=marker)
    assert manifest["version"] == "nirmana-run-manifest/v1"
    assert manifest["scope_target"] == "ka_gochara_v5"
    assert manifest["chart_id"] == CHART_ID
    assert manifest["gochara_v5_test_slice"] == marker
    import hashlib
    canonical = json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── recording fake psycopg ────────────────────────────────────────────────────

class _Harness:
    def __init__(self, *, dependents=None, registry_row=None):
        self.statements: list[str] = []
        self.params: list[tuple] = []
        self.commits: list[int] = []
        self.rollbacks: list[int] = []
        self.dependents = dependents if dependents is not None else []
        self.registry_row = registry_row or {
            "scope": "per_chart", "is_active": False, "has_writer": True,
            "has_substeps": False, "writer_timeout_seconds": 600, "depends_on": [],
        }
        harness = self

        class FakeCur:
            def execute(self, sql, params=None):
                harness.statements.append(sql)
                harness.params.append(params)
                self._last = sql

            def fetchall(self):
                if "ANY(depends_on)" in self._last:
                    return harness.dependents
                return []

            def fetchone(self):
                if "FROM asset_registry WHERE asset_id" in self._last:
                    return harness.registry_row
                if "has_cowriters" in self._last:
                    return {"asset_id": "ka_gochara_v5", "layer": "kala",
                            "scope": "per_chart", "asset_kind": "data",
                            "depends_on": [], "natural_key_partition": None,
                            "has_cowriters": False}
                return None

        class FakeConn:
            autocommit = False

            def cursor(self):
                return FakeCur()

            def commit(self):
                harness.commits.append(len(harness.statements))

            def rollback(self):
                harness.rollbacks.append(len(harness.statements))

            def close(self):
                pass

        self.conn = FakeConn()


def _run_main(harness: _Harness, argv: list[str], capsys):
    fake_psycopg = types.ModuleType("psycopg")
    fake_rows = types.ModuleType("psycopg.rows")
    fake_rows.dict_row = object()
    fake_psycopg.rows = fake_rows
    fake_psycopg.connect = lambda *a, **k: harness.conn
    saved = {k: v for k, v in sys.modules.items() if k.startswith("psycopg")}
    prior_db_url = os.environ.get("DATABASE_URL")
    try:
        sys.modules["psycopg"] = fake_psycopg
        sys.modules["psycopg.rows"] = fake_rows
        os.environ["DATABASE_URL"] = "postgresql://fake/fake"
        _load_fresh().main(argv)
        return capsys.readouterr()
    finally:
        for name in ("psycopg", "psycopg.rows"):
            sys.modules.pop(name, None)
        sys.modules.update(saved)
        if prior_db_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior_db_url


BASE_ARGV = ["--i-am-steward", "--after-settled-1", "--run", "all_classes_1y",
             "--classes", "solar,lunar,eclipse",
             "--horizon-start", "2026-01-01", "--horizon-end", "2026-02-01"]


def test_staging_is_one_transaction_ending_inert(capsys):
    h = _Harness()
    out = _run_main(h, BASE_ARGV, capsys)
    assert len(h.commits) == 1 and not h.rollbacks
    staged = h.statements[: h.commits[0]]
    flips = [s for s in staged if "SET is_active" in s]
    assert flips[0].count("is_active = true") == 1
    assert flips[-1].count("is_active = false") == 1
    assert any("INSERT INTO build_runs" in s and "plan_manifest" in s for s in staged)
    assert any("INSERT INTO build_run_assets" in s for s in staged)
    assert any("asset_throughput" in s and "dormant" in s for s in staged)
    # the staged run names the small-test trigger and carries the slice marker
    run_insert = next(i for i, s in enumerate(h.statements) if "INSERT INTO build_runs" in s)
    params = h.params[run_insert]
    assert params[1] == CHART_ID and params[2] == "ka_gochara_v5"
    assert params[-1] == "gochara-v5-small-test"
    manifest = json.loads(params[4])
    assert manifest["gochara_v5_test_slice"] == MARKER
    assert params[3] == json.dumps(["ka_gochara_v5"])
    # stdout carries ONLY the run_id
    run_id = out.out.strip()
    assert run_id and "\n" not in run_id


def test_dry_run_rolls_back_and_prints_the_plan(capsys):
    h = _Harness()
    out = _run_main(h, BASE_ARGV + ["--dry-run"], capsys)
    assert not h.commits and len(h.rollbacks) == 1
    assert "[dry-run]" in out.err and "nothing written" in out.err
    plan = json.loads(out.out)
    assert plan["triggered_by"] == "gochara-v5-small-test"
    assert plan["asset_id"] == "ka_gochara_v5" and plan["chart_id"] == CHART_ID
    assert plan["plan_manifest"]["gochara_v5_test_slice"] == MARKER


def test_dependents_refuse_the_dispatch(capsys):
    h = _Harness(dependents=[{"asset_id": "some_other_asset"}])
    with pytest.raises(RuntimeError, match="dependency-free"):
        _run_main(h, BASE_ARGV, capsys)
    assert not h.commits
    assert not any("INSERT INTO build_runs" in s for s in h.statements)


def test_a_nonconforming_registry_row_refuses(capsys):
    bad = {"scope": "per_chart", "is_active": False, "has_writer": True,
           "has_substeps": True, "writer_timeout_seconds": 7200, "depends_on": []}
    h = _Harness(registry_row=bad)
    with pytest.raises(RuntimeError, match="has_substeps"):
        _run_main(h, BASE_ARGV, capsys)
    assert not h.commits
    assert not any("INSERT INTO build_runs" in s for s in h.statements)


def test_help_runs(capsys):
    with pytest.raises(SystemExit) as exc:
        _load_fresh().main(["--help"])
    assert exc.value.code == 0
    assert "--i-am-steward" in capsys.readouterr().out
