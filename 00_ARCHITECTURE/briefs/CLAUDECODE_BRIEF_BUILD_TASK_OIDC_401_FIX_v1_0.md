---
artifact: CLAUDECODE_BRIEF_BUILD_TASK_OIDC_401_FIX_v1_0.md
brief_id: BUILD_TASK_OIDC_401_FIX
version: 1.0
status: ACTIVE
authored_at: 2026-06-01
authored_by: cowork-planner
implementation_surface: Claude Code in Google Antigravity IDE (diagnosis + code) + operator (IAM/env)
human_gate: PR-to-main for code. IAM/env changes are operator-gated.
why: >
  The 2026-06-01 production native build could not be triggered through the real path:
  Cloud Tasks → POST /api/build/task returned a persistent 401. The operator bypassed it
  by executing the marsys-build-pipeline-job Cloud Run Job directly. The job-direct path
  works but means the autonomous build trigger is broken in production.
may_touch:
  - platform/src/app/api/build/task/route.ts
  - platform/src/lib/build/trigger.ts
  - platform/src/lib/build/jobInvoker.ts
  - platform/src/app/api/build/__tests__/task_route.test.ts
  - platform/scripts/governance/edge_security_smoke.sh   (if the OIDC assertion changes)
must_not_touch:
  - platform/python-sidecar/                              (engine — unrelated)
  - platform/supabase/migrations/
  - src/                                                  (frontend)
hard_bans:
  - Do NOT "fix" this by re-introducing BUILD_TASK_AUTH_BYPASS or any bypass. The endpoint
    must remain authenticated.
  - No Anthropic models.
prime_directive: only computed facts. no narrative.
---

# Cloud Tasks → /api/build/task OIDC 401 — diagnosis + fix

## 1 · Symptom

`POST /api/build/task` returns **401** for Cloud-Tasks-dispatched requests in production.
The handler's `isAuthorized(request)` returns false. Operator workaround was to run the
`marsys-build-pipeline-job` Cloud Run Job directly — proving the engine and job are fine;
only the HTTP trigger auth is broken.

## 2 · How the auth actually works today (read before changing anything)

`platform/src/app/api/build/task/route.ts` `isAuthorized()`:

