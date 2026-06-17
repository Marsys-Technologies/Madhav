---
brief_id: EXEC_BRIEF_PHASE_14B_BUILD_PIPELINE
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_14B_BUILD_PIPELINE_v1_0.md and execute it."
phase: 14B
phase_name: Cloud Build + Cloud Run Jobs orchestration — GCS sources to Postgres rag_chunks via staging-then-swap
risk_classification: MEDIUM (new infrastructure across Cloud Build, Artifact Registry, Cloud Run Jobs, Cloud SQL; runtime is unaffected because pipeline writes to staging tables and atomically swaps)
parallelizable_with: [14C/14D/14E AUTHORING (not execution); 14F.1]
must_complete_before: [14C, 14D, 14E execution; 14G]
depends_on:
  - EXEC_BRIEF_PHASE_14A_GCS_FOUNDATION_v1_0.md (COMPLETE)
  - EXEC_BRIEF_PHASE_14A_FOLLOWUP_IAM_HARDENING_v1_0.md (COMPLETE)
output_artifacts:
  - 00_ARCHITECTURE/BUILD_PIPELINE_v1_0.md (NEW canonical spec)
  - 00_ARCHITECTURE/PHASE_14B_BUILD_PIPELINE_REPORT_v1_0.md (NEW execution report)
---

# EXEC_BRIEF — Phase 14B — Build Pipeline (Cloud Build + Cloud Run Jobs)

## Mission

Stand up the orchestration layer that turns the GCS sources bucket into the live Cloud SQL `rag_chunks`/`rag_embeddings` corpus. Pipeline reads `VALIDATED_ASSET_REGISTRY_v1_0.json` from `gs://madhav-marsys-sources`, fetches every CURRENT asset, validates frontmatter against Pydantic schemas, chunks via the existing `platform/python-sidecar/rag/chunkers/*` modules, embeds via Vertex AI `text-multilingual-embedding-002` (768-dim, ADC), writes to **staging tables** in Cloud SQL, runs a manifest diff against the live tables, and atomically swaps. Every build emits a manifest JSON to `gs://madhav-marsys-build-artifacts/build-<id>/manifest.json` with full provenance for rollback and audit.

Three architectural commitments:

1. **Existing chunking + embedding logic is reused, not rewritten.** The 6 chunkers in `platform/python-sidecar/rag/chunkers/` and the embedder at `platform/python-sidecar/rag/embed.py` already implement content-hash idempotency, halt-on-error, and the Vertex AI 768-dim path. 14B wraps them, it does not replace them.

2. **Staging-then-swap is non-negotiable.** Build writes to `rag_chunks_staging` + `rag_embeddings_staging`, validates row counts and schema, then a single transaction does `BEGIN; TRUNCATE rag_chunks CASCADE; INSERT ... FROM staging; UPDATE manifest fingerprint; COMMIT`. Pipeline failure leaves live tables untouched. Runtime keeps serving queries throughout.

3. **Future-proofing via writer abstraction.** 14B implements `RAGChunksWriter` against an abstract `IBuildWriter` interface. 14C/14D/14E will plug in `ChartFactsWriter`, `UCNEntriesWriter`, etc. — same orchestrator, same staging discipline, additional writers wired by configuration.

This brief explicitly does NOT alter `platform/src/**` (TypeScript runtime) or any feature flag. Runtime keeps reading from the same `rag_chunks` it does today; what changes is *who writes to it* (now Cloud Run Job, not a local script run).

## Pre-flight gate

