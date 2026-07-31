# L2 Bodha Writer Fixes + B6 Seal Hardening

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two pre-existing writer bugs (bo_anveshana embedding parse, bo_pramana_mapa ModuleNotFoundError), add B6 output-magnitude and writer-runnability gates that catch both bugs on broken state, then rebuild both assets to floor in PROD.

**Architecture:** Two writer fixes (one SQL cast + loud-fail in bo_anveshana; one Dockerfile COPY line for bodha_writers), two new B6 gate classes added to the existing eval harness. Proof-first sequence: gates RED on broken code → fix code → gates GREEN.

**Tech Stack:** Python 3.11+, psycopg3, pgvector, pytest (integration-marked), Cloud SQL proxy on 5433, Cloud Run Job. No orchestrator changes.

---

## Files

| Action | File |
|---|---|
| Modify | `platform/python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py` |
| Modify | `platform/python-sidecar/pipeline/orchestrator/writers/bo_pramana_mapa.py` *(no-op — imports are correct; fix is Dockerfile only)* |
| Modify | `platform/python-sidecar/Dockerfile.pipeline` |
| Modify | `platform/python-sidecar/tests/l2/test_b6_eval_harness.py` |

---

## Task 1: Create feature branch

**Files:** none (git only)

- [ ] **Step 1: Branch off main**

```bash
git checkout main && git pull
git checkout -b fix/l2-bodha-writer-bugs-b6-gates
```

- [ ] **Step 2: Verify clean state**

```bash
git status
```
Expected: nothing to commit (or only pre-existing untracked files from the git status snapshot).

---

## Task 2: Add B6 gate classes (RED state — prove gates fire on BROKEN code)

**Files:**
- Modify: `platform/python-sidecar/tests/l2/test_b6_eval_harness.py`

These gate tests must be written BEFORE the writer fixes, then run to confirm RED (both writers are broken). The gates prove the new assertions catch what the 35-test suite missed.

**Context:** The DB is live at 127.0.0.1:5433 (start with `bash platform/scripts/start_db_proxy.sh`). The test file is already `pytestmark = pytest.mark.integration` so it requires `--db` or `DATABASE_URL`.

- [ ] **Step 1: Add G-MAG class to test_b6_eval_harness.py**

Append after `class TestLelZeroLeak` (before `class TestSealScorecard`):

```python
# ═══════════════════════════════════════════════════════════════════════════════
# GATE G-MAG — output magnitude: each bo_* asset's live count must meet floor
# ═══════════════════════════════════════════════════════════════════════════════

class TestOutputMagnitude:
    """G-MAG: every bo_* asset must produce >= its registered target_floor rows.

    Runs the asset's own chart-scoped count_sql live against PROD.
    A writer producing < 10% of its floor causes this gate to FAIL — this is
    the gap that allowed a seal while bo_anveshana had 5 rows vs floor 5770.
    """

    # Assets with known floors (from asset_registry as of migration 326).
    # target_floor = 0 means "at least 1 row" (floor intentionally zero-is-ok).
    BO_ASSET_FLOORS: dict[str, int] = {
        "bo_laksana":    500,    # bodha_msr_signals
        "bo_bimba":      100,    # bodha_question_lenses
        "bo_karanajala": 300,    # bodha_convergence + bodha_contradictions
        "bo_sangati":    80,     # bodha_cdlm_cells
        "bo_samvada":    50,     # bodha_cdlm_domain_rollups
        "bo_samskara":   1000,   # bodha_signal_embeddings
        "bo_drishti":    50,     # bodha_cgm_nodes
        "bo_upaya":      10,     # bodha_rm_resonances
        "bo_anveshana":  5770,   # bodha_discoveries + bodha_anomalies
        "bo_pramana_mapa": 1,    # synthesis_quality_scorecard
    }

    def test_bo_asset_counts_meet_floors(self, conn):
        """Query asset_registry for count_sql, execute each, assert >= target_floor."""
        rows = _fetch(
            conn,
            """SELECT asset_id, count_sql, target_floor
               FROM asset_registry
               WHERE asset_id LIKE 'bo_%%'
                 AND catalog_status = 'active'
               ORDER BY asset_id""",
        )
        assert rows, "No active bo_* assets found in asset_registry — registry not seeded"

        failures = []
        for row in rows:
            asset_id = row["asset_id"]
            count_sql = row["count_sql"]
            registered_floor = int(row["target_floor"] or 0)

            # Use whichever floor is stricter: registry or our local known-floor map
            floor = max(registered_floor, self.BO_ASSET_FLOORS.get(asset_id, 0))
            if floor == 0:
                continue  # intentionally no floor set

            try:
                # Inject chart_id parameter (count_sql uses %(chart_id)s or $1 style)
                sql = count_sql.replace("%(chart_id)s", "%s").replace("$1", "%s")
                live_count = _count(conn, sql, [CHART_ID])
            except Exception as exc:
                failures.append(f"{asset_id}: count_sql failed — {exc}")
                continue

            pct_of_floor = live_count / floor if floor > 0 else 1.0
            if live_count < floor:
                failures.append(
                    f"{asset_id}: count={live_count} < floor={floor} "
                    f"({pct_of_floor:.1%} of floor) — G-MAG FAIL"
                )

        assert not failures, "Output magnitude gate failures:\n" + "\n".join(failures)
```

