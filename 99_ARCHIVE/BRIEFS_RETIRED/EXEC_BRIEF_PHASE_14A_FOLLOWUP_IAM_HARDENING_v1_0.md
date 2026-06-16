---
brief_id: EXEC_BRIEF_PHASE_14A_FOLLOWUP_IAM_HARDENING
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_14A_FOLLOWUP_IAM_HARDENING_v1_0.md and execute it."
phase: 14A.1 (follow-up to 14A)
phase_name: 14A IAM Hardening — additive permissions on existing Cloud Run SA
risk_classification: LOW (IAM-only changes; no SA swap; preserves all existing flows)
parallelizable_with: [14F.1, 14B (authoring)]
depends_on: [EXEC_BRIEF_PHASE_14A_GCS_FOUNDATION_v1_0.md (COMPLETE)]
output_artifact: 00_ARCHITECTURE/PHASE_14A_FOLLOWUP_IAM_REPORT_v1_0.md
---

# EXEC_BRIEF — Phase 14A Follow-up — IAM Hardening (path-a additive)

## Mission

Phase 14A provisioned `marsys-runtime-reader` and `marsys-pipeline-writer` service accounts but deferred binding the runtime SA to `amjis-web`/`amjis-sidecar` because a swap would (a) sever access to existing buckets `madhav-astrology-chat-attachments` + `madhav-astrology-chart-documents` and (b) drop `aiplatform.user` (needed for query-time embedding calls). Native chose **path-a additive**: keep the existing Cloud Run SA, grant it the additional permissions it needs to read from `madhav-marsys-sources`, and leave `marsys-runtime-reader` as a least-privilege spec-only SA (not runtime-bound). Plus grant `marsys-pipeline-writer` read access on `sources` for the 14B build pipeline.

This brief makes only IAM bindings. Zero code, zero schema, zero feature flag changes.

## Pre-flight gate

1. Verify Phase 14A is COMPLETE (frontmatter check on `EXEC_BRIEF_PHASE_14A_GCS_FOUNDATION_v1_0.md`).
2. `gcloud auth list` — confirm authenticated principal has `roles/resourcemanager.projectIamAdmin` + `roles/storage.admin` on project `madhav-astrology`.
3. Confirm both buckets exist: `gcloud storage buckets describe gs://madhav-marsys-sources` + `gs://madhav-marsys-build-artifacts`.
4. Confirm both SAs exist: `gcloud iam service-accounts describe marsys-runtime-reader@madhav-astrology.iam.gserviceaccount.com` + `marsys-pipeline-writer@...`.

If any fail, halt with actionable message.

## Sub-streams (4 sequential)

### Stream A — Discover current Cloud Run SA

Run:
```bash
WEB_SA=$(gcloud run services describe amjis-web \
  --region=asia-south1 --project=madhav-astrology \
  --format='value(spec.template.spec.serviceAccountName)')
SIDECAR_SA=$(gcloud run services describe amjis-sidecar \
  --region=asia-south1 --project=madhav-astrology \
  --format='value(spec.template.spec.serviceAccountName)')
echo "amjis-web SA: $WEB_SA"
echo "amjis-sidecar SA: $SIDECAR_SA"
```

Record both values in the close report. They may be the same SA or different; both cases are valid. If either is empty (default Compute Engine SA in use), that's a separate concern — surface it in the report and proceed using the empty/default-SA value as-is (additive grants work either way; for default SA, the email is `<project-number>-compute@developer.gserviceaccount.com`).

### Stream B — Audit current bindings on the runtime SA(s)

For each unique SA discovered in Stream A:
```bash
gcloud projects get-iam-policy madhav-astrology \
  --flatten='bindings[].members' \
  --filter="bindings.members:$WEB_SA" \
  --format='value(bindings.role)'
```

Capture the role list. Confirm the SA already has (or does not have):
- `roles/aiplatform.user` — required for Vertex AI embedding calls at query time
- `roles/cloudsql.client` — required for Cloud SQL connectivity
- Any role granting access to `madhav-astrology-chat-attachments` and `madhav-astrology-chart-documents` (bucket-level binding, not project-level — also check `gcloud storage buckets get-iam-policy gs://madhav-astrology-chat-attachments`)

