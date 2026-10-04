"""C38 — stubbed-connection unit tests for platform/scripts/teardown_v5_small_test_job.py.

No database, no production: `psycopg` is replaced by a recording fake. Covered (round 2, ASTRA's review of PR 3098): the locks are
taken before any ownership check; run membership is read from `build_run_assets` (layer runs and comma-separated sets included);
a small-test run must be exclusively this asset's; a NULL-linked receipt is refused and named; the generation's output is deleted
only when the CURRENT manifest proves a test slice (a historical test run is never enough); the legacy ledger tables are guarded,
never deleted; the freshness row goes with the receipts; the default is a dry run and deleting needs `--execute` plus
`--i-am-steward`; the DSN comes from the environment only; a failure prints the exception class, never its text; and the chain /
inventory delete orders are read from the kernel's REAL helpers run against a recording connection. The SQL itself is executed
against real tables in platform/python-sidecar/tests/l3/gochara/test_c38_teardown_real_db.py.
"""
from __future__ import annotations

import contextlib
import os
import re
import sys
import types
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "platform/scripts/teardown_v5_small_test_job.py"
SIDECAR = REPO / "platform/python-sidecar"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "gochara-v5-small-test"
ASSET = "ka_gochara_v5"

sys.path.insert(0, str(SCRIPT.parent))
import teardown_v5_small_test_job as teardown_mod  # noqa: E402

REGISTRY_ROW = dict(teardown_mod.EXPECTED_REGISTRY_ROW)
PRE_1304_ROW = {"scope": "per_chart", "is_active": False, "has_writer": True, "has_substeps": False,
                "writer_timeout_seconds": 600, "depends_on": [], "target_table": "kala_gochara_windows",
                "count_sql": "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='5.0'",
                "target_floor": 0, "estimated_seconds": None}
GEN_TABLES = [t for t, _ in teardown_mod.GENERATION_TABLES]
RUN_1 = str(uuid.uuid4())
_W = teardown_mod._writer()
_SL = _W._validate_test_slice({"schema": _W.TEST_SLICE_SCHEMA, "run": "one_class_full",
                               "horizon": [_W.DEFAULT_HORIZON[0].isoformat(), _W.DEFAULT_HORIZON[1].isoformat()],
                               "classes": [_W.SCORED_CLASSES[0]]})
STAMP = {"stored_scope": _W.TEST_SLICE_SCOPE, "test_slice": _W._slice_component(_SL)}      # exactly what the writer stamps
HORIZON = types.SimpleNamespace(lower=_SL.horizon[0], upper=_SL.horizon[1])
STAMPED = {"status": "candidate", "input_generation_vector": STAMP, "horizon": HORIZON}
UNSTAMPED = {"status": "candidate", "input_generation_vector": {"stored_scope": "stored_non_moon"}, "horizon": HORIZON}


def _test_run(rid=RUN_1, **kw):
    return dict({"id": rid, "triggered_by": TRIGGERED_BY, "scope": "asset", "scope_target": ASSET, "assets": [ASSET]}, **kw)


