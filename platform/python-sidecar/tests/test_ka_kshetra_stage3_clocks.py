"""
tests/test_ka_kshetra_stage3_clocks.py — Lane B (ṢAḌ-DARŚANA W2), Stage 3:
Law-1 applicability (item 12) + the clock/boundary writers + published
functions.

No live DB required (mirrors tests/test_ka_gochara_sweep.py's documented
pattern): pure functions are tested directly; DB-facing functions are
tested against `_FakeConn`, a small in-memory fake that dispatches on
substrings of the issued SQL (same technique as
tests/test_ka_sangam_resumption.py's fakes for chart_dashas-shaped
queries).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from services.ka_kshetra import stage3_clocks as SC
from services.ka_kshetra import uncertainty as U

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


# ── pure helpers ─────────────────────────────────────────────────────────────

class TestDistanceToGridBoundary:
    def test_midpoint(self):
        assert SC._distance_to_grid_boundary(6.6665, 13.333) == pytest.approx(6.6665, rel=1e-3)

    def test_near_lower_boundary(self):
        assert SC._distance_to_grid_boundary(0.2, U.NAK_SPAN_DEG) == pytest.approx(0.2)

    def test_near_upper_boundary(self):
        d = SC._distance_to_grid_boundary(U.NAK_SPAN_DEG - 0.1, U.NAK_SPAN_DEG)
        assert d == pytest.approx(0.1, abs=1e-9)


class TestMoonQualityNakshatra:
    def test_far_from_boundary_is_full_quality(self):
        # exact nakshatra midpoint -> d_nak = NAK_SPAN/2, way over 0.5deg cap -> q=1
        d_nak, q = SC.moon_quality_nakshatra(U.NAK_SPAN_DEG / 2.0)
        assert d_nak == pytest.approx(U.NAK_SPAN_DEG / 2.0)
        assert q == 1.0

    def test_at_boundary_is_zero_quality(self):
        d_nak, q = SC.moon_quality_nakshatra(0.0)
        assert d_nak == pytest.approx(0.0, abs=1e-9)
        assert q == pytest.approx(0.0)

    def test_partial_margin(self):
        # 0.25deg from a boundary, cap is 0.50 -> q = 0.5
        d_nak, q = SC.moon_quality_nakshatra(0.25)
        assert d_nak == pytest.approx(0.25)
        assert q == pytest.approx(0.5)


class TestMoonQualityPada:
    def test_partial_margin(self):
        d_pada, q = SC.moon_quality_pada(0.125)
        assert d_pada == pytest.approx(0.125)
        assert q == pytest.approx(0.5)


class TestCharaQuality:
    def test_requires_at_least_one_candidate(self):
        with pytest.raises(ValueError):
            SC.chara_quality({})

    def test_min_across_candidates(self):
        degrees = {"Sun": 15.0, "Moon": 0.5, "Mars": 29.6, "Saturn": 10.0}
        d_sign, q = SC.chara_quality(degrees)
        # Moon: min(0.5, 29.5) = 0.5 ; Mars: min(29.6, 0.4) = 0.4 -> overall min = 0.4
        assert d_sign == pytest.approx(0.4)
        assert q == pytest.approx(0.4)  # cap 1.00deg

    def test_ignores_non_candidate_grahas(self):
        degrees = {"Rahu": 0.01, "Sun": 15.0}
        d_sign, q = SC.chara_quality(degrees)
        assert d_sign == pytest.approx(15.0)
        assert q == 1.0


# ── fake DB conn ─────────────────────────────────────────────────────────────

class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _FakeConn:
    """Dispatches canned result sets by matching substrings of the issued
    SQL, in registration order. Records every (sql, params) call for
    idempotency/scoping assertions."""

    def __init__(self):
        self._rules: list[tuple[str, list]] = []
        self.calls: list[tuple[str, list]] = []

    def when(self, substring: str, rows: list):
        self._rules.append((substring, rows))
        return self

    def execute(self, sql, params=None):
        self.calls.append((sql, params or []))
        for substring, rows in self._rules:
            if substring in sql:
                return _FakeCursor(rows)
        return _FakeCursor([])


# ── evaluate_applicability / applicable_systems ─────────────────────────────

class TestEvaluateApplicability:
    def test_unknown_system_raises(self):
        conn = _FakeConn()
        with pytest.raises(ValueError):
            SC.evaluate_applicability(CHART_ID, "not_a_real_system", conn)

    def test_no_chart_dashas_rows_is_not_computed(self):
        conn = _FakeConn().when("SELECT COUNT(*)", [{"n": 0}])
        result = SC.evaluate_applicability(CHART_ID, "vimshottari", conn)
        assert result.applicability_state == "not_computed"
        assert result.exclusion_reason == "no chart_dashas rows for system"
        assert result.competence_class == "fruition"
        assert result.seniority_rank == 1
        assert result.quality is None

    def test_ashtottari_is_not_computed_no_quality_rule(self):
        conn = _FakeConn().when("SELECT COUNT(*)", [{"n": 12}])
        result = SC.evaluate_applicability(CHART_ID, "ashtottari", conn)
        assert result.applicability_state == "not_computed"
        assert result.exclusion_reason == "no quality rule defined"
        assert result.is_predictive is True

    def test_naisargika_is_applicable_with_quality_one(self):
        conn = _FakeConn().when("SELECT COUNT(*)", [{"n": 9}])
        result = SC.evaluate_applicability(CHART_ID, "naisargika", conn)
        assert result.applicability_state == "applicable"
        assert result.quality == 1.0
        assert result.competence_class == "life_stage"
        assert result.is_predictive is False

    def test_vimshottari_applicable_with_moon_margin(self):
        conn = (
            _FakeConn()
            .when("SELECT COUNT(*)", [{"n": 45}])
            .when("longitude_sidereal", [{"fact_value_num": 0.25}])
        )
        result = SC.evaluate_applicability(CHART_ID, "vimshottari", conn)
        assert result.applicability_state == "applicable"
        assert result.quality == pytest.approx(0.5)
        assert "moon_nakshatra_margin" in result.quality_basis

    def test_mudda_quality_one_when_covering_row_exists(self):
        conn = _FakeConn().when("SELECT COUNT(*)", [{"n": 30}]).when("LIMIT 1", [1])
        result = SC.evaluate_applicability(CHART_ID, "mudda", conn)
        assert result.applicability_state == "applicable"
        assert result.quality == 1.0

    def test_mudda_quality_zero_when_no_covering_row(self):
        conn = _FakeConn().when("SELECT COUNT(*)", [{"n": 30}])  # no LIMIT-1 rule -> empty
        result = SC.evaluate_applicability(CHART_ID, "mudda", conn)
        assert result.applicability_state == "applicable"
        assert result.quality == 0.0

    def test_chara_karaka_applicable(self):
        conn = (
            _FakeConn()
            .when("SELECT COUNT(*)", [{"n": 20}])
            .when("graha_sign_attributes", [
                {"fact_subject": "SUN", "fact_value_num": 15.0},
                {"fact_subject": "MOON", "fact_value_num": 2.0},
            ])
        )
        result = SC.evaluate_applicability(CHART_ID, "chara_karaka", conn)
        assert result.applicability_state == "applicable"
        assert result.quality == pytest.approx(1.0)  # min(2.0,28.0)=2.0 -> clamp01(2/1)=1.0


class TestApplicableSystems:
    def test_returns_every_registered_system_sorted(self):
        conn = _FakeConn().when("SELECT COUNT(*)", [{"n": 0}])
        results = SC.applicable_systems(CHART_ID, conn)
        assert [r.system_id for r in results] == sorted(SC.SYSTEM_META.keys())
        # 7 classical systems + vimshottari_kp (W3K G-4)
        assert len(results) == 8
        assert SC.KP_SYSTEM_ID in {r.system_id for r in results}


# ── W3K G-4: vimshottari_kp ─────────────────────────────────────────────────
#
# `_FakeConn` dispatches on SQL substrings, so the KP redundancy probe is keyed
# on "AS has_twin" and the L0 boundary read on "bg_kp_sublord_division".

BIRTH_DT = datetime(1984, 2, 5, 5, 13, tzinfo=timezone.utc)  # 10:43 IST


def _kp_conn(*, twin_rows, boundaries=None, moon_lon=None, ayanamsha_lons=None, count=5760):
    conn = _FakeConn().when("SELECT COUNT(*)", [{"n": count}]).when("AS has_twin", twin_rows)
    if boundaries is not None:
        conn.when("bg_kp_sublord_division", [{"start_longitude_deg": b} for b in boundaries])
    if ayanamsha_lons is not None:
        conn.when("ayanamsha_id = ANY", [
            {"ayanamsha_id": a, "fact_value_num": v} for a, v in ayanamsha_lons.items()
        ])
    if moon_lon is not None:
        conn.when("longitude_sidereal", [{"fact_value_num": moon_lon}])
    return conn


class TestKpWindowRedundancy:
    def test_all_rows_twinned_is_redundant(self):
        rows = [{"level_n": 2, "has_twin": True}] * 3 + [{"level_n": 3, "has_twin": True}] * 5
        r = SC.kp_window_redundancy(CHART_ID, _kp_conn(twin_rows=rows), birth_dt=BIRTH_DT)
        assert r.rows_in_horizon == 8
        assert r.twinned_rows == 8
        assert r.untwinned_rows == 0
        assert r.is_redundant is True
        assert r.levels_compared == (2, 3)
        assert "twinned=8/8" in r.basis()

    def test_one_untwinned_row_defeats_redundancy(self):
        """The detector can genuinely come back False (§N.8) — a single instant at
        which the two ladders' lords differ is enough for KP to carry information."""
        rows = [{"level_n": 2, "has_twin": True}] * 7 + [{"level_n": 2, "has_twin": False}]
        r = SC.kp_window_redundancy(CHART_ID, _kp_conn(twin_rows=rows), birth_dt=BIRTH_DT)
        assert r.untwinned_rows == 1
        assert r.is_redundant is False

    def test_zero_in_horizon_rows_is_absence_not_redundancy(self):
        r = SC.kp_window_redundancy(CHART_ID, _kp_conn(twin_rows=[]), birth_dt=BIRTH_DT)
        assert r.rows_in_horizon == 0
        assert r.is_redundant is False

    def test_horizon_is_36525_days_from_birth(self):
        r = SC.kp_window_redundancy(CHART_ID, _kp_conn(twin_rows=[]), birth_dt=BIRTH_DT)
        assert r.horizon_start == BIRTH_DT
        assert (r.horizon_end - r.horizon_start).days == 36525

    def test_query_is_scoped_to_the_horizon_and_the_parent_system(self):
        conn = _kp_conn(twin_rows=[])
        SC.kp_window_redundancy(CHART_ID, conn, birth_dt=BIRTH_DT)
        sql, params = conn.calls[0]
        assert "bg_kp_sublord" not in sql
        assert params[0] == SC.KP_PARENT_SYSTEM_ID
        assert params[3] == CHART_ID
        assert params[5] == SC.KP_SYSTEM_ID
        assert params[6] == BIRTH_DT


