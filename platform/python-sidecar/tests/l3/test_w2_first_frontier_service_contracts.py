"""L3-W2 immutable source contracts for independent service/pure identities.

These tests are deliberately DB-free.  They qualify source behavior only; they
do not claim an accepted physical generation, integration, deployment, or
consumer value.
"""
from __future__ import annotations

from dataclasses import fields
from datetime import date, timedelta
import inspect
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
    AttentionMap,
    CompareVerdict,
    FactorBreakdown,
    KaTulanaService,
    RankedWindow,
    WindowInput,
)
from services.ka_vedha_gochara.writer import KaVedhaGocharaWriter
from panchang_engine.types import MuhuratWindow
from pipeline.orchestrator.writers.ka_avadhi import KaAvdhiWriter
from pipeline.orchestrator.writers.ka_yojaka import KaYojakaWriter


REF = date(2026, 1, 1)


def _field_names(cls: type) -> tuple[str, ...]:
    return tuple(field.name for field in fields(cls))


def _window(window_id: str = "w1", **changes) -> WindowInput:
    values = {
        "window_id": window_id,
        "mode": "A",
        "peak_date": REF + timedelta(days=30),
        "window_start": REF + timedelta(days=20),
        "window_end": REF + timedelta(days=40),
        "convergence_score": 0.8,
        "confidence_label": "high",
        "rarity_years": 15.0,
        "net_label": "auspicious",
        "domains": ["career"],
        "signal_id": "signal-1",
        "source_citation": "fixture:v1",
        "has_dissonance": False,
        "dissonance_domains": [],
    }
    values.update(changes)
    return WindowInput(**values)


class _FailingDashaConnection:
    def execute(self, _sql, _params=None):
        raise RuntimeError("fixture system read failed")


def test_w2_service_payload_shapes_are_exact_and_immutable():
    """Freeze every public field promised by the four S1 service payloads."""
    assert _field_names(EphemerisResult) == ("query_dt", "ayanamsha", "source", "grahas")
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
    assert _field_names(WindowInput) == (
        "window_id", "mode", "peak_date", "window_start", "window_end",
        "convergence_score", "confidence_label", "rarity_years", "net_label",
        "domains", "signal_id", "source_citation", "has_dissonance",
        "dissonance_domains",
    )
    assert _field_names(FactorBreakdown) == (
        "convergence_score", "rarity_norm", "confidence_score",
        "proximity_factor", "composite", "decisive_factor",
    )
    assert _field_names(RankedWindow) == ("rank", "window", "factors", "rationale")
    assert _field_names(CompareVerdict) == (
        "winner", "loser", "winner_factors", "loser_factors",
        "decisive_factor", "confidence_label", "rationale", "dissonance_note",
        "recommendation",
    )
    assert _field_names(AttentionMap) == ("ranked", "by_domain", "horizon_days")


def test_ka_dasha_kala_fails_closed_on_one_system_read_failure():
    service = KaDashaKalaService(_FailingDashaConnection())
    with pytest.raises(RuntimeError, match="vimshottari"):
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
        ({"convergence_score": float("nan")}, "convergence_score must be finite"),
        ({"rarity_years": -1.0}, "rarity_years must be non-negative"),
        ({"confidence_label": "unknown"}, "unknown confidence_label"),
        ({"domains": ["invented-domain"]}, "unknown domains"),
        ({"window_start": REF + timedelta(days=50)}, "window_start must not be after peak_date"),
        ({"window_end": REF + timedelta(days=10)}, "window_end must not be before peak_date"),
    ],
)
def test_ka_tulana_rejects_unqualified_window_inputs(changes, message):
    with pytest.raises(ValueError, match=message):
        KaTulanaService().rank_windows([_window(**changes)], REF)


def test_ka_tulana_rejects_duplicate_window_identity():
    with pytest.raises(ValueError, match="duplicate window_id"):
        KaTulanaService().rank_windows([_window("same"), _window("same")], REF)


def test_ka_tulana_rejects_negative_attention_horizon():
    with pytest.raises(ValueError, match="horizon_days must be non-negative"):
        KaTulanaService().attention_map([_window()], REF, horizon_days=-1)


def test_ka_tulana_fixture_scores_remain_content_bound():
    service = KaTulanaService()
    window_a = _window("fixture-a", peak_date=REF, window_start=None, window_end=None)
    window_b = _window(
        "fixture-b",
        peak_date=date(2026, 6, 1),
        window_start=None,
        window_end=None,
        convergence_score=0.5,
        confidence_label="moderate",
        rarity_years=5.0,
    )

    ranked = service.rank_windows([window_b, window_a], REF)
    verdict = service.compare(window_a, window_b, REF)

    assert [(item.window.window_id, item.factors.composite) for item in ranked] == [
        ("fixture-a", 0.795),
        ("fixture-b", 0.4234),
    ]
    assert verdict.winner.window_id == "fixture-a"
    assert verdict.decisive_factor == "proximity_factor"
    assert verdict.recommendation == "proceed"


@pytest.mark.parametrize(
    ("writer_class", "candidate_anchor", "delete_anchor"),
    [
        (KaGocharaResonanceWriter, "if not all_rows", "cur.execute(_DELETE_SQL"),
        (KaKotaChakraWriter, "if not all_rows", "cur.execute(_DELETE_SQL"),
        (KaMoortiNirnayaWriter, "if not all_rows", "cur.execute(_DELETE_SQL"),
        (KaVedhaGocharaWriter, "if not all_rows", "cur.execute(_DELETE_SQL"),
        (KaTithiPraveshaWriter, "if not all_rows", "cur.execute(_DELETE_SQL"),
        (KaSudarshanaVarshaWriter, "if not all_rows", "cur.execute(_DELETE_SQL"),
        (
            KaYojakaWriter,
            "if not rows",
            '"DELETE FROM kala_activation_predicates WHERE chart_id = %s"',
        ),
        (
            KaAvdhiWriter,
            "if not all_rows",
            '"DELETE FROM kala_avadhi WHERE chart_id = %s"',
        ),
    ],
)
def test_first_frontier_writers_prepare_candidate_before_delete(
    writer_class, candidate_anchor, delete_anchor
):
    source = inspect.getsource(writer_class.run)
    assert source.index(candidate_anchor) < source.index(delete_anchor)


@pytest.mark.parametrize(
    ("writer_class", "coverage_guard"),
    [
        (KaKotaChakraWriter, "grahas_with_data != len(ALL_GRAHAS)"),
        (KaMoortiNirnayaWriter, "missing_bodies"),
        (KaVedhaGocharaWriter, "missing_grahas"),
        (KaAvdhiWriter, "missing_systems"),
    ],
)
def test_first_frontier_writers_refuse_partial_upstream_partitions(
    writer_class, coverage_guard
):
    source = inspect.getsource(writer_class.run)
    assert coverage_guard in source
    assert "prior partition preserved" in source


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
    assert result.rows_inserted == 0
    assert result.notes == "dry_run=True"
