# 01_FACTS_LAYER — Instructions

L1 facts only — no interpretation, narrative or prediction.

- **Live chart facts** are the `chart_facts` DB table built by the L1 `ga_*` writers; this folder holds supporting sources. The old FORENSIC v8.0 markdown is a cold benchmark at `99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md`.
- Current files: `LIFE_EVENT_LOG_v1_2.md` (life events), `LIFE_EVENT_LOG_FACTS_ONLY_v1_0.md`, `LEL_HELD_OUT_PARTITION_v1_0.md`, `SADE_SATI_CYCLES_ALL.md`, `EXTERNAL_COMPUTATION_SPEC_v2_0.md`, ephemeris/eclipse/retrograde CSVs (1900–2100), `STRUCTURED/` (FORENSIC extraction YAML + schema), `SOURCES/` (JH transcription, event chart states).

Rules:
- Every fact carries a provenance tag; missing data = `[EXTERNAL_COMPUTATION_REQUIRED: <spec>]`, never invented.
- Append-only: corrections produce a new version; superseded versions move to `99_ARCHIVE/`.