class TestKpJurisdiction:
    def test_redundant_kp_is_excluded_by_condition(self):
        rows = [{"level_n": 2, "has_twin": True}] * 4
        result = SC.evaluate_applicability(
            CHART_ID, SC.KP_SYSTEM_ID, _kp_conn(twin_rows=rows), birth_dt=BIRTH_DT,
        )
        assert result.applicability_state == "excluded_by_condition"
        assert result.quality is None
        assert "boundary-identical to vimshottari" in result.exclusion_reason
        assert "twinned=4/4" in result.exclusion_reason

    def test_missing_birth_dt_is_not_computed_never_applicable(self):
        """§N.8: no detector ran, so there is no verdict — and the honest state is
        `not_computed`, not a silent admission to S_pred(e)."""
        result = SC.evaluate_applicability(
            CHART_ID, SC.KP_SYSTEM_ID, _kp_conn(twin_rows=[{"level_n": 2, "has_twin": True}]),
        )
        assert result.applicability_state == "not_computed"
        assert "undecidable without the chart's birth instant" in result.exclusion_reason

    def test_shares_vimshottaris_competence_class(self):
        """One clock, one voice — writer.py's §6.4 type-1 insight counts DISTINCT
        competence_classes, so a new class here would have manufactured a second
        voice out of the same clock."""
        assert (SC.SYSTEM_META[SC.KP_SYSTEM_ID].competence_class
                == SC.SYSTEM_META["vimshottari"].competence_class == "fruition")

    def test_the_seven_classical_systems_keep_unconditional_jurisdiction(self):
        for sid in ("vimshottari", "yogini", "ashtottari", "chara_karaka",
                    "kalachakra", "mudda", "naisargika"):
            assert SC._evaluate_jurisdiction(sid) == ("applicable", None)