- [ ] **Step 2: Add G-RUN class to test_b6_eval_harness.py**

Append immediately after the G-MAG class:

```python
# ═══════════════════════════════════════════════════════════════════════════════
# GATE G-RUN — writer runnability: each bo_* writer must import cleanly
# ═══════════════════════════════════════════════════════════════════════════════

class TestWriterRunnability:
    """G-RUN: every bo_* writer module must import without ModuleNotFoundError.

    Runs each writer import in a subprocess that matches the Cloud Run
    PYTHONPATH exactly — so a missing bodha_writers package in the Dockerfile
    is caught here before it reaches Cloud Run.
    """

    BO_WRITER_MODULES = [
        "pipeline.orchestrator.writers.bo_laksana",
        "pipeline.orchestrator.writers.bo_bimba",
        "pipeline.orchestrator.writers.bo_karanajala",
        "pipeline.orchestrator.writers.bo_sangati",
        "pipeline.orchestrator.writers.bo_samvada",
        "pipeline.orchestrator.writers.bo_samskara",
        "pipeline.orchestrator.writers.bo_drishti",
        "pipeline.orchestrator.writers.bo_upaya",
        "pipeline.orchestrator.writers.bo_anveshana",
        "pipeline.orchestrator.writers.bo_pramana_mapa",
    ]

    def test_all_bo_writers_import_cleanly(self):
        """Each writer module must be importable without ModuleNotFoundError."""
        import subprocess
        import sys

        failures = []
        for module in self.BO_WRITER_MODULES:
            result = subprocess.run(
                [sys.executable, "-c", f"import {module}"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                failures.append(f"{module}: {stderr[:300]}")

        assert not failures, (
            "Writer import failures (G-RUN gate):\n" + "\n".join(failures)
        )

    def test_bo_anveshana_embedding_fallback_is_disabled(self):
        """_fetch_embeddings_np must NOT have a silent return-None fallback path.

        Checks that the function is defined to raise on parse failure rather
        than silently returning ([], None). This is a structural code check,
        not a runtime DB check — it catches the regression pattern.
        """
        import inspect
        from pipeline.orchestrator.writers.bo_anveshana import _fetch_embeddings_np

        src = inspect.getsource(_fetch_embeddings_np)
        # The old silent fallback was: `return [], None` inside an except block.
        # After the fix, parse failures must raise. Assert the silent path is gone.
        assert "return [], None" not in src, (
            "_fetch_embeddings_np still has silent 'return [], None' fallback — "
            "embedding parse failures will degrade silently. Fix: raise on parse error."
        )
```

- [ ] **Step 3: Run the new gates in RED state (expected: FAIL)**

Ensure DB proxy is running. From `platform/python-sidecar/`:

```bash
cd /path/to/Madhav/platform/python-sidecar
python -m pytest tests/l2/test_b6_eval_harness.py::TestOutputMagnitude \
    tests/l2/test_b6_eval_harness.py::TestWriterRunnability \
    -v -m integration 2>&1 | tail -40
```

Expected RED failures:
- `TestOutputMagnitude::test_bo_asset_counts_meet_floors` → FAIL for `bo_anveshana` (count=5 < floor=5770)
- `TestWriterRunnability::test_all_bo_writers_import_cleanly` → FAIL for `bo_pramana_mapa` (ModuleNotFoundError: No module named 'bodha_writers')
- `TestWriterRunnability::test_bo_anveshana_embedding_fallback_is_disabled` → FAIL (silent `return [], None` still present)

Save the RED output verbatim for the deliverable.

- [ ] **Step 4: Commit gate stubs**

