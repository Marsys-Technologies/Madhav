"""C38 — stubbed-connection unit tests for platform/scripts/teardown_v5_small_test_job.py.

No database, no production: `psycopg` is replaced by a recording fake. Covered: the happy path (the deletes run chart/run
scoped, in dependency order, in ONE transaction; the registry row is kept, restored inert and validated against the
migration-1304 shape), the receipts-before-run-rows order (the Nirmana monitor reads a receipt whose run cannot be found as
NON-test evidence), every refusal, attribution through the manifest's slice stamp when the cockpit watchdog has pruned the run
row, --dry-run, and drift guards against the writer's own delete orders. The SQL itself is executed against real tables in
platform/python-sidecar/tests/l3/gochara/test_c38_teardown_real_db.py.
"""
from __future__ import annotations

import importlib
import os
import re
import sys
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "platform/scripts/teardown_v5_small_test_job.py"
SIDECAR = REPO / "platform/python-sidecar"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "gochara-v5-small-test"

sys.path.insert(0, str(SCRIPT.parent))
import teardown_v5_small_test_job as teardown_mod  # noqa: E402

REGISTRY_ROW = dict(teardown_mod.EXPECTED_REGISTRY_ROW)
PRE_1304_ROW = {"scope": "per_chart", "is_active": False, "has_writer": True, "has_substeps": False,
                "writer_timeout_seconds": 600, "depends_on": [], "target_table": "kala_gochara_windows",
                "count_sql": "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='5.0'",
                "target_floor": 0, "estimated_seconds": None}
GEN_TABLES = [t for t, _ in teardown_mod.GENERATION_TABLES]


class _Harness:
    def __init__(self, *, published=None, seal=None, authority_generation=None, active_runs=None, rows=None,
                 test_runs=1, non_test_runs=0, foreign_receipts=0, unlinked_receipts=0, stamped=False,
                 receipts=0, registry_row="default"):
        self.statements: list[str] = []
        self.params: list[tuple] = []
        self.commits = 0
        self.rollbacks = 0
        self.published, self.seal, self.authority_generation = published, seal, authority_generation
        self.active_runs = active_runs or []
        self.rows = rows or {}
        self.test_runs, self.non_test_runs = test_runs, non_test_runs
        self.foreign_receipts, self.unlinked_receipts, self.stamped, self.receipts = foreign_receipts, unlinked_receipts, stamped, receipts
        self.registry_row = dict(REGISTRY_ROW) if registry_row == "default" else registry_row
        harness = self

        class FakeCur:
            def execute(self, sql, params=None):
                harness.statements.append(" ".join(sql.split()))
                harness.params.append(params)
                self._last = harness.statements[-1]

            def fetchall(self):
                if "state IN ('planned'" in self._last:
                    return harness.active_runs
                return []

            def fetchone(self):
                sql = self._last
                if "status = 'published'" in sql:
                    return harness.published
                if "FROM ka_gochara_generation_seal" in sql:
                    return harness.seal
                if "FROM kala_gochara_authority" in sql:
                    return None if harness.authority_generation is None else {"authoritative_generation": harness.authority_generation}
                if "FROM asset_registry WHERE asset_id" in sql:
                    return harness.registry_row
                if "triggered_by <> %s" in sql:
                    return {"n": harness.non_test_runs}
                if "input_generation_vector->>'stored_scope'" in sql:
                    return {"n": 1} if harness.stamped else None
                if "FROM asset_provenance_receipts r" in sql:
                    return {"n": harness.foreign_receipts}
                if "FROM asset_provenance_receipts" in sql and "build_id IS NULL" in sql:
                    return {"n": harness.unlinked_receipts}
                if "FROM asset_provenance_receipts" in sql:
                    return {"n": harness.receipts}
                if "count(*) AS n FROM build_runs" in sql:
                    return {"n": harness.test_runs}
                if "FROM build_run_assets" in sql:
                    return {"n": harness.rows.get("build_run_assets", 0)}
                if "FROM asset_throughput" in sql:
                    return {"n": harness.rows.get("asset_throughput", 0)}
                m = re.search(r"FROM (\w+) WHERE chart_id = %s AND generation = %s", sql)
                if m:
                    return {"n": harness.rows.get(m.group(1), 0)}
                return None

        class FakeConn:
            autocommit = False

            def cursor(self):
                return FakeCur()

            def commit(self):
                harness.commits += 1

            def rollback(self):
                harness.rollbacks += 1

            def close(self):
                pass

        self.conn = FakeConn()

    def deletes(self):
        return [s for s in self.statements if s.startswith("DELETE")]


