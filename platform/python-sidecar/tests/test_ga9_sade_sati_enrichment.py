"""
test_ga9_sade_sati_enrichment.py — Unit tests for the GA9 natal_facts real-data
enrichment helpers added to ga_sade_sati_writer.py (BA Full Asset Audit #4).

Prior to this fix, build_ga_sade_sati() built a single `natal_facts` dict from
hardcoded stub values (e.g. `"saturn_yoga_karaka": False  # Aries Lagna`) and
reused it, unchanged, across every Sade Sati cycle for a chart — silently
wrong for any non-Aries-lagna chart, and structurally incapable of reflecting
per-cycle-varying facts (concurrent dasha lords, tara bala at Janma peak).

These tests are DB-free: a minimal FakeConn/FakeCursor backs `conn.execute(sql,
params).fetchone()/.fetchall()` with canned dict-row results, matching the
access pattern the writer itself already uses (`row["col"]`), following the
style of FakeConn/FakeCursor fixtures elsewhere in this tests/ directory
(e.g. test_ga_idempotency.py, test_orchestrator_gate.py).
"""
from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timezone
from typing import Any, Callable

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT  # noqa: E402
from ga_writers.ga_sade_sati_writer import (  # noqa: E402
    YOGA_KARAKA_BY_LAGNA,
    PLANET_OWN_SIGNS,
    PLANET_EXALTATION_SIGN,
    _read_graha_position_field,
    _lookup_dasha_lord_at,
    _lookup_argala_for_sign,
    _lookup_d10_karya_activation_facts,
    _build_static_natal_facts,
    _verif_for_text,
    _verif_for_maybe_none,
    _make_row,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYANAMSHA = "lahiri_chitrapaksha"


def _dt(y, m, d) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


# ── Fake DB plumbing ──────────────────────────────────────────────────────────

class FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConn:
    """
    Routes `conn.execute(sql, params)` to a caller-supplied handler that
    inspects the SQL text and returns the row list FakeCursor should serve.
    Mirrors the dict-row access pattern (`row["col"]`) used throughout
    ga_sade_sati_writer.py's real conn.execute(...).fetchone()/.fetchall() calls.
    """

    def __init__(self, handler: Callable[[str, list], list[dict[str, Any]]]):
        self._handler = handler

    def execute(self, sql: str, params: list | None = None) -> FakeCursor:
        return FakeCursor(self._handler(sql, params or []))


# ── _read_graha_position_field ───────────────────────────────────────────────

def test_read_graha_position_field_returns_per_ayanamsha_map():
    def handler(sql, params):
        assert "graha_position" in sql
        assert params == [CHART_ID, "SAT", "sign"]
        return [{"ayanamsha_id": AYANAMSHA, "val": "Capricorn"}]

    conn = FakeConn(handler)
    result = _read_graha_position_field(conn, CHART_ID, "SAT", "sign")
    assert result == {AYANAMSHA: "Capricorn"}


def test_read_graha_position_field_numeric_uses_value_num_column():
    captured = {}

    def handler(sql, params):
        captured["sql"] = sql
        return [{"ayanamsha_id": AYANAMSHA, "val": 7.0}]

    conn = FakeConn(handler)
    result = _read_graha_position_field(conn, CHART_ID, "SAT", "house_d1", numeric=True)
    assert result == {AYANAMSHA: 7.0}
    assert "fact_value_num" in captured["sql"]


# ── _lookup_dasha_lord_at ─────────────────────────────────────────────────────

def test_lookup_dasha_lord_at_returns_lord_graha_for_vimshottari():
    def handler(sql, params):
        assert "chart_dashas" in sql
        assert params[2] == "vimshottari" and params[3] == 1
        return [{"lord_graha": "JUP", "lord_sign": None}]

    conn = FakeConn(handler)
    val = _lookup_dasha_lord_at(conn, CHART_ID, AYANAMSHA, "vimshottari", 1, _dt(2020, 1, 1))
    assert val == "JUP"


def test_lookup_dasha_lord_at_uses_lord_sign_for_chara_karaka():
    def handler(sql, params):
        return [{"lord_graha": "VEN", "lord_sign": "Libra"}]

    conn = FakeConn(handler)
    val = _lookup_dasha_lord_at(conn, CHART_ID, AYANAMSHA, "chara_karaka", 1, _dt(2020, 1, 1))
    assert val == "Libra"


def test_lookup_dasha_lord_at_returns_none_when_no_covering_row():
    conn = FakeConn(lambda sql, params: [])
    val = _lookup_dasha_lord_at(conn, CHART_ID, AYANAMSHA, "mudda", 1, _dt(2020, 1, 1))
    assert val is None


# ── _lookup_argala_for_sign ───────────────────────────────────────────────────

def test_lookup_argala_for_sign_converts_source_sign_to_house_via_lagna():
    # Target sign = Aquarius (11), Lagna = Aries (1) -> to_h = ((11-1)%12)+1 = 11
    # A non-zero argala row from Sagittarius (9) -> from_h = ((9-1)%12)+1 = 9
    def handler(sql, params):
        assert "argala_natal_matrix" in sql
        assert params[2] == "D1_SIGN_11"
        return [{"fact_key": "from_sign_9_offset_3", "fact_value_num": 0.75}]

    conn = FakeConn(handler)
    result = _lookup_argala_for_sign(conn, CHART_ID, AYANAMSHA, "Aquarius", "Aries")
    assert result == [{"from_h": 9, "to_h": 11, "strength": 0.75}]


def test_lookup_argala_for_sign_returns_empty_for_unknown_sign():
    conn = FakeConn(lambda sql, params: [])
    assert _lookup_argala_for_sign(conn, CHART_ID, AYANAMSHA, "NotASign", "Aries") == []


# ── _lookup_d10_karya_activation_facts ───────────────────────────────────────

def test_lookup_d10_karya_activation_facts_queries_chart_divisionals():
    def handler(sql, params):
        assert "chart_divisionals" in sql
        assert "chart_facts" not in sql  # must NOT query chart_facts (GA6 lives in chart_divisionals)
        return [{"id": "row-uuid-1", "fact_value_text": "career_karya", "fact_value_num": 10.0}]

    conn = FakeConn(handler)
    result = _lookup_d10_karya_activation_facts(conn, CHART_ID, AYANAMSHA)
    assert result == [{"ref_id": "row-uuid-1", "karya": "career_karya", "house": 10.0}]


def test_lookup_d10_karya_activation_facts_empty_when_ga6_not_written():
    conn = FakeConn(lambda sql, params: [])
    assert _lookup_d10_karya_activation_facts(conn, CHART_ID, AYANAMSHA) == []


# ── _build_static_natal_facts: classical rule correctness ───────────────────

def _make_static_facts_conn(
    lagna_sign: str, saturn_sign: str, saturn_house: float,
    moon_house: float, moon_sign_lord: str, lord_sign: str,
) -> FakeConn:
    """
    Route graha_position lookups by (fact_subject, fact_key) so
    _build_static_natal_facts's several _read_graha_position_field calls each
    get the right canned answer.
    """
    def handler(sql, params):
        if "chart_divisionals" in sql:
            return []  # no D10 karya row in this fixture
        chart_id, subject, key = params[0], params[1], params[2]
        if subject == "LAGNA" and key == "sign":
            return [{"ayanamsha_id": AYANAMSHA, "val": lagna_sign}]
        if subject == "SAT" and key == "sign":
            return [{"ayanamsha_id": AYANAMSHA, "val": saturn_sign}]
        if subject == "SAT" and key == "house_d1":
            return [{"ayanamsha_id": AYANAMSHA, "val": saturn_house}]
        if subject == "MOON" and key == "house_d1":
            return [{"ayanamsha_id": AYANAMSHA, "val": moon_house}]
        if subject == "MOON" and key == "sign_lord":
            return [{"ayanamsha_id": AYANAMSHA, "val": moon_sign_lord}]
        # lord's own natal sign lookup (subject = abbreviation of moon_sign_lord)
        if key == "sign":
            return [{"ayanamsha_id": AYANAMSHA, "val": lord_sign}]
        return []

    return FakeConn(handler)


def test_saturn_yoga_karaka_true_for_taurus_lagna():
    """Classical BPHS rule: Saturn is Yogakaraka for Taurus/Libra lagnas."""
    conn = _make_static_facts_conn(
        lagna_sign="Taurus", saturn_sign="Sagittarius", saturn_house=8.0,
        moon_house=3.0, moon_sign_lord="Mars", lord_sign="Aries",
    )
    facts = _build_static_natal_facts(conn, CHART_ID, AYANAMSHA, "Scorpio", 1)
    assert facts["saturn_yoga_karaka"] is True


def test_saturn_yoga_karaka_false_for_aries_lagna():
    """Regression guard: the deleted hardcoded 'Aries Lagna -> False' case
    must still resolve to False, but now via the real per-chart lagna lookup
    + classical table, not a hardcoded native-specific constant."""
    conn = _make_static_facts_conn(
        lagna_sign="Aries", saturn_sign="Capricorn", saturn_house=10.0,
        moon_house=11.0, moon_sign_lord="Saturn", lord_sign="Capricorn",
    )
    facts = _build_static_natal_facts(conn, CHART_ID, AYANAMSHA, "Aquarius", 4)
    assert facts["saturn_yoga_karaka"] is False
    assert facts["lagna_sign"] == "Aries"


def test_natal_saturn_aspects_natal_moon_via_special_drishti():
    """Saturn's special 3rd/7th/10th aspect: Saturn house=1, Moon house=7 (diff=6) -> aspected."""
    conn = _make_static_facts_conn(
        lagna_sign="Cancer", saturn_sign="Capricorn", saturn_house=1.0,
        moon_house=7.0, moon_sign_lord="Moon", lord_sign="Cancer",
    )
    facts = _build_static_natal_facts(conn, CHART_ID, AYANAMSHA, "Cancer", 2)
    assert facts["natal_saturn_aspects_natal_moon"] is True


def test_natal_saturn_aspects_natal_moon_false_when_no_special_drishti():
    """Saturn house=1, Moon house=2 (diff=1) is not a 3rd/7th/10th aspect."""
    conn = _make_static_facts_conn(
        lagna_sign="Cancer", saturn_sign="Capricorn", saturn_house=1.0,
        moon_house=2.0, moon_sign_lord="Moon", lord_sign="Cancer",
    )
    facts = _build_static_natal_facts(conn, CHART_ID, AYANAMSHA, "Cancer", 2)
    assert facts["natal_saturn_aspects_natal_moon"] is False


def test_saturn_moon_parivartana_true_when_mutual_sign_exchange():
    """Saturn in Cancer (Moon's own sign) AND Moon in Aquarius (Saturn's own sign)."""
    conn = _make_static_facts_conn(
        lagna_sign="Gemini", saturn_sign="Cancer", saturn_house=2.0,
        moon_house=9.0, moon_sign_lord="Saturn", lord_sign="Cancer",
    )
    facts = _build_static_natal_facts(conn, CHART_ID, AYANAMSHA, "Aquarius", 3)
    assert facts["saturn_moon_parivartana"] is True


def test_moon_sign_lord_strong_true_when_lord_exalted():
    """Moon in Cancer -> lord is Moon itself; if natal Moon were exalted (Taurus)
    it would be strong. Use Aries Moon (lord Mars) exalted in Capricorn instead."""
    conn = _make_static_facts_conn(
        lagna_sign="Gemini", saturn_sign="Virgo", saturn_house=4.0,
        moon_house=11.0, moon_sign_lord="Mars", lord_sign="Capricorn",
    )
    facts = _build_static_natal_facts(conn, CHART_ID, AYANAMSHA, "Aries", 1)
    assert facts["moon_sign_lord_strong"] is True
    assert PLANET_EXALTATION_SIGN["Mars"] == "Capricorn"


def test_moon_sign_lord_strong_false_when_lord_neutral():
    conn = _make_static_facts_conn(
        lagna_sign="Gemini", saturn_sign="Virgo", saturn_house=4.0,
        moon_house=11.0, moon_sign_lord="Mars", lord_sign="Gemini",
    )
    facts = _build_static_natal_facts(conn, CHART_ID, AYANAMSHA, "Aries", 1)
    assert facts["moon_sign_lord_strong"] is False


def test_static_facts_leaves_undetectable_transit_facts_as_honest_none():
    """No Jupiter/Mars/Rahu/eclipse transit-detection engine exists in this
    writer — these must stay honest None, never a fabricated boolean."""
    conn = _make_static_facts_conn(
        lagna_sign="Gemini", saturn_sign="Virgo", saturn_house=4.0,
        moon_house=11.0, moon_sign_lord="Mars", lord_sign="Gemini",
    )
    facts = _build_static_natal_facts(conn, CHART_ID, AYANAMSHA, "Aries", 1)
    for key in (
        "jupiter_aspects_saturn_during_cycle",
        "mars_aspect_during_period",
        "jupiter_aspect_during_period",
        "saturn_rahu_axis_flag",
        "eclipse_during_period",
        "d10_karya_bhava_activation_flag",
    ):
        assert facts[key] is None, f"{key} should be an honest None placeholder"


# ── Yogakaraka table sanity (matches brief's cited BPHS rule) ────────────────

def test_yoga_karaka_table_matches_bphs_rule():
    assert YOGA_KARAKA_BY_LAGNA["Taurus"] == "Saturn"
    assert YOGA_KARAKA_BY_LAGNA["Libra"] == "Saturn"
    assert "Aries" not in YOGA_KARAKA_BY_LAGNA


def test_planet_own_signs_and_exaltation_tables_are_classical():
    assert PLANET_OWN_SIGNS["Saturn"] == ["Capricorn", "Aquarius"]
    assert PLANET_EXALTATION_SIGN["Saturn"] == "Libra"


# ── _verif_for_text / _verif_for_maybe_none ──────────────────────────────────

def test_verif_for_text_flags_pending_fallback_as_single():
    # Stage 2 honest-tiers rewrite (was: test_verif_for_text_flags_pending_fallback_as_single
    # asserting "single_pass" for the non-placeholder branch). REWRITTEN, not silently
    # flipped: an earlier M-22 pass correctly demoted the non-placeholder branch off the
    # top "two_pass_verified" tier, but landed on 'single_pass' — a DEPRECATED spelling
    # (verification_vocab.VocabEntry('single_pass', ..., deprecated_alias_of='single')),
    # not a distinct tier. The premise that a real-upstream-join value should be
    # DISTINGUISHABLE from a PENDING_* placeholder was never true either: neither branch
    # has a second independent derivation behind it (one upstream DB read is one pass,
    # not two), so both are honestly "no verification ran" — UNVERIFIED_DEFAULT ('single')
    # in both cases. Anchored to the vocab's canonical constant, not to the writer's own
    # literal, so this isn't a tautology over the code under test.
    assert _verif_for_text("PENDING_GA7_LOOKUP") == UNVERIFIED_DEFAULT
    assert _verif_for_text("JUP") == UNVERIFIED_DEFAULT


def test_verif_for_maybe_none_flags_none_as_single():
    # Stage 2 honest-tiers rewrite (was asserting "single_pass" for non-None values) —
    # same rationale as test_verif_for_text_flags_pending_fallback_as_single above: a
    # present-but-unchecked value and an honestly-absent one are both single-pass-or-less,
    # neither backed by a second derivation, so both resolve to UNVERIFIED_DEFAULT.
    assert _verif_for_maybe_none(None) == UNVERIFIED_DEFAULT
    assert _verif_for_maybe_none(False) == UNVERIFIED_DEFAULT
    assert _verif_for_maybe_none(True) == UNVERIFIED_DEFAULT


# ── _make_row: value_jsonb must tolerate Decimal (BA-P3 rebuild regression) ──

def test_make_row_serializes_decimal_inside_value_jsonb():
    """_lookup_d10_karya_activation_facts() returns dicts whose 'house' value
    comes from chart_divisionals.fact_value_num — a NUMERIC column that
    psycopg adapts to Decimal, not float. json.dumps(value_jsonb) without
    default=str raises TypeError: Object of type Decimal is not JSON
    serializable — this broke ga_sade_sati (and therefore blocked its entire
    downstream L2-L5 DAG) as soon as GA9 enrichment started passing real
    upstream facts instead of stub placeholders."""
    from decimal import Decimal

    row = _make_row(
        CHART_ID, AYANAMSHA, "build-x",
        "sade_sati_dasha_context", "cycle1_JANMA", "d10_karya_activation_facts_jsonb",
        value_text=None, value_num=None,
        value_jsonb=[{"ref_id": "row-uuid-1", "karya": "career_karya", "house": Decimal("10")}],
        citation_human="test",
    )
    assert row["fact_value_jsonb"] == '[{"ref_id": "row-uuid-1", "karya": "career_karya", "house": "10"}]'
