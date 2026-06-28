"""
Tests for the DAG edge-completeness guard (pipeline.orchestrator.dag_edge_guard).

Two layers:
  * Unit (no DB): feed evaluate() a synthetic registry + writer text and assert it
    BOTH flags a real missing edge AND clears it once declared — proves the guard
    has teeth and won't drift into a no-op.
  * Integration (needs DATABASE_URL): assert the LIVE registry has zero hard
    edge-completeness violations. This is the CI gate that fails when a writer adds
    an undeclared cross-asset read.
"""
from __future__ import annotations

import os
import pytest

from pipeline.orchestrator import dag_edge_guard as g


# ── Unit: the detection logic has teeth ──────────────────────────────────────

def _synthetic_registry():
    # producer 'ka_sangam' -> table kala_convergence; consumer 'ph_pratikara' reads it.
    return {
        "ka_sangam": {
            "asset_id": "ka_sangam", "scope": "per_chart",
            "target_table": "kala_convergence", "count_sql": "SELECT count(*) FROM kala_convergence",
            "depends_on": [],
        },
        "ph_pratikara": {
            "asset_id": "ph_pratikara", "scope": "per_chart",
            "target_table": "phala_mitigation", "count_sql": "SELECT count(*) FROM phala_mitigation",
            "depends_on": [],  # MISSING ka_sangam
        },
    }


_REAL = {"kala_convergence", "phala_mitigation"}
_CONSUMER_SRC = "@register('ph_pratikara')\nSQL = 'SELECT * FROM kala_convergence WHERE chart_id=%s'\n"


def test_guard_flags_missing_edge():
    reg = _synthetic_registry()
    res = g.evaluate(reg, _REAL, [("ph_pratikara.py", _CONSUMER_SRC)])
    assert any("ph_pratikara" in h and "kala_convergence" in h and "ka_sangam" in h
               for h in res["hard"]), res


def test_guard_clears_when_edge_declared():
    reg = _synthetic_registry()
    reg["ph_pratikara"]["depends_on"] = ["ka_sangam"]  # declare it
    res = g.evaluate(reg, _REAL, [("ph_pratikara.py", _CONSUMER_SRC)])
    assert res["hard"] == [], res


def test_guard_ignores_self_read_and_globals():
    reg = _synthetic_registry()
    src = ("@register('ka_sangam')\n"
           "A = 'SELECT * FROM kala_convergence'  -- own output\n"
           "B = 'SELECT * FROM bg_transit_rules'  -- L0 global, ungated\n")
    res = g.evaluate(reg, _REAL | {"bg_transit_rules"}, [("ka_sangam.py", src)])
    assert res["hard"] == [], res


# ── Integration: the live DAG is edge-complete ───────────────────────────────

@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_live_registry_has_no_hard_violations():
    res = g.analyze()
    assert res["checked_assets"] > 50, f"too few assets scanned: {res['checked_assets']}"
    assert res["hard"] == [], (
        "DAG edge-completeness violations — a writer reads a producer table whose "
        "asset is not in its depends_on closure:\n  " + "\n  ".join(res["hard"])
    )
