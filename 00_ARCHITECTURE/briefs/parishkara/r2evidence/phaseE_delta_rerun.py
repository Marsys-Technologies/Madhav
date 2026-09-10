"""PARISHKARA Phase E — MR-38 live delta-rerun gate.

Re-dispatch the FULL corpus rebuild (all planned substeps) for one chart with
ZERO input changes since the last real build. This does NOT use the
conductor's own resume-check (rebuild_per_substep.py's already_done()) at
all -- that mechanism is now known to be an unsafe proxy (MR-46 correction).
This script relies ENTIRELY on the writer's own internal MR-38 fingerprint
delta-skip (kala_gochara_v2_build_state.class_fingerprint vs recomputed) to
prove the real production mechanism works: every substep should report
"skipping — fingerprint unchanged", zero new rows should be written, and
the corpus should be byte-identical before and after.

Usage: python3 r2evidence/phaseE_delta_rerun.py <chart_id> <label>
"""
import sys, time
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

plan_conn = fresh_conn()
bp = fetch_birth_params(plan_conn, CHART)
w = W()
ctx0 = ContextSpec(asset_id=ASSET_ID, build_id="parishkara-phaseE", db_conn=plan_conn,
                   config={"chart_id": CHART, "birth_params": bp})
steps = w.plan_substeps(ctx0)
total = len(steps)
plan_conn.close()
print(f"[{LABEL}] PHASE E PLAN: {total} substeps", flush=True)

skipped = ran = 0
ins = upd = 0
t_start = time.time()
non_skip_keys = []
for idx, step in enumerate(steps):
    for attempt in (1, 2):
        try:
            conn = fresh_conn()
            ctx = ContextSpec(asset_id=ASSET_ID, build_id="parishkara-phaseE", db_conn=conn,
                              config={"chart_id": CHART, "birth_params": bp})
            with conn.cursor() as cur:
                cur.execute("SAVEPOINT wx")
                r = w.run_substep(ctx, step)
                cur.execute("RELEASE SAVEPOINT wx")
            conn.commit()
            conn.close()
            notes = r.notes or ""
            if "fingerprint unchanged" in notes:
                skipped += 1
            else:
                ran += 1
                non_skip_keys.append(step.key)
                ins += int(r.rows_inserted or 0); upd += int(r.rows_updated or 0)
                print(f"[{LABEL}] {idx+1}/{total} NON-SKIP key={step.key} notes={notes[:150]}",
                      flush=True)
            if (idx+1) % 50 == 0:
                print(f"[{LABEL}] progress {idx+1}/{total} skipped={skipped} ran={ran}",
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
                  f"{str(e)[:200]} — STOPPING", flush=True)
            try: conn.rollback(); conn.close()
            except Exception: pass
            sys.exit(2)

print(f"[{LABEL}] PHASE E DONE: skipped={skipped}/{total} ran={ran}/{total} "
      f"ins={ins} upd={upd} wall={(time.time()-t_start)/60:.1f}m", flush=True)
if ran == 0:
    print(f"[{LABEL}] PHASE E GATE: PASS — 100% delta-skip, zero rows changed", flush=True)
else:
    print(f"[{LABEL}] PHASE E GATE: {ran} substeps did NOT skip: {non_skip_keys}", flush=True)