1. Verify Phase 14A is COMPLETE — frontmatter check on `EXEC_BRIEF_PHASE_14A_GCS_FOUNDATION_v1_0.md`.
2. Verify Phase 14A.1 is COMPLETE — frontmatter check on `EXEC_BRIEF_PHASE_14A_FOLLOWUP_IAM_HARDENING_v1_0.md`. Confirms `marsys-pipeline-writer` has `objectViewer` on `madhav-marsys-sources`.
3. Verify GCS sources bucket has the 22 CURRENT assets — `gcloud storage ls gs://madhav-marsys-sources/` returns 22+ entries.
4. Verify Cloud SQL `amjis-postgres` is reachable from the executor's environment (Auth Proxy or VPC).
5. Verify `gcloud auth list` shows authenticated principal with `roles/cloudbuild.builds.editor`, `roles/run.admin`, `roles/artifactregistry.admin`, `roles/cloudsql.admin`.
6. Verify migrations through 012 are applied to `amjis-postgres` (check `pg_migrations` or equivalent).
7. Confirm git working tree is clean.

If any fail, halt with actionable message.

## Scope

**`may_touch` (cloud resources):**
- New Artifact Registry repository: `marsys-pipeline` in `asia-south1` (Docker image hosting).
- New Cloud Build trigger: `marsys-build-pipeline` (manual + path-filter on push to main; create disabled and document manual `gcloud builds submit` for first runs).
- New Cloud Run Job: `marsys-build-pipeline-job` in `asia-south1`, bound to `marsys-pipeline-writer@...` SA, with VPC connector for Cloud SQL.
- New Cloud Scheduler entry (optional, default DISABLED): nightly idempotent rebuild safety net.
- IAM bindings: only on resources owned by 14B (the new Cloud Run Job, the new Artifact Registry repo).

**`may_touch` (filesystem / git):**
- `cloudbuild.yaml` (NEW — repo root) — Cloud Build orchestration config.
- `platform/python-sidecar/pipeline/` (NEW directory):
  - `pipeline/__init__.py`
  - `pipeline/main.py` (orchestrator entry point)
  - `pipeline/registry_loader.py` (read VALIDATED_ASSET_REGISTRY from GCS)
  - `pipeline/source_fetcher.py` (fetch + sha256 verify against registry)
  - `pipeline/validators.py` (Pydantic models for registry + frontmatter)
  - `pipeline/manifest_writer.py` (build manifest JSON to artifacts bucket)
  - `pipeline/writers/__init__.py`
  - `pipeline/writers/base.py` (`IBuildWriter` abstract base class)
  - `pipeline/writers/rag_chunks_writer.py` (concrete writer for L1/L2.5/L3 → rag_chunks)
  - `pipeline/swap.py` (transactional staging→live swap)
- `platform/python-sidecar/Dockerfile.pipeline` (NEW — image for Cloud Run Job).
- `platform/python-sidecar/pipeline/requirements.txt` (NEW — pinned deps).
- `platform/supabase/migrations/013_build_pipeline_staging.sql` (NEW — staging tables + build_manifests table).
- `00_ARCHITECTURE/BUILD_PIPELINE_v1_0.md` (NEW — canonical spec; describes architecture, schemas, runbook).
- `00_ARCHITECTURE/PHASE_14B_BUILD_PIPELINE_REPORT_v1_0.md` (NEW — execution report).
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (additive — pipeline-related entries; status TRANSITIONAL).

**`must_not_touch`:**
- `platform/src/**` — zero TypeScript changes. Runtime is unaffected by this brief.
- `platform/python-sidecar/rag/chunkers/*.py`, `rag/embed.py` — REUSE, do not modify. If a chunker is genuinely broken, surface it as a finding for a separate brief; do NOT fix in 14B.
- Any feature flag.
- Existing tables `rag_chunks`, `rag_embeddings`, `rag_graph_nodes`, `rag_graph_edges` — schema unchanged. Only contents are rewritten via swap.
- L2 (`02_ANALYTICAL_LAYER/`) — archived; pipeline must NOT process it.
- `99_ARCHIVE/**` — archived assets are not pipeline inputs.

## Sub-streams (7 sequential)

### Stream A — Artifact Registry + Cloud Build trigger setup

1. Create Artifact Registry Docker repo:
   ```bash
   gcloud artifacts repositories create marsys-pipeline \
     --repository-format=docker \
     --location=asia-south1 \
     --description="MARSYS-JIS build pipeline images" \
     --project=madhav-astrology
   ```
