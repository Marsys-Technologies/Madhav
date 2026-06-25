# CI/CD Pipeline Cleanup & Efficiency — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the broken legacy deploy script, add Docker BuildKit layer caching across all build jobs, and add a path-filtering `changes` job so only services with changed source files redeploy on each push to `main`.

**Architecture:** All changes are confined to `.github/workflows/deploy.yml` and the deletion of `platform/scripts/cloud_build_submit.sh`. The `changes` job runs first and sets three boolean outputs (`sidecar`, `mcp`, `pipeline`); the three non-web deploy jobs gain `needs: [changes]` and gate on those outputs. `deploy-web` remains unconditional (it owns migrations). BuildKit caching uses GitHub Actions cache (`type=gha`) with per-service scopes.

**Tech Stack:** GitHub Actions, Docker BuildKit (`docker/setup-buildx-action@v3`, `docker/build-push-action@v6`), `yamllint`, `actionlint`

---

## File Map

| Action | Path | What changes |
|---|---|---|
| Delete | `platform/scripts/cloud_build_submit.sh` | Removed entirely |
| Modify | `.github/workflows/deploy.yml` | 6 targeted edits (see tasks 2–6) |

---

### Task 1: Create feature branch, install actionlint, establish clean baseline

**Files:** none modified

- [ ] **Step 1: Create the feature branch (do this BEFORE any commits)**

```bash
git checkout -b feature/cicd-cleanup-efficiency
```

All commits in Tasks 2–6 land on this branch. The branch is pushed to remote in Task 7.

- [ ] **Step 2: Install actionlint**

```bash
brew install actionlint
```

- [ ] **Step 3: Validate the current workflow passes clean**

```bash
actionlint .github/workflows/deploy.yml
yamllint -d relaxed .github/workflows/deploy.yml
```

Expected: zero errors from either tool. If errors exist, note them — they are pre-existing and not introduced by this work.

---

### Task 2: Delete the legacy deploy script

**Files:**
- Delete: `platform/scripts/cloud_build_submit.sh`

- [ ] **Step 1: Delete the file**

```bash
rm platform/scripts/cloud_build_submit.sh
```

- [ ] **Step 2: Verify it's gone**

```bash
ls platform/scripts/cloud_build_submit.sh 2>/dev/null && echo "STILL EXISTS" || echo "DELETED OK"
```

Expected: `DELETED OK`

- [ ] **Step 3: Commit**

```bash
git add platform/scripts/cloud_build_submit.sh
git commit -m "chore(cicd): delete broken legacy cloud_build_submit.sh

Script referenced platform/cloudbuild.yaml which no longer exists.
deploy.yml is the sole deployment orchestrator per PA-06."
```

---

### Task 3: Remove the dead `platform-mcp/cloudbuild.yaml` comment

**Files:**
- Modify: `.github/workflows/deploy.yml` (lines 314–319)

The comment block above `deploy-mcp` references `platform-mcp/cloudbuild.yaml` which does not exist. Replace the stale line with an accurate one.

- [ ] **Step 1: Edit the comment**

In `.github/workflows/deploy.yml`, find this block:

```yaml
  # ── 4.edge_and_infra_hygiene ──
  # MCP deploy moved off the legacy Cloud Build trigger into GH Actions WIF
  # (acceptance §6: deploy.yml is sole orchestrator). Image still builds via
  # platform-mcp/cloudbuild.yaml or Docker here; trigger is GH Actions only.
  # Image is pinned to Artifact Registry (asia-south1-docker.pkg.dev/...),
  # not legacy gcr.io.
  deploy-mcp:
```

Replace with:

```yaml
  # ── 4.edge_and_infra_hygiene ──
  # MCP deploy moved off the legacy Cloud Build trigger into GH Actions WIF
  # (acceptance §6: deploy.yml is sole orchestrator). Image builds via Docker
  # here; trigger is GH Actions only. Image is pinned to Artifact Registry
  # (asia-south1-docker.pkg.dev/...), not legacy gcr.io.
  deploy-mcp:
```

- [ ] **Step 2: Validate**