class _Harness:
    def __init__(self, *, lock_got=True, published=None, seal=None, authority_generation=None, active=None, members="one",
                 foreign_on_owned=None, elsewhere=None, receipts="linked", legacy=None, absent=(), manifest="stamped", rows="default",
                 registry_row="default", fail_on=None, connect_error=None, snapshot="consistent", inventory_mismatch=0,
                 registry_active=False, freshness_elsewhere=0, catalog_status="CURRENT", dependents=None, evidence=None,
                 evidence_after=None, commit_error=None, rollback_error=None, retention="default"):
        self.statements: list[str] = []
        self.params: list[tuple] = []
        self.commits = self.rollbacks = 0
        self.closed = False
        self.lock_got, self.published, self.seal, self.authority_generation = lock_got, published, seal, authority_generation
        self.active = active or []
        self.members = [_test_run()] if members == "one" else (members or [])
        self.foreign_on_owned, self.elsewhere = foreign_on_owned or [], elsewhere or []
        self.receipts = [{"partition_key": "p1", "build_id": RUN_1}] if receipts == "linked" else (receipts or [])
        self.legacy, self.absent = legacy or {}, set(absent)
        self.manifest = dict(STAMPED) if manifest == "stamped" else manifest
        self.rows = dict(ROWS) if rows == "default" else (rows or {})
        self.registry_row = dict(REGISTRY_ROW) if registry_row == "default" else registry_row
        self.fail_on, self.connect_error = fail_on, connect_error
        self.snapshot = {"same_vector": True, "input_digest": "d" * 64} if snapshot == "consistent" else snapshot
        self.inventory_mismatch = inventory_mismatch
        self.registry_active, self.freshness_elsewhere = registry_active, freshness_elsewhere
        self.catalog_status, self.dependents = catalog_status, dependents or []
        self.evidence, self.evidence_after = evidence or [], evidence_after      # evidence: rows for the end-state query (pre); after: post
        self.commit_error, self.rollback_error = commit_error, rollback_error
        self.retention = ([{"id": RUN_1, "created_at": "2026-10-01 10:00:00+00", "secs": 80 * 86400.0}]
                          if retention == "default" else retention)
        self.flipped = False
        self.end_state_calls = 0
        harness = self

        class FakeCur:
            def execute(self, sql, params=None):
                flat = " ".join(sql.split())
                harness.statements.append(flat)
                harness.params.append(params)
                self._last, self._params = flat, params
                if "SET is_active = false" in flat:
                    harness.flipped = True
                if flat.startswith("SELECT catalog_status"):
                    harness.end_state_calls += 1
                if harness.fail_on and harness.fail_on in flat:
                    raise Exception("could not connect: postgresql://svc:hunter2-secret@db.example/prod refused")

            def _evidence(self):
                # the end-state query: rows before the deletes, `evidence_after` (when given) after them
                if harness.evidence_after is not None and harness.flipped:
                    return harness.evidence_after
                return harness.evidence

            def fetchall(self):
                s = self._last
                if "state IN ('planned'" in s:
                    return harness.active
                if "GROUP BY r.id" in s:
                    return harness.members
                if "build_id = ANY(%s::uuid[]) AND asset_id <> %s" in s:
                    return harness.foreign_on_owned
                if "AND asset_id = %s AND chart_id IS DISTINCT FROM %s::uuid GROUP BY chart_id" in s:
                    return harness.elsewhere
                if "SELECT partition_key, build_id FROM asset_provenance_receipts" in s:
                    return harness.receipts
                if "WHERE %s = ANY(depends_on)" in s:
                    return harness.dependents
                if "FROM asset_provenance_receipts r WHERE r.asset_id" in s:
                    return [r for r in self._evidence() if r.get("kind") == "receipt"]
                if "FROM build_run_assets a LEFT JOIN build_runs b0" in s:
                    return [r for r in self._evidence() if r.get("kind") == "run_asset"]
                if "EXTRACT(EPOCH FROM" in s:
                    return harness.retention
                return []

            def fetchone(self):
                s = self._last
                if "pg_try_advisory_lock" in s:
                    return {"got": harness.lock_got}
                if "to_regclass" in s:
                    table = self._params[0].split(".")[1]
                    return {"r": None if table in harness.absent else f"public.{table}"}
                if "status = 'published'" in s:
                    return harness.published
                if "FROM ka_gochara_generation_seal" in s:
                    return harness.seal
                if "FROM kala_gochara_authority" in s:
                    return None if harness.authority_generation is None else {"authoritative_generation": harness.authority_generation}
                if s.startswith("SELECT catalog_status"):
                    return {"catalog_status": harness.catalog_status}
                if s.startswith("SELECT is_active FROM asset_registry"):
                    return {"is_active": harness.registry_active and not harness.flipped}
                if "FROM asset_registry WHERE asset_id" in s:
                    if harness.registry_row is None:
                        return None
                    row = dict(harness.registry_row)
                    if harness.registry_active and not harness.flipped:
                        row["is_active"] = True
                    return row
                if "SELECT status, input_generation_vector, horizon FROM kala_gochara_publication" in s:
                    return harness.manifest
                if "FROM ka_gochara_search_input_snapshot s JOIN kala_gochara_publication p" in s:
                    return harness.snapshot
                if "FROM ka_gochara_search_inventory i JOIN" in s:
                    return {"n": harness.inventory_mismatch}
                if "FROM asset_freshness WHERE asset_id = %s AND chart_id IS DISTINCT FROM" in s:
                    return {"n": harness.freshness_elsewhere}
                m = re.search(r"count\(\*\) AS n FROM (\w+) WHERE", s)
                if m:
                    table = m.group(1)
                    if table in teardown_mod.LEGACY_GUARD_TABLES:
                        return {"n": harness.legacy.get(table, 0)}
                    return {"n": harness.rows.get(table, 0)}
                return None

        class FakeConn:
            autocommit = False

            def cursor(self):
                return FakeCur()

            def commit(self):
                harness.commits += 1
                if harness.commit_error:
                    raise harness.commit_error

            def rollback(self):
                harness.rollbacks += 1
                if harness.rollback_error and harness.rollbacks == 1:
                    raise harness.rollback_error

            def close(self):
                harness.closed = True

        self.conn = FakeConn()

    def deletes(self):
        return [s for s in self.statements if s.startswith("DELETE")]


ROWS = {"ka_gochara_eval_window": 3, "ka_gochara_relationship_record": 4, "ka_gochara_contact": 5,
        "kala_gochara_coverage": 2, "ka_gochara_search_inventory": 2, "kala_gochara_publication": 1,
        "build_run_assets": 1, "asset_throughput": 1, "asset_provenance_receipts": 1, "asset_freshness": 1}


@contextlib.contextmanager
def _patched(harness, *, database_url="postgresql://fake/fake"):
    fake_psycopg = types.ModuleType("psycopg")
    fake_rows = types.ModuleType("psycopg.rows")
    fake_rows.dict_row = object()
    fake_psycopg.rows = fake_rows
    connects = []

    def connect(*a, **k):
        connects.append(a)
        if harness.connect_error:
            raise harness.connect_error
        return harness.conn
    fake_psycopg.connect = connect
    saved = {k: v for k, v in sys.modules.items() if k.startswith("psycopg")}
    prior = os.environ.get("DATABASE_URL")
    try:
        sys.modules["psycopg"], sys.modules["psycopg.rows"] = fake_psycopg, fake_rows
        if database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = database_url
        harness.connects = connects
        yield
    finally:
        for name in ("psycopg", "psycopg.rows"):
            sys.modules.pop(name, None)
        sys.modules.update(saved)
        if prior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior


def _run(harness, *, dry_run=False):
    with _patched(harness):
        teardown_mod.teardown(dry_run=dry_run)


