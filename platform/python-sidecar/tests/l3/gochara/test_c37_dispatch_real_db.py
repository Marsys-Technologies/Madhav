"""C37 — the small-test DISPATCH executed for real (steward DISPATCH-REALDB; Codex round 4 and Stream B X1).

The 107 unit tests in platform/scripts/__tests__/test_dispatch_v5_small_test.py use a recording fake psycopg, so none of them can show that
the dispatch's SQL is valid, that its locks and the one-active-run index behave, that a refusal really leaves nothing, or that it runs with
the privileges its role holds. Here `dispatch.cli()` runs against a database with the REAL orchestrator tables (migrations 167..1201,
including 595's immutability trigger and one-active-run index and 596's receipts and freshness with their foreign keys), the real Gochara
chain, and the ka_gochara_v5 registry row INACTIVE in its migration-1304 shape.

Shown: staging commits exactly one planned run carrying the marker and its digest; every refusal leaves the database as it was; a dry run
leaves no row and no freshness change; the script runs as a role holding exactly the privileges it needs and a missing one fails the
staging with nothing written; END TO END — the dispatch stages a run with the registry row INACTIVE, the REAL runner entry point
(`python -m pipeline.orchestrator.main --run-id`) executes that run id and the v5 writer really runs the slice, and the teardown then
removes everything and the dispatch can stage again.

NOT shown (stated in the tests that touch it): a COMPLETED slice. For class `marriage` the real run completes through record P1 to P4 and
window P1 and P2, then stops at window P3 on 'member geometry verification' of zero-length (grazing) contacts: a separate defect awaiting
its own ruling (the stop is deliberately NOT pinned here); the teardown is exercised on that real, interrupted state. The first completed
slice through the real runner will be the production small test.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from pipeline.orchestrator.asset_runner import get_writer_source_hash
from pipeline.orchestrator.writers import WRITER_REGISTRY, discover_all
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod

from . import _runner_world as rw
from .test_a55_replace_chain import CHART_ID, SHORT, _World, template  # noqa: F401

SCRIPTS = Path(__file__).resolve().parents[5] / "platform" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import dispatch_v5_small_test_job as dispatch  # noqa: E402
import teardown_v5_small_test_job as td  # noqa: E402

ASSET = dispatch.ASSET_ID
#: `marriage`, not the first scored class: achievement_recognition (and 7 other classes whose signature houses are unknown) fail their P1
#: anchor self-check for a structural reason independent of everything here (steward ruling P1-EMPTY-CLASS; a separate PR fixes the verifier)
ONE_CLASS = "marriage"
ARGV = ["--i-am-steward", "--after-settled-1", "--run", "one_class_full", "--classes", ONE_CLASS]
ROLE = "dispatch_exact_role"


@pytest.fixture(scope="module")
def dtemplate(template):  # noqa: F811
    """The a55 template + the real orchestrator schema + the seeded registry, built ONCE and cloned per test."""
    admin, tpl, dsn = template
    name = f"{tpl}_orch"
    admin.execute(f'CREATE DATABASE "{name}" TEMPLATE "{tpl}"')
    conn = psycopg.connect(make_conninfo(dsn, dbname=name), autocommit=True, connect_timeout=3)
    try:
        rw.apply_orchestrator_schema(conn)
        # the resumption ledger the pre-dispatch readback counts (no v5 path writes it; the readback must still run)
        conn.execute((rw.REPO / "platform/migrations/436_build_substep_progress.sql").read_text(encoding="utf-8"))
        conn.execute("CREATE TABLE IF NOT EXISTS public.kala_gochara_authority (chart_id uuid PRIMARY KEY, authoritative_generation text)")
        discover_all()
        rw.seed_registry(conn, set(WRITER_REGISTRY) - {"bg_nakshatra_medical", "bg_transit_engine"})
    finally:
        conn.close()
    yield admin, name, make_conninfo(dsn, dbname=name)
    admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@pytest.fixture()
def dw(dtemplate):
    w = _World(dtemplate)
    try:
        yield w
    finally:
        w.close()


def _cli(w, argv, capsys, *, user=None):
    prior = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = make_conninfo(w.dsn, user=user) if user else w.dsn
    try:
        code = dispatch.cli(argv)
    finally:
        if prior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior
    streams = capsys.readouterr()
    return code, streams.out, streams.err


def _state(w):
    """Everything the dispatch could touch, as a comparable value (the registry row's xmin shows even a no-op UPDATE)."""
    c = w.conn
    return {
        "runs": c.execute("SELECT count(*) FROM public.build_runs").fetchone()[0],
        "run_assets": c.execute("SELECT count(*) FROM public.build_run_assets").fetchone()[0],
        "throughput": c.execute("SELECT asset_id, state FROM public.asset_throughput WHERE chart_id = %s ORDER BY 1", (CHART_ID,)).fetchall(),
        "freshness": c.execute("SELECT asset_id, partition_key, freshness_state, observed_at FROM public.asset_freshness ORDER BY 1, 2").fetchall(),
        "receipts": c.execute("SELECT count(*) FROM public.asset_provenance_receipts").fetchone()[0],
        "registry": c.execute("SELECT asset_id, is_active, xmin::text FROM public.asset_registry WHERE asset_id = %s", (ASSET,)).fetchall(),
        "manifests": c.execute("SELECT count(*) FROM public.kala_gochara_publication").fetchone()[0],
    }


def _plant_active_run(w, state="running"):
    w.conn.execute("INSERT INTO public.build_runs (chart_id, scope, scope_target, action, state, plan, triggered_by)"
                   " VALUES (%s, 'asset', 'ga_positions', 'rebuild', %s, '[\"ga_positions\"]'::jsonb, 'cockpit')", (CHART_ID, state))


# ── staging, refusals, dry run ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_staging_commits_exactly_one_planned_run_with_the_marker_and_its_digest(dw, capsys):
    before = _state(dw)
    code, out, err = _cli(dw, ARGV + ["--execute"], capsys)
    assert code == 0, err
    run_id = out.strip()
    runs = dw.conn.execute("SELECT id, state, scope, scope_target, action, triggered_by, plan_manifest, plan_manifest_digest, created_at"
                           " FROM public.build_runs WHERE triggered_by = 'gochara-v5-small-test'").fetchall()
    assert len(runs) == 1 and str(runs[0][0]) == run_id and runs[0][1] == "planned"
    assert runs[0][2:6] == ("asset_set", ASSET, "rebuild", "gochara-v5-small-test")
    manifest, digest = runs[0][6], runs[0][7]
    assert manifest["gochara_v5_test_slice"]["classes"] == [ONE_CLASS] and manifest["gochara_v5_test_slice"]["run"] == "one_class_full"
    assert digest == hashlib.sha256(dispatch._canonical_json(manifest).encode("utf-8")).hexdigest()
    assert manifest["assets"][0]["expected_code_digest"] == get_writer_source_hash(ASSET)
    assert dw.conn.execute("SELECT count(*) FROM public.build_run_assets WHERE run_id = %s", (run_id,)).fetchone()[0] == 1
    after = _state(dw)
    assert after["runs"] == before["runs"] + 1 and after["run_assets"] == before["run_assets"] + 1
    assert ("ka_gochara_v5", "dormant") in after["throughput"]
    assert after["registry"] == before["registry"], "the registry row was not touched (not even a no-op UPDATE)"
    assert after["freshness"] == before["freshness"] and after["receipts"] == before["receipts"]
    # D4: the printed deadlines come from the STORED created_at
    stamp = err.split("tear the small test down by ")[1].split(" ")[0]
    import datetime as dt
    assert dt.datetime.fromisoformat(stamp) == (runs[0][8] + dt.timedelta(days=90)).replace(microsecond=0)   # printed to the second


def test_a_dry_run_leaves_no_row_and_no_freshness_change(dw, capsys):
    before = _state(dw)
    code, out, err = _cli(dw, ARGV, capsys)                                     # no --execute: the default is a dry run
    assert code == 0, err
    assert json.loads(out)["triggered_by"] == "gochara-v5-small-test"
    assert _state(dw) == before
    assert "ROLLED BACK" in err


def test_a_second_dispatch_is_refused_by_name_while_the_first_run_is_active(dw, capsys):
    assert _cli(dw, ARGV + ["--execute"], capsys)[0] == 0
    before = _state(dw)
    code, out, err = _cli(dw, ARGV + ["--execute"], capsys)
    assert code == 1 and "a build run is already active on chart" in err and "planned" in err
    assert _state(dw) == before


def _refusal_cases():
    def published(w):
        _stage_manifest(w, "published")

    def candidate(w):
        _stage_manifest(w, "candidate")

    def registry_active(w):
        w.conn.execute("UPDATE public.asset_registry SET is_active = true WHERE asset_id = %s", (ASSET,))

    def probe_green_shortcut(w):
        w.conn.execute("UPDATE public.asset_registry SET integrity_check_sql = 'SELECT true', rebuild_on_probe_fail = true WHERE asset_id = %s", (ASSET,))

    def receipt(w):
        w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, receipt_version, receipt_state)"
                       " VALUES (%s, %s, 'p', 'v1', 'proven')", (ASSET, CHART_ID))

    def dependent(w):
        w.conn.execute("UPDATE public.asset_registry SET depends_on = ARRAY['ka_gochara_v5'] WHERE asset_id = 'ga_positions'")

    def active_run(w):
        _plant_active_run(w, "paused")

    def pre_1304_shape(w):
        w.conn.execute("UPDATE public.asset_registry SET has_substeps = false, writer_timeout_seconds = 600 WHERE asset_id = %s", (ASSET,))

    return [("published", published, "PUBLISHED"), ("existing_candidate", candidate, "already has output"),
            ("registry_active", registry_active, "is_active"), ("probe_green_shortcut", probe_green_shortcut, "integrity_check_sql|rebuild_on_probe_fail"),
            ("receipt_exists", receipt, "receipts of the asset|provenance receipt"), ("dependent_asset", dependent, "nothing may depend"),
            ("active_run", active_run, "already active"), ("pre_1304_shape", pre_1304_shape, "has_substeps|writer_timeout_seconds")]


