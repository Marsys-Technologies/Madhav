---
artifact: CLAUDECODE_BRIEF_PIPELINE_CLEANUP_v1_0.md
version: "1.0"
status: COMPLETE
produced_during: PIPELINE_AUDIT_2026-06-07
role: Executable brief for Claude Code (Antigravity IDE) to fix the deployment-pipeline findings in PIPELINE_AUDIT_v1_0.md.
executor: Claude Code in Google Antigravity IDE (NOT the CLI)
findings_source: 00_ARCHITECTURE/PIPELINE_AUDIT_v1_0.md
hard_constraints:
  - "Each fix is its own commit with its own pre-commit verification. Do NOT batch unrelated findings into one commit."
  - "PA-01 and PA-05/PA-06/PA-08 are gated behind a verification step that can CANCEL the fix. Do not skip the gate."
  - "NEXT_PUBLIC flag fixes require a fresh build + deploy to take effect — gcloud env-var changes do nothing. Do not 'fix' a client flag with --set-env-vars."
  - "PA-02/PA-03 (ephemeris Dockerfiles) land on the L0FR branch, NOT on fix/maps-key-dockerfile-arg."
  - "Build orchestrator (brahma-build-pipeline-job) is a DIFFERENT repo — out of scope here."
---

# Brief — Deployment Pipeline Cleanup

Read `00_ARCHITECTURE/PIPELINE_AUDIT_v1_0.md` first for the full evidence and rationale on
each finding. This brief is the execution plan. Work the findings in the order below. Every
step's commands are paste-ready (Antigravity runs git + terminal inline).

Repo root: `/Users/Dev/Vibe-Coding/Apps/Madhav`. All paths below are relative to it.

---

## STEP 0 — Branch setup + flag-default verification (BLOCKING GATE for PA-01)

### 0.A — Create the working branch off main

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git switch main && git pull --ff-only origin main
git switch -c fix/pipeline-cleanup
```

### 0.B — ★ Verify the intended runtime value for each of the 5 dark flags (PA-01)

You must determine, for each flag, what value SHOULD be baked — do not assume. Read the
client flag-resolution source and the running bundle.

```bash
# 1. Where do client flags resolve + what are their defaults?
grep -rn "R9_PROJECTS\|R9_SEMANTIC_SEARCH\|R9_TOOL_FLOW\|R11B_LOOK_AND_FEEL\|R11V2_MULTI_PROVIDER_PARITY" \
  platform/src/lib/feature_flags.ts platform/src/lib/flags* 2>/dev/null

# 2. What does the LIVE bundle currently have baked? (the ground truth)
#    Confirm the serving revision first, then grep the served JS.
gcloud run services describe amjis-web --region asia-south1 --project madhav-astrology \
  --format='value(status.traffic[0].revisionName)'
#    Then load the app and check the flag values in the browser console, OR
#    curl the homepage and grep the bundled flag strings.
```

**Decision table to fill BEFORE editing deploy.yml** — for each flag record:
`(a) default in feature_flags.ts`, `(b) value baked in live bundle`, `(c) intended value`.

- If a flag is **default-true** in source AND you want it on → the safest fix is to bake
  it `=true` explicitly (matches intent, removes the silent-empty ambiguity).
- If a flag is **default-false** in source and is meant to be ON → it is currently dark;
  bake `=true`.
- If any flag is intended to stay OFF → leave it out (do NOT add an empty build-arg) OR
  bake `=false` explicitly for clarity. **Never bake an empty string.**

**GATE:** if the live bundle already shows a flag as the intended value (e.g. R11B/R11V2
are default-true and already render the Claude-style UI in prod), then that flag is NOT
broken — record it as a no-op and exclude it from the PA-01 fix. Only flags whose live
value ≠ intended value get baked. Report the filled decision table in the commit message.

---

## STEP 1 — PA-01: Bake the confirmed-dark NEXT_PUBLIC flags (P0)

For each flag confirmed dark in Step 0.B, add a build-arg line to BOTH build-arg blocks in
`.github/workflows/deploy.yml`:
- the **build-check** job (around L56-73)
- the **deploy-web** job (around L155-172)

Match the value to the Step 0 decision table. Example (adjust to your confirmed set):

```yaml
            NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS=true
            NEXT_PUBLIC_MARSYS_FLAG_R9_SEMANTIC_SEARCH=true
            NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW=true
            NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL=true
            NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY=true
```

The `ARG`+`ENV` pairs already exist in `platform/Dockerfile` (L34-39, L52-55) — no
Dockerfile change needed for these five. Verify:

```bash
for f in R9_PROJECTS R9_SEMANTIC_SEARCH R9_TOOL_FLOW R11B_LOOK_AND_FEEL R11V2_MULTI_PROVIDER_PARITY; do
  echo "== $f =="
  echo "  Dockerfile ARG: $(grep -c "ARG NEXT_PUBLIC_MARSYS_FLAG_$f" platform/Dockerfile)"
  echo "  deploy.yml build-args: $(grep -c "NEXT_PUBLIC_MARSYS_FLAG_$f=" .github/workflows/deploy.yml)"
