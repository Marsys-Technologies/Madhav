"""C38 — the small-test TEARDOWN executed for real against the chain tables (round 2, ASTRA's review of PR 3098).

The unit tests in platform/scripts/__tests__/test_teardown_v5_small_test.py use a recording fake, so they cannot show that the
script's SQL is valid, that its deletes respect the real foreign keys, or that its locks synchronise with a competing session.
Here the script's own `teardown()` runs over a database holding a REAL build chain (the writer's substeps on the real migration
chain, cloned from PR 3132's template harness) plus the orchestrator tables the script touches (asset_registry, build_runs,
build_run_assets, asset_throughput, asset_provenance_receipts, asset_freshness), created with the foreign keys production has —
notably migration 596's `asset_provenance_receipts.build_id REFERENCES build_runs(id) ON DELETE SET NULL`.

Shown on a real database: the whole small test is removed and everything else kept; an unstamped candidate, a NULL-linked receipt,
a non-test layer run, a mixed-asset test run, an active run, legacy ledger rows each REFUSE and leave every table as it was; a held
orchestrator lock refuses, a held chart lock fails closed on the lock timeout, and a non-test receipt committed by a competing
session while the teardown waits for the chart lock is SEEN by the checks (they run inside the lock); a failure after a partial
delete rolls everything back; the registry row is restored from an active state; a second execution is a clean no-op.

DEPENDS ON PR 3132 (A5.5f): it imports that PR's `_World` / `template` harness.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path

import psycopg
import pytest

from .test_a55_replace_chain import CHART_ID, CLASSES, GEN, SHORT, _World, template  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "platform" / "scripts"))
import teardown_v5_small_test_job as td  # noqa: E402

ASSET = td.ASSET_ID
OTHER_GEN = "5.9"
STAMP = {"stored_scope": "test_slice",
         "test_slice": {"run": "one_class_full", "classes": [CLASSES[0]],
                        "horizon": ["2025-01-01T00:00:00+00:00", "2025-01-20T00:00:00+00:00"]}}
STUB_DDL = (
    "CREATE TABLE IF NOT EXISTS public.kala_gochara_authority (chart_id uuid PRIMARY KEY, authoritative_generation text)",
    "CREATE TABLE public.asset_registry (asset_id text PRIMARY KEY, scope text, is_active boolean, has_writer boolean,"
    " has_substeps boolean, writer_timeout_seconds integer, depends_on text[], target_table text, count_sql text,"
    " target_floor integer, estimated_seconds integer)",
    "CREATE TABLE public.build_runs (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid, scope text,"
    " scope_target text, state text, triggered_by text)",
    "CREATE TABLE public.build_run_assets (run_id uuid NOT NULL REFERENCES public.build_runs(id), asset_id text)",
    "CREATE TABLE public.asset_throughput (chart_id uuid, asset_id text)",
    # migration 596: the run link is SET NULL when the run row is deleted
    "CREATE TABLE public.asset_provenance_receipts (asset_id text NOT NULL REFERENCES public.asset_registry(asset_id)"
    " ON DELETE CASCADE, chart_id uuid, partition_key text NOT NULL DEFAULT 'p',"
    " build_id uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)",
    "CREATE TABLE public.asset_freshness (asset_id text NOT NULL REFERENCES public.asset_registry(asset_id) ON DELETE CASCADE,"
    " chart_id uuid, partition_key text NOT NULL DEFAULT 'p', freshness_state text NOT NULL DEFAULT 'fresh')",
)


@pytest.fixture()
def tworld(template):
    w = _World(template)
    try:
        for ddl in STUB_DDL:
            w.conn.execute(ddl)
        e = td.EXPECTED_REGISTRY_ROW
        w.conn.execute(
            "INSERT INTO public.asset_registry VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (ASSET, e["scope"], False, e["has_writer"], e["has_substeps"], e["writer_timeout_seconds"], e["depends_on"],
             e["target_table"], e["count_sql"], e["target_floor"], e["estimated_seconds"]))
        w.conn.execute("INSERT INTO public.asset_registry VALUES ('other_asset','per_chart',true,true,false,600,'{}',NULL,NULL,0,NULL)")
        yield w
    finally:
        w.close()


def _stamp(w):
    """The C46 stamp: the manifest identifies itself as a test slice (scope word AND component naming run/classes/horizon)."""
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = input_generation_vector || %s::jsonb"
                       " WHERE generation = %s", (json.dumps(STAMP), GEN))


def _run(w, triggered_by=td.TRIGGERED_BY, scope="asset", target=ASSET, assets=(ASSET,), state="completed", receipt=True,
         part="p1"):
    """A build run with its child asset rows, optionally this asset's receipt/freshness/throughput linked to it."""
    rid = uuid.uuid4()
    w.conn.execute("INSERT INTO public.build_runs (id, chart_id, scope, scope_target, state, triggered_by)"
                   " VALUES (%s, %s, %s, %s, %s, %s)", (rid, CHART_ID, scope, target, state, triggered_by))
    for a in assets:
        w.conn.execute("INSERT INTO public.build_run_assets VALUES (%s, %s)", (rid, a))
    if receipt:
        w.conn.execute("INSERT INTO public.asset_throughput VALUES (%s, %s)", (CHART_ID, ASSET))
        w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, build_id)"
                       " VALUES (%s, %s, %s, %s)", (ASSET, CHART_ID, part, rid))
        w.conn.execute("INSERT INTO public.asset_freshness (asset_id, chart_id, partition_key) VALUES (%s, %s, %s)",
                       (ASSET, CHART_ID, part))
    return rid