```bash
git add platform/python-sidecar/tests/l2/test_b6_eval_harness.py
git commit -m "test(b6): add G-MAG output-magnitude and G-RUN writer-runnability gates (RED)"
```

---

## Task 3: Fix Bug 1 — bo_anveshana embedding vector parse

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py`

**Root cause**: `_fetch_embeddings_np` (line 178) catches all exceptions and silently returns `([], None)`. When psycopg3 binary protocol returns `embedding_vec` as `bytes`/`memoryview` (not `str`), `list(v)` produces integers of variable length, `np.array(...)` raises `ValueError: inhomogeneous shape`, this is caught silently, embedding outlier primitive is skipped, and the total discovery count collapses to ~1/ayanamsha.

**Fix**: Cast `embedding_vec::text` in SQL (guarantees string format regardless of psycopg binary mode). Strip empty elements from split. Remove silent `return [], None` — make parse failures raise loudly.

- [ ] **Step 1: Fix `_fetch_embeddings_np` in bo_anveshana.py**

Replace the entire `_fetch_embeddings_np` function (lines 178–210 approximately):

```python
def _fetch_embeddings_np(conn: Any, chart_id: str, aya: str) -> tuple[list[str], np.ndarray | None]:
    """Load signal_ids + embedding vectors for one ayanamsha.

    Casts embedding_vec to text explicitly so psycopg3 binary mode
    never returns bytes/memoryview — we always get a '[x,y,...]' string.
    Parse failures RAISE rather than returning ([], None): silent fallback
    was the root cause of 5-row output (vs floor 5770).
    """
    rows = _fetch_dict(
        conn,
        """SELECT signal_id, embedding_vec::text AS embedding_vec
           FROM bodha_signal_embeddings
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, aya],
    )
    if not rows:
        return [], None

    signal_ids = [str(r["signal_id"]) for r in rows]
    vecs = []
    parse_errors = 0
    for r in rows:
        v = r["embedding_vec"]
        if v is None:
            parse_errors += 1
            continue
        if isinstance(v, (list, tuple)):
            vecs.append([float(x) for x in v])
        elif isinstance(v, str):
            v_clean = v.strip().strip("[]")
            floats = [float(x) for x in v_clean.split(",") if x.strip()]
            if not floats:
                parse_errors += 1
                continue
            vecs.append(floats)
        else:
            # Unexpected type — raise loudly rather than degrading silently
            raise RuntimeError(
                f"[bo_anveshana] Unexpected embedding_vec type {type(v)} for "
                f"signal_id={r.get('signal_id')} — register pgvector type or cast to text"
            )

    if parse_errors > 0:
        logger.warning("[bo_anveshana] %d embedding rows skipped (None/empty)", parse_errors)

    if not vecs:
        raise RuntimeError(
            f"[bo_anveshana] No valid embedding vectors parsed for chart={chart_id} aya={aya} "
            f"({len(rows)} rows fetched, all failed to parse)"
        )

    # Verify uniform dimensionality before constructing matrix
    dim0 = len(vecs[0])
    mismatched = [i for i, v in enumerate(vecs) if len(v) != dim0]
    if mismatched:
        raise RuntimeError(
            f"[bo_anveshana] Inhomogeneous embedding dimensions: expected {dim0} but "
            f"{len(mismatched)} rows have different lengths — data integrity error"
        )

    mat = np.array(vecs, dtype=np.float32)
    return signal_ids[:len(vecs)], mat
```

- [ ] **Step 2: Verify the change compiles**

```bash
cd /path/to/Madhav/platform/python-sidecar
python -c "from pipeline.orchestrator.writers.bo_anveshana import _fetch_embeddings_np; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Run only the structural gate test (no DB needed)**

```bash
python -m pytest tests/l2/test_b6_eval_harness.py::TestWriterRunnability::test_bo_anveshana_embedding_fallback_is_disabled -v
```
Expected: PASS (the `return [], None` string is no longer in the source).

- [ ] **Step 4: Commit the fix**

```bash
git add platform/python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py
git commit -m "fix(bo_anveshana): cast embedding_vec::text, raise on parse failure (silent fallback was causing 5-row output)"
```

---

## Task 4: Fix Bug 2 — bo_pramana_mapa ModuleNotFoundError

**Files:**
- Modify: `platform/python-sidecar/Dockerfile.pipeline`

**Root cause**: `Dockerfile.pipeline` COPYs `pipeline/`, `brahmagyan/`, `ga_writers/`, `pyjhora_adapter/`, `panchang_engine/` — but NOT `bodha_writers/`. The `bodha_writers` package (at `platform/python-sidecar/bodha_writers/`) contains `_idempotency.py` and `formulas.py` which `bo_pramana_mapa.py` imports at runtime. Local dev works (bodha_writers/ is on PYTHONPATH), Cloud Run fails with `ModuleNotFoundError`.

The fix is one COPY line in `Dockerfile.pipeline`. No changes to `bo_pramana_mapa.py` itself — the imports are correct, the package just isn't shipped.

- [ ] **Step 1: Add COPY line for bodha_writers in Dockerfile.pipeline**

After the existing `COPY platform/python-sidecar/ga_writers/` line (line 38), add:

```dockerfile
# L2 Bodha shared helpers (bodha_writers/_idempotency.py + bodha_writers/formulas.py).
# Required by bo_pramana_mapa (and other bo_* writers using idempotency helpers).
# Without this, Cloud Run Job raises ModuleNotFoundError: No module named 'bodha_writers'.
COPY platform/python-sidecar/bodha_writers/ ./platform/python-sidecar/bodha_writers/
```

- [ ] **Step 2: Verify import in the same PYTHONPATH context Cloud Run uses**

```bash
cd /path/to/Madhav
PYTHONPATH=platform/python-sidecar python -c "
from bodha_writers._idempotency import replace_prior_scorecard
from bodha_writers.formulas import VERSION_SALIENCE_FORMULA, VERSION_LINKAGE_FORMULA, VERSION_RESONANCE_FORMULA, VERSION_CONVERGENCE_FORMULA
print('bodha_writers OK:', VERSION_SALIENCE_FORMULA)
"
```
Expected: `bodha_writers OK: v1.0`

- [ ] **Step 3: Verify the full pramana_mapa module imports cleanly**

```bash
PYTHONPATH=platform/python-sidecar python -c "
from pipeline.orchestrator.writers.bo_pramana_mapa import BoPramanaMapa
print('bo_pramana_mapa OK')
"
```
Expected: `bo_pramana_mapa OK`

- [ ] **Step 4: Commit the fix**

```bash
git add platform/python-sidecar/Dockerfile.pipeline
git commit -m "fix(bo_pramana_mapa): add bodha_writers/ COPY to Dockerfile.pipeline (ModuleNotFoundError on Cloud Run)"
```

---

## Task 5: Run gates in GREEN state — confirm both fixes pass

**Files:** none (test run only)

- [ ] **Step 1: Run G-RUN gates**

```bash
cd /path/to/Madhav/platform/python-sidecar
python -m pytest tests/l2/test_b6_eval_harness.py::TestWriterRunnability -v
```
Expected:
- `test_all_bo_writers_import_cleanly` → PASS (all 10 bo_* modules import)
- `test_bo_anveshana_embedding_fallback_is_disabled` → PASS

- [ ] **Step 2: Run full B6 harness (G-MAG will be RED until PROD rebuild)**

```bash
python -m pytest tests/l2/test_b6_eval_harness.py -v -m integration 2>&1 | tail -50
```
Note: `TestOutputMagnitude::test_bo_asset_counts_meet_floors` will still FAIL for `bo_anveshana` until the PROD rebuild in Task 6. This is expected — the gate is working. Save output.

---

## Task 6: PR + CI green (before PROD rebuild)

**Files:** none (git only)

- [ ] **Step 1: Push branch and create PR**

```bash
git push -u origin fix/l2-bodha-writer-bugs-b6-gates
```

Then create PR targeting `main`. PR title: `fix(l2-bodha): bo_anveshana embedding parse + bo_pramana_mapa Dockerfile + B6 magnitude/runnability gates`.

PR body should include:
- Root cause summary for each bug (3 lines each)
- B6 RED gate output (copy from Task 2 Step 3)
- B6 GREEN gate output (from Task 5)
- PROD rebuild to follow after merge (Task 7)

- [ ] **Step 2: Wait for CI to pass**

CI runs `pytest -m "not integration"` so the integration-marked B6 tests don't run in CI. Verify all other governance gates pass.

- [ ] **Step 3: Merge PR**

After CI green and any review, merge to main.

---

## Task 7: PROD rebuild — bo_anveshana then bo_pramana_mapa

**Context:** PROD = Cloud SQL proxy on 5433 (bash `platform/scripts/start_db_proxy.sh`). Chart ID = `482012f1-710e-4a25-994a-93821f5871aa`. Cloud Run Job revision must match the merged PR SHA before trusting the rebuild.

**IMPORTANT**: Verify Cloud Run revision == merge SHA before dispatching any rebuild.

- [ ] **Step 1: Confirm Cloud Run revision matches merge SHA**

```bash
gcloud run jobs describe brahma-build-pipeline-job \
    --region=asia-south1 \
    --format="value(spec.template.spec.containers[0].image)" 2>/dev/null
```

Expected: the image tag should contain the merge SHA from Task 6. If it doesn't, wait for the Cloud Build triggered by merge to complete before proceeding.

- [ ] **Step 2: Mark bo_anveshana stale to enable rebuild**

Using the cockpit or direct SQL via proxy:

```sql
-- Connect: PGPASSWORD="${PGPASSWORD:?}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis"
UPDATE asset_throughput
SET state = 'stale', last_built_at = NOW()
WHERE asset_id = 'bo_anveshana'
  AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
```

- [ ] **Step 3: Dispatch bo_anveshana rebuild via Cloud Run**

Dispatch via cockpit UI or:

```bash
gcloud run jobs execute brahma-build-pipeline-job \
    --region=asia-south1 \
    --args="--chart-id=482012f1-710e-4a25-994a-93821f5871aa,--asset-ids=bo_anveshana"
```

Monitor: `gcloud run jobs executions list --job=brahma-build-pipeline-job --region=asia-south1 --limit=1`

Wait for `succeededCount=1`.

- [ ] **Step 4: Verify bo_anveshana count meets floor**

```sql
SELECT count(*) FROM bodha_discoveries
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';

SELECT count(*) FROM bodha_anomalies
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
```

Expected: discoveries + anomalies ≥ 5770 (expect ~7215 total). If the count is still < 5770, check Cloud Run logs for parse errors (they will now be loud, not silent).

- [ ] **Step 5: Mark bo_pramana_mapa stale and rebuild**

```sql
UPDATE asset_throughput
SET state = 'stale', last_built_at = NOW()
WHERE asset_id = 'bo_pramana_mapa'
  AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
```

Then dispatch:
```bash
gcloud run jobs execute brahma-build-pipeline-job \
    --region=asia-south1 \
    --args="--chart-id=482012f1-710e-4a25-994a-93821f5871aa,--asset-ids=bo_pramana_mapa"
```

Wait for `succeededCount=1`.

- [ ] **Step 6: Verify bo_pramana_mapa**

```sql
SELECT count(*) FROM synthesis_quality_scorecard
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
```
Expected: 1.

- [ ] **Step 7: Verify both asset_throughput = 'lit'**

```sql
SELECT asset_id, state, last_built_at
FROM asset_throughput
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND asset_id IN ('bo_anveshana', 'bo_pramana_mapa')
ORDER BY asset_id;
```
Expected: both `state = 'lit'`.

- [ ] **Step 8: Run G-MAG gate against PROD (should now be GREEN)**

```bash
cd /path/to/Madhav/platform/python-sidecar
python -m pytest tests/l2/test_b6_eval_harness.py::TestOutputMagnitude -v -m integration
```
Expected: PASS (bo_anveshana count ≥ 5770, bo_pramana_mapa count = 1, all other bo_* assets already at floor).

- [ ] **Step 9: Run full B6 harness — confirm 35+4 tests pass**

```bash
python -m pytest tests/l2/test_b6_eval_harness.py -v -m integration 2>&1 | tail -60
```
Expected: all tests pass. Note the count: original 35 tests + 2 new gate classes (3 test methods total in G-MAG + G-RUN = net ~38 tests).

- [ ] **Step 10: Verify ZERO frozen-contract violations in Cloud Run logs**

```bash
gcloud run jobs executions describe <last-execution-name> \
    --region=asia-south1 --format=json | grep -i "commit\|rollback\|asset_throughput" | head -20
```
Expected: no violations.

---

## Deliverable checklist

- [ ] Root-cause + fix diff for bo_anveshana (file:line cited above)
- [ ] Root-cause + fix diff for bo_pramana_mapa (Dockerfile.pipeline:line cited above)
- [ ] B6 RED gate run output (Task 2 Step 3) saved
- [ ] B6 GREEN gate run output (Task 5 + Task 7 Step 8-9) saved
- [ ] PROD: bo_anveshana count ≥ 5770, bo_pramana_mapa = 1, both `state='lit'`, clean logs
- [ ] One-line summary: "Fixed bo_anveshana silent embedding fallback (::text cast + loud raise) and bo_pramana_mapa missing Dockerfile COPY (bodha_writers/); B6 G-MAG + G-RUN gates now prevent both regressions."
