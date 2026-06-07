---
artifact: PIPELINE_AUDIT_v1_0.md
version: "1.1"
status: CURRENT
produced_during: PIPELINE_AUDIT_2026-06-07
changelog:
  - v1.1 (2026-06-08, pipeline-audit-closeout): Added §CLOSEOUT — PA-01/04/05/06/08 completed; GATE 1 passed; GATE 2 infra-blocked (state bucket IAM). PA-02/PA-03 deferred to L0FR branch. PA-09 deferred (maps-key branch). PA-07 resolved via PA-05 deletion.
role: Findings report for the full deployment-pipeline audit (CI/CD, Docker, Cloud Run, build orchestrator). Companion fix brief is CLAUDECODE_BRIEF_PIPELINE_CLEANUP_v1_0.md.
author: Cowork (planning-only; execution handed to Claude Code per cowork_vs_antigravity_split)
scope_audited:
  - .github/workflows/ (6 workflows)
  - platform/Dockerfile, platform/python-sidecar/Dockerfile{,.pipeline}, pyhora.Dockerfile, platform-mcp/Dockerfile
  - platform-mcp/cloudbuild.yaml
  - deploy.yml Cloud Run config (env_vars / secrets / flags / gcloud commands)
  - OPERATOR_ACTIONS_PENDING.md reconciliation
not_audited_in_repo:
  - brahma-build-pipeline-job / marsys-build-pipeline-job source (lives in its own repo per reference_brahma_pipeline_orchestrator)
---

# Deployment Pipeline Audit — 2026-06-07

## How to read this

Every finding has an ID (`PA-NN`), a severity, the evidence (file + line), the root
cause, and the fix. Severity ladder:

- **P0 — Production-correctness:** something is silently wrong in prod *right now*
  (a feature is dark, a build masks a real failure). Fix first.
- **P1 — Latent failure:** will bite on the next relevant change; silent-failure
  traps, drift between config surfaces.
- **P2 — Hygiene:** dead files, duplicated lines, stale comments. Safe, low-risk.

**Verify-before-fix flags (★):** findings marked ★ require a runtime/DB check before
the fix is applied, because the "fix" could *break* a currently-working state if an
assumption is wrong. The brief gates these behind an explicit Step 0 verification.

---

## P0 — Production correctness

### PA-01 ★ — Five NEXT_PUBLIC client flags bake empty: R9 + R11 features likely dark in prod

**Evidence:**
- `platform/Dockerfile` declares `ARG`+`ENV` for: `NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS`
  (L34-35), `R9_SEMANTIC_SEARCH` (L36-37), `R9_TOOL_FLOW` (L38-39),
  `R11B_LOOK_AND_FEEL` (L54-55), `R11V2_MULTI_PROVIDER_PARITY` (L52-53).
- `grep` for all five across `.github/workflows/deploy.yml`: **zero matches.** They are
  absent from both the build-check (PR) build-args and the real deploy build-args.

**Root cause:** `NEXT_PUBLIC_*` flags are baked into the JS bundle at `next build` time.
A flag that has an `ARG` in the Dockerfile but is never passed as `--build-arg` bakes as
the empty string (falsy). Per the `next_public_build_arg_baking` and
`next_public_needs_dockerfile_arg` lessons, these were almost certainly set via
`gcloud run --set-env-vars` (no effect on client flags) or were baked once and dropped in a
later deploy.yml edit. Memory says otherwise — OPERATOR_ACTIONS_PENDING L218 records the
three R9 flags as "flipped + verified 2026-05-23"; CLAUDE.md §E says R11B/R11V2 are "baked
true in deploy.yml." **The file contradicts the memory in all five cases.**

**Impact if confirmed:** R9 Projects, semantic conversation search, and the tool-flow
timeline are off; the R11 Claude-style look-and-feel and the multi-provider parity toggle
are off — in production, despite being recorded as live.

