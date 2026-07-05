"""
Tests for ga_condition writer — pure helper functions + writer class metadata.
Runs without a real DB connection.
"""
from __future__ import annotations

import pytest


# ── Imports ───────────────────────────────────────────────────────────────────

from ga_writers.ga_condition_writer import (
    DIGNITY_SCORES,
    dignity_d1_from_sign,
    avastha_baladi_from_degree,
    avastha_jagradadi_from_dignity,
    avastha_deeptaadi_from_dignity_and_state,
    compute_combustion_arc,
    check_combustion,
    compute_condition_score_v1,
    compute_panchadha_maitri,
    compute_tatkalika_relation,
)
from pipeline.orchestrator.writers.ga_condition import GaConditionWriter


# ── 1. Writer class metadata ──────────────────────────────────────────────────

def test_writer_asset_id():
    """Writer must declare asset_id = 'ga_condition'."""
    assert GaConditionWriter.asset_id == 'ga_condition'


def test_writer_has_substeps():
    """Writer must be a heavy writer (has_substeps = True)."""
    assert GaConditionWriter.has_substeps is True


def test_writer_is_writer_base_subclass():
    """Writer must subclass WriterBase."""
    from pipeline.orchestrator.writers import WriterBase
    assert issubclass(GaConditionWriter, WriterBase)


def test_writer_registered():
    """Writer must be registered in the WRITER_REGISTRY after import."""
    from pipeline.orchestrator.writers import WRITER_REGISTRY
    # Import triggers registration
    import pipeline.orchestrator.writers.ga_condition  # noqa: F401
    assert 'ga_condition' in WRITER_REGISTRY


# ── 2. dignity_d1_from_sign ───────────────────────────────────────────────────

class TestDignityD1FromSign:
    """Sun in Capricorn is the canonical FORENSIC case — must NOT be in dignity."""

    def test_sun_capricorn_is_not_in_dignity(self):
        result = dignity_d1_from_sign("Sun", "Capricorn", 15.0)
        assert result not in ("exalted", "moolatrikona", "own"), (
            f"Sun in Capricorn cannot be in dignity, got '{result}'"
        )

    def test_sun_capricorn_is_enemy(self):
        # Capricorn owned by Saturn; Sun–Saturn are enemies → enemy_sign
        result = dignity_d1_from_sign("Sun", "Capricorn", 15.0)
        assert result == "enemy_sign"

    def test_sun_exaltation_in_aries(self):
        assert dignity_d1_from_sign("Sun", "Aries", 10.0) == "exalted"

    def test_sun_debilitation_in_libra(self):
        assert dignity_d1_from_sign("Sun", "Libra", 10.0) == "debilitated"

    def test_sun_own_sign_leo(self):
        # Degree 25 is past moolatrikona range (0–20), but still own sign
        assert dignity_d1_from_sign("Sun", "Leo", 25.0) == "own"

    def test_sun_moolatrikona_leo_within_range(self):
        # 0–20° in Leo = moolatrikona
        assert dignity_d1_from_sign("Sun", "Leo", 10.0) == "moolatrikona"

    def test_moon_exaltation_taurus(self):
        assert dignity_d1_from_sign("Moon", "Taurus", 3.0) == "exalted"

    def test_moon_debilitation_scorpio(self):
        assert dignity_d1_from_sign("Moon", "Scorpio", 3.0) == "debilitated"

    def test_jupiter_exaltation_cancer(self):
        assert dignity_d1_from_sign("Jupiter", "Cancer", 5.0) == "exalted"

    def test_saturn_exaltation_libra(self):
        assert dignity_d1_from_sign("Saturn", "Libra", 20.0) == "exalted"

    def test_friend_sign_classification(self):
        # Sun in Sagittarius: Jupiter owns Sagittarius; Sun–Jupiter are friends
        result = dignity_d1_from_sign("Sun", "Sagittarius", 15.0)
        assert result == "friend_sign"

    def test_mars_own_sign_scorpio(self):
        assert dignity_d1_from_sign("Mars", "Scorpio", 10.0) == "own"

    def test_mercury_moolatrikona_virgo_in_range(self):
        # Mercury moolatrikona: Virgo 16–20°
        assert dignity_d1_from_sign("Mercury", "Virgo", 17.0) == "moolatrikona"

    def test_mercury_own_gemini(self):
        assert dignity_d1_from_sign("Mercury", "Gemini", 10.0) == "own"


