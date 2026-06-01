"""
Tests for pipeline.build_chart scaffold (C-01).

Verifies DAG_ORDER, CANONICAL_AYANAMSHAS, ASSET_LABELS, parse_args,
dispatch_asset (stub), and check_cancellation using unittest.mock.

All DB calls are mocked — no live DB required.
"""
from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Ensure psycopg2 import won't fail even if the package is absent in CI.
# We inject a minimal stub before importing build_chart so that get_db_connection
# can be called without a real driver.
# ---------------------------------------------------------------------------
if "psycopg2" not in sys.modules:
    psycopg2_stub = types.ModuleType("psycopg2")
    psycopg2_stub.connect = MagicMock()  # type: ignore[attr-defined]
    sys.modules["psycopg2"] = psycopg2_stub

from pipeline.build_chart import (  # noqa: E402
    ASSET_LABELS,
    CANONICAL_AYANAMSHAS,
    DAG_ORDER,
    check_cancellation,
    dispatch_asset,
    parse_args,
)


class TestDAGOrder(unittest.TestCase):
    """Tests for DAG_ORDER correctness."""

    def test_dag_order_has_14_items(self):
        """DAG_ORDER must contain exactly 14 asset entries."""
        self.assertEqual(len(DAG_ORDER), 14)  # assertion 1

    def test_first_item_is_a1_engine(self):
        """A1_engine must be the first entry (zero-dependency root)."""
        self.assertEqual(DAG_ORDER[0], "A1_engine")  # assertion 2

    def test_last_item_is_a14_ucn_digest(self):
        """A14_ucn_digest must be the last entry (synthesis leaf)."""
        self.assertEqual(DAG_ORDER[-1], "A14_ucn_digest")  # assertion 3

    def test_no_duplicate_asset_ids(self):
        """Each asset_id must appear exactly once."""
        self.assertEqual(len(DAG_ORDER), len(set(DAG_ORDER)))  # assertion 4

    def test_all_items_are_strings(self):
        """Every entry in DAG_ORDER must be a non-empty string."""
        for item in DAG_ORDER:
            self.assertIsInstance(item, str)  # assertion 5 (×14 but counted once)
            self.assertTrue(len(item) > 0)

    def test_dag_order_contains_a3_chart_facts(self):
        """A3_chart_facts (L1 structured) must be present."""
        self.assertIn("A3_chart_facts", DAG_ORDER)  # assertion 6

    def test_dag_order_contains_a10_msr(self):
        """A10_msr must be present (synthesis layer entry)."""
        self.assertIn("A10_msr", DAG_ORDER)  # assertion 7

    def test_a1_engine_precedes_a2_forensic(self):
        """A1_engine index must be less than A2_forensic_render."""
        self.assertLess(DAG_ORDER.index("A1_engine"), DAG_ORDER.index("A2_forensic_render"))  # assertion 8

    def test_chart_facts_precedes_msr(self):
        """A3_chart_facts must appear before A10_msr in topological order."""
        self.assertLess(DAG_ORDER.index("A3_chart_facts"), DAG_ORDER.index("A10_msr"))  # assertion 9


class TestCanonicalAyanamshas(unittest.TestCase):
    """Tests for CANONICAL_AYANAMSHAS correctness."""

    def test_canonical_ayanamshas_has_5_items(self):
        """CANONICAL_AYANAMSHAS must contain exactly 5 entries."""
        self.assertEqual(len(CANONICAL_AYANAMSHAS), 5)  # assertion 10

    def test_lahiri_present(self):
        self.assertIn("lahiri", CANONICAL_AYANAMSHAS)  # assertion 11

    def test_true_chitra_present(self):
        self.assertIn("true_chitra", CANONICAL_AYANAMSHAS)  # assertion 12

    def test_kp_present(self):
        self.assertIn("kp", CANONICAL_AYANAMSHAS)  # assertion 13

    def test_raman_present(self):
        self.assertIn("raman", CANONICAL_AYANAMSHAS)  # assertion 14

    def test_surya_siddhanta_present(self):
        self.assertIn("surya_siddhanta", CANONICAL_AYANAMSHAS)  # assertion 15

    def test_no_duplicates(self):
        """No duplicate ayanamsha names."""
        self.assertEqual(len(CANONICAL_AYANAMSHAS), len(set(CANONICAL_AYANAMSHAS)))  # assertion 16


