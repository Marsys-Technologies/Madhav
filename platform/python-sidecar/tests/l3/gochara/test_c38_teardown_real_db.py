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

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod

from .conftest import EPHE_PATH
from .test_a55_replace_chain import CHART_ID, CLASSES, GEN, PATHS, SHORT, _World, template  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "platform" / "scripts"))
import teardown_v5_small_test_job as td  # noqa: E402

ASSET = td.ASSET_ID
OTHER_GEN = "5.9"
OTHER_CHART = "11111111-2222-3333-4444-555555555555"
#: the marker a dispatch would stage: all 26 classes over a window inside the scored horizon (only the first classes are executed here)
MARKER = {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": "all_classes_1y",
          "horizon": [SHORT[0].isoformat(), SHORT[1].isoformat()], "classes": list(writer_mod.SCORED_CLASSES)}
STUB_DDL = (
    "CREATE TABLE IF NOT EXISTS public.kala_gochara_authority (chart_id uuid PRIMARY KEY, authoritative_generation text)",
    "CREATE TABLE public.asset_registry (asset_id text PRIMARY KEY, scope text, is_active boolean, has_writer boolean,"
    " has_substeps boolean, writer_timeout_seconds integer, depends_on text[], target_table text, count_sql text,"
    " target_floor integer, estimated_seconds integer, catalog_status text DEFAULT 'CURRENT', asset_kind text DEFAULT 'data',"
    " asset_type text DEFAULT 'data', health_probe text, integrity_check_sql text, rebuild_on_probe_fail boolean DEFAULT false)",
    "CREATE TABLE public.build_runs (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid, scope text,"
    " scope_target text, state text, triggered_by text, plan_manifest jsonb, plan_manifest_digest text,"
    " created_at timestamptz NOT NULL DEFAULT now())",
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


def _run(w, triggered_by=td.TRIGGERED_BY, scope="asset", target=ASSET, assets=(ASSET,), state="completed", receipt=True,
         part="p1", marker=None, chart=CHART_ID):
    """A build run with its child asset rows, optionally this asset's receipt/freshness/throughput linked to it, and optionally the
    slice marker in build_runs.plan_manifest exactly as a dispatch stages it."""
    rid = uuid.uuid4()
    manifest = None if marker is None else {writer_mod.TEST_SLICE_KEY: marker}
    w.conn.execute("INSERT INTO public.build_runs (id, chart_id, scope, scope_target, state, triggered_by, plan_manifest,"
                   " plan_manifest_digest) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)",
                   (rid, chart, scope, target, state, triggered_by, None if manifest is None else json.dumps(manifest),
                    None if manifest is None else writer_mod._manifest_digest(manifest)))
    for a in assets:
        w.conn.execute("INSERT INTO public.build_run_assets VALUES (%s, %s)", (rid, a))
    if receipt:
        w.conn.execute("INSERT INTO public.asset_throughput VALUES (%s, %s)", (chart, ASSET))
        w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, build_id)"
                       " VALUES (%s, %s, %s, %s)", (ASSET, chart, part, rid))
        w.conn.execute("INSERT INTO public.asset_freshness (asset_id, chart_id, partition_key) VALUES (%s, %s, %s)",
                       (ASSET, chart, part))
    return rid


def _step(w, rid, key, horizon=None):
    config = {"chart_id": CHART_ID, "ephe_path": EPHE_PATH}
    if horizon is not None:
        config["horizon"] = horizon
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id=str(rid), db_conn=w.conn, dry_run=False, config=config)
    with w.conn.transaction():
        return w._w.run_substep(ctx, SubStep(key=key, label=key))


def _default_build(w, horizon=SHORT, classes=CLASSES, paths=PATHS):
    """An ordinary (NON-slice, non-test) candidate build by the writer's own substeps: no marker, the default stamp, its own snapshot.
    The build id is a fresh uuid with no build_runs row (the writer reads a missing row as 'no marker')."""
    rid = uuid.uuid4()
    for key in (writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP):
        _step(w, rid, key, horizon)
    for cls in classes:
        _step(w, rid, f"inventory:{cls}", horizon)
        _step(w, rid, f"coverage:{cls}", horizon)
        for path in paths:
            _step(w, rid, f"record:{cls}:{path}", horizon)