# ── 3. avastha_baladi_from_degree ─────────────────────────────────────────────

class TestAvasthaBaladi:
    """Boundary tests for degree-in-sign → baladi state mapping."""

    @pytest.mark.parametrize("degree,expected", [
        (0.0,   "bala"),
        (3.0,   "bala"),
        (5.9,   "bala"),
        (6.0,   "kumara"),    # boundary: 6 belongs to kumara
        (11.9,  "kumara"),
        (12.0,  "yuva"),      # boundary: 12 belongs to yuva
        (15.0,  "yuva"),
        (17.9,  "yuva"),
        (18.0,  "vriddha"),   # boundary: 18 belongs to vriddha
        (23.9,  "vriddha"),
        (24.0,  "mrita"),     # boundary: 24 belongs to mrita
        (29.9,  "mrita"),
    ])
    def test_degree_to_baladi(self, degree, expected):
        assert avastha_baladi_from_degree(degree) == expected, (
            f"degree={degree} should map to '{expected}'"
        )


# ── 4. avastha_jagradadi_from_dignity ─────────────────────────────────────────

class TestAvasthaJagradadi:
    @pytest.mark.parametrize("dignity,expected", [
        ("exalted",           "jagrata"),
        ("moolatrikona",      "jagrata"),
        ("own",               "jagrata"),
        ("great_friend_sign", "svapna"),
        ("friend_sign",       "svapna"),
        ("neutral_sign",      "sushupti"),
        ("enemy_sign",        "sushupti"),
        ("great_enemy_sign",  "sushupti"),
        ("debilitated",       "sushupti"),
    ])
    def test_dignity_to_jagradadi(self, dignity, expected):
        assert avastha_jagradadi_from_dignity(dignity) == expected


# ── 5. compute_combustion_arc ─────────────────────────────────────────────────

class TestCombustionArc:

    def test_same_longitude(self):
        """Planet at same degree as Sun → arc = 0."""
        assert compute_combustion_arc(100.0, 100.0) == pytest.approx(0.0)

    def test_simple_positive_arc(self):
        assert compute_combustion_arc(115.0, 100.0) == pytest.approx(15.0)

    def test_wrapping_arc_short_side(self):
        """Planet at 359°, Sun at 1° → short arc = 2°."""
        assert compute_combustion_arc(359.0, 1.0) == pytest.approx(2.0)

    def test_wrapping_arc_opposite(self):
        """Planets exactly opposite → arc = 180."""
        assert compute_combustion_arc(180.0, 0.0) == pytest.approx(180.0)

    def test_arc_is_symmetric(self):
        """Arc from A→B equals arc from B→A."""
        assert compute_combustion_arc(30.0, 250.0) == compute_combustion_arc(250.0, 30.0)

    def test_result_in_0_180(self):
        import random
        for _ in range(100):
            p = random.uniform(0, 360)
            s = random.uniform(0, 360)
            arc = compute_combustion_arc(p, s)
            assert 0 <= arc <= 180


# ── 6. check_combustion ───────────────────────────────────────────────────────

class TestCheckCombustion:

    _ORBS = {
        "Moon":    {"orb": 12.0, "deep": 10.0},
        "Mars":    {"orb": 17.0, "deep": 15.0},
        "Mercury": {"orb": 14.0, "deep": 12.0},
        "Jupiter": {"orb": 11.0, "deep":  9.0},
        "Venus":   {"orb": 10.0, "deep":  8.0},
        "Saturn":  {"orb": 15.0, "deep": 12.0},
    }

    def test_sun_never_combust(self):
        is_c, is_dc = check_combustion("Sun", 0.0, self._ORBS)
        assert is_c is False
        assert is_dc is False

    def test_within_deep_orb_is_both(self):
        # Moon, arc = 5° (within deep orb of 10°)
        is_c, is_dc = check_combustion("Moon", 5.0, self._ORBS)
        assert is_c is True
        assert is_dc is True

    def test_between_orbs_is_combust_not_deep(self):
        # Moon: orb=12, deep=10; arc=11° → combust but not deeply
        is_c, is_dc = check_combustion("Moon", 11.0, self._ORBS)
        assert is_c is True
        assert is_dc is False

    def test_outside_orb_is_free(self):
        # Moon: orb=12; arc=15° → not combust
        is_c, is_dc = check_combustion("Moon", 15.0, self._ORBS)
        assert is_c is False
        assert is_dc is False

    def test_exactly_at_deep_orb_boundary(self):
        # Moon deep orb = 10°; arc exactly 10° → deeply combust (≤)
        is_c, is_dc = check_combustion("Moon", 10.0, self._ORBS)
        assert is_c is True
        assert is_dc is True

    def test_graha_not_in_orbs_returns_false(self):
        is_c, is_dc = check_combustion("Rahu", 5.0, {})
        assert is_c is False
        assert is_dc is False


