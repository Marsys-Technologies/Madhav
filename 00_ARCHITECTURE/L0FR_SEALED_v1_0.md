---
artifact: L0FR_SEALED
version: 1.0
status: SEALED
sealed_at: 2026-06-08T06:47+05:30
decision: SEAL
---

# L0FR — Layer 0 Foundation Release — SEALED

## Seal Summary

All 7 L0FR streams shipped, deployed, and verified. Vimarśaka-Z attempt 2 decision: **SEAL**.

## Stream Registry

| Stream | Deliverable | Status |
|---|---|---|
| A | L0 brahmagyan retrieval registry, MCP OAuth 2.0 endpoints, 5 L0 capabilities, migration 081 | SEALED |
| B | Classical text indexing (BPHS, Jaimini, KP, Tajaka), `sutravali_rules` table | SEALED |
| C | CGM edge manifest ingestion, `cgm_edges_manifest_v1_0.json` | SEALED |
| D | Remedy corpus seeding, `brahma_remedy_corpus` | SEALED |
| E | Ephemeris build pipeline, `ephemeris_daily` 825k+ rows | SEALED |
| F | RAG chunk pipeline, `classical_text_chunks` 8,432+ rows | SEALED |
| G | PyJHora adapter, `/api/pyhora/compute` endpoint, `ganita_graha_sthana` table (migration 174), `query_dasha_periods` retrieval tool | SEALED |

## Hard Failures — All Resolved

| ID | Description | Resolution |
|---|---|---|
| HF1 | brahma-build-pipeline-job image predated `--global-build` | Image rebuilt 2026-06-08 from `Dockerfile.pipeline`; digest `sha256:eedd16a966a6c1126ec8a9421dca5df089a85878212bf1b669ebb3599e20229c`; job updated; smoke test exit 0 |
| HF2 | migration 174 (`ganita_graha_sthana`) not applied; Stream G not merged | Migration applied 2026-06-07; `feature/l0fr-stream-g-pyhora` merged to main 2026-06-07 |

## Documented Residuals (Non-Blocking)

| ID | Description | Tracking |
|---|---|---|
| SF1 | `sutravali_rules` 1,213 rows (spec 3,000; §12 range 800-2,000) | Accepted per master plan §12 |
| SF2 | `brahma_remedy_corpus` 200 rows (spec 500; §12 range 200-500) | Native-ratified 2026-06-07 |
| KR1-4 | 4-adapter smoke tests (agentic_loop, bulk_context, openai_function_calling, hybrid) — infra unavailable | Deferred to operator post-deploy |
| KR5 | ChatGPT MCP OAuth roundtrip | Deferred to operator post-deploy |

## Production Artifacts

- **brahma-pipeline image:** `asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline@sha256:eedd16a966a6c1126ec8a9421dca5df089a85878212bf1b669ebb3599e20229c`
- **Cloud Run job:** `brahma-build-pipeline-job` (asia-south1, project madhav-astrology)
- **Smoke test execution:** `brahma-build-pipeline-job-vw5q4` — exit 0
- **Main HEAD at seal:** `bcd15969`

## Conductor Log Reference

`00_ARCHITECTURE/CONDUCTOR/l0fr/CONDUCTOR_LOG.md` — Vimarśaka-Z attempt 2 entry