def _run(harness: _Harness, *, dry_run: bool = False):
    fake_psycopg = types.ModuleType("psycopg")
    fake_rows = types.ModuleType("psycopg.rows")
    fake_rows.dict_row = object()
    fake_psycopg.rows = fake_rows
    fake_psycopg.connect = lambda *a, **k: harness.conn
    saved = {k: v for k, v in sys.modules.items() if k.startswith("psycopg")}
    prior_db_url = os.environ.get("DATABASE_URL")
    try:
        sys.modules["psycopg"] = fake_psycopg
        sys.modules["psycopg.rows"] = fake_rows
        os.environ["DATABASE_URL"] = "postgresql://fake/fake"
        importlib.reload(teardown_mod)
        teardown_mod.teardown(dry_run=dry_run)
    finally:
        for name in ("psycopg", "psycopg.rows"):
            sys.modules.pop(name, None)
        sys.modules.update(saved)
        if prior_db_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior_db_url


ROWS = {"ka_gochara_eval_window": 3, "ka_gochara_relationship_record": 4, "ka_gochara_contact": 5,
        "kala_gochara_coverage": 2, "ka_gochara_search_inventory": 2, "kala_gochara_publication": 1}


def _table_of(delete_sql):
    return re.match(r"DELETE FROM (\w+)", delete_sql).group(1)


def test_happy_path_one_transaction_in_dependency_order_registry_kept():
    h = _Harness(rows=dict(ROWS))
    _run(h)
    assert h.commits == 1 and h.rollbacks == 0
    tables = [_table_of(s) for s in h.deletes()]
    assert tables == (["asset_provenance_receipts", "build_run_assets", "build_runs", "asset_throughput"]
                      + GEN_TABLES)
    for s in h.deletes():
        params = h.params[h.statements.index(s)]
        t = _table_of(s)
        if t in ("build_run_assets", "build_runs"):
            assert params == (TRIGGERED_BY, CHART_ID)
        elif t in ("asset_throughput", "asset_provenance_receipts"):
            assert params == ("ka_gochara_v5", CHART_ID)
        else:
            assert params == (CHART_ID, "5.0") and "chart_id = %s AND generation = %s" in s
    assert not any("DELETE FROM asset_registry" in s for s in h.statements)
    flips = [s for s in h.statements if "SET is_active" in s]
    assert len(flips) == 1 and "is_active = false" in flips[0]


def test_receipts_are_deleted_before_the_run_rows():
    """build_runs -> receipts is ON DELETE SET NULL: deleting the run first would leave a receipt whose run 'cannot be found',
    which the Nirmana monitor (N-137) reads as NON-test evidence. The receipts go first."""
    tables = [_table_of(s) for s in _delete_list()]
    assert tables.index("asset_provenance_receipts") < tables.index("build_runs")
    assert tables.index("build_run_assets") < tables.index("build_runs")


def _delete_list():
    h = _Harness(rows=dict(ROWS))
    _run(h)
    return h.deletes()


def test_only_the_coverage_event_class_partitions_are_deleted_moon_partitions_stay():
    coverage = [s for s in _delete_list() if _table_of(s) == "kala_gochara_coverage"]
    assert len(coverage) == 1 and "partition_kind = 'event_class'" in coverage[0]


def test_the_chain_and_inventory_orders_are_the_writers_own():
    """Drift guard: the teardown must delete what the writer's replace deletes, in the writer's order."""
    sys.path.insert(0, str(SIDECAR))
    from services.gochara_kernel import inventory_store as inv
    chain = [t for t, _ in teardown_mod.CHAIN_TABLES]
    assert chain == ["ka_gochara_eval_window", "ka_gochara_relationship_record", "ka_gochara_contact", "kala_gochara_coverage"]
    inventory = [t for t, _ in teardown_mod.INVENTORY_TABLES]
    assert inventory == [*inv._CLASS_TABLES_DELETE_ORDER, "ka_gochara_search_input_snapshot"]


def test_the_registry_shape_is_the_dispatchs_1304_shape():
    dispatch = SCRIPT.parent / "dispatch_v5_small_test_job.py"
    if not dispatch.exists():
        pytest.skip("dispatch_v5_small_test_job.py is not in this tree yet (PR 3097); the equality is asserted once both are")
    import dispatch_v5_small_test_job as d
    assert teardown_mod.EXPECTED_REGISTRY_ROW == d.EXPECTED_REGISTRY_ROW