def _table_of(delete_sql):
    return re.match(r"DELETE FROM (\w+)", delete_sql).group(1)


def _executed(h):
    return h.deletes()


# ── the happy path, the locks, the order ──────────────────────────────────────────────────────────────────────────────────────

def test_execute_happy_path_one_transaction_in_dependency_order_registry_kept():
    h = _Harness()
    _run(h)
    assert h.commits == 1 and h.closed
    tables = [_table_of(s) for s in h.deletes()]
    assert tables == ["asset_provenance_receipts", "asset_freshness", "build_run_assets", "build_runs", "asset_throughput", *GEN_TABLES]
    for s in h.deletes():
        params = h.params[h.statements.index(s)]
        t = _table_of(s)
        if t in ("build_run_assets", "build_runs"):
            assert params == ([RUN_1],) and "ANY(" in s                # ONLY the proven, exclusively-owned test runs
        elif t in ("asset_throughput", "asset_provenance_receipts", "asset_freshness"):
            assert params == (ASSET, CHART_ID)
        else:
            assert params == (CHART_ID, "5.0") and "chart_id = %s AND generation = %s" in s
    assert not any("DELETE FROM asset_registry" in s for s in h.statements)
    flips = [s for s in h.statements if "SET is_active" in s]
    assert len(flips) == 1 and "is_active = false" in flips[0]


def test_the_locks_are_taken_before_any_ownership_check_and_in_the_orchestrators_order():
    """Codex P1-1: the orchestrator exclusion lock (non-blocking), then lock_timeout, then the Gochara chart lock, and ONLY THEN
    the first SELECT that judges ownership."""
    h = _Harness()
    _run(h)
    s = h.statements
    assert "pg_try_advisory_lock(hashtext(%s))" in s[0] and h.params[0] == (CHART_ID,)
    assert "set_config('lock_timeout'" in s[1] and h.params[1] == (teardown_mod.LOCK_TIMEOUT,)
    assert "ka_gochara_lock_chart" in s[2] and h.params[2] == (CHART_ID,)
    assert "status = 'published'" in s[3]                              # the first check comes after all three
    first_delete = next(i for i, x in enumerate(s) if x.startswith("DELETE"))
    assert first_delete > 3 and h.commits == 1


def test_a_held_orchestrator_lock_refuses_before_anything_is_checked_or_deleted():
    h = _Harness(lock_got=False)
    with pytest.raises(teardown_mod.TeardownRefused, match="exclusion lock"):
        _run(h)
    assert len([x for x in h.statements if "published" in x or "build_runs" in x]) == 0   # no check ran
    assert h.deletes() == [] and h.commits == 0 and h.rollbacks >= 1 and h.closed


def test_the_orchestrator_lock_is_released_at_the_end():
    h = _Harness()
    _run(h)
    assert any("pg_advisory_unlock" in x for x in h.statements) and h.closed


# ── refusals that do not depend on ownership ──────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kw, match", [
    (dict(published={"manifest_id": "m1"}), "PUBLISHED"),
    (dict(seal={"manifest_id": "m9"}), "seal"),
    (dict(authority_generation="5.0"), "serving"),
    (dict(active=[{"id": "r1", "state": "running"}]), "active build_runs"),
], ids=["published", "seal", "authority", "active"])
def test_every_basic_refusal_deletes_nothing(kw, match):
    h = _Harness(**kw)
    with pytest.raises(teardown_mod.TeardownRefused, match=match):
        _run(h)
    assert h.commits == 0 and h.rollbacks >= 1 and h.deletes() == []


def test_the_active_check_is_any_run_on_the_chart_not_this_assets_scope_target():
    """Codex P1-2: a running LAYER build has scope_target 'kala'; the old check (asset_set, exact asset) missed it."""
    h = _Harness(active=[{"id": "layer-run", "state": "running"}])
    with pytest.raises(teardown_mod.TeardownRefused, match="layer-run"):
        _run(h)
    active_sql = next(s for s in h.statements if "state IN ('planned'" in s)
    assert "scope_target" not in active_sql and "scope =" not in active_sql


# ── run membership and exclusivity ────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("run", [
    {"id": "layer-1", "triggered_by": "cockpit-manual-build", "scope": "layer", "scope_target": "kala", "assets": [ASSET, "ka_other"]},
    {"id": "set-1", "triggered_by": "cockpit-manual-build", "scope": "asset_set", "scope_target": f"ga_positions,{ASSET}", "assets": [ASSET]},
    {"id": "plain-1", "triggered_by": "cockpit-manual-build", "scope": "asset", "scope_target": ASSET, "assets": [ASSET]},
], ids=["layer_run", "comma_separated_set", "single_asset"])
def test_a_non_test_run_that_includes_the_asset_is_refused_whatever_its_scope(run):
    h = _Harness(members=[_test_run(), run])
    with pytest.raises(teardown_mod.TeardownRefused, match=run["id"]):
        _run(h)
    assert h.deletes() == [] and h.commits == 0


def test_membership_is_read_from_build_run_assets_and_the_scope_target_tokens():
    h = _Harness()
    _run(h)
    sql = next(s for s in h.statements if "GROUP BY r.id" in s)
    assert "build_run_assets" in sql and "string_to_array(r.scope_target, ',')" in sql and "triggered_by" in sql