done
# Each fixed flag should now show Dockerfile ARG=1 and deploy.yml build-args=2 (build-check + deploy).
```

Commit:

```bash
git add .github/workflows/deploy.yml
git commit -m "fix(deploy): bake dark NEXT_PUBLIC R9/R11 flags into prod build-args (PA-01)

R9_PROJECTS, R9_SEMANTIC_SEARCH, R9_TOOL_FLOW, R11B_LOOK_AND_FEEL,
R11V2_MULTI_PROVIDER_PARITY were declared as Dockerfile ARGs but never passed as
--build-arg, so they baked empty (falsy). gcloud env-var sets do nothing for client
flags. Decision table (default/live/intended) in PIPELINE_AUDIT PA-01.
Effect requires a fresh build+deploy — this commit triggers it on merge to main."
```

**Operator note (post-merge):** these only go live after the merge-to-main deploy rebuilds
the bundle. A `gcloud` env change will NOT activate them.

---

## STEP 2 — PA-04: Remove migration-install soft-pass (P1)

In `.github/workflows/deploy.yml`, the "Install migration runner deps" step (~L105-106):

```yaml
# BEFORE
      - name: Install migration runner deps
        run: cd platform && npm install --ignore-scripts --no-fund tsx pg 2>/dev/null || true
# AFTER
      - name: Install migration runner deps
        run: cd platform && npm install --ignore-scripts --no-fund tsx pg
```

The next step already guards on `DATABASE_URL` being present (L112), so removing the
soft-pass does not break the offline-skip case — migrations skip via the URL check, not via
a swallowed install error.

```bash
git add .github/workflows/deploy.yml
git commit -m "fix(deploy): fail loudly if migration toolchain install fails (PA-04)

Removed '2>/dev/null || true' from the tsx/pg install so a broken toolchain fails the
deploy before migrate.ts runs against it. Offline-skip still handled by the existing
DATABASE_URL-present guard."
```

---

## STEP 3 — PA-08: Align MCP internal-token version pin (P1)

First check how many versions of the secret exist:

```bash
gcloud secrets versions list mcp-internal-token --project madhav-astrology \
  --format='table(name,state,createTime)'
```

In `deploy.yml`, `deploy-web` uses `mcp-internal-token:latest` (L223) and `deploy-mcp` uses
`mcp-internal-token:1` (L345). Make them match. Recommended: pin BOTH to the explicit
current version (reproducible; avoids silent drift on rotate). Replace both with the same
`:N`. If you prefer `:latest`, set both to `:latest` — but the two MUST be identical or
web→MCP calls 401 after any rotation.

```bash
git add .github/workflows/deploy.yml
git commit -m "fix(deploy): align mcp-internal-token version pin across web+mcp (PA-08)

deploy-web pinned :latest while deploy-mcp pinned :1 — a rotation would mismatch the
shared token and 401 all web->MCP calls. Both now pinned to <VERSION>."
```

---

## STEP 4 — PA-05 / PA-07 / PA-10: Resolve the deprecated cloudbuild.yaml (P1/P2, operator-verify)

### 4.A — ★ Confirm no Cloud Build trigger references the deprecated file (GATE)

```bash
gcloud builds triggers list --project madhav-astrology \
  --format='table(name,filename,github.name,disabled)' | grep -i cloudbuild || echo "no cloudbuild-file triggers"
```

- If a trigger references `platform-mcp/cloudbuild.yaml`: disable it
  (`gcloud builds triggers update <NAME> --disabled` or delete in console), THEN proceed.
- If none: proceed to delete the file.

### 4.B — Delete the dead file (after 4.A confirms it's unreferenced)

```bash
git rm platform-mcp/cloudbuild.yaml
git commit -m "chore(mcp): delete deprecated cloudbuild.yaml (PA-05/PA-07/PA-10)

Authoritative MCP deploy is deploy.yml deploy-mcp (Artifact Registry). The file was
DEPRECATED 2026-05-31, still pushed to legacy gcr.io, deployed the same amjis-mcp
service (clobber/race risk), and hardcoded a stale _PLATFORM_URL. Confirmed no Cloud
Build trigger references it before deletion."
```

If for any reason the file must be kept, instead update L74 `_PLATFORM_URL` to
`https://amjis-web-938361928218.asia-south1.run.app` (PA-07) and leave the deprecation
banner.

---

## STEP 5 — PA-06: Terraform-on-hot-path (P1, NATIVE DECISION REQUIRED — do not auto-fix)

Do NOT change this without a native decision. Surface the two options and STOP:

- **Option (a):** grant the GHA SA `roles/storage.objectAdmin` (or narrower
  `objectViewer`+`objectCreator`) on `madhav-astrology-tf-state` so `terraform apply`
  actually runs on deploy; keep `continue-on-error` only on the genuinely-optional pieces.