2. Grant `marsys-pipeline-writer` push/pull access:
   ```bash
   gcloud artifacts repositories add-iam-policy-binding marsys-pipeline \
     --location=asia-south1 \
     --member=serviceAccount:marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com \
     --role=roles/artifactregistry.writer
   ```
3. Create Cloud Build trigger (disabled by default; first runs are manual):
   ```bash
   gcloud builds triggers create manual \
     --name=marsys-build-pipeline-manual \
     --build-config=cloudbuild.yaml \
     --region=asia-south1 \
     --project=madhav-astrology
   ```

Record all resource names + IDs in the close report.

### Stream B — Pipeline Docker image + dependencies

1. Create `platform/python-sidecar/pipeline/requirements.txt` with pinned versions:
   ```
   google-cloud-storage>=2.14.0,<3
   google-cloud-aiplatform>=1.42.0,<2
   psycopg[binary,pool]>=3.1.18,<4
   pydantic>=2.6.0,<3
   PyYAML>=6.0,<7
   python-frontmatter>=1.1.0,<2
   tenacity>=8.2.0,<9
   structlog>=24.1.0,<25
   ```
2. Create `platform/python-sidecar/Dockerfile.pipeline`:
   - Base: `python:3.11-slim` (NOT 3.13 — match Cloud Run runtime expectations)
   - COPY existing `rag/chunkers/`, `rag/embed.py`, and new `pipeline/` directory
   - Pin chunker version with a `PIPELINE_VERSION` ARG; bake into image label
   - Entrypoint: `python -m platform.python_sidecar.pipeline.main`
3. Local build + smoke test:
   ```bash
   docker build -f platform/python-sidecar/Dockerfile.pipeline -t marsys-pipeline:dev .
   docker run --rm marsys-pipeline:dev --help  # expects orchestrator's argparse output
   ```
4. Push to Artifact Registry (tag both `:dev` and `:v1.0.0`):
   ```bash
   docker tag marsys-pipeline:dev asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:v1.0.0
   docker push asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:v1.0.0
   ```

### Stream C — Cloud SQL staging schema migration

Author migration `platform/supabase/migrations/013_build_pipeline_staging.sql`:

```sql
-- 013_build_pipeline_staging.sql
-- Phase 14B: staging tables + build manifest registry
BEGIN;

-- Staging mirrors of live RAG tables. Pipeline writes here first;
-- a transactional swap promotes staging to live atomically.
CREATE TABLE IF NOT EXISTS rag_chunks_staging (LIKE rag_chunks INCLUDING ALL);
CREATE TABLE IF NOT EXISTS rag_embeddings_staging (LIKE rag_embeddings INCLUDING ALL);

-- Build manifest registry. Every pipeline run lands one row here.
-- The latest_build_id row points at the manifest currently live in rag_chunks.
CREATE TABLE IF NOT EXISTS build_manifests (
  build_id TEXT PRIMARY KEY,
  triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  triggered_by TEXT NOT NULL,                 -- 'manual:<email>' | 'scheduler' | 'github-push'
  registry_fingerprint TEXT NOT NULL,         -- sha256 of VALIDATED_ASSET_REGISTRY at fetch time
  pipeline_image_uri TEXT NOT NULL,           -- artifact registry image tag
  embedding_model TEXT NOT NULL,              -- 'text-multilingual-embedding-002'
  embedding_dim INTEGER NOT NULL,             -- 768
  chunk_count INTEGER NOT NULL,
  embedding_count INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('staging', 'live', 'rolled_back', 'failed')),
  manifest_uri TEXT NOT NULL,                 -- gs://madhav-marsys-build-artifacts/build-<id>/manifest.json
  promoted_at TIMESTAMPTZ,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_build_manifests_status ON build_manifests(status);
CREATE INDEX IF NOT EXISTS idx_build_manifests_triggered_at ON build_manifests(triggered_at DESC);

COMMIT;
```

