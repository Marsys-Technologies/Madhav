"""test_keyed_read_helper.py: the keyed exact read helper and the per-asset budget (Nikasha lane W3, n430 ga_dashas).

The helper splits a full-table read of a large table into one statement per partition of the table's leading index key. These tests run on a REAL table in the disposable PostgreSQL: the plan (index read from
the catalog, partitions, counts that must add up), the opt-in-by-structure gate, the soundness rules (a timed-out partition, a budget cut and an untrusted plan are never complete) and the coverage record.
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
import _keyed_fixture as kf  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401

T = "kt_helper"


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


def test_the_plan_partitions_by_the_leading_key_of_the_natural_key_index(table):
    plan = ac.keyed_plan(table)
    assert plan is not None and plan.columns == ("a",) and plan.index == f"{T}_nat"
    assert [p.key for p in plan.partitions] == [("1",), ("2",), ("3",)] and [p.n for p in plan.partitions] == [1000, 1000, 1000]
    assert plan.total == 3000 and sum(p.n for p in plan.partitions) == plan.total
    assert [p.pred for p in plan.partitions][0] == '"a" = \'1\''


def test_the_prefix_is_lengthened_until_the_largest_partition_is_small_enough(table, monkeypatch):
    monkeypatch.setattr(ac, "KEYED_PARTITION_TARGET_ROWS", 600)
    plan = ac.keyed_plan(table)
    assert plan.columns == ("a", "b") and len(plan.partitions) == 6 and {p.n for p in plan.partitions} == {500}
    monkeypatch.setattr(ac, "KEYED_PARTITION_TARGET_ROWS", 10)          # nothing is small enough: the third index column `id` is a per-row key (too many partitions), so the two-column prefix is kept
    monkeypatch.setattr(ac, "KEYED_MAX_PARTITIONS", 100)
    plan = ac.keyed_plan(table)
    assert plan.columns == ("a", "b") and len(plan.partitions) == 6


def test_the_in_scope_count_is_the_chart_scope_not_the_table(table):
    ac.psql(f"INSERT INTO {table} (chart_id, a, b) SELECT '{kf.OTHER}'::uuid, 1, 1 FROM generate_series(1, 700)")
    ac.psql(f"ANALYZE {table}")
    kf.scope_to_chart(table)
    plan = ac.keyed_plan(table)
    assert plan.total == 3000 and [p.n for p in plan.partitions] == [1000, 1000, 1000]
    ac.set_read_scope(None)
    assert ac.keyed_plan(table).total == 3700


def test_a_null_key_value_is_its_own_partition(table):
    ac.psql(f"UPDATE {table} SET a = NULL WHERE a = 3 AND b = 2")
    ac.psql(f"ANALYZE {table}")
    plan = ac.keyed_plan(table)
    keys = {p.key: p for p in plan.partitions}
    assert keys[(None,)].n == 500 and keys[(None,)].pred == '"a" IS NULL' and plan.total == 3000
    for p in plan.partitions:                                             # every partition predicate selects exactly the rows the plan counted
        assert int(ac.scalar(f'SELECT count(*) FROM "{table}" WHERE {p.pred}')) == p.n


def test_below_the_threshold_there_is_no_plan_and_no_catalog_statement(table, monkeypatch):
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 3000)                # exactly the in-scope count: MORE than the threshold is required
    spy = kf.spy_scalar(monkeypatch)
    assert ac.keyed_plan(table) is None
    assert not any("pg_index" in s or "GROUP BY" in s for s in spy.calls)    # the estimate (est <= threshold) ended it: the plan statements were never issued
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 2999)
    assert ac.keyed_plan(table) is not None


def test_a_table_large_in_the_catalog_but_small_in_scope_keeps_the_older_path(table, monkeypatch):
    ac.psql(f"INSERT INTO {table} (chart_id, a, b) SELECT '{kf.OTHER}'::uuid, 1, 1 FROM generate_series(1, 6000)")
    ac.psql(f"ANALYZE {table}")
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 3500)
    kf.scope_to_chart(table)                                            # 3000 rows in scope <= 3500, catalog estimate 9000 > 3500
    assert ac.keyed_plan(table) is None


def test_no_usable_index_means_no_plan(disposable_pg, monkeypatch):
    kf.make_table(disposable_pg, monkeypatch, "kt_noidx", per_cell=500, index=False)     # only the single-column unique primary key: it partitions nothing
    kf.shrink(monkeypatch)
    try:
        assert ac.keyed_plan("kt_noidx") is None
    finally:
        kf.drop_table("kt_noidx")


def test_a_table_the_catalog_cannot_estimate_keeps_the_older_path(table, monkeypatch):
    monkeypatch.setattr(ac, "source_estimate_rows", lambda t: None)
    assert ac.keyed_plan(table) is None


def test_failed_plan_statements_fall_back_to_the_older_path(table, monkeypatch):
    def boom(sql):
        raise ac.Unknown("psql: connection refused")
    monkeypatch.setattr(ac, "scalar", boom)
    assert ac.keyed_plan(table, est=10 ** 6) is None
    monkeypatch.setattr(ac, "scalar", lambda sql: "not json")
    assert ac.keyed_plan(table, est=10 ** 6) is None


def test_counts_that_do_not_add_up_make_the_plan_untrusted(table, monkeypatch):
    def lie(sql, out):
        if "'groups'" in sql:
            d = json.loads(out)
            d["groups"][0]["n"] -= 1
            return json.dumps(d)
        return out
    kf.spy_scalar(monkeypatch, rewrite=lie)
    with pytest.raises(ac.KeyedReadIncomplete, match="not trusted.*2999 row.*3000 are in scope"):
        ac.keyed_plan(table)
    assert issubclass(ac.KeyedReadIncomplete, ac.Unknown)


# ───────────────────────────────────── keyed_read and the per-asset budget ─────────────────────────────────────

def test_every_partition_answered_is_complete_and_the_coverage_is_recorded(table, monkeypatch):
    clock = kf.Clock()
    monkeypatch.setattr(ac, "_chunk_clock", clock)
    plan = ac.keyed_plan(table)

    def read(part):
        clock.t += 10
        return int(ac.scalar(f'SELECT count(*) FROM "{table}" WHERE {part.pred}'))
    budget = ac.AssetReadBudget()
    out = ac.keyed_read(plan, read, what="count", budget=budget)
    assert out.complete and [a for _p, a in out.answers] == [1000, 1000, 1000] and out.rows_covered == 3000
    assert budget.spent == 30 and budget.rows_covered == 3000 and budget.partitions_covered == 3
    assert budget.reads == [dict(what="count", partitions_covered=3, partitions_total=3, rows_covered=3000, rows_total=3000, secs=30.0, complete=True, stopped_on_finding=False)]


def test_a_timed_out_partition_is_unread_never_complete_and_the_others_are_still_read(table, monkeypatch):
    kf.spy_scalar(monkeypatch, slow_marker='"a" = \'2\'')
    plan = ac.keyed_plan(table)
    budget = ac.AssetReadBudget()
    out = ac.keyed_read(plan, lambda part: int(ac.scalar(f'SELECT count(*) FROM "{table}" WHERE {part.pred}')), what="count", budget=budget)
    assert not out.complete and [p.key for p, _a in out.answers] == [("1",), ("3",)] and [p.key for p, _w in out.unread] == [("2",)]
    assert "timed out" in out.unread[0][1]
    text = out.coverage_text(budget)
    assert "covered 2 of 3 partition(s) (2000 of 3000 rows)" in text and f"{table}(a)" in text and "partition (2) timed out" in text
    assert "statement timeout" not in text                                # the phrase would re-route a caller's timeout handling and lose the coverage
    assert budget.reads[0]["complete"] is False and budget.reads[0]["partitions_covered"] == 2


def test_another_error_is_not_swallowed(table):
    plan = ac.keyed_plan(table)

    def boom(part):
        raise ac.Unknown("ERROR:  permission denied for table x")
    with pytest.raises(ac.Unknown, match="permission denied"):
        ac.keyed_read(plan, boom, what="x", budget=ac.AssetReadBudget())
    out = ac.keyed_read(plan, boom, what="x", budget=ac.AssetReadBudget(), unread_reason=lambda e: "permission denied")   # unless the caller says it is an unread reason
    assert not out.complete and len(out.unread) == 3


def test_a_partition_that_changed_under_the_read_is_unread(table):
    plan = ac.keyed_plan(table)

    def read(part):
        if part.key == ("2",):
            raise ac.KeyedPartitionChanged("partition holds 1001 rows, the plan counted 1000")
        return "clean"
    out = ac.keyed_read(plan, read, what="x", budget=ac.AssetReadBudget())
    assert not out.complete and out.unread[0][0].key == ("2",) and "1001" in out.unread[0][1]


def test_the_asset_budget_cuts_the_read_and_the_rest_is_not_read(table, monkeypatch):
    clock = kf.Clock()
    monkeypatch.setattr(ac, "_chunk_clock", clock)
    plan = ac.keyed_plan(table)

    def read(part):
        clock.t += 40
        return "clean"
    budget = ac.AssetReadBudget(total_secs=60)
    out = ac.keyed_read(plan, read, what="x", budget=budget)
    assert [p.key for p, _a in out.answers] == [("1",), ("2",)] and [p.key for p in out.not_read] == [("3",)] and not out.complete
    assert "1 partition(s) not reached" in out.coverage_text(budget) and "60s ran out" in out.coverage_text(budget)


def test_the_budget_is_per_asset_not_per_read(table, monkeypatch):
    clock = kf.Clock()
    monkeypatch.setattr(ac, "_chunk_clock", clock)
    plan = ac.keyed_plan(table)

    def read(part):
        clock.t += 30
        return "clean"
    b = ac.begin_asset_read_budget(total_secs=100)
    first = ac.keyed_read(plan, read, what="column one")             # 90 s of the asset's 100 s
    assert first.complete and b.spent == 90
    second = ac.keyed_read(plan, read, what="column two")            # the SAME asset: 10 s are left, so one partition is read and the rest is cut
    assert len(second.answers) == 1 and len(second.not_read) == 2 and not second.complete
    assert ac.asset_read_budget() is b and [r["what"] for r in b.reads] == ["column one", "column two"]
    ac.end_asset_read_budget()
    fresh = ac.asset_read_budget()                                   # outside an asset run: a fresh budget every call, never a stale exhausted one
    assert fresh is not b and fresh.spent == 0 and ac.asset_read_budget() is not fresh


def test_a_finding_ends_the_read_early_and_is_recorded(table):
    plan = ac.keyed_plan(table)
    out = ac.keyed_read(plan, lambda part: part.key == ("2",), what="x", budget=ac.AssetReadBudget(), stop_when=lambda ans, o: ans is True)
    assert out.stopped and [p.key for p, _a in out.answers] == [("1",), ("2",)] and not out.complete


def test_the_constants_are_named_and_the_budget_is_larger_than_the_old_per_column_walk():
    assert ac.KEYED_READ_MIN_ROWS == 100_000 and ac.ASSET_READ_BUDGET_SECS > ac.PROSE_NONE_WALK_BUDGET_SECS == 600
    assert ac.AssetReadBudget().total_secs == ac.ASSET_READ_BUDGET_SECS


def test_the_measure_loop_installs_and_clears_one_budget_per_asset():
    src = pathlib.Path(ac.__file__).read_text()
    assert src.count("        begin_asset_read_budget()") == 1 and src.count("        end_asset_read_budget()") == 1
    i, j = src.index("        begin_asset_read_budget()"), src.index("        end_asset_read_budget()")
    assert "set_read_scope(None)" in src[i - 400:i] and "set_read_scope(None)" in src[j - 100:j]