@pytest.mark.parametrize("run", [
    _test_run(assets=[ASSET, "ga_positions"]),
    _test_run(scope="asset_set", scope_target=f"{ASSET},ga_positions"),
], ids=["child_row_of_another_asset", "scope_target_names_another_asset"])
def test_a_test_run_that_also_holds_another_asset_is_refused_by_name_and_deleted_by_nobody(run):
    """Codex P1-4: deleting such a run would remove the other asset's bookkeeping and orphan its receipt."""
    h = _Harness(members=[run])
    with pytest.raises(teardown_mod.TeardownRefused, match=r"not exclusively.*ga_positions"):
        _run(h)
    assert h.deletes() == []


def test_another_assets_receipt_linked_to_the_test_run_is_refused():
    h = _Harness(foreign_on_owned=[{"asset_id": "ga_positions", "n": 1}])
    with pytest.raises(teardown_mod.TeardownRefused, match="ga_positions"):
        _run(h)
    assert h.deletes() == []


# ── receipts ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_null_linked_receipt_is_refused_and_named_even_when_the_manifest_is_stamped():
    """Codex P1-3: a pruned real run and a pruned test run look the same; a CURRENT stamp cannot establish the origin."""
    h = _Harness(members=[], receipts=[{"partition_key": "orphan-part", "build_id": None}], manifest="stamped")
    with pytest.raises(teardown_mod.TeardownRefused, match="NO run link.*orphan-part"):
        _run(h)
    assert h.deletes() == []


def test_a_receipt_linked_to_a_run_that_is_not_an_owned_test_run_is_refused():
    other = str(uuid.uuid4())
    h = _Harness(receipts=[{"partition_key": "p9", "build_id": other}])
    with pytest.raises(teardown_mod.TeardownRefused, match=other):
        _run(h)
    assert h.deletes() == []


def test_receipts_are_deleted_by_asset_and_chart_not_through_their_run_link_and_before_the_run_rows():
    h = _Harness()
    _run(h)
    receipt = next(s for s in h.deletes() if _table_of(s) == "asset_provenance_receipts")
    assert "build_id" not in receipt and h.params[h.statements.index(receipt)] == (ASSET, CHART_ID)
    tables = [_table_of(s) for s in h.deletes()]
    assert tables.index("asset_provenance_receipts") < tables.index("build_runs")
    assert tables.index("asset_freshness") < tables.index("build_runs")


def test_the_freshness_projection_of_the_asset_and_chart_is_deleted_with_the_receipts():
    """Codex P2-8: migration 596's registry trigger does not fire for an unchanged is_active, so a surviving 'fresh' row would
    outlive its receipt and output."""
    h = _Harness()
    _run(h)
    fresh = next(s for s in h.deletes() if _table_of(s) == "asset_freshness")
    assert h.params[h.statements.index(fresh)] == (ASSET, CHART_ID)


# ── ownership of the generation's output ─────────────────────────────────────────────────────────────────────────────────────

def test_a_test_run_alone_never_authorises_deleting_an_unstamped_candidate():
    """Codex P1-3 (this test used to enshrine the opposite): a historical test run exists, the CURRENT candidate is a full,
    unstamped one — refuse."""
    h = _Harness(manifest=dict(UNSTAMPED))
    with pytest.raises(teardown_mod.TeardownRefused, match="not PROVEN to be a test slice"):
        _run(h)
    assert h.deletes() == [] and h.commits == 0


def _comp(**changes):
    comp = dict(STAMP["test_slice"])
    comp.update(changes)
    return {"stored_scope": "test_slice", "test_slice": comp}


@pytest.mark.parametrize("vector, why", [
    ({"stored_scope": "test_slice"}, "no 'test_slice' component"),
    ({"test_slice": STAMP["test_slice"]}, "stored_scope is None"),
    (_comp(run="full"), "fails the writer's own validation"),
    (_comp(classes=[]), "fails the writer's own validation"),
    (_comp(classes=[""]), "fails the writer's own validation"),                          # Codex: classes=[""] used to reach all 15 DELETEs
    (_comp(classes=["not_a_scored_class"]), "fails the writer's own validation"),
    (_comp(horizon=["bogus", "backwards"]), "fails the writer's own validation"),         # Codex: arbitrary horizon strings
    (_comp(horizon=["2025-01-01T00:00:00", "2025-02-01T00:00:00"]), "fails the writer's own validation"),   # naive timestamps
    (_comp(schema="gochara_v5_test_slice/9"), "fails the writer's own validation"),
    (_comp(marker_digest="0" * 64), "not the writer's component for its marker"),         # the digest is recomputed and compared
    (_comp(extra_field=1), "not the writer's component for its marker"),
], ids=["scope_only", "component_only", "bad_run", "no_classes", "empty_class_name", "unscored_class", "bogus_horizon",
        "naive_horizon", "wrong_schema", "wrong_digest", "extra_field"])
def test_a_stamp_is_validated_by_the_writers_own_validator_and_digest(vector, why):
    h = _Harness(manifest={"status": "candidate", "input_generation_vector": vector, "horizon": HORIZON})
    with pytest.raises(teardown_mod.TeardownRefused, match=re.escape(why)):
        _run(h)
    assert h.deletes() == []


