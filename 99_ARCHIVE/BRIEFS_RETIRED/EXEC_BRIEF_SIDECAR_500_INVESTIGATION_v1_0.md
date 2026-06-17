---
brief_id: EXEC_BRIEF_SIDECAR_500_INVESTIGATION
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_SIDECAR_500_INVESTIGATION_v1_0.md and execute it."
phase: post-14G — runtime hotfix investigation
phase_name: Python sidecar HTTP 500 — diagnose and resolve
risk_classification: MEDIUM-HIGH (live production runtime issue; downstream phases blocked until resolved; fix may require Cloud Run revision rollback or env-var/IAM correction)
parallelizable_with: []  # serial; the runtime is degraded and other work depends on a healthy sidecar
must_complete_before: [Phase 11B execution; Exec_15 (B.9); any new feature work that exercises the sidecar path]
depends_on:
  - EXEC_BRIEF_PHASE_14G_LOCKDOWN_VERIFICATION_v1_0.md (COMPLETE — surfaced the 500 during Stream E smoke)
output_artifacts:
  - 00_ARCHITECTURE/SIDECAR_500_INVESTIGATION_REPORT_v1_0.md
---

# EXEC_BRIEF — Python Sidecar HTTP 500 Investigation

## Mission

The Phase 14G smoke test (Stream E) discovered the Python sidecar (`amjis-sidecar` Cloud Run service) returns HTTP 500 on the smoke-test path. 14G worked around it via audit-log proxy evidence (11/11 prior production sessions used `msr_sql` tool successfully), so the historical runtime is healthy — but the *current* runtime is degraded for whatever code path exercises the sidecar synchronously.

This brief diagnoses the 500, identifies root cause, and either fixes it (if root cause is small + scoped) or escalates with a clear remediation plan (if root cause is structural).

Three commitments:

1. **No firefighting.** Capture the symptom precisely, audit logs, identify root cause, decide fix-or-escalate. Do NOT start patching files until the cause is understood.

2. **Production runtime is the priority.** If the fix requires a Cloud Run revision rollback to a known-good image, that's the right move — even if it means temporarily reverting a Phase 14 image push. Document and surface; do NOT roll forward through unknown territory.

3. **No scope creep.** This brief fixes the 500. It does NOT touch Phase 14's data layer, the build pipeline, the locked manifest entries, or any tool implementation. If the 500 reveals a deeper issue (e.g., a 14C tool dependency unsatisfied at runtime), that becomes a separate finding for a follow-up brief — this brief still closes once the 500 is gone.

## Pre-flight gate

1. Verify Phase 14G is COMPLETE — frontmatter check on `EXEC_BRIEF_PHASE_14G_LOCKDOWN_VERIFICATION_v1_0.md`.
2. `gcloud auth list` — confirm authenticated principal has `roles/run.admin`, `roles/logging.viewer`, `roles/cloudsql.viewer`.
3. Confirm git working tree clean (we may make small fix commits; tree should start clean).

## Scope

**`may_touch` (cloud resources):**
- Read access to all `gcloud run` + `gcloud logging` + `gcloud sql` queries.
- Cloud Run revision rollback on `amjis-sidecar` ONLY if Stream D's root cause analysis points there AND the rollback is to a known-good revision SHA.
- IAM binding additions on `amjis-sidecar`'s SA ONLY if the cause is a missing permission and the fix is additive (not a removal).
- Env var corrections on `amjis-sidecar` ONLY if Stream D names a specific incorrect variable + correct value.
- New Cloud Run revision deploy (with corrected env or rolled-back image) ONLY after the fix is identified.

**`may_touch` (filesystem / git):**
- `00_ARCHITECTURE/SIDECAR_500_INVESTIGATION_REPORT_v1_0.md` (NEW — investigation + outcome).
- `verification_artifacts/SIDECAR_500/` (NEW — captured logs, error traces, gcloud outputs).
- A small Python or TS source fix in `platform/python-sidecar/**` ONLY IF Stream C identifies a specific code-level cause that's a 1–2 line correction. Larger fixes require their own brief.

**`must_not_touch`:**
- Any Phase 14 data table.
- Any Phase 14 LOCKED manifest entry.
- Any chunker, embedder, or build-pipeline code (those are Phase 14B-owned).
- Any feature flag — even `NEW_QUERY_PIPELINE_ENABLED`. The 500 is not a flag-flip issue; rolling back the flag is NOT in scope.
- Any structured-tool implementation (those are Phase 14C/14D/14E owned).

## Sub-streams (5 sequential)

### Stream A — Symptom capture