def _slice_steps(w, rid, classes=CLASSES, paths=PATHS, head=True):
    """The WRITER's own substeps under the run `rid` (it reads the marker from build_runs.plan_manifest by build id): manifest,
    snapshot, then each class's inventory, coverage and record grains. The manifest and the snapshot it binds are the real ones."""
    def step(key):
        return _step(w, rid, key)
    if head:
        step(writer_mod.MANIFEST_SUBSTEP)
        step(writer_mod.SNAPSHOT_SUBSTEP)
    for cls in classes:
        step(f"inventory:{cls}")
        step(f"coverage:{cls}")
        for path in paths:
            step(f"record:{cls}:{path}")


def _slice_run(w, *, build=True, **kw):
    """A small-test run staged as a dispatch stages it, then built by the writer under it: a REAL stamped candidate whose snapshot and
    inventory carry the manifest's own vector."""
    rid = _run(w, marker=MARKER, **kw)
    if build:
        _slice_steps(w, rid)
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
    _slice_run(w)
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
    _default_build(w)
    _run(w)
    _refused_and_untouched(w, "not PROVEN to be a test slice")


def test_a_null_linked_receipt_is_refused_and_named_even_with_a_stamped_manifest(tworld):
    w = tworld
    rid = _slice_run(w, part="orphan-part")
    _prune(w, rid)                                                   # the watchdog's prune: link -> NULL
    assert w.conn.execute("SELECT count(*), count(build_id) FROM public.asset_provenance_receipts WHERE asset_id = %s",
                          (ASSET,)).fetchone() == (1, 0)
    _refused_and_untouched(w, "NO run link.*orphan-part")


def test_a_pruned_test_run_with_a_stamped_manifest_and_no_receipts_is_removable(tworld):
    w = tworld
    rid = _slice_run(w, receipt=False)
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
    _slice_run(w)
    _refused_and_untouched(w, "kala_gochara_windows")
    assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_windows").fetchone()[0] == 2


def test_a_legacy_table_holding_only_other_generations_does_not_block(tworld):
    w = tworld
    w.conn.execute("CREATE TABLE public.kala_gochara_windows (chart_id uuid, generation text)")
    w.conn.execute("INSERT INTO public.kala_gochara_windows VALUES (%s, %s)", (CHART_ID, OTHER_GEN))
    _slice_run(w)
    _teardown(w)
    assert w.conn.execute("SELECT generation FROM public.kala_gochara_windows").fetchall() == [(OTHER_GEN,)]
    assert all(n == 0 for n in _counts(w).values())


# ── run membership ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_non_test_layer_run_that_includes_the_asset_is_refused(tworld):
    """ASTRA P1-2: a layer build has scope_target 'kala' (not the asset id); membership is read from build_run_assets."""
    w = tworld
    _slice_run(w)
    _run(w, triggered_by="cockpit-manual-build", scope="layer", target="kala", assets=(ASSET, "other_asset"), receipt=False, part="p2")
    _refused_and_untouched(w, "NON-test build run")


def test_a_non_test_comma_separated_asset_set_is_refused(tworld):
    w = tworld
    _slice_run(w)
    _run(w, triggered_by="cockpit-manual-build", scope="asset_set", target=f"other_asset,{ASSET}", assets=(), receipt=False)
    _refused_and_untouched(w, "NON-test build run")


def test_a_test_run_that_also_holds_another_asset_is_refused_and_the_other_assets_rows_are_untouched(tworld):
    """ASTRA P1-4: deleting such a run would delete 'other_asset''s bookkeeping and orphan its receipt."""
    w = tworld
    rid = _slice_run(w, assets=(ASSET, "other_asset"))
    w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, build_id) VALUES ('other_asset', %s, 'q', %s)",
                   (CHART_ID, rid))
    _refused_and_untouched(w, "not exclusively")


def test_any_active_run_on_the_chart_is_refused_whatever_its_shape(tworld):
    w = tworld
    _slice_run(w)
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


# ── round 2 (ASTRA v1.1): proven ownership of the existing output, the end state, effects outside the chart, the rehearsal ───────

