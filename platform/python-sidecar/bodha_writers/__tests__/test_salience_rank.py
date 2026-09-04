"""Unit tests for bodha_writers/salience_rank.py.

NIRMĀṆA L2-W3 (N-16). Regression cover for the W1 finding that the six rarest
signal classes shipped a NULL salience_pctl_in_class — the exact column the
D-SALIENCE rare-class-leader predicate ranks on — because only bo_laksana ran the
percentile pass and each of those classes is written by its own satellite writer.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from bodha_writers.salience_rank import set_salience_pctl_in_class


def _rows(*specs: tuple[str, float]) -> list[dict]:
    return [{"signal_type_class": c, "computed_salience": s} for c, s in specs]


class TestPercentRankSemantics(unittest.TestCase):
    """Must match PERCENT_RANK() exactly — this replaced a SQL window function."""

    def test_matches_percent_rank_with_ties_sharing_minimum(self):
        rows = _rows(("a", 1.0), ("a", 2.0), ("a", 2.0), ("a", 4.0))
        set_salience_pctl_in_class(rows)
        # PERCENT_RANK = (rank - 1) / (n - 1); ties take the minimum rank.
        self.assertEqual([r["salience_pctl_in_class"] for r in rows],
                         [0.0, 0.333333, 0.333333, 1.0])

    def test_single_row_partition_is_zero(self):
        """PERCENT_RANK over a one-row partition is 0.0, not 1.0 and not NULL."""
        rows = _rows(("solo", 9.9))
        set_salience_pctl_in_class(rows)
        self.assertEqual(rows[0]["salience_pctl_in_class"], 0.0)

    def test_all_equal_salience_all_zero(self):
        rows = _rows(("a", 5.0), ("a", 5.0), ("a", 5.0))
        set_salience_pctl_in_class(rows)
        self.assertEqual([r["salience_pctl_in_class"] for r in rows], [0.0, 0.0, 0.0])


class TestClassPartitioning(unittest.TestCase):
    def test_classes_are_ranked_independently(self):
        """A rare class must be ranked within ITSELF, not against the whole chart.

        This is the property the tail lane depends on: a 4-row class has a top
        member at pctl 1.0 even though its salience is far below the chart's.
        """
        rows = _rows(
            ("composite_state", 100.0), ("composite_state", 200.0),
            ("vargottama_amplification", 0.1), ("vargottama_amplification", 0.2),
        )
        set_salience_pctl_in_class(rows)
        by_class = {}
        for row in rows:
            by_class.setdefault(row["signal_type_class"], []).append(
                row["salience_pctl_in_class"])
        self.assertEqual(by_class["composite_state"], [0.0, 1.0])
        self.assertEqual(by_class["vargottama_amplification"], [0.0, 1.0])
        # the rare class's leader outranks nothing chart-wide, and that is the point
        self.assertEqual(by_class["vargottama_amplification"][1], 1.0)

    def test_the_six_rare_classes_all_get_a_percentile(self):
        """The concrete W1 defect: these six shipped NULL on 149 production rows."""
        rare = ("sudarshana_agreement", "nakshatra_semantic", "arudha",
                "special_lagna", "dhana_axis", "vargottama_amplification")
        rows = [{"signal_type_class": c, "computed_salience": float(i)}
                for c in rare for i in (1, 2, 3)]
        set_salience_pctl_in_class(rows)
        self.assertTrue(all(r["salience_pctl_in_class"] is not None for r in rows))
        self.assertEqual(len({r["signal_type_class"] for r in rows}), 6)


class TestHonestGaps(unittest.TestCase):
    def test_rows_without_salience_are_left_unset_not_zeroed(self):
        """A row with no computed_salience must not be given 0.0.

        0.0 is a real percentile — the bottom of its class. Assigning it to a row
        nothing measured would place that row at the bottom as though measured,
        which is the §N.7-item-6 defect this wave exists to remove.
        """
        rows = _rows(("a", 1.0), ("a", 3.0))
        rows.append({"signal_type_class": "a", "computed_salience": None})
        set_salience_pctl_in_class(rows)
        self.assertEqual(rows[0]["salience_pctl_in_class"], 0.0)
        self.assertEqual(rows[1]["salience_pctl_in_class"], 1.0)
        self.assertNotIn("salience_pctl_in_class", rows[2])

    def test_empty_input_is_a_no_op(self):
        rows: list[dict] = []
        set_salience_pctl_in_class(rows)
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
