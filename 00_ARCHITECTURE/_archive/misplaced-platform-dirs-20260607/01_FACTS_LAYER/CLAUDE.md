# 01_FACTS_LAYER — Instructions

This folder holds L1 Facts — the single source of truth for all chart data, life events, and external references. Facts only. No interpretation.

## Current files (authoritative) — cleaned 2026-04-28 Phase 14.0

**Structured extraction (Phase 14C Stream B — 2026-04-29):**
- **`STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml`** — 589-fact structured projection of FORENSIC v8.0 into chart_facts schema (CURRENT)
- **`STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json`** — JSON Schema v1.0 for the YAML (CURRENT)
- Loader: `platform/python-sidecar/pipeline/extractors/forensic_extractor.py`
- Review: `verification_artifacts/PHASE_14C/forensic_extraction_review.html`

**Canonical L1 facts:**
- **`FORENSIC_ASTROLOGICAL_DATA_v8_0.md`** — unified Facts Layer (CURRENT; 32 sections; sole authoritative source for natal chart, KP, all dasha systems, special lagnas, sahams, yogas)
- **`LIFE_EVENT_LOG_v1_2.md`** — 36 dated life events + Swiss Ephemeris chart states (CURRENT)
- **`SADE_SATI_CYCLES_ALL.md`** — lifetime Sade Sati cycles pre-birth through Cycle 3 (CURRENT)

**Governance / spec:**
- **`EXTERNAL_COMPUTATION_SPEC_v2_0.md`** — remaining optional JH export specs (CURRENT governance)
- **`CGP_AUDIT_v1_0.md`** — Completeness Guarantee Protocol audit (CLOSED governance)

**Source references (supporting L1, not consumed directly):**
- **`SOURCES/JHORA_TRANSCRIPTION_v8_0_SOURCE.md`** — Jagannatha Hora export transcript; reconciliation authority for §12.1, §12.2, §6.6–§6.8, §26
- **`SOURCES/EVENT_CHART_STATES_v1_0.md`** — Swiss Ephemeris computed chart states for all 36 LEL events

**Ephemeris CSVs (Phase 14C promoted from DEAD_DATA → TRANSITIONAL; GCS-synced):**
- **`EPHEMERIS_MONTHLY_1900_2100.csv`** — monthly transit positions 1900–2100; GCS: `L1/ephemeris/`
- **`ECLIPSES_1900_2100.csv`** — eclipse catalog 1900–2100; authority source for `eclipses` table
- **`RETROGRADES_1900_2100.csv`** — retrograde stations 1900–2100; authority source for `retrogrades` table

**Archived (superseded — see `99_ARCHIVE/01_FACTS_LAYER/`):**
- `FORENSIC_DATA_v8_0_SUPPLEMENT.md` — merged into v8.0 (FIX_SESSION_003)
- `LIFE_EVENT_LOG_v1_1.md` — replaced by v1.2
- `EXTERNAL_COMPUTATION_SPEC_v1_0.md` — replaced by v2.0 + self-compute

## Planned / optional extensions

- **`EXTERNAL_REFERENCE_CARD.md`** — classical citations used across L2+ (per Architecture §G.1)
- Additional L1 rows only when marked with explicit provenance tags

## Non-negotiable rules

- Facts only. No interpretation, no narrative, no prediction.
- Every fact carries a data provenance tag (`source: swiss_ephemeris | jagannatha_hora | manual_derivation | external_astrologer | UNKNOWN`)
- No fabricated computations. Missing data = `[EXTERNAL_COMPUTATION_REQUIRED: <specification>]`
- Append-only by default. Corrections produce new versions; old versions go to `99_ARCHIVE/`.
- Stable IDs per Architecture §F namespace (`MET.`, `PLN.`, `HSE.`, `EVT.`, etc.)
