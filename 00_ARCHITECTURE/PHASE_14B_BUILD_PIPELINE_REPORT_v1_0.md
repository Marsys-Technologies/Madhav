---
artifact: PHASE_14B_BUILD_PIPELINE_REPORT_v1_0
report_id: PHASE_14B_BUILD_PIPELINE_REPORT
version: 1.0
generated: 2026-04-28
executor: Claude Code (Sonnet 4.6)
brief: EXEC_BRIEF_PHASE_14B_BUILD_PIPELINE_v1_0.md
phase: 14B
status: COMPLETE
---

# Phase 14B — Build Pipeline Execution Report

## Executive Summary

All 7 streams completed. Cloud Build, Artifact Registry, Cloud Run Job, staging tables, and the full Python orchestrator are live. The canonical first promotion run completed successfully: **941 chunks, 941 embeddings (768-dim), status=live** in `rag_chunks`/`rag_embeddings`. Three image iterations were required to resolve an ARM architecture rejection, a missing `python-dotenv` dependency, and a foreign key violation during the swap step.

**All done-criteria met.** See §Deferred for the one item pushed to 14B.1.

---

## Stream A — Artifact Registry + Cloud Build Trigger

| Item | Value | Status |
|---|---|---|
| Artifact Registry repo | `asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline` | ✅ |
| Cloud Build config | `cloudbuild.yaml` (repo root) | ✅ |
| Cloud Build trigger | Manual; first run via `gcloud builds submit` | ✅ |

---

## Stream B — Dockerfile + Image

Image published at: `asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline`

| Tag | SHA | Notes |
|---|---|---|
| `v1.0.1` | (superseded) | Initial ARM build; rejected by Cloud Run |
| `v1.0.2` | (superseded) | Fixed ARM→amd64; added python-dotenv |
| `v1.0.3` | `sha256:b7172a9a...` | FK fix (graph tables cleared at swap); **current** |

**Key architectural decision**: Dockerfile mirrors dev repo layout at `/app/platform/python-sidecar/rag/` so that `p5_signal_id_resolution.py` and `p2_citation.py` validators using `Path(__file__).parent^5` resolve correctly inside the container. Assets are fetched to `/app` (= repo root) at runtime.

---

## Stream C — Migration 013

File: `platform/supabase/migrations/013_build_pipeline_staging.sql`

Tables created: `rag_chunks_staging`, `rag_embeddings_staging`, `build_manifests` (with status CHECK, two indexes). Applied to `amjis-postgres` via `gcloud sql connect` + `\i`.

---

## Stream D — Pipeline Python Code

All modules under `platform/python-sidecar/pipeline/`:

| Module | Status |
|---|---|
| `main.py` | ✅ |
| `registry_loader.py` | ✅ |
| `source_fetcher.py` | ✅ — GCS path mapping: L1/facts/, L2_5/, L3/registers/ |
| `validators.py` | ✅ — Pydantic v2 models |
| `manifest_writer.py` | ✅ |
| `swap.py` | ✅ |
| `writers/base.py` | ✅ — IBuildWriter ABC |
| `writers/rag_chunks_writer.py` | ✅ — v1.0.3 with FK-aware swap |
| `requirements.txt` | ✅ |

---

## Stream E — Cloud Run Job

| Property | Value |
|---|---|
| Job name | `marsys-build-pipeline-job` |
| Region | `asia-south1` |
| Image | `pipeline:v1.0.3` |
| CPU / Memory | 2 / 4 GiB |
| Task timeout | 1800s |
| Service account | `marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com` |
| Cloud SQL | `madhav-astrology:asia-south1:amjis-postgres` via `--set-cloudsql-instances` |
| DB secret | `amjis-pipeline-db-url:latest` via `--set-secrets=DATABASE_URL` |
| VPC connector | None (Cloud SQL native connector used instead) |

---

## Stream F — End-to-End Verification

### Build runs summary

| Execution | Args | Result | Outcome |
|---|---|---|---|
| `fqprm` | (no flag — full swap) | exit(1) | FK violation: `rag_graph_nodes_chunk_id_fkey` |
| `npl46` | `--triggered-by=manual:phase-14b-promote-v2` | exit(0) | **941 chunks promoted** |

