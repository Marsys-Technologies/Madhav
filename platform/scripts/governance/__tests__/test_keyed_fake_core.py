"""test_keyed_fake_core.py: the keyed exact read, proven with a FAKE psql runner (no database is started): the plan, the budget and the templated-column read.

The soundness claims are proven here on planted per-partition results (clean, one violating partition, one timed-out partition, counts that do not add up, a partition that changed under the read,
a table below the threshold). The same claims are also written against a real table in test_keyed_read_helper.py / test_keyed_templated.py, which need the disposable PostgreSQL.
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
import _keyed_fake as kfk  # noqa: E402
import _keyed_fixture as kf  # noqa: E402
import prose_forms as pf  # noqa: E402

CHART = kf.CHART
RX = pf.compile_each(["ref.{n}@chart={chart_id}"], {"n": {"class": "int"}}, CHART)


@pytest.fixture(autouse=True)
def _clean_state():
    ac.set_read_scope(None)
    ac.end_asset_read_budget()
    yield
    ac.set_read_scope(None)
    ac.end_asset_read_budget()


def three(**plants):
    parts = {k: dict(v) for k, v in kfk.THREE.items()}
    for k, v in plants.items():
        parts[k.lstrip("p")].update(v)
    return parts


def db_for(monkeypatch, parts=None, **kw):
    return kfk.FakeKeyedDB(parts or three(), **kw).on("'unmatched'", kfk.templated_handler).install(monkeypatch)


# ───────────────────────────────────────── the plan ─────────────────────────────────────────

def test_the_plan_lists_the_partitions_and_their_counts_add_up(monkeypatch):
    db_for(monkeypatch)
    plan = ac.keyed_plan("kt")
    assert plan.columns == ("a",) and plan.index == "kt_idx" and plan.total == 120000
    assert [p.key for p in plan.partitions] == [("1",), ("2",), ("3",)] and sum(p.n for p in plan.partitions) == plan.total


def test_counts_that_do_not_add_up_make_the_plan_untrusted(monkeypatch):
    db = db_for(monkeypatch)
    db.groups_lie = 1
    with pytest.raises(ac.KeyedReadIncomplete, match="not trusted.*120001 row.*120000 are in scope"):
        ac.keyed_plan("kt")
    db.groups_lie, db.total = 0, 120001                                  # the other direction: the independent in-scope count is larger than the partitions
    with pytest.raises(ac.KeyedReadIncomplete, match="not trusted"):
        ac.keyed_plan("kt")


def test_below_the_threshold_nothing_but_the_estimate_is_asked(monkeypatch):
    db = db_for(monkeypatch, est=100_000)                                # not MORE than the threshold
    assert ac.keyed_plan("kt") is None and len(db.calls) == 1 and "reltuples" in db.calls[0]


def test_large_in_the_catalog_but_small_in_scope_is_the_older_path(monkeypatch):
    db_for(monkeypatch, parts={"1": kfk.clean(60000), "2": kfk.clean(40000)}, est=900_000)
    assert ac.keyed_plan("kt") is None                                   # 100 000 in scope: not MORE than the threshold


def test_no_estimate_or_failed_plan_statements_fall_back_to_the_older_path(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda sql: None)
    assert ac.keyed_plan("kt") is None
    monkeypatch.setattr(ac, "source_estimate_rows", lambda t: 10 ** 6)
    monkeypatch.setattr(ac, "scalar", lambda sql: "not json")
    assert ac.keyed_plan("kt") is None

    def boom(sql):
        raise ac.Unknown("psql: connection refused")
    monkeypatch.setattr(ac, "scalar", boom)
    assert ac.keyed_plan("kt") is None


def test_a_single_column_unique_key_partitions_nothing(monkeypatch):
    db_for(monkeypatch, unique=True)
    assert ac.keyed_plan("kt") is None


def test_the_prefix_is_lengthened_only_while_a_partition_is_too_large(monkeypatch):
    db = db_for(monkeypatch, parts={"1": kfk.clean(15000), "2": kfk.clean(15000)}, est=900_000)
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 20_000)
    plan = ac.keyed_plan("kt")                                           # largest partition 15 000 <= 20 000: one column is enough, one groups statement
    assert plan.columns == ("a",) and sum("'groups'" in s for s in db.calls) == 1


# ───────────────────────────────────────── the budget ─────────────────────────────────────────

def test_the_budget_is_per_asset_and_records_coverage(monkeypatch):
    db_for(monkeypatch)
    plan = ac.keyed_plan("kt")
    clock = kf.Clock()
    monkeypatch.setattr(ac, "_chunk_clock", clock)

    def read(part):
        clock.t += 30
        return "clean"
    b = ac.begin_asset_read_budget(total_secs=100)
    first = ac.keyed_read(plan, read, what="column one")
    assert first.complete and b.spent == 90
    second = ac.keyed_read(plan, read, what="column two")
    assert len(second.answers) == 1 and len(second.not_read) == 2 and not second.complete
    assert [(r["what"], r["partitions_covered"], r["rows_covered"], r["complete"]) for r in b.reads] == [("column one", 3, 120000, True), ("column two", 1, 40000, False)]
    assert "covered 1 of 3 partition(s) (40000 of 120000 rows)" in second.coverage_text(b) and "2 partition(s) not reached" in second.coverage_text(b)
    ac.end_asset_read_budget()
    assert ac.asset_read_budget() is not ac.asset_read_budget() and ac.asset_read_budget().spent == 0


def test_a_server_timeout_is_unread_with_a_reason_that_does_not_carry_the_timeout_phrase(monkeypatch):
    db_for(monkeypatch)
    plan = ac.keyed_plan("kt")

    def read(part):
        if part.key == ("2",):
            raise ac.Unknown(kfk.TIMEOUT)
        return "clean"
    b = ac.AssetReadBudget()
    out = ac.keyed_read(plan, read, what="x", budget=b)
    text = out.coverage_text(b)
    assert not out.complete and [p.key for p, _w in out.unread] == [("2",)] and "covered 2 of 3 partition(s) (80000 of 120000 rows)" in text
    assert "partition (2) timed out" in text and "statement timeout" not in text


def test_another_error_propagates_and_a_changed_partition_is_always_unread(monkeypatch):
    db_for(monkeypatch)
    plan = ac.keyed_plan("kt")

    def boom(part):
        raise ac.Unknown("ERROR:  permission denied for table x")
    with pytest.raises(ac.Unknown, match="permission denied"):
        ac.keyed_read(plan, boom, what="x", budget=ac.AssetReadBudget())

    def changed(part):
        raise ac.KeyedPartitionChanged("holds 40001 row(s), the plan counted 40000")
    out = ac.keyed_read(plan, changed, what="x", budget=ac.AssetReadBudget())
    assert not out.complete and len(out.unread) == 3 and "40001" in out.unread[0][1]


def test_a_finding_ends_the_read_early(monkeypatch):
    db_for(monkeypatch)
    plan = ac.keyed_plan("kt")
    out = ac.keyed_read(plan, lambda part: part.key == ("2",), what="x", budget=ac.AssetReadBudget(), stop_when=lambda ans, o: ans is True)
    assert out.stopped and [p.key for p, _a in out.answers] == [("1",), ("2",)] and not out.complete


# ─────────────────────────── the templated-column read, keyed vs whole ───────────────────────────

def keyed(**kw):
    return ac._formgap_templated_read("kt", "citation_ref", RX, CHART, None)


def whole_answer(db):
    """What the whole-table statement answers on the same planted data (the fake unions the partitions)."""
    return ac._formgap_templated_answer(json.loads(ac.scalar(ac.templated_read_sql("kt", "citation_ref", RX, CHART, None))), "x")


def test_clean_keyed_equals_clean_whole_and_each_partition_is_one_statement(monkeypatch):
    db = db_for(monkeypatch)
    got = keyed()
    assert got == whole_answer(db) == dict(unmatched=[], other_chart=[])
    assert len(db.partition_statements("'unmatched'")) == 3 and len(db.whole_statements("'unmatched'")) == 1      # (the one whole statement is the comparison above)
    assert all("'n', (SELECT count(*)" in s for s in db.partition_statements("'unmatched'"))


def test_a_planted_violation_in_one_partition_is_the_same_finding_as_whole(monkeypatch):
    db = db_for(monkeypatch, three(p2=dict(unmatched=["Jupiter rules the dasha"]), p3=dict(unmatched=["ref.1@chart=OTHER"], other=["ref.1@chart=OTHER"])))
    got = keyed()
    assert got == whole_answer(db) == dict(unmatched=["Jupiter rules the dasha", "ref.1@chart=OTHER"], other_chart=["ref.1@chart=OTHER"])


@pytest.mark.parametrize("where", ["1", "2", "3"])
def test_one_violation_is_found_whichever_partition_holds_it(monkeypatch, where):
    db = db_for(monkeypatch, three(**{"p" + where: dict(unmatched=["a free sentence"])}))
    assert keyed() == whole_answer(db) == dict(unmatched=["a free sentence"], other_chart=[])


def test_many_violations_give_the_bounded_sample(monkeypatch):
    db = db_for(monkeypatch, three(p1=dict(unmatched=["s1", "s2", "s3", "s4"], other=["o1"]), p2=dict(unmatched=["s5"], other=["o2", "o3", "o4"])))
    got = keyed()
    assert got == whole_answer(db) == dict(unmatched=["s1", "s2", "s3"], other_chart=["o1", "o2", "o3"])
    assert len(db.partition_statements("'unmatched'")) == 2              # both sample lists are full after the second partition: the third is not needed


def test_a_timed_out_partition_is_unread_never_clean(monkeypatch):
    db = db_for(monkeypatch, three(p2=dict(timeout=True)))
    got = keyed()
    assert set(got) == {"unread"}
    t = got["unread"]
    assert "covered 2 of 3 partition(s) (80000 of 120000 rows)" in t and "kt.citation_ref (templated pointer) by kt(a)" in t and "partition (2) timed out" in t
    assert "asset read budget" in t and "neither a PASS nor a FAIL" in t and "statement timeout" not in t
    assert len(db.partition_statements("'unmatched'")) == 3             # the other partitions were still read


def test_a_violation_in_a_read_partition_stands_when_another_partition_timed_out(monkeypatch):
    db_for(monkeypatch, three(p1=dict(unmatched=["a free sentence"]), p3=dict(timeout=True)))
    assert keyed() == dict(unmatched=["a free sentence"], other_chart=[])


def test_counts_that_do_not_add_up_leave_the_read_unread(monkeypatch):
    db = db_for(monkeypatch)
    db.groups_lie = 5
    got = keyed()
    assert set(got) == {"unread"} and "not trusted" in got["unread"] and "neither a PASS nor a FAIL" in got["unread"]
    assert db.partition_statements("'unmatched'") == []                 # no partition was read from an untrusted plan


def test_a_partition_that_changed_under_the_read_is_unread(monkeypatch):
    db_for(monkeypatch, three(p1=dict(read_n=40001)))
    got = keyed()
    assert set(got) == {"unread"} and "partition (1) holds 40001 row(s), the plan counted 40000" in got["unread"] and "covered 2 of 3" in got["unread"]


def test_the_asset_budget_running_out_is_unread(monkeypatch):
    db_for(monkeypatch)
    clock = kf.Clock()
    monkeypatch.setattr(ac, "_chunk_clock", clock)
    real = ac.scalar

    def slow(sql):
        if '"a" = ' in sql:
            clock.t += 50
        return real(sql)
    monkeypatch.setattr(ac, "scalar", slow)
    ac.begin_asset_read_budget(total_secs=60)
    got = keyed()
    assert set(got) == {"unread"} and "covered 2 of 3" in got["unread"] and "1 partition(s) not reached" in got["unread"] and "60s ran out" in got["unread"]


def test_the_budget_is_shared_by_two_columns_of_one_asset(monkeypatch):
    db_for(monkeypatch)
    clock = kf.Clock()
    monkeypatch.setattr(ac, "_chunk_clock", clock)
    real = ac.scalar

    def slow(sql):
        if '"a" = ' in sql:
            clock.t += 30
        return real(sql)
    monkeypatch.setattr(ac, "scalar", slow)
    b = ac.begin_asset_read_budget(total_secs=100)
    assert keyed() == dict(unmatched=[], other_chart=[]) and b.spent == 90          # column one spends 90 s of the asset's 100 s
    got = ac._formgap_templated_read("kt", "other_col", RX, CHART, None)           # column two of the SAME asset: 10 s left, so one partition then the cut
    assert set(got) == {"unread"} and "covered 1 of 3" in got["unread"] and "kt.other_col" in got["unread"]


def test_any_other_failure_of_a_partition_is_still_an_error_not_an_unread(monkeypatch):
    db = db_for(monkeypatch)
    real = ac.scalar

    def boom(sql):
        if '"a" = ' in sql:
            raise ac.Unknown("ERROR:  syntax error at or near x")
        return real(sql)
    monkeypatch.setattr(ac, "scalar", boom)
    with pytest.raises(ac.Unknown, match="syntax error"):
        keyed()


def test_below_the_threshold_the_older_path_runs_and_the_keyed_reader_never_does(monkeypatch):
    db = db_for(monkeypatch, est=100_000)
    parts = []
    real_sql = ac.templated_read_sql

    def spy_sql(*a, **k):
        parts.append(k.get("part", a[5] if len(a) > 5 else None))
        return real_sql(*a, **k)
    monkeypatch.setattr(ac, "templated_read_sql", spy_sql)

    def never(*a, **k):
        raise AssertionError("the keyed reader must not run below the threshold")
    monkeypatch.setattr(ac, "keyed_read", never)
    assert keyed() == dict(unmatched=[], other_chart=[]) and parts == [None]
    assert not any("pg_index" in s or "'groups'" in s for s in db.calls)


def test_the_whole_table_statement_is_unchanged_without_a_partition():
    sql = ac.templated_read_sql("chart_dashas", "citation_ref", RX, CHART, None)
    assert sql == ac.templated_read_sql("chart_dashas", "citation_ref", RX, CHART, None, None) and "'n'" not in sql
    ks = ac.templated_read_sql("chart_dashas", "citation_ref", RX, CHART, None, ac.KeyedPartition(("ayanamsha_id",), ("raman",), 5))
    assert "\"ayanamsha_id\" = 'raman'" in ks and "'n', (SELECT count(*)" in ks and sql.count("LIMIT 3") == ks.count("LIMIT 3") == 2


def test_the_coverage_is_recorded_in_the_asset_budget(monkeypatch):
    db_for(monkeypatch)
    b = ac.begin_asset_read_budget()
    assert keyed() == dict(unmatched=[], other_chart=[])
    r = b.reads[0]
    assert r["what"] == "kt.citation_ref (templated pointer)"
    assert (r["partitions_covered"], r["partitions_total"], r["rows_covered"], r["rows_total"], r["complete"]) == (3, 3, 120000, 120000, True)
    assert b.rows_covered == 120000 and b.partitions_covered == 3
