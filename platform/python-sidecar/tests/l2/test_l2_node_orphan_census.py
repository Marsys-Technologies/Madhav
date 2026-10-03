"""
tests/l2/test_l2_node_orphan_census.py -- tests for scripts/l2_node_orphan_census.py

Track I item TI-L2-17 (orphan census core). No database: a small fake connection answers the
two kinds of statement the census issues. The census must find a stale arudha/special_lagna node
(its L1 fact is gone), must not look at node types another writer owns, must follow the
builder's own L1 reader rather than a copy, and must only ever read.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

SIDECAR = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "l2_node_orphan_census", SIDECAR / "scripts" / "l2_node_orphan_census.py")
census = importlib.util.module_from_spec(_spec)
sys.modules["l2_node_orphan_census"] = census
_spec.loader.exec_module(census)  # type: ignore[union-attr]

CHART = "00000000-0000-4000-8000-000000000001"
AYA = "lahiri_chitrapaksha"


class _Cur:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return list(self._rows)


class FakeConn:
    """Answers the builder's L1 fact read and the census's node read; records every statement."""

    def __init__(self, facts, nodes):
        self.facts = facts      # list of (fact_id, category, subject, key, text, num)
        self.nodes = nodes      # list of (ayanamsha, node_type, node_subject)
        self.statements: list[str] = []

    def execute(self, sql, params=None):
        self.statements.append(" ".join(sql.split()))
        if "FROM chart_facts" in sql:
            return _Cur([
                {"fact_id": f[0], "fact_category": f[1], "fact_subject": f[2], "fact_key": f[3],
                 "fact_value_text": f[4], "fact_value_num": f[5]}
                for f in self.facts
            ])
        if "FROM bodha_cgm_nodes" in sql:
            aya = params[1]
            # honour the SQL the way the database would: the type filter applies only if the
            # statement carries it
            types = params[3] if "node_type = ANY" in sql else None
            return _Cur([
                {"node_type": n[1], "node_subject": n[2]}
                for n in self.nodes if n[0] == aya and (types is None or n[1] in types)
            ])
        raise AssertionError(f"unexpected statement: {sql}")


def _arudha(i: int):
    return [(f"f{i}h", "arudha_pada", f"ARUDHA_A{i}", "house_d1", None, float(i)),
            (f"f{i}s", "arudha_pada", f"ARUDHA_A{i}", "sign", "leo", None)]


def _special(name: str):
    return [(f"s_{name}", "special_lagna", name, "house_d1", None, 4.0)]


FACTS = _arudha(1) + _arudha(5) + _special("GHATI_LAGNA")
NODES = [(AYA, "arudha", "A1"), (AYA, "arudha", "A5"), (AYA, "special_lagna", "GHATI_LAGNA")]


# -- pure comparison ---------------------------------------------------------

def test_compare_names_orphans_and_missing_sorted() -> None:
    out = census.compare_node_keys({("arudha", "A1"), ("arudha", "A2")}, {("arudha", "A1"), ("arudha", "A9"), ("arudha", "A3")})
    assert out == {"orphans": [("arudha", "A3"), ("arudha", "A9")], "missing": [("arudha", "A2")]}


def test_compare_identical_sets_is_clean() -> None:
    s = {("special_lagna", "GHATI_LAGNA")}
    assert census.compare_node_keys(s, set(s)) == {"orphans": [], "missing": []}


# -- census over the fake connection ----------------------------------------

def test_consistent_l1_and_nodes_pass() -> None:
    r = census.run_census(FakeConn(FACTS, NODES), CHART, (AYA,))
    assert r["passed"] is True
    assert r["totals"] == {"expected": 3, "live": 3, "orphans": 0, "missing": 0}


def test_a_removed_l1_arudha_fact_leaves_a_named_orphan() -> None:
    # failing-first case from the A.L2 design: the L1 fact for A5 is gone, its node is still live
    facts = _arudha(1) + _special("GHATI_LAGNA")
    r = census.run_census(FakeConn(facts, NODES), CHART, (AYA,))
    assert r["passed"] is False
    assert r["ayanamshas"][AYA]["orphans"] == [["arudha", "A5"]]
    assert r["totals"]["orphans"] == 1 and r["totals"]["missing"] == 0


def test_a_renamed_subject_is_an_orphan_and_a_missing_node() -> None:
    facts = _arudha(1) + _arudha(5) + _special("HORA_LAGNA")
    r = census.run_census(FakeConn(facts, NODES), CHART, (AYA,))
    assert r["ayanamshas"][AYA]["orphans"] == [["special_lagna", "GHATI_LAGNA"]]
    assert r["ayanamshas"][AYA]["missing"] == [["special_lagna", "HORA_LAGNA"]]
    assert r["passed"] is False


def test_an_unbuilt_node_is_missing_but_not_a_failure() -> None:
    r = census.run_census(FakeConn(FACTS, NODES[:2]), CHART, (AYA,))
    assert r["ayanamshas"][AYA]["missing"] == [["special_lagna", "GHATI_LAGNA"]]
    assert r["passed"] is True


def test_node_types_owned_by_other_writers_are_never_examined() -> None:
    nodes = NODES + [(AYA, "graha", "Sun"), (AYA, "yoga", "yoga:gola_yoga"), (AYA, "bhava", "1")]
    conn = FakeConn(FACTS, nodes)
    r = census.run_census(conn, CHART, (AYA,))
    assert r["passed"] is True and r["totals"]["live"] == 3


def test_each_ayanamsha_is_judged_on_its_own() -> None:
    nodes = NODES + [("raman", "arudha", "A7")]
    r = census.run_census(FakeConn(FACTS, nodes), CHART, (AYA, "raman"))
    assert r["ayanamshas"]["raman"]["orphans"] == [["arudha", "A7"]]
    assert r["ayanamshas"][AYA]["orphans"] == []


# -- the census follows the builder, not a copy -----------------------------

def test_expected_keys_come_from_the_writers_own_reader(monkeypatch) -> None:
    import pipeline.orchestrator.writers.bo_karanajala as writer
    monkeypatch.setattr(writer, "_fetch_arudha_special_lagna_facts",
                        lambda conn, c, a: {("arudha", "A12"): {}, ("graha", "Sun"): {}})
    assert census.expected_node_keys(object(), CHART, AYA) == {("arudha", "A12")}


def test_scope_assumptions_still_hold_in_the_writers() -> None:
    import pipeline.orchestrator.writers.bo_karanajala as writer
    from bodha_writers import _idempotency as idem
    assert census.SNAPSHOT_TYPE == writer.SNAPSHOT_TYPE

    class _Rec:
        params = None

        def execute(self, sql, params=None):
            if params is not None:
                _Rec.params = params
            return type("C", (), {"rowcount": 0})()

    idem.replace_prior_cgm_nodes(_Rec(), CHART, AYA, census.SNAPSHOT_TYPE)
    deleted_types = set(_Rec.params[-1])
    # the premise of the census: no writer deletes these node types
    assert not (deleted_types & set(census.CROSS_ASSET_NODE_TYPES)), deleted_types


# -- read-only, exit codes ---------------------------------------------------

def test_connection_is_forced_read_only(monkeypatch) -> None:
    seen = {}

    def fake_connect(url, **kw):
        seen.update(kw)
        raise RuntimeError("stop")

    import psycopg
    monkeypatch.setattr(psycopg, "connect", fake_connect)
    with pytest.raises(RuntimeError):
        census._connect_read_only("postgresql://x")
    assert "default_transaction_read_only=on" in seen["options"]


def test_the_census_issues_only_selects() -> None:
    conn = FakeConn(FACTS, NODES)
    census.run_census(conn, CHART, (AYA,))
    assert conn.statements and all(s.upper().startswith("SELECT") for s in conn.statements)


def _main_with(monkeypatch, facts, nodes, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    conn = FakeConn(facts, nodes)
    conn.rollback = lambda: None
    conn.close = lambda: None
    monkeypatch.setattr(census, "_connect_read_only", lambda url: conn)
    monkeypatch.setattr(census, "CANONICAL_AYAS", (AYA,))
    rc = census.main(["--chart-id", CHART])
    return rc, capsys.readouterr().out


def test_exit_0_on_pass_and_1_on_orphans_with_the_name_printed(monkeypatch, capsys) -> None:
    rc, out = _main_with(monkeypatch, FACTS, NODES, capsys)
    assert rc == 0 and "PASS" in out
    rc, out = _main_with(monkeypatch, _arudha(1) + _special("GHATI_LAGNA"), NODES, capsys)
    assert rc == 1 and "FAIL" in out and "ORPHAN" in out and "A5" in out


def test_exit_2_without_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert census.main(["--chart-id", CHART]) == 2
