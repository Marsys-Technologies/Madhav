"""PARISHKARA Phase D remediation — force-rebuild the 6 classes whose decades
were falsely resume-skipped by rebuild_per_substep.py's already_done() check.

ROOT CAUSE (found during Phase D evidence-pack investigation, 2026-08-12):
already_done() treated the mere PRESENCE of a row at (chart, class, decade) as
proof the decade was already rebuilt by the CURRENT writer. That's true only
when the existing row was itself written by the current engine — it is FALSE
when a pre-R8.8/pre-hierarchy row (peak_basis='gochara_lambda_v3', the
RETIRED bare literal per this writer's own module docstring) already occupies
that key from an earlier build era. Six classes hit this on BOTH charts:
career_advancement, chronic_onset, illness_acute, major_gain, marriage,
surgery — confirmed via direct SQL: 100% (or, for career_advancement, half)
of their rows still carry the retired literal and predate the real Aug-11
20:3x-21:3x UTC rebuild window by ~12 hours, with ZERO build_substep_progress
fingerprint rows to back them.

This script bypasses the resume check entirely for exactly these 6 classes
and force-runs every one of their planned substeps for both charts, so
delete-then-insert (§N.3) genuinely replaces the stale rows with current-
engine output. Uses the same fresh-connection-per-substep + verified-
promotion discipline as rebuild_per_substep.py (that discipline is sound;
only the resume proxy was unsafe).

Usage: python3 r2evidence/rebuild_stale_classes.py <chart_id> <label>
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

STALE_CLASSES = {
    "career_advancement", "chronic_onset", "illness_acute",
    "major_gain", "marriage", "surgery",
}

def fresh_conn():
    c = odb.connect()
    with c.cursor() as cur:
        cur.execute("SET app.allow_protected_sweep_rewrite = 'on'")
    c.commit()
    return c

plan_conn = fresh_conn()
bp = fetch_birth_params(plan_conn, CHART)
w = W()
ctx0 = ContextSpec(asset_id=ASSET_ID, build_id="parishkara-r2-stale-fix", db_conn=plan_conn,
                   config={"chart_id": CHART, "birth_params": bp})
all_steps = w.plan_substeps(ctx0)
steps = [s for s in all_steps if s.key.split("::", 1)[0] in STALE_CLASSES]
plan_conn.close()
total = len(steps)
print(f"[{LABEL}] STALE-FIX PLAN: {total} substeps across {len(STALE_CLASSES)} classes "
      f"(out of {len(all_steps)} total planned)", flush=True)

committed = 0
ins = upd = 0
t_start = time.time()
for idx, step in enumerate(steps):
    for attempt in (1, 2):
        try:
            conn = fresh_conn()
            ctx = ContextSpec(asset_id=ASSET_ID, build_id="parishkara-r2-stale-fix", db_conn=conn,
                              config={"chart_id": CHART, "birth_params": bp})
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT wx")
                r = w.run_substep(ctx, step)
                cur.execute("RELEASE SAVEPOINT wx")
                fp = hashlib.sha256((step.key + ":stale-fix").encode()).hexdigest()[:16]
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
            conn.commit()
            conn.close()
            committed += 1
            ins += int(r.rows_inserted or 0); upd += int(r.rows_updated or 0)
            print(f"[{LABEL}] {idx+1}/{total} ok key={step.key} notes={(r.notes or '')[:100]}",
                  flush=True)
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

print(f"[{LABEL}] DONE committed={committed}/{total} ins={ins} upd={upd} "
      f"wall={(time.time()-t_start)/60:.1f}m", flush=True)
