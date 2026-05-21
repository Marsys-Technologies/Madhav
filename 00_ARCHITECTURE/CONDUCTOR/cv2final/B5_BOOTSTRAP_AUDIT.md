---
artifact: B5_BOOTSTRAP_AUDIT.md
purpose: Audit finding — bootstrap_panchanga.py build_manifests auto-registration gap
packet: B.5
produced_during: CV2-FINAL orchestrator
date: 2026-05-21
status: FINDING_DOCUMENTED
---

# B.5 — bootstrap_panchanga.py build_manifests Auto-Registration Audit

## Finding

`platform/python-sidecar/pipeline/bootstrap_panchanga.py` does **not** register a
`build_manifests` row for each run.

The script writes rows to `panchanga_daily_staging` (keyed by `build_id`), and the
`_check_existing_rows` function queries `panchanga_daily_staging` to detect duplicate
`build_id` values. However, the `build_manifests` table — which is the project-wide
build audit trail used by the atomic swap (`swap_ephemeris_staging.py`) and
read by `drift_detector.py` — receives no row from this script.

## Root cause

`bootstrap_panchanga.py` was authored by mirroring `bootstrap_ephemeris.py`
(documented in CLAUDECODE_BRIEF.md v1.0 §2). `bootstrap_ephemeris.py` also lacks
`build_manifests` registration. Neither script adopted the pattern established in:
- `platform/python-sidecar/pipeline/ingest_eclipses_retrogrades.py` — has
  `_ensure_build_manifest()` function (lines 33–60).
- `platform/python-sidecar/pipeline/ingest_life_events_sade_sati.py` — same pattern.

## Incident reference

During Phase 4C Wave 1 close-out (2026-05-21), bootstrap run
`phase-4c-20260519-153426` required manual rollback because:
1. The script wrote 73,414 rows to `panchanga_daily_staging` but registered no
   `build_manifests` row.
2. When `swap_ephemeris_staging.py` attempted the staging → live atomic swap, it
   looked up `build_manifests` for the FK constraint and found nothing.
3. The prior live build (`phase-4c-20260519-153426`) had to be manually rolled back
   and a new run (`phase-4c-enrich-20260521-r2`) was registered manually before the
   swap could proceed.

## Required fix

Add a `_ensure_build_manifest(build_id: str, db_url: str)` function to
`bootstrap_panchanga.py` following the pattern in `ingest_eclipses_retrogrades.py`
lines 33–60, and call it at the start of `run()` before any row writes begin.

Minimal implementation:
```python
def _ensure_build_manifest(build_id: str, db_url: str) -> None:
    with psycopg.connect(db_url) as conn:
        if conn.execute(
            "SELECT 1 FROM build_manifests WHERE build_id = %s", (build_id,)
        ).fetchone():
            log.info("build_manifests row already exists for build_id=%s", build_id)
            return
        conn.execute(
            """
            INSERT INTO build_manifests
              (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
               embedding_model, embedding_dim, chunk_count, embedding_count,
               status, manifest_uri)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (build_id, "bootstrap_panchanga", "n/a", "n/a", "n/a", 0, 0, 0, "staging", "n/a"),
        )
        log.info("Inserted build_manifests row for build_id=%s", build_id)
```

Status should be `"staging"` at registration time; the atomic swap script updates it
to `"live"` on promotion.

## Scope note

This audit is documentation-only. The fix itself is a Phase 4C follow-up item and
should be executed in a dedicated brief or as a tracked item in
`00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md §open_follow_ups`.

**No code changes were made in this packet.** The finding is committed to governance
trail only.
