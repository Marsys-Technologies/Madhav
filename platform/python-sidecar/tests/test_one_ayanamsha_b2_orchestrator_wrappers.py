"""ONE_AYANAMSHA Phase 1, batch B2: the 13 orchestrator ga_* wrappers take their ayanamsha set from
`ayanamshas_for_chart(ctx.db_conn, ctx.config['chart_id'])`.

* Default (no `charts.build_ayanamshas` column): plan_substeps yields exactly the old substep keys.
* Configured subset: plan_substeps yields exactly that subset (substep keys unchanged in shape).
* AST pin (runs without psycopg): each file calls `ayanamshas_for_chart` and holds no literal list of >= 3 of
  the five ids.

The behavioural part imports the writer modules; modules that need psycopg / the engine at import time are
skipped (importorskip) when it is absent -- CI has none.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from brahmagyan import ayanamsha_scope as sc

SIDECAR = Path(__file__).resolve().parents[1]
WRITERS = SIDECAR / "pipeline" / "orchestrator" / "writers"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
FIVE = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]

# module -> (class name, substep-key formatter, trailing substeps that are NOT ayanamsha passes)
CASES = {
    "ga_ayurdaya": ("GaAyurdayaWriter", "ayanamsha_{}", []),
    "ga_condition": ("GaConditionWriter", "ayanamsha_{}", []),
    "ga_medical": ("GaMedicalWriter", "ayanamsha_{}", []),
    "ga_nakshatra": ("NakshatraWriter", "ayanamsha:{}", ["cross_ayanamsha"]),
    "ga_prashna": ("GaPrashnaWriter", "ayanamsha_{}", []),
    "ga_sensitive": ("GaSensitiveWriter", "ayanamsha:{}", []),
    "ga_sensitive_degree": ("GaSensitiveDegreeWriter", "ayanamsha_{}", []),
    "ga_structural": ("GaStructuralWriter", "ayanamsha_{}", []),
    "ga_transit_anchors": ("GaTransitAnchorsWriter", "ayanamsha_{}", []),
    "ga_vargas": ("GaVargasWriter", "{}", []),
    "ga_vastu": ("GaVastuWriter", "ayanamsha_{}", []),
    "ga_vichara": ("GaVicharaWriter", "ayanamsha_{}", []),
    "ga_yoga": ("GaYogaWriter", "ayanamsha_{}", []),
}
# Three adapters historically iterated krishnamurti BEFORE true_chitra; for the default set that order is kept
# exactly (coordinator rule), via a private _LOCAL_ORDER derived by position from CANONICAL_FIVE.
LEGACY_ORDER = ["lahiri_chitrapaksha", "krishnamurti", "true_chitra", "raman", "surya_siddhanta_classical"]
LOCAL_ORDER_FILES = {"ga_ayurdaya", "ga_medical", "ga_sensitive_degree"}


def _expected_order(mod_name):
    return list(LEGACY_ORDER if mod_name in LOCAL_ORDER_FILES else FIVE)


# Files whose own module-level default constant must now be derived from the helper (not a literal list).
CONSTANT_FILES = {
    "ga_ayurdaya": "_AYANAMSHAS", "ga_medical": "_AYANAMSHAS", "ga_sensitive_degree": "_AYANAMSHAS",
    "ga_transit_anchors": "_AYANAMSHAS", "ga_yoga": "CANONICAL_AYANAMSHAS", "ga_vichara": "CANONICAL_AYANAMSHAS",
}


class _Cur:
    def __init__(self, conn):
        self.c, self.row = conn, None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "information_schema.columns" in s:
            self.row = (1,) if self.c.value is not None else None
        elif s.startswith("SELECT build_ayanamshas FROM charts WHERE id = %s::uuid"):
            self.row = (self.c.value,)
        else:
            raise AssertionError(f"unexpected SQL from plan_substeps: {s}")

    def fetchone(self):
        return self.row


class _Conn:
    """No build_ayanamshas column when value is None; the configured value otherwise."""
    def __init__(self, value=None):
        self.value = value

    def cursor(self):
        return _Cur(self)

    def commit(self):
        raise AssertionError("a writer must never commit ctx.db_conn")

    def close(self):
        raise AssertionError("a writer must never close ctx.db_conn")


def _ctx(value=None):
    return SimpleNamespace(db_conn=_Conn(value), config={"chart_id": CHART}, dry_run=True, build_id="b")


@pytest.fixture(autouse=True)
def _fresh_cache():
    sc.reset_cache()
    yield
    sc.reset_cache()


def _load(mod_name):
    mod = pytest.importorskip(f"pipeline.orchestrator.writers.{mod_name}")
    cls_name, fmt, tail = CASES[mod_name]
    return getattr(mod, cls_name), fmt, tail


# ---- source-level pins (no psycopg needed) ---------------------------------------------------------------

def _tree(mod_name):
    return ast.parse((WRITERS / f"{mod_name}.py").read_text(encoding="utf-8"))


@pytest.mark.parametrize("mod_name", sorted(CASES))
def test_source_uses_ayanamshas_for_chart_in_plan_substeps(mod_name):
    cls_name = CASES[mod_name][0]
    tree = _tree(mod_name)
    cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls_name)
    plan = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "plan_substeps")
    calls = [n for n in ast.walk(plan) if isinstance(n, ast.Call)
             and getattr(n.func, "id", None) == "ayanamshas_for_chart"]
    assert len(calls) == 1, f"{mod_name}.plan_substeps must call ayanamshas_for_chart exactly once"
    args = ast.unparse(calls[0])
    assert "ctx.db_conn" in args and "chart_id" in args


@pytest.mark.parametrize("mod_name", sorted(CASES))
def test_source_has_no_literal_list_of_the_five(mod_name):
    for node in ast.walk(_tree(mod_name)):
        if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
            elts = node.keys if isinstance(node, ast.Dict) else node.elts
            hits = {e.value for e in elts if isinstance(e, ast.Constant) and isinstance(e.value, str)} & set(FIVE)
            assert len(hits) < 3, f"{mod_name}:{node.lineno} still carries a literal ayanamsha list"


@pytest.mark.parametrize("mod_name", sorted(CONSTANT_FILES))
def test_module_default_constant_is_derived_from_the_helper(mod_name):
    name = CONSTANT_FILES[mod_name]
    assigns = [n for n in _tree(mod_name).body
               if (isinstance(n, ast.Assign) and any(getattr(t, "id", None) == name for t in n.targets))
               or (isinstance(n, ast.AnnAssign) and getattr(n.target, "id", None) == name)]
    assert len(assigns) == 1
    value = ast.unparse(assigns[0].value)
    assert "CANONICAL_FIVE" in value or (mod_name in LOCAL_ORDER_FILES and "_LOCAL_ORDER" in value)


@pytest.mark.parametrize("mod_name", sorted(LOCAL_ORDER_FILES))
def test_local_order_is_derived_by_position_from_canonical_five(mod_name):
    assigns = [n for n in _tree(mod_name).body if isinstance(n, ast.Assign)
               and any(getattr(t, "id", None) == "_LOCAL_ORDER" for t in n.targets)]
    assert len(assigns) == 1 and "CANONICAL_FIVE" in ast.unparse(assigns[0].value)
    mod = pytest.importorskip(f"pipeline.orchestrator.writers.{mod_name}")
    assert list(mod._LOCAL_ORDER) == LEGACY_ORDER


# ---- behaviour -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("mod_name", sorted(CASES))
def test_default_plans_all_five(mod_name):
    cls, fmt, tail = _load(mod_name)
    keys = [s.key for s in cls().plan_substeps(_ctx())]
    assert keys == [fmt.format(a) for a in _expected_order(mod_name)] + tail


@pytest.mark.parametrize("mod_name", sorted(CASES))
def test_configured_subset_plans_exactly_that_subset(mod_name):
    cls, fmt, tail = _load(mod_name)
    keys = [s.key for s in cls().plan_substeps(_ctx(["lahiri_chitrapaksha"]))]
    assert keys == [fmt.format("lahiri_chitrapaksha")] + tail
    sc.reset_cache()
    keys = [s.key for s in cls().plan_substeps(_ctx(["raman", "true_chitra"]))]   # canonical order, not given order
    assert keys == [fmt.format("true_chitra"), fmt.format("raman")] + tail
    sc.reset_cache()
    keys = [s.key for s in cls().plan_substeps(_ctx(["true_chitra", "krishnamurti"]))]
    order = _expected_order(mod_name)
    assert keys == [fmt.format(a) for a in order if a in ("true_chitra", "krishnamurti")] + tail


@pytest.mark.parametrize("mod_name", ["ga_yoga", "ga_vichara", "ga_nakshatra", "ga_ayurdaya", "ga_medical",
                                      "ga_sensitive_degree", "ga_transit_anchors", "ga_prashna"])
def test_exported_default_constant_still_the_five(mod_name):
    mod = pytest.importorskip(f"pipeline.orchestrator.writers.{mod_name}")
    const = getattr(mod, CONSTANT_FILES.get(mod_name, "CANONICAL_AYANAMSHAS"))
    assert list(const) == _expected_order(mod_name)
