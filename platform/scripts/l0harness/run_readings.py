"""W-L0-7 readings runner — first-ever decorated-path execution rehearsal.

Executes the frozen 9-step sequence from
00_ARCHITECTURE/briefs/nirmana/L0_W_L0_7_PACKET_REPORT_v1_0.md (v1.5,
"Predicted movement") against the rehearsal fixture DB madhav_l0w7_fixture:

  (0) rebuild fixture (build_fixture.py) + state-B structural gate
  (1) BASELINE: R1 via decorated GaYogaWriter, then R3 via decorated
      BoLaksanaWriter (one primed bind_l2_exact_inputs per R3 run, F-W-L0-7-1);
      snapshot ga_yoga_firings / R2 / C0 / bodha_msr_signals
  (2) PERTURB: DELETE FROM brahma_yoga_catalog WHERE canonical_id='sunapha'
  (3) C0 read            (4) R2 stale read
  (5) R1 rerun (all 5 ayanamsha substeps)
  (6) R2 read            (7) R3 rebuild
  (8) verdict vs the frozen matrix
  (9) RESEED + REPLAY

Hard rules honored: real decorated path (dry_run=False) on a direct
data_plane_builder psycopg connection (session_user, never SET ROLE — 1035:578,
1036:941 require it); no consumer/writer/data-plane SQL edits; failures are
recorded as findings with verbatim error text, never routed around.

Run with a python that has psycopg 3, e.g.:
  /Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3 scripts/l0harness/run_readings.py
(cwd = platform/). Writes reading_verdicts.json next to this file.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import traceback
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLATFORM = HERE.parent.parent
SIDECAR = PLATFORM / "python-sidecar"
TSX = PLATFORM / "node_modules" / ".bin" / "tsx"

PGHOST = os.environ.get("L0H_PGHOST", "127.0.0.1")
PGPORT = os.environ.get("L0H_PGPORT", "55433")
FIXTURE_DB = os.environ.get("L0H_FIXTURE_DB", "madhav_l0w7_fixture")
SUPERUSER = os.environ.get("L0H_PGSUPERUSER", "Dev")
BUILDER_URL = f"postgres://data_plane_builder@{PGHOST}:{PGPORT}/{FIXTURE_DB}"
SUPER_URL = f"postgres://{SUPERUSER}@{PGHOST}:{PGPORT}/{FIXTURE_DB}"

CHART_ID = "f0000000-0000-4000-8000-000000000001"
SUNAPHA_AYANAMSHA = "surya_siddhanta_classical"
SUNAPHA_LINK_SET = [
    "a5d58ce9-5331-5db4-a803-41d9530e45fc",
    "cf36fd63-ba97-5ead-ad17-de9054fc051f",
]
SUNAPHA_CITATIONS = ["bphs:30", "saravali:38"]

# The decorator's provenance pins call asset_runner.get_writer_source_hash,
# which auto-discovers every writer module — the interpreter must resolve the
# sidecar package tree exactly as the orchestrator does.
sys.path.insert(0, str(SIDECAR))
os.environ["DATABASE_URL"] = BUILDER_URL  # pipeline/orchestrator/db.py:39-43

import psycopg  # noqa: E402
import psycopg.rows  # noqa: E402

VERDICTS_PATH = HERE / "reading_verdicts.json"

LOG: list[str] = []
FINDINGS: list[dict] = []
STATE: dict = {"steps": {}, "snapshots": {}, "verdicts": {}, "findings": FINDINGS}


def log(msg: str) -> None:
    line = f"[run_readings] {msg}"
    print(line, flush=True)
    LOG.append(line)


def finding(fid: str, step: str, summary: str, error_text: str | None = None,
            evidence: str | None = None) -> None:
    entry = {"id": fid, "step": step, "summary": summary}
    if error_text:
        entry["error_text"] = error_text
    if evidence:
        entry["evidence"] = evidence
    FINDINGS.append(entry)
    log(f"FINDING {fid} ({step}): {summary}")


def exc_text(exc: BaseException) -> str:
    tb = traceback.format_exc()
    return f"{type(exc).__name__}: {exc}\n--- traceback tail ---\n{tb[-1600:]}"


# ── connections ───────────────────────────────────────────────────────────────

def super_conn() -> psycopg.Connection:
    return psycopg.connect(SUPER_URL, autocommit=True,
                           row_factory=psycopg.rows.dict_row)


def builder_conn() -> psycopg.Connection:
    # Production-faithful session: the orchestrator's own connection factory
    # (keepalives, timeout GUCs, marsys.triggered_by). session_user is
    # data_plane_builder — 1035:578-580 / 1036:805-807 / 1036:941-943 require
    # exactly that; SET ROLE would not satisfy it (session_user is immutable).
    from pipeline.orchestrator.db import connect
    return connect()


# ── build lifecycle rows (data_plane_builder holds no INSERT grant on
#    build_runs/build_run_assets — probed 2026-09-26, recorded as a finding;
#    the harness inserts them as superuser exactly as
#    run_heavy_writer_standalone.py:121-141 does on its own connection) ────────

def lifecycle_start(run_id: str, asset_id: str) -> None:
    with super_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO build_runs
                 (id, chart_id, scope, scope_target, action, plan, state,
                  triggered_by, started_at, current_asset_id)
               VALUES (%s, %s, 'asset', %s, 'rebuild', %s::jsonb, 'running',
                       'l0harness/run_readings', NOW(), %s)""",
            (run_id, CHART_ID, asset_id,
             json.dumps({"entrypoint": "run_readings", "asset_ids": [asset_id]},
                        sort_keys=True),
             asset_id))
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state, started_at)
               VALUES (%s, %s, 0, 'building', NOW())""",
            (run_id, asset_id))


def lifecycle_end(run_id: str, asset_id: str, ok: bool, error: str | None = None) -> None:
    with super_conn() as conn, conn.cursor() as cur:
        if ok:
            cur.execute(
                """UPDATE build_run_assets SET state='complete', ended_at=NOW(), error=NULL
                   WHERE run_id=%s AND asset_id=%s""", (run_id, asset_id))
            cur.execute(
                """UPDATE build_runs SET state='completed', ended_at=NOW()
                   WHERE id=%s""", (run_id,))
        else:
            cur.execute(
                """UPDATE build_run_assets SET state='error', ended_at=NOW(),
                       error=%s WHERE run_id=%s AND asset_id=%s""",
                ((error or "")[:2000], run_id, asset_id))
            cur.execute(
                """UPDATE build_runs SET state='failed', ended_at=NOW()
                   WHERE id=%s""", (run_id,))


# ── serve reads (real TS handlers via read_serve.ts) ──────────────────────────

def serve(tool: str, args: dict) -> dict:
    env = dict(os.environ)
    env["DATABASE_URL"] = BUILDER_URL  # amjis_app holds no SELECT on
    # ga_yoga_firings in the production-probed grant set — serve runs as
    # data_plane_builder here; disclosed in REHEARSAL_NOTES.
    proc = subprocess.run(
        [str(TSX), "-C", "react-server", "scripts/l0harness/read_serve.ts",
         tool, json.dumps(args)],
        cwd=PLATFORM, env=env, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(
            f"read_serve {tool} exited {proc.returncode}: {proc.stderr[-1200:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def read_c0() -> dict:
    return serve("C0", {"yoga_name": "sunapha"})


def read_r2() -> dict:
    return serve("R2", {"chart_id": CHART_ID, "yoga_canonical_id": "sunapha",
                        "all": True})


# ── snapshots ─────────────────────────────────────────────────────────────────

VOLATILE_KEYS = {"id", "build_id", "created_at", "updated_at", "computed_at"}


def snap_firings() -> list[dict]:
    with super_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT to_jsonb(f) AS row FROM ga_yoga_firings f
               WHERE chart_id = %s
               ORDER BY yoga_canonical_id, ayanamsha_id, id""", (CHART_ID,))
        return [r["row"] for r in cur.fetchall()]