```bash
yamllint -d relaxed .github/workflows/deploy.yml
actionlint .github/workflows/deploy.yml
```

Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "chore(cicd): remove dead platform-mcp/cloudbuild.yaml comment reference"
```

---

### Task 4: Add Docker BuildKit caching to all five build jobs

**Files:**
- Modify: `.github/workflows/deploy.yml` — 5 edits, one per job

`docker/setup-buildx-action@v3` must appear as its own step **before** the first `build-push-action` in each job. One setup per job is enough — it stays active for the full job. PRs (`build-check` job) get `cache-from` only; deploy jobs get both `cache-from` and `cache-to: type=gha,mode=max`.

#### 4a — `build-check` job (PR builds)

- [ ] **Step 1: Add `setup-buildx-action` + `cache-from` to `build-check`**

Find:

```yaml
      - name: Build web image (no push)
        uses: docker/build-push-action@v6
        with:
          context: ./platform
          file: ./platform/Dockerfile
          push: false
```

Replace with:

```yaml
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build web image (no push)
        uses: docker/build-push-action@v6
        with:
          context: ./platform
          file: ./platform/Dockerfile
          push: false
          cache-from: type=gha,scope=amjis-web
```

**Note:** The actual file has a `build-args: |` block immediately after `push: false`. The `old_string` above deliberately stops at `push: false` so the Edit tool leaves the existing `build-args` block in place. After the edit the step will read `push: false` → `cache-from` → `build-args: |` — this is valid YAML and correct behaviour.

Then find the pipeline image build step in the same job:

```yaml
      - name: Build pipeline job image (load, no push)
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./platform/python-sidecar/Dockerfile.pipeline
          push: false
          load: true
          tags: brahma-pipeline:pr-check
```

Replace with:

```yaml
      - name: Build pipeline job image (load, no push)
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./platform/python-sidecar/Dockerfile.pipeline
          push: false
          load: true
          tags: brahma-pipeline:pr-check
          cache-from: type=gha,scope=brahma-pipeline
```

#### 4b — `deploy-web` job

- [ ] **Step 2: Add `setup-buildx-action` + caching to `deploy-web`**

Find:

```yaml
      - name: Build and push web image
        uses: docker/build-push-action@v6
        with:
          context: ./platform
          file: ./platform/Dockerfile
          push: true
          tags: |
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-web:${{ github.sha }}
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-web:latest
```

Replace with:

```yaml
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push web image
        uses: docker/build-push-action@v6
        with:
          context: ./platform
          file: ./platform/Dockerfile
          push: true
          tags: |
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-web:${{ github.sha }}
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-web:latest
          cache-from: type=gha,scope=amjis-web
          cache-to: type=gha,mode=max,scope=amjis-web
```

#### 4c — `deploy-sidecar` job

- [ ] **Step 3: Add `setup-buildx-action` + caching to `deploy-sidecar`**

Find:

```yaml
      - name: Build and push sidecar image
        uses: docker/build-push-action@v6
        with:
          context: ./platform/python-sidecar
          file: ./platform/python-sidecar/Dockerfile
          push: true
          tags: |
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-sidecar:${{ github.sha }}
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-sidecar:latest
```

Replace with:

```yaml
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push sidecar image
        uses: docker/build-push-action@v6
        with:
          context: ./platform/python-sidecar
          file: ./platform/python-sidecar/Dockerfile
          push: true
          tags: |
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-sidecar:${{ github.sha }}
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-sidecar:latest
          cache-from: type=gha,scope=amjis-sidecar
          cache-to: type=gha,mode=max,scope=amjis-sidecar
```

#### 4d — `deploy-mcp` job

- [ ] **Step 4: Add `setup-buildx-action` + caching to `deploy-mcp`**

Find:

```yaml
      - name: Build and push MCP image (Artifact Registry, not gcr.io)
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./platform-mcp/Dockerfile
          push: true
          tags: |
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-mcp:${{ github.sha }}
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-mcp:latest
```

Replace with:

```yaml
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push MCP image (Artifact Registry, not gcr.io)
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./platform-mcp/Dockerfile
          push: true
          tags: |
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-mcp:${{ github.sha }}
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-mcp:latest
          cache-from: type=gha,scope=amjis-mcp
          cache-to: type=gha,mode=max,scope=amjis-mcp
```

#### 4e — `deploy-pipeline-job` job

- [ ] **Step 5: Add `setup-buildx-action` + caching to `deploy-pipeline-job`**

Find:

```yaml
      - name: Build and push pipeline job image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./platform/python-sidecar/Dockerfile.pipeline
          push: true
          tags: |
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:${{ github.sha }}
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:latest
```

Replace with:

```yaml
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push pipeline job image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./platform/python-sidecar/Dockerfile.pipeline
          push: true
          tags: |
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:${{ github.sha }}
            asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:latest
          cache-from: type=gha,scope=brahma-pipeline
          cache-to: type=gha,mode=max,scope=brahma-pipeline