def _stage_manifest(w, status):
    """A real candidate manifest of generation 5.0 through the writer's own manifest substep (a stand-in run id: no marker, default stamp)."""
    from pipeline.orchestrator.writers import ContextSpec, SubStep
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id=str(uuid.uuid4()), db_conn=w.conn, dry_run=False,
                      config={"chart_id": CHART_ID, "ephe_path": os.environ["SE_EPHE_PATH"], "horizon": SHORT})
    with w.conn.transaction():
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    if status == "published":
        with w.conn.transaction():
            w.conn.execute("SET LOCAL session_replication_role = replica")
            w.conn.execute("UPDATE public.kala_gochara_publication SET status = 'published' WHERE generation = '5.0'")


@pytest.mark.parametrize("name, plant, message", _refusal_cases(), ids=lambda v: v if isinstance(v, str) and v.islower() else "")
def test_every_refusal_leaves_the_database_exactly_as_it_was(dw, capsys, name, plant, message):
    plant(dw)
    before = _state(dw)
    code, out, err = _cli(dw, ARGV + ["--execute"], capsys)
    assert code == 1, (name, err)
    assert __import__("re").search(message, err), (name, err)
    assert _state(dw) == before, f"{name}: a refusal changed the database"


def test_a_lookup_sees_a_staged_run_the_dry_run_would_refuse_over(dw, capsys):
    """D1 on a real database: after a staged run exists the dry run REFUSES (active run), the lookup does not."""
    assert _cli(dw, ARGV + ["--execute"], capsys)[0] == 0
    run_id = dw.conn.execute("SELECT id FROM public.build_runs WHERE triggered_by = 'gochara-v5-small-test'").fetchone()[0]
    assert _cli(dw, ARGV, capsys)[0] == 1
    before = _state(dw)
    code, out, err = _cli(dw, ["--lookup", str(run_id)], capsys)
    assert code == 0 and json.loads(out)["runs"][0]["id"] == str(run_id) and json.loads(out)["runs"][0]["state"] == "planned"
    assert _state(dw) == before


