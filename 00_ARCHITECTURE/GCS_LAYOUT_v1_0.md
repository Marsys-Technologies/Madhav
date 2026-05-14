---
artifact: GCS_LAYOUT_v1_0.md
version: 1.0
status: CURRENT
purpose: Canonical bucket structure for marsys source artifacts
parent_authoritative_source: VALIDATED_ASSET_REGISTRY_v1_0.json
created_at: 2026-04-28
created_by: Phase_14A_GCS_Foundation
---

# GCS Layout — MARSYS Source Buckets

## Overview

Two GCS buckets form the MARSYS storage foundation, both in region `asia-south1` (co-located with Cloud SQL `amjis-postgres` in `madhav-astrology:asia-south1`).

| Bucket | Purpose | Status |
|---|---|---|
| `gs://madhav-marsys-sources` | L1, L2.5, L3 source artifacts — authoring source-of-truth mirror | CURRENT (live since Phase 14A) |
| `gs://madhav-marsys-build-artifacts` | Pipeline outputs, processed embeddings, build reproducibility | CURRENT (live since Phase 14A) |

**Versioning convention:** filenames carry version strings (e.g., `MSR_v3_0.md`). GCS object versioning is enabled on both buckets, preserving the history of every overwrite within a given path. Do not increment GCS paths for version bumps — overwrite in place; prior versions are retrievable via GCS object versioning.

---

## `gs://madhav-marsys-sources` — Source Artifact Bucket

### Properties

| Property | Value |
|---|---|
| Storage class | STANDARD |
| Region | asia-south1 |
| Object versioning | ENABLED (every overwrite preserved — audit trail) |
| Lifecycle — versions | No deletion (source history is legally important) |
| Public access prevention | enforced |
| Uniform bucket-level access | enabled |
| Labels | `purpose=marsys-l1-l25-l3-sources`, `env=prod` |

### IAM

| Principal | Role | Scope |
|---|---|---|
| `marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com` | `roles/storage.objectCreator` | Sources bucket only — write, no delete |
| `marsys-runtime-reader@madhav-astrology.iam.gserviceaccount.com` | `roles/storage.objectViewer` | Sources bucket only — read only |

### Layout

```
gs://madhav-marsys-sources/
├── L1/
│   ├── facts/
│   │   ├── FORENSIC_ASTROLOGICAL_DATA_v8_0.md       ← canonical_id: FORENSIC
│   │   ├── LIFE_EVENT_LOG_v1_2.md                   ← canonical_id: LEL
│   │   ├── SADE_SATI_CYCLES_ALL.md
│   │   ├── EXTERNAL_COMPUTATION_SPEC_v2_0.md
│   │   └── CGP_AUDIT_v1_0.md
│   ├── ephemeris/
│   │   ├── EPHEMERIS_MONTHLY_1900_2100.csv           ← coverage gap GAP.L1.01 (not yet generated)
│   │   ├── ECLIPSES_1900_2100.csv                   ← coverage gap (not yet generated)
│   │   └── RETROGRADES_1900_2100.csv                ← coverage gap (not yet generated)
│   └── sources/
│       ├── EVENT_CHART_STATES_v1_0.md
│       └── JHORA_TRANSCRIPTION_v8_0_SOURCE.md
├── L2_5/
│   ├── MSR_v3_0.md                                  ← canonical_id: MSR
│   ├── UCN_v4_0.md                                  ← canonical_id: UCN
│   ├── CDLM_v1_1.md                                 ← canonical_id: CDLM
│   ├── RM_v2_0.md                                   ← canonical_id: RM
│   ├── CGM_v9_0.md                                  ← canonical_id: CGM
│   └── RED_TEAM_L2_5_v1_0.md
├── L3/
│   └── registers/
│       ├── PATTERN_REGISTER_v1_0.json
│       ├── PATTERN_REGISTER_v1_0.md                 ← companion narrative
│       ├── RESONANCE_REGISTER_v1_0.json
│       ├── RESONANCE_REGISTER_v1_0.md               ← companion narrative
│       ├── CONTRADICTION_REGISTER_v1_0.json
│       ├── CONTRADICTION_REGISTER_v1_0.md           ← companion narrative
│       ├── CLUSTER_ATLAS_v1_0.json
│       ├── CLUSTER_ATLAS_v1_0.md                    ← companion narrative
│       └── INDEX.json
└── L8/                                              ← L8 added at M8-A-S1 (2026-05-14)
    ├── classical_texts/
    │   ├── tier1/
    │   │   ├── bphs_chunks.jsonl                    ← BPHS (Brihat Parashara Hora Shastra)
    │   │   └── phaladeepika_chunks.jsonl
    │   ├── tier2/
    │   │   ├── saravali_chunks.jsonl
    │   │   ├── uttara_kalamrita_chunks.jsonl
    │   │   └── jaimini_sutra_chunks.jsonl
    │   └── tier3/
    │       ├── prashna_marga_chunks.jsonl
    │       ├── hora_sara_chunks.jsonl
    │       ├── kp_vols_chunks.jsonl
    │       ├── brihat_jataka_chunks.jsonl
    │       └── brihat_samhita_chunks.jsonl
    ├── nadi_bnn/
    │   ├── bhrigu_nandi_nadi_chunks.jsonl
    │   ├── chandra_kala_nadi_chunks.jsonl
    │   └── dhruva_nadi_sampler_chunks.jsonl
    └── registries/
        ├── CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md
        └── CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json
```

    └── L9/                                              ← L9 added at M9-A-S1 (2026-05-14)
        ├── school_analyses/
        │   ├── parashari_analysis.json
        │   ├── jaimini_analysis.json
        │   ├── tajika_analysis.json
        │   ├── kp_analysis.json
        │   ├── nadi_analysis.json
        │   ├── bnn_analysis.json
        │   └── yogini_analysis.json
        └── convergence/
            ├── convergence_scores.json
            └── school_disagreement_register.json