class TestKpSubQuality:
    BOUNDARIES = [0.0, 0.7777777777777778, 1.5555555555555556, 3.7777777777777777]

    def test_margin_beyond_the_ayanamsha_band_is_full_quality(self):
        d_sub, q = SC.kp_sub_quality(2.6666, self.BOUNDARIES, sigma_a_deg=0.05)
        assert d_sub == pytest.approx(1.1110, abs=1e-3)   # nearest boundary 1.5556
        assert q == 1.0

    def test_margin_inside_the_ayanamsha_band_is_partial(self):
        # 0.049deg from the 1.5556 boundary; band = 1.96 * 0.05 = 0.098deg
        d_sub, q = SC.kp_sub_quality(1.5556 - 0.049, self.BOUNDARIES, sigma_a_deg=0.05)
        assert d_sub == pytest.approx(0.049, abs=1e-4)
        assert q == pytest.approx(0.049 / (1.96 * 0.05), rel=1e-3)
        assert 0.0 < q < 1.0

    def test_on_a_boundary_is_zero_quality(self):
        _, q = SC.kp_sub_quality(1.5555555555555556, self.BOUNDARIES, sigma_a_deg=0.05)
        assert q == pytest.approx(0.0, abs=1e-9)

    def test_wraps_across_zero(self):
        d_sub, _ = SC.kp_sub_quality(359.9, self.BOUNDARIES, sigma_a_deg=0.05)
        assert d_sub == pytest.approx(0.1, abs=1e-9)

    def test_refuses_to_invent_a_value_without_the_l0_authority(self):
        with pytest.raises(ValueError):
            SC.kp_sub_quality(10.0, [], sigma_a_deg=0.05)

    def test_refuses_a_nonpositive_sigma_a(self):
        with pytest.raises(ValueError):
            SC.kp_sub_quality(10.0, self.BOUNDARIES, sigma_a_deg=0.0)

    def test_absent_l0_table_renders_as_not_computed_never_a_rederivation(self):
        """No `bg_kp_sublord_division` rows => the quality is unknown, and unknown
        is reported (§N.5: never fall back to re-deriving the L0 authority)."""
        conn = _kp_conn(twin_rows=[{"level_n": 2, "has_twin": False}], boundaries=None)
        result = SC.evaluate_applicability(
            CHART_ID, SC.KP_SYSTEM_ID, conn, birth_dt=BIRTH_DT,
        )
        assert result.applicability_state == "not_computed"
        assert result.exclusion_reason == "no quality rule defined"
        assert result.quality is None

    def test_non_redundant_kp_is_applicable_with_a_real_kp_quality(self):
        conn = _kp_conn(
            twin_rows=[{"level_n": 2, "has_twin": False}],
            boundaries=self.BOUNDARIES,
            ayanamsha_lons={"lahiri_chitrapaksha": 2.60, "krishnamurti": 2.70,
                            "raman": 2.65, "surya_siddhanta_classical": 2.62,
                            "true_chitra": 2.68},
            moon_lon=2.6666,
        )
        result = SC.evaluate_applicability(
            CHART_ID, SC.KP_SYSTEM_ID, conn, birth_dt=BIRTH_DT,
        )
        assert result.applicability_state == "applicable"
        assert result.quality is not None and 0.0 <= result.quality <= 1.0
        assert "kp_sub_margin=" in result.quality_basis
        assert "sigma_a=" in result.quality_basis
        assert result.is_predictive is True