Apply via the project's existing migration runner. Record the applied migration timestamp + checksum.

### Stream D — Pipeline Python code

Implement the modules under `platform/python-sidecar/pipeline/`. Architecture:

**`pipeline/main.py`** — orchestrator entry point. CLI flags:
- `--registry-uri` (default `gs://madhav-marsys-sources/00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json`)
- `--build-id` (auto-generated UUID if omitted)
- `--triggered-by` (string for audit)
- `--dry-run` (validates + chunks but skips write to staging)
- `--skip-swap` (writes staging but does not promote; for verification runs)

Flow:
1. Generate build_id (uuidv4 prefixed `build-`).
2. Load registry from GCS via `registry_loader.py`. Compute sha256 fingerprint.
3. Insert `build_manifests` row with status=`staging`.
4. For each CURRENT asset:
   - Fetch source content from GCS via `source_fetcher.py`. Verify sha256 against registry.
   - Validate frontmatter via `validators.py` Pydantic models.
   - Dispatch to appropriate chunker (lookup by `doc_type` in registry → existing chunker module).
   - Embed via existing `rag/embed.py` interface (in batch mode).
   - Write to `rag_chunks_staging` + `rag_embeddings_staging` via `RAGChunksWriter`.
5. Validate staging:
   - Row count > 0
   - Every chunk has a corresponding embedding row (LEFT JOIN check)
   - Every embedding is 768-dim
6. If `--skip-swap`: stop; mark manifest status as `staging`; emit manifest JSON; exit 0.
7. Otherwise: invoke `swap.py` to atomically promote staging → live. Update manifest row to `status=live, promoted_at=NOW()`.
8. Emit manifest JSON to `gs://madhav-marsys-build-artifacts/build-<id>/manifest.json`.
9. Structured-log the run summary (chunk_count, embedding_count, duration, errors).

**`pipeline/swap.py`** — single transaction:
```python
with conn.transaction():
    cursor.execute("DELETE FROM rag_embeddings")  # CASCADE handles rag_chunks deps
    cursor.execute("DELETE FROM rag_chunks")
    cursor.execute("INSERT INTO rag_chunks SELECT * FROM rag_chunks_staging")
    cursor.execute("INSERT INTO rag_embeddings SELECT * FROM rag_embeddings_staging")
    cursor.execute("TRUNCATE rag_chunks_staging, rag_embeddings_staging")
    cursor.execute("UPDATE build_manifests SET status='live', promoted_at=NOW() WHERE build_id=%s", (build_id,))
    cursor.execute("UPDATE build_manifests SET status='rolled_back' WHERE status='live' AND build_id != %s", (build_id,))
```
Note: any prior `live` manifest is auto-flipped to `rolled_back` so only one row carries `status=live` at any moment. The HNSW index on `rag_embeddings` will need a REINDEX after large swaps; include a post-swap `REINDEX INDEX CONCURRENTLY idx_rag_embeddings_hnsw;` (best-effort; log if reindex skipped).

**`pipeline/writers/base.py`** — abstract:
```python
class IBuildWriter(ABC):
    @abstractmethod
    def write_chunks(self, chunks: list[Chunk], embeddings: list[Embedding], build_id: str) -> WriteResult:
        ...
    @abstractmethod
    def validate_staging(self, build_id: str) -> ValidationResult:
        ...
    @abstractmethod
    def swap_to_live(self, build_id: str) -> SwapResult:
        ...
```
14C/14D/14E plug in additional writers behind this interface.

**Pydantic models** (`pipeline/validators.py`):
- `RegistryEntry` (matches VALIDATED_ASSET_REGISTRY shape)
- `AssetFrontmatter` (matches the shared frontmatter envelope)
- Per-doc_type subclasses (e.g., `MSRSignalFrontmatter`, `UCNSectionFrontmatter`)

### Stream E — Cloud Build YAML + Cloud Run Job spec