def test_the_stamp_is_validated_with_the_writers_function_not_a_second_implementation():
    """Codex round 2 P1 ruling: import the writer's validator. The script holds no copy of the marker rules."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert "_validate_test_slice" in source and "_slice_component" in source
    for rule_text in ("one_class_full", "all_classes_1y", "SCORED_CLASSES", "gochara_v5_test_slice/1"):
        assert rule_text not in source.replace("# ", ""), f"the script restates the writer's rule {rule_text!r}"


def test_the_manifests_horizon_must_be_the_stamps_horizon():
    other = types.SimpleNamespace(lower=_SL.horizon[0], upper=_SL.horizon[1].replace(year=2025))
    h = _Harness(manifest={"status": "candidate", "input_generation_vector": STAMP, "horizon": other})
    with pytest.raises(teardown_mod.TeardownRefused, match="horizon is not the stamp"):
        _run(h)
    assert h.deletes() == []


def test_an_interrupted_replacement_a_stamped_manifest_over_an_older_chain_is_refused_by_name():
    """Codex round 2 P1: a failed non-test candidate's output survives; a later small test stamps its manifest and fails before the
    snapshot substep replaces the old output. The stamp is valid, but the stored snapshot carries the OLD vector."""
    h = _Harness(snapshot={"same_vector": False, "input_digest": "d" * 64})
    with pytest.raises(teardown_mod.TeardownRefused, match="interrupted replacement"):
        _run(h)
    assert h.deletes() == [] and h.commits == 0


def test_output_without_a_snapshot_is_refused_and_a_manifest_alone_is_not():
    h = _Harness(snapshot=None)                                            # output rows exist, no snapshot binds them
    with pytest.raises(teardown_mod.TeardownRefused, match="no input snapshot binds them"):
        _run(h)
    h = _Harness(snapshot=None, rows={}, members=[], receipts=[])         # a stamped manifest and nothing else: removable
    _run(h)
    assert h.commits == 1


def test_inventory_headers_must_carry_the_stamped_manifests_identity():
    h = _Harness(inventory_mismatch=2)
    with pytest.raises(teardown_mod.TeardownRefused, match="2 inventory header"):
        _run(h)
    assert h.deletes() == []
    sql = next(x for x in _Harness().statements) if False else None
    h = _Harness()
    _run(h)
    inventory_sql = next(x for x in h.statements if "FROM ka_gochara_search_inventory i JOIN" in x)
    assert "i.input_digest <> s.input_digest" in inventory_sql and "i.horizon <> p.horizon" in inventory_sql
    assert "i.event_class = ANY" in inventory_sql
    assert h.params[h.statements.index(inventory_sql)][2] == STAMP["test_slice"]["classes"]


def test_output_rows_without_any_manifest_are_refused():
    h = _Harness(manifest=None)
    with pytest.raises(teardown_mod.TeardownRefused, match="NO manifest"):
        _run(h)
    assert h.deletes() == []


def test_a_complete_stamp_proves_the_test_slice_even_when_the_run_rows_were_pruned():
    h = _Harness(members=[], receipts=[], manifest="stamped")
    _run(h)
    assert h.commits == 1
    tables = [_table_of(s) for s in h.deletes()]
    assert "build_runs" in tables and h.params[h.statements.index(next(s for s in h.deletes() if _table_of(s) == "build_runs"))] == ([],)


def test_nothing_at_all_is_a_clean_noop_teardown():
    h = _Harness(rows={}, members=[], receipts=[], manifest=None)
    _run(h)
    assert h.commits == 1 and len(h.deletes()) == 5 + len(GEN_TABLES)         # every delete is scoped; they just match nothing


# ── the legacy ledger tables ──────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("table", ["kala_gochara_windows", "kala_gochara_contacts"])
def test_legacy_ledger_rows_of_5_0_are_refused_and_named_never_deleted(table):
    """Codex P1-5: the v5 writer writes neither table; rows there are not this test's."""
    h = _Harness(legacy={table: 3})
    with pytest.raises(teardown_mod.TeardownRefused, match=table):
        _run(h)
    assert h.deletes() == []


def test_a_legacy_table_is_never_in_a_delete_and_an_absent_one_is_skipped():
    h = _Harness(absent={"kala_gochara_windows", "kala_gochara_contacts"})
    _run(h)
    tables = [_table_of(s) for s in h.deletes()]
    assert not set(teardown_mod.LEGACY_GUARD_TABLES) & set(tables)
    assert not set(teardown_mod.LEGACY_GUARD_TABLES) & set(GEN_TABLES)
    assert "kala_gochara_publication" in tables and "ka_gochara_contact" in tables


def test_only_the_coverage_event_class_partitions_are_deleted_moon_partitions_stay():
    h = _Harness()
    _run(h)
    coverage = [s for s in h.deletes() if _table_of(s) == "kala_gochara_coverage"]
    assert len(coverage) == 1 and "partition_kind = 'event_class'" in coverage[0]


# ── the registry row ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_registry_shape_is_the_dispatchs_1304_shape():
    dispatch = SCRIPT.parent / "dispatch_v5_small_test_job.py"
    if not dispatch.exists():
        pytest.skip("dispatch_v5_small_test_job.py is not in this tree yet (PR 3097); the equality is asserted once both are")
    import dispatch_v5_small_test_job as d
    assert teardown_mod.EXPECTED_REGISTRY_ROW == d.EXPECTED_REGISTRY_ROW


def test_the_pre_1304_registry_row_is_refused_and_everything_rolls_back():
    h = _Harness(registry_row=dict(PRE_1304_ROW))
    with pytest.raises(RuntimeError, match=r"has_substeps|writer_timeout_seconds|depends_on"):
        _run(h)
    assert h.commits == 0 and h.rollbacks >= 1


@pytest.mark.parametrize("field, bad", [("has_substeps", False), ("writer_timeout_seconds", 600), ("depends_on", []),
                                        ("target_table", "kala_gochara_windows")])
