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
    # SS rulings 2026-10-02: BOTH chart-specific conjuncts (Saturn, Sun) are REMOVED; an integrity
    # clause must be true for any chart (no chart id, ayanamsha or graha literal in the SQL body)
    body = "\n".join(l for l in sql.splitlines() if not l.lstrip().startswith("--"))
    assert "graha = 'Saturn'" not in body and "graha = 'Sun'" not in body
    assert "indication_strength <> 'mild'" not in body and "indication_strength <> 'strong'" not in body
    assert "482012f1" not in body and "lahiri_chitrapaksha" not in body


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


def test_every_clause_text_is_marked_intent_only_for_migration_1252_with_the_ordering_rule():
    for f in sorted(_CLAUSE_DIR.glob("*.sql")):
        head = f.read_text(encoding="utf-8")[:900]
        assert head.startswith("-- INTENT ONLY, NOT APPLIED: migration 1252 (to be written at the owner's line)"), f.name
        assert "BEFORE" in head and "WITH OR AFTER the writer deploy" in head, f.name


def test_scoped_variant_says_why_it_is_canonical_scoped_and_that_it_widens_in_s_l1b():
    sql = _clause("ga_condition_integrity_scoped_canonical_NOT_APPLIED.sql")
    assert "90 stale D1-fallback rows" in sql
    assert "WIDENS to all charts" in sql and "REQUIRED step of S-L1b" in sql
    assert "ga_dashas" in sql