# ── 7. compute_condition_score_v1 ─────────────────────────────────────────────

class TestConditionScore:

    def test_score_in_range(self):
        """All valid inputs should produce a score in [0.0, 1.0]."""
        score, breakdown = compute_condition_score_v1(
            dignity_score=0.8,
            deeptaadi="swastha",
            baladi="yuva",
            is_combust=False,
            is_deeply_combust=False,
            is_retrograde=False,
            varga_score=0.7,
        )
        assert score is not None
        assert 0.0 <= score <= 1.0

    def test_missing_dignity_returns_none(self):
        score, breakdown = compute_condition_score_v1(
            dignity_score=None,
            deeptaadi="swastha",
            baladi="yuva",
            is_combust=False,
            is_deeply_combust=False,
            is_retrograde=False,
            varga_score=0.7,
        )
        assert score is None

    def test_missing_deeptaadi_returns_none(self):
        score, _ = compute_condition_score_v1(
            dignity_score=0.8,
            deeptaadi=None,
            baladi="yuva",
            is_combust=False,
            is_deeply_combust=False,
            is_retrograde=False,
            varga_score=None,
        )
        assert score is None

    def test_exalted_planet_scores_high(self):
        """Exalted, deepta, yuva, not combust → score near top.
        Formula ceiling for non-combust planet = 0.85 (dignity_d1 + deeptaadi + baladi + varga).
        """
        score, _ = compute_condition_score_v1(
            dignity_score=1.0,
            deeptaadi="deepta",
            baladi="yuva",
            is_combust=False,
            is_deeply_combust=False,
            is_retrograde=False,
            varga_score=1.0,
        )
        assert score is not None
        assert score >= 0.80

    def test_debilitated_combust_scores_low(self):
        """Debilitated and deeply combust → score near bottom."""
        score, _ = compute_condition_score_v1(
            dignity_score=0.0,
            deeptaadi="khala",
            baladi="mrita",
            is_combust=True,
            is_deeply_combust=True,
            is_retrograde=False,
            varga_score=0.0,
        )
        assert score is not None
        assert score <= 0.1

    def test_breakdown_has_expected_keys(self):
        _, breakdown = compute_condition_score_v1(
            dignity_score=0.5,
            deeptaadi="shanta",
            baladi="kumara",
            is_combust=False,
            is_deeply_combust=False,
            is_retrograde=False,
            varga_score=None,
        )
        expected_keys = {
            "dignity_d1_score", "deeptaadi_state", "deeptaadi_score",
            "baladi_state", "baladi_score", "varga_score",
            "combustion_penalty", "is_retrograde", "raw_score",
            "clamped_score", "formula_version", "weights",
        }
        for k in expected_keys:
            assert k in breakdown, f"Missing key '{k}' in breakdown"

    def test_score_clamped_to_1(self):
        """Score must never exceed 1.0 even with all-maximum inputs."""
        score, _ = compute_condition_score_v1(
            dignity_score=1.0,
            deeptaadi="deepta",
            baladi="yuva",
            is_combust=False,
            is_deeply_combust=False,
            is_retrograde=False,
            varga_score=1.0,
        )
        assert score <= 1.0

    def test_score_clamped_to_0(self):
        """Score must never go below 0.0."""
        score, _ = compute_condition_score_v1(
            dignity_score=0.0,
            deeptaadi="vikala",
            baladi="mrita",
            is_combust=True,
            is_deeply_combust=True,
            is_retrograde=True,
            varga_score=0.0,
        )
        assert score >= 0.0

    def test_varga_fallback_used_flag(self):
        """When varga_score is None, varga_fallback_used should be True in breakdown."""
        _, breakdown = compute_condition_score_v1(
            dignity_score=0.6,
            deeptaadi="shanta",
            baladi="kumara",
            is_combust=False,
            is_deeply_combust=False,
            is_retrograde=False,
            varga_score=None,
        )
        assert breakdown.get("varga_fallback_used") is True


