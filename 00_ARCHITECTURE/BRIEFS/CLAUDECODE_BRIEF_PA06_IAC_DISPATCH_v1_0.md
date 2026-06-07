---
artifact: CLAUDECODE_BRIEF_PA06_IAC_DISPATCH_v1_0.md
version: "1.0"
status: READY_FOR_EXECUTION
produced_during: PIPELINE_AUDIT_2026-06-07
role: Executable brief for Claude Code (Antigravity) to resolve PA-06 — move Terraform off the deploy hot-path into a dispatch-only IaC workflow.
executor: Claude Code in Google Antigravity IDE (NOT the CLI)
finding: PA-06 (PIPELINE_AUDIT_v1_0.md)
native_decision: Option (b) — decouple. Confirmed 2026-06-07.
hard_constraints:
  - "deploy-web must no longer run terraform. After this brief, app deploys do NOT touch IaC."
  - "The new IaC workflow is workflow_dispatch ONLY — never on push/PR/workflow_run. IaC apply is a deliberate human-triggered act."
  - "apply must be plan-visible-before-apply: a plan step runs and is readable in the run log before apply executes. Default the dispatch input to 'plan' so an accidental run-without-thinking does NOT apply."
  - "Reuse the existing infra/scheduler/apply.sh convention {plan|apply}. Do not invent a new pattern."
  - "WIF auth only (no long-lived keys), matching deploy.yml."
---

# Brief — PA-06: Decouple Terraform from the deploy hot-path

**Decision (native, confirmed):** Option (b). App deploys become fast + deterministic and
never run `terraform apply`. IaC changes (`infra/cloud_scheduler`: Cloud Scheduler +
build-reaper SA + IAM) move to a standalone, manually-dispatched workflow with a visible
plan before apply.

Read PA-06 in `00_ARCHITECTURE/PIPELINE_AUDIT_v1_0.md` for rationale. This brief executes it.

Repo root: `/Users/Dev/Vibe-Coding/Apps/Madhav`.

---

## Pre-flight facts (verified 2026-06-07, ground your edits on these)

- The TF steps to remove are `deploy.yml` **lines 119-134** (the `# ── A-S8: Terraform …`
  block): "Set up Terraform", "Terraform init (cloud_scheduler)", "Terraform apply
  (cloud_scheduler)" — all currently `continue-on-error: true`.
- Because they are already `continue-on-error`, the deploy path does NOT hard-depend on TF
  running. Removing them cannot break a deploy that's currently passing — it only removes a
  silently-skipped step. (This is the safety argument for the decouple.)
- `infra/cloud_scheduler/backend.tf` → GCS backend, bucket `madhav-astrology-tf-state`,
  prefix `infra/cloud_scheduler`.
- `infra/cloud_scheduler/main.tf` takes vars `gcp_project` + `gcp_region` (per the
  build_reaper.tf / scheduler convention). Confirm the exact var names by reading
  `infra/cloud_scheduler/*.tf` before writing the apply step — match them.
- Existing convention to mirror: `infra/scheduler/apply.sh` is a
  `{plan|apply|destroy}` idempotent wrapper. There is NO `infra/cloud_scheduler/apply.sh`
  yet — Step 1 creates one in that style.
- WIF in deploy.yml: provider
  `projects/938361928218/locations/global/workloadIdentityPools/github/providers/github-actions`,
  SA `github-actions@madhav-astrology.iam.gserviceaccount.com`.

---

## STEP 0 — Branch + read the TF vars

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin && git switch main && git pull --ff-only origin main
git switch -c fix/pa06-iac-dispatch