def _restamp(w, **changes):
    """Rewrite the stamped manifest's component behind the guards (a corrupted or forged stamp)."""
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        for key, value in changes.items():
            w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector,"
                           " %s::text[], %s::jsonb) WHERE generation = %s", (["test_slice", key], json.dumps(value), GEN))


def test_an_interrupted_replacement_a_later_slice_stamped_over_an_older_nontest_chain_is_refused(tworld):
    """Codex round 2 P1, the scenario itself: a failed NON-test candidate leaves its output; a later small test commits its stamped
    manifest and dies before the snapshot substep replaces the old output. Test run + valid stamp: the old output must NOT be deleted."""
    w = tworld
    _default_build(w)                                                           # the older, non-test candidate (default vector, its own snapshot)
    rid = _run(w, marker=MARKER)                                             # the later small test ...
    _step(w, rid, writer_mod.MANIFEST_SUBSTEP)                               # ... committed its stamped manifest, then failed
    assert w.conn.execute("SELECT input_generation_vector->>'stored_scope' FROM public.kala_gochara_publication WHERE generation = %s",
                          (GEN,)).fetchone()[0] == "test_slice"
    assert _counts(w)["ka_gochara_contact"] >= 5                             # the older output is still there
    _refused_and_untouched(w, "interrupted replacement")


@pytest.mark.parametrize("changes", [
    {"classes": [""]},
    {"horizon": ["bogus", "backwards"]},
    {"marker_digest": "0" * 64},
    {"schema": "gochara_v5_test_slice/9"},
    {"run": "one_class_full"},
], ids=["empty_class", "bogus_horizon", "wrong_digest", "wrong_schema", "run_shape_contradicts_classes"])
def test_a_forged_or_corrupted_stamp_is_refused_by_the_writers_own_validation(tworld, changes):
    """Codex drove classes=[''] and horizon=['bogus','backwards'] through to all 15 DELETEs; the writer's validator and the digest now stand in the way."""
    w = tworld
    _slice_run(w)
    _restamp(w, **changes)
    # Codex round 4 T4: the test run row SURVIVES here, so its ORIGINAL marker must prove the stamp and a forged stamp cannot; that
    # rule fires first. (The writer-validation refusals for a stamp with NO surviving run are the unit tests in test_teardown_v5_small_test.)
    _refused_and_untouched(w, "an owned run row survives, so its ORIGINAL marker preimage must prove the stamp")


def test_a_valid_stamp_whose_inventory_header_has_another_identity_is_refused(tworld):
    w = tworld
    _slice_run(w)
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("UPDATE public.ka_gochara_search_inventory SET horizon = tstzrange('2025-01-01', '2025-01-05') WHERE generation = %s", (GEN,))
    _refused_and_untouched(w, "inventory header")


def test_a_non_test_receipt_of_the_asset_on_another_chart_breaks_the_n137_end_state(tworld):
    """The monitor's evidence query is asset-wide: any chart, any non-test (or unlinked) receipt keeps the asset out of the excluded set."""
    w = tworld
    _built_stamped_with_test_run(w)
    w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, build_id) VALUES (%s, %s, 'x', NULL)",
                   (ASSET, OTHER_CHART))
    _refused_and_untouched(w, f"N-137 end state.*{OTHER_CHART}")


def test_a_non_test_run_asset_row_of_the_asset_on_another_chart_breaks_the_n137_end_state(tworld):
    w = tworld
    _built_stamped_with_test_run(w)
    _run(w, triggered_by="cockpit-manual-build", receipt=False, chart=OTHER_CHART)
    _refused_and_untouched(w, f"N-137 end state.*{OTHER_CHART}")


@pytest.mark.parametrize("break_it, match", [
    ("UPDATE public.asset_registry SET catalog_status = 'RETIRED' WHERE asset_id = 'ka_gochara_v5'", "catalog_status is RETIRED"),
    ("UPDATE public.asset_registry SET depends_on = '{ka_gochara_v5}' WHERE asset_id = 'other_asset'", "depends_on"),
], ids=["retired", "a_dependent"])
def test_the_registry_side_of_the_n137_end_state_is_validated(tworld, break_it, match):
    w = tworld
    _built_stamped_with_test_run(w)
    w.conn.execute(break_it)
    _refused_and_untouched(w, match)


