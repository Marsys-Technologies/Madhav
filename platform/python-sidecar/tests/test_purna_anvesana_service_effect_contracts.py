"""Source-contract locks for the two service assets without probe contracts.

These tests do not touch a database. They prevent the reviewed contract ledger
from silently drifting away from the frozen writer behavior; disposable database
effect tests remain a separate Wave 1 gate.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers.mi_abhilekha import MiAbhilekhaWriter
from pipeline.orchestrator.writers.mi_seva import MiSevaWriter


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
    assert (ROOT.parent / contract["disposable_fixture_evidence"]).is_file()


def test_mi_abhilekha_effect_contract_matches_source_and_stays_unratified() -> None:
    contract = CONTRACTS["mi_abhilekha"]
    source = (ROOT / "python-sidecar/pipeline/orchestrator/writers/mi_abhilekha.py").read_text()

    assert contract["contract_kind"] == "fixture_scoped_effect"
    assert contract["authority_state"] == "source_observed_unratified"
    assert contract["execution_boundary"] == "disposable_fixture_only_until_product_review"
    assert contract["selection"]["prediction_match"] == ["chart_id", "prediction_id"]
    assert contract["selection"]["prediction_prior_lifecycle_status"] == "pending"
    assert contract["observed_classification"]["denied_otherwise"] is True
    assert (ROOT.parent / contract["disposable_fixture_evidence"]).is_file()

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


class _Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.rowcount = 0
        self._one = None
        self._many = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        normalized = " ".join(sql.split())
        self.connection.queries.append((normalized, params))
        if "information_schema.tables" in normalized:
            self._one = (1,) if params[0] in self.connection.present_tables else None
        elif "COUNT(*) AS total" in normalized:
            rows = self.connection.journal
            self._one = {
                "total": len(rows),
                "answered": sum(row["answered_at"] is not None for row in rows),
                "linked": sum(row["resulting_event_id"] is not None for row in rows),
            }
        elif normalized.startswith("SELECT j.chart_id"):
            self._many = [
                {key: row[key] for key in ("chart_id", "prediction_id", "resulting_event_id", "native_answer")}
                for row in self.connection.journal
                if row["answered_at"] is not None and row["resulting_event_id"] is not None
            ]
        elif normalized.startswith("UPDATE mimamsa_predictions"):
            new_status, chart_id, prediction_id = params
            key = (chart_id, prediction_id)
            self.rowcount = int(self.connection.predictions.get(key) == "pending")
            if self.rowcount:
                self.connection.predictions[key] = new_status

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._many


class _Connection:
    def __init__(self, *, present_tables=(), journal=(), predictions=None):
        self.present_tables = set(present_tables)
        self.journal = list(journal)
        self.predictions = dict(predictions or {})
        self.queries = []

    def cursor(self, **_kwargs):
        return _Cursor(self)


def test_mi_seva_contract_executes_fail_closed_without_writes() -> None:
    required = CONTRACTS["mi_seva"]["required_public_relations"]
    connection = _Connection(present_tables=required)
    result = MiSevaWriter().run(SimpleNamespace(db_conn=connection))
    assert result.rows_inserted == 0
    assert all(query.startswith("SELECT 1 FROM information_schema.tables") for query, _ in connection.queries)

    missing = _Connection(present_tables=required[:-1])
    with pytest.raises(RuntimeError, match="required service tables absent"):
        MiSevaWriter().run(SimpleNamespace(db_conn=missing))


def test_mi_abhilekha_effect_is_chart_scoped_pending_only_and_idempotent() -> None:
    journal = [
        {"chart_id": "chart-a", "prediction_id": "p1", "resulting_event_id": "e1", "native_answer": "YES", "answered_at": "now"},
        {"chart_id": "chart-b", "prediction_id": "p1", "resulting_event_id": "e2", "native_answer": "no", "answered_at": "now"},
        {"chart_id": "chart-a", "prediction_id": "p2", "resulting_event_id": "e3", "native_answer": "confirmed", "answered_at": "now"},
        {"chart_id": "chart-a", "prediction_id": "p3", "resulting_event_id": None, "native_answer": "yes", "answered_at": "now"},
    ]
    connection = _Connection(
        journal=journal,
        predictions={
            ("chart-a", "p1"): "pending",
            ("chart-b", "p1"): "pending",
            ("chart-a", "p2"): "pending",
            ("chart-a", "p3"): "confirmed",
        },
    )
    context = SimpleNamespace(db_conn=connection)

    first = MiAbhilekhaWriter().run(context)
    assert first.rows_inserted == 3
    assert connection.predictions == {
        ("chart-a", "p1"): "confirmed",
        ("chart-b", "p1"): "denied",
        ("chart-a", "p2"): "confirmed",
        ("chart-a", "p3"): "confirmed",
    }

    second = MiAbhilekhaWriter().run(context)
    assert second.rows_inserted == 0
    update_queries = [query for query, _ in connection.queries if query.startswith("UPDATE mimamsa_predictions")]
    assert update_queries
    assert all("WHERE chart_id = %s AND prediction_id = %s AND lifecycle_status = 'pending'" in query for query in update_queries)
