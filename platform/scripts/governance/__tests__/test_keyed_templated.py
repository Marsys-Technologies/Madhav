"""test_keyed_templated.py: the templated-column read of a very large table is read KEYED (Nikasha lane W3, n430 ga_dashas).

`citation_ref` of ga_dashas is closed by templates; the whole-table read is `NOT (13 template regexes)` over every row and exceeded the statement timeout on ~484 000 rows. For a table with more than
KEYED_READ_MIN_ROWS rows in scope the SAME statement now runs once per partition of the table's leading index key. These tests prove, on real tables in the disposable PostgreSQL:
  * the keyed answer equals the whole-table answer on a clean table and on a table with a planted violation (same wording, through the engine's own `_measure_prose` too);
  * a partition that times out, a plan whose counts do not add up and a partition that changed under the read leave the cell NO_DETECTOR with the coverage text, never PASS;
  * a table below the threshold takes the older whole-table path (the keyed reader is never called);
  * the coverage (rows / partitions / seconds) is recorded in the asset budget.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
import _keyed_fixture as kf  # noqa: E402
import prose_forms as pf  # noqa: E402
import test_formgap_templated as tt  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import CHART_A, CHART_B, NA, FAIL, NO_DET  # noqa: E402

T = "kt_tpl"
TEMPL = ["ref.{n}@chart={chart_id}"]
PH = {"n": {"class": "int"}}


def _rx(chart=kf.CHART):
    return pf.compile_each(TEMPL, PH, chart)


@pytest.fixture()
def table(disposable_pg, monkeypatch):
    kf.make_table(disposable_pg, monkeypatch, T, per_cell=500)
    kf.shrink(monkeypatch)
    ac.set_read_scope(None)
    ac.end_asset_read_budget()
    yield T
    ac.set_read_scope(None)
    ac.end_asset_read_budget()
    kf.drop_table(T)


def whole(table, chart=kf.CHART):
    """The whole-table answer: the pre-existing statement, run as one."""
    return ac._formgap_templated_answer(ac._formgap_json(ac.templated_read_sql(table, "citation_ref", _rx(chart), chart, None), "x"), "x")


def keyed(table, chart=kf.CHART):
    return ac._formgap_templated_read(table, "citation_ref", _rx(chart), chart, None)


def _one_row(table, a, set_sql):
    ac.psql(f"UPDATE {table} SET {set_sql} WHERE id = (SELECT min(id) FROM {table} WHERE a = {a})")


# ───────────────────────────── keyed == whole-table ─────────────────────────────

def test_a_clean_table_reads_the_same_keyed_as_whole(table, monkeypatch):
    spy = kf.spy_scalar(monkeypatch)
    got = keyed(table)
    assert got == whole(table) == dict(unmatched=[], other_chart=[])
    keyed_stmts = [s for s in spy.calls if "starts_with(" in s and '"a" = ' in s]
    assert len(keyed_stmts) == 3 and all("'n'" in s for s in keyed_stmts)       # one statement per partition, each counting its own rows


def test_a_planted_violation_in_one_partition_is_the_same_finding(table):
    _one_row(table, 2, "citation_ref = 'Jupiter rules the dasha because it is exalted'")
    _one_row(table, 3, f"citation_ref = 'ref.1@chart={kf.OTHER}'")
    got = keyed(table)
    assert got == whole(table)
    assert "Jupiter rules the dasha because it is exalted" in got["unmatched"] and got["other_chart"] == [f"ref.1@chart={kf.OTHER}"]


def test_a_single_planted_violation_is_found_whichever_partition_holds_it(table):
    for a in (1, 2, 3):
        ac.psql(f"UPDATE {table} SET citation_ref = 'ref.' || id || '@chart={kf.CHART}'")        # reset to clean
        _one_row(table, a, "citation_ref = 'a free sentence'")
        assert keyed(table) == whole(table) == dict(unmatched=["a free sentence"], other_chart=[])


def test_many_violations_give_the_same_bounded_sample_size(table):
    ac.psql(f"UPDATE {table} SET citation_ref = 'sentence ' || id WHERE b = 2")
    ac.psql(f"UPDATE {table} SET citation_ref = 'ref.7@chart={kf.OTHER}' WHERE a = 1 AND b = 1")
    got, ref = keyed(table), whole(table)
    assert len(got["unmatched"]) == len(ref["unmatched"]) == ac.FORMGAP_SAMPLE_LIMIT and len(got["other_chart"]) == len(ref["other_chart"]) == ac.FORMGAP_SAMPLE_LIMIT
    assert all(v.startswith("sentence ") or v == f"ref.7@chart={kf.OTHER}" for v in got["unmatched"]) and all(v == f"ref.7@chart={kf.OTHER}" for v in got["other_chart"])     # another chart's pointer also matches no template


def test_the_chart_scope_and_the_slice_bound_the_keyed_read_exactly_as_the_whole_read(table):
    ac.psql(f"INSERT INTO {table} (chart_id, a, b, citation_ref) SELECT '{kf.OTHER}'::uuid, 2, 1, 'another chart sentence' FROM generate_series(1, 30)")
    ac.psql(f"ANALYZE {table}")
    kf.scope_to_chart(table)
    assert keyed(table) == whole(table) == dict(unmatched=[], other_chart=[])                  # the other chart's rows are outside the measured scope in BOTH reads
    ac.set_read_scope(None)
    assert keyed(table) == whole(table) and keyed(table)["unmatched"] == ["another chart sentence"] * 3


# ───────────────────────────── soundness: never a PASS on a read that did not finish ─────────────────────────────

def test_a_timed_out_partition_leaves_the_read_unread_with_the_coverage_text(table, monkeypatch):
    spy = kf.spy_scalar(monkeypatch, slow_marker='"a" = \'2\'')
    got = keyed(table)
    assert set(got) == {"unread"} and "covered 2 of 3 partition(s) (2000 of 3000 rows)" in got["unread"] and "partition (2) timed out" in got["unread"]
    assert f"{table}.citation_ref (templated pointer) by {table}(a)" in got["unread"] and "asset read budget" in got["unread"] and "neither a PASS nor a FAIL" in got["unread"]
    assert "statement timeout" not in got["unread"]
    assert sum('"a" = ' in s for s in spy.calls) == 3                                        # the other partitions were still read


def test_a_violation_in_a_read_partition_stands_even_when_another_partition_timed_out(table, monkeypatch):
    _one_row(table, 1, "citation_ref = 'a free sentence'")
    kf.spy_scalar(monkeypatch, slow_marker='"a" = \'3\'')
    assert keyed(table) == dict(unmatched=["a free sentence"], other_chart=[])


def test_counts_that_do_not_add_up_leave_the_read_unread(table, monkeypatch):
    def lie(sql, out):
        if "'groups'" in sql:
            d = json.loads(out)
            d["groups"][0]["n"] += 1
            return json.dumps(d)
        return out
    kf.spy_scalar(monkeypatch, rewrite=lie)
    got = keyed(table)
    assert set(got) == {"unread"} and "not trusted" in got["unread"] and "neither a PASS nor a FAIL" in got["unread"]


def test_a_partition_whose_rows_differ_from_the_plan_is_unread(table, monkeypatch):
    def off_by_one(sql, out):
        if "starts_with(" in sql and '"a" = \'1\'' in sql:
            d = json.loads(out)
            d["n"] += 1
            return json.dumps(d)
        return out
    kf.spy_scalar(monkeypatch, rewrite=off_by_one)
    got = keyed(table)
    assert set(got) == {"unread"} and "partition (1) holds 1001 row(s), the plan counted 1000" in got["unread"] and "covered 2 of 3" in got["unread"]


def test_the_asset_budget_running_out_leaves_the_read_unread(table, monkeypatch):
    clock = kf.Clock()
    monkeypatch.setattr(ac, "_chunk_clock", clock)
    real = ac.scalar

    def slow(sql):
        if '"a" = ' in sql:
            clock.t += 50
        return real(sql)
    monkeypatch.setattr(ac, "scalar", slow)
    ac.begin_asset_read_budget(total_secs=60)
    got = keyed(table)
    assert set(got) == {"unread"} and "covered 2 of 3" in got["unread"] and "1 partition(s) not reached" in got["unread"] and "60s ran out" in got["unread"]


def test_any_other_failure_of_a_partition_is_still_an_error_not_an_unread(table, monkeypatch):
    real = ac.scalar

    def boom(sql):
        if '"a" = ' in sql:
            raise ac.Unknown("ERROR:  syntax error at or near x")
        return real(sql)
    monkeypatch.setattr(ac, "scalar", boom)
    with pytest.raises(ac.Unknown, match="syntax error"):
        keyed(table)                                                       # as the whole-table read: the engine's guard re-raises it and the cells read ERRORED


# ───────────────────────────── opt-in by structure ─────────────────────────────

def test_below_the_threshold_the_older_whole_table_path_runs_and_the_keyed_reader_never_does(table, monkeypatch):
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 3000)
    parts = []
    real_sql = ac.templated_read_sql

    def spy_sql(*a, **k):
        parts.append(k.get("part", a[5] if len(a) > 5 else None))
        return real_sql(*a, **k)
    monkeypatch.setattr(ac, "templated_read_sql", spy_sql)

    def never(*a, **k):
        raise AssertionError("the keyed reader must not run below the threshold")
    monkeypatch.setattr(ac, "keyed_read", never)
    spy = kf.spy_scalar(monkeypatch)
    assert keyed(table) == dict(unmatched=[], other_chart=[]) and parts == [None]       # ONE whole-table statement, no partition
    assert not any("pg_index" in s or "GROUP BY" in s for s in spy.calls)


def test_the_whole_table_statement_is_unchanged_without_a_partition():
    pairs = _rx()
    sql = ac.templated_read_sql("chart_dashas", "citation_ref", pairs, kf.CHART, None)
    assert sql == ac.templated_read_sql("chart_dashas", "citation_ref", pairs, kf.CHART, None, None) and "'n'" not in sql
    keyed_sql = ac.templated_read_sql("chart_dashas", "citation_ref", pairs, kf.CHART, None, ac.KeyedPartition(("ayanamsha_id",), ("raman",), 5))
    assert "\"ayanamsha_id\" = 'raman'" in keyed_sql and "'n', (SELECT count(*)" in keyed_sql and sql.count("LIMIT 3") == keyed_sql.count("LIMIT 3") == 2


def test_the_coverage_is_recorded_in_the_asset_budget(table, monkeypatch):
    clock = kf.Clock()
    monkeypatch.setattr(ac, "_chunk_clock", clock)
    b = ac.begin_asset_read_budget()
    assert keyed(table) == dict(unmatched=[], other_chart=[])
    assert len(b.reads) == 1 and b.reads[0]["what"] == f"{table}.citation_ref (templated pointer)"
    assert (b.reads[0]["partitions_covered"], b.reads[0]["partitions_total"], b.reads[0]["rows_covered"], b.reads[0]["rows_total"], b.reads[0]["complete"]) == (3, 3, 3000, 3000, True)
    assert b.rows_covered == 3000 and b.partitions_covered == 3


# ───────────────────────────── through the engine: the six Narr / Null cells ─────────────────────────────

@pytest.fixture()
def db(monkeypatch, disposable_pg):
    pg = disposable_pg
    point_psql_at(pg, monkeypatch)
    fs.drop_tables(pg, "chart_dashas")
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "206_ga3_supporting_tables.sql", "chart_dashas"))
    fs.psql(pg, f"""INSERT INTO chart_dashas (chart_id, ayanamsha_id, build_id, system_id, level_n, lord_graha, start_date, end_date, start_iso, end_iso, duration_days,
        verification_pass_status, verification_method, citation_ref, citation_human, engine_version)
        SELECT '{CHART_A}', ay, gen_random_uuid(), 'vimshottari', lv, 'Sun', DATE '2000-01-01', DATE '2001-01-01', TIMESTAMPTZ '2000-01-01 00:00+00' + g * interval '1 day',
        TIMESTAMPTZ '2001-01-01 00:00+00', 366, 'single', 'm', 'chart_dashas.vimshottari.L' || lv || '.Sun@chart={CHART_A}:ay=' || ay || ':eng=pyjhora_adapter/0.1.0', 'h', 'e'
        FROM unnest(ARRAY['lahiri_chitrapaksha','raman','true_chitra']) ay, generate_series(1,2) lv, generate_series(1,400) g""")
    fs.psql(pg, "ANALYZE chart_dashas")
    ac.set_read_scope(None)
    ac.end_asset_read_budget()
    yield pg
    ac.end_asset_read_budget()
    fs.drop_tables(pg, "chart_dashas")


SCOPE = {"chart_dashas": dict(where=f"chart_id = '{CHART_A}'", label="the measured chart")}


def _cells(db, monkeypatch, *, keyed_read=True):
    """The six cells of ga_dashas' templated column: through the engine (`_measure_prose`) with the real chart_dashas DDL and its real unique key (chart_id, ayanamsha_id, system_id, level_n, ...)."""
    if keyed_read:
        monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 500)
        monkeypatch.setattr(ac, "KEYED_PARTITION_TARGET_ROWS", 600)
    return tt._measure(db, monkeypatch, tt._full(), scope=SCOPE)


