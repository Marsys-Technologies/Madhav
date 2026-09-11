"""Regression coverage for shared-MSR writers' database-derived identities."""
from __future__ import annotations

import hashlib
import inspect
import json

import pytest


class _Result:
    def __init__(self, rows: list[dict[str, str | int]]) -> None:
        self._rows = rows

    def fetchall(self) -> list[dict[str, str | int]]:
        return self._rows


class _IdentityConn:
    """Records the authoritative SQL call and returns stable stand-in UUID text."""

    def __init__(self) -> None:
        self.sql: str | None = None
        self.payload: list[dict] | None = None

    def execute(self, sql: str, params: list[str]) -> _Result:
        self.sql = sql
        self.payload = json.loads(params[0])
        ids = []
        for entry in self.payload:
            # Mirror the SQL identity inputs: the payload's positional `i` is
            # only for assigning returned IDs to rows and is not identity.
            stable_key = json.dumps(
                {key: value for key, value in entry.items() if key != "i"},
                sort_keys=True,
                separators=(",", ":"),
            )
            ids.append({"i": entry["i"], "sid": hashlib.sha256(stable_key.encode()).hexdigest()})
        return _Result(ids)


_ASSIGNERS = [
    pytest.param(
        "pipeline.orchestrator.writers.bo_vargottama_dhana",
        "BoVargottamaDhanaWriter",
        "bodha_writers.vargottama_dhana_emitter",
        id="vargottama_dhana",
    ),
    pytest.param(
        "pipeline.orchestrator.writers.bo_nakshatra_semantic",
        "BoNakshatraSemanticWriter",
        "bodha_writers.nakshatra_semantic_emitter",
        id="nakshatra_semantic",
    ),
    pytest.param(
        "pipeline.orchestrator.writers.bo_special_lagna",
        "BoSpecialLagnaWriter",
        "bodha_writers.special_lagna_emitter",
        id="special_lagna",
    ),
]


def _rows() -> list[dict]:
    return [
        {
            "signal_id": "legacy-random-id",
            "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
            "ayanamsha_id": "lahiri_chitrapaksha",
            "signal_type_id": "test:one",
            "varga_id": "D1",
            "configuration_jsonb": '{"z":2,"a":1}',
        },
        {
            "signal_id": None,
            "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
            "ayanamsha_id": "lahiri_chitrapaksha",
            "signal_type_id": "test:two",
            "varga_id": "D9",
            "configuration_jsonb": {"a": 2},
        },
    ]


@pytest.mark.parametrize("module_name,writer_name,emitter_module_name", _ASSIGNERS)
def test_assigner_uses_authoritative_sql_and_is_stable(
    module_name: str,
    writer_name: str,
    emitter_module_name: str,
) -> None:
    module = __import__(module_name, fromlist=["assign_deterministic_signal_ids"])

    first_rows = _rows()
    first_conn = _IdentityConn()
    assert module.assign_deterministic_signal_ids(first_conn, first_rows) == 0

    assert first_conn.sql is not None
    assert "bodha_signal_identity" in first_conn.sql
    assert "jsonb_array_elements" in first_conn.sql
    assert first_conn.payload is not None
    assert first_conn.payload[0]["configuration_jsonb"] == {"z": 2, "a": 1}
    assert all(row["signal_id"] and row["signal_id"] != "legacy-random-id" for row in first_rows)

    second_rows = _rows()
    second_conn = _IdentityConn()
    assert module.assign_deterministic_signal_ids(second_conn, second_rows) == 0
    assert [row["signal_id"] for row in first_rows] == [row["signal_id"] for row in second_rows]

    run_source = inspect.getsource(getattr(module, writer_name).run)
    assert run_source.index("assign_deterministic_signal_ids(conn, rows)") < run_source.index(
        "replace_prior_msr_for_chart("
    ) < run_source.index("conn.execute(_INSERT_SQL, row)")

    emitter_module = __import__(emitter_module_name, fromlist=["__name__"])
    assert "uuid.uuid4" not in inspect.getsource(emitter_module)


@pytest.mark.parametrize("module_name,writer_name,emitter_module_name", _ASSIGNERS)
def test_assigner_reports_collapsed_duplicate_identities(
    module_name: str,
    writer_name: str,
    emitter_module_name: str,
) -> None:
    del writer_name, emitter_module_name
    module = __import__(module_name, fromlist=["assign_deterministic_signal_ids"])
    rows = _rows()
    duplicate = dict(rows[0])
    duplicate["signal_id"] = None
    rows.append(duplicate)

    assert module.assign_deterministic_signal_ids(_IdentityConn(), rows) == 1
    assert rows[0]["signal_id"] == rows[2]["signal_id"]