class TestWriteClockRows:
    def test_empty_list_is_noop(self):
        conn = _FakeConn()
        assert SC.write_clock_rows(CHART_ID, [], conn) == 0
        assert conn.calls == []

    def test_deletes_then_inserts_scoped_to_chart_and_systems(self):
        conn = _FakeConn()
        applicabilities = [
            SC.ClockApplicability(
                system_id="vimshottari", applicability_state="applicable",
                exclusion_reason=None, competence_class="fruition", seniority_rank=1,
                quality=0.8, quality_basis="x", is_predictive=True,
            ),
            SC.ClockApplicability(
                system_id="naisargika", applicability_state="applicable",
                exclusion_reason=None, competence_class="life_stage", seniority_rank=7,
                quality=1.0, quality_basis="y", is_predictive=False,
            ),
        ]
        n = SC.write_clock_rows(CHART_ID, applicabilities, conn)
        assert n == 2
        delete_calls = [c for c in conn.calls if c[0].strip().startswith("DELETE")]
        insert_calls = [c for c in conn.calls if c[0].strip().startswith("INSERT")]
        assert len(delete_calls) == 1
        assert delete_calls[0][1] == [CHART_ID, ["vimshottari", "naisargika"]]
        assert len(insert_calls) == 2


# ── full_lord_period_days ────────────────────────────────────────────────────

