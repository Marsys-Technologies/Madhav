"""
test_ga_medical_nakshatra_spelling.py -- TI-prose-batch2-writers: a Moon in nakshatra 23 got no body part.

The L1 facts spell nakshatra 23 "Dhanishta" (`pyjhora_adapter._names.NAKSHATRA_NAMES`, the spelling
chart_facts carries) while the L0 seed table the writer looks up (`bg_nakshatra_medical`, seeded from
`brahmagyan.l0_medical.NAKSHATRA_MEDICAL`) spells it "Dhanishtha", so the exact-match lookup returned
no row and `ga_medical.nakshatra_body_part` stayed NULL for a Moon there. The lookup now folds the
name to the seed's spelling.

The fake connection below answers the writer's own SQL from the REAL seed list, by exact name match
(as the table's `WHERE nakshatra_name = %s` does), so a spelling the seed does not carry returns no row.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from brahmagyan.l0_medical import NAKSHATRA_MEDICAL  # noqa: E402
from ga_writers import ga_medical_writer as med  # noqa: E402
from pyjhora_adapter._names import NAKSHATRA_NAMES  # noqa: E402

SEED_BY_NAME = {r["nakshatra_name"]: r["body_part"] for r in NAKSHATRA_MEDICAL}
SEED_BY_NUMBER = {r["nakshatra_number"]: r for r in NAKSHATRA_MEDICAL}


class _Cur:
    def __init__(self):
        self._row = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        assert "bg_nakshatra_medical" in sql
        name = params[0]
        self._row = (SEED_BY_NAME[name],) if name in SEED_BY_NAME else None

    def fetchone(self):
        return self._row


class _Conn:
    def cursor(self, **kw):
        return _Cur()


@pytest.mark.parametrize("number", range(1, 28))
def test_every_one_of_the_27_nakshatras_maps_to_a_body_part(number):
    """All 27 names as the L1 adapter spells them reach the seed row of the same nakshatra number."""
    name = NAKSHATRA_NAMES[number]
    got = med._load_nakshatra_body_part(_Conn(), name)
    assert got is not None, f"nakshatra {number} ({name!r}) found no body part"
    assert got == SEED_BY_NUMBER[number]["body_part"]


def test_nakshatra_23_is_the_spelling_that_failed_before():
    assert NAKSHATRA_NAMES[23] == "Dhanishta"
    assert SEED_BY_NUMBER[23]["nakshatra_name"] == "Dhanishtha"
    assert med._load_nakshatra_body_part(_Conn(), "Dhanishta") == "back/knees"
    # the seed's own spelling still resolves
    assert med._load_nakshatra_body_part(_Conn(), "Dhanishtha") == "back/knees"


@pytest.mark.parametrize("variant,number", [("Moola", 19), ("Mrigasira", 5), ("moola", 19), (" Purva  Bhadrapada ", 25)])
def test_the_other_spelling_families_reach_the_same_row(variant, number):
    assert med._load_nakshatra_body_part(_Conn(), variant) == SEED_BY_NUMBER[number]["body_part"]


def test_an_unknown_name_is_still_no_row_not_a_guess():
    assert med._load_nakshatra_body_part(_Conn(), "Nonexistent") is None
    assert med._load_nakshatra_body_part(_Conn(), "") is None


def test_the_stored_natal_nakshatra_keeps_the_l1_spelling(monkeypatch):
    """The fix is at the lookup: the row's `natal_nakshatra` is still the L1 fact's own value
    ('Dhanishta'), only `nakshatra_body_part` changes (NULL -> 'back/knees')."""
    inserted = []

    class _WriteCur(_Cur):
        rowcount = 0

        def execute(self, sql, params=()):
            if "bg_nakshatra_medical" in sql:
                return super().execute(sql, params)
            if sql.lstrip().upper().startswith("INSERT"):
                inserted.append(params)

    class _WriteConn:
        def cursor(self, **kw):
            return _WriteCur()

    monkeypatch.setattr(med, "_load_condition_scores", lambda *a: {g: 0.5 for g in med.ALL_GRAHAS})
    monkeypatch.setattr(med, "_load_medical_mappings", lambda *a: {})
    monkeypatch.setattr(
        med, "_load_graha_positions",
        lambda *a: {"Moon": {"sign": "Capricorn", "nakshatra": "Dhanishta"}},
    )
    n = med.build_ga_medical_substep("c", "b", "lahiri_chitrapaksha", _WriteConn())
    assert n == 9
    moon = next(p for p in inserted if p[2] == "Moon")
    assert moon[4] == "Dhanishta"          # natal_nakshatra, as the L1 fact spells it
    assert moon[9] == "back/knees"         # nakshatra_body_part, found through the folded lookup
