"""NODE-SERIES step 1 (SS N-68/N-69), PR B: P4 `ka_kota_chakra` reads the TRUE node series, pinned and loud.

`services/ka_kota_chakra/writer.py::_fetch_daily_nak_idx_by_graha` reads `ephemeris_daily` for the nine grahas. Unpinned,
a second (MEAN) Rahu/Ketu row set would hand it TWO `(date, nak_idx)` entries per date for each node, with an undefined
`ORDER BY body, date` tie and a nakshatra that flips between TRUE and MEAN: spurious or doubled Kota windows, SILENTLY.

What is proved here (the real-PostgreSQL proof over TRUE vs TRUE+MEAN lives in tests/test_node_series_readers_ignore_mean_rows.py):
  * the statement carries `NODE_SERIES_PREDICATE` (NULL-safe) and is otherwise the old statement;
  * GOLDEN: on today's TRUE-only rows the fetch returns exactly what the pre-change fetch returned (a verbatim copy of the old
    body below, run on the same rows);
  * LOUD: two rows for one (node, date), a node with no row, and a hole in a node's dates raise `NodeSeriesError` (the node
    series is REQUIRED); a hole in a NON-node body keeps the writer's own graceful refusal;
  * through the writer: a duplicate node date raises BEFORE anything is deleted or inserted.
"""
from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

import pytest

import services.ka_kota_chakra.writer as kota
from services.w2g.node_series import NODE_SERIES_PREDICATE, NodeSeriesError

START = date(2026, 7, 1)
END = date(2026, 7, 20)
DAYS = [START + timedelta(days=i) for i in range((END - START).days + 1)]
OFFSET = 23.9
_BASE = {"Sun": 98.0, "Moon": 50.0, "Mars": 150.0, "Mercury": 120.0, "Jupiter": 90.0, "Venus": 140.0,
         "Saturn": 20.0, "Rahu": 330.0, "Ketu": 150.0}
_SPEED = {"Sun": 0.9856, "Moon": 13.176, "Mars": 0.52, "Mercury": 1.1, "Jupiter": 0.08, "Venus": 1.2,
          "Saturn": 0.03, "Rahu": -0.0529, "Ketu": -0.0529}


def _rows(skip=(), extra=()):
    """Dict rows as the orchestrator's dict_row connection returns them (date, body, tropical_longitude)."""
    out = []
    for body in kota.ALL_GRAHAS:                           # ORDER BY body, date is the SQL's; the fetch does not depend on it
        for i, d in enumerate(DAYS):
            if (body, d) in skip:
                continue
            out.append({"date": d, "body": body, "tropical_longitude": (_BASE[body] + _SPEED[body] * i) % 360.0})
    out.extend(extra)
    return out


class _Cursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def execute(self, sql, params=None):
        self.conn.calls.append(("execute", str(sql), params))

    def executemany(self, sql, params):
        self.conn.calls.append(("executemany", str(sql), list(params)))

    def fetchall(self):
        return list(self.conn.rows)


class _Conn:
    def __init__(self, rows):
        self.rows = rows
        self.calls: list = []

    def cursor(self, *_a, **_k):
        return _Cursor(self)

    @property
    def mutations(self):
        return [c for c in self.calls if c[0] == "executemany" or c[1].lstrip().upper().startswith(("DELETE", "INSERT", "UPDATE"))]


