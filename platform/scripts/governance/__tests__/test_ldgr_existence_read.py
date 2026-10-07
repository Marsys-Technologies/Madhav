"""test_ldgr_existence_read.py: the cheap EXISTENCE read of a declared row-level Ldgr.source_presence (interim census, SS rulings 2026-10-06).

Five checks (bg_muhurta_lattice, ga_dashas, ga_sensitive_degree, bo_anveshana, bo_pratijna) read ERRORED under the census role (`canceling statement due to statement timeout`): the
exact read counts every row and scans the table a second time for its sample. For a large table (catalog estimate) or one whose exact read timed out, the verdict is now read by
EXISTS ... LIMIT and a bounded LIMIT sample. These tests prove (a) the SQL shape (no count(*), no ORDER BY, EXISTS / LIMIT), (b) the verdict equals the exact read's on real SQL
(disposable PostgreSQL) over the cases the exact-read tests already use, (c) the routing and its failure modes (timeout -> existence read -> NO_DETECTOR with the cause, never ERRORED; any other
failure is still ERRORED), (d) the text states "at least 1", never an invented total, (e) K1/K2/K3 declared-source logic is the same code (the predicates are shared, not copied).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
import test_n151_ldgr_source as n  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, NA, ERRORED = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA, ac.ERRORED
LDGR = "Ldgr.source_presence"
TIMEOUT = "ERROR:  canceling statement due to statement timeout"


# ───────────────────────────── (a) the SQL shape ─────────────────────────────

def _shape_sqls():
    pred = ac._ldgr_lacking("src", "text")
    exc = "COALESCE((\"tier\")::text = 'p', false)"
    return [ac.source_presence_sql("big_t", pred, ["id"], None), ac.source_presence_sql("big_t", pred, [], None),
            ac.source_presence_sql("big_t", pred, ["id", "k2"], exc), ac.source_presence_sql("big_t", pred, [], exc)]


@pytest.mark.parametrize("sql", _shape_sqls())
def test_the_existence_statement_is_exists_and_limit_with_no_unbounded_count_or_sort(sql):
    assert "EXISTS (SELECT 1 FROM \"big_t\"" in sql and "LIMIT 1)" in sql
    assert f"LIMIT {ac.LDGR_SAMPLE_LIMIT}) s" in sql                                    # the sample is bounded
    assert not re.search(r"count\s*\(", sql, re.I)                                      # no count(*) / count(x) over the target: no total is ever computed
    assert "ORDER BY" not in sql.upper() and "GROUP BY" not in sql.upper()              # a sort or a group would force the full scan this read avoids
    assert sql.count("FROM \"big_t\"") == sql.count("LIMIT")                            # EVERY sub-select over the target is bounded by a LIMIT


def test_the_exact_statement_it_replaces_counts_every_row_and_scans_twice():
    """The 'before' shape, kept for the record: a whole-table count(*) FILTER plus a second scan with ORDER BY for the sample."""
    sql = []
    orig = ac.scalar
    try:
        ac.scalar = lambda q: sql.append(q) or json.dumps(dict(rows=1, lacking=0, sample=[]))
        ac.source_fetch_stats("t", "(x IS NULL)", ["id"])
    finally:
        ac.scalar = orig
    assert "count(*) FILTER (WHERE" in sql[0] and "ORDER BY" in sql[0] and "count(*)" in sql[0]


def test_the_estimate_is_a_catalog_lookup_not_a_table_read(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "scalar", lambda q: seen.append(q) or "1460000")
    assert ac.source_estimate_rows("chart_dashas") == 1_460_000
    assert "pg_class" in seen[0] and "reltuples" in seen[0] and "FROM \"chart_dashas\"" not in seen[0] and "count(" not in seen[0]
    monkeypatch.setattr(ac, "scalar", lambda q: "-1")
    assert ac.source_estimate_rows("t") is None                                          # never analysed: unknown, so the exact read runs first
    monkeypatch.setattr(ac, "scalar", lambda q: '{"rows":1}')
    assert ac.source_estimate_rows("t") is None                                          # an unparseable answer is unknown, never a number
    monkeypatch.setattr(ac, "scalar", lambda q: (_ for _ in ()).throw(ac.Unknown("boom")))
    assert ac.source_estimate_rows("t") is None
    assert ac.source_estimate_rows("t; drop") is None                                    # identifiers are matched before any SQL


# ───────────────────────────── (b) verdicts equal the exact read's (real SQL) ─────────────────────────────

FACTS = n.FACTS
SIGS = n.SIGS


def _case(src, table, cols, setup):
    return (src, table, cols, setup)


def _cases():
    k2 = n._row(dict(column="ratified_by", kinds=["K2"]))
    out = {}
    out["k2_all_good"] = _case(k2, "k2t", ["id", "ratified_by"], n._tbl("k2t", "ratified_by text", ["'N-150'", "'D-4'", "'N-72a'", "'  F-2  '"]))
    out["k2_mixed_partial"] = _case(k2, "k2t", ["id", "ratified_by"], n._tbl("k2t", "ratified_by text", ["'N-150'", "'ratified'", "NULL", "''", "'TBD'", "'N-'"]))
    out["k2_all_bad_fail"] = _case(k2, "k2t", ["id", "ratified_by"], n._tbl("k2t", "ratified_by text", ["'ratified'", "NULL", "'TBD-1'", "'N-0'"]))
    out["k2_empty_no_det"] = _case(k2, "k2t", ["id", "ratified_by"], n._tbl("k2t", "ratified_by text", []))
    k1 = n._row(dict(column="c", kinds=["K1"]), citation_state="sourced")
    out["k1_text_partial"] = _case(k1, "k1t", ["id", "c"], n._tbl("k1t", "c text", ["'Brihat Parashara Hora Shastra 3.12'", "'classical_tradition'", "'UNSOURCED - none'", "NULL"]))
    out["k1_text_pass"] = _case(k1, "k1t", ["id", "c"], n._tbl("k1t", "c text", ["'BPHS 1.1'", "'Saravali 2'"]))
    out["k1_array_partial"] = _case(n._row(dict(column="cites", kinds=["K1"]), citation_state="sourced"), "ar", ["id", "cites"],
                                    n._tbl("ar", "cites text[]", ["ARRAY['BPHS 1.1']", "ARRAY['Saravali 2','classical_tradition']", "ARRAY[]::text[]"]))
    out["k1_json_pass"] = _case(n._row(dict(column="cites", kinds=["K1"]), citation_state="sourced"), "js", ["id", "cites"],
                                n._tbl("js", "cites jsonb", ["'[{\"text_id\":\"BPHS 1.1\"}]'::jsonb"]))
    mix = n._row(dict(column="c", kinds=["K1", "K2"]), citation_state="sourced")
    out["k1k2_mixed_partial"] = _case(mix, "mx", ["id", "c"], n._tbl("mx", "c text", ["'N-150'", "'BPHS ch. 4'", "'classical_tradition'", "NULL", "'N-0'", "'TBD-1'"]))
    k3 = n._row(dict(kinds=["K3"], generator_column="gen", method_column="meth", seed_column="seed", version_column="ver"))
    ddl = "gen text, meth text, seed text, ver text"
    out["k3_pass"] = _case(k3, "k3", ["id", "gen", "meth", "seed", "ver"], n._tbl("k3", ddl, ["'bg_cohort', 'seeded sampling', '20260101', NULL", "'bg_cohort', 'seeded sampling', NULL, 'v2'"]))
    out["k3_partial"] = _case(k3, "k3", ["id", "gen", "meth", "seed", "ver"],
                              n._tbl("k3", ddl, ["'bg_cohort', 'seeded sampling', '20260101', NULL", "'bg_cohort', 'seeded sampling', NULL, NULL", "'TBD', 'm', '1', NULL"]))
    led = n._row(dict(column="facts", kinds=["LEDGER"]))
    out["ledger_pass"] = _case(led, "la", ["id", "facts"], FACTS + n._tbl("la", "facts text[]", ["ARRAY['F1','F2']", "ARRAY['F3']"]))
    out["ledger_partial"] = _case(led, "la", ["id", "facts"], FACTS + n._tbl("la", "facts text[]", ["ARRAY['F1','F2']", "ARRAY['F1','F999']", "ARRAY[]::text[]", "NULL"]))
    out["ledger_fail"] = _case(led, "la", ["id", "facts"], FACTS + n._tbl("la", "facts text[]", ["ARRAY['F999']", "NULL"]))
    sig = n._row(dict(column="refs", kinds=["LEDGER"], path="$.signal_ids", resolves_to="bodha_msr_signals.signal_id"))
    out["ledger_signal_chain_partial"] = _case(sig, "pc", ["id", "refs"], FACTS + SIGS + n._tbl("pc", "refs jsonb", [f"'{{\"signal_ids\":[\"{n.S1}\"]}}'::jsonb", f"'{{\"signal_ids\":[\"{n.S3}\"]}}'::jsonb"]))
    ex = n._row(dict(column="derivation_chain", kinds=["K1"], except_when=dict(column="grounding_tier", equals="pratyaksa")), citation_state="sourced")
    ddl2 = "grounding_tier text, derivation_chain text"
    cols = ["id", "grounding_tier", "derivation_chain"]
    out["except_pass"] = _case(ex, "ex", cols, n._tbl("ex", ddl2, ["'pratyaksa', NULL", "'anumana', 'BPHS 3.12'", "'pratyaksa', 'n/a'"]))
    out["except_partial"] = _case(ex, "ex", cols, n._tbl("ex", ddl2, ["'pratyaksa', NULL", "'anumana', 'BPHS 3.12'", "'anumana', NULL", "'agama', 'classical_tradition'"]))
    out["except_fail"] = _case(ex, "ex", cols, n._tbl("ex", ddl2, ["'pratyaksa', 'BPHS 3.12'", "'anumana', NULL", "'agama', 'n/a'"]))
    out["except_all_excepted_no_det"] = _case(ex, "ex", cols, n._tbl("ex", ddl2, ["'pratyaksa', NULL", "'pratyaksa', 'x 1'"]))
    two = n._row(dict(column="a", kinds=["K2"], except_when=dict(column="tier", equals="p")), dict(column="b", kinds=["K2"], except_when=dict(column="tier", equals="q")))
    rows = ["'p', NULL, 'N-1'", "'q', 'N-2', NULL", "'r', 'N-3', NULL", "'r', NULL, 'N-4'", "'r', NULL, NULL", "'r', 'TBD-1', 'N-0'", "'p', NULL, NULL"]
    out["two_entries_alternatives_partial"] = _case(two, "ew", ["id", "tier", "a", "b"], n._tbl("ew", "tier text, a text, b text", rows))
    out["two_entries_alternatives_pass"] = _case(two, "ew", ["id", "tier", "a", "b"], n._tbl("ew", "tier text, a text, b text", rows[:4] + rows[6:]))
    return out


CASES = _cases()


def _run(monkeypatch, pg, case, estimate, **kw):
    src, table, cols, setup = case
    monkeypatch.setattr(ac, "source_estimate_rows", lambda t: estimate)
    s3._real(monkeypatch, pg, setup)
    return ac.source_declared_check("x", src, table, cols, rows=kw.pop("rows", 1), **kw)[LDGR]


@pytest.mark.parametrize("name", sorted(CASES))
def test_REAL_SQL_the_existence_read_gives_the_exact_reads_verdict(monkeypatch, disposable_pg, name):
    exact = _run(monkeypatch, disposable_pg, CASES[name], None)                          # estimate unknown: the exact read runs
    cheap = _run(monkeypatch, disposable_pg, CASES[name], 10 ** 9)                       # estimate huge: the existence read runs
    assert exact["source"].get("read") != "existence" and cheap["source"]["read"] == "existence"
    assert cheap["v"] == exact["v"], (name, exact["measured"], cheap["measured"])
    assert cheap["citation_state"] == exact["citation_state"] and cheap["declared"] is True
    if exact["v"] in (PASS, PARTIAL, FAIL):
        lack_exact, lack_cheap = exact["source"]["lacking"], cheap["source"]["lacking_at_least"]
        assert (lack_exact > 0) == (lack_cheap > 0)                                      # a violating row exists in both readings, or in neither
        assert cheap["source"]["rows"] is None and cheap["source"]["exact"] is False      # no total is invented
        assert "rows were not counted" in cheap["measured"]
        if lack_exact:
            assert "at least 1 row lacks one" in cheap["measured"]
        sample = cheap["source"].get("sample") or cheap["ldgr"]["sample"]
        assert len(sample) <= ac.LDGR_SAMPLE_LIMIT and all(s in exact["ldgr"]["sample"] or lack_exact > len(exact["ldgr"]["sample"]) for s in sample)     # a sampled offender is a real offender
    if exact["v"] == NO_DET:
        assert "no row was judged" in cheap["measured"] or "no judged rows" in cheap["measured"] or "vacuous" in cheap["measured"]


def test_REAL_SQL_the_sample_names_only_real_offenders_and_at_most_three(monkeypatch, disposable_pg):
    rows = [f"'BPHS {i}'" for i in range(6)] + ["NULL", "'n/a'", "'classical_tradition'", "'TBD'", "''"]
    case = (n._row(dict(column="c", kinds=["K1"]), citation_state="sourced"), "smp", ["id", "c"], n._tbl("smp", "c text", rows))
    cheap = _run(monkeypatch, disposable_pg, case, 10 ** 9, keys=[["id"]])
    assert cheap["v"] == PARTIAL
    ids = [s["id"] for s in cheap["ldgr"]["sample"]]
    assert 1 <= len(ids) <= ac.LDGR_SAMPLE_LIMIT and set(ids) <= {7, 8, 9, 10, 11}        # only the rows that lack a source (ids 7..11)
    assert cheap["ldgr"]["lacking"] is None and cheap["ldgr"]["lacking_at_least"] == 1


def test_REAL_SQL_a_pass_needs_every_row_visited_and_a_single_late_violation_is_found(monkeypatch, disposable_pg):
    good = [f"'BPHS {i}'" for i in range(500)]
    mk = lambda rows: (n._row(dict(column="c", kinds=["K1"]), citation_state="sourced"), "late", ["id", "c"], n._tbl("late", "c text", rows))      # noqa: E731
    assert _run(monkeypatch, disposable_pg, mk(good), 10 ** 9)["v"] == PASS
    late = _run(monkeypatch, disposable_pg, mk(good + ["NULL"]), 10 ** 9)
    assert late["v"] == PARTIAL and late["source"]["lacking_at_least"] == 1               # the last row is the one that violates: PASS is never read past it


def test_REAL_SQL_citation_state_cap_holds_on_the_existence_read(monkeypatch, disposable_pg):
    for st in ("unsourced", "refuted"):
        case = (n._row(dict(column="c", kinds=["K1"]), citation_state=st), "cap", ["id", "c"], n._tbl("cap", "c text", ["'BPHS 1.1'", "'Saravali 2'"]))
        rec = _run(monkeypatch, disposable_pg, case, 10 ** 9)
        assert rec["v"] == NO_DET and "never a PASS" in rec["measured"] and rec["citation_state"] == st


# ───────────────────────────── (c) routing and failure modes ─────────────────────────────

class Server:
    """A fake `scalar`: answers the catalog reads, the estimate, the exact statement and the existence statement from scripted behaviour, and records every statement."""

    def __init__(self, estimate="-1", exact=None, cheap=None):
        self.estimate, self.exact, self.cheap, self.sql = estimate, exact, cheap, []

    def __call__(self, q):
        self.sql.append(q)
        if "reltuples" in q:
            return self.estimate
        if "pg_attribute" in q:
            return json.dumps({"c": "text"})
        beh = self.cheap if "'any_row'" in q else self.exact
        if isinstance(beh, Exception):
            raise beh
        return beh


CHEAP_OK = json.dumps(dict(any_row=True, judged=True, lacking=[{"id": 4}], sourced=True, has_keys=True))
EXACT_OK = json.dumps(dict(rows=10, lacking=1, sample=[{"id": 4}]))
SRC = n._row(dict(column="c", kinds=["K1"]), citation_state="sourced")


def _chk(monkeypatch, server):
    monkeypatch.setattr(ac, "scalar", server)
    return ac.source_declared_check("x", SRC, "t", ["id", "c"], rows=10, keys=[["id"]])[LDGR]


def _is_exact(q):
    return "count(*)" in q and "'any_row'" not in q


def test_a_large_table_is_read_by_existence_straight_away_and_never_counted(monkeypatch):
    srv = Server(estimate=str(ac.LDGR_CHEAP_MIN_ROWS), cheap=CHEAP_OK, exact=AssertionError("the exact read must not run on a large table"))
    rec = _chk(monkeypatch, srv)
    assert rec["v"] == PARTIAL and rec["source"]["read"] == "existence" and "catalog estimates" in rec["source"]["why_cheap"]
    over_target = [q for q in srv.sql if 'FROM "t"' in q]
    assert len(over_target) == 1 and not any(_is_exact(q) for q in srv.sql) and not any(re.search(r"count\s*\(", q) for q in over_target)
    assert "EXISTS" in over_target[0] and "LIMIT" in over_target[0]


def test_a_small_table_keeps_the_exact_read_and_its_text_byte_for_byte(monkeypatch):
    srv = Server(estimate=str(ac.LDGR_CHEAP_MIN_ROWS - 1), exact=EXACT_OK, cheap=AssertionError("the existence read must not run on a small table"))
    rec = _chk(monkeypatch, srv)
    assert rec["v"] == PARTIAL and rec["source"]["rows"] == 10 and rec["source"]["lacking"] == 1 and "read" not in rec["source"]
    assert "names a source on 9/10 rows" in rec["measured"]                              # the exact text, unchanged
    srv2 = Server(estimate="-1", exact=EXACT_OK, cheap=AssertionError("unknown size runs the exact read first"))
    assert _chk(monkeypatch, srv2)["measured"] == rec["measured"]


@pytest.mark.parametrize("err", [ac.Unknown(TIMEOUT), ac.CheckTimeout("client-side timeout after 180s (psql killed): SELECT ...")])
def test_an_exact_read_that_times_out_falls_back_to_the_existence_read(monkeypatch, err):
    srv = Server(estimate="1000", exact=err, cheap=CHEAP_OK)
    rec = _chk(monkeypatch, srv)
    assert rec["v"] == PARTIAL and rec["source"]["read"] == "existence" and "exceeded the statement timeout" in rec["source"]["why_cheap"]
    assert [bool(_is_exact(q)) for q in srv.sql if 'FROM "t"' in q] == [True, False]          # exact tried once, then the existence read


@pytest.mark.parametrize("err", [ac.Unknown(TIMEOUT), ac.CheckTimeout("client-side timeout after 180s (psql killed)")])
def test_when_even_the_existence_read_times_out_the_cell_is_no_detector_with_the_cause_never_errored(monkeypatch, err):
    for srv in (Server(estimate=str(10 ** 7), cheap=err), Server(estimate="5", exact=ac.Unknown(TIMEOUT), cheap=err)):
        rec = _chk(monkeypatch, srv)
        assert rec["v"] == NO_DET and rec["v"] not in (ERRORED, PASS)
        assert "existence read" in rec["measured"] and "also exceeded the statement timeout" in rec["measured"] and "neither a PASS nor a FAIL" in rec["measured"]
        assert rec["source"]["timed_out"] is True and rec["declared"] is True


def test_any_other_failure_is_still_errored_as_before(monkeypatch):
    rec = _chk(monkeypatch, Server(estimate="5", exact=ac.Unknown("ERROR:  relation \"t\" does not exist")))
    assert rec["v"] == ERRORED and "does not exist" in rec["measured"]
    rec = _chk(monkeypatch, Server(estimate=str(10 ** 7), cheap=ac.Unknown("ERROR:  permission denied for table t")))
    assert rec["v"] == ERRORED and "permission denied" in rec["measured"]
    rec = _chk(monkeypatch, Server(estimate=str(10 ** 7), cheap="not json"))
    assert rec["v"] == ERRORED and "unparseable" in rec["measured"]


def test_an_errored_check_is_never_a_pass_in_the_rollup_and_a_no_detector_is_not_one_either():
    errored = {LDGR: dict(v=ERRORED, measured="check errored: x", declared=True)}
    nodet = {LDGR: dict(v=NO_DET, measured="NO_DETECTOR — the existence read of t also exceeded the statement timeout", declared=True)}
    for m in (errored, nodet):
        cell = ac.rollup_asset("L2", m)["Ldgr"]
        assert cell["v"] in (ERRORED, NO_DET) and cell["v"] != PASS
    assert ac.rollup_asset("L2", errored)["Ldgr"]["v"] == ERRORED                                       # the old reading, kept for non-timeout failures
    assert ac.rollup_asset("L2", nodet)["Ldgr"]["v"] == NO_DET


def test_the_existence_record_never_states_a_total():
    pr = dict(any_row=True, judged=True, lacking_at_least=1, sample=[{"id": 4}], sourced=True, exact=False)
    rec = ac.grade_ldgr_source_presence(dict(source_column="c", citation_state="sourced"), pr, "t")
    assert rec["v"] == PARTIAL and "at least 1 row lacks one and at least 1 row names one" in rec["measured"]
    assert not re.search(r"\d+/\d+ rows|\bon \d+ rows", rec["measured"])
    assert rec["ldgr"]["rows"] is None and rec["ldgr"]["lacking"] is None and rec["ldgr"]["lacking_at_least"] == 1 and "first up to 3 found, unordered" in rec["measured"]
    assert ac.grade_ldgr_source_presence(dict(source_column="c", citation_state="sourced"), dict(pr, lacking_at_least=0, sample=[]), "t")["v"] == PASS
    assert ac.grade_ldgr_source_presence(dict(source_column="c", citation_state="sourced"), dict(pr, sourced=False), "t")["v"] == FAIL
    assert ac.grade_ldgr_source_presence(dict(source_column="c", citation_state="sourced"), dict(pr, any_row=False, judged=False), "t")["v"] == NO_DET


# ───────────────────────────── (e) K1 / K2 / K3 logic is the same code ─────────────────────────────

def test_the_existence_read_embeds_the_very_predicate_the_exact_read_uses(monkeypatch):
    """The predicate text is built once by `source_entry_lacking` (K1 / K2 / K3 / LEDGER logic) and handed to either read: both statements contain it verbatim."""
    ktypes = {"c": "text"}
    pred, _ = ac.source_entry_lacking(dict(column="c", kinds=["K1"]), ktypes)
    exact_sql, cheap_sql = [], []
    monkeypatch.setattr(ac, "scalar", lambda q: exact_sql.append(q) or EXACT_OK)
    ac.source_fetch_stats("t", pred, ["id"])
    monkeypatch.setattr(ac, "scalar", lambda q: cheap_sql.append(q) or CHEAP_OK)
    ac.source_fetch_presence("t", pred, ["id"])
    assert pred in exact_sql[0] and pred in cheap_sql[0]