# ── the role ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────

#: what `data_plane_builder` is documented to hold that this script needs (Stream B's production catalog, DB1), granted to a role that holds
#: NOTHING else; asset_registry gets SELECT and the column UPDATE grant FOR SHARE needs, NOT UPDATE(is_active)
DISPATCH_PRIVILEGES = {
    "asset_registry": ("SELECT",),
    "asset_provenance_receipts": ("SELECT",), "asset_freshness": ("SELECT",), "ka_gochara_generation_seal": ("SELECT",),
    "kala_gochara_authority": ("SELECT",), "kala_gochara_publication": ("SELECT",),
    "build_runs": ("SELECT", "INSERT"), "build_run_assets": ("SELECT", "INSERT"), "asset_throughput": ("SELECT", "INSERT", "UPDATE"),
}


@pytest.fixture()
def role_world(dw):
    dw.admin.execute(f"DROP ROLE IF EXISTS {ROLE}")
    dw.admin.execute(f"CREATE ROLE {ROLE} LOGIN")
    dw.conn.execute("REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC")     # production revokes PUBLIC EXECUTE
    try:
        yield dw
    finally:
        dw.conn.execute(f"DROP OWNED BY {ROLE}")
        dw.admin.execute(f"DROP ROLE IF EXISTS {ROLE}")