def snap_msr() -> list[dict]:
    with super_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT to_jsonb(s) AS row FROM bodha_msr_signals s
               WHERE chart_id = %s ORDER BY signal_type_id, signal_id""", (CHART_ID,))
        return [r["row"] for r in cur.fetchall()]


def stable_row(row: dict) -> str:
    return json.dumps({k: v for k, v in row.items() if k not in VOLATILE_KEYS},
                      sort_keys=True, default=str)


# ── R1: decorated GaYogaWriter ────────────────────────────────────────────────

def run_ga_yoga(label: str) -> dict:
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.ga_yoga import GaYogaWriter

    run_id = str(uuid.uuid4())
    log(f"R1[{label}]: build_runs lifecycle {run_id} (scope=asset, ga_yoga)")
    lifecycle_start(run_id, "ga_yoga")
    result: dict = {"run_id": run_id, "ok": False, "substeps": []}
    conn = builder_conn()
    try:
        ctx = ContextSpec(asset_id="ga_yoga", build_id=run_id, db_conn=conn,
                          config={"chart_id": CHART_ID})
        writer = GaYogaWriter()
        for step in writer.plan_substeps(ctx):
            conn.cursor().execute("SAVEPOINT writer_exec")
            try:
                res = writer.run_substep(ctx, step)  # decorated: open+writer+complete
                conn.cursor().execute("RELEASE SAVEPOINT writer_exec")
                conn.commit()
                result["substeps"].append(
                    {"key": step.key, "rows_inserted": int(res.rows_inserted)})
                log(f"R1[{label}] substep {step.key}: rows_inserted={res.rows_inserted}")
            except Exception as exc:
                conn.cursor().execute("ROLLBACK TO SAVEPOINT writer_exec")
                conn.rollback()
                result["error"] = exc_text(exc)
                result["failed_substep"] = step.key
                log(f"R1[{label}] substep {step.key} FAILED: "
                    f"{type(exc).__name__}: {exc}")
                lifecycle_end(run_id, "ga_yoga", False,
                              f"{type(exc).__name__}: {exc}")
                return result
        result["ok"] = True
        lifecycle_end(run_id, "ga_yoga", True)
        return result
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()


# ── R3: decorated BoLaksanaWriter (one primed bind per run, F-W-L0-7-1) ───────

def run_bo_laksana(label: str) -> dict:
    from bodha_writers.data_plane_contracts import _resolve_upstream_context
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bo_laksana import BoLaksanaWriter

    run_id = str(uuid.uuid4())
    log(f"R3[{label}]: build_runs lifecycle {run_id} (scope=asset, bo_laksana)")
    lifecycle_start(run_id, "bo_laksana")
    result: dict = {"run_id": run_id, "ok": False, "substeps": []}
    conn = builder_conn()
    try:
        # The whole run stays in ONE transaction: the bind receipt and pg_temp
        # shadows are ON COMMIT DROP (1036:905-913), so a mid-run commit would
        # destroy them. Prime bind first (F-W-L0-7-1: the decorator calls
        # open-before-bind but open requires the receipt — 1036:984-996).
        vector, _calc = _resolve_upstream_context(
            conn, chart_id=CHART_ID, asset_id="bo_laksana",
            partition_key="aya_lahiri_chitrapaksha")
        with conn.cursor() as cur:
            cur.execute(
                "SELECT public.bind_l2_exact_inputs(%s::uuid, %s::jsonb)",
                (CHART_ID, json.dumps(vector, sort_keys=True)))
        log(f"R3[{label}]: bind primed ({len(vector)}-asset vector)")
        result["vector_assets"] = [v["asset_id"] for v in vector]

        ctx = ContextSpec(asset_id="bo_laksana", build_id=run_id, db_conn=conn,
                          config={"chart_id": CHART_ID})
        writer = BoLaksanaWriter()
        for step in writer.plan_substeps(ctx):
            conn.cursor().execute("SAVEPOINT writer_exec")
            try:
                res = writer.run_substep(ctx, step)
                conn.cursor().execute("RELEASE SAVEPOINT writer_exec")
                result["substeps"].append(
                    {"key": step.key, "rows_inserted": int(res.rows_inserted)})
                log(f"R3[{label}] substep {step.key}: rows_inserted={res.rows_inserted}")
            except Exception as exc:
                conn.cursor().execute("ROLLBACK TO SAVEPOINT writer_exec")
                conn.rollback()
                result["error"] = exc_text(exc)
                result["failed_substep"] = step.key
                log(f"R3[{label}] substep {step.key} FAILED: "
                    f"{type(exc).__name__}: {exc}")
                lifecycle_end(run_id, "bo_laksana", False,
                              f"{type(exc).__name__}: {exc}")
                return result
        conn.commit()
        result["ok"] = True
        lifecycle_end(run_id, "bo_laksana", True)
        return result
    except Exception as exc:
        # Failure before the substep loop (upstream resolution or bind prime).
        conn.rollback()
        result["error"] = exc_text(exc)
        log(f"R3[{label}] pre-flight FAILED: {type(exc).__name__}: {exc}")
        lifecycle_end(run_id, "bo_laksana", False, f"{type(exc).__name__}: {exc}")
        return result
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()


# ── step 0: rebuild + state-B gate ────────────────────────────────────────────

def step0_rebuild_and_gate() -> None:
    python3 = shutil.which("python3") or "/usr/bin/python3"
    log("step 0: rebuilding fixture (build_fixture.py)")
    proc = subprocess.run([python3, "scripts/l0harness/build_fixture.py"],
                          cwd=PLATFORM, capture_output=True, text=True,
                          timeout=1800)
    tail = proc.stdout.strip().splitlines()[-3:] if proc.stdout else []
    for line in tail:
        log(f"  build_fixture: {line}")
    if proc.returncode != 0 or "BUILD GREEN" not in proc.stdout:
        print(proc.stdout[-3000:])
        print(proc.stderr[-3000:], file=sys.stderr)
        raise SystemExit("step 0 FAILED: fixture rebuild not green")
    # State-B structural gate (report v1.5 step 0): sutravali 3002/7, sunapha
    # present, exact post-1123 link set, seeded firing present.
    with super_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) AS n, count(*) FILTER (WHERE yoga_canonical_id IS NOT NULL) AS linked FROM sutravali_rules")
        row = cur.fetchone()
        assert (row["n"], row["linked"]) == (3002, 7), f"sutravali gate: {row}"
        cur.execute("SELECT count(*) AS n FROM brahma_yoga_catalog WHERE canonical_id='sunapha'")
        assert cur.fetchone()["n"] == 1, "sunapha catalog row absent in state B"
        cur.execute(
            "SELECT string_agg(rule_id::text, ',' ORDER BY rule_id::text) AS s "
            "FROM sutravali_rules WHERE yoga_canonical_id='sunapha'")
        assert cur.fetchone()["s"] == ",".join(SUNAPHA_LINK_SET), "sunapha link set drifted"
        cur.execute(
            "SELECT count(*) AS n FROM ga_yoga_firings WHERE chart_id=%s "
            "AND yoga_canonical_id='sunapha' AND ayanamsha_id=%s AND fired",
            (CHART_ID, SUNAPHA_AYANAMSHA))
        assert cur.fetchone()["n"] == 1, "seeded sunapha firing absent"
        cur.execute("SELECT count(*) AS n FROM l1_data_plane_generation_heads")
        heads = cur.fetchone()["n"]
    log(f"step 0: state-B gate green (sutravali 3002/7, sunapha present, "
        f"link set exact, seeded firing present, {heads} L1 heads)")
    STATE["steps"]["0"] = {"ok": True, "l1_heads": heads}


# ── verdict evaluation ────────────────────────────────────────────────────────

def sunapha_r2_row(read: dict) -> dict | None:
    for row in (read.get("content") or {}).get("rows") or []:
        if row.get("yoga_canonical_id") == "sunapha":
            return row
    return None


def evaluate_verdicts() -> None:
    v: dict = {}
    s = STATE["snapshots"]

    # V-C0-S3: sunapha absent from query_yoga_catalog after perturbation.
    c0 = s["c0_step3"]
    present = [r for r in (c0.get("content") or {}).get("rows") or []
               if r.get("canonical_id") == "sunapha"]
    v["V-C0-S3"] = {
        "predicted": "sunapha absent from query_yoga_catalog output",
        "measured": f"total_matching={ (c0.get('content') or {}).get('total_matching') }, "
                    f"sunapha rows={len(present)}",
        "verdict": "PASS" if not present else "FAIL",
    }

    # V-R2-S4: stale window — row PRESENT, catalog_classical_citations -> NULL.
    row = sunapha_r2_row(s["r2_step4"])
    if row is None:
        verdict, measured = "FAIL", "sunapha firing row ABSENT in stale window (must not move)"
    else:
        cit = row.get("catalog_classical_citations")
        verdict = "PASS" if cit is None else "FAIL"
        measured = (f"row present (id={row.get('id')}, ayanamsha={row.get('ayanamsha_id')}), "
                    f"catalog_classical_citations={'NULL' if cit is None else json.dumps(cit)}")
    v["V-R2-S4"] = {
        "predicted": "sunapha firing row STILL PRESENT; catalog_classical_citations -> NULL",
        "measured": measured, "verdict": verdict,
    }

    # V-R1-S5: firings lose exactly (chart, surya_siddhanta_classical, sunapha);
    # every other row byte-identical (modulo volatile id/build_id/timestamps).
    r1 = STATE["steps"].get("5_r1", {})
    if not r1.get("ok"):
        probe = STATE["steps"].get("5_r1_probe", {})
        probe_note = ""
        if probe:
            if probe.get("ok"):
                probe_note = ("; grant-workaround probe R1 COMPLETED "
                              f"(substeps={json.dumps(probe['substeps'])})")
            else:
                probe_note = ("; grant-workaround probe R1 also failed: "
                              f"{probe.get('error', '').splitlines()[0]}")
        v["V-R1-S5"] = {
            "predicted": "firings lose exactly the sunapha/surya_siddhanta row; others byte-identical",
            "measured": f"R1 rerun did not complete: {r1.get('error', 'not run').splitlines()[0]}{probe_note}",
            "verdict": "UNMEASURED",
        }
    else:
        base = {stable_row(r) for r in s["firings_baseline"]}
        post = {stable_row(r) for r in s["firings_step5"]}
        removed = base - post
        added = post - base
        sunapha_key = ("sunapha", SUNAPHA_AYANAMSHA)
        removed_ids = {(json.loads(r)["yoga_canonical_id"], json.loads(r)["ayanamsha_id"])
                       for r in removed}
        ok = (not added) and removed_ids == {sunapha_key}
        v["V-R1-S5"] = {
            "predicted": "lose exactly (chart, surya_siddhanta_classical, sunapha); others byte-identical",
            "measured": f"removed={sorted(removed_ids)}, added_rows={len(added)}",
            "verdict": "PASS" if ok else "FAIL",
        }

    # V-R2-S6: sunapha row absent after the R1 rerun.
    row = sunapha_r2_row(s["r2_step6"])
    if not r1.get("ok"):
        v["V-R2-S6"] = {
            "predicted": "sunapha firing row absent entirely",
            "measured": (f"premise broken (R1 rerun failed); actual served state: "
                         f"row {'PRESENT' if row else 'ABSENT'}"),
            "verdict": "UNMEASURED",
        }
    else:
        v["V-R2-S6"] = {
            "predicted": "sunapha firing row absent entirely",
            "measured": f"row {'ABSENT' if row is None else 'PRESENT'}",
            "verdict": "PASS" if row is None else "FAIL",
        }

    # V-R3-S7: sunapha facts' classical bridge movement.
    r3 = STATE["steps"].get("7_r3", {})
    if not r3.get("ok"):
        v["V-R3-S7"] = {
            "predicted": ("catalog_ids ['sunapha']->[]; rule_ids {a5d58ce9…, cf36fd63…}->[]; "
                          "citations ['bphs:30','saravali:38'] unchanged; "
                          "classical_sources_jsonb NOT NULL; corroboration stays 2"),
            "measured": f"R3 rebuild did not complete: {r3.get('error', 'not run').splitlines()[0]}",
            "verdict": "UNMEASURED",
        }
    else:
        signals = [r for r in s["msr_step7"]
                   if "sunapha" in json.dumps(r.get("configuration_jsonb") or {})
                   or "sunapha" in str(r.get("signal_type_id") or "")]
        checks = []
        for sig in signals:
            cs = sig.get("classical_sources_jsonb") or {}
            checks.append({
                "signal_type_id": sig.get("signal_type_id"),
                "catalog_ids": cs.get("catalog_ids"),
                "rule_ids": cs.get("rule_ids"),
                "citations": cs.get("citations"),
                "corroboration": sig.get("source_corroboration_count_by_text"),
            })
        ok = bool(checks) and all(
            c["catalog_ids"] == [] and c["rule_ids"] == []
            and sorted(c["citations"] or []) == SUNAPHA_CITATIONS
            and c["corroboration"] == 2 for c in checks)
        v["V-R3-S7"] = {
            "predicted": ("catalog_ids ['sunapha']->[]; rule_ids {a5d58ce9…, cf36fd63…}->[]; "
                          "citations unchanged; NOT NULL; corroboration 2"),
            "measured": json.dumps(checks, default=str),
            "verdict": "PASS" if ok else "FAIL",
        }

    STATE["verdicts"] = v


# ── auxiliary probe: 1036 pg_temp shadow ACL (non-verdict) ───────────────────

def probe_shadow_acl() -> None:
    """Re-measure the 1036 shadow-ACL defect through the real bind path.

    bind_l2_exact_inputs only validates that every vector element matches a
    head (1036:813-828) — it does not require closure completeness — so the
    11 synthesized heads give a valid prime vector even with ga_yoga absent.
    The bind builds pg_temp shadows owned by data_plane_l2_owner (SECURITY
    DEFINER); the writer role then resolves `chart_facts` to the shadow first
    (pg_temp precedes public in name resolution) and has no SELECT on it.
    """
    with builder_conn() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT jsonb_agg(jsonb_build_object(
                         'layer','L1','asset_id', h.asset_id,
                         'generation_id', h.current_generation_id,
                         'semantic_output_digest', g.semantic_output_digest)
                         ORDER BY h.asset_id) AS vector
                       FROM l1_data_plane_generation_heads h
                       JOIN l1_data_plane_generations g
                         ON g.chart_id=h.chart_id AND g.asset_id=h.asset_id
                        AND g.generation_id=h.current_generation_id
                      WHERE h.chart_id=%s::uuid AND g.status='complete'""",
                    (CHART_ID,))
                vector = cur.fetchone()["vector"]
                cur.execute("SELECT public.bind_l2_exact_inputs(%s::uuid, %s::jsonb)",
                            (CHART_ID, json.dumps(vector)))
                cur.execute("SELECT count(*) AS n FROM chart_facts")
                n = cur.fetchone()["n"]
            finding("F-W-L0-7-7", "probe",
                    "1036 shadow ACL did NOT reproduce: data_plane_builder read "
                    f"{n} rows from the pg_temp chart_facts shadow",
                    evidence="probe_shadow_acl: bind with 11-head vector, then SELECT count(*) FROM chart_facts")
        except Exception as exc:
            finding("F-W-L0-7-7", "probe",
                    "1036 pg_temp bind shadows are unreadable by the writer role: "
                    "bind_l2_exact_inputs (SECURITY DEFINER, owner data_plane_l2_owner) "
                    "creates the chart_facts shadow with relacl NULL; pg_temp precedes "
                    "public in name resolution, so the decorated bo_laksana run's "
                    "unqualified chart_facts reads land on a shadow it cannot SELECT",
                    error_text=f"{type(exc).__name__}: {exc}",
                    evidence="probe_shadow_acl: bind_l2_exact_inputs with the 11-head "
                             "vector succeeds, then SELECT count(*) FROM chart_facts "
                             "as session_user=data_plane_builder raises")
        finally:
            conn.rollback()