def test_every_field_of_the_1304_shape_is_checked_before_and_after(field, bad):
    h = _Harness(registry_row=dict(REGISTRY_ROW, **{field: bad}))
    with pytest.raises(RuntimeError, match=field):
        _run(h)
    assert h.commits == 0 and h.deletes() == []                      # refused BEFORE the deletes: the dry-run path checks it too


def test_an_active_registry_row_is_restored_inert_inside_the_transaction_and_validated():
    h = _Harness(registry_active=True)
    _run(h)
    assert h.commits == 1 and any("SET is_active = false" in x for x in h.statements)


def test_registry_row_missing_is_a_loud_failure_even_in_a_dry_run():
    """ASTRA: the dry run used to skip registry validation, so a missing row passed it and failed the execution."""
    for dry in (True, False):
        h = _Harness(registry_row=None)
        with pytest.raises(RuntimeError, match="missing"):
            _run(h, dry_run=dry)
        assert h.commits == 0


# ── the dry run ───────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_dry_run_runs_the_same_statements_as_an_execution_and_only_the_last_step_differs(capsys):
    """Codex round 2 P2 ruling: both modes run the SAME statements and validation in the same transaction; the dry run then rolls
    back, with zero commits. The statement lists are identical."""
    dry, run = _Harness(), _Harness()
    _run(dry, dry_run=True)
    _run(run, dry_run=False)
    assert dry.statements == run.statements and dry.params == run.params
    assert dry.deletes() == run.deletes() and len(dry.deletes()) == 5 + len(GEN_TABLES)
    assert any("SET is_active = false" in x for x in dry.statements)                # the registry restore is rehearsed too
    assert dry.commits == 0 and dry.rollbacks >= 1 and dry.closed
    assert run.commits == 1
    assert any("SELECT catalog_status" in x for x in dry.statements)                # and the end-state validation


def test_the_dry_run_listing_names_every_table_and_the_retention_remaining(capsys):
    h = _Harness()
    _run(h, dry_run=True)
    out = capsys.readouterr().out
    listed = {line.split("\t")[0] for line in out.splitlines() if "\t" in line}
    assert listed >= {"asset_provenance_receipts", "asset_freshness", "build_run_assets", "build_runs", "asset_throughput",
                      *GEN_TABLES, *teardown_mod.LEGACY_GUARD_TABLES, "retention"}
    assert "ka_gochara_contact\t5" in out and "build_runs\t1" in out
    assert "kala_gochara_windows\tguard-only (never deleted)" in out
    assert f"run {RUN_1} created 2026-10-01 10:00:00+00: 80.0 day(s) of the 90-day cockpit retention remain" in out


def test_a_run_past_retention_is_flagged_in_the_listing(capsys):
    h = _Harness(retention=[{"id": RUN_1, "created_at": "2026-06-01", "secs": -3 * 86400.0}])
    _run(h, dry_run=True)
    assert "PAST RETENTION" in capsys.readouterr().out


def test_the_dry_run_names_an_absent_legacy_table(capsys):
    h = _Harness(absent={"kala_gochara_windows"})
    _run(h, dry_run=True)
    assert "kala_gochara_windows\tabsent" in capsys.readouterr().out


# ── the command line: intent, environment, credentials ────────────────────────────────────────────────────────────────────────

def test_with_no_flags_the_script_is_a_dry_run(capsys):
    h = _Harness()
    with _patched(h):
        assert teardown_mod.main([]) == 0
    assert h.commits == 0 and h.rollbacks >= 1                          # the statements ran, then ROLLED BACK
    assert "[dry-run]" in capsys.readouterr().err


def test_execute_without_the_steward_flag_is_refused_before_any_connection(capsys):
    h = _Harness()
    with _patched(h):
        with pytest.raises(SystemExit) as exc:
            teardown_mod.main(["--execute"])
    assert exc.value.code == 2 and h.connects == [] and h.deletes() == []
    assert "--i-am-steward" in capsys.readouterr().err


def test_execute_with_the_steward_flag_deletes():
    h = _Harness()
    with _patched(h):
        assert teardown_mod.main(["--execute", "--i-am-steward"]) == 0
    assert h.commits == 1 and h.deletes()


def test_the_steward_flag_alone_does_not_delete():
    h = _Harness()
    with _patched(h):
        assert teardown_mod.main(["--i-am-steward"]) == 0
    assert h.commits == 0 and h.rollbacks >= 1


def test_dry_run_and_execute_are_mutually_exclusive():
    h = _Harness()
    with _patched(h):
        with pytest.raises(SystemExit) as exc:
            teardown_mod.main(["--dry-run", "--execute", "--i-am-steward"])
    assert exc.value.code == 2 and h.connects == []


def test_the_database_url_comes_only_from_the_process_environment(capsys):
    h = _Harness()
    with _patched(h, database_url=None):
        assert teardown_mod.main(["--execute", "--i-am-steward"]) == 2
    assert h.connects == [] and "DATABASE_URL is not set" in capsys.readouterr().err
    source = SCRIPT.read_text(encoding="utf-8")
    assert ".env.local" not in source.replace("no longer reads `.env.local`", "") and "open(" not in source