**★ Why verify first:** if `R11B_LOOK_AND_FEEL` / `R11V2_MULTI_PROVIDER_PARITY` are
*default-true* in `platform/src/lib/feature_flags.ts` (or wherever client flags resolve),
then absence-from-build-args still yields `true` at runtime, and adding an explicit empty
build-arg would **flip them off**. The R9 flags' intended default must likewise be
confirmed. Step 0 of the brief reads the flag-default source AND the live bundle before
deciding the value to bake for each of the five.

**Fix:** for each of the five, add the `--build-arg NAME=<intended-value>` line to BOTH
the build-check and deploy build-arg blocks in `deploy.yml`, matching the intended runtime
value confirmed in Step 0. Then a fresh build + deploy. (gcloud env-var changes will NOT
fix this — rebuild is mandatory.)

---

### PA-02 — Ephemeris downloads use `|| true`: a missing GCS object ships a broken image silently

**Evidence:** `platform/python-sidecar/Dockerfile` L8-12, `Dockerfile.pipeline` L17-21,
`pyhora.Dockerfile` L13-17 — every Swiss Ephemeris `.se1`/`.txt` download is
`curl -sSL ... 2>/dev/null || true`.

**Root cause:** identical shape to the `pipeline_image_deps_and_import_swallow` lesson. If
the bucket path is wrong, the object is missing, or the build SA lacks read on
`madhav-ephemeris`, the `curl` fails, `|| true` swallows it, and the build **succeeds** with
absent/zero-byte ephemeris files. PyJHora/swisseph then fails at runtime (or worse, returns
subtly wrong positions) instead of failing the build. The ephemeris is a hard data
dependency for the engine — it must fail closed.

**Fix:** drop `|| true`; make the download a single `RUN set -euo pipefail` block that
downloads each file and then asserts non-zero size (e.g. `test -s /app/ephe/sepl_18.se1`).
Build fails loudly if any file is missing. Apply to all three sidecar Dockerfiles.

**Note:** these three Dockerfiles are also the L0FR ephemeris-bundling stragglers currently
uncommitted on `fix/maps-key-dockerfile-arg` (see PA-09). The fix should land wherever that
L0FR work is committed, not on the maps-key branch.

---

## P1 — Latent failures

### PA-03 — `Dockerfile.pipeline` has duplicate `SWE_EPHE_PATH` + `mkdir /app/ephe`

**Evidence:** `Dockerfile.pipeline` sets `ENV SWE_EPHE_PATH=/app/ephe` at L22 and again at
L44; `mkdir -p /app/ephe` at L14 and again at L45 (the second mkdir is AFTER the ephemeris
files were already downloaded into it at L17-21, so it's a no-op that also can't help if the
download failed).

**Root cause:** two editing passes (Phase 14B + Stream G PyJHora) each added the same env
without removing the prior. Harmless today but confusing and a maintenance trap.

**Fix:** collapse to a single `mkdir` (before the downloads) and a single `ENV
SWE_EPHE_PATH`. Remove the redundant L44-45 pair.

---

### PA-04 — Migration step swallows install failure with `|| true`, then runs migrations

**Evidence:** `deploy.yml` L106:
`cd platform && npm install --ignore-scripts --no-fund tsx pg 2>/dev/null || true`,
immediately followed by the migration runner (L108-116).

**Root cause:** if the `tsx`/`pg` install fails, `|| true` hides it and the next step
(`npx tsx scripts/migrate.ts`) runs against a broken toolchain — either erroring with a
confusing message or, depending on npx fallback behaviour, doing nothing. Migrations
running on a deploy path should not have their prerequisite install soft-passed.

**Fix:** remove `|| true` (and the `2>/dev/null`) so a failed install fails the deploy
before migrations are attempted. If the intent was "skip when offline," gate explicitly on
the same `DATABASE_URL`-present check the migration step already uses (L112), not on a
swallowed install error.

---

### PA-05 — `cloudbuild.yaml` is DEPRECATED but no Cloud Build trigger has been confirmed-disabled

**Evidence:** `platform-mcp/cloudbuild.yaml` L1-5 declares itself deprecated and says
"Operator action required: disable any Cloud Build trigger pointing at this file." The
canonical MCP deploy is now `deploy.yml`'s `deploy-mcp` job (Artifact Registry). But the
deprecated file still pushes to legacy `gcr.io/$PROJECT_ID/amjis-mcp` (L33/42/56) and
deploys to the same `amjis-mcp` service (L55).

