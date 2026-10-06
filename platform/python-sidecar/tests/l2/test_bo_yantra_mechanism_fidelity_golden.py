"""Golden-value fidelity test for bo_yantra_mechanism mechanism_name and citation_human.

The tenancy-affliction composer is DB-bound, so it is driven with a stub connection that only serves the
chart_facts rows; no database is touched.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_yantra_mechanism import _detect_tenancy_afflictions


class _StubCursor:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __enter__(self) -> "_StubCursor":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, sql: str, params: list) -> None:
        pass

    def fetchall(self) -> list[dict]:
        return self._rows


class _StubConn:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def cursor(self) -> _StubCursor:
        return _StubCursor(self._rows)


def test_tenancy_mechanism_name_and_citation_human_golden() -> None:
    # Rahu in Taurus (its exaltation sign by the doctrine's node convention) in the 2nd house.
    # natural -1.0 (malefic) and dignity +0.5 (exalted): malefic 1.0, benefic 0.5, net -0.5, both
    # components >= 0.4 so the verdict is mixed.
    facts = [
        {"fact_subject": "RAH_MEAN", "fact_key": "house_d1", "fact_value_text": None, "fact_value_num": 2},
        {"fact_subject": "RAH_MEAN", "fact_key": "sign", "fact_value_text": "TAURUS", "fact_value_num": None},
    ]
    nodes_by_id = {
        "g-rahu": {"node_type": "graha", "node_subject": "RAH_MEAN"},
        "b-2": {"node_type": "bhava", "node_subject": "2"},
    }
    rows = _detect_tenancy_afflictions(
        _StubConn(facts), "chart-x", "lahiri", "build-x", "2026-01-01T00:00:00+00:00", nodes_by_id)
    assert len(rows) == 1
    row = rows[0]
    built = {"mechanism_name": row["mechanism_name"], "citation_human": row["citation_human"]}
    assert built == {
        "mechanism_name": "Rahu occupies dhana (2nd) bhāva (mixed)",
        "citation_human": (
            "Rahu (TAURUS) tenants the dhana (2nd) bhāva — valence mixed (net -0.50); "
            "natural -1.0, dignity +0.50"
        ),
    }
