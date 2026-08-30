// Dedicated, non-browser Nirmana conductor identities and callbacks.
//
// This module intentionally does not grant Cloud SQL, Secret Manager, Editor,
// service-account-token-creator, or deployment privileges to either identity.
// The identities can invoke one fixed HTTPS route; the route verifies the OIDC
// subject again and applies the server-side campaign policy/fence.

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

  validation {
    condition     = var.gcp_project == "madhav-astrology"
    error_message = "The conductor is pinned to the madhav-astrology production project."
  }
}

variable "gcp_region" {
  type    = string
  default = "asia-south1"

  validation {
    condition     = var.gcp_region == "asia-south1"
    error_message = "The conductor is pinned to the asia-south1 production region."
  }
}

locals {
  conductor_oidc_audience = "https://amjis-web-938361928218.asia-south1.run.app"
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

data "google_project" "nirmana_elevation_conductor" {
  project_id = var.gcp_project
}

resource "google_service_account" "conductor" {
  account_id   = "amjis-nirmana-conductor"
  display_name = "Nirmana L0 conductor Scheduler invoker"
  description  = "Can invoke only the fixed non-browser Nirmana conductor endpoint. No data-plane or deploy roles."
  project      = var.gcp_project

  lifecycle { prevent_destroy = true }
}

resource "google_service_account" "verifier" {
  account_id   = "amjis-nirmana-verifier"
  display_name = "Nirmana L0 independent verifier Scheduler invoker"
  description  = "Can invoke only the fixed Nirmana readiness-verifier endpoint command. No data-plane or deploy roles."
  project      = var.gcp_project

  lifecycle { prevent_destroy = true }
}

resource "google_cloud_run_v2_service_iam_member" "conductor_invokes_web" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "amjis-web"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.conductor.email}"
}

resource "google_cloud_run_v2_service_iam_member" "verifier_invokes_web" {
  project  = var.gcp_project
  location = var.gcp_region
  name     = "amjis-web"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.verifier.email}"
}

resource "google_service_account_iam_member" "scheduler_mints_conductor_oidc" {
  service_account_id = google_service_account.conductor.name
  role               = "roles/iam.serviceAccountOpenIdTokenCreator"
  member             = "serviceAccount:service-${data.google_project.nirmana_elevation_conductor.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "scheduler_mints_verifier_oidc" {
  service_account_id = google_service_account.verifier.name
  role               = "roles/iam.serviceAccountOpenIdTokenCreator"
  member             = "serviceAccount:service-${data.google_project.nirmana_elevation_conductor.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
}

resource "google_cloud_scheduler_job" "conductor" {
  name             = "amjis-nirmana-elevation-conductor"
  description      = "Evaluate only the allowlisted T0/F0/L0 Nirmana conductor frontier every ten minutes."
  schedule         = "*/10 * * * *"
  time_zone        = "Etc/UTC"
  region           = var.gcp_region
  attempt_deadline = "120s"
  paused           = true

  lifecycle { prevent_destroy = true }

  retry_config {
    retry_count          = 1
    min_backoff_duration = "60s"
    max_backoff_duration = "120s"
    max_doublings        = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${local.conductor_oidc_audience}/api/admin/internal/nirmana-elevation-conductor"
    body        = base64encode("{\"command\":\"evaluate\"}")

    oidc_token {
      service_account_email = google_service_account.conductor.email
      audience              = local.conductor_oidc_audience
    }
  }
}

resource "google_cloud_scheduler_job" "verifier" {
  name             = "amjis-nirmana-elevation-readiness-verifier"
  description      = "Independently verify the Nirmana conductor readiness boundary every thirty minutes."
  schedule         = "7,37 * * * *"
  time_zone        = "Etc/UTC"
  region           = var.gcp_region
  attempt_deadline = "120s"
  paused           = true

  lifecycle { prevent_destroy = true }

  retry_config {
    retry_count          = 1
    min_backoff_duration = "60s"
    max_backoff_duration = "120s"
    max_doublings        = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${local.conductor_oidc_audience}/api/admin/internal/nirmana-elevation-conductor"
    body        = base64encode("{\"command\":\"verify_readiness\"}")

    oidc_token {
      service_account_email = google_service_account.verifier.email
      audience              = local.conductor_oidc_audience
    }
  }
}
