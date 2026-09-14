from __future__ import annotations

import json

from bodha_writers.formulas import ResonanceInputs, resonance_score_v1
from pipeline.orchestrator.writers import bo_pramana_mapa
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