def test_an_owned_run_that_also_holds_a_receipt_of_the_asset_on_another_chart_is_refused(tworld):
    """Deleting the run would set that receipt's run link to NULL (migration 596)."""
    w = tworld
    rid = _slice_run(w)
    w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, build_id) VALUES (%s, %s, 'y', %s)",
                   (ASSET, OTHER_CHART, rid))
    _refused_and_untouched(w, f"other chart.*{OTHER_CHART}")


def test_an_active_registry_row_with_freshness_on_another_chart_is_refused_but_alone_it_is_restored(tworld):
    w = tworld
    _built_stamped_with_test_run(w)
    w.conn.execute("UPDATE public.asset_registry SET is_active = true WHERE asset_id = %s", (ASSET,))
    w.conn.execute("INSERT INTO public.asset_freshness (asset_id, chart_id, partition_key) VALUES (%s, %s, 'z')", (ASSET, OTHER_CHART))
    _refused_and_untouched(w, r"ACTIVE.*596.*EVERY chart")
    w.conn.execute("DELETE FROM public.asset_freshness WHERE chart_id = %s", (OTHER_CHART,))
    _teardown(w)
    assert w.conn.execute("SELECT is_active FROM public.asset_registry WHERE asset_id = %s", (ASSET,)).fetchone()[0] is False


def test_the_dry_run_rehearses_the_deletes_and_so_fails_where_an_execution_would(tworld):
    """Codex round 2 P2: a dry run that returned before the DELETEs could not see a trigger or a constraint that refuses one. A trigger
    that blocks the throughput DELETE makes the DRY RUN fail, and nothing is left changed."""
    w = tworld
    _built_stamped_with_test_run(w)
    w.conn.execute("CREATE FUNCTION public.block_throughput_delete() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'blocked'; END $$")
    w.conn.execute("CREATE TRIGGER block_it BEFORE DELETE ON public.asset_throughput FOR EACH ROW EXECUTE FUNCTION public.block_throughput_delete()")
    before = _snapshot(w)
    with pytest.raises(psycopg.errors.Error):
        _teardown(w, dry_run=True)
    assert _snapshot(w) == before


def test_the_dry_run_prints_the_retention_remaining_for_the_owned_run(tworld, capsys):
    w = tworld
    _built_stamped_with_test_run(w)
    _teardown(w, dry_run=True)
    out = capsys.readouterr().out
    assert "day(s) of the 90-day cockpit retention remain" in out and "PAST RETENTION" not in out
    w.conn.execute("UPDATE public.build_runs SET created_at = now() - interval '91 days'")
    _teardown(w, dry_run=True)
    assert "PAST RETENTION" in capsys.readouterr().out


# ── Stream B additions (TEARDOWN-B-ADD): B3 a role holding EXACTLY the documented privileges, B4/B5 catalog references ────────────

ROLE = "td_exact_role"


def _grant_documented(w, *, registry_update=False, skip=()):
    """Grant EXACTLY td.REQUIRED_PRIVILEGES (and, with registry_update, the conditional ones) to ROLE. `skip` names a privilege to leave out
    as 'table:PRIV' or 'execute:fn' (the missing-grant tests)."""
    rp, c = td.REQUIRED_PRIVILEGES, w.conn
    for t in rp["select_delete"]:
        for priv in ("SELECT", "DELETE"):
            if f"{t}:{priv}" not in skip and _present(w, t):
                c.execute(f"GRANT {priv} ON public.{t} TO {ROLE}")
    for t in rp["select"]:
        if _present(w, t) and f"{t}:SELECT" not in skip:
            c.execute(f"GRANT SELECT ON public.{t} TO {ROLE}")
    for t in rp["update"]:
        if f"{t}:UPDATE" not in skip:
            c.execute(f"GRANT UPDATE ON public.{t} TO {ROLE}")
    for t in rp["select_referencing"]:
        if _present(w, t) and f"{t}:SELECT" not in skip:
            c.execute(f"GRANT SELECT ON public.{t} TO {ROLE}")
    for fn in rp["execute"]:
        if f"execute:{fn}" not in skip:
            c.execute(f"GRANT EXECUTE ON FUNCTION public.{fn} TO {ROLE}")
    if registry_update:
        c.execute(f"GRANT UPDATE (is_active) ON public.asset_registry TO {ROLE}")
        c.execute(f"GRANT SELECT, UPDATE ON public.asset_freshness TO {ROLE}")


