"""
test_phala_bodha_no_default_chart.py -- SS N-384 (PR-S6), item 3 (phala + bodha route modules).

No route module may carry a chart as a DEFAULT: `chart_id` is a required field/param on every
request (FastAPI answers 422 without it), and no module-level NATIVE_CHART_ID constant (with an
env-var fallback to a real chart) may sit around to be used as one. The static checks read the
source (AST), so they run in CI without psycopg or a database.

Two modules legitimately keep a NATIVE_CHART_ID comparison and are named here with the reason:
  muhurta.py     -- a native-specific signal-activation branch (pending the owner's decision)
  l4_anchors.py  -- a native-specific anchor catalogue guard; its router is not mounted
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

_SIDECAR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))

BRAHMAGYAN = _SIDECAR / "brahmagyan"
MODULES = [
    "phala/anchors.py", "phala/muhurta.py", "phala/outlook.py",
    "phala/l4_anchors.py", "phala/l4_muhurta.py", "phala/l4_outlook.py",
    "bodha/bo_2-5.py",
]
KEEPS_NATIVE_COMPARISON = {
    "phala/muhurta.py": "native-specific signal-activation branch, owner decision pending",
    "phala/l4_anchors.py": "native-specific anchor catalogue guard; router not mounted",
}
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def _tree(rel: str) -> ast.Module:
    return ast.parse((BRAHMAGYAN / rel).read_text())


def _is_required_field(value: ast.expr | None) -> bool:
    """True when an annotated chart_id has no default (bare annotation or Field(...))."""
    if value is None:
        return True
    if isinstance(value, ast.Call) and getattr(value.func, "id", getattr(value.func, "attr", "")) in (
        "Field", "PydanticField", "Query", "Path",
    ):
        if value.args:
            return isinstance(value.args[0], ast.Constant) and value.args[0].value is Ellipsis
        return not any(k.arg in ("default", "default_factory") for k in value.keywords)
    return False


@pytest.mark.parametrize("rel", MODULES)
def test_every_chart_id_field_and_param_is_required(rel: str) -> None:
    tree = _tree(rel)
    seen = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "chart_id":
            seen += 1
            assert _is_required_field(node.value), f"{rel}:{node.lineno} chart_id has a default"
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            positional = args.posonlyargs + args.args
            defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
            for a, d in list(zip(positional, defaults)) + list(zip(args.kwonlyargs, args.kw_defaults)):
                if a.arg != "chart_id":
                    continue
                seen += 1
                if d is not None:
                    # only the library/query functions may default to None-like; never to a constant chart
                    assert not (isinstance(d, ast.Constant) and isinstance(d.value, str) and UUID_RE.match(d.value)), \
                        f"{rel}:{node.lineno} chart_id defaults to a literal chart"
                    assert not (isinstance(d, ast.Name) and "NATIVE" in d.id), \
                        f"{rel}:{node.lineno} chart_id defaults to {d.id}"
    assert seen >= 1, f"{rel}: no chart_id declaration found -- the scan would be vacuous"


@pytest.mark.parametrize("rel", MODULES)
def test_no_module_level_native_chart_default(rel: str) -> None:
    tree = _tree(rel)
    defined = [
        n for n in tree.body
        if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "NATIVE_CHART_ID" for t in n.targets)
    ]
    if rel in KEEPS_NATIVE_COMPARISON:
        assert defined, f"{rel} is listed as keeping NATIVE_CHART_ID but no longer defines it; drop it from the keep-list"
        return
    assert defined == [], f"{rel}: module-level NATIVE_CHART_ID (a default chart) is back"
    literals = [
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and UUID_RE.match(n.value)
    ]
    assert literals == [], f"{rel}: a literal chart UUID is in code: {len(literals)}"


def test_l4_muhurta_gate_requires_chart_id_and_uses_it(monkeypatch) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from brahmagyan.phala import l4_muhurta as mod

    seen: list[str] = []

    def fake_query_muhurta(*, chart_id, action_type, horizon_days):
        seen.append(chart_id)
        return {"windows": [{"quality_score": 0.5}]}

    monkeypatch.setattr(mod, "query_muhurta", fake_query_muhurta)
    app = FastAPI()
    app.include_router(mod.router)
    c = TestClient(app)

    r = c.get("/phala/query_muhurta/gate")
    assert r.status_code == 422 and seen == []

    other = "aaaaaaaa-0000-4000-8000-00000000000a"
    r = c.get("/phala/query_muhurta/gate", params={"chart_id": other})
    assert r.status_code == 200
    assert set(seen) == {other}


@pytest.mark.parametrize("rel,url,body", [
    ("phala.anchors", "/phala/event_anchors", {}),
    ("phala.muhurta", "/phala/muhurta_finder", {}),
    ("phala.outlook", "/phala/outlook", {}),
    ("phala.l4_anchors", "/phala/query_phala_anchors", {}),
    ("phala.l4_muhurta", "/phala/query_muhurta", {"action_type": "start_business"}),
    ("phala.l4_outlook", "/phala/phala_outlook", {}),
    ("bodha.bo_2-5", "/query_signals_lens", {}),
])
def test_post_without_chart_id_is_422_on_the_real_routers(rel: str, url: str, body: dict) -> None:
    """Behaviour of the real routers (skipped where psycopg is not installed, e.g. CI)."""
    import importlib
    pytest.importorskip("psycopg")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    mod = importlib.import_module(f"brahmagyan.{rel}")
    app = FastAPI()
    app.include_router(mod.router)
    r = TestClient(app).post(url, json=body)
    assert r.status_code == 422
    assert any(e["loc"][-1] == "chart_id" for e in r.json()["detail"])
