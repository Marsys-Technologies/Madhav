---
title: BUILD_A3_A4_A5_OPERATOR_RUN
version: 1.0
status: FAIL
operator_run_date: "2026-05-30"
operator: Claude Code (Sonnet 4.6)
verdict: "FAIL — /api/build/start not deployed; pipeline image predates A3+A4+A5 writers"
---

# A3+A4+A5 Build Operator Run — Native Chart

## Summary

**VERDICT: FAIL — Pre-flight halted.**  
`/api/build/start` returns 404 on prod (deployed image predates the route).  
`marsys-build-pipeline-job` image predates A3+A4+A5 writers.  
No build was triggered. `chart_facts` remains empty.

---

## Pre-flight Results

### Step 1 — MARSYS_FLAG_BUILD_TRIGGER_ENABLED

| Check | Result |
|---|---|
| Flag present on amjis-web | YES |
| Value | `true` |
| Status | PASS |

### Step 2 — marsys-build-pipeline-job exists

| Check | Result |
|---|---|
| Job exists | YES |
| Image | `asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:a91e4339-ca42-41d2-8f2b-7fefa7d57c8f` |
| Image build date | **2026-05-26** |
| Writers committed | 2026-05-29 / 2026-05-30 |
| Status | **FAIL — image predates A3+A4+A5 writers** |

### Step 3 — Native chart_id lookup

| Check | Result |
|---|---|
| NATIVE_CHART_ID | `362f9f17-95a5-490b-a5a7-027d3e0efda0` |
| Name | Abhisek Mohanty |
| Birth date | 1984-02-05 |
| Birth place | Bhubaneswar |
| Status | PASS |

### Step 4 — Pre-trigger chart_facts count

| Chart ID | PRE_TRIGGER_COUNT |
|---|---|
| `362f9f17-...` | **0** (post-wipe confirmed) |

### Step 5 — Session cookie mint

| Check | Result |
|---|---|
| `get_session_cookie.mjs` | Found at `platform/scripts/get_session_cookie.mjs` |
| Cookie minted | YES (930 bytes) |
| Status | PASS |

### Step 6 — POST /api/build/start

| Check | Result |
|---|---|
| URL attempted | `https://amjis-web-qm256lasva-el.a.run.app/api/build/start` |
| HTTP status | **404** |
| Response | Next.js 404 HTML page |
| Status | **FAIL — route not deployed** |

---

## Root Cause Analysis

### Blocker 1: amjis-web not redeployed since 2026-05-27

The deployed Cloud Run revision `amjis-web-00430-g8l` was built from git commit `367ee47c` (2026-05-27 07:32 IST):

```
367ee47c  2026-05-27 07:32  fix(chart-snapshot): rebuild planetary table + karakas from FORENSIC v8.0
```

The `/api/build/start` route was first added in commit `4b5d60b7` (2026-05-28) and extended in `93de74ef` (2026-05-29). Both postdate the deployed image.

The A3+A4+A5 writers were committed in the conductor run (2026-05-29/30). None of these commits are in the deployed image.

**Timeline gap:**

| Event | Date (IST) | In deployed image? |
|---|---|---|
| Deployed image built from `367ee47c` | 2026-05-27 07:32 | — |
| `/api/build/start` added (`4b5d60b7`) | 2026-05-28 13:49 | **NO** |
| Route extended (`93de74ef`) | 2026-05-29 08:48 | **NO** |
| A3 writers | 2026-05-29 | **NO** |
| A4 writers | 2026-05-29/30 | **NO** |
| A5 writers | 2026-05-29/30 | **NO** |
| CI fixes (`56b66b94`) | 2026-05-30 01:20 | **NO** |
| Current main HEAD (`1dc4b225`) | 2026-05-30 01:03 | **NO** |

### Blocker 2: marsys-build-pipeline-job image predates writers

The pipeline Cloud Run job uses image:
```
pipeline:a91e4339-ca42-41d2-8f2b-7fefa7d57c8f
Built: 2026-05-26T02:56:17Z
```

A3/A4/A5 writers in `platform/python-sidecar/pipeline/` were committed 2026-05-29/30. The pipeline image does NOT contain them. Executing the job directly would populate zero A3/A4/A5 rows.

### Root cause: ACC-S7 "deploy" was documentation-only

Commit `e22632d0` ("feat(deploy/ACC-S7): A3+A4+A5 production deploy COMPLETE") touched only:

```
 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CONDUCTOR_LOG.md  (+16 lines)
 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/session_queue.yaml (2 lines)
 CLAUDECODE_BRIEF.md                                             (-134/+83 lines)
```

No Docker image was rebuilt. No Cloud Run service was updated. GitHub Actions CI/CD has not run a deploy since 2026-05-27 (presumably because CI was failing — the ci.yml fixes shipped in this session at `56b66b94` haven't been deployed either).

---

## What Must Happen Before Build Can Succeed

### Step A — Deploy amjis-web from current main HEAD

GitHub Actions deploy.yml fires automatically when "CI — Ganga Quality Gate" passes on main. Once CI passes on the current main HEAD (which includes the CI fixes from `56b66b94`), deploy.yml will:
1. Build `amjis-web` Docker image from main HEAD → `/api/build/start` route will be live
2. Deploy new revision to Cloud Run (asia-south1)

Alternatively, trigger `workflow_dispatch` from GitHub Actions UI on deploy.yml pointing to main.

### Step B — Build new pipeline image with A3+A4+A5 writers

The pipeline image must be rebuilt from the current state of `platform/python-sidecar/pipeline/`. Steps:
```bash
# From repo root — build pipeline image
docker build -t asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:$(git rev-parse --short HEAD) \
  -f platform/python-sidecar/Dockerfile.pipeline platform/python-sidecar/

docker push asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:$(git rev-parse --short HEAD)
```

### Step C — Update marsys-build-pipeline-job to use new image

```bash
gcloud run jobs update marsys-build-pipeline-job --region=asia-south1 \
  --image=asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:<NEW_TAG>
```

### Step D — Re-run this operator run script

Once A, B, C are complete, re-execute the trigger sequence.

---

## State at Halt

| Item | State |
|---|---|
| chart_facts rows for native | **0** (unchanged from pre-wipe state) |
| builds rows created | **0** |
| build_events rows | **0** |
| l25_* tables | Exist, all empty |
| DB proxy | Running (port 5433), stopped post-report |
| Cookie minted | Not used (halted before trigger) |

---

## DB Schema Verified Present

The following tables confirmed present with correct schema:

| Table | Status |
|---|---|
| `chart_facts` | EXISTS — schema matches A3/A4/A5 spec (`verification_pass_status`, `fact_key`, `fact_value_jsonb`, `ayanamsha_id`) |
| `builds` | EXISTS — 5-ayanamsha `ayanamshas JSONB` column present |
| `build_steps` | EXISTS |
| `build_events` | EXISTS |
| `l25_cdlm_links` | EXISTS (empty) |
| `l25_cgm_edges` | EXISTS (empty) |
| `l25_cgm_nodes` | EXISTS (empty) |
| `l25_msr_signals` | EXISTS (empty) |
| `l25_rm_resonances` | EXISTS (empty) |
| `l25_ucn_sections` | EXISTS (empty) |

Migrations are correctly applied. The DB is ready. The blocker is infrastructure (image freshness), not schema.

---

## Verdict

**FAIL — Two pre-flight blockers halted execution before any build was triggered.**

No data was modified. `chart_facts` remains at 0 rows for the native chart.

Remediation: push CI to green → GitHub Actions auto-deploys → rebuild pipeline image → update job → re-trigger.
