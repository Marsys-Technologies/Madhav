# infra/iam — Per-service runtime service accounts

MARSYS-JIS Platform Modernization Wave 4 unit `4.edge_and_infra_hygiene`.

## What this codifies

Four least-privilege runtime SAs, one per Cloud Run service / build pipeline:

| Service account                          | Role on                                                                   | Justification                                  |
|------------------------------------------|---------------------------------------------------------------------------|------------------------------------------------|
| `amjis-web-runtime`                      | Cloud SQL client, Secret Manager accessor, Cloud Run invoker on `amjis-mcp` + `amjis-sidecar`, Cloud Run viewer on `amjis-web`, Vertex AI user, GCS object viewer on chart-documents | The web frontend; calls MCP + sidecar + DB and observes its own immutable release provenance. |
| `amjis-sidecar-runtime`                  | Cloud SQL client, Secret Manager accessor                                 | Python sidecar; no MCP or Vertex calls.        |
| `amjis-mcp-runtime`                      | Cloud SQL client, Secret Manager accessor, Cloud Run invoker on `amjis-web`, GCS object viewer | MCP server; calls platform routes + reads corpus. |
| `amjis-builder-runtime`                  | Artifact Registry writer only                                             | Retained dormant identity; no WIF, Cloud Run mutation, or runtime actAs authority. |

The live deploy identity is `github-actions@madhav-astrology.iam.gserviceaccount.com`; this root
binds it only to two exact immutable repository-ID OIDC subjects: protected `main` for routine
deploy jobs, and the protected `data-plane-production-cutover` environment for its one-time
bootstrap job. The repository enables GitHub's immutable-subject mode, and GitHub uses an
environment subject in place of the ref subject when a job enters an environment, so both narrow
bindings require the numeric organization and repository IDs. The cutover verifier binds a Cloud SQL restore
operation to its exact backup through Admin Activity audit evidence (Cloud SQL's operation response
omits that source-backup field). It reads that evidence through the single log view
`cloudsql_restore_audit` on the `_Required` bucket; see "Removing the project-wide Logging Viewer". The three runtime SAs are attached to the
corresponding Cloud Run revisions via `--service-account=`. The legacy builder is deliberately
unable to deploy or act as a runtime. This replaces the prior pattern where every service ran under
the project default compute SA (`<project_number>-compute@developer.gserviceaccount.com`).

## Files

- `main.tf` — SA resources + IAM role grants + exact protected-main and protected-environment WIF bindings for the live deploy SA.
- `backend.tf` — GCS-backed terraform remote state.
- `apply.sh` — idempotent plan/apply wrapper.

## Wired into deploy.yml

The Cloud Run `deploy-cloudrun@v2` step pins each service's `service_account` to its runtime SA;
see the `# ── 4.edge_and_infra_hygiene ──` fence block in `.github/workflows/deploy.yml`.

## MCP ingress application gate

The public MCP front door deliberately uses Cloud Run `--allow-unauthenticated` so external MCP
clients can reach the application OAuth/Bearer-token layer. Cloud Run IAM is therefore not the
MCP ingress security boundary. Internal Pūrṇa calls additionally require the shared internal token
and a Google OIDC token pinned to the expected caller service account and audience; candidate
deployment probes exercise that combined path before traffic promotion. The web runtime's
`run.invoker` binding remains useful for authenticated service-to-service calls but is not claimed
as the public MCP gate.

## Removing the project-wide Logging Viewer (LOGVIEW-NARROW-IAC)

Status: **written, not applied. Applying needs the owner's approval; nothing here was run against Google Cloud.**

`github-actions@` still holds the legacy project-wide `roles/logging.viewer` (SR-LOGVIEW-NARROW-KEEP),
because the protected cutover (`deploy.yml` job `privileged-bootstrap` ->
`platform/scripts/data-plane-cutover-preflight.ts`) read Admin Activity audit logs project-wide.
This module now declares the narrow replacement:

| Resource | What it is |
|---|---|
| `google_logging_log_view.cloudsql_restore_audit` | view on `_Required`, filter: Cloud SQL Admin Activity entries only |
| `google_project_iam_member.github_actions_cloudsql_restore_audit_view` | `roles/logging.viewAccessor` for `github-actions@`, IAM-conditioned to that one view |
| `google_project_iam_custom_role.logging_config_reader` + member | Logging configuration reads (no log entries) so `iac-apply.yml` `terraform plan` of the `logging`/`iam` modules still works |
| `var.retain_project_wide_logging_viewer` (default `true`) | the legacy grant; `false` removes it |

The preflight script now calls `gcloud logging read ... --bucket=_Required --location=global --view=cloudsql_restore_audit`.
`test_logview_narrow_iac.py` pins the script, this file and the workflows to the same view and fails if any
GCP-authenticated workflow or script reads logs without a view.

### Owner apply order (every step is an owner act)

1. Read-only first: confirm a view can be created on `_Required` (not verifiable offline; if Google refuses, stop and keep the legacy role):
   `gcloud logging buckets describe _Required --location=global --project=madhav-astrology`
2. Merge this PR (no behaviour change: the default keeps the legacy role; the preflight now needs the view, so do not dispatch a cutover before step 3).
3. `bash apply.sh plan`, review that it shows only the four additions plus a `moved` of the legacy grant (no destroy), then `bash apply.sh apply`.
4. Read back: `gcloud logging views describe cloudsql_restore_audit --bucket=_Required --location=global --project=madhav-astrology`, and a read through the view returns Cloud SQL audit entries and nothing else.
5. Run the cutover preflight once (or any restore-audit read) as `github-actions@` through the view and confirm it succeeds.
6. Only then: `terraform apply -var retain_project_wide_logging_viewer=false`, and read back that `roles/logging.viewer` is absent from `github-actions@` while the view binding and `loggingConfigReader` remain.
7. Run `iac-apply.yml` for modules `iam` and `logging` (plan only) to confirm they still plan as `github-actions@`.

Not covered here: the `gochara_verification_job` view and its binding (runbook Act 12, owner-created with gcloud).
Open check: the exact permission set in `loggingConfigReader` is the smallest set the two module plans are
expected to need; step 7 is the test of that, and any missing permission is added to the role, never fixed by restoring the project-wide viewer.
