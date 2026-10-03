"""Production defect (steward M20261001T213651-aeb0; real rebuild run 9863849f): the L0 table
`reference_signs` stores lord names in LOWERCASE ('mars', brahmagyan/l0_reference.py:269 SIGNS)
but the resonance writer looked them up in a Title-case map ('Mars') — every lord row was
stamped 'unavailable' (51) and every M-6 lord-derived row too (10), although LAGNA, the 12
rulership rows and every graha position existed.

These tests run the REAL writer functions (`_fetch_chart_resolution_context`,
`_stamp_target_resolution`, `_build_m6_derived_rows`) over a recording connection that answers
with the REAL seed's values — lords taken from the L0 seed itself, never hand-typed.
"""
from __future__ import annotations

import pytest

from brahmagyan.l0_reference import SIGNS as L0_SIGNS
from services.ka_gochara_resonance import writer as w

# read-only production facts (steward): graha_position subjects on the canonical chart
SUBJECTS = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN", "LAGNA")
LAGNA_SIGN_NUM = 1            # the canonical chart's lagna is Aries


def test_the_real_l0_seed_is_lowercase_the_premise_of_the_defect():
    lords = {s[3] for s in L0_SIGNS}
    assert lords == {"jupiter", "mars", "mercury", "moon", "saturn", "sun", "venus"}
    assert all(l == l.lower() for l in lords)


class _Cur:
    def __init__(self, conn):
        self.conn, self._rows = conn, []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._rows = self.conn.answer(sql)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class _Conn:
    """Answers each fetch SQL the writer issues from the real seed + the canonical chart."""

    def __init__(self, lords=None, lagna=LAGNA_SIGN_NUM, present=SUBJECTS):
        self.lords = lords if lords is not None else [(s[0], s[3]) for s in L0_SIGNS]
        self.lagna, self.present = lagna, present

    def cursor(self, row_factory=None):
        return _Cur(self)

    def answer(self, sql):
        if sql is w._FETCH_LAGNA_SIGN_SQL:
            return [{"fact_value_num": self.lagna}] if self.lagna is not None else []
        if sql is w._FETCH_SIGN_LORDS_SQL:
            return [{"sign_id": i, "lord": l} for i, l in self.lords]
        if sql is w._FETCH_PRESENT_POSITIONS_SQL:
            return [{"fact_subject": s} for s in self.present]
        if sql is w._FETCH_GRAHA_SIGN_NUMS_SQL:
            return [{"fact_subject": s, "fact_value_num": 1 + i % 12}
                    for i, s in enumerate(self.present) if s != "LAGNA"]
        if sql is w._FETCH_GULIKA_MANDI_SIGNS_SQL:
            return [{"fact_subject": "MANDI", "fact_value_text": "Leo"},
                    {"fact_subject": "YAMAKANTAKA", "fact_value_text": "Cancer"}]
        if sql is w._FETCH_MOON_NAKSHATRA_SQL:
            return [{"fact_value_num": 3}]
        raise AssertionError(f"unexpected SQL: {sql[:60]!r}")


def _lord_rows(refs):
    return [{"target_type": "lord", "target_ref": r, "target_resolution_state": "resolved"}
            for r in refs]


def _stamp(conn, refs):
    ctx = w._fetch_chart_resolution_context(conn, "chart")
    rows = _lord_rows(refs)
    report = {"resolved": 0, "unavailable": 0, "unqualified": 0, "unavailable_refs": [],
              "unqualified_refs": [], "resolved_map": {}}
    w._stamp_target_resolution(rows, ctx, report)
    return ctx, rows, report


def test_lowercase_l0_lords_resolve_every_house_lord_ref_the_51_shape():
    refs = [f"{n}L" for n in range(1, 13)]
    ctx, rows, report = _stamp(_Conn(), refs)
    assert ctx["sign_lords"] is not None and set(ctx["sign_lords"].values()) <= set(
        w._KARAKA_FACT_SUBJECT)                       # normalised to the maps' Title-case keys
    assert [r["target_resolution_state"] for r in rows] == ["resolved"] * 12
    assert report["resolved"] == 12 and report["unavailable"] == 0
    # Aries lagna: 1L = Mars … 12L = Jupiter, resolved through the REAL seed's lords
    assert report["resolved_map"]["1L"] == "Mars" and report["resolved_map"]["7L"] == "Venus"
    assert report["resolved_map"]["12L"] == "Jupiter"


def test_the_bug_would_have_been_every_lord_row_unavailable():
    """The pre-fix lookup, reproduced on the same inputs: a Title-case dict keyed lookup of
    the L0's lowercase lord finds nothing — all 12 'unavailable'."""
    raw = {i: l for i, l in [(s[0], s[3]) for s in L0_SIGNS]}
    assert all(w._KARAKA_FACT_SUBJECT.get(lord) is None for lord in raw.values())


def _m6(conn, sign_lords=None):
    m6 = dict(w._fetch_chart_resolution_context(conn, "chart"))
    m6.update(w._fetch_m6_context(conn, "chart"))
    if sign_lords is not None:
        m6["sign_lords"] = sign_lords
    report = {"rows": 0, "resolved": 0, "unavailable": 0, "unqualified": 0}
    return w._build_m6_derived_rows("bereavement", m6, report=report), report


def test_m6_lord_derived_rows_resolve_where_operands_exist():
    rows, report = _m6(_Conn())
    assert report["rows"] == 5 and report["unavailable"] == 0 and report["unqualified"] == 0
    assert {r["target_resolution_state"] for r in rows} == {"resolved"}


def test_m6_pre_fix_shape_left_the_lord_dependent_rows_unavailable():
    """The same inputs with the lords left exactly as L0 stores them (lowercase, un-normalised):
    the two reference_signs-dependent rows (the 8th lord and the lagna lord) are unavailable —
    the defect. (The 5th-star lord rides the Vimśottarī table, a different path.)"""
    raw = {s[0]: s[3] for s in L0_SIGNS}
    rows, report = _m6(_Conn(), sign_lords=raw)
    bad = {r["target_ref"] for r in rows if r["target_resolution_state"] == "unavailable"}
    assert bad == {"mandi_sign_distance_from_8L", "lagna_lord_minus_yamakantaka"}
    assert report["unavailable"] == 2


def test_an_unrecognised_lord_name_is_unqualified_and_named_never_silently_unavailable():
    seed = [(s[0], s[3]) for s in L0_SIGNS]
    seed[0] = (1, "mangalyaan")                       # an unrecognised spelling for sign 1
    ctx, rows, report = _stamp(_Conn(lords=seed), ["1L", "2L"])
    assert ctx["unknown_lords"] == {1: "mangalyaan"}
    by_ref = {r["target_ref"]: r["target_resolution_state"] for r in rows}
    assert by_ref["1L"] == "unqualified"              # rulership unusable, not 'unavailable'
    assert by_ref["2L"] == "resolved"                 # the rest of the table still resolves
    assert report["unqualified"] == 1


def test_mixed_case_and_padded_names_normalise_through_the_graha_vocabulary():
    for raw in ("MARS", "Mars", "mars", " mars ", "MAR"):
        assert w._canonical_lord(raw) == "Mars", raw
    for raw in ("", None, "nobody"):
        assert w._canonical_lord(raw) is None


def test_an_incomplete_rulership_table_is_still_unqualified_never_a_silent_default():
    ctx, rows, _ = _stamp(_Conn(lords=[(s[0], s[3]) for s in L0_SIGNS][:11]), ["1L"])
    assert ctx["sign_lords"] is None
    assert rows[0]["target_resolution_state"] == "unqualified"
