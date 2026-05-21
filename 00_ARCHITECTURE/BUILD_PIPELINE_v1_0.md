---
artifact: BUILD_PIPELINE_v1_0
canonical_id: BUILD_PIPELINE_v1_0
version: 1.0
status: CURRENT
authored_by: Claude Code (Sonnet 4.6)
authored_at: 2026-04-28
phase: 14B
---

# BUILD_PIPELINE_v1_0 — MARSYS-JIS Build Pipeline Canonical Specification

## §1 — Overview

The MARSYS build pipeline is a Cloud Run Job that transforms GCS source assets into the live Cloud SQL `rag_chunks` + `rag_embeddings` corpus via a staging-then-swap discipline. Every run is identified by a `build_id` (UUID) and produces an immutable manifest in GCS. The pipeline runs outside of the TypeScript runtime — live tables are only touched at the atomic swap step.

### Pipeline invocation

```
gs://madhav-marsys-sources
  └── VALIDATED_ASSET_REGISTRY_v1_0.json
        ↓ registry_loader
  [CURRENT assets]
        ↓ source_fetcher (to /app workspace)
  [Local markdown files]
        ↓ chunkers (rag/chunkers/*)
  [Chunk objects]
        ↓ Vertex AI text-multilingual-embedding-002
  [768-dim float32 vectors]
        ↓ RAGChunksWriter.write_chunks → rag_chunks_staging + rag_embeddings_staging
        ↓ RAGChunksWriter.validate_staging
        ↓ manifest_writer → gs://madhav-marsys-build-artifacts/<build_id>/manifest.json
        ↓ RAGChunksWriter.swap_to_live (transactional)
  rag_chunks + rag_embeddings (live)
```

---

## §2 — GCP Resources

| Resource | Name | Region | Notes |
|---|---|---|---|
| Artifact Registry repo | `marsys-pipeline` | `asia-south1` | Docker; format=DOCKER |
| Docker image | `asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline` | — | Tags: `vX.Y.Z` + `latest` |
| Cloud Run Job | `marsys-build-pipeline-job` | `asia-south1` | 2 vCPU, 4 GiB; task timeout 1800s |
| Service Account | `marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com` | — | See §5 for IAM |
| Cloud SQL | `madhav-astrology:asia-south1:amjis-postgres` | `asia-south1` | Connected via `--set-cloudsql-instances` |
| Sources bucket | `gs://madhav-marsys-sources` | `asia-south1` | Read-only for pipeline |
| Artifacts bucket | `gs://madhav-marsys-build-artifacts` | `asia-south1` | Manifest writes |
| Secret | `amjis-pipeline-db-url` | — | Secret Manager; Cloud SQL socket URL |

---

## §3 — Database Schema

Migration: `platform/supabase/migrations/013_build_pipeline_staging.sql`

### Staging tables

```sql
-- Mirrors of live tables (including all indexes and constraints)
rag_chunks_staging        -- LIKE rag_chunks INCLUDING ALL
rag_embeddings_staging    -- LIKE rag_embeddings INCLUDING ALL
```

### Build manifests

```sql
CREATE TABLE build_manifests (
  build_id            TEXT PRIMARY KEY,
  triggered_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  triggered_by        TEXT NOT NULL,         -- e.g. "manual:email", "scheduler"
  registry_fingerprint TEXT NOT NULL,
  pipeline_image_uri  TEXT NOT NULL,
  embedding_model     TEXT NOT NULL,
  embedding_dim       INTEGER NOT NULL,
  chunk_count         INTEGER NOT NULL,
  embedding_count     INTEGER NOT NULL,
  status              TEXT NOT NULL CHECK (status IN ('staging','live','rolled_back','failed')),
  manifest_uri        TEXT NOT NULL,
  promoted_at         TIMESTAMPTZ,
  notes               TEXT
);
```

---

## §4 — Code Layout

```
platform/python-sidecar/
├── Dockerfile.pipeline              # Cloud Run Job image
├── pipeline/
│   ├── __init__.py
│   ├── main.py                      # Orchestrator; CLI entry point
│   ├── registry_loader.py           # Reads VALIDATED_ASSET_REGISTRY from GCS
│   ├── source_fetcher.py            # Downloads assets to workspace; GCS path mapping
│   ├── validators.py                # Pydantic v2 models for registry + frontmatter
│   ├── manifest_writer.py           # Writes build manifest JSON to GCS
│   ├── swap.py                      # Thin wrapper for swap_to_live
│   ├── requirements.txt
│   └── writers/
│       ├── __init__.py
│       ├── base.py                  # IBuildWriter abstract base class
│       └── rag_chunks_writer.py     # RAGChunksWriter: L1/L2.5/L3 → rag_chunks
```

### Chunker registry (main.py `_build_chunker_registry`)

| Asset path | doc_type | Chunker |
|---|---|---|
| `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` | `l1_fact` | `chunk_l1_facts` |
| `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` | `msr_signal` | `chunk_msr_signals` |
| `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` | `ucn_section` | `chunk_ucn_sections` |
| `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` | `cdlm_cell` | `chunk_cdlm_cells` |
| `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` | `cgm_node` | `chunk_cgm_nodes` |

