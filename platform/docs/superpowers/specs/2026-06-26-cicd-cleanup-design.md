# CI/CD Pipeline Cleanup & Efficiency — Design Spec

**Date:** 2026-06-26
**Status:** Approved

---

## 1. Objective

Two goals:

1. **Delete** the legacy `platform/scripts/cloud_build_submit.sh` script which is broken (references a non-existent `platform/cloudbuild.yaml`) and represents an unsafe out-of-band deployment path that bypasses CI, migrations, and the smoke gate.
2. **Optimize** the GitHub Actions CI/CD pipeline (`deploy.yml`) for speed and correctness via Docker BuildKit layer caching and path-filtered conditional deployments.

---

## 2. Scope

**Files changed:**
- `platform/scripts/cloud_build_submit.sh` — deleted
- `.github/workflows/deploy.yml` — modified (caching + path filtering)

**Files NOT changed:**
- `.github/workflows/ci.yml` — no changes needed
- `.github/workflows/iac-apply.yml` — no changes needed
- `.github/workflows/brahma-conductor.yml` — no changes needed
- Smoke test script — hardening is explicitly out of scope

---

## 3. Change 1: Delete legacy script

**File:** `platform/scripts/cloud_build_submit.sh`

**Reason:** The script's first step references `platform/cloudbuild.yaml` which no longer exists — it errors immediately. The second step (`gcloud run deploy amjis-web --image ...:latest`) deploys stale `:latest` without running migrations and without a smoke gate, bypassing `deploy.yml` entirely. Per the PA-06 IaC decoupling decision, `deploy.yml` is the sole deployment orchestrator. No replacement needed.

---

## 4. Change 2: Docker BuildKit layer caching

**Applies to:** `deploy.yml` — all 4 deploy jobs + the `build-check` PR job.

### Mechanism

Add `docker/setup-buildx-action@v3` as an explicit step **before** each `docker/build-push-action` step. This is a hard prerequisite — `type=gha` cache does not activate without BuildKit being set up via this action. Add `cache-from` and `cache-to` parameters using GitHub Actions cache (`type=gha`) with `mode=max` (caches intermediate layers, not just the final image).

### Cache scopes

| Job | Cache scope |
|---|---|
| `deploy-web` | `amjis-web` |
| `deploy-sidecar` | `amjis-sidecar` |
| `deploy-mcp` | `amjis-mcp` |
| `deploy-pipeline-job` | `brahma-pipeline` |

### PR build-check

The `build-check` job (runs on PRs, no push) adds `cache-from` only — reads from cache warmed by prior main-branch deploys. Does NOT write cache (`cache-to` omitted) to avoid PR builds polluting the main-branch cache.

### Expected gain

- Web build: ~5–8 min saved (Next.js npm install + build is the heaviest layer)
- Sidecar/MCP: pip install layers cached
- Pipeline job: Python base + pip layers cached

---

## 5. Change 3: Path-filtered conditional deployments

**Applies to:** `deploy.yml` — adds a `changes` job and gates three deploy jobs behind it.

### New `changes` job

```
Trigger: workflow_run conclusion == 'success' OR workflow_dispatch
         (pull_request events do NOT trigger this job — deploy.yml's build-check
         job handles PRs; the changes job and all deploy jobs are gated on
         workflow_run or workflow_dispatch only)
Steps:
  1. actions/checkout@v4 with fetch-depth: 2
  2. git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --name-only HEAD
     → set three outputs (fallback covers first-commit and shallow-root edge
       cases; on error defaults all outputs to 'true' so gated jobs deploy safely)
Outputs:
  sidecar: true | false
  mcp:     true | false
  pipeline: true | false
```

**Fallback policy:** If `git diff HEAD~1 HEAD` exits non-zero (e.g., initial commit, unexpected shallow clone), the step sets all three outputs to `true` — every gated service deploys. Safe over silent-skip.

### Path definitions

| Output | Triggers when these paths change |
|---|---|
| `sidecar` | `platform/python-sidecar/**` |
| `mcp` | `platform-mcp/**` |
| `pipeline` | `platform/python-sidecar/Dockerfile.pipeline`, `platform/python-sidecar/ga_writers/**`, `platform/python-sidecar/requirements*.txt`, `035_DISCOVERY_LAYER/**` |

Note: `pipeline` paths overlap with `sidecar` (`platform/python-sidecar/**` subsumes the pipeline-specific subdirs). This is intentional — a change to `ga_writers/` or `requirements*.txt` should trigger **both** the sidecar image and the pipeline job image, since both consume those files. The overlap is additive, not redundant.

### Job gating

- `deploy-web` — **always runs** (no path filter). Two reasons: (1) it owns the migration step — if a migration is coupled to a web-only code change, gating web behind path changes would require also gating migrations, creating a complex dependency; (2) `platform/**` covers most changes anyway so the skip rate would be negligible.
- `deploy-sidecar` — adds `needs: [changes]`; gated by `sidecar == 'true'`
- `deploy-mcp` — adds `needs: [changes]`; gated by `mcp == 'true'`
- `deploy-pipeline-job` — adds `needs: [changes]`; gated by `pipeline == 'true'`

### `workflow_dispatch` bypass

All gated jobs include `|| github.event_name == 'workflow_dispatch'` in their `if` condition. Manual emergency deploys always push everything regardless of changed paths.

### Practical examples

| What changed | Services deployed |
|---|---|
| `platform/src/**` only | web only |
| `platform/python-sidecar/ga_writers/**` | web + sidecar + pipeline-job |
| `platform-mcp/**` | web + mcp |
| `platform/python-sidecar/Dockerfile.pipeline` | web + sidecar + pipeline-job |
| `workflow_dispatch` (manual) | all four |

---

## 6. Out of scope, explicit deferrals, and acknowledgements

- **Smoke test** remains `continue-on-error: true`. Hardening requires improving the smoke script itself — separate scope.
- **Migration sequencing** — `deploy-web` runs migrations; `deploy-sidecar`/`deploy-mcp`/`deploy-pipeline-job` remain parallel to it. These services don't directly depend on DB schema migrations so the current topology is acceptable.
- **`ci.yml`** — no changes.
- **Dead comment in `deploy-mcp`** — line 317 of `deploy.yml` references `platform-mcp/cloudbuild.yaml` which no longer exists. This comment is a dead reference (same class as the deleted `platform/cloudbuild.yaml`). Cleaning it up is in scope as a one-line comment removal during the same PR.
- **Secret scan** — `cloud_build_submit.sh` contains no secrets (reads from `.env.local` at runtime, not hardcoded). Deletion has no secret scan impact.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| `changes` job with `fetch-depth: 2` fails on shallow clone | `fetch-depth: 2` fetches exactly HEAD + HEAD~1, which is sufficient for `git diff HEAD~1 HEAD`. Merge commits on main have the prior main HEAD as parent. |
| Service deployed with stale image if path filter misses a dependency | `workflow_dispatch` bypass ensures manual full-deploy is always available. Path definitions are inclusive (e.g. all of `platform/python-sidecar/**` triggers sidecar, not just specific subdirs). |
| GHA cache eviction causing cold builds | GitHub Actions cache has a 10 GB limit per repo; eviction falls back gracefully to a full build. No correctness risk. |
