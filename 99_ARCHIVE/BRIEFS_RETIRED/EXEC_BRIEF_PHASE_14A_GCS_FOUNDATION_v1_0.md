---
brief_id: EXEC_BRIEF_PHASE_14A_GCS_FOUNDATION
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_14A_GCS_FOUNDATION_v1_0.md and execute it."
phase: 14A
phase_name: GCS Foundation — buckets, IAM, lifecycle, initial source sync
risk_classification: LOW (infrastructure provisioning + read-only file uploads; no platform code changes; no DB changes)
parallelizable_with: []
depends_on: [EXEC_BRIEF_PHASE_14_0_ASSET_INVENTORY_v1_0.md (COMPLETE — registry is canonical input)]
output_artifact: 00_ARCHITECTURE/PHASE_14A_GCS_FOUNDATION_REPORT_v1_0.md
---

# EXEC_BRIEF — Phase 14A — GCS Foundation

## Mission

Provision the Google Cloud Storage layer that the modernization pipeline (14B+) and production runtime will read from. Create canonical source and build-artifact buckets with proper IAM, lifecycle policies, and object versioning. Populate the source bucket with the current CURRENT-tagged assets from `VALIDATED_ASSET_REGISTRY_v1_0.json` so that subsequent phases have a single GCS-canonical location to read from.

After this phase, **the GCS source bucket becomes the canonical deployment surface** for L1, L2.5, and L3 source artifacts. Local files in the git repo continue to be the authoring source-of-truth, but production reads no longer depend on a developer's filesystem — they read from GCS.

This brief explicitly does NOT modify any platform code, DB schema, or feature flag. Those changes happen in Phases 14B-14G after this foundation is in place.

## Pre-flight gate

1. Verify Phase 14.0 is COMPLETE (frontmatter check on `EXEC_BRIEF_PHASE_14_0_ASSET_INVENTORY_v1_0.md`).
2. Verify `00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json` exists and parses.
3. Verify `gcloud` is installed, authenticated, and pointing at the correct project (the same project that hosts Cloud SQL `amjis-postgres`).
4. Verify the executor has these IAM roles on the project: `roles/storage.admin`, `roles/iam.serviceAccountAdmin`, `roles/resourcemanager.projectIamAdmin`. If missing, halt with: "Need elevated IAM to create buckets + service accounts."
5. Confirm git working tree is clean.

If any fail, halt with a clear actionable message.

## Scope

**`may_touch` (cloud resources):**
- New GCS buckets (provisioned in this brief): `madhav-marsys-sources`, `madhav-marsys-build-artifacts`
- New IAM service accounts: `marsys-pipeline-writer@<project>.iam.gserviceaccount.com`, `marsys-runtime-reader@<project>.iam.gserviceaccount.com`
- New IAM bindings on the new buckets (no changes to existing buckets unless explicitly noted)
- New Secret Manager secrets only if the pipeline-writer service account needs a key (prefer Workload Identity Federation; secrets only as fallback)

**`may_touch` (filesystem / git — minimal):**
- `00_ARCHITECTURE/PHASE_14A_GCS_FOUNDATION_REPORT_v1_0.md` (NEW — the report)
- `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md` (NEW — canonical bucket structure documentation)
- `platform/python-sidecar/scripts/gcs_sync.py` (NEW — minimal sync helper used by Stream D; not yet wired into platform code)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (additive update — new entries point at GCS URIs alongside existing local paths; status: TRANSITIONAL until 14B cuts over)

**`must_not_touch`:**
- `platform/src/**` — zero TypeScript changes in this brief
- `platform/python-sidecar/rag/**` — zero changes to embedding/chunking logic
- Any DB schema or content
- Any feature flag
- Any existing GCS bucket (`madhav-astrology-chat-attachments`, `madhav-astrology-chart-documents`) — those remain owned by the live app
- Any file in `99_ARCHIVE/` — archived assets stay archived; do not upload them to GCS
- Any L2 file (`02_ANALYTICAL_LAYER/`) — formally archived in 14F; NOT included in source bucket
- L4 (does not exist; nothing to sync)

## Sub-streams (5 sequential)

### Stream A — Bucket provisioning + lifecycle policy

1. Create `gs://madhav-marsys-sources` in region `asia-south1` (same region as Cloud SQL for low-latency reads). Properties:
   - Storage class: `STANDARD`
   - Object versioning: **ENABLED** (every overwrite preserves prior version for audit)
   - Lifecycle rule: keep all versions indefinitely for sources (legally important — version history is the audit trail)
   - Public access prevention: `enforced`
   - Uniform bucket-level access: `enabled`
   - Default labels: `{purpose: "marsys-l1-l2.5-l3-sources", env: "prod"}`

2. Create `gs://madhav-marsys-build-artifacts` in region `asia-south1`. Properties:
   - Storage class: `STANDARD` for first 90 days, then transition to `NEARLINE` (lifecycle rule)
   - Object versioning: enabled (build reproducibility)
   - Lifecycle rule: delete versions older than 365 days (build artifacts have lower long-term value than sources)
   - Public access prevention: enforced
   - Uniform bucket-level access: enabled
   - Default labels: `{purpose: "marsys-build-pipeline-output", env: "prod"}`

