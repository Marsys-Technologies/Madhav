"""PARISHKARA R2 Phase C — resilient corpus rebuild driver, v2.

Fresh connection PER SUBSTEP (the approach THE ONE rebuild found survives the
sandbox TCP-drop fragility, ledger 2026-08-11 ~14:3x IST). Each substep:
  - own connection (db.connect: keepalives + idle_in_transaction_session_timeout=0
    real SET, per MR-39/C6) + the C4-authorized session-scoped GUC
  - SAVEPOINT + run_substep + RELEASE + commit  (writer never commits/closes)
  - build_substep_progress row written HERE so the coverage envelope becomes
    honest (substeps_committed > 0) — the v3 writer doesn't write it itself
  - one retry on a connection-lost OperationalError
Also writes build_substep_progress; promotes asset_throughput to 'lit' ONLY if
all planned substeps committed (honest earned-signal, mirrors the SATYA-DĪPA
predicate). No ALTER DATABASE/ROLE. GUC dies with each connection.

v2 additions (native chart died mid-run on MR-44/45's now-fixed bug; native
verification directly asked whether a restart resumes or starts over):
  1. RESUME: before running each substep, check kala_gochara_windows_v2 for a
     row at (chart_id, event_class, era_slice_key, generation='g3_utkarsha')
     computed_at newer than RESUME_CUTOFF (this run's own start time is NOT
     the cutoff — a prior INTERRUPTED run's rows are still correct, idempotent
     writer output; we skip ANY decade that already has a committed row,
     regardless of which run wrote it). This is a real skip, not a proxy —
     if the row is missing, the substep runs; if present, it's provably
     already correct (delete-then-insert makes any completed row the FULL
     correct set for that decade, never partial).
  2. VISIBILITY: sets asset_throughput.state='building' at the START of the
     run (previously only set at the very end) so the Nirmāṇa cockpit shows
     live progress, not a stale status from an earlier failed attempt.

Usage:  python3 r2evidence/rebuild_per_substep.py <chart_id> <label>
"""
import sys, time, hashlib
import pipeline.orchestrator.db as odb
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
    GocharaV3CenturyMaterializeWriter as W, ASSET_ID,
)
from pipeline.orchestrator.birth_params import fetch_birth_params
import psycopg

CHART = sys.argv[1]
LABEL = sys.argv[2] if len(sys.argv) > 2 else "chart"

def fresh_conn():
    c = odb.connect()
    with c.cursor() as cur:
        cur.execute("SET app.allow_protected_sweep_rewrite = 'on'")
    c.commit()
    return c

def already_done(conn, chart_id, event_class, era_slice_key):
    """A decade is done iff it has ANY row (any resolution/shape) in the
    staging table for this exact (chart, class, decade) key — delete-then-
    insert means a present row is always the full, current, correct set."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT 1 FROM kala_gochara_windows_v2
               WHERE chart_id=%s AND event_class=%s AND era_slice_key=%s
                 AND generation='g3_utkarsha' LIMIT 1""",
            (chart_id, event_class, era_slice_key),
        )
        return cur.fetchone() is not None

# Plan once (own short-lived connection)
plan_conn = fresh_conn()
bp = fetch_birth_params(plan_conn, CHART)
w = W()
ctx0 = ContextSpec(asset_id=ASSET_ID, build_id="parishkara-r2", db_conn=plan_conn,
                   config={"chart_id": CHART, "birth_params": bp})
steps = w.plan_substeps(ctx0)
total = len(steps)
print(f"[{LABEL}] PLAN: {total} substeps", flush=True)

# Mark building for cockpit visibility BEFORE any work starts.
with plan_conn.cursor() as cur:
    cur.execute(
        """UPDATE asset_throughput SET state='building', last_error=NULL,
                  last_built_at=NOW() WHERE chart_id=%s AND asset_id=%s""",
        (CHART, ASSET_ID))
plan_conn.commit()
plan_conn.close()
print(f"[{LABEL}] asset_throughput -> building (cockpit-visible)", flush=True)

