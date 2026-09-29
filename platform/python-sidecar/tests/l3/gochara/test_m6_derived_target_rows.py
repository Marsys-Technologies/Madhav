"""
test_m6_derived_target_rows.py — M-6 derived transit targets
(GOCHARA_RULING_SHEET_v2_0 §1 M-6; remainder brief §4.4; WP1_CONTRACTS.md
§2.2 items 9-11; Phaladīpikā Adh. XVII).

Pins:
  1. VALID_TARGET_TYPES carries the three contract-extension types.
  2. The shared sign-grain arithmetic in
     services/gochara_grammar/derived_points.py (single source imported by
     BOTH the resonance writer and gochara_intensity.enrichment).
  3. The writer-side builders (_build_m6_derived_rows,
     _build_bhava_arudha_rows): class scoping (bereavement/illness_acute
     only for the derived points), honest resolution states, citation and
     qualifier discipline, provisional weight 0.5 (WP8 owns values).
  4. The read-side resolver (enrichment.enrich_target) end-to-end against a
     sqlite-shimmed chart_facts/reference_signs built from the WP1 golden
     fixtures (tests/l3/gochara/fixtures/wp1_target_resolution.json v1.1).

Fixture discipline: every chart id is a synthetic wp1-synth-* id; no real
chart, no Swiss-Ephemeris output (derivation: hand-specified).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from services.gochara_grammar.models import VALID_TARGET_TYPES, ResonanceTarget
from services.gochara_grammar import derived_points as dp
from services.gochara_intensity.enrichment import enrich_target
from services.ka_gochara_resonance.writer import (
    _CLASSICAL_SIGN_LORDS,
    _build_bhava_arudha_rows,
    _build_m6_derived_rows,
    build_resonance_rows,
)

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures/wp1_target_resolution.json").read_text()
)
AYANAMSHA = "lahiri_chitrapaksha"


def _case(name: str) -> dict:
    return FIXTURES["cases"][name]


# ── 1. target_type vocabulary ────────────────────────────────────────────────

class TestValidTargetTypes:
    def test_m6_types_present(self):
        for tt in ("gulika_mandi_distance", "yamakantaka_difference", "bhava_arudha"):
            assert tt in VALID_TARGET_TYPES

    def test_original_eight_unchanged(self):
        for tt in ("bhava", "lord", "karaka", "mechanism_node", "sensitive_degree",
                   "arudha", "yoga_constituent", "dasha_lord_portfolio"):
            assert tt in VALID_TARGET_TYPES

    def test_resonance_target_accepts_m6_types(self):
        t = ResonanceTarget(
            chart_id="wp1-synth-x", event_class="bereavement",
            target_type="yamakantaka_difference",
            target_ref="sun_minus_yamakantaka", weight=0.5,
            classical_citation="PG214:C1 śl.7",
        )
        assert t.target_type == "yamakantaka_difference"


# ── 2. shared arithmetic (derived_points.py) ─────────────────────────────────

class TestDerivedPointsArithmetic:
    def test_difference_sign_num_fixture_pins(self):
        # From the fixture goldens:
        assert dp.difference_sign_num(3, 5) == 10   # lagna-lord Moon Gemini − Y Leo -> Capricorn
        assert dp.difference_sign_num(1, 5) == 8    # Sun Aries − Y Leo -> Scorpio
        assert dp.difference_sign_num(5, 6) == 11   # Y Leo − Māndi Virgo -> Aquarius
        assert dp.difference_sign_num(8, 5) == 3    # Mars Scorpio − Y Leo -> Gemini
        assert dp.difference_sign_num(2, 2) == 12   # equal operands -> 0 read as 12 (Pisces)

    def test_mandi_distance_fixture_pin(self):
        # e=2 (Taurus), m=6 (Virgo): N=(6-2)=4 steps forward from Māndi
        # (Libra 1, Scorpio 2, Sagittarius 3, Capricorn 4) -> 10 (Capricorn)
        assert dp.mandi_distance_target_sign_num(2, 6) == 10
        # same sign -> N=0 -> Māndi's own sign (literal reading of the verse)
        assert dp.mandi_distance_target_sign_num(6, 6) == 6

    def test_sign_round_trip(self):
        for n in range(1, 13):
            assert dp.sign_num_of(dp.sign_name_of(n)) == n
        assert dp.sign_num_of("Ophiuchus") is None

    def test_fifth_star_lord_fixture_pin(self):
        # natal nakṣatra 1 counts as the 1st; 5th = 5 (Mṛigaśīrṣa) -> Mars
        assert dp.nakshatra_lord(5) == "Mars"
        assert dp.fifth_star_lord(1) == "Mars"
        # wrap: natal 25 -> 5th = 29 -> 2 (Bharanī) -> Venus
        assert dp.fifth_star_lord(25) == "Venus"

    def test_scope_and_formula_pins(self):
        assert dp.M6_EVENT_CLASSES == ("bereavement", "illness_acute")
        assert dp.MANDI_DISTANCE_REF == "mandi_sign_distance_from_8L"
        assert dp.MANDI_DISTANCE_CITATION == "PG220:C1 śl.26"
        assert dp.MANDI_DISTANCE_AGENT == "Saturn"
        formulas = {f["ref"]: f for f in dp.YAMAKANTAKA_FORMULAS}
        assert set(formulas) == {
            "lagna_lord_minus_yamakantaka", "sun_minus_yamakantaka",
            "yamakantaka_minus_mandi", "panchama_tara_lord_minus_yamakantaka",
        }
        assert formulas["lagna_lord_minus_yamakantaka"]["agent"] == "Jupiter"
        assert formulas["lagna_lord_minus_yamakantaka"]["citation"] == "PG214:C1 śl.6; PG217:C1 śl.14"
        assert formulas["sun_minus_yamakantaka"]["agent"] == "Jupiter"
        assert formulas["yamakantaka_minus_mandi"]["agent"] == "Saturn"
        assert formulas["yamakantaka_minus_mandi"]["minuend"] == "yamakantaka"
        assert formulas["yamakantaka_minus_mandi"]["subtrahend"] == "mandi"
        assert formulas["panchama_tara_lord_minus_yamakantaka"]["minuend"] == "fifth_star_lord"


# ── 3. writer-side builders ──────────────────────────────────────────────────

def _full_m6_ctx() -> dict:
    """Mirrors the golden fixture chart (...000d/000e): LAGNA Cancer(4),
    SAT Taurus(2), MOON Gemini(3), SUN Aries(1), MAR Scorpio(8),
    MANDI Virgo, YAMAKANTAKA Leo, Moon nakṣatra 1."""
    return {
        "lagna_sign_num": 4,
        "sign_lords": dict(_CLASSICAL_SIGN_LORDS),
        "graha_sign_nums": {"SAT": 2, "MOON": 3, "SUN": 1, "MAR": 8},
        "gulika_mandi_signs": {"MANDI": "Virgo", "YAMAKANTAKA": "Leo"},
        "moon_nakshatra_id": 1,
    }


def _by_ref(rows: list[dict]) -> dict:
    return {(r["target_type"], r["target_ref"]): r for r in rows}


class TestBuildM6DerivedRows:
    def test_golden_all_five_rows_resolved(self):
        report = {"rows": 0, "resolved": 0, "unavailable": 0, "unqualified": 0}
        rows = _build_m6_derived_rows("bereavement", _full_m6_ctx(), report=report)
        assert len(rows) == 5
        refs = _by_ref(rows)
        assert refs[("gulika_mandi_distance", "mandi_sign_distance_from_8L")]["target_resolution_state"] == "resolved"
        for ref in ("lagna_lord_minus_yamakantaka", "sun_minus_yamakantaka",
                    "yamakantaka_minus_mandi", "panchama_tara_lord_minus_yamakantaka"):
            row = refs[("yamakantaka_difference", ref)]
            assert row["target_resolution_state"] == "resolved"
        assert report == {"rows": 5, "resolved": 5, "unavailable": 0, "unqualified": 0}

    def test_citation_qualifier_weight_discipline(self):
        rows = _build_m6_derived_rows("bereavement", _full_m6_ctx())
        for row in rows:
            assert row["weight"] == 0.5, "provisional weight pending WP8"
            assert row["uncited_extension"] is False
            assert row["classical_citation"], "M-6 rows are classically cited (B.10)"
            assert row["target_qualifier"].startswith("agent:")
        refs = _by_ref(rows)
        assert refs[("gulika_mandi_distance", "mandi_sign_distance_from_8L")]["target_qualifier"] == "agent:Saturn"
        assert refs[("gulika_mandi_distance", "mandi_sign_distance_from_8L")]["classical_citation"] == "PG220:C1 śl.26"
        assert refs[("yamakantaka_difference", "yamakantaka_minus_mandi")]["target_qualifier"] == "agent:Saturn"

    def test_class_scoping_both_m6_classes(self):
        for event_class in dp.M6_EVENT_CLASSES:
            assert len(_build_m6_derived_rows(event_class, _full_m6_ctx())) == 5

    @pytest.mark.parametrize("event_class", [
        "marriage", "major_gain", "career_advancement", "chronic_onset", "surgery",
        "childbirth", "parental_event", "spiritual_turn", "birth_anchor",
    ])
    def test_class_scoping_other_classes_get_zero_rows(self, event_class):
        assert _build_m6_derived_rows(event_class, _full_m6_ctx()) == []

    def test_missing_mandi_fact_unavailable(self):
        ctx = _full_m6_ctx()
        ctx["gulika_mandi_signs"] = {"YAMAKANTAKA": "Leo"}
        refs = _by_ref(_build_m6_derived_rows("bereavement", ctx))
        assert refs[("gulika_mandi_distance", "mandi_sign_distance_from_8L")]["target_resolution_state"] == "unavailable"
        assert refs[("yamakantaka_difference", "yamakantaka_minus_mandi")]["target_resolution_state"] == "unavailable"
        assert refs[("yamakantaka_difference", "sun_minus_yamakantaka")]["target_resolution_state"] == "resolved"

    def test_missing_yamakantaka_fact_unavailable_native_only(self):
        """E-008: Yamakaṇṭaka is native-only; no day-table fallback. Absent
        fact -> every yamakantaka_difference row 'unavailable'; the Māndi
        row (no Yamakaṇṭaka operand) is unaffected."""
        ctx = _full_m6_ctx()
        ctx["gulika_mandi_signs"] = {"MANDI": "Virgo"}
        refs = _by_ref(_build_m6_derived_rows("illness_acute", ctx))
        for ref in ("lagna_lord_minus_yamakantaka", "sun_minus_yamakantaka",
                    "yamakantaka_minus_mandi", "panchama_tara_lord_minus_yamakantaka"):
            assert refs[("yamakantaka_difference", ref)]["target_resolution_state"] == "unavailable"
        assert refs[("gulika_mandi_distance", "mandi_sign_distance_from_8L")]["target_resolution_state"] == "resolved"

    def test_missing_rulership_unqualified_not_silent_fallback(self):
        ctx = _full_m6_ctx()
        ctx["sign_lords"] = None
        refs = _by_ref(_build_m6_derived_rows("bereavement", ctx))
        assert refs[("gulika_mandi_distance", "mandi_sign_distance_from_8L")]["target_resolution_state"] == "unqualified"
        assert refs[("yamakantaka_difference", "lagna_lord_minus_yamakantaka")]["target_resolution_state"] == "unqualified"
        # formulas without a lord operand stay resolved
        assert refs[("yamakantaka_difference", "yamakantaka_minus_mandi")]["target_resolution_state"] == "resolved"

    def test_missing_lagna_unavailable(self):
        ctx = _full_m6_ctx()
        ctx["lagna_sign_num"] = None
        refs = _by_ref(_build_m6_derived_rows("bereavement", ctx))
        assert refs[("gulika_mandi_distance", "mandi_sign_distance_from_8L")]["target_resolution_state"] == "unavailable"
        assert refs[("yamakantaka_difference", "lagna_lord_minus_yamakantaka")]["target_resolution_state"] == "unavailable"

    def test_missing_moon_nakshatra_unavailable(self):
        ctx = _full_m6_ctx()
        ctx["moon_nakshatra_id"] = None
        refs = _by_ref(_build_m6_derived_rows("bereavement", ctx))
        assert refs[("yamakantaka_difference", "panchama_tara_lord_minus_yamakantaka")]["target_resolution_state"] == "unavailable"


class TestBuildBhavaArudhaRows:
    def test_golden_mix(self):
        facts = [{"fact_subject": "ARUDHA_A7", "fact_value_text": "Gemini"}]
        report = {"rows": 0, "unavailable": 0}
        rows = _build_bhava_arudha_rows("marriage", [1, 7], facts, report=report)
        assert len(rows) == 2
        refs = _by_ref(rows)
        a7 = refs[("bhava_arudha", "BHAVA_ARUDHA_A7")]
        assert a7["target_resolution_state"] == "resolved"
        assert a7["weight"] == 0.6 and a7["uncited_extension"] is True
        assert a7["classical_citation"] is None
        a1 = refs[("bhava_arudha", "BHAVA_ARUDHA_A1")]
        assert a1["target_resolution_state"] == "unavailable"
        assert report == {"rows": 2, "unavailable": 1}

    def test_invalid_sign_value_unavailable(self):
        rows = _build_bhava_arudha_rows(
            "marriage", [7], [{"fact_subject": "ARUDHA_A7", "fact_value_text": "Ophiuchus"}])
        assert rows[0]["target_resolution_state"] == "unavailable"

    def test_emitted_for_any_class_via_build_resonance_rows(self):
        rows = build_resonance_rows(
            "spiritual_turn",
            houses=["9"], lords=[], karakas=[],
            arudha_fact_rows=[{"fact_id": "wp1synth.arudha_a9.sign",
                               "fact_subject": "ARUDHA_A9", "fact_value_text": "Leo"}],
        )
        ba = [r for r in rows if r["target_type"] == "bhava_arudha"]
        assert len(ba) == 1 and ba[0]["target_ref"] == "BHAVA_ARUDHA_A9"
        assert ba[0]["target_resolution_state"] == "resolved"
        # The derived M-6 points are run()-level, never built here.
        assert not [r for r in rows
                    if r["target_type"] in ("gulika_mandi_distance", "yamakantaka_difference")]


# ── 4. read-side resolver (enrichment) against the WP1 golden fixtures ───────

class _SqlitePgShim:
    """sqlite3-backed stand-in for a psycopg connection: translates the
    %s placeholders this codebase writes (psycopg style) to sqlite's ? and
    keeps an explicit transaction open so savepoint_scope exercises real
    SAVEPOINT/RELEASE semantics (same technique as
    tests/test_gochara_intensity.py's orchestrator-savepoint tests)."""

    def __init__(self):
        self._conn = sqlite3.connect(":memory:", isolation_level=None)
        self._conn.execute("BEGIN")

    def execute(self, sql, params=None):
        return self._conn.execute(sql.replace("%s", "?"), params or [])

    def close(self):
        self._conn.close()


def _shim_for_case(case: dict, *, reference_signs: bool = True) -> _SqlitePgShim:
    shim = _SqlitePgShim()
    shim.execute(
        "CREATE TABLE chart_facts (chart_id TEXT, ayanamsha_id TEXT, fact_category TEXT,"
        " fact_subject TEXT, fact_key TEXT, fact_value_text TEXT, fact_value_num REAL,"
        " fact_id TEXT)"
    )
    for f in case["inputs"].get("chart_facts", []):
        shim.execute(
            "INSERT INTO chart_facts VALUES (?,?,?,?,?,?,?,?)",
            [case["chart_id"], AYANAMSHA, f["fact_category"], f["fact_subject"],
             f["fact_key"], f.get("fact_value_text"), f.get("fact_value_num"),
             f.get("fact_id")],
        )
    if reference_signs:
        shim.execute("CREATE TABLE reference_signs (sign_id INTEGER, lord TEXT)")
        for sign_id, lord in sorted(_CLASSICAL_SIGN_LORDS.items()):
            shim.execute("INSERT INTO reference_signs VALUES (?,?)", [sign_id, lord])
    return shim


def _target_of(case: dict) -> ResonanceTarget:
    rt = case["inputs"]["resonance_target"]
    expected = case["expected"]
    # Mirror the writer row's citation discipline: cited for the derived
    # points, uncited_extension for bhava_arudha.
    expected_target = (expected.get("targets") or [{}])[0]
    citation = expected_target.get("classical_citation")
    uncited = bool(expected_target.get("uncited_extension"))
    return ResonanceTarget(
        chart_id=case["chart_id"], event_class=rt["event_class"],
        target_type=rt["target_type"], target_ref=rt["target_ref"],
        weight=rt["weight"],
        classical_citation=citation or ("TEST FIXTURE" if not uncited else None),
        uncited_extension=uncited,
    )


class TestEnrichmentM6Golden:
    @pytest.mark.parametrize("case_name", [
        "m6_gulika_mandi_distance_golden",
        "m6_yamakantaka_lagna_lord_golden",
        "m6_yamakantaka_sun_golden",
        "m6_yamakantaka_minus_mandi_golden",
        "m6_yamakantaka_panchama_tara_golden",
        "m6_bhava_arudha_golden",
    ])
    def test_fixture_golden_resolves_target_sign(self, case_name):
        case = _case(case_name)
        shim = _shim_for_case(case)
        try:
            enriched = enrich_target(shim, _target_of(case), ayanamsha_id=AYANAMSHA)
        finally:
            shim.close()
        expected = case["expected"]["targets"][0]
        assert enriched.target_sign == expected["target_sign"]
        # whole-sign span check: the interval is [30*(s-1), 30*s), never a point
        s = dp.sign_num_of(enriched.target_sign)
        assert expected["span_deg"] == [30.0 * (s - 1), 30.0 * s]
        assert enriched.target_longitude_deg is None


class TestEnrichmentM6Unavailable:
    @pytest.mark.parametrize("case_name", [
        "neg_m6_mandi_fact_absent_unavailable",
        "neg_m6_yamakantaka_fact_absent_unavailable",
        "neg_m6_moon_nakshatra_absent_unavailable",
        "neg_m6_bhava_arudha_sign_absent_or_invalid_unavailable",
    ])
    def test_fixture_negative_leaves_target_unresolved(self, case_name):
        case = _case(case_name)
        shim = _shim_for_case(case)
        try:
            enriched = enrich_target(shim, _target_of(case), ayanamsha_id=AYANAMSHA)
        finally:
            shim.close()
        assert enriched.target_sign is None

    def test_missing_reference_signs_leaves_lord_dependent_unresolved(self):
        case = _case("m6_gulika_mandi_distance_golden")
        shim = _shim_for_case(case, reference_signs=False)
        try:
            enriched = enrich_target(shim, _target_of(case), ayanamsha_id=AYANAMSHA)
        finally:
            shim.close()
        assert enriched.target_sign is None

    def test_unknown_yamakantaka_ref_unresolved(self):
        case = _case("m6_yamakantaka_sun_golden")
        shim = _shim_for_case(case)
        target = ResonanceTarget(
            chart_id=case["chart_id"], event_class="bereavement",
            target_type="yamakantaka_difference", target_ref="bogus_ref",
            weight=0.5, classical_citation="TEST FIXTURE",
        )
        try:
            enriched = enrich_target(shim, target, ayanamsha_id=AYANAMSHA)
        finally:
            shim.close()
        assert enriched.target_sign is None

    def test_conn_none_degrades_honestly(self):
        case = _case("m6_yamakantaka_sun_golden")
        enriched = enrich_target(None, _target_of(case), ayanamsha_id=AYANAMSHA)
        assert enriched.target_sign is None
