"""
SUPERSEDED — use run_heavy_writer_standalone.py instead.

  DATABASE_URL=... python run_heavy_writer_standalone.py ga_sensitive

WHY SUPERSEDED: This script called build_ga_sensitive(conn=None) directly,
bypassing the orchestrator completely. That means asset_throughput was never
updated — the asset stayed in state='error' even after a successful run.

The new script calls _run_data_writer directly which:
  - Never sets state='building' (TypeScript watchdog never fires)
  - Commits per-substep via _drive_substeps (durable on crash)
  - Sets state='lit' with correct rows_written on success
  - Marks downstream assets stale automatically

See run_heavy_writer_standalone.py for the full documented pattern.
"""
import sys
print(__doc__)
print("Run: DATABASE_URL=... python run_heavy_writer_standalone.py ga_sensitive")
sys.exit(1)