def _old_fetch(conn, horizon_start, horizon_end, offset):
    """VERBATIM copy of the pre-change body of `_fetch_daily_nak_idx_by_graha` (everything after the fetch)."""
    rows = conn.rows
    by_graha = {g: [] for g in kota.ALL_GRAHAS}
    for r in rows:
        graha = r["body"]
        if graha not in by_graha:
            continue
        sid_lon = (float(r["tropical_longitude"]) - offset) % 360.0
        nak_idx = int(sid_lon // kota.NAK_SIZE_DEG) % 27
        by_graha[graha].append((r["date"], nak_idx))
    return by_graha


# ------------------------------------------------------------------------------------------- the statement
def test_the_statement_is_the_old_one_plus_the_null_safe_pin():
    sql = kota._FETCH_EPHEMERIS_RANGE_SQL
    assert NODE_SERIES_PREDICATE in sql
    assert "(body NOT IN ('Rahu', 'Ketu') OR node_mode = 'true')" in sql
    old = ("SELECT date, body, tropical_longitude FROM ephemeris_daily WHERE ayanamsha_id = 'tropical' "
           "AND date BETWEEN %s AND %s AND body = ANY(%s) ORDER BY body, date")
    assert " ".join(sql.replace(f"AND {NODE_SERIES_PREDICATE}", "").split()) == old


def test_the_fetch_issues_the_pinned_statement_with_unchanged_parameters():
    conn = _Conn(_rows())
    kota._fetch_daily_nak_idx_by_graha(conn, START, END, OFFSET)
    (kind, sql, params), = conn.calls
    assert sql == kota._FETCH_EPHEMERIS_RANGE_SQL and NODE_SERIES_PREDICATE in sql
    assert params == (START, END, list(kota.ALL_GRAHAS))


# ------------------------------------------------------------------------------------------- golden
def test_golden_the_pinned_fetch_returns_exactly_the_old_result_on_the_true_only_rows():
    conn = _Conn(_rows())
    new = kota._fetch_daily_nak_idx_by_graha(conn, START, END, OFFSET)
    assert new == _old_fetch(conn, START, END, OFFSET)
    assert set(new) == set(kota.ALL_GRAHAS) and all(len(v) == len(DAYS) for v in new.values())
    assert all(kota._has_complete_daily_series(v, START, END) for v in new.values())     # the writer's own gate passes


# ------------------------------------------------------------------------------------------- loud refusal
def test_two_rows_for_one_node_date_raise_instead_of_doubling_a_window():
    dup = {"date": DAYS[5], "body": "Rahu", "tropical_longitude": 331.0}                    # a second Rahu row for 2026-07-06
    with pytest.raises(NodeSeriesError, match="ambiguous"):
        kota._fetch_daily_nak_idx_by_graha(_Conn(_rows(extra=[dup])), START, END, OFFSET)


@pytest.mark.parametrize("node", ["Rahu", "Ketu"])
def test_a_node_with_no_row_raises(node):
    skip = {(node, d) for d in DAYS}
    with pytest.raises(NodeSeriesError, match=f"no row for {node}"):
        kota._fetch_daily_nak_idx_by_graha(_Conn(_rows(skip=skip)), START, END, OFFSET)


def test_a_hole_in_a_nodes_dates_raises():
    with pytest.raises(NodeSeriesError, match="hole"):
        kota._fetch_daily_nak_idx_by_graha(_Conn(_rows(skip={("Ketu", DAYS[7])})), START, END, OFFSET)


def test_a_hole_in_a_non_node_body_keeps_the_writers_own_graceful_refusal():
    got = kota._fetch_daily_nak_idx_by_graha(_Conn(_rows(skip={("Saturn", DAYS[3])})), START, END, OFFSET)
    assert len(got["Saturn"]) == len(DAYS) - 1
    assert not kota._has_complete_daily_series(got["Saturn"], START, END)                   # run() then writes nothing, with a note


# ------------------------------------------------------------------------------------------- through the writer
def _writer_ctx(conn):
    return SimpleNamespace(db_conn=conn, config={"chart_id": "chart-1"}, dry_run=False)


def _patch_writer(monkeypatch):
    today = date.today()
    monkeypatch.setattr(kota, "HORIZON_BACK_DAYS", (today - START).days)
    monkeypatch.setattr(kota, "HORIZON_FORWARD_DAYS", (END - today).days)
    monkeypatch.setattr(kota, "_fetch_janma_nakshatra_idx", lambda *_: (0, "fact-1"))
    monkeypatch.setattr(kota, "_fetch_ring_assignments", lambda *_: ({}, "citation"))
    monkeypatch.setattr(kota, "_compute_ayanamsha_offset", lambda *_: OFFSET)
    monkeypatch.setattr(kota, "detect_ring_runs", lambda *_a, **_k: [{
        "nakshatra_idx": 0, "start_date": START, "end_date": END, "start_truncated": False, "end_truncated": False}])
    monkeypatch.setattr(kota, "count_from_janma", lambda *_: 1)
    monkeypatch.setattr(kota, "ring_for_count", lambda *_: "STAMBHA")
    monkeypatch.setattr(kota, "attack_defence_reading",
                        lambda *_: {"is_natural_malefic": False, "posture": "defence", "severity": "low"})


def test_the_writer_runs_through_the_pinned_fetch_and_writes_the_same_rows(monkeypatch):
    _patch_writer(monkeypatch)
    conn = _Conn(_rows())
    result = kota.KaKotaChakraWriter().run(_writer_ctx(conn))
    assert result.rows_inserted == len(kota.ALL_GRAHAS)
    assert conn.mutations[0][1].lstrip().upper().startswith("DELETE") and conn.mutations[-1][0] == "executemany"
    # the same rows as the old fetch would have produced
    monkeypatch.setattr(kota, "_fetch_daily_nak_idx_by_graha", lambda c, s, e, o: _old_fetch(c, s, e, o))
    conn2 = _Conn(_rows())
    result2 = kota.KaKotaChakraWriter().run(_writer_ctx(conn2))
    assert result2.rows_inserted == result.rows_inserted
    assert conn2.mutations[-1][2] == conn.mutations[-1][2]


def test_the_writer_raises_before_any_delete_when_a_node_date_is_duplicated(monkeypatch):
    _patch_writer(monkeypatch)
    dup = {"date": DAYS[5], "body": "Ketu", "tropical_longitude": 151.0}
    conn = _Conn(_rows(extra=[dup]))
    with pytest.raises(NodeSeriesError):
        kota.KaKotaChakraWriter().run(_writer_ctx(conn))
    assert conn.mutations == []                                                             # nothing deleted, nothing inserted
