---
session_id: DAR-P4-S13
phase: 4
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
may_touch:
  - 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml
must_not_touch:
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md  # read-only ground truth
  - platform/migrations/
  - 025_HOLISTIC_SYNTHESIS/
---

# DAR-P4-S13: chart_facts extractors — Narayana Dasha + Moola Dasha + Sudasa + Ishta/Kashta + Pancha-Vargeeya

## Context

Final batch of chart_facts YAML enhancements. Adds 5 more categories that were missing
from the initial extraction. All values from FORENSIC v8.0.

## Steps

1. Read `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — locate:
   - Narayana Dasha (sign-based dasha periods for Lagna + other relevant lagnas)
   - Moola Dasha (planet-based alternative dasha system)
   - Sudasa (another alternative dasha — if present in FORENSIC)
   - Ishta Phala / Kashta Phala (benefic/malefic force scores per planet)
   - Pancha-Vargeeya Bala (5-divisional strength per planet: Rasi+Hora+Drekkana+Navamsha+Dvadashamsha)

2. Read current `CHART_FACTS_EXTRACTION_v1_0.yaml` to understand cumulative structure.

3. Add `narayana_dasha` category: list of sign periods (Ar→Sc direction or Sc→Ar) with
   start/end years for the native, sourced from FORENSIC v8.0.

4. Add `moola_dasha` category: planetary sequence and period lengths as in FORENSIC v8.0.

5. Add `sudasa` category if present in FORENSIC v8.0. If FORENSIC v8.0 does not contain
   Sudasa data, mark the category as `status: EXTERNAL_COMPUTATION_REQUIRED` per B.10.

6. Add `ishta_kashta` category: ishta_phala and kashta_phala scores per planet.

7. Add `pancha_vargeeya` category: 5-divisional bala scores per planet.

8. Validate YAML:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml'))"
   ```

9. Bump YAML frontmatter version: `1.0` → `1.2` (reflects 15 new categories now complete).

10. Commit:
    ```
    dar: P4-S13 chart_facts YAML v1.2 — narayana_dasha + moola_dasha + sudasa + ishta_kashta + pancha_vargeeya
    ```

## Acceptance criteria

- `grep 'narayana_dasha' CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- `grep 'moola_dasha\|sudasa' CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- `grep 'ishta_kashta\|pancha_vargeeya' CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- YAML parses without error