@pytest.fixture()
def exact_role(tworld):
    w = tworld
    w.admin.execute(f"DROP ROLE IF EXISTS {ROLE}")
    w.admin.execute(f"CREATE ROLE {ROLE} LOGIN")
    # production revokes PUBLIC EXECUTE on the functions its owner creates (migration 1220 grants the builder the guard functions
    # explicitly for that reason); a freshly built test database leaves PUBLIC EXECUTE in place, which would MASK a missing EXECUTE
    w.conn.execute("REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC")
    # the tables production has referencing build_runs (names and columns from the production catalog, Stream B, 2026-10-05): the script
    # counts them, so the role needs SELECT on each; empty here, so none refuses
    for table, column in (("conversations", "archived_by_run_id"), ("event_chart_state_index", "chart_context_superseded_by_run_id"),
                          ("mimamsa_predictions", "chart_context_superseded_by_run_id"),
                          ("mimamsa_calibration_snapshot", "chart_context_superseded_by_run_id"),
                          ("brahma_prospective_ledger", "chart_context_superseded_by_run_id"),
                          ("brahma_mimamsa_prediction_ledger", "chart_context_superseded_by_run_id")):
        w.conn.execute(f"CREATE TABLE public.{table} (id serial PRIMARY KEY, {column} uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)")
    # migration 596's invoker-rights invalidation, VERBATIM function body; the trigger lists only the columns the stub registry has
    w.conn.execute("""CREATE OR REPLACE FUNCTION public.nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE asset_freshness
     SET freshness_state = 'stale',
         reasons = CASE WHEN reasons ? 'registry_changed' THEN reasons ELSE reasons || '["registry_changed"]'::jsonb END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END;
$$""")
    w.conn.execute("ALTER TABLE public.asset_freshness ADD COLUMN IF NOT EXISTS reasons jsonb NOT NULL DEFAULT '[]'::jsonb")
    w.conn.execute("ALTER TABLE public.asset_freshness ADD COLUMN IF NOT EXISTS observed_at timestamptz NOT NULL DEFAULT now()")
    w.conn.execute("""CREATE TRIGGER nirmana_registry_receipt_invalidation AFTER UPDATE OF depends_on, scope, has_writer, is_active, target_table,
       target_floor ON public.asset_registry FOR EACH ROW WHEN (OLD IS DISTINCT FROM NEW) EXECUTE FUNCTION public.nirmana_invalidate_registry_receipts()""")
    w.conn.execute("REVOKE EXECUTE ON FUNCTION public.nirmana_invalidate_registry_receipts() FROM PUBLIC")
    try:
        yield w
    finally:
        w.conn.execute(f"DROP OWNED BY {ROLE}")
        w.admin.execute(f"DROP ROLE IF EXISTS {ROLE}")


def _teardown_as(w, dry_run=False):
    from psycopg.conninfo import make_conninfo
    prior = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = make_conninfo(w.dsn, user=ROLE)
    try:
        td.teardown(dry_run=dry_run)
    finally:
        if prior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior


def test_b3_the_script_runs_as_a_role_holding_exactly_the_documented_privileges(exact_role, capsys):
    """The other tests connect as a superuser and prove LOGIC, not privileges. Here the dry run and then the execution run as a role that
    holds EXACTLY `REQUIRED_PRIVILEGES` (the registry row is inert, so no registry UPDATE is granted)."""
    w = exact_role
    _built_stamped_with_test_run(w)
    _grant_documented(w)
    before = _snapshot(w)
    _teardown_as(w, dry_run=True)                                       # the rehearsal succeeds with those privileges alone
    assert _snapshot(w) == before
    _teardown_as(w)
    assert all(n == 0 for n in _counts(w).values())
    assert w.conn.execute("SELECT count(*) FROM public.asset_provenance_receipts WHERE asset_id = %s", (ASSET,)).fetchone()[0] == 0


