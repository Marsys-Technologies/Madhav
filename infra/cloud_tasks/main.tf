// MARSYS-JIS Platform Modernization — Wave 4 unit 4.build_trigger
// Provisions the `amjis-build-queue` Cloud Tasks queue used by
// /api/build/start to enqueue invocations of the
// `marsys-build-pipeline-job` Cloud Run Job.
//
// IaC only — DO NOT run `terraform apply` from this Conductor worktree.
// State must be shared with main; apply runs via the zero-touch deploy
// pipeline (or manually by the operator once IaC is on main).

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
  type        = string
  description = "GCP project ID"
  default     = "madhav-astrology"
}

variable "gcp_region" {
  type        = string
  description = "Region — must match Cloud Run services + the build Job"
  default     = "asia-south1"
}

variable "queue_id" {
  type        = string
  description = "Cloud Tasks queue identifier"
  default     = "amjis-build-queue"
}

variable "max_dispatches_per_second" {
  type        = number
  description = "Throttle — builds are heavy; one in flight is plenty."
  default     = 1
}

variable "max_concurrent_dispatches" {
  type        = number
  description = "At most one build runs at a time per chart_id (the Job itself is single-instance)."
  default     = 1
}

variable "max_attempts" {
  type        = number
  description = "Retry policy — one retry then dead-letter."
  default     = 2
}

variable "task_handler_audience" {
  type        = string
  description = <<EOT
The OIDC audience the task handler validates. This is the URL of the
amjis-web Cloud Run service — Cloud Tasks signs the OIDC token with this
audience and the handler verifies it via the same value at runtime.
EOT
  default     = "https://amjis-web-938361928218.asia-south1.run.app"
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

resource "google_cloud_tasks_queue" "amjis_build_queue" {
  name     = var.queue_id
  location = var.gcp_region

  rate_limits {
    max_dispatches_per_second = var.max_dispatches_per_second
    max_concurrent_dispatches = var.max_concurrent_dispatches
  }

  retry_config {
    max_attempts       = var.max_attempts
    max_retry_duration = "600s"
    min_backoff        = "5s"
    max_backoff        = "60s"
    max_doublings      = 2
  }

  stackdriver_logging_config {
    sampling_ratio = 1.0
  }
}

// Service account that the task handler runs as (impersonated by Cloud Tasks
// via OIDC). Reused if it already exists in the project — we only declare it
// here so the IaC documents the required principal. Creation can also be done
// out-of-band; this resource is annotated to be import-safe.
resource "google_service_account" "build_task_invoker" {
  account_id   = "amjis-build-invoker"
  display_name = "MARSYS-JIS Cloud Tasks → /api/build/task invoker"
  description  = "OIDC identity for amjis-build-queue tasks. Granted run.invoker on amjis-web + amjis-builder."
}

// Allow the invoker SA to invoke the web service (the task handler endpoint).
resource "google_cloud_run_v2_service_iam_member" "invoker_on_web" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "amjis-web"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.build_task_invoker.email}"
}

// Allow the invoker SA to execute the Cloud Run Job (run_jobs_run on
// marsys-build-pipeline-job). The handler invokes the Job via
// google.cloud.run_v2.JobsClient.RunJob.
resource "google_project_iam_member" "invoker_jobs_run" {
  project = var.gcp_project
  role    = "roles/run.jobsExecutorWithOverrides"
  member  = "serviceAccount:${google_service_account.build_task_invoker.email}"
}

output "queue_name" {
  value       = google_cloud_tasks_queue.amjis_build_queue.name
  description = "Fully-qualified queue name — set as BUILD_TASK_QUEUE env var on amjis-web."
}

output "queue_location" {
  value       = google_cloud_tasks_queue.amjis_build_queue.location
  description = "Region of the queue — set as BUILD_TASK_QUEUE_LOCATION env var on amjis-web."
}

output "task_invoker_sa_email" {
  value       = google_service_account.build_task_invoker.email
  description = "Service-account email Cloud Tasks impersonates via OIDC. Set as BUILD_TASK_INVOKER_SA on amjis-web."
}

output "task_handler_audience" {
  value       = var.task_handler_audience
  description = "OIDC audience the handler validates. Set as BUILD_TASK_AUDIENCE on amjis-web."
}