def test_a_connection_error_prints_the_class_and_never_the_text(capsys):
    """Codex P2-6: a malformed-URI parse error carries the password token; the boundary prints the class only."""
    h = _Harness(connect_error=ValueError("invalid percent-encoding in postgresql://svc:hunter2-secret@db.example/prod"))
    with _patched(h):
        code = teardown_mod.main([])
    streams = capsys.readouterr()
    assert code == 1 and "ValueError" in streams.err and "No transaction was opened" in streams.err
    assert "hunter2" not in streams.err + streams.out and "postgresql://" not in streams.err + streams.out


def test_a_failure_mid_transaction_rolls_back_and_prints_no_exception_text(capsys):
    h = _Harness(fail_on="DELETE FROM build_runs")
    with _patched(h):
        code = teardown_mod.main(["--execute", "--i-am-steward"])
    streams = capsys.readouterr()
    assert code == 1 and h.commits == 0 and h.rollbacks >= 1
    assert "hunter2" not in streams.err + streams.out and "ROLLBACK CONFIRMED" in streams.err


def test_a_named_refusal_is_printed_with_its_ids(capsys):
    h = _Harness(members=[_test_run(), {"id": "layer-9", "triggered_by": "cockpit", "scope": "layer", "scope_target": "kala", "assets": [ASSET]}])
    with _patched(h):
        code = teardown_mod.main([])
    err = capsys.readouterr().err
    assert code == 1 and "teardown refused" in err and "layer-9" in err


# ── drift guard: the kernel's REAL delete helpers against a recording connection ────────────────────────────────────────────────

class _Recording:
    """Answers the sealed probe and the candidate-manifest lookup the helpers make; records every statement."""

    def __init__(self):
        self.statements: list[str] = []

    def execute(self, sql, params=None):
        flat = " ".join(sql.split())
        self.statements.append(flat)

        class _R:
            rowcount = 1

            def fetchone(self_inner):
                if "ka_gochara_generation_is_sealed" in flat:
                    return (False,)
                if "FROM kala_gochara_publication" in flat:
                    return (uuid.uuid4(), "candidate")
                return None

            def fetchall(self_inner):
                return []
        return _R()


def _deletes_of(conn):
    return [re.match(r"DELETE FROM (?:public\.)?(\w+)(.*?)(?: WHERE|$)", s).group(1) for s in conn.statements if s.startswith("DELETE")]


def test_the_chain_order_is_the_kernels_real_helper_not_a_second_hardcoded_list():
    """Codex P3-9: run RecordStore.delete_generation_chain and compare what it ACTUALLY deletes; a new output table in the
    writer's replace now fails this test."""
    sys.path.insert(0, str(SIDECAR))
    from services.gochara_kernel import record_store as rs
    conn = _Recording()
    rs.RecordStore(conn).delete_generation_chain(chart_id=CHART_ID, generation="5.0")
    assert _deletes_of(conn) == [t for t, _ in teardown_mod.CHAIN_TABLES]
    coverage = next(s for s in conn.statements if "kala_gochara_coverage" in s and s.startswith("DELETE"))
    assert teardown_mod.CHAIN_TABLES[-1][1].strip() in coverage                       # the event-class filter is the kernel's own


def test_the_inventory_order_is_the_kernels_real_helper():
    sys.path.insert(0, str(SIDECAR))
    from services.gochara_kernel import inventory_store as inv
    conn = _Recording()
    inv.InventoryStore(conn).delete_generation_inventory(CHART_ID, "5.0")
    assert _deletes_of(conn) == [t for t, _ in teardown_mod.INVENTORY_TABLES]


def test_the_drift_guard_fails_when_the_helper_gains_a_table(monkeypatch):
    """The guard is only worth having if it can fail: a helper that deletes one more table makes the comparison differ."""
    sys.path.insert(0, str(SIDECAR))
    from services.gochara_kernel import record_store as rs
    real = rs.RecordStore.delete_generation_chain

    def widened(self, *, chart_id, generation):
        out = real(self, chart_id=chart_id, generation=generation)
        self.conn.execute("DELETE FROM public.ka_gochara_new_output_table WHERE chart_id = %s AND generation = %s", (chart_id, generation))
        return out
    monkeypatch.setattr(rs.RecordStore, "delete_generation_chain", widened)
    conn = _Recording()
    rs.RecordStore(conn).delete_generation_chain(chart_id=CHART_ID, generation="5.0")
    assert _deletes_of(conn) != [t for t, _ in teardown_mod.CHAIN_TABLES]


# ── round 2, items 4 to 6 (ASTRA v1.1): the N-137 end state, effects outside the chart, honest failure reporting ────────────────

@pytest.mark.parametrize("kw, match", [
    (dict(catalog_status="RETIRED"), "catalog_status is RETIRED"),
    (dict(dependents=[{"asset_id": "ka_some_dependent"}]), "ka_some_dependent"),
    (dict(evidence=[{"kind": "receipt", "chart_id": "other-chart", "n": 2}]), r"receipts of the asset from a non-test run.*other-chart"),
    (dict(evidence=[{"kind": "run_asset", "chart_id": "other-chart", "n": 1}]), r"build_run_assets rows of the asset from a non-test run.*other-chart"),
], ids=["retired", "dependent", "non_test_receipt_elsewhere", "non_test_run_asset_elsewhere"])
def test_the_n137_end_state_is_validated_before_anything_is_deleted(kw, match):
    """Codex round 2 P2 (definitions.ts N-137): catalog_status, dependents, and non-test evidence on ANY chart."""
    h = _Harness(**kw)
    with pytest.raises(teardown_mod.TeardownRefused, match=match):
        _run(h)
    assert h.deletes() == [] and h.commits == 0


