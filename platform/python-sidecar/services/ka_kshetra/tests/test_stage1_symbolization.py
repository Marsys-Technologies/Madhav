"""Tests for services.ka_kshetra.stage1_symbolization.

Offline tier only (no DB / no swisseph needed) — the envelope contract and
every primitive builder are pure functions of already-computed stage-0
outputs / already-fetched reference rows.
"""
from __future__ import annotations

import datetime

import pytest

from services.ka_kshetra.stage0_kinematics import ContactEpisode
from services.ka_kshetra.stage1_symbolization import (
    CoverageGap,
    EnvelopeContractViolation,
    PrimitiveRow,
    av_kaksha_gate_coverage,
    build_contact_primitive_with_dwell,
    build_moorti_primitive,
    build_panchanga_limb_primitive,
    build_sandhi_band_primitives,
    build_station_band_primitive,
    build_syzygy_band_primitive,
    build_vedha_primitive,
    envelope_value_at,
    latta_coverage,
    row_to_params,
    validate_envelope,
    write_primitive_rows,
)


# ── Envelope contract ──────────────────────────────────────────────────────────

class TestValidateEnvelope:
    def test_rejects_fewer_than_two_knots(self):
        with pytest.raises(EnvelopeContractViolation):
            validate_envelope([(0.0, 0.0)])

    def test_rejects_v_outside_unit_interval(self):
        with pytest.raises(EnvelopeContractViolation):
            validate_envelope([(0.0, 0.0), (1.0, 1.5)])
        with pytest.raises(EnvelopeContractViolation):
            validate_envelope([(0.0, -0.1), (1.0, 1.0)])

    def test_rejects_non_ascending_t(self):
        with pytest.raises(EnvelopeContractViolation):
            validate_envelope([(1.0, 0.0), (0.0, 1.0)])

    def test_allows_one_coincident_pair(self):
        # Box/step: (0,0),(0,1),(1,1),(1,0) — two coincident pairs total.
        validate_envelope([(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)])

    def test_rejects_three_repeats_of_same_t(self):
        with pytest.raises(EnvelopeContractViolation):
            validate_envelope([(0.0, 0.0), (0.0, 0.5), (0.0, 1.0), (1.0, 0.0)])

    def test_rejects_backwards_after_coincident_pair(self):
        with pytest.raises(EnvelopeContractViolation):
            validate_envelope([(1.0, 0.0), (1.0, 1.0), (0.5, 0.5)])


class TestEnvelopeValueAt:
    def test_linear_interpolation(self):
        knots = [(0.0, 0.0), (10.0, 1.0)]
        assert envelope_value_at(knots, 5.0) == pytest.approx(0.5)

    def test_zero_outside_range(self):
        knots = [(0.0, 0.0), (10.0, 1.0)]
        assert envelope_value_at(knots, -5.0) == 0.0
        assert envelope_value_at(knots, 15.0) == 0.0

    def test_box_step_value(self):
        knots = [(0.0, 0.0), (0.0, 1.0), (10.0, 1.0), (10.0, 0.0)]
        assert envelope_value_at(knots, 5.0) == pytest.approx(1.0)
        assert envelope_value_at(knots, -1.0) == 0.0
        assert envelope_value_at(knots, 11.0) == 0.0


# ── PrimitiveRow validation ────────────────────────────────────────────────────

class TestPrimitiveRow:
    def test_rejects_bad_polarity(self):
        with pytest.raises(ValueError):
            PrimitiveRow(chart_id="c1", primitive_kind="vedha", subject="Saturn",
                         t_start=0.0, t_end=1.0, envelope=[(0.0, 0.0), (1.0, 1.0)],
                         polarity="bogus")

    def test_rejects_bad_source_kind(self):
        with pytest.raises(ValueError):
            PrimitiveRow(chart_id="c1", primitive_kind="vedha", subject="Saturn",
                         t_start=0.0, t_end=1.0, envelope=[(0.0, 0.0), (1.0, 1.0)],
                         polarity="neutral", source_kind="bogus")

    def test_valid_row_constructs(self):
        row = PrimitiveRow(chart_id="c1", primitive_kind="vedha", subject="Saturn",
                            t_start=0.0, t_end=1.0, envelope=[(0.0, 0.0), (1.0, 1.0)],
                            polarity="neutral")
        assert row.chart_id == "c1"


