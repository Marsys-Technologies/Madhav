---
session_id: UDA-4-S2
phase: UDA-4
title: "Bootstrap build_manifests auto-registration"
status: pending
---

# UDA-4-S2: Bootstrap build_manifests auto-registration

## Goal
Fix `platform/python-sidecar/scripts/bootstrap_panchanga.py` to auto-register a
`build_manifests` row on completion — preventing the manual rollback incident documented
in CLAUDE.md §E (Phase 4C open follow-up, 2026-05-21).

## Context
The bootstrap script runs a multi-hour data build but doesn't write a `build_manifests` row.
When a prior run needed to be rolled back, the operator had to manually identify and delete
the orphan rows. Auto-registration prevents this.

## Steps

1. Read `platform/python-sidecar/scripts/bootstrap_panchanga.py` to understand:
   - How the build_id is determined
   - Where the script writes its final row (staging→live swap)
   - What database connection is used

2. Add auto-registration at script completion:
   ```python
   # At the end of the script, after successful staging→live swap:
   cursor.execute("""
     INSERT INTO build_manifests (build_id, script_name, status, completed_at, row_count)
     VALUES (%s, %s, 'complete', NOW(), %s)
     ON CONFLICT (build_id) DO UPDATE SET status='complete', completed_at=NOW(), row_count=EXCLUDED.row_count
   """, (build_id, 'bootstrap_panchanga.py', total_rows_written))
   conn.commit()
   print(f"[build_manifests] Registered build_id={build_id} with {total_rows_written} rows")
   ```
   Adapt the exact SQL to match the actual `build_manifests` table schema — read the migration
   file first: `ls platform/supabase/migrations/ | grep build_manifest`.

3. Add equivalent auto-registration to any other bootstrap scripts found in
   `platform/python-sidecar/scripts/` that write bulk data without manifesting.

4. Commit:
   ```bash
   git add platform/python-sidecar/scripts/bootstrap_panchanga.py
   git add platform/python-sidecar/scripts/*.py  # any other bootstraps touched
   git commit -m "fix(bootstrap): UDA-4-S2 — auto-register build_manifests row on completion"
   ```

## Acceptance criteria
- grep -q 'build_manifests' platform/python-sidecar/scripts/bootstrap_panchanga.py && echo PASS
- Script is syntactically valid: python3 -m py_compile platform/python-sidecar/scripts/bootstrap_panchanga.py && echo PASS
