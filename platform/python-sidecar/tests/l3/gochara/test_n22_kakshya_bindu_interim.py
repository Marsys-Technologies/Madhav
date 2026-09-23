"""
N-22 / N-13 (L3 §4.3) — kakṣyā sign-level bindu interim.

Exit-gate fixtures for the recorded flag `kakshya_bindu_interim`
(engine._KAKSHYA_BINDU_INTERIM_ENABLED, default OFF):

  * graha with 0 bindus in the transited sign -> crossing carries
    completeness_state='unqualified' + failure_detail and contributes NO
    activity;
  * graha with 4 bindus in the transited sign -> crossing is qualified
    (qualification_grain='sign', the sign-level BAV declared as the coarser
    qualification) and contributes activity;
  * flag off -> today's behaviour byte-identical (no new detail keys, same
    activity, same contributions).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.gochara_grammar.models import ResonanceTarget
from services.gochara_v3 import engine as engine_module
from services.gochara_v3.context import (
    BinduSignRow, ClassContext, KakshyaBoundaryRow, _fetch_bindu_sign_rows,
)
from services.gochara_v3.engine import (
    _compute_activity_v3, _kakshya_cell_crossing_from_context,
)

_BASE_JD = 2461042.0


def _make_context(**overrides) -> ClassContext:
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
        "bindu_sign_rows": (),
    }
    defaults.update(overrides)
    return ClassContext(**defaults)


def _target(sign: str = "Aries") -> ResonanceTarget:
    return ResonanceTarget(
        chart_id="test-chart-id",
        event_class="marriage",
        target_type="bhava",
        target_ref="7",
        weight=1.0,
        target_sign=sign,
        uncited_extension=True,
    )


def _transit_event(jd: float):
    ev = MagicMock()
    ev.event_jd = jd
    ev.event_datetime_ist = "2026-01-01T12:00:00+05:30"
    ev.exact_longitude_deg = 15.0
    return ev


_L1_ROWS = (
    KakshyaBoundaryRow(planet="Jupiter", kakshya_index=0, start_deg=10.0, end_deg=20.0),
    KakshyaBoundaryRow(planet="Jupiter", kakshya_index=1, start_deg=20.0, end_deg=30.0),
)


def _crossings(ctx: ClassContext, planet: str = "Jupiter"):
    with patch(
        "services.gochara_v3.engine.find_aspect_events",
        return_value=[_transit_event(_BASE_JD + 1.0)],
    ):
        return _kakshya_cell_crossing_from_context(
            MagicMock(), ctx, _target(), _BASE_JD, _BASE_JD + 30.0,
            planets=[planet],
        )


@pytest.fixture
def flag_on(monkeypatch):
    monkeypatch.setattr(engine_module, "_KAKSHYA_BINDU_INTERIM_ENABLED", True)


class TestN22FlagOffByteIdentical:
    """Flag off (the default): today's behaviour is byte-identical."""

    def test_default_is_off(self):
        assert engine_module._KAKSHYA_BINDU_INTERIM_ENABLED is False

    def test_no_new_detail_keys(self):
        ctx = _make_context(
            kakshya_boundaries=_L1_ROWS,
            bindu_sign_rows=(BinduSignRow(graha="JUP", sign_number=1, bindus=0.0),),
        )
        sentences = _crossings(ctx)
        assert len(sentences) == 2
        for s in sentences:
            assert "completeness_state" not in s.detail
            assert "qualification_grain" not in s.detail
            assert "bindu_count" not in s.detail
            assert "failure_detail" not in s.detail
            assert set(s.detail) == {"boundary_deg", "kakshya_index", "source"}

    def test_activity_identical_regardless_of_bindu_rows(self):
        ctx_with = _make_context(
            kakshya_boundaries=_L1_ROWS,
            bindu_sign_rows=(BinduSignRow(graha="JUP", sign_number=1, bindus=0.0),),
        )
        ctx_without = _make_context(kakshya_boundaries=_L1_ROWS)
        sentences_with = _crossings(ctx_with)
        sentences_without = _crossings(ctx_without)

        result_with = _compute_activity_v3(sentences_with, {"7": 1.0})
        result_without = _compute_activity_v3(sentences_without, {"7": 1.0})
        assert result_with == result_without

        activity, detail, term_breakdown = result_with
        # Two sentences, orb_decay fallback 0.5 each, weight 1.0:
        # noisy-OR = 1 - (1 - 0.5)^2 = 0.75
        assert activity == pytest.approx(0.75)
        assert detail["sentence_count_active"] == 2
        assert term_breakdown["kakshya_cell_crossing"] == pytest.approx(1.0)