- **Option (b):** remove the `terraform init`/`apply` steps from `deploy-web` and move them
  to a separate `workflow_dispatch` IaC workflow so prod deploys don't silently depend on
  (and silently skip) IaC apply.

Write the recommendation into the commit message of a *docs-only* note or wait for the
native to pick. Leave `deploy.yml` untouched for this finding until then.

---

## STEP 6 — PA-02 / PA-03: Ephemeris Dockerfile fail-closed + dedup (P0/P1) — ON THE L0FR BRANCH

These three files are L0FR ephemeris-bundling work. They are currently uncommitted on
`fix/maps-key-dockerfile-arg`. They must NOT be committed on `fix/pipeline-cleanup` either.
Land them on the L0FR branch.

```bash
# Determine the L0FR branch (memory: feature/l0fr-stream-a-infrastructure may exist)
git branch -a | grep -i l0fr
# Move the 3 sidecar Dockerfiles (and any companion L0FR files) to that branch via
# stash/switch/pop or cherry-pick, per the git-hygiene plan from the earlier session.
```

### 6.A — PA-02: fail-closed ephemeris download (all 3 sidecar Dockerfiles)

Replace the five `curl ... || true` lines in EACH of `platform/python-sidecar/Dockerfile`,
`Dockerfile.pipeline`, `pyhora.Dockerfile` with a single fail-closed block:

```dockerfile
# Swiss Ephemeris data files — bundled from GCS. Fail the build if any file is missing
# or zero-byte (do NOT '|| true' — a broken ephemeris ships a silently-wrong engine).
RUN set -euo pipefail; \
    mkdir -p /app/ephe; \
    for f in sepl_18.se1 semo_18.se1 seas_18.se1 sefstars.txt seleapsec.txt; do \
      curl -fSL -o "/app/ephe/$f" "https://storage.googleapis.com/madhav-ephemeris/se1/$f"; \
      test -s "/app/ephe/$f" || { echo "FATAL: /app/ephe/$f missing or empty"; exit 1; }; \
    done
ENV SWE_EPHE_PATH=/app/ephe
```

(`curl -f` fails on HTTP errors; `set -euo pipefail` + `test -s` makes a missing/empty file
abort the build.)

### 6.B — PA-03: remove the duplicate ENV/mkdir in Dockerfile.pipeline

After 6.A collapses the download block, ensure `Dockerfile.pipeline` has exactly ONE
`ENV SWE_EPHE_PATH=/app/ephe` and no leftover standalone `mkdir -p /app/ephe` /
`ENV SWE_EPHE_PATH` pair at the old L44-45 location.

### 6.C — Verify the images still build

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
docker build -f platform/python-sidecar/Dockerfile -t sidecar-test platform/python-sidecar
docker build -f platform/python-sidecar/Dockerfile.pipeline -t pipeline-test .
docker build -f platform/python-sidecar/pyhora.Dockerfile -t pyhora-test platform/python-sidecar
# All three must succeed. If the ephemeris bucket is unreachable from the build host, that
# is now a HARD failure by design — fix the bucket/credentials, do not re-add '|| true'.
```

Commit on the L0FR branch:

```bash
git add platform/python-sidecar/Dockerfile platform/python-sidecar/Dockerfile.pipeline platform/python-sidecar/pyhora.Dockerfile
git commit -m "fix(sidecar): ephemeris download fails closed + dedup pipeline ENV (PA-02/PA-03)

Replaced 'curl ... || true' with a set -euo pipefail loop that asserts non-zero file
size, so a missing GCS object aborts the build instead of shipping a broken engine.
Collapsed Dockerfile.pipeline's duplicate SWE_EPHE_PATH/mkdir."
```

---

## STEP 7 — Push + PR(s)

```bash
# Pipeline-cleanup branch (Steps 1-4):
git switch fix/pipeline-cleanup
git push -u origin fix/pipeline-cleanup
# Open PR to main. CI (ci.yml) + deploy.yml build-check run on the PR.

# L0FR branch (Step 6): push + PR per the L0FR workstream's own merge policy.
```

The `pull_request:` build-check in `deploy.yml` will build the web image with the new
build-args — confirm it goes green before merge. After merge to main, the `workflow_run`
deploy rebuilds + ships, which is what actually activates the PA-01 flags.

---

## Post-merge verification (operator / next session)

1. **PA-01:** after the main deploy completes, confirm the serving revision and that the
   five flags now resolve to their intended values in the live bundle (same check as Step
   0.B, expecting the corrected values).
2. **PA-08:** confirm web→MCP calls succeed (no 401) after the token-pin change.
3. Update `OPERATOR_ACTIONS_PENDING.md`: correct the R9-flags "flipped 2026-05-23" line
   (PA-01 showed they were never baked) and mark R11.F-RES-2 (`pull_request:` trigger)
   RESOLVED in `V1_3_AUDIT_QUEUE_v1_0.md`.
4. **Out of scope reminder:** the build-orchestrator watchdog gap
   (`project_build_orchestrator_no_watchdog`) is a separate-repo BUILD_TIMEOUT_HARDENING
   brief — not addressed here.