`cloudbuild.yaml` at repo root:

```yaml
steps:
  - id: build-pipeline-image
    name: gcr.io/cloud-builders/docker
    args:
      - build
      - -f
      - platform/python-sidecar/Dockerfile.pipeline
      - -t
      - asia-south1-docker.pkg.dev/$PROJECT_ID/marsys-pipeline/pipeline:$BUILD_ID
      - -t
      - asia-south1-docker.pkg.dev/$PROJECT_ID/marsys-pipeline/pipeline:latest
      - .
  - id: push-image
    name: gcr.io/cloud-builders/docker
    args:
      - push
      - --all-tags
      - asia-south1-docker.pkg.dev/$PROJECT_ID/marsys-pipeline/pipeline
  - id: deploy-job
    name: gcr.io/google.com/cloudsdktool/cloud-sdk
    entrypoint: gcloud
    args:
      - run
      - jobs
      - update
      - marsys-build-pipeline-job
      - --image=asia-south1-docker.pkg.dev/$PROJECT_ID/marsys-pipeline/pipeline:$BUILD_ID
      - --region=asia-south1
options:
  logging: CLOUD_LOGGING_ONLY
images:
  - asia-south1-docker.pkg.dev/$PROJECT_ID/marsys-pipeline/pipeline:$BUILD_ID
  - asia-south1-docker.pkg.dev/$PROJECT_ID/marsys-pipeline/pipeline:latest
```

Cloud Run Job creation (one-time, via gcloud):
```bash
gcloud run jobs create marsys-build-pipeline-job \
  --image=asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:v1.0.0 \
  --region=asia-south1 \
  --service-account=marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com \
  --vpc-connector=<existing-connector-name> \
  --set-env-vars=GCS_SOURCES_BUCKET=madhav-marsys-sources,GCS_ARTIFACTS_BUCKET=madhav-marsys-build-artifacts,CLOUD_SQL_INSTANCE=madhav-astrology:asia-south1:amjis-postgres \
  --set-secrets=DB_PASSWORD=amjis-db-password:latest \
  --memory=4Gi \
  --cpu=2 \
  --max-retries=1 \
  --task-timeout=30m \
  --project=madhav-astrology
```
(VPC connector name should be discovered from existing `amjis-web` config; if not present, document and surface — Cloud SQL via private IP requires it.)

### Stream F — End-to-end first run + verification

1. Trigger first build manually:
   ```bash
   gcloud builds submit --config=cloudbuild.yaml --project=madhav-astrology
   ```
2. Wait for build to succeed; capture build URL + image tag.
3. Trigger pipeline run with `--skip-swap` (DRY-RUN-ish — writes to staging, no live touch):
   ```bash
   gcloud run jobs execute marsys-build-pipeline-job \
     --args=--triggered-by=manual:phase-14b-first-run,--skip-swap \
     --region=asia-south1 --wait
   ```
4. Connect to Cloud SQL via Auth Proxy. Verify staging:
   ```sql
   SELECT COUNT(*) FROM rag_chunks_staging;        -- should be > 0
   SELECT COUNT(*) FROM rag_embeddings_staging;    -- should match
   SELECT vector_dims(embedding) FROM rag_embeddings_staging LIMIT 1; -- should be 768
   SELECT status, chunk_count, embedding_count FROM build_manifests ORDER BY triggered_at DESC LIMIT 1;
   ```
5. Compare row counts to current live `rag_chunks` count. Surface any unexpected delta in close report.
6. Trigger pipeline run WITH swap:
   ```bash
   gcloud run jobs execute marsys-build-pipeline-job \
     --args=--triggered-by=manual:phase-14b-promote \
     --region=asia-south1 --wait
   ```
7. Verify swap:
   ```sql
   SELECT COUNT(*) FROM rag_chunks;                                             -- should match staging count
   SELECT COUNT(*) FROM rag_embeddings;
   SELECT status, build_id, promoted_at FROM build_manifests WHERE status='live'; -- exactly one row
   SELECT COUNT(*) FROM rag_chunks_staging;                                     -- should be 0 (truncated post-swap)
   ```
