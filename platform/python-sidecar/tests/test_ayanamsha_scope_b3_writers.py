"""ONE_AYANAMSHA Phase 1, batch B3: the 20 bo_* writers take their ayanamsha set from ayanamshas_for_chart.

Default (no `charts.build_ayanamshas` column): every writer iterates EXACTLY its old literal list, in the old
order (hard-coded below). Configured subset: exactly that subset, in the writer's historical order.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

from brahmagyan import ayanamsha_scope

WRITERS = Path(__file__).resolve().parents[1] / "pipeline" / "orchestrator" / "writers"
NAMES = [
    "bo_anveshana", "bo_arudha", "bo_bimba", "bo_cdlm_summary", "bo_cgm_motifs", "bo_cgm_paths",
    "bo_chart_gestalt", "bo_drishti", "bo_grounding", "bo_karanajala", "bo_laksana",
    "bo_nakshatra_semantic", "bo_pratijna", "bo_samskara", "bo_sangati", "bo_special_lagna",
    "bo_sudarshana", "bo_upaya", "bo_vargottama_dhana", "bo_yantra_mechanism",
]
# The old literal order of every one of the 20 files (differs from CANONICAL_FIVE).
OLD_ORDER = ["lahiri_chitrapaksha", "raman", "krishnamurti", "surya_siddhanta_classical", "true_chitra"]
CONSTANTS = ("CANONICAL_AYAS", "CANONICAL_AYANAMSHAS")


class _Cur:
    def __init__(self, conn):
        self.conn = conn
        self._row = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.conn.sql.append(sql)
        if "information_schema" in sql:
            self._row = (1,) if self.conn.configured is not None else None
        else:
            self._row = (self.conn.configured,)

    def fetchone(self):
        return self._row


class _Conn:
    def __init__(self, configured=None):
        self.configured = configured
        self.sql: list[str] = []

    def cursor(self):
        return _Cur(self)


@pytest.fixture(autouse=True)
def _fresh_cache():
    ayanamsha_scope.reset_cache()
    yield
    ayanamsha_scope.reset_cache()


@pytest.mark.parametrize("name", NAMES)
def test_source_uses_helper_and_has_no_literal_list(name):
    src = (WRITERS / f"{name}.py").read_text()
    tree = ast.parse(src)
    assert "ayanamshas_for_chart" in src
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)):
            strs = {e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
            assert len(strs & set(ayanamsha_scope.CANONICAL_FIVE)) < 3, f"{name}: literal ayanamsha list"
    consts = [n for n in tree.body if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", None) in CONSTANTS]
    assert len(consts) == 1


@pytest.mark.parametrize("name", NAMES)
def test_default_and_subset_iteration(name):
    pytest.importorskip("psycopg")
    mod = importlib.import_module(f"pipeline.orchestrator.writers.{name}")
    const = next(getattr(mod, c) for c in CONSTANTS if hasattr(mod, c))
    assert const == OLD_ORDER                                   # old constant, element for element
    assert mod._scoped_ayas(_Conn(None), "c") == OLD_ORDER      # column absent / NULL: the old loop
    ayanamsha_scope.reset_cache()
    assert mod._scoped_ayas(_Conn(["krishnamurti", "lahiri_chitrapaksha"]), "c") == [
        "lahiri_chitrapaksha", "krishnamurti"]                   # subset, old relative order
    ayanamsha_scope.reset_cache()
    assert mod._scoped_ayas(_Conn(["true_chitra"]), "c") == ["true_chitra"]


@pytest.mark.parametrize("name", ["bo_samskara", "bo_laksana"])
def test_plan_substeps_keys(name):
    pytest.importorskip("psycopg")
    mod = importlib.import_module(f"pipeline.orchestrator.writers.{name}")
    from pipeline.orchestrator.writers import ContextSpec
    cls = next(v for k, v in vars(mod).items() if k.startswith("Bo") and k.endswith("Writer") and name.split("_")[1].capitalize() in k)
    def ctx(conn):
        return ContextSpec(asset_id=name, build_id="b", db_conn=conn, config={"chart_id": "c", "birth_params": {}})
    assert [s.key for s in cls().plan_substeps(ctx(_Conn(None)))] == [f"aya_{a}" for a in OLD_ORDER]
    ayanamsha_scope.reset_cache()
    assert [s.key for s in cls().plan_substeps(ctx(_Conn(["lahiri_chitrapaksha"])))] == ["aya_lahiri_chitrapaksha"]