def _grant(w, skip=()):
    c = w.conn
    for table, privs in DISPATCH_PRIVILEGES.items():
        for priv in privs:
            if f"{table}:{priv}" not in skip:
                c.execute(f"GRANT {priv} ON public.{table} TO {ROLE}")
    for table, _extra in dispatch.shared.OUTPUT_TABLES:
        if f"{table}:SELECT" not in skip:
            c.execute(f"GRANT SELECT ON public.{table} TO {ROLE}")
    if "asset_registry:UPDATE(probe)" not in skip:                      # the column grant that makes FOR SHARE work (the builder's four probe columns)
        c.execute(f"GRANT UPDATE (service_health, last_invoked_at, last_selftest_at, selftest_detail) ON public.asset_registry TO {ROLE}")
    # only the lock function: ka_gochara_generation_is_sealed is called by the DELETE guards (the teardown), never by the dispatch — a test
    # showed the dispatch runs without it, so it is not part of this script's needs even though the builder holds it
    if "execute:ka_gochara_lock_chart(uuid)" not in skip:
        c.execute(f"GRANT EXECUTE ON FUNCTION public.ka_gochara_lock_chart(uuid) TO {ROLE}")


def test_the_dispatch_runs_as_a_role_holding_exactly_the_documented_privileges(role_world, capsys):
    w = role_world
    _grant(w)
    code, out, err = _cli(w, ARGV, capsys, user=ROLE)                        # the rehearsal first
    assert code == 0, err
    code, out, err = _cli(w, ARGV + ["--execute"], capsys, user=ROLE)
    assert code == 0, err
    assert w.conn.execute("SELECT count(*) FROM public.build_runs WHERE triggered_by = 'gochara-v5-small-test'").fetchone()[0] == 1
    assert w.conn.execute("SELECT is_active FROM public.asset_registry WHERE asset_id = %s", (ASSET,)).fetchone()[0] is False


@pytest.mark.parametrize("skip", ["build_runs:INSERT", "build_run_assets:INSERT", "asset_throughput:UPDATE", "asset_registry:UPDATE(probe)",
                                  "execute:ka_gochara_lock_chart(uuid)",
                                  "kala_gochara_publication:SELECT", "asset_provenance_receipts:SELECT"],
                         ids=lambda s: s.replace(":", "_").replace("(uuid)", "").replace("(uuid, text)", "").replace("(probe)", ""))