# ── auxiliary probe: open_l1 build_runs grant workaround (non-verdict) ───────

def probe_grant_workaround(label: str) -> dict:
    """Disclosed harness-side probe for F-W-L0-7-9 → F-W-L0-7-5 measurement.

    open_l1_data_plane_generation's build_runs/build_run_assets existence
    check (1035:599-611) executes as the function owner data_plane_l1_owner
    (SECURITY DEFINER), which holds no SELECT grant on either table (grant
    probe 2026-09-26: only amjis_app has any privilege on them). The main R1
    path therefore dies inside open_l1 with `permission denied for table
    build_runs` before the writer body — which masks the downstream failure
    the packet predicts (F-W-L0-7-5, undeclared empty output). To measure that
    downstream failure honestly, this probe temporarily grants SELECT to the
    owner role as superuser, reruns R1, then revokes — mirroring the fixture
    brief's "solve surprises in the builder (roles/ordering), never edit
    migrations" doctrine. No migration/consumer/writer SQL is touched and the
    grant is reverted in the same probe.
    """
    with super_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "GRANT SELECT ON build_runs, build_run_assets TO data_plane_l1_owner")
    log(f"probe[{label}]: GRANT SELECT ON build_runs, build_run_assets TO "
        f"data_plane_l1_owner (temporary, disclosed)")
    try:
        return run_ga_yoga(f"probe-grant-workaround/{label}")
    finally:
        with super_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "REVOKE SELECT ON build_runs, build_run_assets FROM data_plane_l1_owner")
        log(f"probe[{label}]: workaround grant REVOKED")


