"""A5.3 / C36 — BUILD-TIMING harness for the ka_gochara_v5 orchestrated build.

NOT part of CI (no `test_` file name — run it explicitly, ONE narrow command, on a local
disposable server):

    python -m pytest tests/l3/gochara/perf_a53_build_timing.py -q -s

What it does, on a THROWAWAY database it creates and drops itself (the shared
disposable-DB guard `_disposable_db_guard.guarded_admin_connect` is the only way in —
a hostile admin DSN is a configuration ERROR, never a skip):

  * runs the writer's OWN orchestrated build — `plan_substeps` executed in order, one
    substep per transaction exactly like the orchestrator (`WriterBase.run` aggregates
    the same plan; we iterate it only so each substep is timed individually). A FAILING
    substep is timed, its error recorded (first line), and the plan CONTINUES — on the
    disposable stubbed-L1 world the verification substeps are EXPECTED to fail (the
    stub L1 is not a consistent candidate: no all-lord daśā cover can exist without
    overlapping rows — the same "the gate would refuse them; the measurement is of
    cost" discipline as perf_a53_seal_cost's replicated clones). Against a real L1
    export they pass;
  * records per-substep wall time, rows_inserted, notes and any error;
  * records per-table row counts of every public ka_gochara_*/kala_gochara_* table
    after the build;
  * records this process's peak RSS (getrusage ru_maxrss) and the Postgres backend's
    RSS before/after (via `ps` on pg_backend_pid, same method as perf_a53_seal_cost);
  * prints the whole measurement as JSON, and also writes it to
    $GOCHARA_BUILD_TIMING_JSON when that path is set.

When the pinned .se1 corpus is unavailable (conftest._PROBLEMS), the three Swiss
seams (knots / contacts / writer) are replaced by ONE deterministic stand-in
(a constant longitude per body, retflag=2 — flat splines, no crossings, so the
plan runs fast) and the input-vector verifier's
four Swiss-probing derivations (file census, backend/version, series probe,
absolute probe) are stood in from the stored vector's own values — every OTHER
independent derivation still really runs. The report's "swiss" field says
"stand-in" then and the substrate/solve timings are NOT solve-representative.
With the corpus present the whole build is real and "swiss" is "real".

It asserts NOTHING about speed and changes NO kernel code — it is a measuring
instrument only.

Pointing it at a read-only L1 export later (not today): restore the export onto a
LOCAL disposable server (a loopback DSN only — the guard refuses anything else),
then run with GOCHARA_A53_ADMIN_DSN=postgresql://…@localhost:<port>/postgres. The
harness still creates and drops its own a53t_bt_* database on that server and never
touches the export's own databases; the export simply makes the stubbed L1 tables
realistic. Never point GOCHARA_A53_ADMIN_DSN at a non-loopback host — the guard
refuses it by construction.
"""
from __future__ import annotations

import json
import os
import resource
import subprocess
import time

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod

from ._disposable_db_guard import UnsafeAdminDSN, check_admin_dsn
from .conftest import _PROBLEMS as SE1_PROBLEMS
from .test_a53_am5_writer import make_ephe
from .test_a53_inventory import CHART_ID, H0, H1, create_am5_database, drop_am5_database

GEN = writer_mod.GENERATION


def test_refuses_non_disposable_dsn():
    """The only connection path is the shared guard: remote and multi-host DSNs are refused outright."""
    with pytest.raises(UnsafeAdminDSN):
        check_admin_dsn("postgresql://u:p@db.prod.example.com:5432/postgres")
    with pytest.raises(UnsafeAdminDSN):
        check_admin_dsn("postgresql://u:p@localhost:5432,db.prod.example.com:5432/postgres")


def _backend_rss_mb(pid: int) -> float:
    out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return int(out or 0) / 1024