Record the audit result. The next stream grants only what's missing.

### Stream C — Grant missing permissions (additive)

For each runtime SA, grant the following ONLY IF the audit in Stream B showed them missing:

```bash
# Missing aiplatform.user (project-level)
gcloud projects add-iam-policy-binding madhav-astrology \
  --member=serviceAccount:$WEB_SA \
  --role=roles/aiplatform.user

# Missing cloudsql.client (project-level)
gcloud projects add-iam-policy-binding madhav-astrology \
  --member=serviceAccount:$WEB_SA \
  --role=roles/cloudsql.client
```

ALWAYS grant (regardless of prior bindings, this is a new bucket):

```bash
# Read access to the new sources bucket (bucket-level, NOT project)
gcloud storage buckets add-iam-policy-binding gs://madhav-marsys-sources \
  --member=serviceAccount:$WEB_SA \
  --role=roles/storage.objectViewer
```

Repeat for `$SIDECAR_SA` if different from `$WEB_SA`.

Also grant `marsys-pipeline-writer` read access to `sources` for 14B prep:

```bash
gcloud storage buckets add-iam-policy-binding gs://madhav-marsys-sources \
  --member=serviceAccount:marsys-pipeline-writer@madhav-astrology.iam.gserviceaccount.com \
  --role=roles/storage.objectViewer
```

### Stream D — Verify + close report

1. Re-run the audit from Stream B. Confirm the runtime SA(s) now have `aiplatform.user`, `cloudsql.client`, and `objectViewer` on `madhav-marsys-sources`.
2. Confirm `marsys-pipeline-writer` has `objectViewer` on `madhav-marsys-sources` plus its existing `objectCreator` (so it has both read and write — required for 14B's source-fetch + processed-artifact-upload pattern).
3. Confirm `amjis-web` and `amjis-sidecar` STILL use their original SA (no swap occurred):
   ```bash
   gcloud run services describe amjis-web \
     --region=asia-south1 --project=madhav-astrology \
     --format='value(spec.template.spec.serviceAccountName)'
   ```
   Should match the value captured in Stream A.
4. Write `00_ARCHITECTURE/PHASE_14A_FOLLOWUP_IAM_REPORT_v1_0.md` covering:
   - Discovered runtime SA(s) (verbatim from Stream A)
   - Pre-existing bindings audit (Stream B output)
   - Bindings added in Stream C (with role + scope)
   - Final state verification (Stream D)
   - Note: `marsys-runtime-reader` remains UNBOUND from Cloud Run; it is a documented least-privilege spec retained for future use (e.g., a dedicated read-only debug runtime). Do NOT delete it.
5. Commit the report. Message: `Phase 14A.1: IAM hardening (additive path-a) — runtime SA grants for sources bucket + Vertex AI`.

## Done criteria

1. Runtime SA(s) on `amjis-web` + `amjis-sidecar` have: `aiplatform.user`, `cloudsql.client`, `storage.objectViewer` on `madhav-marsys-sources`.
2. `amjis-web` + `amjis-sidecar` still use their original SA (verified, no swap).
3. `marsys-pipeline-writer` has `storage.objectViewer` on `madhav-marsys-sources`.
4. `marsys-runtime-reader` remains provisioned but unbound from Cloud Run.
5. Existing flows preserved: chat-attachments bucket access, chart-documents bucket access, Cloud SQL connectivity, Vertex AI calls — none disturbed.
6. `PHASE_14A_FOLLOWUP_IAM_REPORT_v1_0.md` exists and committed.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Discovered runtime SA is the default Compute Engine SA | Medium | Low | Bindings work the same way; just surface in report so native knows the runtime is on default SA (not ideal long-term but not 14A.1's concern) |
| `gcloud projects add-iam-policy-binding` race condition with parallel admin work | Low | Low | gcloud handles ETag retries automatically |
| Native already granted some of these manually | Medium | None | Stream C is idempotent; granting an existing role is a no-op |

## Trigger phrase

"Read EXEC_BRIEF_PHASE_14A_FOLLOWUP_IAM_HARDENING_v1_0.md and execute it."
