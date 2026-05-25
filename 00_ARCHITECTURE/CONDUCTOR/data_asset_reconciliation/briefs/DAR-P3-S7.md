---
session_id: DAR-P3-S7
phase: 3
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P1-S2]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_EXTRACT_DRY_RUN.md  # create
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - platform/supabase/migrations/
  - platform/migrations/
---

# DAR-P3-S7: MSR v5.0 pipeline dry-run

## Context

DAR-P1-S2 has updated all Python pipeline references to MSR v5.0 and EXPECTED_COUNT=573.
This session runs the MSR extractor in dry-run mode against the actual `MSR_v5_0.md` file
to confirm 573 signals extract cleanly before any live DB writes happen (those come in S8).

## Steps

1. Navigate to the Python sidecar:
   ```bash
   cd platform/python-sidecar
   ```

2. Run the MSR extractor in dry-run / count-only mode:
   ```bash
   python3 -m pipeline.extractors.msr_extractor --dry-run \
     --source 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md 2>&1
   ```
   If `--dry-run` flag doesn't exist, adapt to whatever the extractor supports for
   count-only validation (look at the extractor's argparse setup first).

3. Alternatively, run the msr_extractor test to trigger the extraction with fixture:
   ```bash
   cd platform && npx vitest run src/scripts/etl/__tests__/msr_parser.test.ts 2>&1
   ```
   This validates the TS-side parser. For the Python side:
   ```bash
   cd platform/python-sidecar
   python3 -c "
   from pipeline.extractors.msr_extractor import MSRExtractor
   e = MSRExtractor()
   signals = e.extract('../../025_HOLISTIC_SYNTHESIS/MSR_v5_0.md')
   print(f'signals_extracted: {len(signals)}')
   print(f'gate_check: {\"PASS\" if len(signals) == 573 else \"FAIL\"}')"
   ```

4. Capture the output. Create
   `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_EXTRACT_DRY_RUN.md`:
   ```yaml
   # MSR v5.0 Extract Dry-Run Report
   # Generated: [timestamp]

   source_file: 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
   signals_extracted: 573
   gate_check: PASS
   notes: [any warnings or anomalies observed]
   ```

5. Commit:
   ```
   dar: P3-S7 MSR v5.0 dry-run — 573 signals extracted, gate PASS
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_EXTRACT_DRY_RUN.md` → TRUE
- `grep 'signals_extracted: 573' MSR_EXTRACT_DRY_RUN.md` → match
- `grep 'gate_check: PASS' MSR_EXTRACT_DRY_RUN.md` → match
