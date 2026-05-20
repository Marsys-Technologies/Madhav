---
artifact: BOOTSTRAP_PANCHANGA_BUILD_MANIFESTS_AUDIT_v1_0.md
type: FORENSIC_AUDIT
canonical_id: BOOTSTRAP_PANCHANGA_BUILD_MANIFESTS_AUDIT
version: 1.0
status: FINAL
authored_by: Cowork session — Cowork_PanchangProdClose_2026-05-21
authored_on: 2026-05-21
trigger: >
  Phase 4C Wave 1 production close-out (2026-05-21) flagged that the prior
  bootstrap build `phase-4c-20260519-153426` required manual rollback because
  `bootstrap_panchanga.py` did not auto-register a `build_manifests` row. The
  operator had to insert that row by hand to mark the build as `rolled_back`
  before the second build (`phase-4c-enrich-20260521-r2`) could run cleanly.
  The successful build was likewise registered manually. This audit determines
  root cause and proposes a fix.
scope: Read-only forensic. No code modified in this audit; proposed patch is
  documented for a subsequent coding session.
mirror_obligations: none (Claude-only artifact; no Gemini-side counterpart)
---

# Bootstrap Panchanga × `build_manifests` — Forensic Audit

## §1 — Headline

`bootstrap_panchanga.py` (the writer that populates `panchanga_daily_staging`) does **not** register a row in `build_manifests` for the build it is running. Neither does any swap step in the Phase 4C runbook (`RUNBOOK_EPHEMERIS_REBUILD_v1_0.md §4`) — the runbook's "atomic swap" is raw `BEGIN; TRUNCATE; INSERT…SELECT; COMMIT;` with no `build_manifests` interaction at all.

The result is that `panchanga_daily` can be populated under a `build_id` for which `build_manifests` carries no provenance row. This breaks two invariants:

1. **Audit trail.** `build_manifests` is the canonical "who ran what, when, with what tooling" registry (`platform/migrations/013_build_pipeline_staging.sql` lines 12–26). Phase 4C builds leave it empty for the panchanga stream.
2. **Operational queries.** Any logic that asks "what is the current live panchanga build?" via `SELECT build_id FROM build_manifests WHERE status='live'` returns nothing for the panchanga stream. Rollback, version comparison, and per-build telemetry all degrade to manual SQL.

Both Phase 4C builds (`phase-4c-20260519-153426` and `phase-4c-enrich-20260521-r2`) needed `build_manifests` rows inserted by hand at close-out. The second build's rollback would have required a third manual step.

## §2 — Comparison Against the Canonical Pattern

The RAG-pipeline and ephemeris-rebuild streams handle `build_manifests` correctly. Three reference points:

**Reference 1 — RAG pipeline writer (`platform/python-sidecar/pipeline/main.py` lines 171–189):**

```python
with psycopg.connect(db_url, ...) as conn:
    conn.execute(
        """
        INSERT INTO build_manifests
          (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
           embedding_model, embedding_dim, chunk_count, embedding_count,
           status, manifest_uri)
        VALUES (%s, %s, %s, %s, %s, %s, 0, 0, %s, '')
        ON CONFLICT (build_id) DO NOTHING
        """,
        (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
         embedding_model, embedding_dim, 'staging'),
    )
```

Status `'staging'` set at run-start. `ON CONFLICT (build_id) DO NOTHING` makes this idempotent on retry.

**Reference 2 — Ephemeris swap script (`platform/python-sidecar/pipeline/swap_ephemeris_staging.py` lines 36–50, 80):**

```python
cur.execute("SELECT 1 FROM build_manifests WHERE build_id = %s", (BUILD_ID,))
if not cur.fetchone():
    log.info("Inserting build_manifests row for %s", BUILD_ID)
    cur.execute("""
        INSERT INTO build_manifests
          (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
           embedding_model, embedding_dim, chunk_count, embedding_count,
           status, manifest_uri, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (build_id) DO NOTHING
    """, ( ... ))
...
# After the staging→live INSERT:
cur.execute("UPDATE build_manifests SET status = 'live', promoted_at = NOW() "
            "WHERE build_id = %s", (BUILD_ID,))
```

Two-stage protocol: backfill the registration if the writer didn't already do it (belt-and-suspenders idempotency), then mark `live` + record `promoted_at` after the swap commits.

**Reference 3 — Panchanga writer (`platform/python-sidecar/pipeline/bootstrap_panchanga.py` lines 46–102, 252–341):**