8. Smoke-test runtime: invoke the Consume API on a known query that previously returned good results. If results materially regress, ROLLBACK by re-running pipeline pinning `--registry-uri` to the prior registry version (or document the manual SQL to re-promote a prior staging snapshot — note this is degraded coverage and should be flagged for 14G to formalize).
9. Verify build manifest landed in GCS:
   ```bash
   gcloud storage ls gs://madhav-marsys-build-artifacts/
   ```

### Stream G — Spec doc + close report + commit

1. Author `00_ARCHITECTURE/BUILD_PIPELINE_v1_0.md` covering:
   - Architecture diagram (text/ascii) of the pipeline
   - Trigger mechanisms (manual, push, scheduler)
   - Image versioning strategy
   - Staging-then-swap discipline + rollback runbook
   - Build manifest schema (the JSON written to artifacts bucket)
   - Writer plug-in pattern (for 14C/14D/14E)
   - Operational runbook: how to invoke a build, how to rollback, how to inspect a manifest
2. Author `00_ARCHITECTURE/PHASE_14B_BUILD_PIPELINE_REPORT_v1_0.md` covering:
   - All cloud resources created (with IDs)
   - Image SHA + tag of v1.0.0
   - First-build run summary (chunk/embedding counts, duration, manifest URI)
   - Swap verification SQL output
   - Rollback path tested (yes/no — if no, surface as residual for 14G)
   - Validator output (drift_detector, schema_validator, mirror_enforcer post-swap)
3. Update `CAPABILITY_MANIFEST.json` with:
   - `marsys-pipeline-image:v1.0.0` artifact entry
   - `marsys-build-pipeline-job` runtime entry
   - `BUILD_PIPELINE_v1_0.md` doc entry
   - `migration:013_build_pipeline_staging.sql` schema entry
4. Atomic commit. Message: `Phase 14B: Build pipeline (Cloud Build + Cloud Run Jobs) — staging-then-swap + manifest discipline`.

## Done criteria

1. Artifact Registry repo `marsys-pipeline` exists in `asia-south1`.
2. Pipeline image tagged `v1.0.0` is pushed and pullable.
3. Cloud Run Job `marsys-build-pipeline-job` exists, bound to `marsys-pipeline-writer` SA, has VPC connector for Cloud SQL.
4. Migration 013 is applied; `rag_chunks_staging`, `rag_embeddings_staging`, `build_manifests` tables exist.
5. `pipeline/` Python modules exist; orchestrator + writer + validators + swap implemented per spec.
6. First end-to-end build with `--skip-swap` succeeded; staging populated with chunk/embedding counts ≥ pre-build live counts.
7. Promotion build succeeded; `rag_chunks`/`rag_embeddings` updated; exactly one `build_manifests` row has `status='live'`.
8. Build manifest JSON exists at `gs://madhav-marsys-build-artifacts/build-<id>/manifest.json`.
9. Runtime smoke test post-swap: Consume API returns plausible results for a known query (no material regression vs pre-build).
10. `BUILD_PIPELINE_v1_0.md` + `PHASE_14B_BUILD_PIPELINE_REPORT_v1_0.md` exist and are committed.
11. `CAPABILITY_MANIFEST.json` reflects 14B additions; fingerprint rotated.
12. `cloudbuild.yaml` present at repo root.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Swap removes rows that runtime is mid-query — query returns partial results | Low | Medium | Swap is a single transaction; readers see either old or new state, never partial. Cloud SQL MVCC handles this. |
| Pipeline writes 0 chunks (registry parse error, source fetch failure) and swap empties live tables | Low | HIGH | Swap.py MUST gate on `staging_chunk_count > 0.5 * live_chunk_count`. Below threshold = ABORT swap, mark manifest `failed`, leave live untouched. |
| Vertex AI API quota hit mid-run | Medium | Medium | Use existing tenacity retry (already in embed.py). On hard quota, fail with manifest `failed` — do NOT swap partial staging. |
| Existing chunkers expect local-filesystem paths and break on GCS-fetched in-memory content | Medium | Medium | `source_fetcher.py` writes fetched content to a temp dir matching expected layout, OR adapts chunker call sites. Verify in Stream B Docker smoke test. |
| Cloud Run Job timeout (30m) too tight for full corpus rebuild | Low | Medium | 22 CURRENT assets is small (~minutes). If 14C/14D/14E balloon corpus, raise timeout in a separate brief. |
| HNSW reindex post-swap blocks queries | Low | Low | Use `REINDEX INDEX CONCURRENTLY`; readers unaffected. If non-concurrent only, schedule reindex during low-traffic window and log warning. |
| `rag_embeddings.embedding` is `vector(1024)` not `vector(768)` (migration 010 drift) | Low | HIGH | Pre-flight check: `SELECT vector_dims(embedding) FROM rag_embeddings_staging LIMIT 1` before swap. Mismatch = abort. |
| Cloud Build trigger accidentally fires from unrelated push | Low | Medium | Trigger created in `manual` mode at first; no automatic trigger in 14B. Path-filter trigger added in a separate brief once first runs are stable. |
| Pipeline's image lacks chunker version pinning, future image breaks reproducibility | Low | Medium | Embed `PIPELINE_VERSION` build arg + label in image; record in build_manifests row. |

