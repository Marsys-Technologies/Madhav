from __future__ import annotations

import json
import inspect
from types import SimpleNamespace

from bodha_writers.formulas import ResonanceInputs, resonance_score_v1
from pipeline.orchestrator.writers import bo_pramana_mapa
from pipeline.orchestrator.writers import bo_pratijna, bo_samskara, bo_samvada
from pipeline.orchestrator.writers.bo_sangati import _build_cdlm_cells


def _signal(
    signal_id: str,
    *,
    root: str,
    signal_class: str = "dosha",
    contradictions: list[str] | None = None,
    valence: str = "malefic",
) -> dict:
    return {
        "signal_id": signal_id,
        "signal_type_class": signal_class,
        "signal_tradition": "parashari",
        "domains_affected_array": ["career", "wealth"],
        "computed_salience": 0.5,
        "verification_pass_status": "two_pass_verified",
        "salience_formula_version": "v2",
        "constituent_facts_array": [root],
        "shared_factor_keys_jsonb": None,
        "contradicts_signals_array": contradictions,
        "valence": valence,
        "classical_sources_jsonb": {"rule_ids": ["rule-1"]},
    }


def test_resonance_is_invariant_to_l3_dasha_input():
    base = ResonanceInputs(shadbala_normalized=0.25, dasha_proximity_activation_score=0.0)
    temporally_claimed = ResonanceInputs(
        shadbala_normalized=0.25, dasha_proximity_activation_score=1.0,
    )
    unavailable = ResonanceInputs(
        shadbala_normalized=0.25, dasha_proximity_activation_score=None,
    )
    assert resonance_score_v1(base) == resonance_score_v1(temporally_claimed)
    assert resonance_score_v1(base) == resonance_score_v1(unavailable)


def test_cdlm_independence_uses_root_ancestry_and_dosha_is_not_automatically_negative():
    signals = [
        _signal("00000000-0000-0000-0000-000000000001", root="fact:shared"),
        _signal("00000000-0000-0000-0000-000000000002", root="fact:shared"),
    ]
    rows = _build_cdlm_cells(
        "00000000-0000-0000-0000-000000000010",
        "lahiri_chitrapaksha",
        "00000000-0000-0000-0000-000000000020",
        signals,
        set(),
        "2026-09-14T00:00:00+00:00",
    )
    cell = next(row for row in rows if row["domain_row"] == "career" and row["domain_col"] == "wealth")
    assert cell["shared_signal_count"] == 2
    assert cell["shared_factor_count"] == 1
    assert json.loads(cell["shared_factor_keys_jsonb"])["shared_root_groups"] == ["fact:shared"]
    assert cell["negative_contribution"] == 0
    assert cell["cross_domain_contradiction_flag"] is False

    signals[0]["contradicts_signals_array"] = [signals[1]["signal_id"]]
    qualified = _build_cdlm_cells(
        "00000000-0000-0000-0000-000000000010",
        "lahiri_chitrapaksha",
        "00000000-0000-0000-0000-000000000020",
        signals,
        set(),
        "2026-09-14T00:00:00+00:00",
    )[0]
    assert qualified["negative_contribution"] > 0
    assert qualified["cross_domain_contradiction_flag"] is True


def test_quality_detectors_have_reachable_false_branches(monkeypatch):
    def violations(_conn, sql, _params):
        if "bodha_question_lenses" in sql:
            return 1
        if "bodha_cdlm_cells" in sql:
            return 2
        if "bodha_discoveries" in sql:
            return 3
        if "l2_data_plane_row_snapshots" in sql:
            return 4
        if "bodha_cgm_edges" in sql:
            return 5
        raise AssertionError(sql)

    monkeypatch.setattr(bo_pramana_mapa, "_count_one", violations)
    result = bo_pramana_mapa.detect_l2_contract_integrity(object(), "chart-1")
    assert result["no_pre_answer"]["pass"] is False
    assert result["ledger_independence_and_duplicate_root"]["pass"] is False
    assert result["discovery_grounding"]["pass"] is False
    assert result["context_generation"]["pass"] is False
    assert result["signed_relation_and_cancellation"]["pass"] is False


def test_lel_detector_is_self_contained_and_serving_refresh_is_passive():
    assert "life_events" not in bo_pramana_mapa._LEL_TERM_B_SQL
    assert "source_l1_asset" in bo_pramana_mapa._LEL_TERM_B_SQL
    run_source = inspect.getsource(bo_pramana_mapa.BoPramanaMapa.run)
    assert "_refresh_mv(" not in run_source
    assert "mv_cdlm_dasha_window_lookup" not in run_source


def test_samvada_preserves_serving_view_without_ddl():
    class Conn:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params=None):
            self.calls.append((sql, params))

    conn = Conn()
    result = bo_samvada.BoSamvadaWriter().run(SimpleNamespace(
        dry_run=False, db_conn=conn, config={}, build_id="test-build",
    ))
    assert result.rows_inserted == 0
    assert result.rows_skipped == 1
    assert conn.calls == []


def test_samskara_reuse_is_immutable_and_partial_batches_fail_closed():
    reuse_source = inspect.getsource(bo_samskara._fetch_existing_embeddings)
    assert "l2_data_plane_row_snapshots" in reuse_source
    assert "l2_data_plane_generation_is_compatible" in reuse_source
    run_source = inspect.getsource(bo_samskara.BoSamskaraWriter.run_substep)
    assert "refusing a partial generation" in run_source


def _pratijna_score(status: str):
    return SimpleNamespace(
        status=status,
        rubric_version="rubric-v1",
        occurrence_label="MODERATE",
        condition_label="AFFLICTED",
        occurrence_pre_denial=0.5,
        occurrence=0.5,
        condition=2.0,
        engine_version="engine-v1",
        weights={},
        factor_ledger=[],
        denials=[],
        condition_ledger=[],
        provenance={},
    )


def test_pratijna_persists_units_and_polarities_for_value_and_missingness():
    for status in ("scored", "no_evidence"):
        row = bo_pratijna._row_for_score(
            chart_id="chart", aya="lahiri", build_id="build",
            event_class_id="event", score=_pratijna_score(status), now="now",
        )
        derivation = json.loads(row["derivation"])
        assert derivation["occurrence_unit"] == "probability_like_structural_score_0_1"
        assert derivation["occurrence_polarity"] == "higher_is_more_formed"
        assert derivation["condition_unit"] == "affliction_0_10"
        assert derivation["condition_polarity"] == "higher_is_more_afflicted"