# ── 8. compute_panchadha_maitri ───────────────────────────────────────────────

class TestPanchadhaMaitri:

    @pytest.mark.parametrize("naisargika,tatkalika,expected", [
        ("friend",  "friend", "great_friend"),
        ("friend",  "enemy",  "neutral"),
        ("neutral", "friend", "friend"),
        ("neutral", "enemy",  "enemy"),
        ("enemy",   "friend", "neutral"),
        ("enemy",   "enemy",  "great_enemy"),
    ])
    def test_all_combinations(self, naisargika, tatkalika, expected):
        result = compute_panchadha_maitri(naisargika, tatkalika)
        assert result == expected, (
            f"panchadha({naisargika!r}, {tatkalika!r}) → expected '{expected}', got '{result}'"
        )


# ── 9. DIGNITY_SCORES constant ────────────────────────────────────────────────

def test_dignity_scores_range():
    """All DIGNITY_SCORES values must be in [0.0, 1.0]."""
    for label, score in DIGNITY_SCORES.items():
        assert 0.0 <= score <= 1.0, f"DIGNITY_SCORES['{label}'] = {score} out of range"


def test_dignity_scores_ordering():
    """Exalted must be highest; debilitated must be lowest."""
    assert DIGNITY_SCORES["exalted"]    == 1.0
    assert DIGNITY_SCORES["debilitated"] == 0.0
    assert DIGNITY_SCORES["own"]        > DIGNITY_SCORES["friend_sign"]
    assert DIGNITY_SCORES["friend_sign"] > DIGNITY_SCORES["neutral_sign"]
    assert DIGNITY_SCORES["neutral_sign"] > DIGNITY_SCORES["enemy_sign"]


# ── 10. compute_tatkalika_relation ────────────────────────────────────────────

class TestTatkalikaRelation:

    def test_2nd_from_is_friend(self):
        # Reference in house 1; planet in house 2 → offset 1 → friend
        assert compute_tatkalika_relation(planet_house=2, reference_planet_house=1) == "friend"

    def test_5th_from_is_enemy(self):
        # Offset 4 → enemy
        assert compute_tatkalika_relation(planet_house=5, reference_planet_house=1) == "enemy"

    def test_7th_from_is_enemy(self):
        # Offset 6 → enemy
        assert compute_tatkalika_relation(planet_house=7, reference_planet_house=1) == "enemy"

    def test_12th_from_is_friend(self):
        # Reference in house 1; planet in house 12 → offset 11 → friend
        assert compute_tatkalika_relation(planet_house=12, reference_planet_house=1) == "friend"

    def test_same_house_is_enemy(self):
        # Offset 0 → not in friend offsets → enemy
        assert compute_tatkalika_relation(planet_house=5, reference_planet_house=5) == "enemy"


# ── 11. dry_run guard ─────────────────────────────────────────────────────────

def test_run_substep_dry_run_returns_zero_rows():
    """ctx.dry_run=True must return 0 rows and make no DB calls."""
    from pipeline.orchestrator.writers.ga_condition import GaConditionWriter
    from pipeline.orchestrator.writers import SubStep, ContextSpec
    from unittest.mock import MagicMock

    writer = GaConditionWriter()
    ctx = MagicMock(spec=ContextSpec)
    ctx.config = {"chart_id": "482012f1-710e-4a25-994a-93821f5871aa"}
    ctx.build_id = "test-dry-build"
    ctx.dry_run = True
    ctx.db_conn = MagicMock()

    step = SubStep(key="ayanamsha_lahiri_chitrapaksha", label="test")
    result = writer.run_substep(ctx, step)

    assert result.rows_inserted == 0, f"dry_run must return 0 rows, got {result.rows_inserted}"
    ctx.db_conn.cursor.assert_not_called()