```

- [ ] **Step 6: Validate**

```bash
yamllint -d relaxed .github/workflows/deploy.yml
actionlint .github/workflows/deploy.yml
```

Expected: zero errors.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "perf(cicd): add Docker BuildKit GHA layer caching to all five build jobs

Four distinct scopes: amjis-web, amjis-sidecar, amjis-mcp, brahma-pipeline.
build-check PR job reuses amjis-web and brahma-pipeline scopes read-only (no cache-to).
deploy jobs write with mode=max to cache intermediate layers for maximum reuse."
```

---

### Task 5: Add the `changes` path-detection job

**Files:**
- Modify: `.github/workflows/deploy.yml` — insert new job after `build-check`

The `changes` job runs `git diff --name-only HEAD~1 HEAD` to detect which service directories changed, then sets three boolean outputs. It only runs on `workflow_run` success or `workflow_dispatch` (same trigger guard as the deploy jobs). PRs never reach this job.

- [ ] **Step 1: Insert the `changes` job**

In `.github/workflows/deploy.yml`, find the exact block that begins `deploy-web:` (the job name line preceded by its comment):

```yaml
  deploy-web:
    name: Build & Deploy Web
    # Only deploy on workflow_run (CI passed on main) or manual dispatch.
    # pull_request events are handled by the build-check job above.
    if: github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'
```

Insert the following block **immediately before** this block (preserving 2-space job-level indentation):

```yaml
  # ── Path-change detection — sets sidecar/mcp/pipeline outputs ───────────────
  # Runs only on workflow_run success or manual dispatch (same guard as deploy
  # jobs). pull_request events never reach this job. Fallback: if HEAD~1
  # doesn't exist (first commit / shallow root), all three outputs default to
  # 'true' so gated jobs deploy safely rather than silently skip.
  changes:
    name: Detect changed paths
    if: github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    permissions:
      contents: read
    outputs:
      sidecar: ${{ steps.diff.outputs.sidecar }}
      mcp: ${{ steps.diff.outputs.mcp }}
      pipeline: ${{ steps.diff.outputs.pipeline }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Detect changed paths
        id: diff
        run: |
          CHANGED=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --name-only HEAD)
          echo "=== Changed files ==="
          printf '%s\n' "$CHANGED"
          echo "====================="

          sidecar=false
          mcp=false
          pipeline=false

          if printf '%s\n' "$CHANGED" | grep -q '^platform/python-sidecar/'; then
            sidecar=true
          fi

          if printf '%s\n' "$CHANGED" | grep -q '^platform-mcp/'; then
            mcp=true
          fi

          if printf '%s\n' "$CHANGED" | grep -qE \
            '^(platform/python-sidecar/Dockerfile\.pipeline|platform/python-sidecar/ga_writers/|platform/python-sidecar/requirements|035_DISCOVERY_LAYER/)'; then
            pipeline=true
          fi

          echo "sidecar=$sidecar" >> "$GITHUB_OUTPUT"
          echo "mcp=$mcp" >> "$GITHUB_OUTPUT"
          echo "pipeline=$pipeline" >> "$GITHUB_OUTPUT"

          echo "=== Outputs ==="
          echo "sidecar=$sidecar  mcp=$mcp  pipeline=$pipeline"
  # ── /Path-change detection ───────────────────────────────────────────────────

```

- [ ] **Step 2: Validate**

```bash
yamllint -d relaxed .github/workflows/deploy.yml
actionlint .github/workflows/deploy.yml
```

Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "feat(cicd): add changes job to detect which service directories changed

Outputs: sidecar / mcp / pipeline (bool). Falls back to true on
shallow-root git diff failure so gated jobs never silently skip."
```

---

### Task 6: Gate `deploy-sidecar`, `deploy-mcp`, and `deploy-pipeline-job` behind `changes`

**Files:**
- Modify: `.github/workflows/deploy.yml` — 3 targeted edits

`deploy-web` stays unconditional. The three gated jobs add `needs: [changes]` and update their `if:` to also require the relevant `changes` output to be `'true'` — unless triggered by `workflow_dispatch` (manual deploys always push everything).

#### 6a — `deploy-sidecar`

- [ ] **Step 1: Update `deploy-sidecar` job header**

Find:

```yaml
  deploy-sidecar:
    name: Build & Deploy Sidecar
    if: github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
