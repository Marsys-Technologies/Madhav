"""
test_ga_condition_band_table.py -- I-28 / Q-L1-16(c) (SS ruling N-62): ONE band table over
`condition_score`, owned by ga_condition, read by ga_medical and ga_vastu.

Covers:
  * golden boundary tests of the table (0.4 and 0.7 exact, just below / above, NULL, Decimal);
  * the table is ONE object shared by ga_condition / ga_medical / ga_vastu (identity, not equality);
  * neither consumer carries its own cut points (AST scan: no 0.4 / 0.6 / 0.7 numeric literal in
    executable code of ga_medical_writer.py / ga_vastu_writer.py);
  * both label vocabularies cover exactly the table's bands; the two consumers always agree on
    which band a score is in (the 0.6-0.7 disagreement this ruling removed);
  * NULL score -> NULL band / 'unknown', never 'neutral', in both consumers;
  * (Saturn: no build-time guard exists any more; see test_ga_medical_saturn_golden.py.)

DB-free: pure functions only.
"""
from __future__ import annotations

import ast
import pathlib
import sys
from decimal import Decimal

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_condition_bands as bands  # noqa: E402
from ga_writers import ga_condition_writer as cond  # noqa: E402
from ga_writers import ga_medical_writer as med  # noqa: E402
from ga_writers import ga_vastu_writer as vas  # noqa: E402

_GA_WRITERS = pathlib.Path(__file__).resolve().parents[1] / "ga_writers"


# ── golden boundary tests of the table ────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (0.0,        "low"),
    (0.3,        "low"),
    (0.39,       "low"),
    (0.3999999,  "low"),    # just below the low/mid edge
    (0.4,        "mid"),    # AT the edge: lower bound inclusive
    (0.4000001,  "mid"),    # just above
    (0.5,        "mid"),
    (0.6,        "mid"),    # a friend-sign planet scoring 0.6 stays in the middle band
    (0.65,       "mid"),
    (0.6999999,  "mid"),    # just below the mid/high edge
    (0.7,        "high"),   # AT the edge: lower bound inclusive
    (0.7000001,  "high"),   # just above
    (1.0,        "high"),
    (-0.2,       "low"),    # out-of-range is still bucketed, never invented away
    (1.5,        "high"),
    (None,       None),     # NULL score -> NULL band
    (float("nan"), None),   # not a number -> NULL band
    ("not-a-number", None),
])
def test_score_band_goldens(score, expected):
    assert bands.score_band(score) == expected


@pytest.mark.parametrize("score,expected", [
    (Decimal("0.4"),      "mid"),    # psycopg returns numeric as Decimal; Decimal('0.4') < 0.4 is True
    (Decimal("0.400000"), "mid"),    #   in Python, so the table converts with float() first
    (Decimal("0.399999"), "low"),
    (Decimal("0.7"),      "high"),
    (Decimal("0.700000"), "high"),
    (Decimal("0.699999"), "mid"),
    ("0.4",               "mid"),
    ("0.7",               "high"),
])
def test_decimal_and_numeric_string_scores_do_not_misbucket_at_the_edges(score, expected):
    assert bands.score_band(score) == expected


def test_the_two_cut_points_are_the_ruled_ones():
    assert bands.CUT_LOW_MID == 0.4
    assert bands.CUT_MID_HIGH == 0.7
    assert [b.name for b in bands.SCORE_BANDS] == ["low", "mid", "high"]


def test_table_is_contiguous_ordered_and_open_at_both_ends():
    bs = bands.SCORE_BANDS
    assert bs[0].lower is None and bs[-1].upper is None
    for left, right in zip(bs, bs[1:]):
        assert left.upper == right.lower
    # every score on a fine grid lands in exactly ONE band
    for i in range(-50, 151):
        s = i / 100.0
        assert sum(1 for b in bs if b.contains(s)) == 1, s


# ── ONE table: identity across the three writers ──────────────────────────────