1. Requires header `X-CloudTasks-QueueName` to be present (else false).
2. Requires `Authorization: Bearer <jwt>` (else false).
3. Requires `BUILD_TASK_AUDIENCE` env to be set (else false).
4. Base64-decodes the JWT payload and asserts `payload.aud === BUILD_TASK_AUDIENCE`
   (parsing only — **no signature crypto in the app**; the comment says "Cloud Run
   verifies the JWT signature").

That last assumption is the likely fault line. **The app reads the `Authorization` header
to parse the audience — but if the Cloud Run service is deployed `--no-allow-unauthenticated`,
Cloud Run consumes and strips the OIDC `Authorization` header during its own IAM check
before the request reaches the container.** The app then sees no bearer → returns false → 401.

So there are two mutually-exclusive correct designs, and the bug is being half-in-each:

- **Design A — Cloud Run IAM does the auth.** Service is private
  (`--no-allow-unauthenticated`); the Cloud Tasks SA holds `roles/run.invoker`; Cloud Run
  validates the OIDC token and strips it. The app must then authorise on the
  `X-CloudTasks-*` headers ALONE (it cannot see the bearer). 
- **Design B — app does the auth.** Service is public
  (`--allow-unauthenticated`); the OIDC token passes through; the app validates the bearer
  audience (ideally with real signature verification against Google's JWKS, not just a
  base64 audience parse).

Current code is Design-B-shaped (reads the bearer) but the service is almost certainly
deployed Design-A-shaped (private), so the bearer never arrives. That is the 401.

## 3 · Diagnosis steps (executor: confirm before choosing a fix)

Run these and record findings in the PR description. **Read-only — no changes yet.**

1. Service auth posture:
   ```bash
   gcloud run services get-iam-policy amjis-web --region asia-south1 --project madhav-astrology
   gcloud run services describe amjis-web --region asia-south1 --project madhav-astrology \
     --format='value(spec.template.metadata.annotations,status.conditions)'
   ```
   Is `allUsers` an invoker? Is the service public or private?
2. Does the Cloud Tasks SA have `run.invoker` on `amjis-web`? Identify the SA the queue
   `marsys-build-queue` uses for OIDC (check the queue/task config in `trigger.ts` /
   `jobInvoker.ts` — `BUILD_TASK_AUDIENCE` and the OIDC `serviceAccountEmail`).
3. Is `BUILD_TASK_AUDIENCE` set on `amjis-web`, and does it equal the audience the queue
   signs the token with?
   ```bash
   gcloud run services describe amjis-web --region asia-south1 --project madhav-astrology \
     --format='value(spec.template.spec.containers[0].env)' | tr ',' '\n' | grep -i AUDIENCE
   ```
4. Reproduce: capture the actual inbound headers at the handler for one Cloud-Tasks
   request (temporary `console.log(Object.fromEntries(request.headers))` in a scratch
   branch, or Cloud Run request logs). **Confirm empirically whether `Authorization`
   reaches the container.** This single observation decides Design A vs B.

## 4 · Recommended fix — Design A (IAM-enforced, app trusts the platform)

Design A is the GCP-idiomatic and more secure path: Cloud Run does cryptographic OIDC
verification; the app does not hand-roll JWT parsing.

1. Ensure `amjis-web` is private (`--no-allow-unauthenticated`) and the Cloud Tasks OIDC
   SA has `roles/run.invoker` (operator IAM action).
2. Rewrite `isAuthorized()` to authorise on platform-verified signals the app CAN see:
   presence of `X-CloudTasks-QueueName` matching the expected queue name
   (`marsys-build-queue`), and optionally `X-CloudTasks-TaskName`. Drop the bearer-parse
   branch entirely (it cannot work behind IAM). Document that signature verification is
   delegated to Cloud Run IAM.
3. Update `task_route.test.ts`: the existing security regression test asserts
   `BUILD_TASK_AUTH_BYPASS` has zero effect — keep that. Add a test that the handler
   authorises on the queue header and 401s without it.
4. Keep `edge_security_smoke.sh` honest: if it asserted a bearer-audience check, update it
   to assert the IAM posture instead.

### Alternative — Design B (public service, app verifies token properly)

Only if the native wants `amjis-web` to stay public. Then the app MUST do real OIDC
verification: fetch Google's JWKS, verify the JWT signature, `iss`, `exp`, and `aud`
(not just a base64 `aud` string compare). Add a vetted JWT lib; do not ship hand-rolled
crypto. This is more code and more attack surface than Design A — recommend against unless
there's a reason the service must be public.

## 5 · Acceptance criteria

1. Root cause documented in the PR with the §3.4 header observation (bearer present/absent).
2. A real Cloud-Tasks-dispatched `POST /api/build/task` returns 2xx and dispatches the job
   — verified by triggering a native build through `/api/build/start` (NOT job-direct) and
   watching it reach `build_complete`.
3. Unauthenticated / forged requests still 401 (security regression test green).
4. `BUILD_TASK_AUTH_BYPASS` still has zero effect (existing test stays green).
5. `pytest`/`vitest` suites green; `tsc --noEmit` clean.

## 6 · Related operator hygiene (separate, do now — not part of this PR)

`BUILD_TASK_AUTH_BYPASS=test` is currently set on `amjis-web`. The code already neutralised
it (it grants nothing and logs a SECURITY alert), so removal is pure hygiene to silence the
alert:

```bash
gcloud run services update amjis-web --region asia-south1 --project madhav-astrology \
  --remove-env-vars BUILD_TASK_AUTH_BYPASS
```

(Remember `deploy-cloudrun@v2` merges env vars — removing the line from `deploy.yml` alone
won't drop the running var; the explicit `--remove-env-vars` is required.
[[deploy-cloudrun-env-merge]])

## 7 · Antigravity kickoff prompt (paste verbatim)

```
Execute CLAUDECODE_BRIEF_BUILD_TASK_OIDC_401_FIX_v1_0.md at
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BUILD_TASK_OIDC_401_FIX_v1_0.md.

Start with §3 diagnosis — READ ONLY. Capture the inbound headers of a real Cloud Tasks
request and confirm whether the Authorization bearer reaches the container. Paste that
finding before writing any fix.

Then implement Design A (§4) unless the header observation or the native says otherwise:
authorise on X-CloudTasks-QueueName, drop the in-app bearer parse, rely on Cloud Run IAM
for signature verification. Keep the BUILD_TASK_AUTH_BYPASS zero-effect test green; add a
queue-header auth test.

Do NOT reintroduce any auth bypass. Do NOT run gcloud mutations (IAM/env are operator
actions — list the exact commands in the PR for the native to run). Halt at PR-to-main.

Verify by triggering a native build through /api/build/start (not job-direct) and showing
it reaches build_complete. Paste the PR URL + the 5 acceptance criteria checked.
```

---

*End of CLAUDECODE_BRIEF_BUILD_TASK_OIDC_401_FIX_v1_0.md*
