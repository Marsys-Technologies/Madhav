---
artifact: PHASE_14A_FOLLOWUP_IAM_REPORT_v1_0
report_id: PHASE_14A_FOLLOWUP_IAM_REPORT
version: 1.0
generated: 2026-04-28
executor: Claude Code (Sonnet 4.6)
brief: EXEC_BRIEF_PHASE_14A_FOLLOWUP_IAM_HARDENING_v1_0.md
verdict: COMPLETE
status: COMPLETE
---

# Phase 14A.1 — IAM Hardening Report (additive path-a)

## Pre-flight Gate

| Check | Result | Detail |
|---|---|---|
| Phase 14A EXEC_BRIEF status | ✅ PASS | `status: COMPLETE` confirmed in `EXEC_BRIEF_PHASE_14A_GCS_FOUNDATION_v1_0.md` |
| Authenticated principal | ✅ PASS | `mail.abhisek.mohanty@gmail.com` — `roles/owner` on `madhav-astrology` |
| `gs://madhav-marsys-sources` exists | ✅ PASS | Created 2026-04-28T15:58:57Z, `env: prod` |
| `gs://madhav-marsys-build-artifacts` exists | ✅ PASS | Created 2026-04-28T15:59:03Z, `env: prod` |
| `marsys-runtime-reader` SA exists | ✅ PASS | Display name: MARSYS Runtime Reader |
| `marsys-pipeline-writer` SA exists | ✅ PASS | Display name: MARSYS Pipeline Writer |

All pre-flight checks pass.

---

## Stream A — Discovered Runtime SA(s)

| Cloud Run Service | Runtime SA |
|---|---|
| `amjis-web` | `938361928218-compute@developer.gserviceaccount.com` |
| `amjis-sidecar` | `938361928218-compute@developer.gserviceaccount.com` |

Both services use the **default Compute Engine SA** (same SA). This is the medium-likelihood risk identified in the brief's risk register. Additive grants work identically for the default Compute Engine SA; no blocking concern for 14A.1. Surfaced here for native awareness: long-term, a dedicated runtime SA (such as `marsys-runtime-reader`) is the preferred posture, but SA-swap is deferred and not in scope here.

---

## Stream B — Pre-existing Bindings Audit

### Project-level roles (`938361928218-compute@developer.gserviceaccount.com`)

| Role | Pre-existing |
|---|---|
| `roles/aiplatform.user` | ❌ MISSING — to be added |
| `roles/cloudsql.client` | ✅ present |
| `roles/editor` | ✅ present (broad project editor) |
| `roles/secretmanager.secretAccessor` | ✅ present |
| `roles/storage.objectAdmin` | ✅ present (superset of objectViewer; covers all project buckets) |

### Bucket-level bindings (relevant buckets)

| Bucket | Runtime SA binding | Pre-existing |
|---|---|---|
| `madhav-astrology-chat-attachments` | none explicit (covered by project `storage.objectAdmin`) | ✅ effective access |
| `madhav-astrology-chart-documents` | none explicit (covered by project `storage.objectAdmin`) | ✅ effective access |
| `madhav-marsys-sources` | none | ❌ bucket-level grant needed per brief |

### `marsys-pipeline-writer` pre-existing bindings on `madhav-marsys-sources`

| Role | Pre-existing |
|---|---|
| `roles/storage.objectCreator` | ✅ present (set during Phase 14A) |
| `roles/storage.objectViewer` | ❌ MISSING — to be added |

---

## Stream C — Bindings Added

### Grant 1: `aiplatform.user` (project-level) — was MISSING

```
gcloud projects add-iam-policy-binding madhav-astrology \
  --member=serviceAccount:938361928218-compute@developer.gserviceaccount.com \
  --role=roles/aiplatform.user
```

**Result:** Applied. Required for query-time Vertex AI embedding calls (`text-multilingual-embedding-002`).

### Grant 2: `storage.objectViewer` on `gs://madhav-marsys-sources` — runtime SA (ALWAYS per brief)