def test_b2_b3_an_active_registry_row_needs_the_conditional_privileges_and_without_them_the_dry_run_fails(exact_role):
    w = exact_role
    _built_stamped_with_test_run(w)
    w.conn.execute("UPDATE public.asset_registry SET is_active = true WHERE asset_id = %s", (ASSET,))
    _grant_documented(w)                                                # NOT the conditional UPDATE(is_active)
    before = _snapshot(w)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _teardown_as(w, dry_run=True)
    assert _snapshot(w) == before
    _grant_documented(w, registry_update=True)
    _teardown_as(w, dry_run=True)
    assert _snapshot(w) == before
    _teardown_as(w)
    assert w.conn.execute("SELECT is_active FROM public.asset_registry WHERE asset_id = %s", (ASSET,)).fetchone()[0] is False


@pytest.mark.parametrize("skip", ["asset_freshness:DELETE", "asset_provenance_receipts:DELETE", "build_runs:DELETE",
                                  "kala_gochara_publication:DELETE", "ka_gochara_contact:DELETE", "execute:ka_gochara_lock_chart(uuid)"],
                         ids=lambda s: s.replace(":", "_").replace("(uuid)", ""))
def test_b3_a_missing_grant_fails_the_dry_run_and_changes_nothing(exact_role, skip):
    """The rehearsal runs the real statements, so a missing privilege shows up in the DRY RUN, not at the steward's execution."""
    w = exact_role
    _built_stamped_with_test_run(w)
    _grant_documented(w, skip=(skip,))
    before = _snapshot(w)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _teardown_as(w, dry_run=True)
    assert _snapshot(w) == before


def test_b4_another_table_referencing_an_owned_run_is_found_from_the_catalog_and_named(tworld):
    """build_runs deletion sets ON DELETE SET NULL references to NULL (conversations, the ledgers, ...): found from pg_constraint, not a list."""
    w = tworld
    rid = _slice_run(w)
    w.conn.execute("CREATE TABLE public.conversations_like (id serial PRIMARY KEY, archived_by_run_id uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)")
    w.conn.execute("INSERT INTO public.conversations_like (archived_by_run_id) VALUES (%s)", (rid,))
    _refused_and_untouched(w, r"conversations_like\.archived_by_run_id \(1 row\(s\), ON DELETE SET NULL\)")


def test_b5_a_no_action_reference_to_the_manifest_is_named_not_a_bare_sqlstate(tworld):
    w = tworld
    _slice_run(w)
    w.conn.execute("CREATE TABLE public.contacts_like (id serial PRIMARY KEY, input_generation_vector_id uuid REFERENCES public.kala_gochara_publication(manifest_id))")
    w.conn.execute("INSERT INTO public.contacts_like (input_generation_vector_id) SELECT manifest_id FROM public.kala_gochara_publication WHERE generation = %s", (GEN,))
    _refused_and_untouched(w, r"contacts_like\.input_generation_vector_id \(1 row\(s\), ON DELETE NO ACTION\)")


def test_b6_the_pid_and_lock_checks_pass_on_a_direct_connection(tworld):
    """On a real direct connection the backend does not change across transactions and the session lock is held by it."""
    w = tworld
    _built_stamped_with_test_run(w)
    _teardown(w, dry_run=True)


# ── Codex round 3 (v1.2): items 1 and 2 on a real database ───────────────────────────────────────────────────────────────────────

#: the six foreign keys INTO build_runs that migrations 1120, 1122 and 1123 add (ON DELETE SET NULL), with their real table and column names
RUN_FKS = (("conversations", "archived_by_run_id"),
           ("event_chart_state_index", "chart_context_superseded_by_run_id"),
           ("mimamsa_predictions", "chart_context_superseded_by_run_id"),
           ("mimamsa_calibration_snapshot", "chart_context_superseded_by_run_id"),
           ("brahma_prospective_ledger", "chart_context_superseded_by_run_id"),
           ("brahma_mimamsa_prediction_ledger", "chart_context_superseded_by_run_id"))