def test_measure_orchestrated_build_timing(monkeypatch, tmp_path):
    import psycopg

    admin, name, dsn = create_am5_database("bt")            # guard-enforced; skips NOT_RUN when unreachable
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        ephe = make_ephe(tmp_path, monkeypatch)
        swiss_mode = "real"
        if SE1_PROBLEMS:
            swiss_mode = "stand-in"     # no pinned corpus: deterministic drift, NOT solve-representative

            def _fake_calc(body, jd, ephe_path):
                return (float(sum(map(ord, body)) % 360), 2)   # constant: no crossings, fast flat splines

            monkeypatch.setattr("services.gochara_kernel.knots.calc_sidereal_lon", _fake_calc)
            monkeypatch.setattr("services.gochara_kernel.contacts.calc_sidereal_lon", _fake_calc)
            monkeypatch.setattr(writer_mod, "calc_sidereal_lon", _fake_calc)

            # the input-vector verifier's FOUR Swiss-probing derivations (file census, backend/version,
            # series probe, absolute probe) cannot run without the corpus — stand them in from the stored
            # vector's own values; EVERY other independent derivation (registry digest, L0, sky convention,
            # per-file sha256, library, platform, schema/policy) still really runs
            from services.gochara_kernel import input_vector_verifier as gk_ivv
            real_verify = gk_ivv.verify_inputs

            def _verify_with_probe_stand_ins(conn, stored, **kw):
                return real_verify(
                    conn, stored,
                    census_probe=lambda ephe, lo, hi: dict(stored["ephemeris"]["files"]),
                    backend_probe=lambda ephe: (stored["ephemeris"]["backend"], stored["ephemeris"]["swe_version"]),
                    series_probe=lambda ephe: stored["ephemeris"]["probe_digest"],
                    absolute_probe=lambda ephe: gk_ivv.ABSOLUTE_PROBE_SUN_LAHIRI_DEG,
                    **kw)

            monkeypatch.setattr(gk_ivv, "verify_inputs", _verify_with_probe_stand_ins)
        writer = writer_mod.GocharaV5Writer()
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="perf-build", db_conn=conn,
                          config={"chart_id": CHART_ID, "horizon": (H0, H1), "ephe_path": ephe},
                          dry_run=False)

        backend_pid = conn.execute("SELECT pg_backend_pid()").fetchone()[0]
        rss_before = _backend_rss_mb(backend_pid)

        plan = writer.plan_substeps(ctx)
        substeps = []
        t_all = time.perf_counter()
        for step in plan:
            t0 = time.perf_counter()
            error = None
            rows = None
            notes = ""
            try:
                with conn.transaction():                    # one substep = one transaction, like the orchestrator
                    result = writer.run_substep(ctx, SubStep(key=step.key, label=step.key))
                rows, notes = result.rows_inserted, result.notes
            except Exception as exc:  # noqa: BLE001 — a failing substep is TIMED and recorded, never hidden:
                error = f"{type(exc).__name__}: {exc}".splitlines()[0][:300]
            substeps.append({"key": step.key, "seconds": round(time.perf_counter() - t0, 6),
                             "rows_inserted": rows, "notes": notes, "error": error})
        total = time.perf_counter() - t_all

        tables = [r[0] for r in conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            " AND (tablename LIKE 'ka\\_gochara%' OR tablename LIKE 'kala\\_gochara%') ORDER BY 1").fetchall()]
        row_counts = {t: conn.execute(f'SELECT count(*) FROM public."{t}"').fetchone()[0] for t in tables}

        report = {
            "asset": writer_mod.ASSET_ID, "chart_id": CHART_ID, "generation": GEN,
            "build_id": "perf-build", "database": name, "swiss": swiss_mode,
            "substeps_planned": len(plan), "total_seconds": round(total, 3),
            "substeps_failed": sum(1 for s in substeps if s["error"]),
            "substeps": substeps, "row_counts": row_counts,
            "process_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "backend": {"pid": backend_pid, "rss_mb_before": rss_before, "rss_mb_after": _backend_rss_mb(backend_pid)},
        }
        out = os.environ.get("GOCHARA_BUILD_TIMING_JSON")
        if out:
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2)
        print("\nBUILD-TIMING " + json.dumps(
            {k: v for k, v in report.items() if k != "substeps"}, indent=2))
        slowest = sorted(substeps, key=lambda s: -s["seconds"])[:10]
        print("BUILD-TIMING slowest substeps: " + ", ".join(f"{s['key']}={s['seconds']:.3f}s" for s in slowest))
        assert len(substeps) == len(plan)                  # every planned substep ran and was timed
    finally:
        conn.close()
        drop_am5_database(admin, name)