def _prune(w, rid):
    """The cockpit watchdog's prune: receipt link -> NULL (migration 596)."""
    w.conn.execute("DELETE FROM public.build_run_assets WHERE run_id = %s", (rid,))
    w.conn.execute("DELETE FROM public.build_runs WHERE id = %s", (rid,))


def _survivors(w):
    """A Moon partition of this generation, a whole other generation, another asset's receipt / freshness / throughput."""
    from services.gochara_kernel import record_store as rs
    store = rs.RecordStore(w.conn)
    kala = store.ensure_kala_convention()
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        store.write_moon_coverage(
            chart_id=CHART_ID, generation=GEN, partition_key="moon-q1", convention_id=kala, horizon=SHORT,
            resolution=3600.0, relations_searched=["residence"], targets_requested=1, targets_resolved=1,
            state_counts={"searched_complete": 1}, unavailable_inputs={}, unsearched_reason=None, build_id="moon-q1")
        for table, extra in (("ka_gochara_contact", ""), ("kala_gochara_coverage", " AND partition_kind = 'event_class'")):
            w.conn.execute(f"CREATE TEMP TABLE _s AS SELECT * FROM public.{table} WHERE generation = %s{extra} LIMIT 1", (GEN,))
            w.conn.execute("UPDATE _s SET generation = %s", (OTHER_GEN,))
            w.conn.execute(f"INSERT INTO public.{table} SELECT * FROM _s")
            w.conn.execute("DROP TABLE _s")
    w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id) VALUES ('other_asset', %s)", (CHART_ID,))
    w.conn.execute("INSERT INTO public.asset_freshness (asset_id, chart_id) VALUES ('other_asset', %s)", (CHART_ID,))
    w.conn.execute("INSERT INTO public.asset_throughput VALUES (%s, 'other_asset')", (CHART_ID,))


def _present(w, table):
    return w.conn.execute("SELECT to_regclass(%s)", (f"public.{table}",)).fetchone()[0] is not None


def _counts(w):
    out = {}
    for table, extra in td.GENERATION_TABLES:
        out[table] = w.conn.execute(f"SELECT count(*) FROM public.{table} WHERE chart_id = %s AND generation = %s{extra}",
                                    (CHART_ID, GEN)).fetchone()[0]
    return out


def _bookkeeping(w):
    c = w.conn
    return {"runs": c.execute("SELECT count(*) FROM public.build_runs").fetchone()[0],
            "run_assets": c.execute("SELECT count(*) FROM public.build_run_assets").fetchone()[0],
            "receipts": c.execute("SELECT asset_id, count(*) FROM public.asset_provenance_receipts GROUP BY 1 ORDER BY 1").fetchall(),
            "freshness": c.execute("SELECT asset_id, count(*) FROM public.asset_freshness GROUP BY 1 ORDER BY 1").fetchall(),
            "throughput": c.execute("SELECT asset_id, count(*) FROM public.asset_throughput GROUP BY 1 ORDER BY 1").fetchall(),
            "registry": c.execute("SELECT asset_id, is_active FROM public.asset_registry ORDER BY 1").fetchall()}


def _snapshot(w):
    return (_counts(w), _bookkeeping(w))


def _teardown(w, dry_run=False):
    prior = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = w.dsn
    try:
        td.teardown(dry_run=dry_run)
    finally:
        if prior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior


def _built_stamped_with_test_run(w):
    w.build(SHORT)
    _stamp(w)
    _run(w)
    _survivors(w)
    assert _counts(w)["ka_gochara_contact"] >= 5 and _counts(w)["ka_gochara_relationship_record"] >= 1
    assert _counts(w)["ka_gochara_search_inventory"] >= 1 and _counts(w)["kala_gochara_publication"] == 1


