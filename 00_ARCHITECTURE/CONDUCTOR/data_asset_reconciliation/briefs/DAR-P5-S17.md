---
session_id: DAR-P5-S17
phase: 5
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P5-S16]
may_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml
must_not_touch:
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md  # read-only ground truth
  - platform/migrations/
---

# DAR-P5-S17: B.3 grounding backfill — Mercury + Jupiter + Venus + Saturn domains

## Context

S16 grounded Lagna/Sun/Moon/Mars. This session grounds the remaining 4 classic planetary
domains. Same methodology: read FORENSIC v8.0 sections, cite specific fact IDs, set status
to GROUNDED.

## Steps

1. Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — sections:
   - Mercury (house, sign, nakshatra, dignity, combustion status, budha-aditya yoga condition)
   - Jupiter (house, sign, nakshatra, retrograde, aspects, guru chandal condition)
   - Venus (house, sign, nakshatra, dignity, malavya yoga condition)
   - Saturn (house, sign, nakshatra, retrograde, sade sati status, shasha yoga condition)

2. For each MSR signal in the **Mercury domain**: populate `l1_sources` from FORENSIC.
   Set `grounding_status: GROUNDED`, `grounded_by: DAR-P5-S17`, `grounded_date: 2026-05-25`.

3. Repeat for **Jupiter domain** signals.

4. Repeat for **Venus domain** signals.

5. Repeat for **Saturn domain** signals.

6. Update `GROUNDING_PROGRESS.yaml`:
   ```yaml
   grounded_mercury: DONE
   grounded_jupiter: DONE
   grounded_venus: DONE
   grounded_saturn: DONE
   ```

7. Commit:
   ```
   dar: P5-S17 B.3 grounding — Mercury + Jupiter + Venus + Saturn signal domains
   ```

## Acceptance criteria

- `grep 'grounded_mercury: DONE' GROUNDING_PROGRESS.yaml` → match
- `grep 'grounded_jupiter: DONE' GROUNDING_PROGRESS.yaml` → match
- `grep 'grounded_venus: DONE' GROUNDING_PROGRESS.yaml` → match
- `grep 'grounded_saturn: DONE' GROUNDING_PROGRESS.yaml` → match
