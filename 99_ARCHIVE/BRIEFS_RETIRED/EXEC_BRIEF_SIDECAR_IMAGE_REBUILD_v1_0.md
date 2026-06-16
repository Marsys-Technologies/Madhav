---
brief_id: EXEC_BRIEF_SIDECAR_IMAGE_REBUILD
version: 1.0
status: AUTHORED
authored_by: Claude Code (Sonnet 4.6) — Sidecar 500 investigation session
authored_at: 2026-04-29
target_executor: Claude Code session
trigger_phrase: "Read EXEC_BRIEF_SIDECAR_IMAGE_REBUILD_v1_0.md and execute it."
phase: post-sidecar-500-investigation
phase_name: Rebuild Python sidecar image with RAG routes
risk_classification: LOW-MEDIUM (sidecar rebuild + redeploy; data layer is read-only)
parallelizable_with: [EXEC_BRIEF_FILESYSTEM_ADAPTER_FIX]
must_complete_before: [any work that depends on /rag/* sidecar endpoints being available]
depends_on:
  - SIDECAR_500_INVESTIGATION_REPORT_v1_0.md (COMPLETE)
output_artifacts:
  - New amjis-sidecar Cloud Run revision with RAG routes
---

# EXEC_BRIEF — Python Sidecar Image Rebuild

## Finding (from Sidecar 500 Investigation)

The deployed `amjis-sidecar` image (sha256:0753472, from 2026-04-25) predates the addition of
RAG route handlers to `platform/python-sidecar/main.py`. The deployed sidecar only has:

  POST /eclipses, /ephemeris, /event_chart_states, /jaimini_drishti, /retrogrades, /sade_sati, /v7_additions
  GET  /health

Missing from deployed image:
  POST /rag/route, /rag/retrieve, /rag/synthesize

Current risk: LOW — the TypeScript new pipeline does NOT call sidecar RAG routes (it uses
TypeScript tools that call Postgres directly). The missing routes don't cause current failures.

Risk becomes MEDIUM if: (a) any direct client starts calling the sidecar RAG endpoints, or
(b) future code paths are added that proxy RAG through the sidecar.

## Fix

Rebuild and redeploy the sidecar image:

```bash
cd platform
docker build -f python-sidecar/Dockerfile -t \
  asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-sidecar:latest \
  python-sidecar/
docker push asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-sidecar:latest
gcloud run deploy amjis-sidecar \
  --image asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-sidecar:latest \
  --region=asia-south1 --project=madhav-astrology
```

## Acceptance criteria

1. New revision deployed and healthy (`Ready: True`)
2. `GET /health` → 200
3. `POST /rag/route` with `{"query":"test","chart_id":"test"}` → 422 or 200 (not 404)
4. `POST /rag/retrieve` → 422 or 200 (not 404)
5. No regression on existing routes (`/ephemeris`, `/eclipses`, etc.)