1. Reproduce the 500 against the live Consume API:
   ```bash
   curl -i -X POST https://<amjis-web-domain>/api/chat/consume \
     -H 'Content-Type: application/json' \
     -H 'Cookie: <session-cookie-from-an-authenticated-session>' \
     -d '{"chartId":"<test-chart-id>","message":"What is my Saturn longitude?"}'
   ```
   Capture full HTTP status, headers, body (which may include a stack trace or just a generic 500 page).
2. If the 500 only fires for certain query types, repeat with 3–4 query variants — factual, predictive, structured-tool, plain rag-search. Note which fail.
3. Capture timestamps + request IDs (`x-cloud-trace-context` header on the response if present).
4. Save raw outputs to `verification_artifacts/SIDECAR_500/symptom_capture.txt`.

If reproduction fails (API returns 200), the issue is intermittent or has self-resolved. Continue to Stream B regardless — log analysis still surfaces what was wrong.

### Stream B — Service + logs audit

1. Cloud Run service describe:
   ```bash
   gcloud run services describe amjis-sidecar \
     --region=asia-south1 --project=madhav-astrology \
     --format=yaml > verification_artifacts/SIDECAR_500/service_describe.yaml
   ```
   Confirm: `status.conditions[*].status='True'`, latest revision is healthy, no error annotations, instance count > 0.
2. Recent revisions:
   ```bash
   gcloud run revisions list --service=amjis-sidecar \
     --region=asia-south1 --project=madhav-astrology \
     --format='table(name, active, deployed, image)' \
     | tee verification_artifacts/SIDECAR_500/revisions.txt
   ```
   Identify which revision is currently serving. Note its image SHA + deploy timestamp. Compare to the previous revision (the last known-good).
3. Cloud Logging — pull last 100 errors + last 30 minutes of sidecar stderr:
   ```bash
   gcloud logging read \
     'resource.type="cloud_run_revision" AND resource.labels.service_name="amjis-sidecar" AND severity>=ERROR' \
     --limit=100 --project=madhav-astrology \
     --format=json > verification_artifacts/SIDECAR_500/error_logs.json
   gcloud logging read \
     'resource.type="cloud_run_revision" AND resource.labels.service_name="amjis-sidecar" AND timestamp>="-30m"' \
     --limit=200 --project=madhav-astrology \
     --format=json > verification_artifacts/SIDECAR_500/recent_logs.json
   ```
4. Look for patterns:
   - Stack traces (Python tracebacks, Node uncaught exceptions)
   - Cloud SQL connection failures (`could not connect to server`, `password authentication failed`, `IAM`)
   - Vertex AI errors (`PermissionDenied`, `RESOURCE_EXHAUSTED`, `INVALID_ARGUMENT`)
   - Module import errors (`ModuleNotFoundError`, missing dep)
   - GCS errors (403, 404 against `madhav-marsys-sources` if sidecar reads sources at runtime)
   - Container OOM (`exit code 137`, memory > limit)
   - Startup probe failures
5. Capture the top 3 most-frequent error patterns + sample stack traces.

### Stream C — Root cause hypothesis

Based on Stream A symptom + Stream B log patterns, classify the cause into one of these buckets and document evidence:

| Bucket | Typical signals | Common fix |
|---|---|---|
| **Recent revision regression** | Logs spike around recent deploy; prior revision was healthy | Rollback Cloud Run to prior revision (Stream D) |
| **Cloud SQL auth/IAM** | "password auth failed", "could not connect", IAM PermissionDenied | Verify SA has `cloudsql.client`; check Auth Proxy / connection string env vars |
| **Vertex AI auth/quota** | `PermissionDenied` for aiplatform; `RESOURCE_EXHAUSTED` | Verify SA has `aiplatform.user` (per 14A.1 grant); check quotas |
| **Phase 14 dependency drift** | Tool calls failing because the runtime expects a column/row that doesn't match Phase 14's schema | Compare runtime expectations vs locked schema; surface as Phase 14G follow-up |
| **Missing env var** | Startup error citing missing config; `KeyError: 'X_REQUIRED_VAR'` | Set the missing env var on the Cloud Run revision |
| **Container OOM / cold-start timeout** | Exit 137; 502/504 (not 500) but sometimes manifests as 500 from upstream | Bump memory; tune min-instances |
| **Code-level bug introduced post-14G** | Stack trace points at a specific recent commit | Surface the commit; revert or hotfix |

If signals don't fit one bucket cleanly, document the conflict and surface — do not pick a bucket arbitrarily.

### Stream D — Fix (if simple) OR finding triage (if complex)