```

Replace with:

```yaml
  deploy-sidecar:
    name: Build & Deploy Sidecar
    needs: [changes]
    if: (github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success') && (github.event_name == 'workflow_dispatch' || needs.changes.outputs.sidecar == 'true')
    runs-on: ubuntu-latest
```

#### 6b — `deploy-mcp`

- [ ] **Step 2: Update `deploy-mcp` job header**

Find:

```yaml
  deploy-mcp:
    if: github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'
    name: Build & Deploy MCP
    runs-on: ubuntu-latest
```

Replace with:

```yaml
  deploy-mcp:
    needs: [changes]
    if: (github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success') && (github.event_name == 'workflow_dispatch' || needs.changes.outputs.mcp == 'true')
    name: Build & Deploy MCP
    runs-on: ubuntu-latest
```

#### 6c — `deploy-pipeline-job`

- [ ] **Step 3: Update `deploy-pipeline-job` job header**

Find:

```yaml
  deploy-pipeline-job:
    name: Build & Deploy Pipeline Job Image
    if: github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
```

Replace with:

```yaml
  deploy-pipeline-job:
    name: Build & Deploy Pipeline Job Image
    needs: [changes]
    if: (github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success') && (github.event_name == 'workflow_dispatch' || needs.changes.outputs.pipeline == 'true')
    runs-on: ubuntu-latest
```

- [ ] **Step 4: Validate**

```bash
yamllint -d relaxed .github/workflows/deploy.yml
actionlint .github/workflows/deploy.yml
```

Expected: zero errors.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "feat(cicd): path-filter sidecar/mcp/pipeline-job deploys

deploy-sidecar: only when platform/python-sidecar/** changed
deploy-mcp: only when platform-mcp/** changed
deploy-pipeline-job: only when Dockerfile.pipeline / ga_writers / requirements / 035_DISCOVERY_LAYER changed
workflow_dispatch always deploys all services regardless of changed paths."
```

---

### Task 7: Final validation

- [ ] **Step 1: Full linting pass**

```bash
yamllint -d relaxed .github/workflows/deploy.yml
actionlint .github/workflows/deploy.yml
```

Expected: zero errors from both tools.

- [ ] **Step 2: Confirm the legacy script is gone and no other scripts reference it**

```bash
grep -r "cloud_build_submit" . --include="*.sh" --include="*.md" --include="*.yml" --include="*.yaml" -l 2>/dev/null | grep -v node_modules
```

Expected: no output (or only this plan file, which is documentation).

- [ ] **Step 3: Confirm all 5 build jobs have `setup-buildx-action`**

```bash
grep -c "setup-buildx-action" .github/workflows/deploy.yml
```

Expected: `5`

- [ ] **Step 4: Confirm `changes` job outputs are wired to all 3 gated jobs**

```bash
grep -c "needs.changes.outputs" .github/workflows/deploy.yml
```

Expected: `3`

- [ ] **Step 5: Push the feature branch**

```bash
git push -u origin feature/cicd-cleanup-efficiency
```

Open the Actions tab in GitHub and confirm:
- CI workflow (`ci.yml`) triggers on the branch push
- No deploy workflow triggers (deploy only fires on `main` via `workflow_run`)
- All CI jobs pass

- [ ] **Step 6: Open PR to `main`**

```bash
gh pr create \
  --title "chore(cicd): BuildKit caching + path filtering + delete legacy script" \
  --body "## Summary
- Deletes broken \`cloud_build_submit.sh\` (referenced non-existent \`cloudbuild.yaml\`)
- Adds Docker BuildKit GHA layer caching to all 5 build jobs (~5–8 min saved per deploy)
- Adds \`changes\` job; gates sidecar/mcp/pipeline-job deploys on changed source paths
- Removes dead \`platform-mcp/cloudbuild.yaml\` comment

## Test plan
- [ ] CI passes on this PR
- [ ] \`build-check\` PR job completes (web + pipeline images build, cache warms)
- [ ] Merge to main → watch deploy workflow; confirm \`changes\` job runs and all 4 deploy jobs run (first deploy after merge — nothing yet cached, everything deploys)
- [ ] Second merge with only \`platform/src/\` changes → confirm only \`deploy-web\` runs"
```
