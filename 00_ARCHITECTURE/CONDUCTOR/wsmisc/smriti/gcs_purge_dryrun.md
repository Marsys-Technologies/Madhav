---
session: gcs-purge
type: DRY_RUN_REPORT
timestamp: 2026-06-05T06:59:00+05:30
tier: 2
---

# GCS Purge DRY-RUN Report

## §1 Bucket Inventory (project: madhav-astrology)

All buckets enumerated via `gcloud storage buckets list`:

| Bucket | Purpose | Classification |
|--------|---------|---------------|
| `madhav-astrology-chart-documents` | Chart document assets per-chart-id | SCAN_FOR_ORPHANS |
| `madhav-astrology-chat-attachments` | User chat attachment uploads | SCAN_FOR_ORPHANS |
| `madhav-astrology-tf-state` | Terraform remote state | KEEP (infrastructure) |
| `madhav-astrology.appspot.com` | Firebase/App Engine bucket | KEEP (infrastructure) |
| `madhav-astrology_cloudbuild` | Cloud Build artifacts | KEEP (infrastructure) |
| `madhav-brahma-olap` | Brahma OLAP/analytics bucket (new) | KEEP (Brahma asset) |
| `madhav-marsys-sources` | Source documents / L-layer assets | KEEP (Brahma asset) |
| `marsys-jis-build-state` | Build state tracker (legacy arc) | KEEP (still active) |
| `marsys-tracker-public` | Public tracker website | KEEP (infrastructure) |
| `staging.madhav-astrology.appspot.com` | App Engine staging | KEEP (infrastructure) |

### Buckets expected by brief that do NOT exist:
- `gs://madhav-marsys-build-artifacts` — 404 NOT FOUND. Bucket was never created or was already deleted by the cleanup arc. **No action needed.**
- `gs://chart-attachments` — 404 NOT FOUND. Actual bucket is `madhav-astrology-chat-attachments`.
- `gs://chart-documents` — 404 NOT FOUND. Actual bucket is `madhav-astrology-chart-documents`.

**Tier-2 disposition decision:** The brief's expected bucket names (`madhav-marsys-build-artifacts`, `chart-attachments`, `chart-documents`) were the legacy names. The actual buckets use the `madhav-astrology-` prefix. This is a naming resolution, not a missing-bucket problem. Confidence: 0.92. Decision logged to smriti.

---

## §2 Content Classification

### `madhav-astrology-chart-documents`

Contents: one chart folder `charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/`

**Orphan check:** Chart ID `362f9f17-95a5-490b-a5a7-027d3e0efda0` queried against `charts` table → **0 rows** (does not exist by `id` OR `chart_id`).

Only valid chart in DB: `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek Mohanty).

| GCS Path | Classification | Reason |
|----------|---------------|--------|
| `charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/` (13 objects: L1, L2, L2.5, L3 layers) | **DELETE — ORPHAN** | chart_id not in `charts` table; orphaned pre-Brahma chart document set |

Objects to delete (13 total):
```
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L1/cgp_audit_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L1/event_chart_states_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L1/external_computation_spec_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L1/forensic_data_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L1/forensic_data_v7_supplement_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L1/life_event_log_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L1/sade_sati_cycles_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2.5/cdlm_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2.5/cgm_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2.5/msr_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2.5/rm_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2.5/ucn_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2/deep_analysis_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2/matrix_dasha_periods_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2/matrix_divisionals_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2/matrix_houses_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2/matrix_planets_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L2/matrix_signs_v1.0.md
gs://madhav-astrology-chart-documents/charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/L3/report_financial_v1.0.md
```

### `madhav-astrology-chat-attachments`

Contents: **empty** (no objects). No action needed.

### `madhav-marsys-sources`

Prefixes present: `00_ARCHITECTURE/`, `025_HOLISTIC_SYNTHESIS/`, `035_DISCOVERY_LAYER/`, `L1/`, `L2_5/`, `L3/`, `L8/`, `L9/`

**Classification against DELETE list** (brief: `l25/, rag/, msr/, chart_facts/, classical/, panchanga_daily/, build_manifests/`):

| Prefix | Classification | Reason |
|--------|---------------|--------|
| `L1/` | **KEEP** | Brahma L-layer structure (ephemeris, facts) |
| `L2_5/` | **KEEP** | Brahma L-layer structure (holistic synthesis) — note: `L2_5` is the Brahma name for what was `l25/` |
| `L3/` | **KEEP** | Brahma L-layer structure (discovery registers) |
| `L8/` | **KEEP** | Classical texts (BPHS, Jaimini, etc.) |
| `L9/` | **KEEP** | Multi-school convergence |
| `00_ARCHITECTURE/` | **KEEP** | Registry files |
| `025_HOLISTIC_SYNTHESIS/` | **KEEP** | Legacy source copies (these are source inputs, not build artifacts) |
| `035_DISCOVERY_LAYER/` | **KEEP** | Legacy source copies (source inputs) |

**No legacy prefixes found.** The bucket was renamed and reorganized — `L2_5/` is the successor to `l25/` (already migrated). No deletes needed in this bucket.

---

## §3 UNCLASSIFIED Prefixes

**Zero UNCLASSIFIED prefixes.** All prefixes classified with confidence ≥ 0.6.

Per orchestrator instructions: "If zero UNCLASSIFIED: proceed with deletes."

---

## §4 Delete Candidate Summary

| Bucket | Delete Count | Keep Count | Notes |
|--------|-------------|------------|-------|
| `madhav-astrology-chart-documents` | 19 objects (1 orphan folder) | 0 | Orphan chart-id not in DB |
| `madhav-astrology-chat-attachments` | 0 | 0 | Already empty |
| `madhav-marsys-sources` | 0 | 35+ objects | All KEEP |
| All other buckets | 0 | - | Infrastructure, not in scope |

**Total objects to delete: 19 (all in one orphaned chart folder)**

---

## §5 Auto-resume decision

Zero UNCLASSIFIED prefixes → auto-resume per orchestrator instructions. Proceeding to execute deletes.

---
