---
brief_id: EXEC_BRIEF_FILESYSTEM_ADAPTER_FIX
version: 1.0
status: COMPLETE
authored_by: Claude Code (Sonnet 4.6) — Sidecar 500 investigation session
authored_at: 2026-04-29
target_executor: Claude Code session
trigger_phrase: "Read EXEC_BRIEF_FILESYSTEM_ADAPTER_FIX_v1_0.md and execute it."
phase: post-sidecar-500-investigation
phase_name: Filesystem adapter production hardening
risk_classification: MEDIUM (code change + redeploy required; changes runtime behavior of storage layer)
parallelizable_with: []
must_complete_before: [any new amjis-web deployment with current codebase; Phase 11B legacy deletion]
depends_on:
  - SIDECAR_500_INVESTIGATION_REPORT_v1_0.md (COMPLETE — this brief is a finding from that investigation)
output_artifacts:
  - platform/src/lib/storage/filesystem.ts (modified — REPO_ROOT env-var driven)
  - 00_ARCHITECTURE/SIDECAR_500_INVESTIGATION_REPORT_v1_0.md (updated — mark REM-002 in progress)
---

# EXEC_BRIEF — Filesystem Adapter REPO_ROOT Production Hardening

## Finding (from Sidecar 500 Investigation)

`platform/src/lib/storage/filesystem.ts` line 4:
```typescript
const REPO_ROOT = '/Users/Dev/Vibe-Coding/Apps/Madhav'
```

This hardcoded path only exists on the local development machine. On Cloud Run, this path
does not exist. Any call to `storage.readFile()` (e.g., `loadManifest` in the new query
pipeline) will fail with ENOENT on Cloud Run, producing a 500.

Current risk: LOW — the deployed `amjis-web-00010-pd8` image was built before Phase 11A and
has `NEW_QUERY_PIPELINE_ENABLED: false` by default, so `loadManifest` is not called in
production today. Risk becomes HIGH the moment any new image is deployed with Phase 11A code.

## Fix design

Two changes required:

1. **`filesystem.ts`**: Replace hardcoded path with `process.env.MARSYS_REPO_ROOT ?? process.cwd()`.
   - In local dev: set `MARSYS_REPO_ROOT=/Users/Dev/Vibe-Coding/Apps/Madhav` in `.env.local`
   - On Cloud Run: either bundle the governance files into the image (recommended) or point to a
     GCS-backed path

2. **Dockerfile + CI**: Copy the required governance files into the `platform/` context so they
   are available inside the Docker image:
   - `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
   - `00_ARCHITECTURE/manifest_overrides.yaml`
   Add a `COPY ../00_ARCHITECTURE/CAPABILITY_MANIFEST.json ./00_ARCHITECTURE/` step (or copy
   during CI before docker build).
   
   Alternative: make `manifest_reader.ts` fall back to GCS when the local file doesn't exist.
   This is more resilient but adds complexity.

## Acceptance criteria

1. `filesystemAdapter.readFile('00_ARCHITECTURE/CAPABILITY_MANIFEST.json')` succeeds on Cloud Run
   without the hardcoded path.
2. Local dev continues to work (env var override).
3. New image deployed to Cloud Run; revision reaches Ready.
4. A single smoke query via `POST /api/chat/consume` returns 200 with tools invoked.