3. Verify both buckets are queryable via `gsutil ls gs://madhav-marsys-sources` (empty initially — Stream D populates).

**Stream A deliverable:** Both buckets exist, properties verified by `gsutil ls -L`. Output: bucket inspection results pasted into report.

### Stream B — Service accounts + IAM

1. Create service account `marsys-pipeline-writer@<project>.iam.gserviceaccount.com`. Purpose: used by Cloud Build / Cloud Run Jobs to write to source bucket on builds and write to build-artifacts bucket on every pipeline run.
   - Grant: `roles/storage.objectCreator` on `gs://madhav-marsys-sources` (write only — never delete sources)
   - Grant: `roles/storage.objectAdmin` on `gs://madhav-marsys-build-artifacts` (full control of artifacts)
   - Grant: `roles/cloudsql.client` (Cloud SQL Auth Proxy access — needed in 14B+)
   - Grant: `roles/aiplatform.user` (Vertex AI ADC for embeddings — needed in 14B+)

2. Create service account `marsys-runtime-reader@<project>.iam.gserviceaccount.com`. Purpose: used by `amjis-web` and `amjis-sidecar` Cloud Run services to read sources at runtime.
   - Grant: `roles/storage.objectViewer` on `gs://madhav-marsys-sources` (read only)
   - Grant: `roles/cloudsql.client`

3. Update `amjis-web` and `amjis-sidecar` Cloud Run services to use the runtime-reader service account. **Do this only if the deployment scripts are well-tested**; otherwise document the change as "Cloud Run service-account binding update — required before 14C is deployed" and surface to native to apply manually.

4. Verify IAM by impersonating the runtime-reader and attempting a `gsutil cp gs://madhav-marsys-sources/test-file local-file` (should succeed once the bucket has any file). Skip until Stream D populates.

**Stream B deliverable:** Service accounts created with correct bindings. Document each in the report.

### Stream C — Bucket layout + naming convention

Define the canonical structure of `gs://madhav-marsys-sources`:

```
gs://madhav-marsys-sources/
├── L1/
│   ├── facts/
│   │   ├── FORENSIC_ASTROLOGICAL_DATA_v8_0.md
│   │   ├── LIFE_EVENT_LOG_v1_2.md
│   │   ├── SADE_SATI_CYCLES_ALL.md
│   │   ├── EXTERNAL_COMPUTATION_SPEC_v2_0.md
│   │   └── CGP_AUDIT_v1_0.md
│   ├── ephemeris/
│   │   ├── EPHEMERIS_MONTHLY_1900_2100.csv
│   │   ├── ECLIPSES_1900_2100.csv
│   │   └── RETROGRADES_1900_2100.csv
│   └── sources/
│       ├── EVENT_CHART_STATES_v1_0.md
│       └── JHORA_TRANSCRIPTION_v8_0_SOURCE.md
├── L2_5/
│   ├── MSR_v3_0.md
│   ├── UCN_v4_0.md
│   ├── CDLM_v1_1.md
│   ├── RM_v2_0.md
│   ├── CGM_v9_0.md
│   └── RED_TEAM_L2_5_v1_0.md
└── L3/
    └── registers/
        ├── PATTERN_REGISTER_v1_0.json
        ├── PATTERN_REGISTER_v1_0.md
        ├── RESONANCE_REGISTER_v1_0.json
        ├── RESONANCE_REGISTER_v1_0.md
        ├── CONTRADICTION_REGISTER_v1_0.json
        ├── CONTRADICTION_REGISTER_v1_0.md
        ├── CLUSTER_ATLAS_v1_0.json
        ├── CLUSTER_ATLAS_v1_0.md
        └── INDEX.json
```

Document this layout at `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md` with frontmatter:

```
---
artifact: GCS_LAYOUT_v1_0.md
status: CURRENT
purpose: Canonical bucket structure for marsys source artifacts
parent_authoritative_source: VALIDATED_ASSET_REGISTRY_v1_0.json
---
```

The doc has a section per layer with: bucket path, intended consumer (which platform module reads it), versioning convention (filenames carry version, GCS object versioning preserves history of overwrites within a name).

**Stream C deliverable:** `GCS_LAYOUT_v1_0.md` committed.

### Stream D — Initial source sync

Write a minimal sync helper at `platform/python-sidecar/scripts/gcs_sync.py`. Single-purpose: read `VALIDATED_ASSET_REGISTRY_v1_0.json`, for each CURRENT asset, upload to its target GCS path per the layout doc.

The script:

1. Loads the registry.
2. For every entry with `status: CURRENT`:
   a. Computes the target GCS path per `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md` mapping.
   b. Computes local file's sha256.
   c. If GCS object doesn't exist OR its sha256 differs: upload via `google-cloud-storage` Python client, with metadata `{source_version, source_sha256, uploaded_at, uploaded_by: "phase_14A"}`.
   d. If exists and matches: skip (idempotent).
