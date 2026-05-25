---
session_id: DAR-P7-S25
phase: 7
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P7-S24]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md  # create
must_not_touch:
  - platform/migrations/
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
---

# DAR-P7-S25: Cross-asset integrity check

## Context

Final verification before governance close. This session confirms that all CGM, UCN, and
CDLM signal references resolve to actual rows in the DB, and that school_convergence_index
is at the correct 4,011 rows.

## Steps

1. Extract all signal IDs cited in CGM:
   ```bash
   grep -oP 'SIG\.MSR\.\d+' 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md | sort -u > /tmp/cgm_refs.txt
   wc -l /tmp/cgm_refs.txt
   ```

2. Verify all CGM-cited signals exist in DB `msr_signals`:
   ```bash
   while IFS= read -r sig_id; do
     count=$(psql "$DATABASE_URL" -tAc "SELECT COUNT(*) FROM msr_signals WHERE signal_id='$sig_id';")
     if [ "$count" = "0" ]; then echo "MISSING: $sig_id"; fi
   done < /tmp/cgm_refs.txt
   ```
   Expected: 0 MISSING lines.

3. Repeat for UCN (`025_HOLISTIC_SYNTHESIS/UCN_v4_0.md`):
   ```bash
   grep -oP 'SIG\.MSR\.\d+' 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md | sort -u > /tmp/ucn_refs.txt
   # same verification loop
   ```

4. Repeat for CDLM (`025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md`):
   ```bash
   grep -oP 'SIG\.MSR\.\d+' 025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md | sort -u > /tmp/cdlm_refs.txt
   # same verification loop
   ```

5. school_convergence_index row count:
   ```bash
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM school_convergence_index;"
   ```
   Expected: 4,011

6. Create `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md`:
   ```yaml
   # Cross-Asset Integrity Report — Phase 7 S25
   # Generated: [timestamp]

   cgm_signal_refs_checked: <N>
   cgm_msr_refs: ALL_VALID
   ucn_signal_refs_checked: <N>
   ucn_msr_refs: ALL_VALID
   cdlm_signal_refs_checked: <N>
   cdlm_msr_refs: ALL_VALID
   school_convergence_rows: 4011
   integrity_status: PASS
   ```

7. Commit:
   ```
   dar: P7-S25 cross-asset integrity check PASS — CGM/UCN/CDLM refs valid; school_convergence=4011
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md` → TRUE
- `grep 'cgm_msr_refs: ALL_VALID' CROSS_ASSET_INTEGRITY_REPORT.md` → match
- `grep 'ucn_msr_refs: ALL_VALID' CROSS_ASSET_INTEGRITY_REPORT.md` → match
- `grep 'school_convergence_rows: 4011' CROSS_ASSET_INTEGRITY_REPORT.md` → match