# ── Builders ────────────────────────────────────────────────────────────────────

class TestContactPrimitive:
    def test_moon_reference(self):
        ep = ContactEpisode(body="Jupiter", target_ref="Mo", t_in=10.0, t_out=20.0,
                             t_peak=15.0, orb_deg=3.0, orb_source="default_3deg",
                             ok_core_in=13.0, ok_core_out=17.0)
        row = build_contact_primitive_with_dwell(ep, "c1", "Mo", w_dwell=0.6)
        assert row.primitive_kind == "contact_moon_ref"
        assert row.t_start == 10.0 and row.t_end == 20.0
        assert envelope_value_at(row.envelope, 15.0) == pytest.approx(0.6)
        assert envelope_value_at(row.envelope, 5.0) == 0.0

    def test_lagna_reference(self):
        ep = ContactEpisode(body="Jupiter", target_ref="Lagna", t_in=10.0, t_out=20.0,
                             t_peak=15.0, orb_deg=3.0, orb_source="default_3deg")
        row = build_contact_primitive_with_dwell(ep, "c1", "Lagna", w_dwell=0.4)
        assert row.primitive_kind == "contact_lagna_ref"

    def test_unknown_reference_raises(self):
        ep = ContactEpisode(body="Jupiter", target_ref="Ma", t_in=10.0, t_out=20.0,
                             t_peak=15.0, orb_deg=3.0, orb_source="default_3deg")
        with pytest.raises(ValueError):
            build_contact_primitive_with_dwell(ep, "c1", "Ma", w_dwell=0.5)

    def test_grazing_episode_no_core_gives_triangle(self):
        ep = ContactEpisode(body="Jupiter", target_ref="Mo", t_in=10.0, t_out=20.0,
                             t_peak=15.0, orb_deg=3.0, orb_source="default_3deg",
                             ok_core_in=None, ok_core_out=None)
        row = build_contact_primitive_with_dwell(ep, "c1", "Mo", w_dwell=0.6)
        assert len(row.envelope) == 3
        assert row.envelope[1] == (15.0, 0.6)


class TestStationBandPrimitive:
    def test_symmetric_band_scales_with_dwell(self):
        low = build_station_band_primitive("c1", "Saturn", 100.0, w_dwell=0.0)
        high = build_station_band_primitive("c1", "Saturn", 100.0, w_dwell=1.0)
        low_width = low.t_end - low.t_start
        high_width = high.t_end - high.t_start
        assert high_width > low_width
        assert envelope_value_at(low.envelope, 100.0) == pytest.approx(1.0)


class TestSyzygyBandPrimitive:
    def test_exact_1_5_day_half_width(self):
        row = build_syzygy_band_primitive("c1", "Moon", 200.0, "new", False)
        assert row.t_start == pytest.approx(198.5)
        assert row.t_end == pytest.approx(201.5)

    def test_eclipse_candidate_carried_as_class_label(self):
        row = build_syzygy_band_primitive("c1", "Moon", 200.0, "full", True)
        assert row.class_label == "eclipse_candidate"

    def test_non_eclipse_carries_syzygy_kind(self):
        row = build_syzygy_band_primitive("c1", "Moon", 200.0, "new", False)
        assert row.class_label == "new"