class TestN22FlagOnUnqualified:
    """Flag on: no resolvable bindu -> unqualified, no activity."""

    def test_zero_bindus_unqualified_no_activity(self, flag_on):
        ctx = _make_context(
            kakshya_boundaries=_L1_ROWS,
            bindu_sign_rows=(BinduSignRow(graha="JUP", sign_number=1, bindus=0.0),),
        )
        sentences = _crossings(ctx)
        assert len(sentences) == 2
        for s in sentences:
            assert s.detail["completeness_state"] == "unqualified"
            fd = s.detail["failure_detail"]
            assert fd["primitive"] == "kakshya_cell_crossing"
            assert fd["error_class"] == "bindu_zero"
            assert "0 bindus in sign 1" in fd["message"]
            assert fd["row_identity"] == "test-chart-id:JUP-SIGN_1"
            assert "qualification_grain" not in s.detail

        activity, detail, term_breakdown = _compute_activity_v3(sentences, {"7": 1.0})
        assert activity == 0.0
        assert detail["sentence_count_active"] == 0
        assert detail["contributions"] == []
        assert "kakshya_cell_crossing" not in term_breakdown

    def test_missing_row_unqualified(self, flag_on):
        ctx = _make_context(kakshya_boundaries=_L1_ROWS, bindu_sign_rows=())
        sentences = _crossings(ctx)
        for s in sentences:
            assert s.detail["completeness_state"] == "unqualified"
            fd = s.detail["failure_detail"]
            assert fd["error_class"] == "bindu_unresolvable"
            assert fd["row_identity"] == "test-chart-id:JUP-SIGN_1"

        activity, _, _ = _compute_activity_v3(sentences, {"7": 1.0})
        assert activity == 0.0

    def test_node_crossing_unqualified(self, flag_on):
        """Nodes have no BAV rows — honestly unqualified under the interim."""
        ctx = _make_context(kakshya_boundaries=(), bindu_sign_rows=())
        sentences = _crossings(ctx, planet="Rahu")
        assert len(sentences) == 8  # equal-eighths fallback
        for s in sentences:
            assert s.detail["completeness_state"] == "unqualified"
            assert s.detail["failure_detail"]["error_class"] == "bindu_unresolvable"
            assert s.detail["failure_detail"]["row_identity"].endswith(":RAH_MEAN-SIGN_1")

        activity, _, _ = _compute_activity_v3(sentences, {"7": 1.0})
        assert activity == 0.0

    def test_bindu_row_for_other_sign_does_not_qualify(self, flag_on):
        ctx = _make_context(
            kakshya_boundaries=_L1_ROWS,
            bindu_sign_rows=(BinduSignRow(graha="JUP", sign_number=2, bindus=4.0),),
        )
        sentences = _crossings(ctx)
        for s in sentences:
            assert s.detail["completeness_state"] == "unqualified"


class TestN22FlagOnQualified:
    """Flag on: a resolvable bindu count qualifies the crossing (sign grain)."""

    def test_four_bindus_qualified_contributes_activity(self, flag_on):
        ctx = _make_context(
            kakshya_boundaries=_L1_ROWS,
            bindu_sign_rows=(BinduSignRow(graha="JUP", sign_number=1, bindus=4.0),),
        )
        sentences = _crossings(ctx)
        assert len(sentences) == 2
        for s in sentences:
            assert s.detail["completeness_state"] == "qualified"
            assert s.detail["qualification_grain"] == "sign"
            assert s.detail["bindu_count"] == 4
            assert s.detail["bindu_source"] == "chart_facts.ashtakavarga_bindu_sign"
            assert "failure_detail" not in s.detail

        activity, detail, term_breakdown = _compute_activity_v3(sentences, {"7": 1.0})
        assert activity == pytest.approx(0.75)
        assert detail["sentence_count_active"] == 2
        assert term_breakdown["kakshya_cell_crossing"] == pytest.approx(1.0)

    def test_one_bindu_is_the_qualification_floor(self, flag_on):
        ctx = _make_context(
            kakshya_boundaries=_L1_ROWS,
            bindu_sign_rows=(BinduSignRow(graha="JUP", sign_number=1, bindus=1.0),),
        )
        sentences = _crossings(ctx)
        for s in sentences:
            assert s.detail["completeness_state"] == "qualified"
            assert s.detail["bindu_count"] == 1


class TestN22ContextFetch:
    """_fetch_bindu_sign_rows parses the CR-99a subject convention."""

    def test_parse_and_degrade(self):
        conn = MagicMock()
        conn.execute.return_value.fetchall.return_value = [
            ("JUP-SIGN_1", 4.0),
            ("JUP-SIGN_2", 0.0),
            ("SAT-SIGN_12", 3.0),
            ("SARVA-SIGN_1", 31.0),
            ("malformed-subject", 5.0),
            ("JUP-SIGN_x", 5.0),
        ]
        rows = _fetch_bindu_sign_rows(conn, "chart-1")
        by_key = {(r.graha, r.sign_number): r.bindus for r in rows}
        assert by_key == {
            ("JUP", 1): 4.0,
            ("JUP", 2): 0.0,
            ("SAT", 12): 3.0,
            ("SARVA", 1): 31.0,
        }

    def test_none_conn_and_none_value(self):
        assert _fetch_bindu_sign_rows(None, "chart-1") == []
        conn = MagicMock()
        conn.execute.return_value.fetchall.return_value = [("JUP-SIGN_1", None)]
        rows = _fetch_bindu_sign_rows(conn, "chart-1")
        assert rows == [BinduSignRow(graha="JUP", sign_number=1, bindus=None)]

    def test_fetch_exception_degrades_to_empty(self):
        conn = MagicMock()
        conn.execute.side_effect = RuntimeError("relation missing")
        assert _fetch_bindu_sign_rows(conn, "chart-1") == []
