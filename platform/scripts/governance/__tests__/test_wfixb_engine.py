"""test_wfixb_engine.py: WFIX-B engine additions to the prose_none closure (Exec Suvarna, census 5124c348a).

(1) A json leaf path may be closed by `sha256`: a list of sha256 digests of the exact leaf strings the path may hold. It is the json-leaf twin of the top-level `curated_corpus`: hand-typed classical
    note sentences (longer than the 200 characters a `values` entry may be, and rejected as a vocabulary because they are sentences) are pinned by digest and CHECKED against the data: the live leaf
    must hash to one of the pins, an edited sentence or a sentence at another path is outside the closure.
(2) The existence read of a json closure is CHUNKED. bo_drishti's `bodha_question_lenses` holds three jsonb documents of up to ~3000 ranked signals per row (885 KB per row): ONE statement over the
    table was cancelled by the statement timeout, so the closure was never read (Narr.agree NO_DETECTOR, census 5124c348a). The chunked read walks the table in `ctid` order, a fixed number of rows per
    statement (keyset on ctid, no OFFSET), stops at the first violating row and reaches the SAME verdict as the single statement; a PASS still needs the scan to reach the end of the table.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_n150_prose_none as pn  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

TIMEOUT = "ERROR:  canceling statement due to statement timeout"
NOTE_A = "Sun-centric 60-year scheme; period lengths per classical table " + "x" * 220          # longer than the 200 characters a `values` entry may hold
NOTE_B = "Reckoned via the nine-tara cycle from the Moon's nakshatra."


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ───────────────────────────── (1) the sha256 leaf pattern ─────────────────────────────

def _cc(patterns):
    return dict(column="seq", json_leaf_patterns=patterns, why="a json record whose note leaves are pinned classical sentences")


def _decl(patterns):
    return dict(prose_fields=[], prose_none=dict(why=pn.WHY, closed_columns=[_cc(patterns)]))


def test_a_sha256_pattern_is_a_sound_declaration_and_the_other_shapes_are_unchanged():
    good = [dict(path="$.note", sha256=sorted([sha(NOTE_A), sha(NOTE_B)])), dict(path="$.type", values=["a", "b"])]
    assert ac.prose_none_problem(_decl(good)) is None
    assert ac.prose_none_problem(_decl([dict(path="$.at", kind="iso8601_timestamp")])) is None


@pytest.mark.parametrize("bad", [
    dict(path="$.note", sha256=[]),                                           # an empty pin closes nothing
    dict(path="$.note", sha256=["abc"]),                                      # not a sha256 hex digest
    dict(path="$.note", sha256=[sha(NOTE_A).upper()]),                        # upper-case hex is not what the check compares
    dict(path="$.note", sha256=[sha(NOTE_A), sha(NOTE_A)]),                   # a duplicate pin
    dict(path="$.note", sha256=[sha(NOTE_A)], values=["x"]),                  # two closure kinds on one path
    dict(path="$.note", sha256=[sha(NOTE_A)], kind="uuid"),
    dict(path="$.note", sha256="a" * 64),                                     # not a list
])
def test_a_malformed_sha256_pattern_is_refused(bad):
    assert ac.prose_none_problem(_decl([bad])) is not None


def test_the_sha256_pin_count_is_bounded():
    over = [sha(str(i)) for i in range(ac.PROSE_NONE_MAX_PATTERN_VALUES + 1)]
    assert ac.prose_none_problem(_decl([dict(path="$.note", sha256=over)])) is not None


def test_the_predicate_names_the_digests_and_is_shared_by_both_reads():
    entry = _cc([dict(path="$.note", sha256=[sha(NOTE_A)])])
    cond = ac._prose_none_cond('"c"', "json", entry)
    assert sha(NOTE_A) in cond and "sha256(" in cond
    assert cond in ac.prose_none_outside_sql("t", "c", "json", entry, None) and cond in ac.prose_none_existence_sql("t", "c", "json", entry, None)


def _mk(pg, monkeypatch, table, ddl, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {table}")
    ac.psql(f"CREATE TABLE {table} ({ddl})")
    for r in rows:
        ac.psql(f"INSERT INTO {table} VALUES ({r})")


def _j(doc) -> str:
    return "'" + json.dumps(doc, ensure_ascii=False).replace("'", "''") + "'::jsonb"


@pytest.mark.parametrize("name,doc,want", [
    ("pinned_a", {"type": "rashi_sequence", "note": NOTE_A}, 0),
    ("pinned_b", {"note": NOTE_B}, 0),
    ("edited_sentence", {"note": NOTE_B + " (edited)"}, 1),
    ("pinned_sentence_at_an_undeclared_path", {"comment": NOTE_B}, 1),
    ("closed_value_outside", {"type": "free prose"}, 1),
    ("no_string_leaf", {"n": 1, "xs": [1, 2]}, 0),
])
def test_REAL_SQL_the_sha256_closure_verdict(monkeypatch, disposable_pg, name, doc, want):
    t = "wfixb_sha2"
    entry = _cc([dict(path="$.note", sha256=sorted([sha(NOTE_A), sha(NOTE_B)])), dict(path="$.type", values=["rashi_sequence"])])
    _mk(disposable_pg, monkeypatch, t, "c jsonb", [_j(doc)])
    try:
        assert int(ac.scalar(ac.prose_none_outside_sql(t, "c", "json", entry, None))) == want, name
        assert ac.prose_none_fetch_existence(t, "c", "json", entry, None)["violating"] is bool(want), name
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


# ───────────────────────────── (2) the chunked existence read ─────────────────────────────

ENTRY = dict(column="c", values=None, json_leaf_patterns=[dict(path="$.ids[*]", kind="uuid"), dict(path="$.cls[*]", values=["a", "b"])])
UU = "11111111-2222-3333-4444-555555555555"


def _row(i, bad=False):
    d = {"ids": [UU], "cls": ["a", "b"], "n": i}
    if bad:
        d["note"] = "a free sentence"
    return _j(d)


def test_the_chunk_statement_is_bounded_ordered_by_ctid_and_keysets_without_offset():
    first = ac.prose_none_existence_chunk_sql("big_t", "c", "json", ENTRY, None, None)
    nxt = ac.prose_none_existence_chunk_sql("big_t", "c", "json", ENTRY, None, "(7,3)")
    for sql in (first, nxt):
        assert "ORDER BY ctid" in sql and f"LIMIT {ac.PROSE_NONE_CHUNK_ROWS}" in sql and "OFFSET" not in sql.upper()
        assert f"LIMIT {ac.PROSE_NONE_SAMPLE_LIMIT}" in sql                                # the violating sample stays bounded
        assert "count(*)::text" not in sql and ac._prose_none_cond('"c"', "json", ENTRY) in sql
    assert "ctid > '(7,3)'::tid" in nxt and "ctid >" not in first
    f = ac.prose_none_existence_chunk_sql("big_t", "c", "json", ENTRY, dict(column="k", equals="x"), None)
    assert """"k"::text = 'x'""" in f


@pytest.mark.parametrize("bad", ["(1;2)", "1,2", "(1,2)'; drop table x; --", "x"])
def test_a_malformed_after_cursor_is_refused_not_interpolated(bad):
    with pytest.raises(ValueError):
        ac.prose_none_existence_chunk_sql("t", "c", "json", ENTRY, None, bad)


@pytest.fixture()
def frozen_clock(monkeypatch):
    """A clock that never moves: every statement 'costs' 0 s, so the chunk grows each time (the light-row case) unless a test advances it."""
    t = [0.0]
    monkeypatch.setattr(ac, "_chunk_clock", lambda: t[0])
    return t


@pytest.mark.parametrize("n,bad_at", [(0, None), (1, None), (3, None), (4, None), (5, None), (14, None), (14, 0), (14, 4), (14, 13), (200, None), (200, 150)])
def test_REAL_SQL_the_chunked_verdict_equals_the_single_statement_verdict(monkeypatch, disposable_pg, frozen_clock, n, bad_at):
    t = "wfixb_chunk"
    _mk(disposable_pg, monkeypatch, t, "c jsonb", [_row(i, bad=(i == bad_at)) for i in range(n)])
    try:
        seen = []
        real = ac.scalar
        monkeypatch.setattr(ac, "scalar", lambda q: (seen.append(q), real(q))[1])
        got = ac.prose_none_fetch_existence(t, "c", "json", ENTRY, None)
        single = json.loads(real(ac.prose_none_existence_sql(t, "c", "json", ENTRY, None)))
        assert got["violating"] is bool(single) is (bad_at is not None), (n, bad_at, got)
        assert got["exact"] is False and len(got["sample"]) <= ac.PROSE_NONE_SAMPLE_LIMIT
        assert all("ORDER BY ctid" in q and "LIMIT" in q for q in seen)
        sizes = [int(re.search(r"ORDER BY ctid LIMIT (\d+)", q).group(1)) for q in seen]
        assert sizes[0] == ac.PROSE_NONE_CHUNK_ROWS and sizes[1:] == [min(ac.PROSE_NONE_CHUNK_MAX_ROWS, ac.PROSE_NONE_CHUNK_ROWS * ac.PROSE_NONE_CHUNK_GROW ** i) for i in range(1, len(sizes))]   # grows while cheap
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_every_row_is_visited_exactly_once_whatever_the_chunk_sizes(monkeypatch, disposable_pg, frozen_clock):
    """A violating row at EVERY position is found: no row is skipped at a chunk boundary (the chunks are 4, 16, 64 ... rows)."""
    t = "wfixb_chunk_all"
    n = 90
    _mk(disposable_pg, monkeypatch, t, "c jsonb", [_row(i) for i in range(n)])
    try:
        assert ac.prose_none_fetch_existence(t, "c", "json", ENTRY, None)["violating"] is False
        for bad_at in range(n):
            ac.psql(f"UPDATE {t} SET c = c || '{{\"note\": \"a free sentence\"}}'::jsonb WHERE (c->>'n')::int = {bad_at}")
            assert ac.prose_none_fetch_existence(t, "c", "json", ENTRY, None)["violating"] is True, bad_at
            ac.psql(f"UPDATE {t} SET c = c - 'note'")
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_slice_filter_bounds_the_chunk_walk_like_the_single_statement(monkeypatch, disposable_pg):
    t = "wfixb_chunk_f"
    rows = [f"'keep', {_row(i)}" for i in range(7)] + [f"'other', {_row(99, bad=True)}"]
    _mk(disposable_pg, monkeypatch, t, "k text, c jsonb", rows)
    try:
        assert ac.prose_none_fetch_existence(t, "c", "json", ENTRY, dict(column="k", equals="keep"))["violating"] is False
        assert ac.prose_none_fetch_existence(t, "c", "json", ENTRY, dict(column="k", equals="other"))["violating"] is True
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_the_chunk_size_adapts_to_the_measured_cost_of_a_statement():
    n = ac.next_chunk_rows
    assert n(4, 0.01) == 16 and n(16, 0.5) == 64                                   # cheap: grow
    assert n(64, ac.PROSE_NONE_CHUNK_TARGET_SECS) == 64 and n(64, 2.0) == 64      # about right: keep
    assert n(64, ac.PROSE_NONE_CHUNK_TARGET_SECS * 2 + 0.1) == 16                  # too slow: shrink
    assert n(1, 100.0) == 1 and n(ac.PROSE_NONE_CHUNK_MAX_ROWS, 0.0) == ac.PROSE_NONE_CHUNK_MAX_ROWS


class Chunks:
    """A fake `scalar` for a table of `n` rows read in chunks of the size each statement asks for (parsed from its LIMIT): records every statement and advances the clock by `cost` seconds per row;
    row `bad_at` (if any) violates; `fail_at` makes that statement time out."""

    def __init__(self, n, clock, cost=0.0, bad_at=None, fail_at=None):
        self.n, self.clock, self.cost, self.bad_at, self.fail_at, self.sql, self.pos, self.asked = n, clock, cost, bad_at, fail_at, [], 0, []

    def __call__(self, q):
        if "pg_index" in q:                                                          # the keyed-read planner's index catalog (a table past KEYED_READ_MIN_ROWS): this table has no usable index, so the older walk runs
            return "[]"
        i = len(self.sql)
        self.sql.append(q)
        if self.fail_at is not None and i == self.fail_at:
            raise ac.Unknown(TIMEOUT)
        ask = int(re.search(r"ORDER BY ctid LIMIT (\d+)", q).group(1))
        self.asked.append(ask)
        lo, hi = self.pos, min(self.pos + ask, self.n)
        self.pos = hi
        self.clock[0] += self.cost * (hi - lo)
        bad = ["free"] if self.bad_at is not None and lo <= self.bad_at < hi else []
        return json.dumps(dict(rows=hi - lo, last=f"({i},{hi - lo})" if hi > lo else None, sample=bad))


def test_heavy_rows_keep_every_statement_under_the_target_light_rows_walk_a_big_table_in_a_handful(monkeypatch, frozen_clock):
    heavy = Chunks(n=180, clock=frozen_clock, cost=1.0)                             # bo_drishti: ~1 s of leaf traversal per row
    monkeypatch.setattr(ac, "scalar", heavy)
    got = ac.prose_none_fetch_existence("big_t", "c", "json", ENTRY, None)
    assert got["violating"] is False and heavy.pos == 180
    assert max(heavy.asked) * 1.0 <= ac.PROSE_NONE_CHUNK_TARGET_SECS * 2 * ac.PROSE_NONE_CHUNK_GROW      # no statement is asked to cost more than a few targets
    frozen_clock[0] = 0.0
    light = Chunks(n=176298, clock=frozen_clock, cost=0.0)                          # bg_muhurta_lattice: 176 298 tiny rows
    monkeypatch.setattr(ac, "scalar", light)
    assert ac.prose_none_fetch_existence("big_t", "c", "json", ENTRY, None)["violating"] is False
    assert len(light.sql) <= 12 and light.pos == 176298 and max(light.asked) <= ac.PROSE_NONE_CHUNK_MAX_ROWS


def test_no_statement_ever_covers_more_than_one_chunk_and_the_cursor_moves_forward(monkeypatch, frozen_clock):
    srv = Chunks(n=500, clock=frozen_clock)
    monkeypatch.setattr(ac, "scalar", srv)
    got = ac.prose_none_fetch_existence("big_t", "c", "json", ENTRY, None)
    assert got["violating"] is False and srv.pos == 500
    assert all(q.count('FROM "big_t"') == 2 for q in srv.sql)                                                  # the ctid walk and the predicate read of that chunk, nothing else
    assert "ctid >" not in srv.sql[0] and srv.sql[1].count("ctid > '(0,") == 1


def test_a_chunk_that_times_out_leaves_the_closure_unread_never_a_pass(monkeypatch, frozen_clock):
    srv = Chunks(n=500, clock=frozen_clock, fail_at=2)
    monkeypatch.setattr(ac, "scalar", srv)
    got = ac.prose_none_read_outside("big_t", "c", "json", ENTRY, None, est=ac.LDGR_CHEAP_MIN_ROWS)
    assert "unread" in got and "statement timeout" in got["unread"] and "neither a PASS nor a FAIL" in got["unread"]
    assert len(srv.sql) == 3                                                                                     # it stopped at the failing chunk


def test_a_violation_in_a_late_chunk_is_found_and_stops_the_walk(monkeypatch, frozen_clock):
    srv = Chunks(n=500, clock=frozen_clock, bad_at=401)
    monkeypatch.setattr(ac, "scalar", srv)
    got = ac.prose_none_fetch_existence("big_t", "c", "json", ENTRY, None)
    assert got["violating"] is True and got["sample"] == ["free"] and srv.pos >= 402 and srv.pos < 500 + 1


def test_a_cursor_that_does_not_advance_is_an_unknown_not_an_endless_walk(monkeypatch, frozen_clock):
    monkeypatch.setattr(ac, "scalar", lambda q: json.dumps(dict(rows=ac.PROSE_NONE_CHUNK_ROWS * 100, last="(0,1)", sample=[])))
    with pytest.raises(ac.Unknown, match="did not advance"):
        ac.prose_none_fetch_existence("big_t", "c", "json", ENTRY, None)


def test_a_malformed_chunk_answer_is_an_unknown_not_a_verdict(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda q: "not json")
    with pytest.raises(ac.Unknown, match="unparseable"):
        ac.prose_none_fetch_existence("big_t", "c", "json", ENTRY, None)
    monkeypatch.setattr(ac, "scalar", lambda q: json.dumps(dict(rows="x", sample=[])))
    with pytest.raises(ac.Unknown, match="malformed"):
        ac.prose_none_fetch_existence("big_t", "c", "json", ENTRY, None)


def test_text_and_array_columns_keep_the_single_statement_read(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "scalar", lambda q: (seen.append(q), "[]")[1])
    for kind in ("text", "array"):
        got = ac.prose_none_fetch_existence("big_t", "c", kind, dict(column="c", values=["x"]), None)
        assert got["violating"] is False
    assert len(seen) == 2 and all("ORDER BY ctid" not in q for q in seen)
