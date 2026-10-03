"""C38 — stubbed-connection unit tests for platform/scripts/teardown_v5_small_test_job.py.

No database, no production: `psycopg` is replaced by a recording fake. Covered:
the happy path (all five refusal checks pass; the deletes run chart/run-scoped
in ONE transaction; the registry row is kept, restored inert and validated),
each refusal (published manifest, generation seal, serving authority, active
runs, '5.0' rows with no small-test run behind them), --dry-run (counts per
table, rollback, nothing deleted), and a non-conforming post-teardown registry
row.
"""
from __future__ import annotations

import importlib
import os
import sys
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "platform/scripts/teardown_v5_small_test_job.py"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "gochara-v5-small-test"

sys.path.insert(0, str(SCRIPT.parent))
import teardown_v5_small_test_job as teardown_mod  # noqa: E402

REGISTRY_ROW = {
    "scope": "per_chart", "is_active": False, "has_writer": True,
    "has_substeps": False, "writer_timeout_seconds": 600, "depends_on": [],
}


class _Harness:
    def __init__(self, *, published=None, seal=None, authority_generation=None,
                 active_runs=None, data_counts=None, smalltest_runs=1,
                 registry_row=None):
        self.statements: list[str] = []
        self.params: list[tuple] = []
        self.commits = 0
        self.rollbacks = 0
        self.published = published
        self.seal = seal
        self.authority_generation = authority_generation
        self.active_runs = active_runs or []
        self.data_counts = data_counts or {}
        self.smalltest_runs = smalltest_runs
        self.registry_row = registry_row or dict(REGISTRY_ROW)
        harness = self

        class FakeCur:
            def execute(self, sql, params=None):
                harness.statements.append(sql)
                harness.params.append(params)
                self._last = sql

            def fetchall(self):
                if "state IN ('planned'" in self._last:
                    return harness.active_runs
                return []

            def fetchone(self):
                sql = self._last
                if "status = 'published'" in sql:
                    return harness.published
                if "FROM ka_gochara_generation_seal" in sql:
                    return harness.seal
                if "FROM kala_gochara_authority" in sql:
                    if harness.authority_generation is None:
                        return None
                    return {"authoritative_generation": harness.authority_generation}
                if "FROM asset_registry WHERE asset_id" in sql:
                    return harness.registry_row
                if "count(*) AS n FROM build_runs" in sql:
                    return {"n": harness.smalltest_runs}
                if "FROM build_run_assets" in sql:
                    return {"n": harness.data_counts.get("build_run_assets", 0)}
                if "FROM asset_throughput" in sql:
                    return {"n": harness.data_counts.get("asset_throughput", 0)}
                for table in ("kala_gochara_windows", "kala_gochara_contacts",
                              "kala_gochara_coverage", "kala_gochara_publication"):
                    if f"FROM {table}" in sql:
                        return {"n": harness.data_counts.get(table, 0)}
                return None

        class FakeConn:
            autocommit = False

            def cursor(self):
                return FakeCur()

            def commit(self):
                harness.commits += 1

            def rollback(self):
                harness.rollbacks += 1

            def close(self):
                pass

        self.conn = FakeConn()


def _run(harness: _Harness, *, dry_run: bool = False):
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
        importlib.reload(teardown_mod)
        teardown_mod.teardown(dry_run=dry_run)
    finally:
        for name in ("psycopg", "psycopg.rows"):
            sys.modules.pop(name, None)
        sys.modules.update(saved)
        if prior_db_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior_db_url


DATA = {"kala_gochara_windows": 3, "kala_gochara_contacts": 1,
        "kala_gochara_coverage": 2, "kala_gochara_publication": 0}


def test_happy_path_one_transaction_chart_scoped_registry_kept():
    h = _Harness(data_counts=dict(DATA))
    _run(h)
    assert h.commits == 1 and h.rollbacks == 0
    deletes = [s for s in h.statements if s.lstrip().startswith("DELETE")]
    assert len(deletes) == 7
    # the build bookkeeping is scoped to the small-test trigger AND the chart
    run_deletes = [s for s in deletes if "build_run" in s]
    assert len(run_deletes) == 2
    for s in deletes:
        i = h.statements.index(s)
        params = h.params[i]
        if "build_run" in s:
            assert params == (TRIGGERED_BY, CHART_ID)
        elif "asset_throughput" in s:
            assert params == ("ka_gochara_v5", CHART_ID)
        else:
            assert "generation = '5.0'" in s and params == (CHART_ID,)
    # the registry row is NOT deleted — restored inert and validated in the
    # same transaction
    assert not any("DELETE FROM asset_registry" in s for s in h.statements)
    flips = [s for s in h.statements if "SET is_active" in s]
    assert len(flips) == 1 and "is_active = false" in flips[0]


def test_refuses_a_published_manifest():
    h = _Harness(published={"manifest_id": "m1"})
    with pytest.raises(RuntimeError, match="PUBLISHED"):
        _run(h)
    assert h.commits == 0 and h.rollbacks == 1
    assert not any(s.lstrip().startswith("DELETE") for s in h.statements)


def test_refuses_a_generation_seal():
    h = _Harness(seal={"manifest_id": "m9"})
    with pytest.raises(RuntimeError, match="seal"):
        _run(h)
    assert h.commits == 0
    assert not any(s.lstrip().startswith("DELETE") for s in h.statements)


def test_refuses_a_serving_generation():
    h = _Harness(authority_generation="5.0")
    with pytest.raises(RuntimeError, match="serving"):
        _run(h)
    assert h.commits == 0
    assert not any(s.lstrip().startswith("DELETE") for s in h.statements)


def test_refuses_active_execution():
    h = _Harness(active_runs=[{"id": "r1", "state": "running"}])
    with pytest.raises(RuntimeError, match="active build_runs"):
        _run(h)
    assert h.commits == 0
    assert not any(s.lstrip().startswith("DELETE") for s in h.statements)


def test_refuses_50_rows_without_a_smalltest_run():
    h = _Harness(data_counts=dict(DATA), smalltest_runs=0)
    with pytest.raises(RuntimeError, match="not produced by a small-test run"):
        _run(h)
    assert h.commits == 0
    assert not any(s.lstrip().startswith("DELETE") for s in h.statements)


def test_dry_run_lists_counts_and_rolls_back(capsys):
    h = _Harness(data_counts={**DATA, "build_run_assets": 1, "asset_throughput": 1})
    _run(h, dry_run=True)
    assert h.commits == 0 and h.rollbacks == 1
    assert not any(s.lstrip().startswith("DELETE") for s in h.statements)
    out = capsys.readouterr().out
    assert "kala_gochara_windows\t3" in out
    assert "kala_gochara_coverage\t2" in out
    assert "build_runs\t1" in out
    assert "build_run_assets\t1" in out


def test_nonconforming_registry_row_after_teardown_rolls_back():
    bad = dict(REGISTRY_ROW, writer_timeout_seconds=7200)
    h = _Harness(data_counts=dict(DATA), registry_row=bad)
    with pytest.raises(RuntimeError, match="writer_timeout_seconds"):
        _run(h)
    assert h.commits == 0 and h.rollbacks == 1


def test_registry_row_missing_is_a_loud_failure():
    h = _Harness(data_counts=dict(DATA), registry_row=None)
    # _Harness replaces None with the default; force the missing-row path
    h.registry_row = None
    with pytest.raises(RuntimeError, match="missing"):
        _run(h)
    assert h.commits == 0
