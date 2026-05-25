---
session_id: DAR-P4-S12
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

# DAR-P4-S12: chart_facts extractors — Yogi/Avayogi + Mrityu Bhaga + Chalit kinetic + Avastha + longevity

## Context

Continuation of chart_facts enhancement. This session adds 5 more missing categories.
All values must be sourced from `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`.

## Steps

1. Read `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — locate sections:
   - Yogi/Avayogi (the fortunate and inimical point degrees + planets)
   - Mrityu Bhaga (death point degrees for each planet in each sign)
   - Chalit kinetic (Chalit chart house positions — different from rasi positions)
   - Avastha (planetary states: bala, kumara, yuva, vriddha, mrita)
   - Longevity (ayurbala, longevity span, deha/jeeva lords)

2. Read the current `CHART_FACTS_EXTRACTION_v1_0.yaml` to understand how previous
   categories (from S11) were added.

3. Add `yogi_avayogi` category: yogi degree + planet + avayogi degree + planet,
   sourced from FORENSIC v8.0.

4. Add `mrityu_bhaga` category: list of planet → sign → critical degree triples,
   as declared in FORENSIC v8.0 for this chart.

5. Add `chalit_kinetic` category: Chalit house positions for all 9 planets + Lagna,
   where they differ from rasi positions.

6. Add `avastha` category: all planets with their avastha state (bala/kumara/yuva/vriddha/mrita)
   as declared in FORENSIC v8.0.

7. Add `longevity` category: ayurbala values, longevity estimate range, deha/jeeva lords.

8. Validate YAML:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml'))"
   ```

9. Commit:
   ```
   dar: P4-S12 chart_facts YAML — yogi_avayogi + mrityu_bhaga + chalit_kinetic + avastha + longevity
   ```

## Acceptance criteria

- `grep 'yogi_avayogi' CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- `grep 'mrityu_bhaga' CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- `grep 'chalit_kinetic' CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- `grep 'avastha' CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- YAML parses without error
