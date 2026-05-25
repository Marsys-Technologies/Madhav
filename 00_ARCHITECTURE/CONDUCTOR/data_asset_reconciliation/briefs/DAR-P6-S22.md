---
session_id: DAR-P6-S22
phase: 6
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
estimated_minutes: 360
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/
  - platform/src/
  - platform/python-sidecar/pipeline/extractors/
  - platform/python-sidecar/pipeline/writers/
  - platform/python-sidecar/pipeline/bootstrap_ephemeris.py
---

# DAR-P6-S22: Run ephemeris bootstrap synchronously (MEAN_NODE, ~4–6 hours)

Context: The production ephemeris_daily table (657,450 rows) contains TRUE_NODE Rahu/Ketu
data. Commit c63ef9f9 (2026-05-19) fixed bootstrap_ephemeris.py to use MEAN_NODE instead.
The production table has NOT been rebuilt since the fix. This session runs the full rebuild.

WARNING: This session is expected to run for 4–6 hours. Do not interrupt it.
The gate commands for this session will not pass until the bootstrap completes successfully.

## Steps

### 1. Start DB proxy
  bash /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/scripts/start_db_proxy.sh &
  PROXY_PID=$!
  sleep 20
  nc -z localhost 5433 && echo "PROXY_READY" || (echo "PROXY_FAILED" && exit 1)

### 2. Verify bootstrap uses MEAN_NODE (from pre-rebuild check in DAR-P6-S21)
  grep -n 'MEAN_NODE\|mean_node\|TRUE_NODE\|true_node\|node_type' \
    platform/python-sidecar/pipeline/bootstrap_ephemeris.py | head -30

  If TRUE_NODE is still hardcoded anywhere, apply the fix before proceeding:
  Replace the node_type or equivalent parameter with MEAN_NODE.

  The EPHEMERIS_PRE_REBUILD_CHECK.md from DAR-P6-S21 should confirm
  bootstrap_script_node_type: MEAN_NODE — if it says TRUE_NODE, stop and fix first.

### 3. Run the bootstrap synchronously
This command will run for approximately 4–6 hours. Execute it and wait for completion.
Do not background it — wait for the process to exit with code 0.

  python3 platform/python-sidecar/pipeline/bootstrap_ephemeris.py \
    2>&1 | tee 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
  
  BOOTSTRAP_EXIT=$?

  If the script requires additional arguments (e.g. --rebuild, --node-type), check:
    python3 platform/python-sidecar/pipeline/bootstrap_ephemeris.py --help
  Then re-run with the correct flags, still piping to the log file.

### 4. Verify successful completion
  if [ $BOOTSTRAP_EXIT -ne 0 ]; then
    echo "BOOTSTRAP FAILED with exit code $BOOTSTRAP_EXIT"
    tail -100 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
    exit 1
  fi
  
  tail -30 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
  echo "Bootstrap completed successfully."

### 5. Write completion markers to the log
  echo "" >> 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
  echo "bootstrap_complete: true" >> 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
  echo "exit_code: 0" >> 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
  echo "completed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt

### 6. Stop proxy
  kill $PROXY_PID 2>/dev/null || true
