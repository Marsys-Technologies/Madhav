"""Drive the REAL registered writers of this branch (ga_positions upstream fixture, ga_vargas with the F-A2 writer, ga_structural) through the
REAL data-plane path as role data_plane_builder: real open_l1_data_plane_generation, guard trigger, l1_data_plane_capture_row and
complete_l1_data_plane_partition (the l1_producer_contract wrapper), exactly as the rehearsal harness did.

The upstream facts (chart_facts of ga_positions) are FIXTURES: the real ga_positions writer body is run as the superuser with
session_replication_role = replica (guards/captures off), the same way the rehearsal loaded them; they are not the system under test."""
from __future__ import annotations

import importlib
import os
import sys
import time
import traceback
import uuid

import psycopg
import psycopg.rows

import conftest as cf

SIDECAR = cf.REPO / "platform/python-sidecar"
os.environ.setdefault("SE_EPHE_PATH", "/tmp/se1")
os.environ.setdefault("SWE_EPHE_PATH", "/tmp/se1")
os.environ.setdefault("CONDUCTOR_HALT_LOG_DIR_OVERRIDE", "/private/tmp/claude-504/dpfa2/halt")
for p in (str(SIDECAR), str(cf.REPO)):
    if p not in sys.path:
        sys.path.insert(0, p)


def ephemeris_available() -> bool:
    return os.path.isdir(os.environ["SE_EPHE_PATH"]) and any(f.endswith(".se1") for f in os.listdir(os.environ["SE_EPHE_PATH"]))


def connect(cluster, db, user="data_plane_builder"):
    return psycopg.connect(host="127.0.0.1", port=cluster.port, dbname=db, user=user, row_factory=psycopg.rows.dict_row)


def new_run(cluster, db, asset_id, chart=cf.CHART):
    run = str(uuid.uuid4())
    cluster.su(db, "INSERT INTO build_runs(id,chart_id,state) VALUES (%s,%s,'running')", (run, chart))
    cluster.su(db, "INSERT INTO build_run_assets(run_id,asset_id,state) VALUES (%s,%s,'building')", (run, asset_id))
    return run


def finish_run(cluster, db, run, asset_id):
    cluster.su(db, "UPDATE build_run_assets SET state='complete' WHERE run_id=%s AND asset_id=%s", (run, asset_id))
    cluster.su(db, "UPDATE build_runs SET state='completed' WHERE id=%s", (run,))


def fail_run(cluster, db, run, asset_id):
    cluster.su(db, "UPDATE build_run_assets SET state='error' WHERE run_id=%s AND asset_id=%s", (run, asset_id))
    cluster.su(db, "UPDATE build_runs SET state='failed' WHERE id=%s", (run,))


def drive(writer, ctx, only=None):
    """Replica of asset_runner._drive_substeps: SAVEPOINT writer_exec / RELEASE / commit per sub-step. Returns {key: rows_inserted}."""
    conn = ctx.db_conn
    out = {}
    for step in writer.plan_substeps(ctx):
        if only is not None and step.key not in only:
            continue
        with conn.cursor() as cur:
            cur.execute("SAVEPOINT writer_exec")
            try:
                r = writer.run_substep(ctx, step)
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT writer_exec")
                conn.rollback()
                raise
            cur.execute("RELEASE SAVEPOINT writer_exec")
        conn.commit()
        out[step.key] = r.rows_inserted
    return out


def shim_ascendant_longitude(module):
    """HARNESS-ONLY shim for the pre-existing defect: compute_chart()['ascendant'] has 'longitude_deg' only, ga_structural requires 'longitude'."""
    orig = module.compute_chart

    def shim(*a, **k):
        o = orig(*a, **k)
        for key in ("ascendant", "lagna"):
            asc = o.get(key)
            if isinstance(asc, dict) and "longitude" not in asc and "longitude_deg" in asc:
                asc["longitude"] = asc["longitude_deg"]
        return o
    module.compute_chart = shim


def load_writer(asset_id):
    mod = importlib.import_module(f"pipeline.orchestrator.writers.{asset_id}")
    return [v for v in vars(mod).values() if isinstance(v, type) and getattr(v, "asset_id", "") == asset_id][0]()


def context(cluster, db, asset_id, run, conn):
    from pipeline.orchestrator.writers import ContextSpec
    return ContextSpec(asset_id=asset_id, build_id=run, db_conn=conn, config={"chart_id": cf.CHART, "birth_params": cf.BP})


def load_upstream(cluster, db, names=("ga_positions",)):
    """Fixtures: chart_facts / chart_divisionals written by the REAL upstream writer bodies as the superuser with triggers off."""
    import ga_writers._idempotency as idem
    idem.authorize_chart_fact_delete = lambda *a, **k: None
    conn = psycopg.connect(host="127.0.0.1", port=cluster.port, dbname=db, user="postgres", row_factory=psycopg.rows.dict_row)
    conn.execute("SET session_replication_role = replica")
    conn.commit()
    run = str(uuid.uuid4())
    out = {}
    for n in names:
        try:
            w = load_writer(n)
            ctx = context(cluster, db, n, run, conn)
            if getattr(w, "has_substeps", False):
                for st in w.plan_substeps(ctx):
                    fn = w.run_substep.__wrapped__ if hasattr(w.run_substep, "__wrapped__") else w.run_substep
                    out[(n, st.key)] = fn(w, ctx, st).rows_inserted
                    conn.commit()
            else:
                fn = w.run.__wrapped__ if hasattr(w.run, "__wrapped__") else w.run
                out[n] = fn(w, ctx).rows_inserted
                conn.commit()
        except Exception as exc:       # an upstream fixture that cannot load here (reference tables not modelled) is reported, not hidden
            conn.rollback()
            out[n] = f"NOT LOADED: {type(exc).__name__}: {str(exc).splitlines()[0][:100]}"
    conn.close()
    return out
