"""L3-W2 immutable source contracts for independent service/pure identities.

These tests are deliberately DB-free.  They qualify source behavior only; they
do not claim an accepted physical generation, integration, deployment, or
consumer value.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import fields
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from services.ka_dasha_kala.service import (
    CrossDashaAgreement,
    EligibleWindow,
    KaDashaKalaResult,
    KaDashaKalaService,
)
from services.ka_graha_sancara.engine import EphemerisResult, GrahaState
from services.ka_gochara_resonance.writer import KaGocharaResonanceWriter
from services.ka_kota_chakra.writer import KaKotaChakraWriter
from services.ka_moorti_nirnaya.writer import KaMoortiNirnayaWriter
from services.ka_sudarshana_varsha.writer import KaSudarshanaVarshaWriter
from services.ka_tithi_pravesha.writer import KaTithiPraveshaWriter
from services.ka_tulana.ranker import (
    CompareRequest,
    KaTulanaService,
    WindowInput,
)
from services.ka_vedha_gochara.writer import KaVedhaGocharaWriter
from panchang_engine.types import MuhuratWindow
from pipeline.orchestrator.writers.ka_avadhi import KaAvdhiWriter
from pipeline.orchestrator.writers.ka_yojaka import KaYojakaWriter


REF = date(2026, 1, 1)


def _field_names(cls: type) -> tuple[str, ...]:
    return tuple(field.name for field in fields(cls))


def _window(window_id: str = "w1", **changes) -> dict:
    values = {
        "chart_id": "chart-1",
        "window_id": window_id,
        "field_snapshot_id": "snapshot-1",
        "window_start": REF + timedelta(days=20),
        "window_end": REF + timedelta(days=40),
        "precision_regime": "day_grade",
        "event_class": "career-event",
        "event_domain": "career",
        "confidence_tier": "concurrent",
        "jury": {
            "assertion_id": "jury:" + window_id,
            "generation": "candidate:fixture",
            "dw": 0.62,
            "anchor_days": 30,
            "provenance": {"fact_ids": ["fixture-fact-1"]},
        },
        "jury_binding": {
            "chart_id": "chart-1",
            "window_id": window_id,
            "field_snapshot_id": "snapshot-1",
            "assertion_id": "jury:" + window_id,
            "generation": "candidate:fixture",
        },
        "contest_rows": 0,
    }
    values.update(changes)
    return values


class _FailingDashaConnection:
    def execute(self, _sql, _params=None):
        raise RuntimeError("fixture system read failed")


def test_w2_service_payload_shapes_are_exact_and_immutable():
    """Freeze every public field promised by the four S1 service payloads."""
    # KA-1w / ALGO 3.18 adds declared sky metadata after the legacy fields.
    assert _field_names(EphemerisResult) == (
        "query_dt", "ayanamsha", "source", "grahas",
        "jd", "time_scale", "path", "backend", "flags", "flag_names",
        "node_model", "ayanamsha_id", "ayanamsha_deg", "convention_id",
        "coverage", "null_reason",
    )
    assert _field_names(GrahaState) == (
        "name", "sidereal_lon_deg", "sign", "sign_idx", "nakshatra",
        "nakshatra_idx", "degrees_in_sign", "degrees_in_nakshatra",
        "speed_dps", "is_retrograde", "source",
    )
    assert _field_names(KaDashaKalaResult) == (
        "chart_id", "ayanamsha_id", "target_lords", "related_lords",
        "date_start", "date_end", "max_level", "prana_grain",
        "systems_queried", "windows", "kp_windows", "total_windows",
        "high_agreement_count",
    )
    assert _field_names(EligibleWindow) == (
        "dasha_row_id", "chart_id", "ayanamsha_id", "system_id", "level_n",
        "lord_graha", "start_date", "end_date", "ancestor_lords",
        "eligibility_band", "eligibility_score", "cross_dasha_agreement",
        "kp_sublevel", "kp_sub_lord", "is_prana_computed",
    )
    assert _field_names(CrossDashaAgreement) == ("count", "systems_agreeing")
    assert _field_names(MuhuratWindow) == (
        "event", "start_utc", "end_utc", "star_rating", "score", "breakdown",
    )
    # K7-4 replaces only Tulana's retired scalar payloads (ALGO §3.10).
    assert tuple(WindowInput.model_fields) == (
        "chart_id", "window_id", "field_snapshot_id", "window_start", "window_end",
        "precision_regime", "event_class", "event_domain", "confidence_tier",
        "weakest_link", "robustness", "jury", "jury_binding", "obstruction",
        "contest_rows", "lambda_peak", "null_p", "factor_informativeness",
        "factor_consequence",
    )
    assert tuple(CompareRequest.model_fields) == (
        "windows", "date_from", "date_to", "question_frame", "preference",
    )
    result = KaTulanaService().compare_windows([_window()], date_from=REF)
    assert set(result) == {
        "contract_version", "evidence", "comparisons", "front", "ordered",
        "rejected", "order_policy", "question_frame", "entity_not_evaluated",
        "tolerances", "empty_reason", "front_rule", "dominance_cycles",
    }
    assert result["front_rule"] == "undominated_or_cycle_member"
    assert result["dominance_cycles"] == []
    evidence = result["evidence"]["w1"]
    assert set(evidence) == {"axes", "anchor_days", "annotations"}
    assert set(evidence["axes"]) == {"nearest", "strongest", "most_robust"}
    for axis in evidence["axes"].values():
        assert set(axis) == {"state", "value", "reason"}
    assert set(evidence["annotations"]) == {
        "confidence_tier", "weakest_link", "robustness", "lambda_peak", "null_p",
        "factor_informativeness", "factor_consequence", "strongest_qualification",
        "strongest_coverage", "strongest_provenance", "witness_signature",
        "obstruction", "contest_rows", "dissonance",
    }
    pair = KaTulanaService().compare(_window("a"), _window("b"), REF)
    assert set(pair) == {"A", "B", "axes", "relation", "reason"}
    assert pair["relation"] == "tie"
    for axis in pair["axes"].values():
        assert set(axis) == {"A", "B", "relation", "tolerance"}


def test_ephemeris_legacy_constructor_preserves_fields_without_fabricating_metadata():
    """Retained comparison engines can still construct the four-field envelope."""
    instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
    grahas = {}
    result = EphemerisResult(instant, "lahiri", "bg_ephemeris", grahas)

    assert (result.query_dt, result.ayanamsha, result.source, result.grahas) == (
        instant, "lahiri", "bg_ephemeris", grahas,
    )
    assert result.grahas is grahas
    assert (
        result.jd, result.time_scale, result.path, result.backend, result.flags,
        result.flag_names, result.node_model, result.ayanamsha_id,
        result.ayanamsha_deg, result.convention_id, result.coverage, result.null_reason,
    ) == (None,) * 12


def test_ka_dasha_kala_fails_closed_on_population_read_failure():
    from services.gochara_kernel.dasha_read import DashaBuildRefused

    service = KaDashaKalaService(_FailingDashaConnection())
    with pytest.raises(DashaBuildRefused, match="dasha_read_unavailable") as refusal:
        service.query(
            chart_id="chart-1",
            ayanamsha_id="lahiri_chitrapaksha",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=REF,
            date_end=REF + timedelta(days=30),
            max_level=1,
            systems={"vimshottari"},
        )
    assert refusal.value.code == "dasha_read_unavailable"
    assert isinstance(refusal.value.__cause__, RuntimeError)
    assert str(refusal.value.__cause__) == "fixture system read failed"


@pytest.mark.parametrize(
    ("systems", "start", "end", "message"),
    [
        ({"invented_system"}, REF, REF + timedelta(days=1), "unknown dasha systems"),
        (set(), REF, REF + timedelta(days=1), "systems must not be empty"),
        ({"vimshottari"}, REF, REF, "date_start must be before date_end"),
    ],
)
def test_ka_dasha_kala_rejects_ambiguous_query_contracts(systems, start, end, message):
    service = KaDashaKalaService(_FailingDashaConnection())
    with pytest.raises(ValueError, match=message):
        service.query(
            chart_id="chart-1",
            ayanamsha_id="lahiri_chitrapaksha",
            target_lords={"Saturn"},
            related_lords=set(),
            date_start=start,
            date_end=end,
            max_level=1,
            systems=systems,
        )


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"lambda_peak": float("nan")}, "finite number"),
        ({"null_p": float("inf")}, "finite number"),
        ({"contest_rows": -1}, "greater than or equal to 0"),
        ({"contest_rows": True}, "valid integer"),
        ({"confidence_tier": "unknown"}, "unknown confidence_tier"),
        ({"mode": "NOT_A_MODE"}, "Extra inputs are not permitted"),
        ({"convergence_score": 0.8}, "Extra inputs are not permitted"),
        ({"window_start": REF + timedelta(days=50)}, "invalid window span"),
        ({"window_end": REF + timedelta(days=10)}, "invalid window span"),
        ({"jury_binding": {"chart_id": "other-chart"}}, "outside chart/window/snapshot/generation"),
        ({"jury": None}, "jury binding without jury evidence"),
    ],
)
def test_ka_tulana_rejects_unqualified_window_inputs(changes, message):
    with pytest.raises(ValueError, match=message):
        KaTulanaService().compare_windows([_window(**changes)], date_from=REF)


@pytest.mark.parametrize("field,value,message", [
    ("dw", float("nan"), "finite signed D"),
    ("dw", True, "finite signed D"),
    ("dw", None, "null D"),
    ("anchor_days", -1, "positive finite jury anchor_days"),
    ("anchor_days", 0, "positive finite jury anchor_days"),
])
def test_ka_tulana_rejects_unqualified_jury_inputs(field, value, message):
    window = _window()
    window["jury"][field] = value
    with pytest.raises(ValueError, match=message):
        KaTulanaService().compare_windows([window], date_from=REF)


def test_ka_tulana_unknown_domain_is_unavailable_and_contest_is_bound():
    a, b = _window("a", event_domain="invented-domain"), _window("b")
    result = KaTulanaService().compare_windows(
        [a, b], date_from=REF, question_frame={"domain": "career"},
    )
    assert result["evidence"]["a"]["axes"]["best_suited"] == {
        "state": "information_unavailable", "value": None,
        "reason": "event_class_not_in_ontology",
    }
    assert result["comparisons"][0]["relation"] == "incomparable"
    assert result["front"] == ["a", "b"]
    a["contest_rows"] = 2
    b["contest_rows"] = 2
    b["jury_binding"] = None
    result = KaTulanaService().compare_windows([a, b], date_from=REF)
    assert result["evidence"]["a"]["annotations"]["dissonance"] is True
    assert result["evidence"]["b"]["annotations"]["dissonance"] is None
    assert result["evidence"]["b"]["annotations"]["contest_rows"] is None


def test_ka_tulana_rejects_duplicate_window_identity():
    with pytest.raises(ValueError, match="duplicate window_id"):
        KaTulanaService().compare_windows([_window("same"), _window("same")], date_from=REF)


@pytest.mark.parametrize("horizon_days", [-1, 0])
def test_ka_tulana_rejects_nonpositive_comparison_horizon(horizon_days):
    with pytest.raises(ValueError, match="date_to must exceed date_from"):
        KaTulanaService().compare_windows(
            [_window()], date_from=REF, date_to=REF + timedelta(days=horizon_days),
        )


def test_ka_tulana_fixture_evidence_and_dominance_remain_content_bound():
    service = KaTulanaService()
    window_a = _window("fixture-a", window_start=REF)
    window_b = _window(
        "fixture-b",
        window_start=date(2026, 6, 1),
        window_end=date(2026, 6, 30),
        confidence_tier="structural_prior",
    )
    window_b["jury"]["dw"] = 0.50
    original = deepcopy([window_b, window_a])
    result = service.compare_windows([window_b, window_a], date_from=REF)
    verdict = service.compare(window_a, window_b, REF)
    assert result["front"] == ["fixture-a"]
    assert result["ordered"] == ["fixture-a", "fixture-b"]
    assert verdict["relation"] == "A_dominates"
    assert verdict["reason"] is None
    for axis, a_value, b_value, tolerance in (
        ("nearest", 0, 151, 1),
        ("strongest", 0.62, 0.50, 1 / 30),
        ("most_robust", 1, 0, 0),
    ):
        assert verdict["axes"][axis] == {
            "A": {"state": "evaluated", "value": a_value, "reason": None},
            "B": {"state": "evaluated", "value": b_value, "reason": None},
            "relation": "A_better", "tolerance": tolerance,
        }
    assert result["evidence"]["fixture-a"]["annotations"]["strongest_provenance"] == {
        "fact_ids": ["fixture-fact-1"],
    }
    assert [window_b, window_a] == original


def test_ka_tulana_fixture_tradeoff_and_preference_never_rewrite_evidence():
    service = KaTulanaService()
    a = _window("a", window_start=REF, confidence_tier="structural_prior")
    b = _window("b")
    default = service.compare_windows([a, b], date_from=REF)
    nearest = service.compare_windows([a, b], date_from=REF, preference=["nearest"])
    assert default["front"] == nearest["front"] == ["a", "b"]
    assert default["comparisons"][0]["relation"] == "incomparable"
    assert default["comparisons"][0]["reason"] == "tradeoff"
    assert default["ordered"] == ["b", "a"]
    assert nearest["ordered"] == ["a", "b"]
    assert nearest["order_policy"] == ["nearest", "most_robust", "strongest"]
    assert default["evidence"] == nearest["evidence"]
    assert default["comparisons"] == nearest["comparisons"]


class _NoAccessConnection:
    def cursor(self, *_args, **_kwargs):
        raise AssertionError("dry run accessed the database")


@pytest.mark.parametrize("writer_class", [KaYojakaWriter, KaAvdhiWriter])
def test_first_frontier_pipeline_writers_are_mutation_free_on_dry_run(writer_class):
    ctx = SimpleNamespace(
        db_conn=_NoAccessConnection(),
        config={"chart_id": "chart-1"},
        dry_run=True,
    )
    result = writer_class().run(ctx)
    assert result.asset_id == writer_class.asset_id
    assert result.rows_inserted == 0
    assert result.notes == "dry_run=True"
