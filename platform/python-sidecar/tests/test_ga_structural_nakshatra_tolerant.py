"""
test_ga_structural_nakshatra_tolerant.py -- a Moon in nakshatra 5, 19 or 23 no longer misses in ga_structural.

`_build_nakshatra_relationship_rows` looked the Moon's (and every graha's) nakshatra up with
`NAKSHATRA_NAMES_27.index(name)` against the writer's own 27-name table. L1
(`pyjhora_adapter._names`) writes "Mrigashira" / "Mula" / "Dhanishta" and the L0 lexicon spells them
"Mrigasira" / "Moola" / "Dhanishtha", while the writer's table spells "Mrigashira" / "Mula" /
"Dhanishtha": so a Moon in nakshatra 23 (L1 "Dhanishta") silently produced no tara_bala rows.
The lookups now go through the tolerant reader `brahmagyan.nakshatra_vocabulary.nakshatra_number`.

These tests run the writer's real function against a fake connection (no DB), and pin that for every
input that resolved before the stored output is byte-identical (the emitted `nakshatra` text is the
input text; the lord fallback is the table's own value).
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from brahmagyan.nakshatra_vocabulary import (  # noqa: E402
    CANONICAL_NAKSHATRA_NAMES,
    canonical_nakshatra,
    nakshatra_number,
)
from ga_writers import ga_structural_writer as gs  # noqa: E402
from pyjhora_adapter._names import NAKSHATRA_NAMES as L1_NAMES  # noqa: E402

MOON = gs.PLANET_TO_SUBJECT["Moon"]
MARS = gs.PLANET_TO_SUBJECT["Mars"]
TABLE = gs.NAKSHATRA_NAMES_27


class _Cur:
    def __init__(self, nak_rows):
        self._nak_rows = nak_rows
        self._last = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        # graha_position/nakshatra rows are served; the graha_nakshatra_join lord query returns
        # nothing, so the writer takes its NAKSHATRA_LORDS fallback.
        self._last = list(self._nak_rows) if "graha_position" in sql else []

    def fetchall(self):
        return self._last


class _Conn:
    def __init__(self, nak_rows):
        self._nak_rows = nak_rows

    def cursor(self, **kw):
        return _Cur(self._nak_rows)


def _run(moon_nak: str, mars_nak: str):
    conn = _Conn([(MOON, moon_nak, "fid-moon"), (MARS, mars_nak, "fid-mars")])
    return gs._build_nakshatra_relationship_rows(conn, "test-chart", "test-build", "lahiri", "2026-01-01T00:00:00Z", "t")


def _by(rows, category, subject):
    return [r for r in rows if r["fact_category"] == category and r["fact_subject"] == subject]


# Moon nakshatra 5 / 19 / 23 under L1's current spelling, the canonical lexicon spelling, and the table's.
CASES = [
    (5, "Mrigashira"), (5, "Mrigasira"),
    (19, "Mula"), (19, "Moola"),
    (23, "Dhanishta"), (23, "Dhanishtha"),
]


@pytest.mark.parametrize("number,spelling", CASES)
def test_moon_in_5_19_23_resolves_any_spelling(number, spelling):
    mars = TABLE[(number - 1 + 3) % 27]  # Mars three nakshatras on -> tara_count 4 ("kshema")
    rows = _run(spelling, mars)
    tara = _by(rows, "tara_bala", MARS)
    assert len(tara) == 1, f"Moon in {spelling!r} produced no tara_bala row"
    assert tara[0]["fact_value_num"] == 4.0 and tara[0]["fact_value_text"] == "kshema"
    # Moon against itself: janma (1)
    moon_tara = _by(rows, "tara_bala", MOON)
    assert len(moon_tara) == 1 and moon_tara[0]["fact_value_num"] == 1.0
    # the stored nakshatra text is the L1 fact's own text, untouched
    assert moon_tara[0]["fact_value_jsonb"]["moon_nakshatra"] == spelling
    lord = _by(rows, "nakshatra_lord_relationship", MOON)[0]
    assert lord["fact_value_text"] == gs._graha_to_title(gs.NAKSHATRA_LORDS[TABLE[number - 1]])
    assert lord["fact_value_jsonb"]["nakshatra"] == spelling


def test_graha_in_5_19_23_resolves_when_moon_elsewhere():
    for number, spelling in CASES:
        rows = _run("Ashwini", spelling)
        tara = _by(rows, "tara_bala", MARS)
        assert len(tara) == 1
        assert tara[0]["fact_value_num"] == float(number)  # Moon in Ashwini (no. 1) -> count == number
        lord = _by(rows, "nakshatra_lord_relationship", MARS)[0]
        assert lord["fact_value_text"] == gs._graha_to_title(gs.NAKSHATRA_LORDS[TABLE[number - 1]])


def test_every_previously_resolving_input_is_unchanged():
    """Old behaviour: idx = TABLE.index(name) for the 27 table names. New output must equal it."""
    for i, name in enumerate(TABLE):
        assert nakshatra_number(name) == i + 1  # same index the .index() lookup gave
        mars = TABLE[(i + 5) % 27]
        rows = _run(name, mars)
        tara = _by(rows, "tara_bala", MARS)
        assert len(tara) == 1
        assert tara[0]["fact_value_num"] == float(5 % 27 + 1)  # old formula: (mars_idx - moon_idx) % 27 + 1
        for subj, nak in ((MOON, name), (MARS, mars)):
            lord = _by(rows, "nakshatra_lord_relationship", subj)[0]
            assert lord["fact_value_jsonb"]["nakshatra"] == nak  # stored spelling == input spelling
            assert lord["fact_value_text"] == gs._graha_to_title(gs.NAKSHATRA_LORDS[nak])  # old fallback


def test_all_27_resolve_under_l1_and_canonical_spellings():
    l1 = [n for n in L1_NAMES if n]  # _names.NAKSHATRA_NAMES is 1-based (index 0 is blank)
    assert len(l1) == len(TABLE) == len(CANONICAL_NAKSHATRA_NAMES) == 27
    for i in range(27):
        for spelling in (TABLE[i], l1[i], CANONICAL_NAKSHATRA_NAMES[i]):
            assert nakshatra_number(spelling) == i + 1, spelling
            rows = _run(spelling, TABLE[i])
            tara = _by(rows, "tara_bala", MARS)
            assert len(tara) == 1 and tara[0]["fact_value_num"] == 1.0, spelling
            lord = _by(rows, "nakshatra_lord_relationship", MOON)[0]
            assert lord["fact_value_text"] == gs._graha_to_title(gs.NAKSHATRA_LORDS[TABLE[i]]), spelling


def test_unknown_name_is_an_honest_miss():
    for bad in ("Abhijit", "NotANakshatra", "", "  "):
        assert canonical_nakshatra(bad) is None and nakshatra_number(bad) is None
        rows = _run(bad, "Ashwini")
        assert _by(rows, "tara_bala", MARS) == [] and _by(rows, "tara_bala", MOON) == []
        if bad:  # an empty name is dropped before the lookup (no row at all)
            assert _by(rows, "nakshatra_lord_relationship", MOON)[0]["fact_value_text"] == ""
    assert nakshatra_number(None) is None and canonical_nakshatra(5) is None


def test_reader_folds_case_and_whitespace_only():
    assert canonical_nakshatra("  dhanishta ") == "Dhanishtha"
    assert canonical_nakshatra("PURVA_BHADRAPADA") == "Purva Bhadrapada"
    assert nakshatra_number("Purva Bhadrapada") == 25  # the native's Moon is unaffected