def test_the_pre_1304_registry_row_is_refused_and_everything_rolls_back():
    """The reviewed defect: the old check expected the 1243 shape, so after 1304 the post-delete validation always raised."""
    h = _Harness(rows=dict(ROWS), registry_row=dict(PRE_1304_ROW))
    with pytest.raises(RuntimeError, match=r"has_substeps|writer_timeout_seconds|depends_on"):
        _run(h)
    assert h.commits == 0 and h.rollbacks == 1


@pytest.mark.parametrize("field, bad", [("has_substeps", False), ("writer_timeout_seconds", 600), ("depends_on", []),
                                        ("target_table", "kala_gochara_windows"), ("is_active", True)])
def test_every_field_of_the_1304_shape_is_checked(field, bad):
    h = _Harness(rows=dict(ROWS), registry_row=dict(REGISTRY_ROW, **{field: bad}))
    with pytest.raises(RuntimeError, match=field):
        _run(h)
    assert h.commits == 0 and h.rollbacks == 1


def test_registry_row_missing_is_a_loud_failure():
    h = _Harness(rows=dict(ROWS), registry_row=None)
    with pytest.raises(RuntimeError, match="missing"):
        _run(h)
    assert h.commits == 0


@pytest.mark.parametrize("kw, match", [
    (dict(published={"manifest_id": "m1"}), "PUBLISHED"),
    (dict(seal={"manifest_id": "m9"}), "seal"),
    (dict(authority_generation="5.0"), "serving"),
    (dict(active_runs=[{"id": "r1", "state": "running"}]), "active build_runs"),
    (dict(non_test_runs=1), "NON-test build run"),
    (dict(foreign_receipts=2), "not a 'gochara-v5-small-test' run"),
    (dict(rows=dict(ROWS), test_runs=0, stamped=False), "not produced by a small-test run|NO build_runs row"),
    (dict(unlinked_receipts=2, test_runs=1, stamped=False, rows={}), "cannot be attributed"),
    (dict(unlinked_receipts=1, test_runs=0, stamped=False, rows={}), "run-less receipt"),
], ids=["published", "seal", "authority", "active", "non_test_run", "foreign_receipt", "unattributed_rows",
        "unlinked_receipts_unstamped", "unlinked_receipts_no_runs"])
def test_every_refusal_deletes_nothing(kw, match):
    h = _Harness(**kw)
    with pytest.raises(RuntimeError, match=match):
        _run(h)
    assert h.commits == 0 and h.rollbacks == 1
    assert h.deletes() == []


def test_a_stamped_manifest_attributes_the_output_when_the_watchdog_pruned_the_run_row():
    """Run rows are pruned by the cockpit watchdog; the slice stamp lives in the manifest itself, so a pruned small test is
    still removable — including run-less receipts."""
    h = _Harness(rows=dict(ROWS), test_runs=0, stamped=True, unlinked_receipts=2, receipts=2)
    _run(h)
    assert h.commits == 1 and h.rollbacks == 0
    assert _table_of(h.deletes()[0]) == "asset_provenance_receipts"


def test_a_test_run_attributes_the_output_without_a_stamp():
    h = _Harness(rows=dict(ROWS), test_runs=1, stamped=False)
    _run(h)
    assert h.commits == 1


def test_nothing_at_all_is_a_clean_noop_teardown():
    h = _Harness(rows={}, test_runs=0, stamped=False)
    _run(h)
    assert h.commits == 1 and len(h.deletes()) == 4 + len(GEN_TABLES)         # every delete is scoped; they just match nothing


def test_dry_run_lists_every_table_and_rolls_back(capsys):
    h = _Harness(rows={**ROWS, "build_run_assets": 1, "asset_throughput": 1}, receipts=2)
    _run(h, dry_run=True)
    assert h.commits == 0 and h.rollbacks == 1 and h.deletes() == []
    out = capsys.readouterr().out
    listed = {line.split("\t")[0] for line in out.splitlines() if "\t" in line}
    assert listed == {"asset_provenance_receipts", "build_run_assets", "build_runs", "asset_throughput", *GEN_TABLES}
    assert "ka_gochara_contact\t5" in out and "asset_provenance_receipts\t2" in out and "build_runs\t1" in out