@pytest.mark.parametrize("table, column", RUN_FKS, ids=[t for t, _ in RUN_FKS])
def test_item1_each_real_build_runs_foreign_key_is_found_from_the_catalog_and_refused_by_name(tworld, table, column):
    """Codex round 3 P2: the six real ON DELETE SET NULL references. The list comes from pg_constraint at run time, so a future one is covered."""
    w = tworld
    rid = _slice_run(w)
    w.conn.execute(f"CREATE TABLE public.{table} (id serial PRIMARY KEY, {column} uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)")
    w.conn.execute(f"INSERT INTO public.{table} ({column}) VALUES (%s)", (rid,))
    _refused_and_untouched(w, rf"{table}\.{column} \(1 row\(s\), ON DELETE SET NULL\)")


def test_item1_an_unreferenced_new_foreign_key_does_not_block(tworld):
    """A table with such a key but no row pointing at an owned run is not an obstacle (a hardcoded 'any FK blocks' would be wrong too)."""
    w = tworld
    _slice_run(w)
    w.conn.execute("CREATE TABLE public.some_future_table (id serial PRIMARY KEY, built_by uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)")
    w.conn.execute("INSERT INTO public.some_future_table (built_by) VALUES (NULL)")
    _teardown(w)
    assert all(n == 0 for n in _counts(w).values())


NON_CANONICAL = dict(MARKER, horizon=[SHORT[0].isoformat().replace("+00:00", "Z"), SHORT[1].isoformat().replace("+00:00", "Z")],
                     classes=list(reversed(MARKER["classes"])))


def test_item2_a_valid_writer_stamp_from_a_non_canonical_marker_is_proved_against_the_original_marker_of_the_run(tworld, capsys):
    """The writer hashes the marker AS GIVEN (Z timestamps, reversed class order) and stores the normalised component, so the stamp's
    digest is not the reconstruction's. With the run row alive the proof is the original preimage and the teardown accepts it."""
    w = tworld
    rid = _run(w, marker=NON_CANONICAL)
    _slice_steps(w, rid)
    _teardown(w, dry_run=True)
    assert f"stamp\tproved against the ORIGINAL marker of run {rid}" in capsys.readouterr().out
    _teardown(w)
    assert all(n == 0 for n in _counts(w).values())


def test_item2_the_same_stamp_with_no_run_row_left_is_refused_and_the_refusal_says_why(tworld):
    w = tworld
    rid = _run(w, marker=NON_CANONICAL, receipt=False)
    _slice_steps(w, rid)
    _prune(w, rid)                                                           # the watchdog's prune: nothing left to read the preimage from
    _refused_and_untouched(w, r"original marker preimage could not prove it \(no owned run row survives\).*reconstruction")


# ── Codex round 4 / Stream B (v1.3): T1, T4, TB1, D3 on a real database ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("parent", ["run", "manifest"])
def test_t1_a_reference_committed_while_the_teardown_waits_for_the_row_lock_is_seen_by_the_checks(tworld, parent):
    """THE RACE: a competing session inserts a row referencing an owned run (or the manifest) and has not yet committed. It holds a KEY SHARE
    lock on the parent row. The teardown's FOR UPDATE row lock waits for it; when the session commits, the teardown's VALIDATION (which runs
    after the lock) sees the reference and refuses by name. Without the row lock the checks would run first and pass, the DELETE would then
    wait out the same lock and, once the session committed, silently set the reference to NULL (or fail on a NO ACTION one): the dry run
    would 'succeed'. So this test fails if either FOR UPDATE is removed (mutation-checked)."""
    w = tworld
    _slice_run(w)
    if parent == "run":
        w.conn.execute("CREATE TABLE public.conversations_like (id serial PRIMARY KEY, archived_by_run_id uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)")
        sql, args = "INSERT INTO public.conversations_like (archived_by_run_id) SELECT id FROM public.build_runs LIMIT 1", ()
        named = r"conversations_like\.archived_by_run_id \(1 row\(s\)"
    else:
        w.conn.execute("CREATE TABLE public.contacts_like (id serial PRIMARY KEY, input_generation_vector_id uuid REFERENCES public.kala_gochara_publication(manifest_id))")
        sql, args = "INSERT INTO public.contacts_like (input_generation_vector_id) SELECT manifest_id FROM public.kala_gochara_publication WHERE generation = %s", (GEN,)
        named = r"contacts_like\.input_generation_vector_id \(1 row\(s\)"
    other = psycopg.connect(w.dsn, autocommit=False)
    outcome = {}

    def teardown_thread():
        try:
            _teardown(w, dry_run=True)
            outcome["result"] = "succeeded"
        except BaseException as exc:                          # noqa: BLE001
            outcome["result"] = exc

    try:
        other.execute(sql, args)                              # uncommitted: KEY SHARE on the parent row
        before = _snapshot(w)
        t = threading.Thread(target=teardown_thread)
        t.start()
        time.sleep(3)                                         # the teardown is waiting on the lock (lock_timeout is 10 s)
        assert t.is_alive(), f"the teardown did not wait for the row lock: {outcome}"
        other.commit()                                        # the reference becomes visible; the waiting lock is released
        t.join(60)
    finally:
        other.close()
    result = outcome.get("result")
    assert isinstance(result, td.TeardownRefused), result
    assert __import__("re").search(named, str(result)), str(result)
    assert _snapshot(w) == before