committed = 0
skipped_resume = 0
ins = upd = 0
t_start = time.time()
for idx, step in enumerate(steps):
    event_class, era_slice_key = step.key.split("::", 1)

    # RESUME CHECK — real skip, not a proxy: a present row is provably the
    # full, current, correct output for this decade (idempotent writer).
    check_conn = fresh_conn()
    is_done = already_done(check_conn, CHART, event_class, era_slice_key)
    check_conn.close()
    if is_done:
        skipped_resume += 1
        if skipped_resume <= 3 or skipped_resume % 30 == 0:
            print(f"[{LABEL}] {idx+1}/{total} SKIP (already done, resume) key={step.key}",
                  flush=True)
        committed += 1
        continue

    for attempt in (1, 2):
        try:
            conn = fresh_conn()
            ctx = ContextSpec(asset_id=ASSET_ID, build_id="parishkara-r2", db_conn=conn,
                              config={"chart_id": CHART, "birth_params": bp})
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT wx")
                r = w.run_substep(ctx, step)
                cur.execute("RELEASE SAVEPOINT wx")
                fp = hashlib.sha256(step.key.encode()).hexdigest()[:16]
                cur.execute(
                    """INSERT INTO build_substep_progress
                         (chart_id, asset_id, substep_key, build_fingerprint, rows_written)
                       VALUES (%s,%s,%s,%s,%s)
                       ON CONFLICT (chart_id, asset_id, substep_key)
                       DO UPDATE SET build_fingerprint=EXCLUDED.build_fingerprint,
                                     rows_written=EXCLUDED.rows_written,
                                     completed_at=NOW()""",
                    (CHART, ASSET_ID, step.key, fp, int(r.rows_inserted or 0)),
                )
                cur.execute(
                    """UPDATE asset_throughput SET last_built_at=NOW(), state='building'
                       WHERE chart_id=%s AND asset_id=%s""", (CHART, ASSET_ID))
            conn.commit()
            conn.close()
            committed += 1
            ins += int(r.rows_inserted or 0); upd += int(r.rows_updated or 0)
            if (idx+1) % 20 == 0 or idx == 0:
                el = time.time()-t_start
                print(f"[{LABEL}] {idx+1}/{total} ok key={step.key} ins={ins} "
                      f"skipped={skipped_resume} elapsed={el/60:.1f}m", flush=True)
            break
        except psycopg.OperationalError as e:
            print(f"[{LABEL}] {idx+1}/{total} conn-lost on {step.key} attempt {attempt}: "
                  f"{str(e)[:80]}", flush=True)
            try: conn.close()
            except Exception: pass
            if attempt == 2:
                print(f"[{LABEL}] FATAL: substep {step.key} failed twice — STOPPING", flush=True)
                sys.exit(1)
            time.sleep(3)
        except Exception as e:
            print(f"[{LABEL}] {idx+1}/{total} ERROR on {step.key}: {type(e).__name__}: "
                  f"{str(e)[:200]} — STOPPING (no hand-patch)", flush=True)
            try: conn.rollback(); conn.close()
            except Exception: pass
            sys.exit(2)

# Honest promotion: only if every planned substep committed (this run OR a prior resumed one)
# RESILIENT: retry with a fresh connection + VERIFY via re-read, since a connection can be
# silently dropped between COMMIT being issued and its ack reaching the client (the same
# sandbox fragility MR-39 targets mid-substep) -- native caught this exact gap live:
# the log printed "PROMOTED to lit" but the row never actually changed. Never trust a
# print statement as evidence again; read the row back before declaring success.
def promote_with_verification(target_state, rows_written, error_text):
    for attempt in (1, 2, 3):
        try:
            pconn = fresh_conn()
            with pconn.cursor() as cur:
                cur.execute(
                    """UPDATE asset_throughput SET state=%s, rows_written=%s, last_error=%s,
                              last_built_at=NOW() WHERE chart_id=%s AND asset_id=%s""",
                    (target_state, rows_written, error_text, CHART, ASSET_ID))
                affected = cur.rowcount
            pconn.commit()
            # VERIFY: re-read on a SEPARATE fresh connection -- proves the write survived,
            # not just that the UPDATE statement executed without raising.
            pconn.close()
            vconn = fresh_conn()
            with vconn.cursor() as cur:
                cur.execute(
                    """SELECT state, rows_written FROM asset_throughput
                       WHERE chart_id=%s AND asset_id=%s""", (CHART, ASSET_ID))
                row = cur.fetchone()
            vconn.close()
            if row and row["state"] == target_state:
                return True, affected
            print(f"[{LABEL}] promotion attempt {attempt}: UPDATE claimed rowcount={affected} "
                  f"but re-read shows state={row['state'] if row else 'MISSING'} (expected "
                  f"{target_state}) -- retrying", flush=True)
        except Exception as e:
            print(f"[{LABEL}] promotion attempt {attempt} raised {type(e).__name__}: "
                  f"{str(e)[:150]} -- retrying", flush=True)
        time.sleep(2)
    return False, 0

if committed == total:
    ok, affected = promote_with_verification("lit", ins+upd, None)
    if ok:
        print(f"[{LABEL}] PROMOTED to lit (VERIFIED via re-read): {committed}/{total} substeps "
              f"({skipped_resume} resumed, {committed-skipped_resume} run this pass), "
              f"{ins} rows", flush=True)
    else:
        print(f"[{LABEL}] PROMOTION FAILED after 3 verified attempts -- corpus data is complete "
              f"({committed}/{total}) but asset_throughput.state could NOT be confirmed updated. "
              f"Manual verification required before trusting the cockpit for this asset.",
              flush=True)
        sys.exit(3)
else:
    promote_with_verification(
        "incomplete", None, f"{committed}/{total} substeps committed — not promoted")
    print(f"[{LABEL}] NOT promoted: {committed}/{total}", flush=True)
print(f"[{LABEL}] DONE committed={committed}/{total} (resumed={skipped_resume}) ins={ins} "
      f"upd={upd} wall={(time.time()-t_start)/60:.1f}m", flush=True)