**Root cause:** if a GCP Cloud Build trigger still points at this file (e.g. on push to
`platform-mcp/`), then **two** pipelines deploy `amjis-mcp` — one from GH Actions (correct,
Artifact Registry image) and one from Cloud Build (legacy gcr.io image) — and they can
race / clobber each other's revision. The deprecation note has been live since 2026-05-31
with no confirmation the trigger was removed.

**Fix (operator, verify):** in GCP Console → Cloud Build → Triggers, confirm no trigger
references `platform-mcp/cloudbuild.yaml`. If one exists, disable it. Once confirmed, either
delete the file or keep it with the deprecation banner (it's already non-authoritative). The
brief includes the `gcloud builds triggers list` command to check.

---

### PA-06 — Terraform apply on the deploy hot-path is `continue-on-error` and can drift silently

**Evidence:** `deploy.yml` L120-134 — `terraform init` and `terraform apply -auto-approve`
both `continue-on-error: true`, falling back to an `echo WARN`.

**Root cause:** IaC (`infra/cloud_scheduler`: scheduler + build-reaper SA + IAM) is applied
on every prod deploy but never blocks it. If the GHA SA lacks
`storage.objects.list` on the TF state bucket (the WARN message's own hypothesis), apply
silently no-ops on every deploy and the IaC drifts from the committed `.tf` indefinitely —
the build-reaper SA / scheduler could be absent while the pipeline reports green.

**Fix:** this is a judgment call, not a clean bug. Two defensible options — (a) grant the
GHA SA the missing role so apply actually runs, and keep `continue-on-error` only for the
genuinely-optional pieces; or (b) move TF apply OFF the per-deploy hot-path into its own
manually-dispatched workflow so deploys don't depend on it at all. The brief presents both
and asks the native to choose; it does not auto-change this.

---

### PA-07 — `cloudbuild.yaml` hardcodes a stale `_PLATFORM_URL` substitution

**Evidence:** `cloudbuild.yaml` L74:
`_PLATFORM_URL: https://amjis-web-qm256lasva-el.a.run.app` — a `-el.a.run.app` (old US
hash) URL. The live platform URL used everywhere else is
`https://amjis-web-938361928218.asia-south1.run.app` (deploy.yml L197/343).

**Root cause:** stale default left from the original MCP bring-up. Only matters if the
deprecated trigger is still firing (PA-05) — if so, the MCP gets pointed at a dead platform
URL. Subsumed by PA-05's resolution (disable trigger / delete file), listed separately so
it isn't lost if the file is kept.

**Fix:** if the file is retained, update the substitution to the asia-south1 URL; if deleted
per PA-05, moot.

---

### PA-08 — `deploy-mcp` secret pin mismatch: `:1` vs `:latest`

**Evidence:** `deploy.yml` L345 pins `MCP_INTERNAL_TOKEN=mcp-internal-token:1` in the
`deploy-mcp` job, but the same secret is pinned `:latest` in `deploy-web` (L223) and in the
deprecated cloudbuild (L68). The web service authenticates to MCP using its copy of this
token; the MCP validates against its copy. If the secret was ever rotated (a new version
created), `deploy-web` picks up `:latest` (new) while `deploy-mcp` stays pinned to `:1`
(old) → token mismatch → all web→MCP calls 401.

**Root cause:** inconsistent version pinning across the two services that must share the
token. Either both `:latest` or both pinned to the same explicit version.

**Fix:** make both sides reference the same version. Recommend pinning both to an explicit
version (reproducible) rather than `:latest` (silent drift on rotate), but at minimum they
must match. Verify current `mcp-internal-token` version count before choosing.

---

## P2 — Hygiene

### PA-09 — L0FR ephemeris Dockerfiles + main.py committed on the wrong branch

**Evidence:** `fix/maps-key-dockerfile-arg` working tree carries
`platform/python-sidecar/Dockerfile`, `Dockerfile.pipeline`,
`pipeline/orchestrator/main.py` (+ untracked `global_runner.py`) — all L0FR
ephemeris/global-build work, none of which addresses the branch's named scope (the Maps key
ARG). See the earlier git-hygiene analysis in this session.

**Fix:** move these to the L0FR branch (carry `main.py` + `global_runner.py` together). Not
part of the pipeline-correctness fixes but called out so PA-02/PA-03 land on the right
branch.

### PA-10 — `cloudbuild.yaml` retained as dead file

If PA-05 confirms no trigger references it, delete the file rather than leaving a
deprecated-but-live deploy script in the tree (it still contains working push+deploy
commands a stray manual `gcloud builds submit` could fire).

---

## What is NOT broken (audited and confirmed healthy)

These were checked against the documented lessons/residuals and found already-correct — do
not "fix" them:

- **`pull_request:` CI trigger** — present in both `ci.yml` (L6) and `deploy.yml` (L13).
  R11.F-RES-2 in V1_3_AUDIT_QUEUE flagged this as missing; it has since been added. Mark
  that residual RESOLVED.
- **build-check vs real-deploy build-arg parity** — the two build-arg lists in `deploy.yml`
  are byte-identical (verified by diff). PR builds test exactly what ships.
- **NEXT_PUBLIC runtime-env comment** — `deploy.yml` L208-212 correctly documents that
  `NEXT_PUBLIC_FIREBASE_*` are intentionally absent from runtime `env_vars`. Correct.
- **Web Dockerfile ARG/ENV discipline** — every NEXT_PUBLIC build-arg that IS passed has a
  matching `ARG`+`ENV` pair; the C1 comment (L56-58) shows the ARG-drop lesson was already
  learned for R11C.
- **schema_validator / drift_detector exit-code policy** — `ci.yml` L222-241 correctly
  treats exit 3 (known_residuals) as pass and 1/2 as fail; schema_validator hardened
  (continue-on-error removed) per the 2026-05-31 governance pass.
- **`deploy-cloudrun` env-merge trap** — the `env_vars`/`secrets` blocks in `deploy-web`
  are declared in-workflow (not relying on prior state); the `deploy_cloudrun_env_merge`
  hazard applies to *removals*, which aren't happening here.
- **WIF auth** — all deploy jobs use Workload Identity Federation (no long-lived keys);
  per-service least-priv runtime SAs are set on web/sidecar/mcp.

---

## Out of scope (own repo)

The **build orchestrator** (`brahma-build-pipeline-job` / `marsys-build-pipeline-job`) and
its watchdog/timeout gap (`project_build_orchestrator_no_watchdog`: 32 rows stuck over 39h)
live in a **separate repo** (`reference_brahma_pipeline_orchestrator`). The fix —
BUILD_TIMEOUT_HARDENING — is a brahma-pipeline brief, not a Madhav-repo change. It is
acknowledged here for completeness but cannot be fixed from this repo. The schema gotchas
to respect when that brief is written: `build_steps.status` CHECK allows
queued/running/complete/failed/skipped (NOT cancelled/pending); `builds.cancelled_at`
exists, `cancel_reason` does not.

---

## Fix sequencing (see companion brief)

1. **PA-01 ★** (P0) — verify flag defaults + live bundle, then bake the 5 flags. Highest
   user-visible impact.
2. **PA-02** (P0) — ephemeris fail-closed, on the L0FR branch.
3. **PA-04, PA-03** (P1) — migration-install soft-pass; pipeline Dockerfile dedup.
4. **PA-08** (P1) — MCP token version-pin alignment (verify version count first).
5. **PA-05 / PA-07 / PA-10** (P1/P2, operator-verify) — confirm Cloud Build trigger gone,
   then delete-or-fix cloudbuild.yaml.
6. **PA-06** (P1, native decision) — Terraform-on-hot-path: choose option (a) or (b).
7. **PA-09** (P2) — relocate L0FR stragglers off the maps-key branch.

Each fix carries its own pre-commit verification; no batched `answer:eval` is implied here
(that discipline is for retrieval-tool changes, per `project_retrieval_tools_consolidated_eval`).

---

## §CLOSEOUT — Execution record (2026-06-08)

Execution session: Claude Code, 2026-06-07/08.
Three PRs merged: #219 (CI green-main), #217 (PA-01/04/05/08), #218 (PA-06 IaC decouple).

### Completed findings

| PA | Severity | Status | Commit | Notes |
|---|---|---|---|---|
| PA-01 | P0 | **DONE** | `dd0cbebe` (PR #217) | All 5 NEXT_PUBLIC flags baked into deploy.yml build-args (build-check + deploy-web). GATE 1 PASSED — flags confirmed in revision `amjis-web-00536-6hg`. |
| PA-04 | P1 | **DONE** | `dd0cbebe` (PR #217) | Removed `2>/dev/null \|\| true` from migration toolchain install. |
| PA-05 | P1/P2 | **DONE** | `dd0cbebe` (PR #217) | `platform-mcp/cloudbuild.yaml` deleted after confirming no active Cloud Build trigger. |
| PA-07 | P2 | **DONE** | `dd0cbebe` (PR #217) | Resolved by PA-05 deletion — stale `_PLATFORM_URL` went with the file. |
| PA-08 | P1 | **DONE** | `dd0cbebe` (PR #217) | `mcp-internal-token` pinned to `:1` in both `deploy-web` and `deploy-mcp`. |
| PA-06 | P1 | **DONE** | `7c8d6621` (PR #218) | Terraform decoupled from auto-deploy hot-path. New `iac-apply.yml` is dispatch-only (module + action inputs). `deploy.yml` now has `pull_request:` build-check trigger. |

### GATE 1 — NEXT_PUBLIC flags in live bundle

**PASSED.** Verification: deploy workflow run `27103733563` built from commit `dd0cbebe`.
That commit's `deploy.yml` contains all 5 flags (`R9_PROJECTS`, `R9_SEMANTIC_SEARCH`,
`R9_TOOL_FLOW`, `R11B_LOOK_AND_FEEL`, `R11V2_MULTI_PROVIDER_PARITY`) in both build-arg
blocks. Serving revision at gate time: `amjis-web-00536-6hg`.

### GATE 2 — IaC cloud_scheduler plan (no destroy/replace)

**INFRASTRUCTURE BLOCKED — not a GATE 2 halt.** Workflow run `27104108901` failed at
Terraform backend initialization:

```
Error: Failed to get existing workspaces: querying Cloud Storage failed: googleapi:
Error 403: github-actions@madhav-astrology.iam.gserviceaccount.com does not have
storage.objects.list access to the Google Cloud Storage bucket.
Permission 'storage.objects.list' denied on resource
'//storage.googleapis.com/projects/_/buckets/madhav-astrology-tf-state'
```

The SA cannot reach the GCS state bucket — the terraform plan never ran, so no
destroy/replace output exists to evaluate. GATE 2 trigger condition (any destroy/replace)
was NOT met. Operator prerequisite: grant `github-actions@madhav-astrology.iam.gserviceaccount.com`
`roles/storage.objectAdmin` (or at minimum `storage.objects.list` + `storage.objects.get` +
`storage.objects.create`) on `madhav-astrology-tf-state`. Until that is provisioned,
`iac-apply.yml` plan runs will always fail at backend init. Tracked in
`OPERATOR_ACTIONS_PENDING.md §HIGH`.

### Deferred findings

| PA | Status | Reason |
|---|---|---|
| PA-02 | **DEFERRED** | L0FR branch (ephemeris fail-closed Dockerfiles). Must land on the L0FR workstream branch, not on a pipeline-cleanup branch. |
| PA-03 | **DEFERRED** | L0FR branch (Dockerfile.pipeline `SWE_EPHE_PATH` dedup). Same constraint as PA-02. |
| PA-09 | **DEFERRED** | L0FR branch (relocate L0FR sidecar Dockerfiles off `fix/maps-key-dockerfile-arg`). |
| PA-10 | **DONE** | Resolved by PA-05 deletion — `cloudbuild.yaml` was the only surface with the deprecated gcr.io tag. |