def _refused_and_untouched(w, match, **kw):
    before = _snapshot(w)
    with pytest.raises(td.TeardownRefused, match=match):
        _teardown(w, **kw)
    assert _snapshot(w) == before, "a refusal changed the database"


# ── the whole small test, and nothing else ─────────────────────────────────────────────────────────────────────────────────────

def test_the_teardown_removes_the_whole_small_test_and_keeps_everything_else(tworld, capsys):
    w = tworld
    _built_stamped_with_test_run(w)
    sky_before = w.conn.execute("SELECT count(*) FROM public.ka_gochara_sky_event").fetchone()[0]
    assert sky_before > 0
    before = _snapshot(w)

    _teardown(w, dry_run=True)                                       # lists, changes nothing
    listed = capsys.readouterr().out
    assert "asset_provenance_receipts\t1" in listed and "asset_freshness\t1" in listed and "ka_gochara_contact\t" in listed
    assert _snapshot(w) == before

    _teardown(w)
    after = _counts(w)
    assert all(n == 0 for n in after.values()), {t: n for t, n in after.items() if n}
    c = w.conn
    assert c.execute("SELECT count(*) FROM public.asset_provenance_receipts WHERE asset_id = %s", (ASSET,)).fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM public.asset_freshness WHERE asset_id = %s", (ASSET,)).fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM public.build_runs WHERE triggered_by = %s", (td.TRIGGERED_BY,)).fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM public.build_run_assets").fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM public.asset_throughput WHERE asset_id = %s", (ASSET,)).fetchone()[0] == 0
    # what stays
    assert c.execute("SELECT count(*) FROM public.asset_provenance_receipts WHERE asset_id = 'other_asset'").fetchone()[0] == 1
    assert c.execute("SELECT count(*) FROM public.asset_freshness WHERE asset_id = 'other_asset'").fetchone()[0] == 1
    assert c.execute("SELECT count(*) FROM public.asset_throughput WHERE asset_id = 'other_asset'").fetchone()[0] == 1
    assert c.execute("SELECT count(*) FROM public.kala_gochara_coverage WHERE generation = %s AND partition_kind = 'moon_on_demand'",
                     (GEN,)).fetchone()[0] == 1
    assert c.execute("SELECT count(*) FROM public.ka_gochara_contact WHERE generation = %s", (OTHER_GEN,)).fetchone()[0] == 1
    assert c.execute("SELECT count(*) FROM public.ka_gochara_sky_event").fetchone()[0] == sky_before
    row = c.execute("SELECT is_active, has_substeps, writer_timeout_seconds, depends_on FROM public.asset_registry"
                    " WHERE asset_id = %s", (ASSET,)).fetchone()
    assert row == (False, True, 7200, ["ga_positions", "ga_dashas"])


def test_a_second_execution_is_a_clean_noop(tworld):
    w = tworld
    _built_stamped_with_test_run(w)
    _teardown(w)
    after_first = _snapshot(w)
    _teardown(w)                                                     # nothing left: every delete matches nothing
    assert _snapshot(w) == after_first


def test_an_active_registry_row_is_restored_inert(tworld):
    """ASTRA: the earlier unit case did not apply the UPDATE; here the real row is flipped back."""
    w = tworld
    _built_stamped_with_test_run(w)
    w.conn.execute("UPDATE public.asset_registry SET is_active = true WHERE asset_id = %s", (ASSET,))
    _teardown(w)
    assert w.conn.execute("SELECT is_active FROM public.asset_registry WHERE asset_id = %s", (ASSET,)).fetchone()[0] is False


def test_a_failure_after_a_partial_delete_rolls_everything_back(tworld, monkeypatch):
    w = tworld
    _built_stamped_with_test_run(w)
    before = _snapshot(w)
    real = td._delete_everything

    def partial_then_boom(cur, owned):
        real(cur, owned)                                             # every delete ran inside the transaction …
        raise RuntimeError("injected failure after the deletes")     # … and then the teardown fails
    monkeypatch.setattr(td, "_delete_everything", partial_then_boom)
    with pytest.raises(RuntimeError, match="injected failure"):
        _teardown(w)
    assert _snapshot(w) == before


# ── ownership ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_historical_test_run_never_authorises_deleting_an_unstamped_candidate(tworld):
    """ASTRA P1-3: a test run exists, the current candidate is a full unstamped build — refuse (the old suite enshrined acceptance)."""
    w = tworld
    w.build(SHORT)
    _run(w)
    _refused_and_untouched(w, "not PROVEN to be a test slice")


