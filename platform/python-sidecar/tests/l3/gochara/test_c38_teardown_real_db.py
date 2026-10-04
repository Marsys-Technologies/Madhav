"""C38 — the small-test TEARDOWN executed for real against the chain tables.

The unit tests in platform/scripts/__tests__/test_teardown_v5_small_test.py use a recording fake, so they cannot show that the
script's SQL is valid or that its deletes respect the real foreign keys. Here the script's own `teardown()` runs over a database
holding a REAL build chain (the writer's substeps on the real migration chain, cloned from PR 3132's template harness) plus the
orchestrator tables the script touches (asset_registry, build_runs, build_run_assets, asset_throughput,
asset_provenance_receipts), created with the same foreign keys production has — notably migration 596's
`asset_provenance_receipts.build_id REFERENCES build_runs(id) ON DELETE SET NULL`, which is why the receipts must go BEFORE the
run rows: a receipt left behind with a NULL run link is evidence whose run cannot be found, which the Nirmana monitor (N-137) reads as
NON-test evidence.

DEPENDS ON PR 3132 (A5.5f): it imports that PR's `_World` / `template` harness.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod

from .test_a55_replace_chain import CHART_ID, CLASSES, GEN, SHORT, _World, template  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "platform" / "scripts"))
import teardown_v5_small_test_job as td  # noqa: E402

ASSET = td.ASSET_ID
OTHER_GEN = "5.9"
STUB_DDL = (
    "CREATE TABLE IF NOT EXISTS public.kala_gochara_authority (chart_id uuid PRIMARY KEY, authoritative_generation text)",
    "CREATE TABLE public.asset_registry (asset_id text PRIMARY KEY, scope text, is_active boolean, has_writer boolean,"
    " has_substeps boolean, writer_timeout_seconds integer, depends_on text[], target_table text, count_sql text,"
    " target_floor integer, estimated_seconds integer)",
    "CREATE TABLE public.build_runs (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid, scope text,"
    " scope_target text, state text, triggered_by text)",
    "CREATE TABLE public.build_run_assets (run_id uuid NOT NULL REFERENCES public.build_runs(id), asset_id text)",
    "CREATE TABLE public.asset_throughput (chart_id uuid, asset_id text)",
    # migration 596, the column that matters: the run link is SET NULL when the run row is deleted
    "CREATE TABLE public.asset_provenance_receipts (asset_id text NOT NULL REFERENCES public.asset_registry(asset_id)"
    " ON DELETE CASCADE, chart_id uuid, partition_key text NOT NULL DEFAULT 'p',"
    " build_id uuid REFERENCES public.build_runs(id) ON DELETE SET NULL)",
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


def _test_run(w, triggered_by=td.TRIGGERED_BY):
    rid = uuid.uuid4()
    w.conn.execute("INSERT INTO public.build_runs (id, chart_id, scope, scope_target, state, triggered_by)"
                   " VALUES (%s, %s, 'asset_set', %s, 'completed', %s)", (rid, CHART_ID, ASSET, triggered_by))
    w.conn.execute("INSERT INTO public.build_run_assets VALUES (%s, %s)", (rid, ASSET))
    w.conn.execute("INSERT INTO public.asset_throughput VALUES (%s, %s)", (CHART_ID, ASSET))
    w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, build_id) VALUES (%s, %s, %s)",
                   (ASSET, CHART_ID, rid))
    return rid


def _survivors(w):
    """A Moon partition of this generation, a whole other generation, another asset's receipt: none may be touched."""
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


def _counts(w):
    out = {}
    for table, extra in td.GENERATION_TABLES:
        out[table] = w.conn.execute(f"SELECT count(*) FROM public.{table} WHERE chart_id = %s AND generation = %s{extra}",
                                    (CHART_ID, GEN)).fetchone()[0]
    return out


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


def _built_with_test_run(w):
    w.build(SHORT)
    _test_run(w)
    _survivors(w)
    assert _counts(w)["ka_gochara_contact"] >= 5 and _counts(w)["ka_gochara_relationship_record"] >= 1
    assert _counts(w)["ka_gochara_search_inventory"] >= 1 and _counts(w)["kala_gochara_publication"] == 1