14C/14D/14E register additional entries in this dict; the orchestrator and writer interface do not change.

---

## §5 — IAM Bindings

| Principal | Resource | Role | Purpose |
|---|---|---|---|
| `marsys-pipeline-writer` SA | `madhav-marsys-sources` bucket | `roles/storage.objectViewer` | Read source assets |
| `marsys-pipeline-writer` SA | `madhav-marsys-build-artifacts` bucket | `roles/storage.objectCreator` | Write manifests |
| `marsys-pipeline-writer` SA | `amjis-postgres` Cloud SQL | `roles/cloudsql.client` | Connect via native connector |
| `marsys-pipeline-writer` SA | Project | `roles/aiplatform.user` | Vertex AI embeddings |
| `marsys-pipeline-writer` SA | `amjis-pipeline-db-url` secret | `roles/secretmanager.secretAccessor` | Read DB URL |
| Cloud Build SA | Project | Standard Cloud Build roles | Build + push image |

---

## §6 — Container Layout and Validator Path Resolution

The Dockerfile mirrors the dev repo layout inside the container so that `p5_signal_id_resolution.py` and `p2_citation.py` validators (which use `Path(__file__).parent^5` to find source files) resolve correctly:

```
/app/                                        ← WORKDIR = repo_root
  platform/python-sidecar/
    rag/                                     ← 5 levels up from rag/validators/ = /app
    pipeline/
  01_FACTS_LAYER/                            ← fetched at runtime by source_fetcher
  025_HOLISTIC_SYNTHESIS/                    ← fetched at runtime by source_fetcher
```

At runtime `fetch_all_assets()` downloads assets to `workspace_root=/app`. After chunking, the `01_FACTS_LAYER/` and `025_HOLISTIC_SYNTHESIS/` subdirectories are removed via `shutil.rmtree`. The `platform/` subtree is never cleaned.

---

## §7 — Swap Protocol

`RAGChunksWriter.swap_to_live(build_id)`:

1. **Safety gate**: abort if `staging_count < 0.5 × live_count` (prevents catastrophic partial-build promotion).
2. **Transaction**:
   ```sql
   BEGIN;
   DELETE FROM rag_graph_edges;      -- FK dependent on rag_graph_nodes
   DELETE FROM rag_graph_nodes;      -- FK dependent on rag_chunks
   DELETE FROM rag_embeddings;
   DELETE FROM rag_chunks;
   INSERT INTO rag_chunks SELECT * FROM rag_chunks_staging;
   INSERT INTO rag_embeddings SELECT * FROM rag_embeddings_staging;
   TRUNCATE rag_chunks_staging, rag_embeddings_staging;
   UPDATE build_manifests SET status='live', promoted_at=NOW() WHERE build_id=<id>;
   UPDATE build_manifests SET status='rolled_back' WHERE status='live' AND build_id!=<id>;
   COMMIT;
   ```
3. **Best-effort HNSW reindex**: `REINDEX INDEX CONCURRENTLY idx_rag_embeddings_hnsw` (non-blocking; skipped on error with warning).

Note: `rag_graph_edges` and `rag_graph_nodes` are cleared at swap because they reference `rag_chunks` via FK. Graph data is rebuilt by Phase 14C/14D.

---

## §8 — CLI

```bash
# Full run (embed + write + swap)
gcloud run jobs execute marsys-build-pipeline-job \
  --args="--triggered-by=manual:email" \
  --region=asia-south1 --project=madhav-astrology --wait

# Dry run (chunk only, no writes)
... --args="--dry-run --triggered-by=ci"

# Stage only (no swap)
... --args="--skip-swap --triggered-by=manual:email"

# Custom registry URI
... --args="--registry-uri=gs://madhav-marsys-sources/00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json"
```

---

## §9 — Build Manifest Schema

Written to `gs://madhav-marsys-build-artifacts/<build_id>/manifest.json`:

```json
{
  "build_id": "build-<uuid>",
  "triggered_by": "manual:email",
  "triggered_at": "<iso8601>",
  "registry_fingerprint": "<sha256>",
  "pipeline_image_uri": "asia-south1-docker.pkg.dev/.../pipeline:<build_id>",
  "embedding_model": "text-multilingual-embedding-002",
  "embedding_dim": 768,
  "chunk_count": 941,
  "embedding_count": 941,
  "status": "live",
  "asset_sha256_map": {
    "01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md": "<sha256>",
    ...
  }
}
```

---

## §10 — Adding New Writers (14C/14D/14E pattern)

1. Create `platform/python-sidecar/pipeline/writers/<name>_writer.py` implementing `IBuildWriter`.
2. Add entry to `_build_chunker_registry()` in `main.py` for each new asset path.
3. Instantiate and call the new writer inside `run_build()` after step 7 (`staging_written`).
4. Add required staging table migration (`014_...sql`).
5. No changes to `IBuildWriter`, `swap.py`, `manifest_writer.py`, or the orchestrator flow.

---

*End of BUILD_PIPELINE_v1_0. Phase 14B (2026-04-28). Status: CURRENT.*
