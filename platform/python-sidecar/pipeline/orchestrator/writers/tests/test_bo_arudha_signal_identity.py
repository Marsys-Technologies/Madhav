"""bo_arudha must never write a random signal_id.

Nirmana #1770/#1804 (CONDUCTOR ruling on #2524/#2535, 2026-09-09): `signal_id`
was `str(uuid.uuid4())` at the emit site (bodha_writers.arudha_emitter.
_make_row), so every rebuild minted fresh identities for the same signals --
the exact CASCADE/orphan hazard #1770 already ruled on for any
`bodha_msr_signals` writer, and the same defect class bo_laksana fixed first
under #1804.

The identity itself is computed by `bodha_signal_identity()` (migration 660),
the single source of truth, and is never reimplemented here.

These tests cover what a migration dry-run cannot: the WIRING. That the
writer calls the function, assigns the result back onto the row dicts,
cannot be bypassed, and reports collapses honestly. Mirrors
test_bo_bimba_node_identity.py's shape (conn.execute(...).fetchall(), not
test_bo_laksana_signal_identity's cursor-based one) -- bo_arudha.py's own
emitter module already calls conn.execute() directly elsewhere
(_fetch_arudha_facts / _fetch_graha_houses).
"""
from __future__ import annotations

import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "bo_arudha.py"
EMITTER_SOURCE = Path(__file__).resolve().parents[4] / "bodha_writers" / "arudha_emitter.py"


class _FakeConn:
    """Returns a derived-looking id per row, echoing the input index."""

    def __init__(self) -> None:
        self.log: list = []
        self._rows: list[dict] = []

    def execute(self, sql: str, params=None) -> "_FakeConn":
        self.log.append((sql, params))
        payload = json.loads(params[0])
        # Mimic bodha_signal_identity: a pure function of the identity tuple.
        # sort_keys mirrors jsonb's key-order normalisation.
        self._rows = [
            {
                "i": e["i"],
                "sid": "det-{}-{}-{}".format(
                    e["ayanamsha_id"], e["signal_type_id"], json.dumps(e["configuration_jsonb"], sort_keys=True)
                ),
            }
            for e in payload
        ]
        return self

    def fetchall(self):
        return self._rows


def _row(sid, aya="lahiri", stype="arudha:AL_bhava_relation", cfg=None, varga="D1") -> dict:
    return {
        "signal_id": sid,
        "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
        "ayanamsha_id": aya,
        "signal_type_id": stype,
        "varga_id": varga,
        "configuration_jsonb": cfg if cfg is not None else json.dumps({"al_house": 9}),
    }


def test_assigns_the_database_derived_identity_onto_the_row() -> None:
    from pipeline.orchestrator.writers.bo_arudha import assign_deterministic_signal_ids

    conn = _FakeConn()
    rows = [_row(None), _row(None, stype="arudha:AL_conjunction:JUP")]
    assign_deterministic_signal_ids(conn, rows)

    assert all(r["signal_id"].startswith("det-") for r in rows)
    assert rows[0]["signal_id"] != rows[1]["signal_id"]


def test_identity_comes_from_sql_not_reimplemented_in_python() -> None:
    """The function must be CALLED. A Python copy is free to drift from the SQL one."""
    from pipeline.orchestrator.writers.bo_arudha import assign_deterministic_signal_ids

    conn = _FakeConn()
    assign_deterministic_signal_ids(conn, [_row(None)])
    sql = conn.log[0][0]
    assert "bodha_signal_identity(" in sql, "the writer must call the SQL identity function"
    assert SOURCE.read_text(encoding="utf-8").count("uuid_generate_v5") == 0, (
        "the identity algorithm must not be reimplemented in Python"
    )


def test_same_identity_tuple_yields_the_same_id_across_separate_calls() -> None:
    """Determinism at the wiring level: two runs, same inputs, same id."""
    from pipeline.orchestrator.writers.bo_arudha import assign_deterministic_signal_ids

    first, second = [_row(None)], [_row(None)]
    assign_deterministic_signal_ids(_FakeConn(), first)
    assign_deterministic_signal_ids(_FakeConn(), second)
    assert first[0]["signal_id"] == second[0]["signal_id"]


def test_reports_collapse_honestly_rather_than_assuming_none() -> None:
    """Two rows sharing a derived identity ARE the same signal -- but say so."""
    from pipeline.orchestrator.writers.bo_arudha import assign_deterministic_signal_ids

    rows = [_row(None), _row(None)]  # identical identity tuples
    collapsed = assign_deterministic_signal_ids(_FakeConn(), rows)
    assert collapsed == 1
    assert assign_deterministic_signal_ids(
        _FakeConn(), [_row(None), _row(None, stype="arudha:AL_conjunction:JUP")]
    ) == 0


def test_preserialised_config_derives_the_same_id_as_the_object() -> None:
    """The identity payload must embed the configuration OBJECT, never the string.

    _make_row() stores configuration_jsonb pre-serialised (json.dumps) for the
    INSERT's ::jsonb cast. Passing that string into the identity payload
    double-encodes it -- the writer must parse the string back to an object
    before deriving.
    """
    from pipeline.orchestrator.writers.bo_arudha import assign_deterministic_signal_ids

    as_object = [_row(None, cfg={"b": 1, "a": 2})]
    as_string = [_row(None, cfg=json.dumps({"a": 2, "b": 1}))]  # different key order too
    assign_deterministic_signal_ids(_FakeConn(), as_object)
    assign_deterministic_signal_ids(_FakeConn(), as_string)
    assert as_object[0]["signal_id"] == as_string[0]["signal_id"]


def test_no_emit_site_can_construct_a_random_signal_id() -> None:
    """The defect itself, guarded at the source (both the writer and the emitter
    module it calls into -- the emit site actually lives in arudha_emitter.py,
    not bo_arudha.py)."""
    for source in (SOURCE, EMITTER_SOURCE):
        text = source.read_text(encoding="utf-8")
        offenders = [
            line.strip()
            for line in text.splitlines()
            if "signal_id" in line and "uuid4" in line and not line.strip().startswith("#")
        ]
        assert offenders == [], f"{source.name}: signal_id must never be randomly generated: {offenders}"


def test_derivation_runs_before_the_insert_loop() -> None:
    """Placement matters: identities must be derived before any row is written."""
    text = SOURCE.read_text(encoding="utf-8")
    assign_at = text.index("assign_deterministic_signal_ids(conn, rows)", text.index("def run("))
    insert_loop_at = text.index("conn.execute(_INSERT_SQL, row)")
    assert assign_at < insert_loop_at, (
        "identities must be derived before any row is written"
    )
