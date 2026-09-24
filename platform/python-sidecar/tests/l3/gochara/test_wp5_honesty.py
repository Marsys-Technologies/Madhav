"""
Test WP5 honesty escalations (H-1a, H-2, H-3, H-4/H-5/H-6).

These tests exercise the gochara_v3 pipeline's honest failure-state and
physical-event-identity machinery without a DB or ephemeris.

Note on provenance: this file was first written in a different checkout
(by mistake, during interactive execution) before being reconciled onto
this branch. The H-4/H-5/H-6 identity test below was rewritten during that
reconciliation to exercise the pinned `services.gochara_kernel.ids`
contract via `_sentence_identity` (WP1_CONTRACTS.md §3.2), rather than the
non-canonical single-argument `contact_id(sentence)` /
`independence_group(sentence)` calls the original draft used, which do not
match the kernel's real keyword-argument signature and would have produced
ids disagreeing with the WP6 ledger's. H-1a/H-2/H-3 below are otherwise
unchanged from that draft; they were re-verified against this worktree's
actual `context.py`/`interval_solver.py`/`resolution_hierarchy.py` content.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from services.gochara_grammar.models import ConfigurationSentence, ResonanceTarget
from services.gochara_kernel import ids as kernel_ids
from services.gochara_v3.context import ClassContext, KakshyaBoundaryRow
from services.gochara_v3.engine import (
    _gather_sentences_no_db,
    _kakshya_cell_crossing_from_context,
    _sentence_identity,
)
from services.gochara_v3.interval_solver import (
    EvaluationFailure,
    find_threshold_crossings,
    score_chain_milestones,
)
from services.gochara_v3.resolution_hierarchy import build_resolution_hierarchy
from services.gochara_v3.threshold import ThresholdConfig


_BASE_JD = 2461042.0


def _make_threshold_config(lambda_thresh: float = 0.30) -> ThresholdConfig:
    return ThresholdConfig(
        percentile_used=0.80,
        lambda_thresh=lambda_thresh,
        implied_density=10.0,
        base_rate_cited=0.20,
        age_band_used="band_41_60",
        density_flag="ok",
        fallback_used=False,
        sample_count=5200,
    )


def _make_mock_context(**overrides) -> ClassContext:
    defaults = {
        "chart_id": "test-chart-id",
        "event_class": "marriage",
        "resonance_targets": (),
        "promise": 0.5,
        "promise_detail": {},
        "dasha_periods": (),
        "relevant_grahas": frozenset(),
        "relevant_signs": frozenset(),
        "temporal_shape": "point",
        "valence": "neutral",
        "is_adverse": False,
        "beta_e": 1.0,
        "weight_by_target_ref": {},
        "natal_facts": None,
        "av_gate_rows": (),
        "av_gate_fetch_error": None,
        "sade_sati_phases": (),
        "vedha_rows": (),
        "malefic_scale": (),
        "kakshya_boundaries": (),
        "moorti_rows": (),
    }
    defaults.update(overrides)
    return ClassContext(**defaults)


# ---------------------------------------------------------------------------
# H-1a: kakṣyā-cell crossing uses L1 boundaries pre-fetched in ClassContext.
# ---------------------------------------------------------------------------

class TestH1aKakshyaContextBoundaries:
    """WP5 H-1a: _kakshya_cell_crossing_from_context uses context.kakshya_boundaries."""

    def _transit_event(self, jd: float, lon: float = 15.0):
        ev = MagicMock()
        ev.event_jd = jd
        ev.event_datetime_ist = "2026-01-01T12:00:00+05:30"
        ev.exact_longitude_deg = lon
        return ev

    def test_uses_l1_rows_when_present(self):
        target = ResonanceTarget(
            chart_id="c",
            event_class="marriage",
            target_type="bhava",
            target_ref="7",
            weight=1.0,
            target_sign="Aries",
            uncited_extension=True,
        )
        l1_rows = (
            KakshyaBoundaryRow(planet="Jupiter", kakshya_index=0, start_deg=10.0, end_deg=20.0),
            KakshyaBoundaryRow(planet="Jupiter", kakshya_index=1, start_deg=20.0, end_deg=30.0),
        )
        ctx = _make_mock_context(kakshya_boundaries=l1_rows)

        with patch(
            "services.gochara_v3.engine.find_aspect_events",
            return_value=[self._transit_event(_BASE_JD + 1.0)],
        ) as mock_find:
            sentences = _kakshya_cell_crossing_from_context(
                MagicMock(), ctx, target, _BASE_JD, _BASE_JD + 30.0,
                planets=["Jupiter"],
            )

        assert len(sentences) == 2
        assert {s.detail["boundary_deg"] for s in sentences} == {10.0, 20.0}
        for s in sentences:
            assert s.detail["source"] == "chart_facts.ashtakavarga_kakshya_boundary"
            assert s.uncited_extension is False

        calls = mock_find.call_args_list
        assert len(calls) == 2
        boundary_args = {c.args[2] for c in calls}
        assert boundary_args == {10.0, 20.0}

    def test_honest_equal_eighths_fallback(self):
        target = ResonanceTarget(
            chart_id="c",
            event_class="marriage",
            target_type="bhava",
            target_ref="7",
            weight=1.0,
            target_sign="Aries",
            uncited_extension=True,
        )
        ctx = _make_mock_context(kakshya_boundaries=())

        with patch(
            "services.gochara_v3.engine.find_aspect_events",
            return_value=[self._transit_event(_BASE_JD + 1.0)],
        ) as mock_find:
            sentences = _kakshya_cell_crossing_from_context(
                MagicMock(), ctx, target, _BASE_JD, _BASE_JD + 30.0,
                planets=["Jupiter"],
            )

        # Aries starts at 0 degrees, so equal-eighths boundaries are 0, 3.75, 7.5, ...
        assert len(sentences) == 8
        for s in sentences:
            assert s.detail["source"] == "equal_eighths_fixture_approximation"
            assert s.uncited_extension is True

        assert mock_find.call_count == 8


# ---------------------------------------------------------------------------
# H-2: explicit EvaluationFailure state.
# ---------------------------------------------------------------------------

class TestH2EvaluationFailure:
    """WP5 H-2: failures become unqualified records, not silent 0.0/None."""

    def test_find_threshold_crossings_emits_unqualified_interval(self):
        ctx = _make_mock_context()
        swe = MagicMock()
        exc = EvaluationFailure("engine blew up")

        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
            side_effect=exc,
        ):
            intervals = find_threshold_crossings(
                swe, ctx,
                start_jd=_BASE_JD,
                end_jd=_BASE_JD + 30.0,
                threshold_config=_make_threshold_config(),
                coarse_step_days=1.0,
            )

        assert len(intervals) == 1
        iv = intervals[0]
        assert iv.completeness_state == "unqualified"
        assert iv.failure_detail == "engine blew up"
        assert iv.peak_lambda == 0.0
        assert iv.enter_jd == _BASE_JD
        assert iv.exit_jd == _BASE_JD + 30.0

    def test_score_chain_milestones_per_milestone_failure(self):
        ctx = _make_mock_context()
        swe = MagicMock()
        threshold_config = _make_threshold_config(lambda_thresh=0.30)

        template = [
            {"milestone_id": "m1", "typical_offset_days": 0.0, "is_irreversibility_milestone": False},
            {"milestone_id": "m2", "typical_offset_days": 5.0, "is_irreversibility_milestone": False},
        ]

        def side_effect(swe, context, jd_array, v1_parity_mode=False, **kwargs):
            jd = float(jd_array[0])
            if jd == _BASE_JD:
                raise EvaluationFailure("first milestone failed")
            result = MagicMock()
            result.raw_lambda = 0.80
            return [result]

        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
            side_effect=side_effect,
        ):
            scores = score_chain_milestones(
                swe, ctx, _BASE_JD, template, threshold_config,
            )

        assert len(scores) == 2
        s0, s1 = scores
        assert s0.completeness_state == "unqualified"
        assert s0.failure_detail is not None
        assert s1.completeness_state == "applied"
        assert s1.failure_detail is None


# ---------------------------------------------------------------------------
# H-3: horizon fields on HierarchyResult.
# ---------------------------------------------------------------------------

class TestH3HorizonFields:
    """WP5 H-3: requested/completed horizon fields are populated."""

    def test_build_resolution_hierarchy_populates_horizon(self):
        swe = MagicMock()
        ctx = _make_mock_context()
        start_jd = _BASE_JD
        end_jd = _BASE_JD + 365.0

        interval = type("IntervalBoundary", (), {
            "enter_jd": start_jd + 10.0,
            "exit_jd": start_jd + 40.0,
            "peak_jd": start_jd + 25.0,
            "peak_lambda": 0.80,
            "era_slice_key": "g3_utkarsha",
            "term_breakdown": None,
            "lambda_v3_ci_low": None,
            "lambda_v3_ci_high": None,
            "ci_source": None,
            "completeness_state": "applied",
            "failure_detail": None,
        })()

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=([interval], [], []),
        ):
            result = build_resolution_hierarchy(
                swe, ctx, start_jd, end_jd,
                threshold_config=_make_threshold_config(),
            )

        assert result.requested_start_jd == start_jd
        assert result.requested_end_jd == end_jd
        assert result.completed_start_jd == start_jd + 10.0
        assert result.completed_end_jd == start_jd + 40.0

    def test_empty_result_still_carries_requested_horizon(self):
        swe = MagicMock()
        ctx = _make_mock_context()

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=([], [], []),
        ):
            result = build_resolution_hierarchy(
                swe, ctx, _BASE_JD, _BASE_JD + 30.0,
                threshold_config=_make_threshold_config(),
            )

        assert result.requested_start_jd == _BASE_JD
        assert result.requested_end_jd == _BASE_JD + 30.0
        assert result.completed_start_jd is None
        assert result.completed_end_jd is None


# ---------------------------------------------------------------------------
# H-4/H-6: physical-event identity via the PINNED kernel contract, and
# duplicate collapse. (H-5, the stored-peak cap, is NOT covered here — see
# ESCALATIONS.md; it needs P-1/P-2 serving-side coordination.)
# ---------------------------------------------------------------------------

class TestH4H6PhysicalEventIdentity:
    """WP5 H-4/H-6: contact_id/independence_group via services.gochara_kernel.ids,
    and one-row-per-physical-event collapse."""

    def _sentence(self, *, target_ref: str, event_jd: float, primitive: str = "degree_contact") -> ConfigurationSentence:
        return ConfigurationSentence(
            primitive=primitive,
            chart_id="c",
            event_class="marriage",
            target_type="bhava",
            target_ref=target_ref,
            transit_planet="Jupiter",
            secondary_planet=None,
            event_jd=event_jd,
            event_datetime_ist="2026-01-01T12:00:00+05:30",
            temporal_shape="point",
            uncited_extension=True,
            detail={"target_longitude_deg": 15.0, "aspect_deg": 0.0},
        )

    def test_sentence_identity_matches_kernel_contract(self):
        """The adapter must call the real kernel functions, not a local
        reimplementation — verified by reproducing its result independently
        via the same keyword-argument contract WP1_CONTRACTS.md §3.2 pins."""
        s = self._sentence(target_ref="7", event_jd=_BASE_JD)
        cid, igroup = _sentence_identity(s)

        expected_cid = kernel_ids.contact_id(
            chart_id="c",
            convention_id="wp1-design-pending",
            body="Jupiter",
            target_type="bhava",
            relation="degree_contact",
            aspect_deg=0.0,
            t_exact_jd=_BASE_JD,
            target_ref="7",
            method_version="gochara_v3_engine.wp5",
        )
        expected_igroup = kernel_ids.independence_group(
            body="Jupiter",
            relation="degree_contact",
            aspect_deg=0.0,
            target_deg=15.0,
            t_exact_jd=_BASE_JD,
            t_fallback_jd=_BASE_JD,
        )
        assert cid == expected_cid
        assert igroup == expected_igroup
        assert cid != igroup

    def test_no_instant_yields_no_identity(self):
        s = self._sentence(target_ref="7", event_jd=_BASE_JD)
        s.event_jd = None
        cid, igroup = _sentence_identity(s)
        assert cid is None
        assert igroup is None

    def test_duplicate_independence_group_collapses_to_one_row(self):
        target_a = ResonanceTarget(
            chart_id="c", event_class="marriage", target_type="bhava",
            target_ref="7", weight=1.0, uncited_extension=True,
        )
        target_b = ResonanceTarget(
            chart_id="c", event_class="marriage", target_type="bhava",
            target_ref="8", weight=1.0, uncited_extension=True,
        )

        # Same physical instant, same transit body, same target longitude/aspect.
        sentence_a = self._sentence(target_ref="7", event_jd=_BASE_JD + 1.0)
        sentence_b = self._sentence(target_ref="8", event_jd=_BASE_JD + 1.0)

        def fake_primitive(swe, chart_id, target, start_jd, end_jd):
            if target.target_ref == "7":
                return [sentence_a]
            return [sentence_b]

        with patch("services.gochara_v3.engine.P.degree_contact", side_effect=fake_primitive):
            with patch("services.gochara_v3.engine.P.drishti_contact", return_value=[]):
                with patch("services.gochara_v3.engine.P.sign_ingress", return_value=[]):
                    with patch("services.gochara_v3.engine.P.nakshatra_ingress_tara", return_value=[]):
                        with patch("services.gochara_v3.engine.P.station_retro_loop", return_value=[]):
                            with patch("services.gochara_v3.engine.P.eclipse_degree", return_value=[]):
                                with patch("services.gochara_v3.engine._kakshya_cell_crossing_from_context", return_value=[]):
                                    with patch("services.gochara_v3.engine.P.gochara_vedha_pair", return_value=[]):
                                        with patch("services.gochara_v3.engine.SBC.find_sarvatobhadra_vedha_states", return_value=[]):
                                            result = _gather_sentences_no_db(
                                                MagicMock(), _make_mock_context(),
                                                [target_a, target_b],
                                                _BASE_JD, _BASE_JD + 30.0,
                                            )

        assert len(result) == 1
        assert result[0].detail["contact_id"] is not None
        assert result[0].detail["independence_group"] is not None

    def test_distinct_physical_events_remain_distinct(self):
        target = ResonanceTarget(
            chart_id="c", event_class="marriage", target_type="bhava",
            target_ref="7", weight=1.0, uncited_extension=True,
        )
        sentence_a = self._sentence(target_ref="7", event_jd=_BASE_JD + 1.0)
        sentence_b = self._sentence(target_ref="7", event_jd=_BASE_JD + 2.0)

        with patch("services.gochara_v3.engine.P.degree_contact", return_value=[sentence_a, sentence_b]):
            with patch("services.gochara_v3.engine.P.drishti_contact", return_value=[]):
                with patch("services.gochara_v3.engine.P.sign_ingress", return_value=[]):
                    with patch("services.gochara_v3.engine.P.nakshatra_ingress_tara", return_value=[]):
                        with patch("services.gochara_v3.engine.P.station_retro_loop", return_value=[]):
                            with patch("services.gochara_v3.engine.P.eclipse_degree", return_value=[]):
                                with patch("services.gochara_v3.engine._kakshya_cell_crossing_from_context", return_value=[]):
                                    with patch("services.gochara_v3.engine.P.gochara_vedha_pair", return_value=[]):
                                        with patch("services.gochara_v3.engine.SBC.find_sarvatobhadra_vedha_states", return_value=[]):
                                            result = _gather_sentences_no_db(
                                                MagicMock(), _make_mock_context(),
                                                [target],
                                                _BASE_JD, _BASE_JD + 30.0,
                                            )

        assert len(result) == 2
