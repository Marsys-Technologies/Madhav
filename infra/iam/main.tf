// MARSYS-JIS Platform Modernization — Wave 4 unit 4.edge_and_infra_hygiene
//
// Per-service least-privilege runtime service accounts:
//   amjis-web-runtime      — Cloud Run service amjis-web
//   amjis-sidecar-runtime  — Cloud Run service amjis-sidecar
//   amjis-mcp-runtime      — Cloud Run service amjis-mcp
//   amjis-builder-runtime  — Build/deploy identity (used by GH Actions WIF)

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

variable "github_wif_principal" {
  type        = string
  description = "Workload identity principal for the github-actions WIF provider (used to grant impersonation on the builder SA)."
  default     = "principalSet://iam.googleapis.com/projects/938361928218/locations/global/workloadIdentityPools/github/attribute.repository/Abhisek-Mohanty/MadhavStreamC"
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
  display_name = "amjis build/deploy identity"
  description  = "Used by GH Actions WIF to push images + deploy revisions. Replaces broad github-actions@ SA."
}

// ── amjis-web-runtime grants ─────────────────────────────────────────────────

resource "google_project_iam_member" "web_sql_client" {
  project = var.gcp_project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

resource "google_project_iam_member" "web_secrets" {
  project = var.gcp_project
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

resource "google_project_iam_member" "web_vertex" {
  project = var.gcp_project
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
}

resource "google_project_iam_member" "web_gcs" {
  project = var.gcp_project
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.amjis_web_runtime.email}"
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

// ── amjis-sidecar-runtime grants ─────────────────────────────────────────────

resource "google_project_iam_member" "sidecar_sql_client" {
  project = var.gcp_project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.amjis_sidecar_runtime.email}"
}

resource "google_project_iam_member" "sidecar_secrets" {
  project = var.gcp_project
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.amjis_sidecar_runtime.email}"
}

// ── amjis-mcp-runtime grants ─────────────────────────────────────────────────

resource "google_project_iam_member" "mcp_sql_client" {
  project = var.gcp_project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.amjis_mcp_runtime.email}"
}

resource "google_project_iam_member" "mcp_secrets" {
  project = var.gcp_project
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.amjis_mcp_runtime.email}"
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

resource "google_project_iam_member" "builder_run_admin" {
  project = var.gcp_project
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.amjis_builder_runtime.email}"
}

resource "google_project_iam_member" "builder_ar_writer" {
  project = var.gcp_project
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.amjis_builder_runtime.email}"
}

// Builder must be able to actAs each runtime SA to deploy revisions under it.
resource "google_service_account_iam_member" "builder_actas_web" {
  service_account_id = google_service_account.amjis_web_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.amjis_builder_runtime.email}"
}

resource "google_service_account_iam_member" "builder_actas_sidecar" {
  service_account_id = google_service_account.amjis_sidecar_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.amjis_builder_runtime.email}"
}

resource "google_service_account_iam_member" "builder_actas_mcp" {
  service_account_id = google_service_account.amjis_mcp_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.amjis_builder_runtime.email}"
}

// WIF principal → impersonate builder SA.
resource "google_service_account_iam_member" "wif_impersonates_builder" {
  service_account_id = google_service_account.amjis_builder_runtime.name
  role               = "roles/iam.workloadIdentityUser"
  member             = var.github_wif_principal
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