# Confirm the exact variable names + any required vars in the module:
cat infra/cloud_scheduler/main.tf infra/cloud_scheduler/build_reaper.tf
grep -rn "variable " infra/cloud_scheduler/ || echo "(no explicit variable blocks — module may use locals/data; adjust apply.sh -var flags accordingly)"
```

If the module declares no `gcp_project`/`gcp_region` variables, drop the `-var` flags from
the apply.sh you write (don't pass vars the module doesn't accept — that errors). Match
reality.

---

## STEP 1 — Add infra/cloud_scheduler/apply.sh (mirror the scheduler convention)

Create `infra/cloud_scheduler/apply.sh`:

```bash
#!/usr/bin/env bash
# MARSYS-JIS — IaC apply wrapper for the cloud_scheduler module
# (Cloud Scheduler jobs + build-reaper SA + IAM). Idempotent.
# PA-06: invoked ONLY from the dispatch-only iac-apply workflow or by an operator.
# NEVER run from the per-deploy path. DO NOT run from a git worktree.

set -euo pipefail
CMD="${1:-plan}"
PROJECT="${TF_VAR_gcp_project:-madhav-astrology}"
REGION="${TF_VAR_gcp_region:-asia-south1}"
STATE_BUCKET="${TF_STATE_BUCKET:-${PROJECT}-tf-state}"
STATE_PREFIX="infra/cloud_scheduler"

command -v terraform >/dev/null 2>&1 || { echo "terraform CLI not on PATH" >&2; exit 1; }

terraform init \
  -backend-config="bucket=${STATE_BUCKET}" \
  -backend-config="prefix=${STATE_PREFIX}"

# NOTE: pass -var flags ONLY if the module declares these variables (see Step 0).
case "$CMD" in
  plan)    terraform plan    -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}" ;;
  apply)   terraform apply -auto-approve -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}" ;;
  destroy) terraform destroy -auto-approve -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}" ;;
  *) echo "usage: $0 {plan|apply|destroy}" >&2; exit 2 ;;
esac
```

```bash
chmod +x infra/cloud_scheduler/apply.sh
```

(If Step 0 showed no `gcp_project`/`gcp_region` variables, remove the `-var` flags from the
plan/apply/destroy lines.)

---

## STEP 2 — New dispatch-only workflow: .github/workflows/iac-apply.yml

Create `.github/workflows/iac-apply.yml`:

```yaml
name: IaC Apply (manual — dispatch only)

# PA-06: Terraform was removed from the per-deploy path (deploy.yml). IaC changes
# are now a deliberate, human-triggered act with a visible plan before apply.
# This workflow NEVER runs on push / pull_request / workflow_run.
on:
  workflow_dispatch:
    inputs:
      module:
        description: 'Which infra module to act on'
        required: true
        default: cloud_scheduler
        type: choice
        options:
          - cloud_scheduler
      action:
        description: 'plan (safe, default) or apply'
        required: true
        default: plan
        type: choice
        options:
          - plan
          - apply

permissions:
  contents: read
  id-token: write   # Workload Identity Federation

env:
  GCP_REGION: asia-south1
  WIF_PROVIDER: projects/938361928218/locations/global/workloadIdentityPools/github/providers/github-actions
  WIF_SERVICE_ACCOUNT: github-actions@madhav-astrology.iam.gserviceaccount.com

jobs:
  iac:
    name: Terraform ${{ github.event.inputs.action }} — ${{ github.event.inputs.module }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ env.WIF_PROVIDER }}
          service_account: ${{ env.WIF_SERVICE_ACCOUNT }}

      - name: Set up Terraform
        uses: hashicorp/setup-terraform@v3

      # Always plan first — the plan output is visible in the run log regardless of action.
      - name: Terraform plan (always)
        working-directory: infra/${{ github.event.inputs.module }}
        run: bash apply.sh plan

      # Apply ONLY when the operator explicitly chose 'apply'. The plan above has
      # already printed what will change.
      - name: Terraform apply (only if action == apply)
        if: ${{ github.event.inputs.action == 'apply' }}
        working-directory: infra/${{ github.event.inputs.module }}
        run: bash apply.sh apply