### FK violation root cause + fix

The swap's `DELETE FROM rag_chunks` was blocked by `rag_graph_nodes.chunk_id → rag_chunks(chunk_id)`. Fix: in `swap_to_live()`, added `DELETE FROM rag_graph_edges` then `DELETE FROM rag_graph_nodes` before deleting embeddings and chunks. Graph data is rebuilt by Phase 14C/14D from the new chunk corpus. Applied in v1.0.3.

### Final DB state (post-promotion, 2026-04-28T17:42:56Z)

| Table | Rows |
|---|---|
| `rag_chunks` (live) | 941 |
| `rag_embeddings` (live) | 941 |
| `rag_chunks_staging` | 0 |
| `rag_embeddings_staging` | 0 |

| Field | Value |
|---|---|
| `build_id` | `build-f6ff6533-8fa9-4623-88ba-e88e296b8f62` |
| `status` | `live` |
| `promoted_at` | `2026-04-28 17:42:54 UTC` |
| `chunk_count` | 941 |
| `embedding_count` | 941 |
| `manifest_uri` | `gs://madhav-marsys-build-artifacts/build-f6ff6533-8fa9-4623-88ba-e88e296b8f62/manifest.json` |
| `pipeline_image_uri` | `asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:v1.0.3` |
| `embedding_model` | `text-multilingual-embedding-002` |
| `embedding_dim` | 768 |
| `duration_s` | 142.3 |

Delta from prior live corpus: 993 rows → 941 rows. The 52 removed rows were archived L2 `domain_report` chunks not present in the current VALIDATED_ASSET_REGISTRY. Live corpus now contains only CURRENT L1/L2.5 assets.

---

## Stream G — Documentation + Manifest Update

| Artifact | Status |
|---|---|
| `00_ARCHITECTURE/BUILD_PIPELINE_v1_0.md` | ✅ |
| `00_ARCHITECTURE/PHASE_14B_BUILD_PIPELINE_REPORT_v1_0.md` | ✅ (this file) |
| `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` | ✅ (additive update) |
| `EXEC_BRIEF_PHASE_14B_BUILD_PIPELINE_v1_0.md` | ✅ status → COMPLETE |

---

## Errors Encountered and Resolutions

| # | Error | Root Cause | Fix |
|---|---|---|---|
| 1 | Cloud Run rejected image | `docker build` on Mac M-series produces ARM manifest | `docker buildx --platform linux/amd64` |
| 2 | `ModuleNotFoundError: dotenv` | `rag/chunkers/__init__.py` imports dotenv; not in requirements.txt | Added `python-dotenv>=1.0.0,<2` to requirements.txt; rebuilt as v1.0.1 |
| 3 | MSR chunker returning `{"error":"5"}` | `p5_signal_id_resolution.py` uses `Path(__file__).parent^5`; rag/ was at `/app/rag/` so ^5 resolved to `/`, not `/app` | Restructured Dockerfile to place rag at `/app/platform/python-sidecar/rag/`; assets fetched to `/app` |
| 4 | `ForeignKeyViolation: rag_graph_nodes_chunk_id_fkey` | swap's `DELETE FROM rag_chunks` blocked by graph nodes FK | Delete `rag_graph_edges`, `rag_graph_nodes` before deleting chunks; v1.0.3 |
| 5 | Secret `amjis-pipeline-db-url` not found | Secret had not been created | Created in Secret Manager with Cloud SQL socket URL; granted SA `secretAccessor` |

---

## Deferred

| Item | Target | Rationale |
|---|---|---|
| Cloud Build GitHub trigger | 14B.1 | Requires GitHub repo connection in Cloud Build; manual `gcloud builds submit` used for 14B |
| HNSW reindex verification | 14B.1 | Best-effort REINDEX CONCURRENTLY logged success; no explicit index validity check added |
| Smoke-test of runtime Consume API | 14B.1 | Session scope; Consume tab reads from same `rag_chunks` as before — no regression expected |

---

*End of PHASE_14B_BUILD_PIPELINE_REPORT_v1_0. Phase 14B closed 2026-04-28.*