def test_the_n137_end_state_is_validated_again_before_success_is_claimed():
    """Evidence that appears only AFTER the deletes (the second evaluation) refuses and rolls back; success is not claimed."""
    h = _Harness(evidence_after=[{"kind": "receipt", "chart_id": "x", "n": 1}])
    with pytest.raises(teardown_mod.TeardownRefused, match="after the deletes, so success is not claimed"):
        _run(h)
    assert h.commits == 0 and h.rollbacks >= 1 and len(h.deletes()) > 0          # the deletes ran, and were rolled back


def test_the_end_state_query_is_the_monitors_predicate_over_every_chart():
    h = _Harness()
    _run(h)
    receipts = next(x for x in h.statements if "FROM asset_provenance_receipts r WHERE r.asset_id" in x)
    run_assets = next(x for x in h.statements if "FROM build_run_assets a LEFT JOIN build_runs b0" in x)
    for sql in (receipts, run_assets):
        assert "chart_id = %s" not in sql.replace("GROUP BY", "")                          # asset-wide: not pinned to the chart
        assert "NOT EXISTS (SELECT 1 FROM build_runs b WHERE b.id = " in sql and "b.triggered_by = %s" in sql


def test_an_owned_run_with_receipts_of_the_asset_on_another_chart_is_refused():
    """Codex round 2 P2: deleting the run would set those receipts' run link to NULL."""
    h = _Harness(elsewhere=[{"chart_id": "other-chart", "n": 3}])
    with pytest.raises(teardown_mod.TeardownRefused, match="other-chart"):
        _run(h)
    assert h.deletes() == []


def test_an_active_registry_row_with_freshness_on_another_chart_is_refused_because_596_would_stale_it():
    h = _Harness(registry_active=True, freshness_elsewhere=2)
    with pytest.raises(teardown_mod.TeardownRefused, match=r"ACTIVE.*596.*EVERY chart"):
        _run(h)
    assert h.deletes() == []
    h = _Harness(registry_active=False, freshness_elsewhere=2)                  # already inert: the flip changes nothing, no trigger
    _run(h)
    assert h.commits == 1


def test_a_null_linked_receipt_refusal_names_the_retention_window_and_the_runbook():
    h = _Harness(members=[], receipts=[{"partition_key": "orphan-part", "build_id": None}])
    with pytest.raises(teardown_mod.TeardownRefused, match="90 days") as exc:
        _run(h)
    assert "V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md" in str(exc.value)


def test_the_retention_window_is_the_watchdogs_and_the_docstring_says_to_run_within_it():
    assert teardown_mod.RETENTION_DAYS == 90
    watchdog = (REPO / "platform/src/app/api/cockpit/watchdog/route.ts").read_text(encoding="utf-8")
    assert "INTERVAL '90 days'" in watchdog and "build_runs" in watchdog           # the constant is the cockpit's own
    doc = teardown_mod.__doc__
    assert "WITHIN 90 DAYS" in doc and "V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md" in doc
    assert (REPO / "00_ARCHITECTURE/briefs/pravaha/V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md").exists()


def test_a_failure_before_the_commit_reports_a_confirmed_rollback(capsys):
    h = _Harness(fail_on="DELETE FROM build_runs")
    with _patched(h):
        assert teardown_mod.main(["--execute", "--i-am-steward"]) == 1
    err = capsys.readouterr().err
    assert "ROLLBACK CONFIRMED" in err and "COMMIT OUTCOME UNKNOWN" not in err and h.commits == 0


def test_a_failure_AT_the_commit_is_reported_as_an_unknown_outcome_never_as_nothing_committed(capsys):
    """Codex round 2 P2: once COMMIT has been sent, nobody may print 'nothing was committed'."""
    h = _Harness(commit_error=ConnectionError("server closed the connection unexpectedly (postgresql://svc:hunter2-secret@db/prod)"))
    with _patched(h):
        assert teardown_mod.main(["--execute", "--i-am-steward"]) == 1
    streams = capsys.readouterr()
    text = streams.err + streams.out
    assert "COMMIT OUTCOME UNKNOWN" in text and "may or may not have committed" in text
    assert "ROLLBACK CONFIRMED" not in text and "changed nothing" not in text and "Nothing was committed" not in text
    assert "hunter2" not in text
    assert h.commits == 1 and h.rollbacks == 0                                    # no rollback was attempted after the COMMIT went out


def test_a_failed_rollback_is_reported_as_not_confirmed(capsys):
    h = _Harness(fail_on="DELETE FROM build_runs", rollback_error=ConnectionError("lost"))
    with _patched(h):
        assert teardown_mod.main(["--execute", "--i-am-steward"]) == 1
    err = capsys.readouterr().err
    assert "ROLLBACK NOT CONFIRMED" in err and "ROLLBACK CONFIRMED:" not in err


def test_a_named_refusal_reports_its_confirmed_rollback(capsys):
    h = _Harness(members=[_test_run(), {"id": "layer-9", "triggered_by": "cockpit", "scope": "layer", "scope_target": "kala", "assets": [ASSET]}])
    with _patched(h):
        assert teardown_mod.main([]) == 1
    err = capsys.readouterr().err
    assert "layer-9" in err and "ROLLBACK CONFIRMED" in err


def test_no_message_in_the_script_can_say_nothing_was_committed_without_a_confirmed_rollback():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "Nothing was committed" not in source and "nothing was committed" not in source
