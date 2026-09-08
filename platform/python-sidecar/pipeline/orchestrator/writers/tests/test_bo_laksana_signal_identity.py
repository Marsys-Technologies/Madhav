"""bo_laksana must never write a random signal_id.

Nirmāṇa #1804 (D-NATIVE-05 action 8; D-CND-11 as amended by that ruling).

`signal_id` was `str(uuid.uuid4())` at three emit sites, so every rebuild minted
fresh identities for the same signals. That is the mechanism behind the orphaning
D-NATIVE-05 §5 assigns dispositions for: `bodha_triangulation` holds 143 dangling
references today — on the two HEALTHY charts, zero on the DAMAGED one (D-CND-17) —
because the array kept ids a later run replaced.

The identity itself is computed by `bodha_signal_identity()` (migration 660), the
single source of truth, and is verified against production in that migration's
dry-run: 150,150 rows / 150,150 distinct identities across all three charts, plus
determinism, jsonb key-order invariance, and NULL-vs-empty-varga distinctness.

These tests cover what that dry-run cannot: the WIRING. That the writer calls the
function, assigns the result back onto the row dicts, cannot be bypassed, and
reports collapses honestly.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "bo_laksana.py"


class _FakeCursor:
    """Returns a derived-looking id per row, echoing the input index.

    fetchall() returns DICT rows -- the production connection uses a dict_row
    factory, and mimicking tuples here is exactly how the 2026-09-08 TypeError
    (fixed in PR #2448) stayed invisible to this suite: the fake let the old
    tuple-unpacking loop pass while production crashed on its first real fetch.
    """

    def __init__(self, log: list) -> None:
        self._log = log
        self._rows: list[dict] = []

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, sql: str, params=None) -> None:
        self._log.append((sql, params))
        payload = json.loads(params[0])
        # Mimic bodha_signal_identity: a pure function of the identity tuple.
        # sort_keys mirrors jsonb's key-order normalisation, so a payload that
        # embeds the configuration OBJECT is order-invariant here just as it is
        # in Postgres -- while a pre-serialised string embedded by mistake stays
        # a string and derives a different id (see the double-encoding test).
        self._rows = [
            {
                "i": e["i"],
                "sid": "det-{}-{}-{}".format(
                    e["ayanamsha_id"], e["signal_type_id"], json.dumps(e["configuration_jsonb"], sort_keys=True)
                ),
            }
            for e in payload
        ]

    def fetchall(self):
        return self._rows


class _FakeConn:
    def __init__(self) -> None:
        self.log: list = []

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self.log)


def _row(sid, aya="lahiri", stype="t1", cfg=None, varga=None) -> dict:
    return {
        "signal_id": sid,
        "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
        "ayanamsha_id": aya,
        "signal_type_id": stype,
        "varga_id": varga,
        "configuration_jsonb": cfg if cfg is not None else {"fact_key": "x"},
    }


def test_assigns_the_database_derived_identity_onto_the_row() -> None:
    from pipeline.orchestrator.writers.bo_laksana import assign_deterministic_signal_ids

    conn = _FakeConn()
    rows = [_row(None), _row(None, stype="t2")]
    assign_deterministic_signal_ids(conn, rows)

    assert all(r["signal_id"].startswith("det-") for r in rows)
    assert rows[0]["signal_id"] != rows[1]["signal_id"]


def test_identity_comes_from_sql_not_reimplemented_in_python() -> None:
    """The function must be CALLED. A Python copy is free to drift from the SQL one.

    L4 made the same call on #1754, and a drifted identity function is
    indistinguishable from having none at all.
    """
    from pipeline.orchestrator.writers.bo_laksana import assign_deterministic_signal_ids

    conn = _FakeConn()
    assign_deterministic_signal_ids(conn, [_row(None)])
    sql = conn.log[0][0]
    assert "bodha_signal_identity(" in sql, "the writer must call the SQL identity function"
    assert SOURCE.read_text(encoding="utf-8").count("uuid_generate_v5") == 0, (
        "the identity algorithm must not be reimplemented in Python"
    )


def test_same_identity_tuple_yields_the_same_id_across_separate_calls() -> None:
    """Determinism at the wiring level: two runs, same inputs, same id."""
    from pipeline.orchestrator.writers.bo_laksana import assign_deterministic_signal_ids

    first, second = [_row(None)], [_row(None)]
    assign_deterministic_signal_ids(_FakeConn(), first)
    assign_deterministic_signal_ids(_FakeConn(), second)
    assert first[0]["signal_id"] == second[0]["signal_id"]


def test_reports_collapse_honestly_rather_than_assuming_none() -> None:
    """§N.8: two rows sharing a derived identity ARE the same signal — but say so."""
    from pipeline.orchestrator.writers.bo_laksana import assign_deterministic_signal_ids

    rows = [_row(None), _row(None)]  # identical identity tuples
    collapsed = assign_deterministic_signal_ids(_FakeConn(), rows)
    assert collapsed == 1
    assert assign_deterministic_signal_ids(_FakeConn(), [_row(None), _row(None, stype="t2")]) == 0


def test_preserialised_config_derives_the_same_id_as_the_object() -> None:
    """The identity payload must embed the configuration OBJECT, never the string.

    Emit sites store configuration_jsonb pre-serialised (json.dumps) for the
    INSERT's ::jsonb cast. Passing that string into the identity payload
    double-encodes it -- bodha_signal_identity then hashes Python's emit-order
    serialisation instead of the key-order-normalised jsonb object, so the
    stored signal_id is not derivable from the stored row (migration 661 PART 4;
    verified live on 150,280/150,280 rows, #2455). The writer must parse the
    string back to an object before deriving.
    """
    from pipeline.orchestrator.writers.bo_laksana import assign_deterministic_signal_ids

    as_object = [_row(None, cfg={"b": 1, "a": 2})]
    as_string = [_row(None, cfg=json.dumps({"a": 2, "b": 1}))]  # different key order too
    assign_deterministic_signal_ids(_FakeConn(), as_object)
    assign_deterministic_signal_ids(_FakeConn(), as_string)
    assert as_object[0]["signal_id"] == as_string[0]["signal_id"]


def test_no_emit_site_can_construct_a_random_signal_id() -> None:
    """The defect itself, guarded at the source.

    Three emit sites carried `str(uuid.uuid4())`. A fourth is easy to add by
    copy-paste, and it would reintroduce the orphan class silently — the row would
    look completely normal.
    """
    text = SOURCE.read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in text.splitlines()
        if "signal_id" in line and "uuid4" in line and not line.strip().startswith("#")
    ]
    assert offenders == [], f"signal_id must never be randomly generated: {offenders}"


def test_derivation_runs_on_the_single_insert_path_not_at_the_emit_sites() -> None:
    """Placement matters: emit sites multiply, the insert path does not."""
    text = SOURCE.read_text(encoding="utf-8")
    insert_at = text.index("def _batch_insert(")
    assign_at = text.index("assign_deterministic_signal_ids(conn, rows)", insert_at)
    inserted_at = text.index("inserted = 0", insert_at)
    assert assign_at < inserted_at, (
        "identities must be derived before any row is written"
    )