```

Design notes baked in (do not weaken):
- `workflow_dispatch` only — no automatic trigger.
- `action` defaults to `plan`; a click-through-without-thinking produces a plan, not an
  apply.
- The plan step runs unconditionally, so even an `apply` run shows the plan in the log
  immediately before the apply (plan-visible-before-apply).
- `module` is a `choice` seeded with `cloud_scheduler` so the workflow extends cleanly to
  `scheduler`/`iam`/etc. later by adding options + ensuring each has an `apply.sh`.

---

## STEP 3 — Remove the TF block from deploy.yml deploy-web

Delete `deploy.yml` lines 119-134 inclusive — the entire
`# ── A-S8: Terraform apply … ──` / `# ── /A-S8: terraform ──` block (the "Set up
Terraform", "Terraform init (cloud_scheduler)", and "Terraform apply (cloud_scheduler)"
steps). Leave the migration steps above it and the "Copy governance files" step below it
intact.

Verify nothing else in deploy.yml references terraform:

```bash
grep -n "terraform\|Terraform" .github/workflows/deploy.yml || echo "deploy.yml is terraform-free — correct"
```

---

## STEP 4 — Verify + commit

```bash
# YAML sanity on both files:
python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/iac-apply.yml')); yaml.safe_load(open('.github/workflows/deploy.yml')); print('both workflows parse OK')"

# apply.sh is executable + syntactically valid:
bash -n infra/cloud_scheduler/apply.sh && echo "apply.sh syntax OK"

git add .github/workflows/iac-apply.yml infra/cloud_scheduler/apply.sh .github/workflows/deploy.yml
git commit -m "fix(deploy): decouple Terraform from deploy hot-path → dispatch-only IaC workflow (PA-06)

Removed the continue-on-error terraform init/apply block from deploy-web (lines
119-134). App deploys no longer run IaC. Added .github/workflows/iac-apply.yml
(workflow_dispatch only, action defaults to 'plan', plan-visible-before-apply) and
infra/cloud_scheduler/apply.sh mirroring the infra/scheduler convention.

Rationale: app deploys ship many times/day; cloud_scheduler IaC rarely changes.
Coupling ran apply -auto-approve unattended on every deploy, masked under
continue-on-error (drift was silent). IaC is now a deliberate, plan-visible,
human-triggered act. The removed steps were already continue-on-error, so the deploy
path had no hard dependency on them — removal cannot break a passing deploy."
```

---

## STEP 5 — Push + PR

```bash
git push -u origin fix/pa06-iac-dispatch
# Open PR to main. ci.yml + deploy.yml build-check run on the PR (deploy.yml still has its
# PR build-check job; only the TF steps inside deploy-web were removed).
```

---

## Post-merge operator actions (one-time)

1. **First IaC sync after decouple:** the per-deploy apply is gone, so run the dispatch
   workflow once to reconcile any drift that accumulated while apply was silently skipped:
   GitHub → Actions → "IaC Apply (manual — dispatch only)" → Run workflow →
   module `cloud_scheduler`, action `plan`. **Read the plan.** If it shows resources to
   create/change (e.g. the build-reaper SA or scheduler job that may have been missing),
   re-run with action `apply`.
2. **SA permission check:** the dispatch workflow uses the same
   `github-actions@…` SA. If the plan step errors on
   `storage.objects.list` against `madhav-astrology-tf-state`, grant the SA read on the
   state bucket (this was the latent cause of the old silent-skip) — narrowest grant:
   `roles/storage.objectViewer` on the bucket, plus `objectCreator`/`objectAdmin` if apply
   must write state. Then re-run.
3. Update `00_ARCHITECTURE/PIPELINE_AUDIT_v1_0.md` PA-06 status → RESOLVED (option b), and
   note the first-sync plan result.

## Out of scope
Other infra modules (`scheduler`, `iam`, `cloud_tasks`, `edge`, `memorystore`) keep their
existing apply.sh / manual flow. The `module` choice input is pre-wired to add them later,
but wiring each requires confirming that module has an apply.sh and the SA has access —
defer to when an actual change to those modules is needed.
