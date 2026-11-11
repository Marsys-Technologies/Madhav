// MARSYS-JIS Platform Modernization — Wave 4 unit 4.edge_and_infra_hygiene
// Amended 2026-06-03 (Brahma Infra Verification remediation):
//   - web_gcs: project-wide objectViewer → per-bucket objectAdmin (chat-attachments + chart-documents)
//   - web_bq_job_user: added bigquery.jobUser (was live, not codified)
//   - web_triggers_bootstrap_job: added run.jobsExecutorWithOverrides on brahma-foundation-bootstrap job;
//       apply the same resource pattern for any future chart-build job created during the Brahma build arc.
//
// Per-service least-privilege runtime service accounts:
//   amjis-web-runtime      — Cloud Run service amjis-web
//   amjis-sidecar-runtime  — Cloud Run service amjis-sidecar
//   amjis-mcp-runtime      — Cloud Run service amjis-mcp
//   amjis-builder-runtime  — Dormant legacy build identity (no deploy or WIF authority)

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

variable "gcp_project" {
  type    = string
  default = "madhav-astrology"
}

variable "gcp_region" {
  type    = string
  default = "asia-south1"
}

variable "github_deploy_wif_subject" {
  type        = string
  description = "Exact immutable protected-main GitHub OIDC subject allowed to impersonate the live deploy identity. Repository-wide principalSets are forbidden."
  default     = "principal://iam.googleapis.com/projects/938361928218/locations/global/workloadIdentityPools/github/subject/repo:Marsys-Technologies@311530097/Madhav@1213634114:ref:refs/heads/main"
}

variable "github_data_plane_cutover_wif_subject" {
  type        = string
  description = "Exact immutable protected GitHub environment OIDC subject allowed to impersonate the live deploy identity for the one-time data-plane cutover."
  default     = "principal://iam.googleapis.com/projects/938361928218/locations/global/workloadIdentityPools/github/subject/repo:Marsys-Technologies@311530097/Madhav@1213634114:environment:data-plane-production-cutover"
}

variable "retain_project_wide_logging_viewer" {
  type        = bool
  default     = true
  description = "Keep the legacy project-wide roles/logging.viewer on github-actions@. Set false only after the cloudsql_restore_audit view, its binding and the logging_config_reader role are applied and read back."
}