3. Reports per-asset: `UPLOADED | SKIPPED | ERROR`.

Use Application Default Credentials (ADC) so the same code path works in dev (developer's gcloud) and prod (Cloud Run service account).

Run the sync. Verify with `gsutil ls -r gs://madhav-marsys-sources/` that every CURRENT asset from the registry has a corresponding object.

**Stream D deliverable:** Sync script + initial population. Per-asset upload log in the report.

### Stream E — Manifest update + report

1. Update `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`:
   - For each CURRENT asset that's now also in GCS: add a `gcs_uri` field alongside the existing local `path` field.
   - Mark the entry's status as `TRANSITIONAL` (live now reads local; will read GCS post-14C).
   - Recompute the manifest fingerprint.

2. Write `00_ARCHITECTURE/PHASE_14A_GCS_FOUNDATION_REPORT_v1_0.md` with sections:
   - Bucket provisioning (Stream A)
   - Service accounts + IAM (Stream B)
   - Layout doc reference (Stream C)
   - Per-asset sync results table (Stream D)
   - Manifest fingerprint old → new (Stream E)
   - Native action required: review IAM bindings; confirm the Cloud Run service-account update from Stream B can proceed (or schedule for separate maintenance window)

3. Single git commit at end: `chore(14A): GCS foundation — buckets, IAM, layout doc, initial sync`.

**Stream E deliverable:** Report + manifest update + git commit.

## Critical constraints

- **No platform code changes.** This brief provisions infrastructure and populates source files; it does NOT modify the runtime code paths that read those files. Subsequent phases (14B+) handle the platform integration.
- **No bucket deletion.** Existing buckets stay as-is.
- **Idempotent uploads.** Stream D's sync skips files that match by sha256. Re-running the sync is safe.
- **Read-only on archived files.** Never upload anything from `99_ARCHIVE/` to GCS. The archive stays in git as historical record.
- **Object versioning is non-negotiable** on the source bucket. We need the audit trail of every change to FORENSIC, MSR, etc.
- **Service-account least-privilege.** runtime-reader has read-only on sources. pipeline-writer can write but cannot delete. Enforced by IAM, not by application logic.
- **Region affinity.** Both buckets in `asia-south1` to match Cloud SQL. This avoids cross-region latency and egress charges.
- **TRANSITIONAL manifest status.** The manifest gains GCS URIs but doesn't yet remove local paths. Production code still reads local until 14C cuts over. Do not remove local references prematurely.

## Done criteria

1. Stream A: both buckets exist with correct properties (versioning, lifecycle, public-access prevention, uniform IAM).
2. Stream B: both service accounts exist with correct least-privilege bindings. Cloud Run service-account update either applied (verified via `gcloud run services describe`) or explicitly deferred to native with a follow-up note.
3. Stream C: `GCS_LAYOUT_v1_0.md` exists at `00_ARCHITECTURE/`, committed.
4. Stream D: every CURRENT asset from `VALIDATED_ASSET_REGISTRY_v1_0.json` has a corresponding object in `gs://madhav-marsys-sources/` at its layout-doc path; sha256 verified.
5. Stream E: `CAPABILITY_MANIFEST.json` updated with `gcs_uri` fields and TRANSITIONAL status; report written; git commit landed.
6. Native acceptance: native confirms IAM bindings look correct and signs off via "Phase 14A accepted — proceed to 14B".

## Risk classification: LOW

This brief is infrastructure provisioning. Mitigations:
- No production code changes — runtime behavior unchanged
- No DB changes
- IAM least-privilege from day one
- Object versioning preserves recovery options
- Idempotent sync — re-running is safe
- Cloud Run service-account update is the only "live" change; gated behind explicit native approval if the executor isn't comfortable applying it directly

## Forward implications

After 14A closes:
- **14B (Build Pipeline)** has buckets to write to and read from. Cloud Build trigger can be authored next.
- **14C (L1 Structured Tables)** will read source files from `gs://madhav-marsys-sources/L1/` (instead of local filesystem) when projecting to Postgres. The build pipeline becomes the only writer of structured tables.
- The **CAPABILITY_MANIFEST.json TRANSITIONAL status** flips back to CURRENT in 14C/14D when production code is cut over to GCS reads.
- **Multi-native readiness**: this layout supports per-native subdirectories (e.g., `L1/<native_id>/facts/`) when M3+ adds federation. Today single-native, no subdir needed.

## How native triggers

Cloud SQL Auth Proxy not required for this brief (no DB access). Just `gcloud` authenticated with project IAM access.

In a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension):

> Read EXEC_BRIEF_PHASE_14A_GCS_FOUNDATION_v1_0.md and execute it.

Estimated wall-clock: ~2 hours including sync uploads (file sizes are small except the EPHEMERIS CSV at 1.69MB).

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when all 6 done-criteria pass and native accepts
