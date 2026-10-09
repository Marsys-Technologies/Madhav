"""
tests/test_ga_graha_title_names.py -- graha-valued fact_value_text is the canonical Title-case name.

SS N-305: chart_facts.fact_value_text held lowercase graha ids ('jupiter', 'ketu', ...) in
ga_nakshatra's graha_nakshatra_join (key nakshatra_lord) and graha_pada_join (key pada_lord) and in
ga_structural's nakshatra_lord_relationship (key nakshatra_lord), while every other graha-valued column
uses the Title name ('Jupiter'). The L0 reference tables store the ids in lowercase, so the emitters now
pass those two keys through the graha SSoT (brahmagyan.graha_vocabulary.to_title).
Consumer audit (no reader depends on the lowercase ids): migrations 789-792 compare with lower();
ga_structural's dispositor chain re-capitalises; bo_laksana classifies by category only; the TS tools and
the dossier slices carry category:key names, never these values.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from ga_writers import ga_nakshatra_emitters as em

TITLE = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
LOWER_IDS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def _chart_output():
    grahas = [{"name": b, "nakshatra_id": 1 + i, "pada": 1 + (i % 4)} for i, b in enumerate(BODIES)]
    return {"grahas": grahas, "ascendant": {"nakshatra_id": 10, "pada": 2}}


def _nak_rows():
    # reference_nakshatra stores vimshottari_lord as a lowercase id
    return {n: {"vimshottari_lord": LOWER_IDS[(n - 1) % 9], "gana": "deva", "nadi": "adi"} for n in range(1, 28)}


def _pada_rows():
    # reference_nakshatra_pada stores pada_lord as a lowercase id
    return {(n, p): {"pada_lord": LOWER_IDS[(n + p) % 9], "pada_akshara": "Chu", "pada_navamsa_sign": "Aries"}
            for n in range(1, 28) for p in range(1, 5)}


def _emit():
    return em.emit_nakshatra_join("c", "lahiri_chitrapaksha", "b", _chart_output(), _nak_rows(), _pada_rows())


def test_nakshatra_lord_of_graha_nakshatra_join_is_a_canonical_title_name():
    vals = [r["fact_value_text"] for r in _emit()
            if r["fact_category"] == "graha_nakshatra_join" and r["fact_key"] == "nakshatra_lord"]
    assert len(vals) == 10 and set(vals) <= TITLE            # 9 grahas + Lagna


def test_pada_lord_of_graha_pada_join_is_a_canonical_title_name():
    vals = [r["fact_value_text"] for r in _emit()
            if r["fact_category"] == "graha_pada_join" and r["fact_key"] == "pada_lord"]
    assert len(vals) == 10 and set(vals) <= TITLE


def test_every_node_form_maps_to_the_released_name():
    for raw, want in (("rahu", "Rahu"), ("ketu", "Ketu"), ("rahu_mean", "Rahu"), ("ketu_mean", "Ketu"),
                      ("Jupiter", "Jupiter"), ("jupiter", "Jupiter")):
        assert em._graha_valued_text("nakshatra_lord", raw) == want


def test_other_attribute_values_are_untouched():
    rows = _emit()
    gana = {r["fact_value_text"] for r in rows if r["fact_key"] == "gana"}
    assert gana == {"deva"}                                  # not title-cased: only graha-valued keys are normalised
    akshara = {r["fact_value_text"] for r in rows if r["fact_key"] == "akshara"}
    assert akshara == {"Chu"}
    assert em._graha_valued_text("gana", "deva") == "deva"


def test_row_count_and_keys_unchanged():
    keys = sorted({(r["fact_category"], r["fact_key"]) for r in _emit()})
    assert ("graha_nakshatra_join", "nakshatra_lord") in keys and ("graha_pada_join", "pada_lord") in keys


# ga_structural imports psycopg at module level, so its behavioural test needs it; the source pin does not.
_STRUCT = Path(__file__).resolve().parents[1] / "ga_writers" / "ga_structural_writer.py"


def test_structural_relationship_value_goes_through_the_graha_ssot_source_pin():
    src = _STRUCT.read_text(encoding="utf-8")
    m = re.search(r'nak_lord = (\w+)\(graha_lord_name\.get\(graha_subj, NAKSHATRA_LORDS\.get\(nak, ""\)\)\)', src)
    assert m, "nakshatra_lord_relationship must normalise the lord through the graha SSoT"
    assert m.group(1) == "_graha_to_title"
    assert "canonical_graha_title as _graha_to_title" in src
    ast.parse(src)


def test_structural_relationship_rows_are_title_case_with_a_lowercase_l1_value():
    pytest.importorskip("psycopg")
    from ga_writers import ga_structural_writer as gs

    nak_raw = [("MOON", "Purva Bhadrapada", "f-moon"), ("RAH_MEAN", "Ardra", "f-rahu")]
    lord_raw = [("MOON", "jupiter", "j-moon"), ("RAH_MEAN", "rahu", "j-rahu")]

    class Cur:
        def __init__(self):
            self.calls = 0
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def execute(self, sql, params=None):
            self.calls += 1
            self.which = nak_raw if self.calls == 1 else lord_raw
        def fetchall(self):
            return self.which
    class Conn:
        def __init__(self):
            self.cur = Cur()
        def cursor(self, **kw):
            return self.cur

    rows = gs._build_nakshatra_relationship_rows(Conn(), "c", "b", "lahiri_chitrapaksha", "2026-01-01T00:00:00+00:00", "e")
    rel = {r["fact_subject"]: r for r in rows if r["fact_category"] == "nakshatra_lord_relationship"}
    assert rel["MOON"]["fact_value_text"] == "Jupiter"
    assert rel["RAH_MEAN"]["fact_value_text"] == "Rahu"
    assert rel["MOON"]["fact_value_jsonb"]["lord"] == "Jupiter"


def test_shared_helper_is_fail_closed_and_handles_legacy_mean_forms():
    from ga_writers._graha_text import canonical_graha_title as c
    assert [c(v) for v in ("rahu_mean", "KET_MEAN", "ketu_mean", "jupiter", "Jupiter", "RAH_MEAN")] == \
        ["Rahu", "Ketu", "Ketu", "Jupiter", "Jupiter", "Rahu"]
    # an unrecognised token is NOT title-cased into a plausible name: it comes back unchanged
    assert c("not_a_graha") == "not_a_graha" and c("xyz") == "xyz"
    assert em._graha_valued_text("pada_lord", "qux") == "qux"


def test_structural_and_emitter_share_one_helper():
    src = _STRUCT.read_text(encoding="utf-8")
    emit = Path(em.__file__).read_text(encoding="utf-8")
    assert "_graha_text import canonical_graha_title" in src and "_graha_text import canonical_graha_title" in emit
