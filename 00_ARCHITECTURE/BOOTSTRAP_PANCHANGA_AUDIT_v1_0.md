---
artifact: BOOTSTRAP_PANCHANGA_AUDIT_v1_0.md
version: 1.0
status: CLOSED
authored: 2026-05-23
authored_by: Claude Code — MCPT v3.6 housekeeping pass
---

# bootstrap_panchanga.py — Build Manifests Auto-Registration Audit

## Background

CLAUDE.md §E Phase 4C documented an open follow-up:
> "audit `bootstrap_panchanga.py` build_manifests auto-registration (prior build needed manual
> rollback because the bootstrap writer didn't auto-register a build_manifests row; documented 2026-05-21)"

## Findings

### Finding 1: Existing entries had empty asset_id

The three panchanga build_manifests entries were manually registered by the operator with
correct metadata (build_id, triggered_by, notes, manifest_uri='n/a') but with `asset_id` = ''
(empty string). The `asset_id` column was added in migration 081 (`ALTER TABLE build_manifests
ADD COLUMN IF NOT EXISTS asset_id text`) as a nullable column, so existing rows were not required
to have a value.

| Build ID | Status | asset_id before fix | asset_id after fix |
|---|---|---|---|
| phase-4b-20260519-150800 | live | '' | 'panchanga_daily' |
| phase-4c-20260519-153426 | rolled_back | '' | 'panchanga_daily' |
| phase-4c-enrich-20260521-r2 | live | '' | 'panchanga_daily' |

**Fix applied:** `UPDATE build_manifests SET asset_id='panchanga_daily' WHERE build_id IN (...)`

### Finding 2: bootstrap_panchanga.py had no auto-registration call

The `run()` function wrote rows to `panchanga_daily_staging` but made no INSERT into
`build_manifests`. The prior builds were manually registered by the operator post-run.

**Fix applied:** Added `_register_build_manifest()` helper function to
`platform/python-sidecar/pipeline/bootstrap_panchanga.py`. Called from `run()` after the final
`_flush()` when `dry_run=False`.

Registration behavior:
- Inserts with `status='staging'` and `asset_id='panchanga_daily'`
- Uses 'n/a' and 0 placeholders for cloud-build-specific fields (pipeline_image_uri,
  embedding_model, embedding_dim, chunk_count, embedding_count, manifest_uri)
- ON CONFLICT DO UPDATE preserves existing live/rolled_back status (idempotent)
- Errors are caught as WARNING and logged — bootstrap completion is NOT blocked if registration fails
- Supports both psycopg2 and psycopg (matches existing _flush() driver detection)

## Impact

Future `bootstrap_panchanga.py` runs will auto-register with:
- `build_id`: whatever `--build-id` was passed (or the uuid4 default)
- `asset_id`: 'panchanga_daily'
- `status`: 'staging' (operator must UPDATE to 'live' after atomic swap verification)
- `notes`: "Panchanga bootstrap {start}..{end} Lahiri sidereal Bhubaneswar, {row_count} rows"

Operator responsibility remains: UPDATE build_manifests SET status='live' after staging→live swap.
The registration marks the build as 'staging'; only the operator can promote to 'live'.

## Status: CLOSED