```

*(L2_5/ also receives MSR_v5_0.md at M9-A-S1 close: `gs://madhav-marsys-sources/L2_5/MSR_v5_0.md`)*

**Notes:**
- `L1/ephemeris/` paths are reserved; files don't exist locally yet (coverage gaps). The sync script skips non-existent files.
- L3 `.md` companion files exist on disk alongside `.json` registry entries; both are included in the sync per this layout.
- L2 (`02_ANALYTICAL_LAYER/`) is formally archived — NOT included in this bucket. Archived per Phase 14F.
- L4 does not exist (single-native; federated discovery is M3+ work).
- L5 (`06_LEARNING_LAYER/`) is not included in this bucket in Phase 14A. Learning Layer sync scope is a separate decision.
- L9 (`09_MULTI_SCHOOL_TRIANGULATION/`) added at M9-A-S1 (2026-05-14) — multi-school analysis JSON outputs and convergence metrics.

---

## `gs://madhav-marsys-build-artifacts` — Build Artifact Bucket

### Properties

| Property | Value |
|---|---|
| Storage class | STANDARD (first 90 days) → NEARLINE (after 90 days) |
| Region | asia-south1 |
| Object versioning | ENABLED |
| Lifecycle — class transition | STANDARD → NEARLINE after 90 days |
| Lifecycle — noncurrent version deletion | Delete noncurrent versions older than 365 days |
| Public access prevention | enforced |
| Uniform bucket-level access | enabled |
| Labels | `purpose=marsys-build-pipeline-output`, `env=prod` |

### IAM

| Principal | Role | Scope |
|---|---|---|
| `marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com` | `roles/storage.objectAdmin` | Artifacts bucket — full control of objects |

### Intended Layout (populated by Phase 14B+)

```
gs://madhav-marsys-build-artifacts/
└── runs/
    └── <build-run-id>/
        ├── embeddings/
        │   └── *.json          ← chunk embeddings produced by rag pipeline
        ├── chunks/
        │   └── *.json          ← chunked source documents
        └── manifest.json       ← build manifest: source hashes, config, timestamps
```

This layout is defined in Phase 14B (Build Pipeline). The bucket exists now to receive those outputs.

---

## Naming Conventions

1. **Source file names** carry the artifact version in the filename (`_v3_0`, `_v1_2`, etc.). Do not create version-less paths for versioned artifacts.
2. **GCS path = layer prefix + flat filename**. No subdirectory nesting beyond the layout above.
3. **Object versioning** is the history mechanism — do not create parallel `_old`, `_backup` objects. Overwrite in place.
4. **Build artifact paths** always include a `<build-run-id>` component for isolation. Runs are immutable once written.

---

## Transition Status (Phase 14A → 14C)

The CAPABILITY_MANIFEST.json entries for CURRENT assets now carry both `path` (local filesystem) and `gcs_uri` fields, with `status: TRANSITIONAL`. The platform runtime (`platform/src/`) still reads from local paths until Phase 14C cuts over to GCS reads. The transition flips `TRANSITIONAL → CURRENT` and removes the local-path dependency from the runtime.

---

*End GCS_LAYOUT_v1_0.md. Governed by Phase 14A; updated at each phase that modifies bucket structure.*