def test_medical_and_vastu_use_the_same_table_object_as_ga_condition():
    assert cond.SCORE_BANDS is bands.SCORE_BANDS
    assert med.SCORE_BANDS is bands.SCORE_BANDS
    assert vas.SCORE_BANDS is bands.SCORE_BANDS
    assert med.SCORE_BANDS is vas.SCORE_BANDS
    assert cond.score_band is bands.score_band
    assert med.score_band is bands.score_band
    assert vas.score_band is bands.score_band
    assert cond.CUT_LOW_MID is bands.CUT_LOW_MID and cond.CUT_MID_HIGH is bands.CUT_MID_HIGH


def _numeric_literals_in_code(path: pathlib.Path) -> set[float]:
    """Float/int constants that appear in EXECUTABLE code (docstrings and comments excluded)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    doc_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
                doc_nodes.add(id(body[0].value))
    out: set[float] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and id(node) not in doc_nodes:
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                out.add(float(node.value))
    return out


@pytest.mark.parametrize("writer", ["ga_medical_writer.py", "ga_vastu_writer.py"])
def test_consumers_carry_no_private_cut_points(writer):
    """The pre-I-28 defect: each consumer hard-coded its own 0.4 / 0.6 / 0.7. A cut point may not
    reappear in either file's executable code (they read the one table)."""
    lits = _numeric_literals_in_code(_GA_WRITERS / writer)
    assert not (lits & {0.4, 0.6, 0.7}), (writer, sorted(lits & {0.4, 0.6, 0.7}))


# ── label vocabularies: cover the table exactly; consumers agree on the band ──

def test_each_consumer_labels_exactly_the_tables_bands():
    assert set(med.INDICATION_STRENGTH_BY_BAND) == set(bands.BAND_NAMES)
    assert set(vas.DIRECTION_IMPACT_BY_BAND) == set(bands.BAND_NAMES)


def test_stored_label_values_are_unchanged():
    """I-28 does not rename stored values."""
    assert med.INDICATION_STRENGTH_BY_BAND == {"low": "strong", "mid": "moderate", "high": "mild"}
    assert vas.DIRECTION_IMPACT_BY_BAND == {"low": "weakened", "mid": "neutral", "high": "strengthened"}


def test_medical_and_vastu_always_agree_on_the_band_of_a_score():
    inv_med = {v: k for k, v in med.INDICATION_STRENGTH_BY_BAND.items()}
    inv_vas = {v: k for k, v in vas.DIRECTION_IMPACT_BY_BAND.items()}
    for i in range(0, 1001):
        s = i / 1000.0
        assert inv_med[med.indication_strength_from_score(s)] == inv_vas[vas.compute_direction_impact(s)] == bands.score_band(s), s


def test_the_old_disagreement_band_0_6_to_0_7_is_one_band_now():
    """Canonical chart: 15 rows sat between 0.6 and 0.7 -- medical said 'mild', vastu said 'neutral'."""
    for s in (0.6000001, 0.61, 0.65, 0.68, 0.6972, 0.6999999):
        assert med.indication_strength_from_score(s) == "moderate"
        assert vas.compute_direction_impact(s) == "neutral"


# ── NULL score: NULL band / 'unknown', never 'neutral' ────────────────────────

def test_null_score_is_null_band_and_unknown_never_neutral():
    assert bands.score_band(None) is None
    assert med.indication_strength_from_score(None) == "unknown"
    assert vas.compute_direction_impact(None) == "unknown"
    assert vas.compute_direction_impact(None) != "neutral"
    assert vas.compute_direction_impact(float("nan")) == "unknown"
    # 'neutral' is the vastu MID label, so it can only come out of a real mid-band score
    assert vas.compute_direction_impact(0.5) == "neutral"


def test_unknown_label_is_the_one_constant_both_consumers_share():
    assert med.INDICATION_STRENGTH_UNKNOWN == vas.DIRECTION_IMPACT_UNKNOWN == bands.BAND_UNKNOWN == "unknown"


def test_vastu_decimal_score_at_the_low_edge_is_mid_not_low():
    """ga_vastu_writer reads condition_score straight from psycopg (Decimal); the pre-I-28 code
    compared it to a float, which would bucket a stored 0.4 as 'weakened'."""
    assert vas.compute_direction_impact(Decimal("0.400000")) == "neutral"
    assert vas.compute_direction_impact(Decimal("0.700000")) == "strengthened"