class TestFullLordPeriodDays:
    def test_raises_when_no_matching_rows(self):
        conn = _FakeConn().when("FROM chart_dashas", [])
        with pytest.raises(RuntimeError):
            SC.full_lord_period_days(CHART_ID, "vimshottari", "Jupiter", conn)

    def test_single_occurrence_returns_its_own_duration(self):
        rows = [
            {"dasha_row_id": "r1", "lord_graha": "Jupiter", "lord_sign": None,
             "start_iso": datetime(2000, 1, 1, tzinfo=timezone.utc),
             "end_iso": datetime(2016, 1, 1, tzinfo=timezone.utc), "duration_days": 5000.0},
        ]
        conn = _FakeConn().when("FROM chart_dashas", rows)
        days, source = SC.full_lord_period_days(CHART_ID, "vimshottari", "Jupiter", conn)
        assert days == pytest.approx(5000.0)
        assert source == "single_occurrence_approx"

    def test_recurrence_takes_the_max_full_cycle(self):
        rows = [
            {"dasha_row_id": "r1", "lord_graha": "Jupiter", "lord_sign": None,
             "start_iso": datetime(1984, 2, 5, tzinfo=timezone.utc),
             "end_iso": datetime(1990, 1, 1, tzinfo=timezone.utc), "duration_days": 2000.0},  # truncated birth balance
            {"dasha_row_id": "r2", "lord_graha": "Jupiter", "lord_sign": None,
             "start_iso": datetime(2104, 2, 5, tzinfo=timezone.utc),
             "end_iso": datetime(2120, 2, 5, tzinfo=timezone.utc), "duration_days": 5844.0},  # full 16y cycle
        ]
        conn = _FakeConn().when("FROM chart_dashas", rows)
        days, source = SC.full_lord_period_days(CHART_ID, "vimshottari", "Jupiter", conn)
        assert days == pytest.approx(5844.0)
        assert source == "full_cycle_recurrence"

    def test_matches_by_lord_sign_for_sign_based_systems(self):
        rows = [
            {"dasha_row_id": "r1", "lord_graha": None, "lord_sign": "Aries",
             "start_iso": datetime(1984, 2, 5, tzinfo=timezone.utc),
             "end_iso": datetime(1990, 1, 1, tzinfo=timezone.utc), "duration_days": 400.0},
        ]
        conn = _FakeConn().when("FROM chart_dashas", rows)
        days, source = SC.full_lord_period_days(CHART_ID, "chara_karaka", "Aries", conn)
        assert days == pytest.approx(400.0)