```
gcloud storage buckets add-iam-policy-binding gs://madhav-marsys-sources \
  --member=serviceAccount:938361928218-compute@developer.gserviceaccount.com \
  --role=roles/storage.objectViewer
```

**Result:** Applied. Explicit bucket-level read access to the new sources bucket.

### Grant 3: `storage.objectViewer` on `gs://madhav-marsys-sources` — `marsys-pipeline-writer`

```
gcloud storage buckets add-iam-policy-binding gs://madhav-marsys-sources \
  --member=serviceAccount:marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com \
  --role=roles/storage.objectViewer
```

**Result:** Applied. `marsys-pipeline-writer` now has both `objectCreator` (write) + `objectViewer` (read) on `madhav-marsys-sources` — required for the 14B source-fetch + processed-artifact-upload pattern.

### Grant 4: `cloudsql.client` (project-level) — SKIPPED (already present)

Pre-existing; `add-iam-policy-binding` is idempotent but no-op needed.

---

## Stream D — Final State Verification

### D.1: Runtime SA final project-level roles

| Role | Final State |
|---|---|
| `roles/aiplatform.user` | ✅ CONFIRMED |
| `roles/cloudsql.client` | ✅ CONFIRMED |
| `roles/editor` | ✅ CONFIRMED |
| `roles/secretmanager.secretAccessor` | ✅ CONFIRMED |
| `roles/storage.objectAdmin` | ✅ CONFIRMED |

### D.1: `gs://madhav-marsys-sources` final bucket policy (relevant bindings)

| Member | Role |
|---|---|
| `938361928218-compute@developer.gserviceaccount.com` | `roles/storage.objectViewer` ✅ |
| `marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com` | `roles/storage.objectCreator` ✅ |
| `marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com` | `roles/storage.objectViewer` ✅ |
| `marsys-runtime-reader@madhav-astrology.iam.gserviceaccount.com` | `roles/storage.objectViewer` ✅ (pre-existing from Phase 14A) |

### D.2: `marsys-pipeline-writer` has both objectCreator + objectViewer on sources

Confirmed. Both `roles/storage.objectCreator` and `roles/storage.objectViewer` are bound on `gs://madhav-marsys-sources`. Read + write capability present for 14B.

### D.3: Cloud Run SA unchanged (no swap)

| Service | SA at close | Matches Stream A |
|---|---|---|
| `amjis-web` | `938361928218-compute@developer.gserviceaccount.com` | ✅ unchanged |
| `amjis-sidecar` | `938361928218-compute@developer.gserviceaccount.com` | ✅ unchanged |

### D.4: `marsys-runtime-reader` status

Provisioned and unbound from Cloud Run (as designed). It holds `roles/storage.objectViewer` on `gs://madhav-marsys-sources` from Phase 14A. Retained as a documented least-privilege spec SA for future use (e.g., a dedicated read-only debug runtime). **Not deleted.**

### D.5: Existing flows preserved

| Flow | Status |
|---|---|
| `madhav-astrology-chat-attachments` read/write | ✅ preserved — project-level `storage.objectAdmin` unaffected |
| `madhav-astrology-chart-documents` read/write | ✅ preserved — project-level `storage.objectAdmin` unaffected |
| Cloud SQL connectivity | ✅ preserved — `cloudsql.client` pre-existing + confirmed |
| Vertex AI embedding calls | ✅ now unblocked — `aiplatform.user` added |

---

## Done Criteria Check

| # | Criterion | Status |
|---|---|---|
| 1 | Runtime SA has `aiplatform.user`, `cloudsql.client`, `objectViewer` on `madhav-marsys-sources` | ✅ |
| 2 | `amjis-web` + `amjis-sidecar` still use original SA (no swap) | ✅ |
| 3 | `marsys-pipeline-writer` has `objectViewer` on `madhav-marsys-sources` | ✅ |
| 4 | `marsys-runtime-reader` provisioned but unbound from Cloud Run | ✅ |
| 5 | Existing flows preserved (chat-attachments, chart-documents, Cloud SQL, Vertex AI) | ✅ |
| 6 | This report exists and committed | ✅ |