// Runtime Secret Manager access is deliberately secret-specific. Keep these
// sets aligned with deploy.yml and every Cloud Run job that reuses a runtime
// service account; a service-level inventory alone misses those job mounts.
locals {
  web_runtime_secret_ids = toset([
    "firebase-admin-credentials",
    "amjis-db-password",
    "nirmana-campaign-control-db-password",
    "nirmana-evidence-ingress-db-password",
    "openai-api-key",
    "GOOGLE_GENERATIVE_AI_API_KEY",
    "DEEPSEEK_API_KEY",
    "NVIDIA_NIM_API_KEY",
    "PYTHON_SIDECAR_API_KEY",
    "SUPER_ADMIN_EMAIL",
    "mcpt-scheduler-secret",
    "mcp-internal-token",
    "mcp-canary-key",
    // brahma-build-pipeline-job also runs as amjis-web-runtime.
    "amjis-pipeline-db-url",
  ])
  sidecar_runtime_secret_ids = toset([
    "PYTHON_SIDECAR_API_KEY",
    "GOOGLE_GENERATIVE_AI_API_KEY",
    "amjis-pipeline-db-url",
  ])
  mcp_runtime_secret_ids = toset([
    "mcp-internal-token",
    "PYTHON_SIDECAR_API_KEY",
  ])
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

// ── Service accounts ─────────────────────────────────────────────────────────

resource "google_service_account" "amjis_web_runtime" {
  account_id   = "amjis-web-runtime"
  display_name = "amjis-web Cloud Run runtime"
  description  = "Least-priv runtime identity for amjis-web. Calls MCP + sidecar + Cloud SQL + Vertex + GCS."
}

resource "google_service_account" "amjis_sidecar_runtime" {
  account_id   = "amjis-sidecar-runtime"
  display_name = "amjis-sidecar Cloud Run runtime"
  description  = "Least-priv runtime identity for amjis-sidecar (python). Cloud SQL + Secret Manager only."
}

resource "google_service_account" "amjis_mcp_runtime" {
  account_id   = "amjis-mcp-runtime"
  display_name = "amjis-mcp Cloud Run runtime"
  description  = "Least-priv runtime identity for amjis-mcp. Cloud SQL + Secret Manager + Cloud Run invoker (web) + GCS."
}

resource "google_service_account" "amjis_builder_runtime" {
  account_id   = "amjis-builder-runtime"
  display_name = "amjis legacy build identity"
  description  = "Retained without WIF, Cloud Run mutation, or runtime actAs authority."
}

// Deployment may attach only these exact runtime identities. The former
// project-wide serviceAccountUser grant allowed github-actions@ to act as the
// data-plane builder and every other service account in the project.
resource "google_service_account_iam_member" "github_actions_acts_as_web_runtime" {
  service_account_id = google_service_account.amjis_web_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:github-actions@${var.gcp_project}.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "github_actions_acts_as_sidecar_runtime" {
  service_account_id = google_service_account.amjis_sidecar_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:github-actions@${var.gcp_project}.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "github_actions_acts_as_mcp_runtime" {
  service_account_id = google_service_account.amjis_mcp_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:github-actions@${var.gcp_project}.iam.gserviceaccount.com"
}

// The protected deployment preflight reads IAM and runtime metadata to prove
// the data-plane isolation boundary. Security Reviewer grants policy metadata
// only: it cannot access secret payloads, impersonate identities, or mutate
// IAM/runtime state.
resource "google_project_iam_member" "github_actions_security_reviewer" {
  project = var.gcp_project
  role    = "roles/iam.securityReviewer"
  member  = "serviceAccount:github-actions@${var.gcp_project}.iam.gserviceaccount.com"
}

// ── Narrow audit-log read for the protected cutover verifier (LOGVIEW-NARROW-IAC) ──
//
// The protected cutover verifier (platform/scripts/data-plane-cutover-preflight.ts,
// run by deploy.yml job privileged-bootstrap) reads the immutable Admin Activity entry
// for the named Cloud SQL restore operation, because operations.describe omits the
// source backup identifier. It used to do that through a project-wide
// roles/logging.viewer. It now reads through ONE log view on the `_Required` bucket
// (where Admin Activity audit logs are stored), so the grant can be a single-view
// roles/logging.viewAccessor and the project-wide role can go (SR-LOGVIEW-NARROW-KEEP).
//
// The view admits only Cloud SQL Admin Activity entries. The bucket, location and view
// name below must equal CLOUDSQL_RESTORE_AUDIT_LOG_VIEW in the preflight script
// (pinned by platform/scripts/governance/__tests__/test_logview_narrow_iac.py).
//
// The gochara_verification_job view that gochara-seal-approved.yml reads is owner-created
// with gcloud (runbook Act 12) and is deliberately NOT declared here: Terraform would
// try to create an object that already exists.
resource "google_logging_log_view" "cloudsql_restore_audit" {
  name        = "cloudsql_restore_audit"
  bucket      = "projects/${var.gcp_project}/locations/global/buckets/_Required"
  description = "Cloud SQL Admin Activity audit entries only: lets the protected data-plane cutover verifier bind a restore operation to its backup. No other log is visible through this view."
  filter      = "SOURCE(\"projects/${var.gcp_project}\") AND resource.type = \"cloudsql_database\" AND LOG_ID(\"cloudaudit.googleapis.com/activity\")"
}

// Project-level viewAccessor limited by an IAM condition to that one view (Google's
// documented way to bind a single view). Without the condition this role would expose
// every view in the project, which is what this change exists to avoid.
resource "google_project_iam_member" "github_actions_cloudsql_restore_audit_view" {
  project = var.gcp_project
  role    = "roles/logging.viewAccessor"
  member  = "serviceAccount:github-actions@${var.gcp_project}.iam.gserviceaccount.com"

  condition {
    title       = "cloudsql_restore_audit_view_only"
    description = "Only the cloudsql_restore_audit log view; never another view."
    expression  = "resource.name == \"projects/${var.gcp_project}/locations/global/buckets/_Required/views/cloudsql_restore_audit\""
  }
}

// roles/logging.viewer also carries the Logging CONFIGURATION reads that the
// plan-only workflow iac-apply.yml needs (it plans the `logging` and `iam` modules as
// github-actions@). viewAccessor does not. This custom role keeps exactly those reads
// and no log-entry read (no logging.logEntries.list, no logging.logs.list), so removing
// the project-wide viewer does not break `terraform plan`.
resource "google_project_iam_custom_role" "logging_config_reader" {
  role_id     = "loggingConfigReader"
  title       = "Logging configuration reader"
  description = "Read Logging exclusions, buckets and views (configuration only; no log entries). For terraform plan as github-actions@."
  permissions = [
    "logging.buckets.get",
    "logging.buckets.list",
    "logging.exclusions.get",
    "logging.exclusions.list",
    "logging.views.get",
    "logging.views.list",
  ]
}

resource "google_project_iam_member" "github_actions_logging_config_reader" {
  project = var.gcp_project
  role    = google_project_iam_custom_role.logging_config_reader.id
  member  = "serviceAccount:github-actions@${var.gcp_project}.iam.gserviceaccount.com"
}

// The legacy project-wide grant. It stays (default true) so merging this file changes
// nothing until the owner has applied the additions above AND checked that the cutover
// preflight reads through the view. Setting this to false removes the grant:
//   terraform apply -var retain_project_wide_logging_viewer=false
// Apply needs owner approval; see infra/iam/README.md "Removing the project-wide
// Logging Viewer".
resource "google_project_iam_member" "github_actions_logging_viewer" {
  count   = var.retain_project_wide_logging_viewer ? 1 : 0
  project = var.gcp_project
  role    = "roles/logging.viewer"
  member  = "serviceAccount:github-actions@${var.gcp_project}.iam.gserviceaccount.com"
}

// Adding `count` renames the address; without this the first plan would destroy and
// recreate the live grant.
moved {
  from = google_project_iam_member.github_actions_logging_viewer
  to   = google_project_iam_member.github_actions_logging_viewer[0]
}

// Firebase custom-token signing is self-only. A project-wide Token Creator
// grant would also allow this SDK identity to impersonate the data-plane builder.
resource "google_service_account_iam_member" "firebase_admin_self_token_creator" {
  service_account_id = "projects/${var.gcp_project}/serviceAccounts/firebase-adminsdk-fbsvc@${var.gcp_project}.iam.gserviceaccount.com"
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:firebase-adminsdk-fbsvc@${var.gcp_project}.iam.gserviceaccount.com"
}

// ── amjis-web-runtime grants ─────────────────────────────────────────────────

resource "google_project_iam_member" "web_sql_client" {
  project = var.gcp_project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "web_secret_access" {
  for_each  = local.web_runtime_secret_ids
  project   = var.gcp_project
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

resource "google_project_iam_member" "web_vertex" {
  project = var.gcp_project
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

// GCS: scoped objectAdmin on the two buckets web actually writes to
// (chat attachment uploads, chart document exports). Project-wide objectViewer
// removed — bucket-level objectAdmin supersedes it and is least-priv.
resource "google_storage_bucket_iam_member" "web_chat_attachments_admin" {
  bucket = "madhav-astrology-chat-attachments"
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

resource "google_storage_bucket_iam_member" "web_chart_docs_admin" {
  bucket = "madhav-astrology-chart-documents"
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

resource "google_project_iam_member" "web_bq_job_user" {
  project = var.gcp_project
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

// Brahma build arc: web-runtime triggers brahma-foundation-bootstrap (and any
// future chart-build job) via direct jobs.run. Duplicate this resource block
// for each new Cloud Run job added during the Brahma build arc.
resource "google_cloud_run_v2_job_iam_member" "web_triggers_bootstrap_job" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "brahma-foundation-bootstrap"
  role     = "roles/run.jobsExecutorWithOverrides"
  member   = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

// Per-chart build pipeline job — invoked by /api/build/start via invokeBuildJob().
// Same pattern as web_triggers_bootstrap_job per the header note.
resource "google_cloud_run_v2_job_iam_member" "web_triggers_build_pipeline_job" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "brahma-build-pipeline-job"
  role     = "roles/run.jobsExecutorWithOverrides"
  member   = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

// Cloud Run invoker on amjis-mcp (per-service binding, not project-wide).
resource "google_cloud_run_v2_service_iam_member" "web_invokes_mcp" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "amjis-mcp"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

resource "google_cloud_run_v2_service_iam_member" "web_invokes_sidecar" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "amjis-sidecar"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

// Nirmana Elevation tracker: allow the web runtime to observe the one Cloud
// Run service it reports on. This supplies run.services.get and
// run.revisions.get without granting project-wide visibility or mutation.
resource "google_cloud_run_v2_service_iam_member" "web_observes_own_release" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "amjis-web"
  role     = "roles/run.viewer"
  member   = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

// ── amjis-sidecar-runtime grants ─────────────────────────────────────────────

resource "google_project_iam_member" "sidecar_sql_client" {
  project = var.gcp_project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.amjis_sidecar_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "sidecar_secret_access" {
  for_each  = local.sidecar_runtime_secret_ids
  project   = var.gcp_project
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.amjis_sidecar_runtime.email}"
}

// ── amjis-mcp-runtime grants ─────────────────────────────────────────────────

resource "google_project_iam_member" "mcp_sql_client" {
  project = var.gcp_project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.amjis_mcp_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "mcp_secret_access" {
  for_each  = local.mcp_runtime_secret_ids
  project   = var.gcp_project
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.amjis_mcp_runtime.email}"
}

resource "google_project_iam_member" "mcp_gcs" {
  project = var.gcp_project
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.amjis_mcp_runtime.email}"
}

// MCP calls back into platform routes (e.g. /api/mcp/primitives/*).
resource "google_cloud_run_v2_service_iam_member" "mcp_invokes_web" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "amjis-web"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.amjis_mcp_runtime.email}"
}

// ── amjis-builder-runtime grants (deploy identity) ───────────────────────────

resource "google_project_iam_member" "builder_ar_writer" {
  project = var.gcp_project
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.amjis_builder_runtime.email}"
}

// The live workflow currently deploys as github-actions@, not the legacy
// builder identity. Bind that administrative trust boundary to the exact
// protected-main OIDC subject. During the governed live cutover, remove both
// old repository-wide github-actions@ bindings and the legacy builder's WIF,
// Run Admin and runtime actAs grants before creating any new secret.
resource "google_service_account_iam_member" "protected_main_impersonates_github_actions" {
  service_account_id = "projects/${var.gcp_project}/serviceAccounts/github-actions@${var.gcp_project}.iam.gserviceaccount.com"
  role               = "roles/iam.workloadIdentityUser"
  member             = var.github_deploy_wif_subject
}

// GitHub replaces the ref-based OIDC subject with an environment-based subject
// when a job enters a protected environment. Keep that bootstrap-only route as
// a second exact subject instead of widening the protected-main binding to the
// whole repository.
resource "google_service_account_iam_member" "data_plane_cutover_environment_impersonates_github_actions" {
  service_account_id = "projects/${var.gcp_project}/serviceAccounts/github-actions@${var.gcp_project}.iam.gserviceaccount.com"
  role               = "roles/iam.workloadIdentityUser"
  member             = var.github_data_plane_cutover_wif_subject
}

// ── Pub/Sub: cockpit-events (SSE real-time build events) ─────────────────────
//
// amjis-web (subscriber) creates an ephemeral subscription per SSE request, filtered
// by chart_id. brahma-build-pipeline-job (publisher) emits asset.state_change /
// asset.progress / asset.substep / run.state_change events during a build run.
//
// Publisher SA verification: the pipeline job was originally created out-of-band
// without an explicit --service-account. Before applying, confirm with:
//   gcloud run jobs describe brahma-build-pipeline-job \
//     --region=asia-south1 --format='value(template.serviceAccount)'
// If the result is NOT amjis-sidecar-runtime@madhav-astrology.iam.gserviceaccount.com,
// duplicate the sidecar_cockpit_events_publisher block below with the actual SA.

resource "google_pubsub_topic" "cockpit_events" {
  name = "cockpit-events"
  // 10-minute retention matches the ephemeral subscription TTL in the SSE route.
  message_retention_duration = "600s"
}

// amjis-web-runtime creates + deletes ephemeral per-request subscriptions on this
// topic; roles/pubsub.editor at topic scope grants the minimum required permissions:
// attachSubscription, createSubscription, deleteSubscription, consume.
resource "google_pubsub_topic_iam_member" "web_cockpit_events_editor" {
  topic  = google_pubsub_topic.cockpit_events.name
  role   = "roles/pubsub.editor"
  member = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

// brahma-build-pipeline-job publishes build events. The job container descends from
// the python-sidecar codebase; amjis-sidecar-runtime is the expected runtime SA.
// Verify with gcloud (see comment above) and add an extra binding if different.
resource "google_pubsub_topic_iam_member" "sidecar_cockpit_events_publisher" {
  topic  = google_pubsub_topic.cockpit_events.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.amjis_sidecar_runtime.email}"
}

// brahma-build-pipeline-job confirmed SA: amjis-web-runtime (not amjis-sidecar-runtime).
// Verified 2026-06-26 via: gcloud run jobs describe brahma-build-pipeline-job --format='value(template.serviceAccount)'
// Binding alongside sidecar binding so both SAs can publish if the job SA ever changes.
resource "google_pubsub_topic_iam_member" "web_runtime_cockpit_events_publisher" {
  topic  = google_pubsub_topic.cockpit_events.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

// ── Outputs ──────────────────────────────────────────────────────────────────

output "web_runtime_sa" {
  value = google_service_account.amjis_web_runtime.email
}

output "sidecar_runtime_sa" {
  value = google_service_account.amjis_sidecar_runtime.email
}

output "mcp_runtime_sa" {
  value = google_service_account.amjis_mcp_runtime.email
}

output "builder_runtime_sa" {
  value = google_service_account.amjis_builder_runtime.email
}