# ── boundary_breakpoints ─────────────────────────────────────────────────────

class TestBoundaryBreakpoints:
    def test_ascending_and_excludes_unsupported(self):
        rows = [{"t_boundary": 100.0}, {"t_boundary": 50.0}]
        conn = _FakeConn().when("FROM kala_field_boundaries", rows)
        result = SC.boundary_breakpoints(CHART_ID, conn)
        # ordering comes from SQL ORDER BY in the real DB; the fake just
        # returns whatever rows it was given, so assert the SQL filters
        # precision_unsupported and the function converts to float list.
        assert result == [100.0, 50.0]
        sql = conn.calls[0][0]
        assert "precision_unsupported" in sql
        assert "ORDER BY t_boundary ASC" in sql


# ── J2000 conversion ─────────────────────────────────────────────────────────

class TestEpochConversion:
    def test_j2000_epoch_is_zero(self):
        assert SC.to_t_days(SC.J2000_EPOCH) == pytest.approx(0.0)

    def test_round_trip(self):
        dt = datetime(2024, 6, 15, 3, 30, tzinfo=timezone.utc)
        t = SC.to_t_days(dt)
        back = SC.from_t_days(t)
        assert back == dt

    def test_naive_datetime_treated_as_utc(self):
        dt_naive = datetime(2024, 6, 15, 3, 30)
        dt_aware = dt_naive.replace(tzinfo=timezone.utc)
        assert SC.to_t_days(dt_naive) == pytest.approx(SC.to_t_days(dt_aware))


# ── moon_velocity_dps_at_birth (real swisseph, no DB) ───────────────────────

class TestMoonVelocityAtBirth:
    def test_native_chart_velocity_is_physically_plausible(self):
        # Native: 1984-02-05 10:43 IST (UTC+5:30).
        birth_params = {"datetime_iso": "1984-02-05T10:43:00", "tz_offset_hours": 5.5}
        v = SC.moon_velocity_dps_at_birth(birth_params)
        # V0-1-style sanity bound (design doc's own validation range).
        assert 11.60 <= abs(v) <= 15.50

    def test_velocity_is_ayanamsha_invariant_matches_direct_jd_call(self):
        birth_params = {"datetime_iso": "1984-02-05T10:43:00", "tz_offset_hours": 5.5}
        v_from_birth = SC.moon_velocity_dps_at_birth(birth_params)

        import swisseph as swe
        utc_dt = datetime(1984, 2, 5, 10, 43, 0) - timedelta(hours=5.5)
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute / 60.0)
        v_direct = SC.moon_velocity_dps_at_jd(jd)
        assert v_from_birth == pytest.approx(v_direct, abs=1e-3)


# ── clock_activation ─────────────────────────────────────────────────────────

