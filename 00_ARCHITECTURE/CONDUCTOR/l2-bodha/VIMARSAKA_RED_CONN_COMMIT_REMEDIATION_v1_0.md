# Vimarśaka RED — `ctx.db_conn.commit()` FROZEN-contract violation (remediation brief)

**Paste this entire file as the prompt in Claude Code (Antigravity). Targeted remediation against the L2 Bodha seal
branch `feature/l2-bodha` (PR #302) BEFORE it merges. This is a Vimarśaka RED finding from an independent audit of
the merged code — NOT a re-build. Scope is contained: remove the writer-level commits/rollbacks that violate the
FROZEN orchestrator contract, re-run the affected assets, confirm the data still lands.**

---

## THE FINDING (independent audit of commit `e70fe83c`, 2026-06-20)
The FROZEN orchestrator contract (`platform/python-sidecar/pipeline/orchestrator/writers/__init__.py` §lines 94–97,
and the runner `asset_runner.py` line 217) is explicit: **a writer MUST NOT call `ctx.db_conn.commit()` /
`.rollback()` / `.close()` — the orchestrator owns the transaction + savepoint lifecycle and commits once per
sub-step.** Six of the ten bo_* writers VIOLATE this — they call `conn.commit()` (and some `conn.rollback()`) where
`conn = ctx.db_conn`. Confirmed: in every case `conn` IS `ctx.db_conn` (not a separate connection).

**Why it matters:** the orchestrator commits once per sub-step as its savepoint boundary. A writer that ALSO commits
mid-stream breaks savepoint isolation — on a FAILED row/sub-step or a rebuild, the orchestrator can no longer cleanly
roll back to its savepoint because the writer already committed part of the work. It passes on a clean run (which is
why B6 went 35/35 and the data landed correctly — 66,738 rows, traps clean) but the error-recovery guarantee the
FROZEN contract exists to protect is silently traded away. Likely root cause: a workaround for the psycopg3
"cascading transaction errors on schema mismatch" the swarm hit during the build (seal doc §line 110) — a
"make-it-work" patch, not a "make-it-right" fix.

## THE EXACT SCOPE (9 violating calls across 6 writers; the other 4 are CLEAN)
| Writer | Line(s) | Call | Fix |
|---|---|---|---|
| `bo_laksana.py` | 896 | `conn.rollback()` (per-row fallback) | REMOVE — see §B (savepoint pattern) |
| `bo_laksana.py` | 897 | `conn.commit()` (per-batch) | REMOVE |
| `bo_sangati.py` | 320 | `conn.commit()` | REMOVE |
| `bo_samskara.py` | 139 | `conn.rollback()` (per-row fallback) | REMOVE — §B |
| `bo_samskara.py` | 140 | `conn.commit()` | REMOVE |
| `bo_upaya.py` | 462 | `conn.commit()` | REMOVE |
| `bo_drishti.py` | 260, 284 | `conn.commit()` ×2 | REMOVE both |
| `bo_anveshana.py` | 723 | `conn.rollback()` (per-row fallback) | REMOVE — §B |
| `bo_anveshana.py` | 724, 748 | `conn.commit()` ×2 | REMOVE both |
**CLEAN (do NOT touch):** `bo_karanajala.py`, `bo_bimba.py`, `bo_samvada.py`, `bo_pramana_mapa.py` — zero violations.
(All 6 affected confirmed `conn = ctx.db_conn` at: laksana 951 · sangati 337 · samskara 157 · upaya 484 · drishti 273 · anveshana 737.)

## §A — THE FIX (the simple, correct case — the bare commits)
For every plain `conn.commit()` on `ctx.db_conn`: **DELETE the line.** The orchestrator's `run_substep` driver
commits the sub-step's savepoint after the writer returns (`asset_runner.py` §202–217). The writer just executes its
INSERTs on `ctx.db_conn`; it does NOT commit. (The data still lands — the orchestrator commits it.)

## §B — THE FIX (the per-row-fallback case — laksana / samskara / anveshana)
These writers have a "batch insert → on failure, per-row insert with `conn.rollback()` to skip a bad row" fallback.
The `conn.rollback()` there rolls back the WHOLE connection (illegal + destroys prior work). Correct pattern — use a
**per-row SAVEPOINT** so a single bad row is skipped WITHOUT touching the connection-level transaction:
```python
for row in batch:
    try:
        cur.execute("SAVEPOINT row_sp")
        cur.execute(_INSERT_SQL, row)
        cur.execute("RELEASE SAVEPOINT row_sp")
    except Exception as row_exc:
        cur.execute("ROLLBACK TO SAVEPOINT row_sp")   # rolls back ONLY this row, not the connection
        logger.warning("[writer] skipping row ...: %s", row_exc)
```
Then DELETE the per-batch `conn.commit()`. The orchestrator owns the outer commit. (If the writer is a heavy
`plan_substeps`/`run_substep` writer, the orchestrator already wraps each sub-step in its own savepoint — the
per-row savepoint nests safely inside it.)

## §C — RE-VERIFY (prove the data still lands + the contract holds)
1. **Static:** `grep -rnE "ctx\.db_conn\.(commit|rollback|close)|conn\.(commit|rollback|close)\(\)"` across the 10
   writers → must return ZERO (where `conn = ctx.db_conn`). The other 4 writers stay clean.
2. **Re-run the 6 affected assets** via the orchestrator for `482012f1` (Cloud SQL proxy up): bo_laksana,
   bo_sangati, bo_samskara, bo_upaya, bo_drishti, bo_anveshana. Delete-then-insert idempotency means a clean re-run.
3. **Confirm counts UNCHANGED on prod** (the fix must not change data — only who commits): MSR=66,738, embeddings=66,738,
   discoveries=1,411, anomalies=4,359, lenses=60; Trap-1=0; FORENSIC 7/7.
4. **Failure-path test (the actual point of the fix):** force a bad row in one batch; confirm the per-row savepoint
   skips ONLY that row, the sub-step otherwise commits via the orchestrator, and the connection transaction is intact
   (no cascading-abort). This is what was broken; prove it's fixed.
5. **B6 re-run** (or at least the affected dimensions) → still PASS.

## §D — LAND IT
- Commit on `feature/l2-bodha`: `fix(l2-bodha): writers honor FROZEN contract — remove ctx.db_conn commit/rollback (Vimarśaka RED); per-row savepoint for bad-row skip`.
- Update `L2_BODHA_CLOSE_v1_0.md`: add a "post-seal remediation" note (the Vimarśaka RED finding + fix + re-verify result) — honest provenance.
- Push; the PR #302 update carries it; CI green; then merge.
- Smṛti log: record the RED finding + remediation per AUTONOMY_RESILIENCE §C.1 (Vimarśaka RED → fix → re-verify).

## HARD STOPS
- If removing a `conn.commit()` causes data to NOT land (the orchestrator isn't committing the sub-step) → that
  would mean the writer isn't conforming to the run_substep contract elsewhere → investigate the run()/run_substep
  shape against §N.2, do NOT re-add the commit. (Expected: data lands — the orchestrator commits.)
- If a count CHANGES after the fix → STOP + report (the fix must be data-neutral; a change means something else moved).

**Begin: §A + §B edits across the 6 writers (9 calls), then §C re-verify, then §D land. Go.**
