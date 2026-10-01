"""
test_ga_condition_band_clause_texts.py -- I-28: the registry `integrity_check_sql` clause TEXTS that a
LATER migration will apply (BAND_X2_LANE_INTENT_v1_0.md section 9; NOT applied here) must carry the
same cut points and the same NULL label as the one band table. SQL cannot import the Python table, so
the texts are pinned to it here; this test cannot see the live registry rows.

DB-free: reads the clause files committed beside the intent document.
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_condition_bands as bands  # noqa: E402

_CLAUSE_DIR = (
    pathlib.Path(__file__).resolve().parents[3]
    / "00_ARCHITECTURE/briefs/suvarna/exec/band_x2/registry_clause_texts"
)
_CUT_RE = re.compile(r"condition_score\s*(<=|<)\s*([0-9.]+)\s+THEN\s+'(\w+)'")


def _clause(name: str) -> str:
    return (_CLAUSE_DIR / name).read_text(encoding="utf-8")


def test_medical_clause_text_uses_the_band_tables_cut_points_and_labels():
    sql = _clause("ga_medical_integrity_NOT_APPLIED.sql")
    assert _CUT_RE.findall(sql) == [("<", "0.4", "strong"), ("<", "0.7", "moderate")]
    assert "WHEN c.condition_score IS NULL THEN 'unknown'" in sql
    assert "ELSE 'mild'" in sql
    # the Saturn FORENSIC conjunct is stated against the LOW band, not against 'mild'
    assert "indication_strength IN ('strong', 'unknown')" in sql
    assert "indication_strength <> 'mild'" not in sql


def test_vastu_clause_text_uses_the_band_tables_cut_points_and_never_neutral_for_null():
    sql = _clause("ga_vastu_integrity_NOT_APPLIED.sql")
    assert _CUT_RE.findall(sql) == [("<", "0.4", "weakened"), ("<", "0.7", "neutral")]
    assert "WHEN c.condition_score IS NULL THEN 'unknown'" in sql
    assert "WHEN c.condition_score IS NULL THEN 'neutral'" not in sql
    assert "ELSE 'strengthened'" in sql


def test_clause_cut_points_equal_the_python_table():
    for name in ("ga_medical_integrity_NOT_APPLIED.sql", "ga_vastu_integrity_NOT_APPLIED.sql"):
        nums = [float(x) for _, x, _ in _CUT_RE.findall(_clause(name))]
        assert nums == [bands.CUT_LOW_MID, bands.CUT_MID_HIGH], (name, nums)


def test_ga_condition_clause_texts_carry_the_x2_conjuncts_and_differ_only_in_scope():
    scoped = _clause("ga_condition_integrity_scoped_canonical_NOT_APPLIED.sql")
    wide = _clause("ga_condition_integrity_table_wide_NOT_APPLIED.sql")
    for sql in (scoped, wide):
        assert "(e) X2 / I-29" in sql and "(f) the detector must be able to SEE chart_divisionals" in sql
        assert "row_security_active('public.chart_divisionals')" in sql
    canon_line = "WHERE gc.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'\n      AND COALESCE("
    assert canon_line in scoped and canon_line not in wide