# ── 12. _load_dasha_periods peak/weak symmetry (BA Phase 2.5 fast-follow #2) ──
#
# weak_dasha_periods was previously an unconditional stub (always None) while
# peak_dasha_periods was populated. Fixed to mirror the same classical
# condition-score criterion (see migrations/251_ga_condition_composite.sql:
# peak = "high-condition periods", weak = "low-condition periods").

class _FakeDashaCursor:
    """Minimal fake cursor: returns 3 canned mahadasha rows for any chart/graha."""

    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a, **k):
        pass

    def fetchall(self):
        return self._rows


class _FakeDashaConn:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self, *a, **k):
        return _FakeDashaCursor(self._rows)


def _make_dasha_rows():
    from datetime import datetime, timezone
    return [
        (
            "vimshottari", 1, "Saturn",
            datetime(2000, 1, 1, tzinfo=timezone.utc),
            datetime(2019, 1, 1, tzinfo=timezone.utc),
        ),
    ]


class TestLoadDashaPeriodsSymmetry:

    def test_strong_condition_score_populates_peak_only(self):
        """condition_score >= 0.65 (classically strong) → peak populated, weak None."""
        from ga_writers.ga_condition_writer import (
            _load_dasha_periods, _PEAK_CONDITION_THRESHOLD,
        )

        conn = _FakeDashaConn(_make_dasha_rows())
        peak, weak = _load_dasha_periods(
            conn, "482012f1-710e-4a25-994a-93821f5871aa", "Saturn",
            condition_score=_PEAK_CONDITION_THRESHOLD,
            dignity_d1="exalted",
        )

        assert weak is None
        assert peak is not None and len(peak) == 1
        assert peak[0]["dasha_label"] == "Saturn Mahadasha"
        assert "strong" in peak[0]["reason"]

    def test_weak_condition_score_populates_weak_only(self):
        """condition_score <= 0.35 (classically weak — e.g. debilitated/combust)
        → weak_dasha_periods is populated, mirroring peak's logic exactly with
        the inverted threshold. This is the bug fix: weak must NOT be an
        unconditional None stub."""
        from ga_writers.ga_condition_writer import (
            _load_dasha_periods, _WEAK_CONDITION_THRESHOLD,
        )

        conn = _FakeDashaConn(_make_dasha_rows())
        peak, weak = _load_dasha_periods(
            conn, "482012f1-710e-4a25-994a-93821f5871aa", "Saturn",
            condition_score=_WEAK_CONDITION_THRESHOLD,
            dignity_d1="debilitated",
        )

        assert peak is None
        assert weak is not None and len(weak) == 1
        assert weak[0]["dasha_label"] == "Saturn Mahadasha"
        assert "weak" in weak[0]["reason"]
        assert "debilitated" in weak[0]["reason"]

    def test_neutral_condition_score_yields_neither(self):
        """Mid-band condition_score (neither classically strong nor weak) must
        return (None, None) — a genuine no-signal case, not a stub."""
        from ga_writers.ga_condition_writer import _load_dasha_periods

        conn = _FakeDashaConn(_make_dasha_rows())
        peak, weak = _load_dasha_periods(
            conn, "482012f1-710e-4a25-994a-93821f5871aa", "Saturn",
            condition_score=0.5,
            dignity_d1="neutral_sign",
        )

        assert peak is None
        assert weak is None

    def test_no_condition_score_yields_neither(self):
        """When condition_score is unavailable (None), cannot classify → both None,
        even though chart_dashas rows exist."""
        from ga_writers.ga_condition_writer import _load_dasha_periods

        conn = _FakeDashaConn(_make_dasha_rows())
        peak, weak = _load_dasha_periods(
            conn, "482012f1-710e-4a25-994a-93821f5871aa", "Saturn",
            condition_score=None,
        )

        assert peak is None
        assert weak is None

    def test_no_chart_dashas_rows_yields_neither(self):
        """No mahadasha rows at all → (None, None) regardless of condition_score."""
        from ga_writers.ga_condition_writer import _load_dasha_periods

        conn = _FakeDashaConn([])
        peak, weak = _load_dasha_periods(
            conn, "482012f1-710e-4a25-994a-93821f5871aa", "Saturn",
            condition_score=0.9,
        )

        assert peak is None
        assert weak is None