**Simple cases (apply fix in this brief):**
- Recent revision regression with clear known-good prior → roll back:
  ```bash
  gcloud run services update-traffic amjis-sidecar \
    --to-revisions=<prior-good-revision>=100 \
    --region=asia-south1 --project=madhav-astrology
  ```
  Verify 200s return on the smoke query post-rollback. Document the rolled-back-from revision SHA + hypothesized cause.
- Missing IAM binding → grant per 14A.1 pattern (additive only).
- Missing env var with known value → set via `gcloud run services update --update-env-vars=KEY=value`.
- Vertex AI quota → request quota increase (out of brief scope; surface as DEFERRED).

**Complex cases (surface, do not patch in this brief):**
- Code-level bug requiring more than 1–2 line fix → author a follow-up `EXEC_BRIEF_SIDECAR_500_FIX_<id>_v1_0.md` brief stub at repo root with `status: AUTHORED`. Brief outlines the diagnosis, the proposed fix, and acceptance criteria.
- Phase 14 schema/runtime drift → surface as a Phase 14G post-lockdown finding; author a DEFERRED brief.
- Multiple concurrent causes → halt; surface; require native sign-off on remediation plan before any change.

In either path, capture the decision in the report.

### Stream E — Re-verify + close report

1. Re-run the Stream A reproduction against the live API. Confirm 200 (or document residual 500 if fix is partial).
2. Run a 5-query smoke set against the Consume API — same shape as 14G's Stream E original spec. Capture audit_event for each. Verify ≥4 of 5 succeed and call structured tools.
3. Author `00_ARCHITECTURE/SIDECAR_500_INVESTIGATION_REPORT_v1_0.md`:
   - Symptom (verbatim from Stream A)
   - Service + log audit findings (Stream B)
   - Root cause (Stream C bucket + evidence)
   - Action taken (Stream D — fix landed | finding queued | rollback executed)
   - Re-verification result (Stream E — pass/fail + smoke counts)
   - Residuals (any partial-fix items, follow-up briefs queued)
4. Atomic commit. Title: `Sidecar 500 investigation — root cause: <bucket>; resolution: <fix-or-deferred>`.

## Done criteria

1. Symptom captured to verification_artifacts.
2. Service + log audit captured.
3. Root cause classified into one bucket (or conflict explicitly documented).
4. Either fix landed in this brief OR follow-up brief stub authored at repo root.
5. Re-verification: live API returns 200 on the test query (or, if the fix is deferred, the report explicitly documents the runtime is still degraded and the next brief's trigger phrase).
6. SIDECAR_500_INVESTIGATION_REPORT_v1_0.md exists and committed.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cloud Run rollback to "known-good" revision actually has a different bug | Medium | Medium | Verify post-rollback with Stream E smoke; if smoke fails, roll forward to a third revision OR surface as multi-revision-corruption finding |
| Fix requires Phase 14 manifest unfreeze | Low | High | Stop. Surface to native. Phase 14 lockdown is a hard floor; unfreezing is a deliberate decision, not a side effect of a hotfix |
| Logs are insufficient (rotation, missing instrumentation) | Medium | Medium | If Stream B can't extract a clear pattern, the brief surfaces "diagnostic gap" as a finding and proposes an observability brief |
| Fix masks the actual cause (silent retry / catch-all) | Medium | High | Stream D explicitly forbids catch-all silencing; fixes must address root cause |
| Multiple users hit the 500 during investigation | High | Low (depending on traffic) | If traffic is meaningful, escalate to consider an immediate rollback even before full RCA — prioritize restoring service over completing the investigation |

## Trigger phrase

"Read EXEC_BRIEF_SIDECAR_500_INVESTIGATION_v1_0.md and execute it."

## Notes for the executor

- Investigation discipline: DO NOT make changes until Stream C completes. Patches before diagnosis are how 500s become 503s.
- The audit_log evidence from 14G shows historical sessions worked. That's strong signal that something *recent* broke the sidecar — start with Stream B's revision-list check and look for a deploy timestamp that aligns with when the 500 started.
- If Cloud Run shows the latest revision was deployed during Phase 14G itself (unlikely but possible), check whether 14G's verification work touched any sidecar config. Phase 14G `must_not_touch` excluded platform/src and feature flags, but a manifest-fingerprint update could conceivably have triggered a redeploy.
- The fix path is either small-and-scoped (rollback, env, IAM) or it becomes its own brief. Resist the urge to expand scope.
- After this brief closes, the path is clear for Phase 11B legacy deletion or Exec_15 (B.9). Both depend on a healthy sidecar.
