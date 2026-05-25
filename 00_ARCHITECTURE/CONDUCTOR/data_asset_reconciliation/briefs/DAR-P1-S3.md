---
session_id: DAR-P1-S3
phase: 1
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
may_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md  # git mv only — move to 99_ARCHIVE
  - 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md  # git mv only — move to 99_ARCHIVE
  - 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/   # create + receive MSR v3/v4
  - 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
  - CLAUDE.md
  - 00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md
  - 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
  - 00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md
  - 025_HOLISTIC_SYNTHESIS/RED_TEAM_L2_5_v1_0.md  # git mv to 00_ARCHITECTURE/
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - platform/
---

# DAR-P1-S3: Archive MSR v3+v4 + GCS_LAYOUT v1.1 + LEL count corrections

## Context

MSR v3.0 and v4.0 still live in `025_HOLISTIC_SYNTHESIS/` alongside the canonical v5.0.
Having all three on disk confuses drift_detector and the `read_asset` tool. This session
archives v3+v4, bumps GCS_LAYOUT to v1.1, corrects the stale LEL count (36 → 57 events)
across 9 governance files, backfills MIGRATIONS_APPLIED_LOG for migrations 072–082, and
moves RED_TEAM_L2_5_v1_0.md to its correct folder.

## Steps

1. Create archive directory and move superseded MSR files:
   ```bash
   mkdir -p 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/
   git mv 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
   git mv 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v4_0.md
   ```

2. Read and update `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md`:
   - Bump version frontmatter: `1.0` → `1.1`
   - Add changelog entry: "v1.1 (2026-05-25): MSR v3+v4 marked superseded; MSR_v5_0 primary; ephemeris section updated"
   - In the `L2_5/` section: mark `MSR_v3_0.md` and `MSR_v4_0.md` as `SUPERSEDED → 99_ARCHIVE/`; set `MSR_v5_0.md` as `PRIMARY (573 signals)`
   - Update ephemeris entry to reflect Phase 4C completion: `panchanga_daily` 73,414 rows live

3. Update LEL count in ALL NINE stale governance files.
   For each file listed below, find the phrase referencing LEL event count and update:
   - Old patterns: `"36 events"`, `"LEL v1.6"`, `"1.6"` (as version)
   - New values: `"57 events + 5 period summaries + 8 chronic patterns"`, `"LEL v1.7"`, `"version: 1.7"`
   Files to update:
   - `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — find LEL entry, update count and version
   - `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` — find LEL row, update version + description
   - `CLAUDE.md §D` — LEL table row
   - `CLAUDE.md §E` — LEL workstream bullet (event count in text)
   - `00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md` — LEL reference
   - `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` — LEL prerequisite mention

4. Backfill `00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md` for migrations 072–082 (MCP Transformation batch).
   Read each migration file at `platform/migrations/` to get the description, then add one row per migration:
   ```
   | migration | confirmed_date | confirmed_method | description |
   | 072       | 2026-05-22     | inferred_from_workstream_close | [from file header] |
   ...
   | 082       | 2026-05-22     | inferred_from_workstream_close | [from file header] |
   ```

5. Move RED_TEAM_L2_5_v1_0.md to correct folder:
   ```bash
   git mv 025_HOLISTIC_SYNTHESIS/RED_TEAM_L2_5_v1_0.md 00_ARCHITECTURE/RED_TEAM_L2_5_v1_0.md
   ```

6. Commit:
   ```
   dar: P1-S3 archive MSR v3+v4; GCS_LAYOUT v1.1; LEL v1.7 count corrections across 9 files
   ```

## Acceptance criteria

- `test -f 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` → TRUE
- `test -f 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v4_0.md` → TRUE
- `test -f 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` → FALSE (archived)
- `test -f 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md` → FALSE (archived)
- `grep 'version: 1.1' 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md` → match
- `grep '57 events' 00_ARCHITECTURE/CAPABILITY_MANIFEST.json` → match