Grep result: `grep -n "build_manifest" bootstrap_panchanga.py` returns nothing. The writer constructs `build_id` (line 322: `row_data["build_id"] = build_id`), passes it into the staging-table INSERT, and otherwise never references the manifest table.

The runbook's swap step (`RUNBOOK_EPHEMERIS_REBUILD_v1_0.md §4 step 5`) is bare SQL:

```sql
BEGIN;
TRUNCATE panchanga_daily;
INSERT INTO panchanga_daily SELECT * FROM panchanga_daily_staging;
COMMIT;
```

No `build_manifests` interaction at either stage of the panchanga pipeline.

## §3 — Root Cause

The Phase 4C bootstrap was modelled on `bootstrap_ephemeris.py` (which also doesn't write `build_manifests` itself — it delegates that to its swap script). But Phase 4C's swap was specified as inline runbook SQL rather than as a parallel `swap_panchanga_staging.py`. The `build_manifests` responsibility fell into the gap between the writer (which didn't own it) and the swap (which didn't exist).

This is a copy-paste lineage issue, not a logic error. The original 4C author copied the writer pattern but stopped before creating the swap script that would have carried the manifest responsibility forward.

## §4 — Blast Radius

**What is broken in production today** (2026-05-21):

- `SELECT * FROM build_manifests WHERE build_id LIKE 'phase-4c-%'` returns rows only if the operator inserted them manually during close-out. Without operator effort, this query returns nothing.
- Future panchanga rebuilds will fail the same way unless the operator remembers to do the manual `INSERT` and `UPDATE` again. The runbook does not currently document this requirement.

**What is not broken:**

- `panchanga_daily` itself is correctly populated. `build_id` is in every row, so per-row provenance is preserved.
- The application code does not query `build_manifests` for panchanga (it reads `panchanga_daily` directly). No user-facing breakage.

**Severity:** medium. No data integrity issue; this is an operational hygiene gap that compounds each rebuild cycle.

## §5 — Proposed Fix

Two patches. The first is mandatory; the second is recommended for symmetry with `bootstrap_ephemeris.py` + `swap_ephemeris_staging.py`.

### §5.1 — Patch A (mandatory): register `build_manifests` row in `bootstrap_panchanga.py`

Add an `_ensure_build_manifest()` call inside `run()`, executed before the main write loop. Mirrors `pipeline/main.py` lines 171–189.

```python
# Insert near top of pipeline/bootstrap_panchanga.py, before _check_existing_rows():

_BUILD_MANIFEST_INSERT_SQL = """
INSERT INTO build_manifests
  (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
   embedding_model, embedding_dim, chunk_count, embedding_count,
   status, manifest_uri, notes)
VALUES
  (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (build_id) DO NOTHING
"""


def _ensure_build_manifest(db_url: str, build_id: str) -> None:
    """
    Register this panchanga rebuild in build_manifests with status='staging'.
    Idempotent via ON CONFLICT — safe to call on retry. Status is later
    promoted to 'live' by the operator swap step (see RUNBOOK §4 step 5,
    or swap_panchanga_staging.py once it lands).
    """
    try:
        import psycopg2
    except ImportError:
        import psycopg as psycopg2  # type: ignore[no-redef]

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(_BUILD_MANIFEST_INSERT_SQL, (
                build_id,
                f"bootstrap_panchanga.py:{os.environ.get('USER', 'unknown')}",
                "n/a-panchanga-engine-direct",       # no asset registry for engine-direct
                EPHEMERIS_VERSION,                    # pipeline 'image' = sidecar version
                "n/a-no-embeddings",                  # panchanga uses no embeddings
                0,                                    # embedding_dim
                0,                                    # chunk_count
                0,                                    # embedding_count
                "staging",
                f"engine-direct:{build_id}",          # manifest_uri placeholder
                f"bootstrap_panchanga.py run; range {DATE_START}–{DATE_END}",
            ))
        conn.commit()
    logger.info("build_manifests row registered (status=staging) for build_id=%s", build_id)
```

And inside `run()`, add a call right after the existing `_check_existing_rows` guard:

```python
def run(build_id: str, start: date = DATE_START, end: date = DATE_END, dry_run: bool = False) -> int:
    swe = _init_swe()
    logger.info("bootstrap_panchanga: build_id=%s start=%s end=%s dry_run=%s",
                build_id, start, end, dry_run)
    ...
    if not dry_run:
        db_url = os.environ["DATABASE_URL"]
        existing = _check_existing_rows(db_url, build_id)
        if existing is not None:
            return existing
        _ensure_build_manifest(db_url, build_id)   # NEW LINE
    ...
```

Cost: +30 lines. Test coverage: extend `pipeline/__tests__/test_bootstrap_panchanga.py` to mock `psycopg2.connect` and assert the INSERT was called with status='staging'.

### §5.2 — Patch B (recommended): create `swap_panchanga_staging.py`

A direct port of `swap_ephemeris_staging.py`, retargeted at `panchanga_daily` / `panchanga_daily_staging`. The runbook's §4 step 5 raw SQL becomes a single Python invocation:

```bash
# Old runbook step 5:
psql "$DATABASE_URL" <<'SQL'
BEGIN;
TRUNCATE panchanga_daily;
INSERT INTO panchanga_daily SELECT * FROM panchanga_daily_staging;
COMMIT;
SQL

# New runbook step 5:
python -m pipeline.swap_panchanga_staging
```

The script wraps the same TRUNCATE+INSERT with three additional responsibilities lifted from `swap_ephemeris_staging.py`:

1. **Idempotent backfill of `build_manifests`** if Patch A hasn't registered the row yet (belt-and-suspenders defence).
2. **Promotion to `status='live'`** with `promoted_at = NOW()` after the staging→live INSERT commits.
3. **Cleanup of staging rows** for the swapped `build_id` (`DELETE FROM panchanga_daily_staging WHERE build_id = %s`).

If Patch A lands, Patch B's backfill INSERT becomes a no-op on the happy path (ON CONFLICT DO NOTHING). The `UPDATE … status='live'` is the irreplaceable function.

### §5.3 — Update `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md §4`

Step 5 swap commands replaced with `python -m pipeline.swap_panchanga_staging` per §5.2. Add a new step 7: "Spot-check `build_manifests` — `SELECT build_id, status, promoted_at FROM build_manifests WHERE build_id = '<run_build_id>'` should show one row with status='live' and a recent `promoted_at`."

## §6 — Minimal-Surface Alternative (if Patch B is deferred)

If `swap_panchanga_staging.py` is too much scope for the fix-up, the minimum operational repair is:

- Apply Patch A (writer registers `staging`).
- Update runbook §4 step 5 SQL to include the status transition inline:

  ```sql
  BEGIN;
  TRUNCATE panchanga_daily;
  INSERT INTO panchanga_daily SELECT * FROM panchanga_daily_staging;
  UPDATE build_manifests SET status='live', promoted_at=NOW()
    WHERE build_id = (SELECT DISTINCT build_id FROM panchanga_daily_staging LIMIT 1);
  COMMIT;
  ```

This leaves the panchanga pipeline asymmetric vs the ephemeris pipeline (no swap script) but closes the operational gap without new files.

## §7 — Recommendation

Land **Patch A** and the **§6 runbook SQL update** in a single coding session as the minimum fix. Land **Patch B** (`swap_panchanga_staging.py`) in a follow-up if/when the panchang stream needs another rebuild and the asymmetry vs ephemeris becomes friction.

Either path should land **before the next panchanga rebuild** — otherwise the manual-registration drill repeats and we accumulate more "phantom" `build_id`s with no `build_manifests` provenance.

## §8 — Open Questions for the Next Session

- Should the `triggered_by` column carry the operator's email (per `manual:<email>` convention in `013_build_pipeline_staging.sql` line 15) or just the script name? Existing scripts vary — `swap_ephemeris_staging.py` uses a script-name string.
- Does `pipeline_image_uri` need a meaningful value for engine-direct (non-Docker) builds, or is the `EPHEMERIS_VERSION` placeholder above acceptable?
- Should bootstrap retry-failure leave the `build_manifests` row at `status='staging'` indefinitely, or should it actively mark `status='failed'` on caught exceptions? (RAG `main.py` leaves it at `staging`; ephemeris path has no explicit failure handler.)

These are governance + ergonomics questions, not blockers. Default the answers to "match `bootstrap_ephemeris.py` exactly" unless the next coding session has reason to diverge.

---

**End of audit.** Cite as `BOOTSTRAP_PANCHANGA_BUILD_MANIFESTS_AUDIT_v1_0.md` in any subsequent session that implements the fix.
