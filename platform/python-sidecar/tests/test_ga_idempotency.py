"""Double-run idempotency tests for the L1 Gaṇita writers.

Proves that the `replace_prior_*` helpers (called at the top of every writer's
insert path) make a rebuild under a fresh build_id REPLACE the chart's rows rather
than accrete a second copy — the bug that produced the 13-build chart_facts /
7-build chart_dashas bloat.

These are pure unit tests (no DB): a `FakeConn` backs an in-memory store keyed by
the *real* unique key (which includes build_id), so without the helper a second
build would double the row count. The tests call the real helper, then simulate the
writer's INSERT, and assert the store holds the single-run count.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers._idempotency import (  # noqa: E402
    replace_prior_chart_facts,
    replace_prior_chart_dashas,
    replace_prior_chart_divisionals,
    clear_table_for_chart,
)


class _Cursor:
    def __init__(self, rowcount):
        self.rowcount = rowcount


class FakeConn:
    """Backs an in-memory list of row dicts; interprets exactly the DELETE shapes the
    helpers emit so the real helper code path is exercised."""

    def __init__(self, table, rows=None):
        self.table = table
        self.rows = list(rows or [])

    def execute(self, sql, params):
        sql = " ".join(sql.split())
        assert sql.startswith(f"DELETE FROM {self.table} WHERE chart_id = %s"), sql
        chart_id = params[0]
        if "AND " not in sql:  # whole-chart delete (clear_table_for_chart)
            before = len(self.rows)
            self.rows = [r for r in self.rows if r["chart_id"] != chart_id]
            return _Cursor(before - len(self.rows))
        # second predicate column: fact_category / system_id / varga
        col = sql.split("AND ", 1)[1].split(" = ANY", 1)[0].strip()
        allowed = set(params[1])
        ayan = set(params[2]) if "ayanamsha_id = ANY" in sql else None

        def matches(r):
            if r["chart_id"] != chart_id:
                return False
            if r.get(col) not in allowed:
                return False
            if ayan is not None and r.get("ayanamsha_id") not in ayan:
                return False
            return True

        before = len(self.rows)
        self.rows = [r for r in self.rows if not matches(r)]
        return _Cursor(before - len(self.rows))

    # Simulate the writer INSERT honouring the real unique key (incl build_id).
    def insert(self, rows, key):
        seen = {tuple(r[k] for k in key) for r in self.rows}
        for r in rows:
            t = tuple(r[k] for k in key)
            if t not in seen:
                self.rows.append(r)
                seen.add(t)

    def count(self, chart_id):
        return sum(1 for r in self.rows if r["chart_id"] == chart_id)


CID = "482012f1-710e-4a25-994a-93821f5871aa"
CF_KEY = ("chart_id", "ayanamsha_id", "fact_category", "fact_subject", "fact_key", "build_id")
AYANAMSHAS = ["lahiri_chitrapaksha", "raman"]


def _facts(build_id, categories=("sade_sati_cycle", "sade_sati_phase")):
    rows = []
    for ay in AYANAMSHAS:
        for cat in categories:
            for subj in ("A", "B"):
                rows.append({
                    "chart_id": CID, "ayanamsha_id": ay, "fact_category": cat,
                    "fact_subject": subj, "fact_key": "k", "build_id": build_id,
                })
    return rows


def _run_facts_build(conn, rows):
    replace_prior_chart_facts(conn, rows)   # the writer's idempotency step
    conn.insert(rows, CF_KEY)               # the writer's INSERT


def test_chart_facts_double_run_replaces_not_accretes():
    conn = FakeConn("chart_facts")
    _run_facts_build(conn, _facts("build-1"))
    single = conn.count(CID)
    assert single == 8  # 2 ayanamshas × 2 cats × 2 subjects
    _run_facts_build(conn, _facts("build-2"))   # fresh build_id
    assert conn.count(CID) == single            # replaced, not 16
    assert {r["build_id"] for r in conn.rows} == {"build-2"}


def test_chart_facts_without_helper_would_double():
    """Control: skipping the helper accretes — proves the helper is what fixes it."""
    conn = FakeConn("chart_facts")
    conn.insert(_facts("build-1"), CF_KEY)
    conn.insert(_facts("build-2"), CF_KEY)
    assert conn.count(CID) == 16


def test_chart_facts_writers_do_not_delete_each_others_categories():
    """Two writers with disjoint categories: rebuilding one leaves the other intact."""
    conn = FakeConn("chart_facts")
    writer_a = _facts("build-1", categories=("sade_sati_cycle",))
    writer_b = _facts("build-1", categories=("aspect_jaimini",))
    conn.insert(writer_a, CF_KEY)
    conn.insert(writer_b, CF_KEY)
    assert conn.count(CID) == 8
    # rebuild only writer A under a new build
    _run_facts_build(conn, _facts("build-2", categories=("sade_sati_cycle",)))
    assert conn.count(CID) == 8  # A replaced (4), B untouched (4)
    cats = {r["fact_category"] for r in conn.rows}
    assert cats == {"sade_sati_cycle", "aspect_jaimini"}


def test_chart_facts_per_ayanamsha_calls_do_not_wipe_siblings():
    """sade_sati inserts per-ayanamsha; an ayanamsha's call must not wipe the one
    written just before it in the same build."""
    conn = FakeConn("chart_facts")
    for ay in AYANAMSHAS:
        rows = [r for r in _facts("build-1") if r["ayanamsha_id"] == ay]
        _run_facts_build(conn, rows)
    assert conn.count(CID) == 8  # both ayanamshas survive


def test_chart_dashas_double_run_replaces():
    conn = FakeConn("chart_dashas")
    key = ("chart_id", "ayanamsha_id", "system_id", "level_n", "start_iso", "build_id")

    def dashas(build_id):
        return [{"chart_id": CID, "ayanamsha_id": "lahiri_chitrapaksha",
                 "system_id": "vimshottari", "level_n": 1, "start_iso": f"d{i}",
                 "build_id": build_id} for i in range(5)]

    replace_prior_chart_dashas(conn, dashas("b1")); conn.insert(dashas("b1"), key)
    assert conn.count(CID) == 5
    replace_prior_chart_dashas(conn, dashas("b2")); conn.insert(dashas("b2"), key)
    assert conn.count(CID) == 5


def test_chart_divisionals_double_run_replaces():
    conn = FakeConn("chart_divisionals")
    key = ("chart_id", "ayanamsha_id", "varga", "graha", "fact_category", "fact_key")

    def divs(build_id):
        return [{"chart_id": CID, "ayanamsha_id": "lahiri_chitrapaksha", "varga": "D9",
                 "graha": g, "fact_category": "varga_position", "fact_key": "sign",
                 "build_id": build_id} for g in ("Sun", "Moon")]

    replace_prior_chart_divisionals(conn, divs("b1")); conn.insert(divs("b1"), key)
    assert conn.count(CID) == 2
    replace_prior_chart_divisionals(conn, divs("b2")); conn.insert(divs("b2"), key)
    assert conn.count(CID) == 2


def test_clear_table_for_chart_scopes_to_chart():
    conn = FakeConn("ganita_positions", rows=[
        {"chart_id": CID, "planet": "Sun"},
        {"chart_id": "other", "planet": "Sun"},
    ])
    # clear_table_for_chart emits: DELETE FROM ganita_positions WHERE chart_id = %s
    deleted = clear_table_for_chart(conn, "ganita_positions", CID)
    assert deleted == 1
    assert conn.count(CID) == 0
    assert any(r["chart_id"] == "other" for r in conn.rows)


def test_helpers_noop_on_empty():
    conn = FakeConn("chart_facts")
    assert replace_prior_chart_facts(conn, []) == 0
    assert replace_prior_chart_dashas(conn, []) == 0
    assert replace_prior_chart_divisionals(conn, []) == 0