## Concurrency declaration

**Parallel-with**:
- `14C/14D/14E AUTHORING` — those briefs can be authored while 14B executes; their executions gate on 14B done.
- `14F.1` follow-up — disjoint surface (governance docs), safe parallel.

**Must complete before**:
- `14C` execution — needs migration 013 applied and pipeline running before chart_facts table is added.
- `14D` execution — needs writer abstraction in place.
- `14E` execution — needs writer abstraction in place.
- `14G` lockdown — needs 14B's manifest baseline and pipeline runbook.

**Shared-file vigilance**:
- `CAPABILITY_MANIFEST.json` — 14B adds new entries to active block. If any concurrent session (14F.1, registry tool) touches the manifest, rebase and retry.
- `platform/supabase/migrations/` — only 14B writes 013. 14C will write 014. No conflict expected.

## Trigger phrase

"Read EXEC_BRIEF_PHASE_14B_BUILD_PIPELINE_v1_0.md and execute it."

## Notes for the executor

- The existing `rag/embed.py` is the chosen embedding interface — use it as a library, not a CLI. If its API requires refactoring to be importable cleanly (e.g., it has top-level side effects), do the minimal refactor required and document it; do NOT rewrite the embedding logic.
- Idempotency: chunk_id is derived from `(doc_type, source_file, source_version, content_hash)` per the existing chunker convention. A re-run on unchanged sources produces identical chunk_ids — staging then has the same rows as live, swap is a no-op data-wise but a fresh manifest is still recorded. This is the intended idempotency behavior.
- The 0.5x abort threshold on swap is conservative; if first runs prove stable, this can be tightened in a follow-up brief.
- VPC connector for Cloud SQL: discover via `gcloud run services describe amjis-web --region=asia-south1 --format='value(spec.template.metadata.annotations."run.googleapis.com/vpc-access-connector")'`. If empty, Cloud SQL is reached via public IP + Auth Proxy — adjust Cloud Run Job env accordingly.
- Cloud Logging: structlog → stdout → Cloud Logging. Verify logs are visible in Cloud Logging Console under resource type `cloud_run_job` after first run.
- This brief intentionally does NOT enable the GitHub-push trigger. That's a separate brief once first manual runs prove stable. Reduces blast radius in 14B.
- Phase 14C/14D/14E will each add new writers to `pipeline/writers/`. They will register their writers in `main.py`'s writer registry. 14B should leave the writer registry as a simple list/dict so additions are mechanical.