class TestMoortiPrimitive:
    def test_svarna_tier1_is_supportive_and_full_strength(self):
        row = build_moorti_primitive("c1", "Jupiter", 50.0, 80.0, "swarna", 1)
        assert row.polarity == "supportive"
        assert envelope_value_at(row.envelope, 60.0) == pytest.approx(1.0)
        assert row.source_table == "bg_transit_moorti"

    def test_loha_tier4_is_obstructive_and_low_strength(self):
        row = build_moorti_primitive("c1", "Saturn", 50.0, 80.0, "loha", 4)
        assert row.polarity == "obstructive"
        assert envelope_value_at(row.envelope, 60.0) == pytest.approx(0.25)

    def test_box_shape_is_zero_outside_ingress_span(self):
        row = build_moorti_primitive("c1", "Jupiter", 50.0, 80.0, "swarna", 1)
        assert envelope_value_at(row.envelope, 40.0) == 0.0
        assert envelope_value_at(row.envelope, 90.0) == 0.0


class TestVedhaPrimitive:
    def test_is_obstructive_box(self):
        row = build_vedha_primitive("c1", "Saturn", 10.0, 20.0, vedha_house=5,
                                     phala="obstructs 11H gains")
        assert row.polarity == "obstructive"
        assert row.object_ref == "house_5"
        assert row.source_table == "bg_transit_rules"
        assert envelope_value_at(row.envelope, 15.0) == pytest.approx(1.0)


class TestPanchangaLimbPrimitive:
    def test_references_panchanga_daily(self):
        row = build_panchanga_limb_primitive(
            "c1", "tithi", 0.0, 1.0, limb_value_id=3, limb_value_name="Tritiya",
            source_row_date=datetime.date(2024, 1, 1),
        )
        assert row.source_kind == "l1_fact"
        assert row.source_table == "panchanga_daily"
        assert row.class_label == "Tritiya"

    def test_rejects_unknown_limb(self):
        with pytest.raises(ValueError):
            build_panchanga_limb_primitive("c1", "bogus_limb", 0.0, 1.0, 1, "x",
                                            datetime.date(2024, 1, 1))


class TestSandhiBandFallback:
    def test_honest_not_computed_when_lane_b_absent(self):
        rows, gap = build_sandhi_band_primitives("c1", conn=None)
        assert rows == []
        assert isinstance(gap, CoverageGap)
        assert gap.reason_code == "not_computed"
        assert gap.primitive_kind == "sandhi_band"

    def test_uses_injected_function_when_provided(self):
        rows, gap = build_sandhi_band_primitives(
            "c1", conn=None, boundary_breakpoints_fn=lambda chart_id, conn: [100.0, 200.0],
        )
        assert gap is None
        assert len(rows) == 2
        assert {r.t_end - r.t_start for r in rows} == {6.0}  # +-3.0 days


class TestHonestCoverageGaps:
    def test_av_kaksha_gate_is_not_in_corpus(self):
        gap = av_kaksha_gate_coverage()
        assert gap.reason_code == "not_in_corpus"
        assert gap.primitive_kind == "av_kaksha_gate"

    def test_latta_is_not_in_corpus(self):
        gap = latta_coverage()
        assert gap.reason_code == "not_in_corpus"
        assert gap.primitive_kind == "latta"


# ── DB write layer (fake connection, offline) ─────────────────────────────────

class _FakeConn:
    def __init__(self):
        self.executed: list[tuple[str, dict]] = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return self


class TestWritePrimitiveRows:
    def test_upserts_each_row_once(self):
        row1 = build_vedha_primitive("c1", "Saturn", 10.0, 20.0, 5, "x")
        row2 = build_moorti_primitive("c1", "Jupiter", 50.0, 80.0, "swarna", 1)
        conn = _FakeConn()
        n = write_primitive_rows(conn, [row1, row2])
        assert n == 2
        assert len(conn.executed) == 2

    def test_row_to_params_serializes_envelope_as_json(self):
        row = build_vedha_primitive("c1", "Saturn", 10.0, 20.0, 5, "x")
        params = row_to_params(row)
        assert isinstance(params["envelope"], str)
        assert '"t"' in params["envelope"] and '"v"' in params["envelope"]