class TestClockActivation:
    def test_returns_one_when_no_clock_row(self):
        conn = _FakeConn()  # SELECT quality FROM kala_field_clocks returns []
        result = SC.clock_activation(CHART_ID, "vimshottari", "career_change", 0.0, conn)
        assert result == pytest.approx(1.0)

    def test_returns_one_when_quality_is_null(self):
        conn = _FakeConn().when("kala_field_clocks", [{"quality": None}])
        result = SC.clock_activation(CHART_ID, "ashtottari", "career_change", 0.0, conn)
        assert result == pytest.approx(1.0)

    def test_neutral_when_lord_stack_empty(self):
        conn = (
            _FakeConn()
            .when("kala_field_clocks", [{"quality": 0.8}])
            .when("FROM kala_field_boundaries", [])  # no supported levels
        )
        result = SC.clock_activation(CHART_ID, "vimshottari", "career_change", 0.0, conn)
        assert result == pytest.approx(1.0)

    def test_positive_route_gain_boosts_activation_above_one(self):
        conn = (
            _FakeConn()
            .when("kala_field_clocks", [{"quality": 0.8}])
            .when("FROM kala_field_boundaries", [{"level": "MD"}])
            .when("FROM chart_dashas", [{"lord_graha": "Jupiter", "lord_sign": None}])
            .when("kala_field_promise_routes", [{"route_gain": 0.7, "suppressed_by": []}])
        )
        result = SC.clock_activation(CHART_ID, "vimshottari", "career_change", 0.0, conn)
        assert result > 1.0

    def test_suppressed_route_pulls_activation_below_one(self):
        conn = (
            _FakeConn()
            .when("kala_field_clocks", [{"quality": 0.8}])
            .when("FROM kala_field_boundaries", [{"level": "MD"}])
            .when("FROM chart_dashas", [{"lord_graha": "Jupiter", "lord_sign": None}])
            .when("kala_field_promise_routes", [{"route_gain": 0.7, "suppressed_by": ["vedha:Sa->10"]}])
        )
        result = SC.clock_activation(CHART_ID, "vimshottari", "career_change", 0.0, conn)
        assert result < 1.0

    def test_chara_karaka_lord_sign_translated_to_ruling_graha(self):
        conn = (
            _FakeConn()
            .when("kala_field_clocks", [{"quality": 0.8}])
            .when("FROM kala_field_boundaries", [{"level": "MD"}])
            .when("FROM chart_dashas", [{"lord_graha": None, "lord_sign": "Aries"}])
            .when("kala_field_promise_routes", [{"route_gain": 0.5, "suppressed_by": []}])
        )
        result = SC.clock_activation(CHART_ID, "chara_karaka", "career_change", 0.0, conn)
        # Aries -> Mars; the route query must have been issued with graha:Mars
        route_calls = [c for c in conn.calls if "kala_field_promise_routes" in c[0]]
        assert route_calls[0][1][2] == "graha:Mars"
        assert result > 1.0


class TestLordToGraha:
    def test_sign_translates_to_ruler(self):
        assert SC._lord_to_graha("Capricorn") == "Saturn"

    def test_graha_passes_through(self):
        assert SC._lord_to_graha("Mercury") == "Mercury"


# ── lord_stack_at ────────────────────────────────────────────────────────────

class TestLordStackAt:
    def test_empty_when_no_levels_supported(self):
        conn = _FakeConn().when("FROM kala_field_boundaries", [])
        stack = SC.lord_stack_at(CHART_ID, "vimshottari", 0.0, conn)
        assert stack == {}

    def test_populates_supported_levels_only(self):
        conn = (
            _FakeConn()
            .when("FROM kala_field_boundaries", [{"level": "MD"}, {"level": "AD"}])
            .when("FROM chart_dashas", [{"lord_graha": "Jupiter", "lord_sign": None}])
        )
        stack = SC.lord_stack_at(CHART_ID, "vimshottari", 0.0, conn)
        assert set(stack.keys()) == {"MD", "AD"}
        assert stack["MD"] == "Jupiter"

    def test_missing_covering_row_is_skipped_honestly(self):
        conn = (
            _FakeConn()
            .when("FROM kala_field_boundaries", [{"level": "MD"}])
            # no "FROM chart_dashas" rule registered -> fetchone() returns None
        )
        stack = SC.lord_stack_at(CHART_ID, "vimshottari", 999999.0, conn)
        assert stack == {}


# ── compute_boundaries_for_system / write_boundary_rows ─────────────────────