def _count_keyed(monkeypatch):
    calls = []
    real = ac.keyed_read

    def counting(plan, *a, **k):
        calls.append(plan)
        return real(plan, *a, **k)
    monkeypatch.setattr(ac, "keyed_read", counting)
    return calls


def test_REAL_ENGINE_a_clean_chart_dashas_reads_the_same_six_cells_keyed_as_whole(db, monkeypatch):
    old = _cells(db, monkeypatch, keyed_read=False)                          # 2400 rows < 100 000: the older path
    fs.all_na(old)
    calls = _count_keyed(monkeypatch)
    new = _cells(db, monkeypatch)
    assert calls and calls[0].columns == ("chart_id", "ayanamsha_id", "system_id", "level_n") and len(calls[0].partitions) == 6
    assert json.dumps(new, sort_keys=True, default=str) == json.dumps(old, sort_keys=True, default=str)


@pytest.mark.parametrize("bad,needle", [
    ("Jupiter rules the dasha because it is exalted in the tenth house", "matches none of the 3 declared template(s)"),
    ("chart_dashas.vimshottari.L1.Sun@chart={b}:ay=raman:eng=pyjhora_adapter/0.1.0".format(b=CHART_B), "carries another chart's id"),
])
def test_REAL_ENGINE_a_planted_violation_is_the_same_FAIL_with_the_same_wording(db, monkeypatch, bad, needle):
    fs.psql(db, f"UPDATE chart_dashas SET citation_ref = '{bad}' WHERE ayanamsha_id = 'true_chitra' AND level_n = 2 AND start_iso = (SELECT min(start_iso) FROM chart_dashas WHERE ayanamsha_id = 'true_chitra' AND level_n = 2)")
    old = _cells(db, monkeypatch, keyed_read=False)
    calls = _count_keyed(monkeypatch)
    new = _cells(db, monkeypatch)
    assert calls and old["Narr.agree"]["v"] == FAIL and needle in old["Narr.agree"]["measured"]
    assert new["Narr.agree"]["v"] == FAIL and new["Narr.agree"]["measured"] == old["Narr.agree"]["measured"]
    assert json.dumps(new, sort_keys=True, default=str) == json.dumps(old, sort_keys=True, default=str)


def test_REAL_ENGINE_a_slow_partition_reads_no_detector_with_the_coverage_in_the_cell(db, monkeypatch):
    kf.spy_scalar(monkeypatch, slow_marker="\"ayanamsha_id\" = 'raman'")
    got = _cells(db, monkeypatch)
    assert got["Narr.agree"]["v"] == NO_DET, got["Narr.agree"]["measured"]
    assert all(c["v"] == NO_DET for c in got.values())
    txt = got["Narr.agree"]["measured"]
    assert "covered 4 of 6 partition(s) (1600 of 2400 rows)" in txt and "chart_dashas(chart_id, ayanamsha_id, system_id, level_n)" in txt and "neither a PASS nor a FAIL" in txt


def test_REAL_ENGINE_counts_that_do_not_add_up_read_no_detector(db, monkeypatch):
    def lie(sql, out):
        if "'groups'" in sql:
            d = json.loads(out)
            d["groups"][0]["n"] -= 1
            return json.dumps(d)
        return out
    kf.spy_scalar(monkeypatch, rewrite=lie)
    got = _cells(db, monkeypatch)
    assert all(c["v"] == NO_DET for c in got.values()) and "not trusted" in got["Narr.agree"]["measured"]
