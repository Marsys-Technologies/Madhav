"""N-14 (L3 §4.9) exit-gate fixture — `nodal_drishti` removal flag.

When nodal_drishti='removed':
  - drishti_contact emits no rows with body ∈ {Rahu, Ketu} (nodes stay
    agents/targets for the other relations);
  - w30_modifier leaves the λ product;
  - the removed term survives one generation as the labelled non-scoring
    annotation term_breakdown.w30_annotation;
  - the absence is recorded as completeness_state on w30_detail.

Synthetic chart data only (no real chart, no person).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from services.gochara_grammar.models import ConfigurationSentence
from services.gochara_v3 import engine


CHART_ID = "00000000-0000-4000-8000-0000000004a9"  # synthetic, non-person
T_JD = 2460000.0
W30_VALUE = 1.05


def _sentence(primitive: str, body: str) -> ConfigurationSentence:
    return ConfigurationSentence(
        primitive=primitive,
        chart_id=CHART_ID,
        event_class="synthetic_n14",
        target_type="synthetic",
        target_ref="syn:target",
        transit_planet=body,
        secondary_planet=None,
        event_jd=T_JD,
        event_datetime_ist=None,
        uncited_extension=True,
        temporal_shape="point",
        detail={"aspect_deg": 180.0, "target_longitude_deg": 280.0},
    )


def _activity_sentence() -> ConfigurationSentence:
    s = _sentence("degree_contact", "Saturn")
    s.detail["orb_strength"] = 1.0
    return s


class _Swe:
    MOON = 1
    FLG_SIDEREAL = 2

    def calc_ut(self, jd, body, flags):
        return ((10.0, 0.0, 0.0, 0.0), 2)


class _Ctx:
    chart_id = CHART_ID
    event_class = "synthetic_n14"
    temporal_shape = "point"
    promise = 0.8
    promise_detail = {}
    weight_by_target_ref = {"syn:target": 1.0}
    valence = "benefic"
    is_adverse = False
    beta_e = 0.0


def _patch_eval_path(monkeypatch, gathered):
    monkeypatch.setattr(
        engine, "_compute_permission_from_context",
        lambda *a, **k: (0.5, {"calibration_state": "structural_prior"}),
    )
    monkeypatch.setattr(
        engine, "_gather_sentences_no_db",
        lambda *a, **k: gathered,
    )
    monkeypatch.setattr(
        engine, "_compute_quality_gates_from_context",
        lambda *a, **k: (1.0, {}),
    )
    monkeypatch.setattr(engine, "_jd_to_ist_iso", lambda swe, jd: "syn-iso")
    monkeypatch.setattr(engine, "_jd_to_date_iso", lambda swe, jd: "syn-date")
    monkeypatch.setattr(
        engine._w23, "compute",
        lambda *a, **k: SimpleNamespace(
            modifier=1.0, tara_name=None, tara_position=None,
            skipped=True, skip_reason="synthetic", mechanism_id="w23",
        ),
    )
    monkeypatch.setattr(
        engine._w30, "compute",
        lambda *a, **k: SimpleNamespace(
            modifier=W30_VALUE, rahu_sign=1, ketu_sign=7,
            aspected_sign_indices=[1], skipped=False,
            skip_reason=None, mechanism_id="w30",
        ),
    )


def test_gather_emits_no_nodal_drishti_rows_when_removed(monkeypatch):
    drishti_rows = [
        _sentence("drishti_contact", "Rahu"),
        _sentence("drishti_contact", "Ketu"),
        _sentence("drishti_contact", "Saturn"),
    ]
    for name in (
        "degree_contact", "sign_ingress", "nakshatra_ingress_tara",
        "station_retro_loop", "eclipse_degree",
    ):
        monkeypatch.setattr(engine.P, name, lambda *a, **k: [])
    monkeypatch.setattr(engine.P, "drishti_contact", lambda *a, **k: drishti_rows)
    monkeypatch.setattr(engine.P, "gochara_vedha_pair", lambda *a, **k: [])
    monkeypatch.setattr(
        engine.SBC, "find_sarvatobhadra_vedha_states", lambda *a, **k: [],
    )
    monkeypatch.setattr(
        engine, "_kakshya_cell_crossing_from_context", lambda *a, **k: [],
    )

    out_removed = engine._gather_sentences_no_db(
        None, _Ctx(), ["syn:target"], T_JD - 5.0, T_JD + 5.0,
        nodal_drishti="removed",
    )
    bodies = [(s.primitive, s.transit_planet) for s in out_removed]
    assert ("drishti_contact", "Rahu") not in bodies
    assert ("drishti_contact", "Ketu") not in bodies
    assert ("drishti_contact", "Saturn") in bodies  # non-node rows kept

    out_enabled = engine._gather_sentences_no_db(
        None, _Ctx(), ["syn:target"], T_JD - 5.0, T_JD + 5.0,
    )
    bodies_enabled = [(s.primitive, s.transit_planet) for s in out_enabled]
    assert ("drishti_contact", "Rahu") in bodies_enabled
    assert ("drishti_contact", "Ketu") in bodies_enabled


def test_w30_leaves_lambda_product_when_removed(monkeypatch):
    _patch_eval_path(monkeypatch, [_activity_sentence()])
    result = engine._evaluate_single_from_context(
        _Swe(), _Ctx(), T_JD, ["syn:target"], nodal_drishti="removed",
    )
    # 0.8 × 0.5 × 1.0(activity) × 1.0(tara) × 1.0(w30 absent) × 1.0(gates)
    assert abs(result.raw_lambda - 0.4) < 1e-9
    assert result.term_breakdown["w30_modifier"] == 1.0
    annotation = result.term_breakdown["w30_annotation"]
    assert annotation["scoring"] is False
    assert annotation["would_be_modifier"] == W30_VALUE
    assert "N-14" in annotation["label"]
    w30_detail = result.x_t_detail["w30_detail"]
    assert w30_detail["completeness_state"] == "inapplicable"
    assert w30_detail["removed_by_ruling"] == "N-14"


def test_w30_in_product_when_enabled(monkeypatch):
    _patch_eval_path(monkeypatch, [_activity_sentence()])
    result = engine._evaluate_single_from_context(
        _Swe(), _Ctx(), T_JD, ["syn:target"],
    )
    assert abs(result.raw_lambda - 0.4 * W30_VALUE) < 1e-9
    assert "w30_annotation" not in result.term_breakdown
    assert "completeness_state" not in result.x_t_detail["w30_detail"]


def test_flag_off_byte_identical(monkeypatch):
    _patch_eval_path(monkeypatch, [_activity_sentence()])
    r_default = engine._evaluate_single_from_context(
        _Swe(), _Ctx(), T_JD, ["syn:target"],
    )
    r_enabled = engine._evaluate_single_from_context(
        _Swe(), _Ctx(), T_JD, ["syn:target"], nodal_drishti="enabled",
    )
    assert r_default.raw_lambda == r_enabled.raw_lambda
    assert r_default.term_breakdown == r_enabled.term_breakdown
    assert r_default.x_t_detail["w30_detail"] == r_enabled.x_t_detail["w30_detail"]


def test_invalid_mode_rejected():
    with pytest.raises(ValueError, match="nodal_drishti"):
        engine._evaluate_single_from_context(
            None, None, 0.0, [], nodal_drishti="not_a_mode",
        )
