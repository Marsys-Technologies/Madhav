"""Source-contract locks for the two service assets without probe contracts.

These tests do not touch a database. They prevent the reviewed contract ledger
from silently drifting away from the frozen writer behavior; disposable database
effect tests remain a separate Wave 1 gate.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = json.loads(
    (ROOT / "python-sidecar/scripts/nirmana_service_effect_contracts.json").read_text()
)["contracts"]


def test_mi_seva_readiness_contract_matches_source() -> None:
    contract = CONTRACTS["mi_seva"]
    source = (ROOT / "python-sidecar/pipeline/orchestrator/writers/mi_seva.py").read_text()

    assert contract["contract_kind"] == "readiness_read"
    assert contract["writes"] == []
    assert contract["required_public_relations"] == sorted(
        [
            "mimamsa_multipliers",
            "mimamsa_signal_adjustment",
            "mimamsa_insight_units",
            "mimamsa_journal",
        ]
    )
    assert all(f'"{relation}"' in source for relation in contract["required_public_relations"])
    assert "raise RuntimeError(" in source
    assert "rows_inserted=0" in source


def test_mi_abhilekha_effect_contract_matches_source_and_stays_unratified() -> None:
    contract = CONTRACTS["mi_abhilekha"]
    source = (ROOT / "python-sidecar/pipeline/orchestrator/writers/mi_abhilekha.py").read_text()

    assert contract["contract_kind"] == "fixture_scoped_effect"
    assert contract["authority_state"] == "source_observed_unratified"
    assert contract["execution_boundary"] == "disposable_fixture_only_until_product_review"
    assert contract["selection"]["prediction_match"] == ["chart_id", "prediction_id"]
    assert contract["selection"]["prediction_prior_lifecycle_status"] == "pending"
    assert contract["observed_classification"]["denied_otherwise"] is True

    for fragment in (
        "j.answered_at IS NOT NULL",
        "j.resulting_event_id IS NOT NULL",
        '"confirmed" if "yes" in answer or "confirmed" in answer else "denied"',
        "WHERE chart_id = %s AND prediction_id = %s",
        "AND lifecycle_status = 'pending'",
    ):
        assert fragment in source


def test_contract_inventory_is_exact() -> None:
    assert sorted(CONTRACTS) == ["mi_abhilekha", "mi_seva"]