def test_the_teardown_removes_the_whole_small_test_and_keeps_everything_else(tworld, capsys):
    w = tworld
    _built_with_test_run(w)
    sky_before = w.conn.execute("SELECT count(*) FROM public.ka_gochara_sky_event").fetchone()[0]
    assert sky_before > 0

    _teardown(w, dry_run=True)                                       # lists, changes nothing
    listed = capsys.readouterr().out
    assert "asset_provenance_receipts\t1" in listed and "ka_gochara_contact\t" in listed
    assert _counts(w)["ka_gochara_contact"] >= 5

    _teardown(w)
    after = _counts(w)
    assert all(n == 0 for n in after.values()), {t: n for t, n in after.items() if n}
    c = w.conn
    assert c.execute("SELECT count(*) FROM public.asset_provenance_receipts WHERE asset_id = %s", (ASSET,)).fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM public.build_runs WHERE triggered_by = %s", (td.TRIGGERED_BY,)).fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM public.build_run_assets").fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM public.asset_throughput WHERE asset_id = %s", (ASSET,)).fetchone()[0] == 0
    # what stays
    assert c.execute("SELECT count(*) FROM public.asset_provenance_receipts WHERE asset_id = 'other_asset'").fetchone()[0] == 1
    assert c.execute("SELECT count(*) FROM public.kala_gochara_coverage WHERE generation = %s AND partition_kind = 'moon_on_demand'",
                     (GEN,)).fetchone()[0] == 1
    assert c.execute("SELECT count(*) FROM public.ka_gochara_contact WHERE generation = %s", (OTHER_GEN,)).fetchone()[0] == 1
    assert c.execute("SELECT count(*) FROM public.ka_gochara_sky_event").fetchone()[0] == sky_before
    row = c.execute("SELECT is_active, has_substeps, writer_timeout_seconds, depends_on FROM public.asset_registry"
                    " WHERE asset_id = %s", (ASSET,)).fetchone()
    assert row == (False, True, 7200, ["ga_positions", "ga_dashas"])


def test_deleting_the_run_first_would_orphan_the_receipt_which_is_why_the_receipts_go_first(tworld):
    """The real foreign key, shown: delete the run row and the receipt survives with a NULL run link."""
    w = tworld
    rid = _test_run(w)
    w.conn.execute("DELETE FROM public.build_run_assets WHERE run_id = %s", (rid,))
    w.conn.execute("DELETE FROM public.build_runs WHERE id = %s", (rid,))
    assert w.conn.execute("SELECT count(*), count(build_id) FROM public.asset_provenance_receipts WHERE asset_id = %s",
                          (ASSET,)).fetchone() == (1, 0)


def test_a_pruned_run_with_an_unstamped_manifest_cannot_be_attributed_and_is_refused(tworld):
    w = tworld
    w.build(SHORT)
    rid = _test_run(w)
    w.conn.execute("DELETE FROM public.build_run_assets WHERE run_id = %s", (rid,))
    w.conn.execute("DELETE FROM public.build_runs WHERE id = %s", (rid,))        # the watchdog's prune: receipt link -> NULL
    before = _counts(w)
    with pytest.raises(RuntimeError, match="cannot be attributed|NO build_runs row"):
        _teardown(w)
    assert _counts(w) == before


def test_a_pruned_run_with_a_slice_stamped_manifest_is_still_removable(tworld):
    w = tworld
    w.build(SHORT)
    rid = _test_run(w)
    w.conn.execute("DELETE FROM public.build_run_assets WHERE run_id = %s", (rid,))
    w.conn.execute("DELETE FROM public.build_runs WHERE id = %s", (rid,))
    with w.conn.transaction():              # the C46 stamp: the manifest identifies itself as a test candidate
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector ="
                       " jsonb_set(input_generation_vector, '{stored_scope}', '\"test_slice\"') WHERE generation = %s", (GEN,))
    _teardown(w)
    assert all(n == 0 for n in _counts(w).values())
    assert w.conn.execute("SELECT count(*) FROM public.asset_provenance_receipts WHERE asset_id = %s", (ASSET,)).fetchone()[0] == 0


def test_a_non_test_build_of_the_asset_is_refused(tworld):
    w = tworld
    w.build(SHORT)
    _test_run(w)
    _test_run(w, triggered_by="cockpit-manual-build")
    before = _counts(w)
    with pytest.raises(RuntimeError, match="NON-test build run"):
        _teardown(w)
    assert _counts(w) == before
