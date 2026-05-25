---
session_id: DAR-P5-S19
phase: 5
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P5-S18]
may_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml
must_not_touch:
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
  - platform/migrations/
---

# DAR-P5-S19: B.3 grounding backfill — Nadi/BNN + Yogini/Tajaka new signals (SIG.MSR.515–573)

## Context

Signals SIG.MSR.515–573 are new additions in MSR v4.0 and v5.0 — covering Nadi/BNN
(Brighu Nadi Nakshatras) and Yogini/Tajaka systems. These are the most recently added
signals and most likely to lack grounding. This session grounds them.

## Steps

1. Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — sections:
   - Nadi astrology / BNN section (nakshatra-based Nadi designations)
   - Yogini Dasha (yogini planets, period sequence)
   - Tajaka / Varshaphal (annual chart for current year, Muntha, Sahams)

2. In `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md`, locate signals SIG.MSR.515 through SIG.MSR.573.
   These are the Nadi/BNN and Yogini/Tajaka signals.

3. For each signal in the Nadi/BNN group (SIG.MSR.515 onward to the boundary):
   - Read what fact the signal claims
   - Find the corresponding FORENSIC fact reference
   - Populate `l1_sources` with the FORENSIC v6_id
   - Set `grounding_status: GROUNDED`

4. For each signal in the Yogini/Tajaka group:
   - Same process as above

5. Update `GROUNDING_PROGRESS.yaml`:
   ```yaml
   grounded_nadi_bnn: DONE
   grounded_yogini_tajaka: DONE
   ```

6. Count remaining PENDING signals to validate all are grounded before S20 runs.

7. Commit:
   ```
   dar: P5-S19 B.3 grounding — Nadi/BNN + Yogini/Tajaka signals (SIG.MSR.515-573)
   ```

## Acceptance criteria

- `grep 'grounded_nadi_bnn: DONE' GROUNDING_PROGRESS.yaml` → match
- `grep 'grounded_yogini_tajaka: DONE' GROUNDING_PROGRESS.yaml` → match