# ── main sequence ─────────────────────────────────────────────────────────────

def main() -> None:
    log("═══ W-L0-7 readings runner — decorated-path rehearsal ═══")

    step0_rebuild_and_gate()

    # (1) BASELINE
    log("── step 1: BASELINE (R1 then R3, snapshots)")
    r1_base = run_ga_yoga("baseline")
    STATE["steps"]["1_r1"] = r1_base
    if not r1_base["ok"]:
        finding("F-W-L0-7-9", "1/R1-baseline",
                "open_l1_data_plane_generation (SECURITY DEFINER, owner "
                "data_plane_l1_owner) checks build_runs/build_run_assets "
                "existence (1035:599-611) but the owner role holds no SELECT "
                "grant on either table (grant probe 2026-09-26: only amjis_app "
                "holds any privilege on them) — the decorated R1 dies inside "
                "open_l1 before the writer body. open_l2_data_plane_generation "
                "carries the same check (1036:951-963) under "
                "data_plane_l2_owner with the same missing grant; not "
                "measurable here because R3 fails earlier at upstream "
                "resolution (F-W-L0-7-8)",
                error_text=r1_base.get("error"),
                evidence="1035:599-611 (PL/pgSQL line 18: build_runs/"
                         "build_run_assets existence check); grant probe "
                         "(information_schema.role_table_grants): no "
                         "data_plane_l1_owner priv on either table")
        log("step 1 probe: temporary GRANT SELECT on build_runs to "
            "data_plane_l1_owner (disclosed; revoked after) to measure the "
            "downstream failure the packet predicts")
        r1_probe = probe_grant_workaround("baseline")
        STATE["steps"]["1_r1_probe"] = r1_probe
        if not r1_probe["ok"]:
            finding("F-W-L0-7-5", "1/R1-baseline (grant-workaround probe)",
                    "ga_yoga writer plans 5 ayanamsha substeps but the fixture "
                    "seeds chart_facts for surya_siddhanta_classical only; the "
                    "first substep (ayanamsha_lahiri_chitrapaksha) finds 0 "
                    "facts, writes 0 rows, and "
                    "complete_l1_data_plane_partition rejects the undeclared "
                    "empty partition (asset_registry.target_floor=63 ≠ 0). "
                    "Measured via the disclosed grant workaround because "
                    "F-W-L0-7-9 otherwise masks it",
                    error_text=r1_probe.get("error"),
                    evidence="ga_yoga.py:45-52 (5-substep plan); "
                             "ga_yoga_writer.py:147-156 + :2822-2828 (no facts "
                             "→ return 0); 1035:1385-1389 (undeclared empty "
                             "output); asset_registry target_floor probe")
        else:
            finding("F-W-L0-7-5", "1/R1-baseline (grant-workaround probe)",
                    "PREDICTION WRONG: with the open_l1 grant workaround the "
                    "decorated R1 COMPLETED against this fixture — the "
                    "predicted undeclared-empty-output rejection did not fire",
                    evidence=f"substeps={json.dumps(r1_probe['substeps'])}")
    r3_base = run_bo_laksana("baseline")
    STATE["steps"]["1_r3"] = r3_base
    if not r3_base["ok"]:
        finding("F-W-L0-7-8", "1/R3-baseline",
                "bo_laksana cannot resolve its upstream vector: ga_yoga is in its "
                "transitive L1 closure but has no generation head (R1 baseline "
                "failed), so _resolve_upstream_context raises before bind/open",
                error_text=r3_base.get("error"),
                evidence="bodha_writers/data_plane_contracts.py:262-266 "
                         "(missing completed selected L1 dependencies)")
    STATE["snapshots"]["firings_baseline"] = snap_firings()
    STATE["snapshots"]["msr_baseline"] = snap_msr()
    STATE["snapshots"]["c0_baseline"] = read_c0()
    STATE["snapshots"]["r2_baseline"] = read_r2()
    log(f"step 1: baseline snapshots — firings={len(STATE['snapshots']['firings_baseline'])}, "
        f"msr={len(STATE['snapshots']['msr_baseline'])}, "
        f"C0 total={STATE['snapshots']['c0_baseline']['content'].get('total_matching')}, "
        f"R2 total={STATE['snapshots']['r2_baseline']['content'].get('total_matching')}")

    # (2) PERTURB
    log("── step 2: PERTURB — DELETE sunapha catalog row (as superuser, per brief)")
    with super_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT to_jsonb(c)::text AS row FROM brahma_yoga_catalog c "
                    "WHERE canonical_id='sunapha'")
        doomed = cur.fetchone()["row"]
        STATE["snapshots"]["sunapha_catalog_row"] = json.loads(doomed)
        cur.execute("DELETE FROM brahma_yoga_catalog WHERE canonical_id='sunapha'")
        assert cur.rowcount == 1, f"perturb rowcount={cur.rowcount}, expected 1"
    log("step 2: sunapha catalog row deleted (rowcount=1); pre-image captured")

    # (3) C0 read
    log("── step 3: C0 read (query_yoga_catalog)")
    STATE["snapshots"]["c0_step3"] = read_c0()
    log(f"step 3: C0 total_matching="
        f"{STATE['snapshots']['c0_step3']['content'].get('total_matching')}")

    # (4) R2 stale read
    log("── step 4: R2 stale read (get_yoga_firings, no writer rerun yet)")
    STATE["snapshots"]["r2_step4"] = read_r2()
    row = sunapha_r2_row(STATE["snapshots"]["r2_step4"])
    log(f"step 4: R2 sunapha row={'PRESENT' if row else 'ABSENT'}, "
        f"catalog_classical_citations="
        f"{'NULL' if row and row.get('catalog_classical_citations') is None else 'set'}")

    # (5) R1 rerun
    log("── step 5: R1 rerun (all 5 ayanamsha substeps, perturbed catalog)")
    r1_post = run_ga_yoga("post-perturb")
    STATE["steps"]["5_r1"] = r1_post
    STATE["snapshots"]["firings_step5"] = snap_firings()
    if not r1_post["ok"]:
        log(f"step 5: R1 rerun failed at {r1_post.get('failed_substep')} — "
            f"recorded; downstream verdicts conditional")
        log("step 5 probe: grant-workaround rerun to check whether the "
            "perturbed catalog changes the R1 failure mode")
        r1_probe5 = probe_grant_workaround("post-perturb")
        STATE["steps"]["5_r1_probe"] = r1_probe5
        STATE["snapshots"]["firings_step5_probe"] = snap_firings()
        if r1_probe5["ok"]:
            log("step 5 probe: R1 COMPLETED under workaround — firings moved; "
                "step-6 read already taken, so V-R2-S6 premise note applies")

    # (6) R2 read
    log("── step 6: R2 read (post-rerun)")
    STATE["snapshots"]["r2_step6"] = read_r2()
    row = sunapha_r2_row(STATE["snapshots"]["r2_step6"])
    log(f"step 6: R2 sunapha row={'PRESENT' if row else 'ABSENT'}")

    # (7) R3 rebuild
    log("── step 7: R3 rebuild (bind prime with current vector)")
    r3_post = run_bo_laksana("post-perturb")
    STATE["steps"]["7_r3"] = r3_post
    STATE["snapshots"]["msr_step7"] = snap_msr()

    # auxiliary non-verdict probe: 1036 shadow ACL through the real bind path
    log("── probe: 1036 pg_temp shadow ACL (auxiliary, non-verdict)")
    probe_shadow_acl()

    # (8) VERDICT
    log("── step 8: verdict vs frozen matrix")
    evaluate_verdicts()

    # (9) RESEED + REPLAY
    log("── step 9: RESEED sunapha catalog row + REPLAY reads")
    with super_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO brahma_yoga_catalog "
            "SELECT * FROM jsonb_populate_record(NULL::brahma_yoga_catalog, %s::jsonb)",
            (json.dumps(STATE["snapshots"]["sunapha_catalog_row"]),))
        assert cur.rowcount == 1
        cur.execute("SELECT count(*) AS n FROM brahma_yoga_catalog WHERE canonical_id='sunapha'")
        assert cur.fetchone()["n"] == 1
        cur.execute(
            "SELECT string_agg(rule_id::text, ',' ORDER BY rule_id::text) AS s "
            "FROM sutravali_rules WHERE yoga_canonical_id='sunapha'")
        assert cur.fetchone()["s"] == ",".join(SUNAPHA_LINK_SET)
    c0_replay = read_c0()
    r2_replay = read_r2()
    replay_row = sunapha_r2_row(r2_replay)
    STATE["steps"]["9_reseed_replay"] = {
        "ok": True,
        "c0_total_matching": c0_replay["content"].get("total_matching"),
        "r2_row_present": replay_row is not None,
        "r2_catalog_citations_restored": bool(
            replay_row and replay_row.get("catalog_classical_citations")),
    }
    log(f"step 9: reseeded; replay C0 total={c0_replay['content'].get('total_matching')}, "
        f"R2 citations restored={STATE['steps']['9_reseed_replay']['r2_catalog_citations_restored']}")

    # ── report ────────────────────────────────────────────────────────────
    print("\n═══ VERDICT TABLE (frozen matrix vs measured) ═══")
    for vid, entry in STATE["verdicts"].items():
        print(f"{vid}: {entry['verdict']}")
        print(f"  predicted: {entry['predicted']}")
        print(f"  measured:  {entry['measured']}")

    print("\n═══ FINDINGS ═══")
    for f in FINDINGS:
        print(f"{f['id']} ({f['step']}): {f['summary']}")
        if f.get("error_text"):
            print(f"  error: {f['error_text'].splitlines()[0]}")
        if f.get("evidence"):
            print(f"  evidence: {f['evidence']}")

    VERDICTS_PATH.write_text(json.dumps(STATE, indent=2, default=str))
    log(f"reading_verdicts.json written ({VERDICTS_PATH})")


if __name__ == "__main__":
    main()