def test_a_null_linked_receipt_is_refused_and_named_even_with_a_stamped_manifest(tworld):
    w = tworld
    w.build(SHORT)
    _stamp(w)
    rid = _run(w, part="orphan-part")
    _prune(w, rid)                                                   # the watchdog's prune: link -> NULL
    assert w.conn.execute("SELECT count(*), count(build_id) FROM public.asset_provenance_receipts WHERE asset_id = %s",
                          (ASSET,)).fetchone() == (1, 0)
    _refused_and_untouched(w, "NO run link.*orphan-part")


def test_a_pruned_test_run_with_a_stamped_manifest_and_no_receipts_is_removable(tworld):
    w = tworld
    w.build(SHORT)
    _stamp(w)
    rid = _run(w, receipt=False)
    _prune(w, rid)
    _teardown(w)
    assert all(n == 0 for n in _counts(w).values())


def test_deleting_the_run_orphans_the_receipt_which_is_why_receipts_are_deleted_by_asset_and_chart(tworld):
    """The real foreign key, shown: delete the run row and the receipt survives with a NULL run link."""
    w = tworld
    rid = _run(w)
    _prune(w, rid)
    assert w.conn.execute("SELECT count(*), count(build_id) FROM public.asset_provenance_receipts WHERE asset_id = %s",
                          (ASSET,)).fetchone() == (1, 0)


def test_legacy_ledger_rows_of_5_0_are_refused_and_named_never_deleted(tworld):
    """ASTRA P1-5: the v5 writer writes neither legacy table; a '5.0' row there is not this test's. The row survives the refusal."""
    w = tworld
    assert not _present(w, "kala_gochara_windows")
    w.conn.execute("CREATE TABLE public.kala_gochara_windows (chart_id uuid, generation text)")
    w.conn.execute("INSERT INTO public.kala_gochara_windows VALUES (%s, '5.0'), (%s, %s)", (CHART_ID, CHART_ID, OTHER_GEN))
    w.build(SHORT)
    _stamp(w)
    _run(w)
    _refused_and_untouched(w, "kala_gochara_windows")
    assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_windows").fetchone()[0] == 2


def test_a_legacy_table_holding_only_other_generations_does_not_block(tworld):
    w = tworld
    w.conn.execute("CREATE TABLE public.kala_gochara_windows (chart_id uuid, generation text)")
    w.conn.execute("INSERT INTO public.kala_gochara_windows VALUES (%s, %s)", (CHART_ID, OTHER_GEN))
    w.build(SHORT)
    _stamp(w)
    _run(w)
    _teardown(w)
    assert w.conn.execute("SELECT generation FROM public.kala_gochara_windows").fetchall() == [(OTHER_GEN,)]
    assert all(n == 0 for n in _counts(w).values())


# ── run membership ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_non_test_layer_run_that_includes_the_asset_is_refused(tworld):
    """ASTRA P1-2: a layer build has scope_target 'kala' (not the asset id); membership is read from build_run_assets."""
    w = tworld
    w.build(SHORT)
    _stamp(w)
    _run(w)
    _run(w, triggered_by="cockpit-manual-build", scope="layer", target="kala", assets=(ASSET, "other_asset"), receipt=False, part="p2")
    _refused_and_untouched(w, "NON-test build run")


def test_a_non_test_comma_separated_asset_set_is_refused(tworld):
    w = tworld
    w.build(SHORT)
    _stamp(w)
    _run(w)
    _run(w, triggered_by="cockpit-manual-build", scope="asset_set", target=f"other_asset,{ASSET}", assets=(), receipt=False)
    _refused_and_untouched(w, "NON-test build run")


def test_a_test_run_that_also_holds_another_asset_is_refused_and_the_other_assets_rows_are_untouched(tworld):
    """ASTRA P1-4: deleting such a run would delete 'other_asset''s bookkeeping and orphan its receipt."""
    w = tworld
    w.build(SHORT)
    _stamp(w)
    rid = _run(w, assets=(ASSET, "other_asset"))
    w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, build_id) VALUES ('other_asset', %s, 'q', %s)",
                   (CHART_ID, rid))
    _refused_and_untouched(w, "not exclusively")


def test_any_active_run_on_the_chart_is_refused_whatever_its_shape(tworld):
    w = tworld
    w.build(SHORT)
    _stamp(w)
    _run(w)
    _run(w, triggered_by="cockpit-manual-build", scope="layer", target="phala", assets=("other_asset",), state="running", receipt=False)
    _refused_and_untouched(w, "active build_runs")