class TestComputeBoundariesForSystem:
    BIRTH_PARAMS = {"datetime_iso": "1984-02-05T10:43:00", "tz_offset_hours": 5.5}

    def test_naisargika_uses_birth_time_only_sigma(self):
        # naisargika is in BIRTH_TIME_ONLY_SYSTEMS, so no chart_facts /
        # full_lord_period_days lookups should be needed.
        rows = [
            {
                "dasha_row_id": "row-md-1", "level_n": 1, "lord_graha": "Sun", "lord_sign": None,
                "parent_row_id": None,
                "start_iso": SC.J2000_EPOCH, "duration_days": 36525.0,
            },
        ]
        conn = (
            _FakeConn()
            .when("phala_rectification", [])  # -> default sigma_T
            .when("FROM chart_dashas", rows)
        )
        result = SC.compute_boundaries_for_system(
            CHART_ID, "naisargika", conn, birth_params=self.BIRTH_PARAMS
        )
        assert len(result) == 1
        row = result[0]
        assert row.level == "MD"
        assert row.lord == "Sun"
        assert row.sigma_t_days == pytest.approx(U.DEFAULT_SIGMA_T_DAYS)
        assert row.dominant_uncertainty_source == "birth_time"
        # width = 2*1.96*sigma_T (~0.0027 days) is tiny vs a 100-year period -> instant
        assert row.precision_state == "instant"
        assert row.source_pk == "row-md-1"

    def test_precision_unsupported_for_a_very_short_period_with_large_sigma(self):
        rows = [
            {
                "dasha_row_id": "row-sd-1", "level_n": 4, "lord_graha": "Mercury", "lord_sign": None,
                "parent_row_id": None,
                "start_iso": SC.J2000_EPOCH, "duration_days": 0.0005,  # ~43 seconds
            },
        ]
        conn = (
            _FakeConn()
            .when("phala_rectification", [])
            .when("FROM chart_dashas", rows)
        )
        result = SC.compute_boundaries_for_system(
            CHART_ID, "mudda", conn, birth_params=self.BIRTH_PARAMS
        )
        assert result[0].precision_state == "precision_unsupported"

    def test_ancestor_lords_chain_outermost_first(self):
        rows = [
            {
                "dasha_row_id": "md-1", "level_n": 1, "lord_graha": "Jupiter", "lord_sign": None,
                "parent_row_id": None,
                "start_iso": SC.J2000_EPOCH, "duration_days": 5844.0,
            },
            {
                "dasha_row_id": "ad-1", "level_n": 2, "lord_graha": "Saturn", "lord_sign": None,
                "parent_row_id": "md-1",
                "start_iso": SC.J2000_EPOCH, "duration_days": 900.0,
            },
            {
                "dasha_row_id": "pd-1", "level_n": 3, "lord_graha": "Mercury", "lord_sign": None,
                "parent_row_id": "ad-1",
                "start_iso": SC.J2000_EPOCH, "duration_days": 60.0,
            },
        ]
        conn = (
            _FakeConn()
            .when("phala_rectification", [])
            .when("FROM chart_dashas", rows)
        )
        result = SC.compute_boundaries_for_system(
            CHART_ID, "naisargika", conn, birth_params=self.BIRTH_PARAMS
        )
        pd_row = next(r for r in result if r.level == "PD")
        assert pd_row.parent_lords == ["Jupiter", "Saturn"]


class TestWriteBoundaryRows:
    def test_empty_list_still_deletes_scope(self):
        conn = _FakeConn()
        n = SC.write_boundary_rows(CHART_ID, "vimshottari", [], conn)
        assert n == 0
        assert len(conn.calls) == 1
        assert conn.calls[0][0].strip().startswith("DELETE")
        assert conn.calls[0][1] == [CHART_ID, "vimshottari"]

    def test_writes_one_insert_per_row(self):
        conn = _FakeConn()
        rows = [
            SC.BoundaryRow(
                system_id="vimshottari", level="MD", lord="Jupiter", parent_lords=[],
                t_boundary=0.0, period_days=5844.0, sigma_t_days=0.01,
                interval_lo=-0.02, interval_hi=0.02, precision_state="instant",
                dominant_uncertainty_source="birth_time", sigma_t_source="default_120s_assumption",
                source_pk="row-1",
            ),
        ]
        n = SC.write_boundary_rows(CHART_ID, "vimshottari", rows, conn)
        assert n == 1
        insert_calls = [c for c in conn.calls if c[0].strip().startswith("INSERT")]
        assert len(insert_calls) == 1
