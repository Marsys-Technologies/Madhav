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


def test_guard_ignores_table_names_inside_comments():
    """A commented-out query or an explanatory `# reads X` note must not read as
    a real dependency — a false positive would either spuriously flag a HARD
    violation on a table the writer doesn't actually touch, or (worse) let a
    stale comment mask a genuine missing depends_on edge on the real read."""
    reg = _synthetic_registry()
    src_python_comment = (
        "@register('ph_pratikara')\n"
        "# Old approach used to read kala_convergence directly via FROM kala_convergence\n"
        "SQL = 'SELECT * FROM phala_mitigation'\n"
    )
    res = g.evaluate(reg, _REAL, [("ph_pratikara.py", src_python_comment)])
    assert res["hard"] == [], (
        "table name inside a '#' comment must not be treated as a real read: " + repr(res)
    )

    src_sql_comment = (
        "@register('ph_pratikara')\n"
        "SQL = '''\n"
        "-- FROM kala_convergence (old, no longer used)\n"
        "SELECT * FROM phala_mitigation\n"
        "'''\n"
    )
    res2 = g.evaluate(reg, _REAL, [("ph_pratikara.py", src_sql_comment)])
    assert res2["hard"] == [], (
        "table name inside a SQL '--' comment must not be treated as a real read: " + repr(res2)
    )


def test_read_through_served_view_is_a_read_of_its_base_table():
    """#3869 verifier F1 (N.8): migration 1405 moved the K9 readers onto `kala_convergence_served`, a view no asset
    owns. Recorded under its own name it is skipped (no producer) and the reader escapes the edge check; it must
    count as a read of kala_convergence, so a missing depends_on edge on ka_sangam is flagged."""
    reg = _synthetic_registry()
    src = "@register('ph_pratikara')\nSQL = 'SELECT * FROM kala_convergence_served WHERE chart_id=%s'\n"
    real = _REAL | {"kala_convergence_served"}  # information_schema.tables lists views too
    res = g.evaluate(reg, real, [("ph_pratikara.py", src)])
    assert any("ph_pratikara" in h and "kala_convergence" in h and "ka_sangam" in h for h in res["hard"]), res
    reg["ph_pratikara"]["depends_on"] = ["ka_sangam"]
    assert g.evaluate(reg, real, [("ph_pratikara.py", src)])["hard"] == []


def test_every_served_view_in_migrations_is_mapped():
    """A new `*_served` view (a later K9 generation scope) must be added to _VIEW_BASE_TABLES, or its readers are
    invisible to the guard again. Scans the committed migrations for the view definitions."""
    import re
    from pathlib import Path
    mig = Path(g.__file__).resolve().parents[3] / "migrations"
    found = set()
    for f in mig.glob("*.sql"):
        found.update(m.lower() for m in re.findall(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:public\.)?([a-z0-9_]+_served)\b",
            f.read_text(encoding="utf-8", errors="ignore"), re.IGNORECASE))
    assert "kala_convergence_served" in found, "migration scan found no served view; the scan is broken"
    assert found <= set(g._VIEW_BASE_TABLES), sorted(found - set(g._VIEW_BASE_TABLES))


# ── Integration: the live DAG is edge-complete ───────────────────────────────

@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_live_registry_has_no_hard_violations():
    res = g.analyze()
    assert res["checked_assets"] > 50, f"too few assets scanned: {res['checked_assets']}"
    assert res["hard"] == [], (
        "DAG edge-completeness violations — a writer reads a producer table whose "
        "asset is not in its depends_on closure:\n  " + "\n  ".join(res["hard"])
    )