def test_a_missing_grant_fails_the_staging_and_nothing_is_written(role_world, capsys, skip):
    w = role_world
    _grant(w, skip=(skip,))
    before = _state(w)
    code, out, err = _cli(w, ARGV + ["--execute"], capsys, user=ROLE)
    assert code == 1 and "InsufficientPrivilege" in err and "ROLLBACK CONFIRMED" in err, err
    assert _state(w) == before


def test_the_readbacks_run_read_only_on_a_real_database(dw):
    """The two read-only production readbacks parse and execute (their expected values are in their comments)."""
    for name in ("v5_small_test_registry_row_readback.sql", "v5_small_test_incoming_fks_readback.sql", "v5_small_test_predispatch_readback.sql"):
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        code_only = "\n".join(x for x in text.splitlines() if not x.strip().startswith("--"))          # comments may contain ';'
        statements = [s for s in code_only.split(";") if s.strip()]
        with dw.conn.transaction():
            dw.conn.execute("SET TRANSACTION READ ONLY")
            for statement in statements:
                code = "\n".join(x for x in statement.splitlines() if not x.strip().startswith("--")).strip()
                if code.upper() in ("BEGIN READ ONLY", "COMMIT"):
                    continue
                dw.conn.execute(code)                                                     # raises on any parse, name or write error


# ── END TO END: dispatch -> the REAL runner -> teardown ─────────────────────────────────────────────────────────────────────────

def test_end_to_end_the_dispatch_stages_the_real_runner_runs_the_slice_and_the_teardown_removes_it(dw, capsys):
    """Registry row INACTIVE throughout. (1) the dispatch stages a run; (2) the REAL entry point executes THAT run id — the writer runs
    rules, convention, 8 bodies, manifest, snapshot, inventory, coverage and the first record grain of the class (and, observed, further
    — see the module docstring); (3) the registry row is still inactive; (4) the teardown removes whatever state the run left; (5) the
    dispatch can stage again."""
    w = dw
    code, out, err = _cli(w, ARGV + ["--execute"], capsys)
    assert code == 0, err
    run_id = out.strip()
    result = rw.run_real_entry_point(w.dsn, run_id, ephe_env=os.environ["SE_EPHE_PATH"])
    keys = [e["substep_key"] for e in rw.substep_events(result["stdout"])]
    run = w.conn.execute("SELECT state FROM public.build_runs WHERE id = %s", (run_id,)).fetchone()[0]
    asset = w.conn.execute("SELECT state, error FROM public.build_run_assets WHERE run_id = %s", (run_id,)).fetchone()
    print("E2E:", {"code": result["code"], "seconds": round(result["seconds"], 1), "run": run, "substeps": keys, "error_head": (asset[1] or "")[:120]})
    head = ["rules", "convention"] + [f"body:{b}" for b in writer_mod.SUBSTRATE_BODIES] + \
        [writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP, f"inventory:{ONE_CLASS}", f"coverage:{ONE_CLASS}", f"record:{ONE_CLASS}:P1"]
    assert keys[:len(head)] == head, (keys, result["stderr"][-1500:])
    assert result["code"] == 0                                                    # exit 0 whatever the run state (the exit-code finding)
    assert run in ("failed", "completed") and "P1 anchor verification failed" not in (asset[1] or "")
    assert w.conn.execute("SELECT is_active FROM public.asset_registry WHERE asset_id = %s", (ASSET,)).fetchone()[0] is False
    assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_publication WHERE generation = '5.0'").fetchone()[0] == 1
    # the teardown removes the real interrupted state
    prior = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = w.dsn
    try:
        td.teardown(dry_run=False)
    finally:
        if prior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior
    capsys.readouterr()
    assert w.conn.execute("SELECT count(*) FROM public.build_runs WHERE triggered_by = 'gochara-v5-small-test'").fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_publication WHERE generation = '5.0'").fetchone()[0] == 0
    assert w.conn.execute("SELECT is_active FROM public.asset_registry WHERE asset_id = %s", (ASSET,)).fetchone()[0] is False
    assert _cli(w, ARGV + ["--execute"], capsys)[0] == 0                          # a clean start: the dispatch stages again