def test_t4_a_surviving_run_with_a_wrong_plan_digest_is_refused_even_though_the_stamp_is_canonical(tworld):
    w = tworld
    rid = _slice_run(w)
    w.conn.execute("UPDATE public.build_runs SET plan_manifest_digest = %s WHERE id = %s", ("0" * 64, rid))
    _refused_and_untouched(w, r"an owned run row survives.*does not match its plan_manifest_digest")


def test_tb1_a_chain_row_of_a_class_outside_the_stamp_is_refused_and_nothing_is_deleted(tworld):
    w = tworld
    _slice_run(w)
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("UPDATE public.kala_gochara_coverage SET partition_key = 'zz_not_a_stamped_class' WHERE generation = %s"
                       " AND partition_kind = 'event_class' AND partition_key = (SELECT min(partition_key) FROM public.kala_gochara_coverage"
                       " WHERE generation = %s AND partition_kind = 'event_class')", (GEN, GEN))
    _refused_and_untouched(w, r"belong to a class outside the stamp.*'coverage': 1")


def _interrupted_replacement(w):
    """The earlier slice's chain and snapshot (run r1), then a later slice (r2, a different horizon) that committed its stamped manifest
    and died before its snapshot substep replaced anything."""
    from datetime import timedelta
    r1 = _slice_run(w, receipt=False)
    later = dict(MARKER, horizon=[SHORT[0].isoformat(), (SHORT[1] + timedelta(days=1)).isoformat()])
    r2 = _run(w, marker=later, part="p2")
    _step(w, r2, writer_mod.MANIFEST_SUBSTEP)
    manifest_vector, snapshot_vector = (w.conn.execute(q, (GEN,)).fetchone()[0] for q in (
        "SELECT input_generation_vector FROM public.kala_gochara_publication WHERE generation = %s",
        "SELECT input_generation_vector FROM public.ka_gochara_search_input_snapshot WHERE generation = %s"))
    assert manifest_vector != snapshot_vector                                  # the interrupted-replacement state, really
    assert manifest_vector["test_slice"]["marker_digest"] != snapshot_vector["test_slice"]["marker_digest"]
    return r1, r2


def test_d3_an_older_proven_test_chain_under_a_newer_proven_test_manifest_is_removed(tworld):
    """Each stamp is proved by an owned run's ORIGINAL marker (the shared proof, applied to the snapshot's own vector)."""
    w = tworld
    _interrupted_replacement(w)
    assert _counts(w)["ka_gochara_contact"] >= 5
    _teardown(w)
    assert all(n == 0 for n in _counts(w).values())


def test_d3_the_same_state_is_refused_once_the_older_run_is_pruned_and_the_runbook_not_the_other_script_is_named(tworld):
    w = tworld
    r1, _r2 = _interrupted_replacement(w)
    _prune(w, r1)                                                              # the older stamp can no longer be proved
    before = _snapshot(w)
    with pytest.raises(td.TeardownRefused, match="older stamp is not proved by an owned test run") as exc:
        _teardown(w)
    assert "V5_SMALLTEST_TEARDOWN_RUNBOOK" in str(exc.value) and "dispatch" not in str(exc.value).lower()
    assert _snapshot(w) == before
