"""NIRMĀṆA L2-W3 — the three D-SYNTHESIS cross-system rollups.

Adjudication #1720 granted a per-signal redefinition of system_convergence_count and
made NULL-not-empty the campaign's standing convention for denormalised array columns.
These tests pin the parts of that contract that live in code rather than in SQL results.
"""
from __future__ import annotations

import os
import re
import sys
import importlib.util
import types
import unittest

_HERE = os.path.dirname(__file__)
_SIDECAR = os.path.abspath(os.path.join(_HERE, "../.."))
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

_WRITERS = os.path.join(_SIDECAR, "pipeline", "orchestrator", "writers")


def _load_bo_laksana():
    """Load bo_laksana with a stub package so `from . import WriterBase` resolves."""
    pkg = types.ModuleType("_bl_pkg")
    pkg.__path__ = [_WRITERS]

    class _WriterBase:  # minimal stubs — we only exercise module-level helpers
        pass

    def _register(_asset_id):
        return lambda cls: cls

    for name, obj in (
        ("WriterBase", _WriterBase), ("ContextSpec", object),
        ("WriterResult", object), ("SubStep", object), ("register", _register),
    ):
        setattr(pkg, name, obj)
    sys.modules["_bl_pkg"] = pkg
    spec = importlib.util.spec_from_file_location(
        "_bl_pkg.bo_laksana", os.path.join(_WRITERS, "bo_laksana.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_bl_pkg.bo_laksana"] = mod
    spec.loader.exec_module(mod)
    return mod


BL = _load_bo_laksana()


class _FakeCursor:
    def __init__(self, rowcounts): self._rc = list(rowcounts); self.executed = []
    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self.rowcount = self._rc.pop(0) if self._rc else 0
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _FakeConn:
    def __init__(self, rowcounts): self.cursor_obj = _FakeCursor(rowcounts)
    def cursor(self): return self.cursor_obj


class TestRollupContract(unittest.TestCase):
    def test_returns_rowcounts_for_both_statements(self):
        conn = _FakeConn([9872, 22])
        rollup, contradicts = BL._populate_synthesis_rollups(conn, "chart-1", "lahiri_chitrapaksha")
        self.assertEqual((rollup, contradicts), (9872, 22))

    def test_both_statements_are_chart_and_ayanamsha_scoped(self):
        conn = _FakeConn([1, 1])
        BL._populate_synthesis_rollups(conn, "chart-1", "raman")
        self.assertEqual(len(conn.cursor_obj.executed), 2)
        for sql, params in conn.cursor_obj.executed:
            self.assertEqual(params, {"chart_id": "chart-1", "aya": "raman"})
            # never a chart-wide or all-ayanamsha write
            self.assertIn("%(chart_id)s", sql)
            self.assertIn("%(aya)s", sql)


class TestStorageContract(unittest.TestCase):
    """The three-way NULL / measured-zero / measured-count split, asserted on the SQL."""

    def test_convergence_defaults_to_measured_zero_not_null(self):
        # A signal whose facts resolve but that shares no subject gets 0 — a measured
        # zero. COALESCE over the LEFT JOIN is what produces it.
        self.assertIn("COALESCE(conv.n, 0)", BL._SYNTHESIS_ROLLUP_SQL)
        self.assertIn("LEFT JOIN conv", BL._SYNTHESIS_ROLLUP_SQL)

    def test_signals_without_resolvable_facts_are_never_touched(self):
        # The UPDATE drives off `cons`, which is built from `sig` — an INNER JOIN to
        # chart_facts. A signal with no resolvable constituent facts cannot appear
        # there, so it keeps its NULL without needing an explicit skip.
        self.assertRegex(BL._SYNTHESIS_ROLLUP_SQL, r"FROM\s+bodha_msr_signals s\s+JOIN chart_facts")
        self.assertIn("WHERE m.signal_id = cons.signal_id", BL._SYNTHESIS_ROLLUP_SQL)

    def test_contradicts_array_is_never_written_as_empty(self):
        # bo_upaya reads '{}' as a MEASURED "no contradictions found" and would enable
        # its contradiction_factor term with nothing behind it. Only rows present in
        # bodha_contradictions are updated; everything else keeps NULL.
        sql = BL._CONTRADICTS_SQL
        self.assertIn("array_agg(DISTINCT other)", sql)
        self.assertIn("WHERE m.signal_id = agg.sid", sql)
        self.assertNotIn("'{}'", sql)
        self.assertNotIn("COALESCE(agg.arr", sql)

    def test_contradictions_are_symmetric(self):
        # A contradiction is mutual: both signals must list the other, so the source
        # is UNION ALLed in both directions before aggregation.
        self.assertIn("UNION ALL", BL._CONTRADICTS_SQL)
        self.assertIn("SELECT signal_a_id AS sid, signal_b_id AS other", BL._CONTRADICTS_SQL)
        self.assertIn("SELECT signal_b_id, signal_a_id", BL._CONTRADICTS_SQL)


class TestConsensusIsSubjectLevel(unittest.TestCase):
    def test_consensus_counts_traditions_not_facts(self):
        # Fact-level cross-tradition overlap was measured at 2 facts chart-wide, so a
        # definition keyed on a shared fact_id is dead on arrival. The count is over
        # DISTINCT signal_tradition, grouped by fact_subject.
        self.assertIn("count(DISTINCT signal_tradition)", BL._SYNTHESIS_ROLLUP_SQL)
        self.assertRegex(BL._SYNTHESIS_ROLLUP_SQL, r"SELECT fact_subject, count\(DISTINCT signal_tradition\)")

    def test_convergence_and_consensus_are_different_quantities(self):
        # They are computed from different CTEs. If one were ever assigned from the
        # other's expression, the column names would stop meaning what they say.
        conv_assign = re.search(r"system_convergence_count\s*=\s*(.+)", BL._SYNTHESIS_ROLLUP_SQL)
        cons_assign = re.search(r"cross_system_consensus_count\s*=\s*(.+)", BL._SYNTHESIS_ROLLUP_SQL)
        self.assertIsNotNone(conv_assign)
        self.assertIsNotNone(cons_assign)
        conv_expr = conv_assign.group(1).strip().rstrip(",")
        cons_expr = cons_assign.group(1).strip().rstrip(",")
        self.assertNotEqual(conv_expr, cons_expr)
        # each reads its OWN CTE — swapping them would leave both column names lying
        self.assertIn("conv.n", conv_expr)
        self.assertIn("cons.n_trad", cons_expr)


if __name__ == "__main__":
    unittest.main()
