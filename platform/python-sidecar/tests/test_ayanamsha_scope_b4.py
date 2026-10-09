"""ONE_AYANAMSHA batch B4: CLI / router sites take the ayanamsha set from brahmagyan.ayanamsha_scope.

Migrated: scripts/l2_node_orphan_census.py, run_bo_samskara_parallel.py, _rebuild_ga_structural_v2.py
(chart-scoped, via ayanamshas_for_chart) and routers/jaimini.py (validation vocabulary, from CANONICAL_FIVE).
Source-level (AST) pins run without psycopg; the behavioural parts that need psycopg or fastapi skip without it.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from concurrent.futures import Future
from pathlib import Path

import pytest

from brahmagyan import ayanamsha_scope as sc

SIDECAR = Path(__file__).resolve().parents[1]
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
OLD_FIVE = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
OLD_CENSUS_ORDER = ("lahiri_chitrapaksha", "raman", "krishnamurti", "surya_siddhanta_classical", "true_chitra")
MIGRATED = ["scripts/l2_node_orphan_census.py", "run_bo_samskara_parallel.py",
            "_rebuild_ga_structural_v2.py", "routers/jaimini.py"]
CHART_SCOPED = ["scripts/l2_node_orphan_census.py", "run_bo_samskara_parallel.py",
                "_rebuild_ga_structural_v2.py"]


def _tree(rel: str) -> ast.AST:
    return ast.parse((SIDECAR / rel).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _fresh():
    sc.reset_cache()
    yield
    sc.reset_cache()


class ScopeConn:
    """Answers the helper's two statements; anything else is a test error."""

    def __init__(self, configured=None):
        self.configured = configured
        self.sqls: list[str] = []

    def cursor(self):
        conn = self

        class Cur:
            row = None

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def execute(self, sql, params=None):
                s = " ".join(sql.split())
                conn.sqls.append(s)
                if "information_schema.columns" in s:
                    self.row = (1,) if conn.configured is not None else None
                elif s.startswith("SELECT build_ayanamshas FROM charts"):
                    self.row = (conn.configured,)
                else:
                    raise AssertionError(s)

            def fetchone(self):
                return self.row

        return Cur()

    def commit(self):
        raise AssertionError("never commit")

    def close(self):
        raise AssertionError("never close")


# -- source-level pins (no psycopg needed) -------------------------------------------------------------

@pytest.mark.parametrize("rel", MIGRATED)
def test_migrated_file_has_no_literal_list_of_the_five(rel):
    five = set(sc.CANONICAL_FIVE)
    for node in ast.walk(_tree(rel)):
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            hits = {e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)} & five
            assert len(hits) < 3, f"{rel}:{node.lineno} still carries its own list of the five"


@pytest.mark.parametrize("rel", MIGRATED)
def test_migrated_file_imports_the_helper(rel):
    mods = [n for n in ast.walk(_tree(rel)) if isinstance(n, ast.ImportFrom)]
    assert any(m.module == "brahmagyan.ayanamsha_scope" for m in mods), rel


@pytest.mark.parametrize("rel", CHART_SCOPED)
def test_chart_scoped_files_call_ayanamshas_for_chart(rel):
    calls = [n for n in ast.walk(_tree(rel)) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "ayanamshas_for_chart"]
    assert calls, rel


def test_rebuild_script_no_longer_loops_a_writer_constant():
    names = {n.id for n in ast.walk(_tree("_rebuild_ga_structural_v2.py")) if isinstance(n, ast.Name)}
    assert "CANONICAL_AYANAMSHAS" not in names


def test_parallel_runner_no_longer_hardcodes_five_workers():
    src = (SIDECAR / "run_bo_samskara_parallel.py").read_text(encoding="utf-8")
    assert "max_workers=5" not in src and "CANONICAL_AYAS" not in src


# -- l2_node_orphan_census: behaviour (no psycopg import at module level) -----------------------------

def _census():
    spec = importlib.util.spec_from_file_location("l2_census_b4", SIDECAR / "scripts" / "l2_node_orphan_census.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["l2_census_b4"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_census_default_constant_is_the_old_tuple_in_the_old_order():
    assert _census().CANONICAL_AYAS == OLD_CENSUS_ORDER
    assert set(_census().CANONICAL_AYAS) == set(sc.CANONICAL_FIVE)


@pytest.mark.parametrize("configured,expected", [
    (None, OLD_CENSUS_ORDER),                                         # no column / NULL: the old five, old order
    (["lahiri_chitrapaksha"], ("lahiri_chitrapaksha",)),
    (["true_chitra", "raman"], ("raman", "true_chitra")),             # the census's own report order
])
def test_census_main_runs_exactly_the_chart_set(monkeypatch, configured, expected):
    census = _census()
    seen = {}
    conn = ScopeConn(configured)

    def fake_run(c, chart_id, ayas):
        seen["args"] = (c, chart_id, tuple(ayas))
        return {"chart_id": chart_id, "ayanamshas": {}, "totals": {}, "not_examined": False, "passed": True}

    conn.rollback = lambda: None
    conn.close = lambda: None
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setattr(census, "_connect_read_only", lambda url: conn)
    monkeypatch.setattr(census, "run_census", fake_run)
    assert census.main(["--chart-id", CHART, "--json"]) == 0
    assert seen["args"] == (conn, CHART, expected)


# -- routers/jaimini: validation vocabulary stays the default five ------------------------------------

def test_jaimini_validation_set_is_the_old_five_list():
    pytest.importorskip("fastapi")
    from routers import jaimini
    assert jaimini._VALID_AYANAMSHAS == OLD_FIVE
    assert isinstance(jaimini._VALID_AYANAMSHAS, list)


# -- run_bo_samskara_parallel: behaviour (needs psycopg for its worker import) ------------------------

class _InlinePool:
    submitted: list[str] = []
    max_workers = None

    def __init__(self, max_workers=None):
        type(self).max_workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def submit(self, fn, aya, chart_id, db_url, dry_run):
        type(self).submitted.append(aya)
        f: Future = Future()
        f.set_result((aya, 1))
        return f


@pytest.mark.parametrize("configured,expected", [
    (None, OLD_FIVE),
    (["raman"], ["raman"]),
])
def test_parallel_runner_submits_exactly_the_chart_set(monkeypatch, configured, expected):
    psycopg = pytest.importorskip("psycopg")
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    spec = importlib.util.spec_from_file_location("run_bo_samskara_parallel_b4",
                                                  SIDECAR / "run_bo_samskara_parallel.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    class Conn(ScopeConn):
        def close(self):
            pass

    monkeypatch.setattr(psycopg, "connect", lambda *a, **k: Conn(configured))
    _InlinePool.submitted = []
    monkeypatch.setattr(mod, "ProcessPoolExecutor", _InlinePool)
    monkeypatch.setattr(sys, "argv", ["run_bo_samskara_parallel.py", "--dry-run"])
    mod.main()
    assert sorted(_InlinePool.submitted) == sorted(expected)
    assert _InlinePool.max_workers == len(expected)
