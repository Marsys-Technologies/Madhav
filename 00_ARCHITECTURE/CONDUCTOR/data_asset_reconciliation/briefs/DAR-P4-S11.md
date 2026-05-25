---
session_id: DAR-P4-S11
phase: 4
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
may_touch:
  - 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml
  - platform/python-sidecar/tools/chart_facts_extractor.py
must_not_touch:
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md  # read-only ground truth
  - platform/migrations/
  - 025_HOLISTIC_SYNTHESIS/
---

# DAR-P4-S11: chart_facts extractors — Ashtakavarga + Sthira Karakas + Upagrahas + Bhrigu Bindu

## Context

The DAR audit found 15 FORENSIC sections absent from `CHART_FACTS_EXTRACTION_v1_0.yaml`.
This session adds the first 4 missing categories. All values must come from
`01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — the ground-truth L1 fact source.
Do NOT derive or compute values; find them in FORENSIC v8.0 and copy them into the YAML.

## Steps

1. Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` in full — locate sections:
   - Ashtakavarga (bindu scores for each planet + Lagna, sarvashtakavarga total)
   - Sthira Karakas (Atmakaraka, Amatyakaraka, etc. — fixed-planet assignment)
   - Upagrahas (Mandi/Gulika, Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu)
   - Bhrigu Bindu (the midpoint between Moon and Rahu's dispositor)

2. Read `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` — understand existing
   structure (category → facts list).

3. Add `ashtakavarga` category with all planet bindu scores and sarvashtakavarga total
   sourced verbatim from FORENSIC v8.0. Each fact must include `forensic_ref:` field.

4. Add `sthira_karaka` category with all 7 karakas (AK through GK / DK) as listed in
   FORENSIC v8.0.

5. Add `upagraha` category with all 6 upagraha positions as listed in FORENSIC v8.0.

6. Add `bhrigu_bindu` category with the BB degree + nakshatra + navamsha as in FORENSIC v8.0.

7. Validate YAML syntax:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml'))"
   ```

8. Commit:
   ```
   dar: P4-S11 chart_facts YAML — ashtakavarga + sthira_karaka + upagraha + bhrigu_bindu
   ```

## Acceptance criteria

- `grep -q 'ashtakavarga' 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- `grep -q 'sthira_karaka' 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- `grep -q 'upagraha' 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- `grep -q 'bhrigu_bindu' 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` → match
- YAML parses without error