# ── synchronisation ────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_held_orchestrator_lock_refuses_and_changes_nothing(tworld):
    w = tworld
    _built_stamped_with_test_run(w)
    holder = psycopg.connect(w.dsn, autocommit=True, connect_timeout=3)
    try:
        holder.execute("SELECT pg_advisory_lock(hashtext(%s))", (CHART_ID,))             # what a build run holds
        _refused_and_untouched(w, "exclusion lock")
    finally:
        holder.close()
    _teardown(w)                                                                          # released: it proceeds
    assert all(n == 0 for n in _counts(w).values())


def test_a_held_chart_lock_fails_the_teardown_closed_on_the_lock_timeout(tworld, monkeypatch):
    w = tworld
    _built_stamped_with_test_run(w)
    before = _snapshot(w)
    monkeypatch.setattr(td, "LOCK_TIMEOUT", "300ms")
    holder = psycopg.connect(w.dsn, autocommit=False, connect_timeout=3)
    try:
        holder.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))     # a writer inside its transaction
        with pytest.raises(psycopg.errors.LockNotAvailable):
            _teardown(w)
    finally:
        holder.rollback()
        holder.close()
    assert _snapshot(w) == before
    _teardown(w)
    assert all(n == 0 for n in _counts(w).values())


def test_a_non_test_run_committed_while_the_teardown_waits_for_the_chart_lock_is_seen_by_the_checks(tworld):
    """ASTRA P1-1, the race itself: the checks run INSIDE the locks. A competing session holds the chart lock, starts a real build of
    the asset (run row + receipt) and commits only after the teardown is already waiting; the teardown then sees that run and
    refuses. With the checks before the lock (the old code) it would have judged the earlier, clean state and deleted the receipt."""
    w = tworld
    _built_stamped_with_test_run(w)
    outcome: list = []

    def run_teardown():
        try:
            _teardown(w)
            outcome.append("deleted")
        except BaseException as exc:                                  # noqa: BLE001
            outcome.append(exc)

    rival = psycopg.connect(w.dsn, autocommit=False, connect_timeout=3)
    thread = threading.Thread(target=run_teardown)
    try:
        rival.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        thread.start()
        deadline = time.time() + 20
        while time.time() < deadline:                                 # wait until the teardown is queued on the chart lock
            blocked = w.conn.execute("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted").fetchone()[0]
            if blocked:
                break
            time.sleep(0.05)
        else:
            pytest.fail("the teardown never queued on the chart lock")
        rid = uuid.uuid4()
        rival.execute("INSERT INTO public.build_runs (id, chart_id, scope, scope_target, state, triggered_by)"
                      " VALUES (%s, %s, 'asset', %s, 'completed', 'cockpit-manual-build')", (rid, CHART_ID, ASSET))
        rival.execute("INSERT INTO public.build_run_assets VALUES (%s, %s)", (rid, ASSET))
        rival.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, build_id) VALUES (%s, %s, 'real', %s)",
                      (ASSET, CHART_ID, rid))
        rival.commit()                                                # the lock is released; the teardown proceeds
        thread.join(30)
    finally:
        rival.close()
    assert not thread.is_alive()
    assert len(outcome) == 1 and isinstance(outcome[0], td.TeardownRefused), outcome
    assert "NON-test build run" in str(outcome[0])
    assert w.conn.execute("SELECT count(*) FROM public.asset_provenance_receipts WHERE partition_key = 'real'").fetchone()[0] == 1
    assert _counts(w)["ka_gochara_contact"] >= 5


# ── the command line against a real database ─────────────────────────────────────────────────────────────────────────────────

def test_the_cli_defaults_to_a_dry_run_and_deletes_only_with_both_flags(tworld, monkeypatch, capsys):
    w = tworld
    _built_stamped_with_test_run(w)
    monkeypatch.setenv("DATABASE_URL", w.dsn)
    before = _snapshot(w)
    assert td.main([]) == 0 and _snapshot(w) == before                                    # default: dry run
    with pytest.raises(SystemExit):
        td.main(["--execute"])                                                            # intent without the steward flag
    assert _snapshot(w) == before
    assert td.main(["--execute", "--i-am-steward"]) == 0
    assert all(n == 0 for n in _counts(w).values())


def test_a_malformed_database_url_prints_the_class_and_never_the_credential(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://svc:hunter2-secret%ZZ@localhost:1/none")
    code = td.main([])
    streams = capsys.readouterr()
    assert code == 1 and "hunter2" not in streams.err + streams.out