class TestAssetLabels(unittest.TestCase):
    """Tests for ASSET_LABELS dict."""

    def test_asset_labels_has_14_entries(self):
        """ASSET_LABELS must have exactly 14 entries matching DAG_ORDER."""
        self.assertEqual(len(ASSET_LABELS), 14)  # assertion 17

    def test_all_dag_order_items_have_labels(self):
        """Every asset_id in DAG_ORDER must have a label."""
        for asset_id in DAG_ORDER:
            self.assertIn(asset_id, ASSET_LABELS)  # assertion 18

    def test_all_labels_are_non_empty_strings(self):
        """Every label value must be a non-empty string."""
        for asset_id, label in ASSET_LABELS.items():
            self.assertIsInstance(label, str)
            self.assertTrue(len(label) > 0)  # assertion 19


class TestParseArgs(unittest.TestCase):
    """Tests for parse_args()."""

    def test_parse_args_with_required_fields(self):
        """parse_args must accept --build-id and --chart-id."""
        ns = parse_args(["--build-id", "build-abc", "--chart-id", "chart-xyz"])
        self.assertEqual(ns.build_id, "build-abc")  # assertion 20
        self.assertEqual(ns.chart_id, "chart-xyz")  # assertion 21

    def test_parse_args_db_url_optional(self):
        """--db-url is optional; defaults to None."""
        ns = parse_args(["--build-id", "b1", "--chart-id", "c1"])
        self.assertIsNone(ns.db_url)  # assertion 22

    def test_parse_args_db_url_present(self):
        """--db-url, when supplied, is stored verbatim."""
        ns = parse_args(["--build-id", "b2", "--chart-id", "c2", "--db-url", "postgresql://localhost/test"])
        self.assertEqual(ns.db_url, "postgresql://localhost/test")  # assertion 23

    def test_parse_args_missing_build_id_raises(self):
        """parse_args must fail if --build-id is missing."""
        with self.assertRaises(SystemExit):  # assertion 24
            parse_args(["--chart-id", "c1"])

    def test_parse_args_missing_chart_id_raises(self):
        """parse_args must fail if --chart-id is missing."""
        with self.assertRaises(SystemExit):  # assertion 25
            parse_args(["--build-id", "b1"])


class TestDispatchAsset(unittest.TestCase):
    """Tests for dispatch_asset() stub behaviour."""

    def test_dispatch_asset_returns_int(self):
        """dispatch_asset must return an integer."""
        result = dispatch_asset("A1_engine", "build-001", "chart-001", ["lahiri"])
        self.assertIsInstance(result, int)  # assertion 26

    def test_dispatch_asset_returns_zero(self):
        """Stub must return 0 (no rows written)."""
        result = dispatch_asset("A1_engine", "build-001", "chart-001", ["lahiri"])
        self.assertEqual(result, 0)  # assertion 27

    def test_dispatch_asset_any_asset_id_returns_int(self):
        """dispatch_asset returns an int for every asset_id in DAG_ORDER.
        Unregistered assets (A1_engine) return 0; registered writers may return non-zero.
        """
        for asset_id in DAG_ORDER:
            result = dispatch_asset(
                asset_id, "build-001", "chart-001", CANONICAL_AYANAMSHAS
            )
            self.assertIsInstance(result, int, f"dispatch_asset({asset_id!r}) returned non-int")  # assertion 28

    def test_dispatch_asset_unregistered_returns_zero(self):
        """Unregistered asset_id (A1_engine has no WRITER_REGISTRY entry) returns 0."""
        result = dispatch_asset("A1_engine", "build-001", "chart-001", CANONICAL_AYANAMSHAS)
        self.assertEqual(result, 0)  # assertion 28b


class TestCheckCancellation(unittest.TestCase):
    """Tests for check_cancellation() with mocked DB cursor."""

    def _make_conn(self, status_value: str):
        """Build a minimal mock connection whose cursor returns status_value."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (status_value,)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn

    def test_cancelling_status_returns_true(self):
        """check_cancellation must return True when builds.status == 'cancelling'."""
        conn = self._make_conn("cancelling")
        result = check_cancellation(conn, "build-001")
        self.assertTrue(result)  # assertion 29

    def test_running_status_returns_false(self):
        """check_cancellation must return False when builds.status == 'running'."""
        conn = self._make_conn("running")
        result = check_cancellation(conn, "build-001")
        self.assertFalse(result)  # assertion 30

    def test_queued_status_returns_false(self):
        """check_cancellation must return False for any non-cancelling status."""
        conn = self._make_conn("queued")
        result = check_cancellation(conn, "build-001")
        self.assertFalse(result)  # assertion 31

    def test_complete_status_returns_false(self):
        """check_cancellation returns False for 'complete'."""
        conn = self._make_conn("complete")
        result = check_cancellation(conn, "build-001")
        self.assertFalse(result)  # assertion 32

    def test_missing_build_returns_false(self):
        """check_cancellation returns False gracefully when build_id not found."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        result = check_cancellation(mock_conn, "nonexistent-build")
        self.assertFalse(result)  # assertion 33


if __name__ == "__main__":
    unittest.main()
