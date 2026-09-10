// Nirmana elevation executor + verifier — isolated Terraform root.
//
// This root deliberately owns only these six resources. It must not share
// state with infra/nirmana_elevation_monitor (a different, already-live
// identity) or infra/scheduler, whose state manages unrelated Scheduler jobs.
//
// Unlike the monitor, there is no Cloud Scheduler job here: the executor and
// verifier are invoked on demand (per campaign action), not on a fixed
// cadence, so the calling identity mints its own short-lived ID token via
// service-account impersonation rather than a standing Scheduler trigger.
//
// No roles/run.invoker grant: `amjis-web`'s Cloud Run IAM policy already
// grants roles/run.invoker to allUsers (verified live, 2026-09-01) -- the
// service is publicly reachable and every route in
// platform/src/app/api/admin/internal/ does its own authorization at the
// application layer via verifyOidcToken(). Adding an invoker grant here would
// be redundant, not load-bearing, and the monitor root's own invoker grant
// (predates this observation) is redundant for the same reason.

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
    error_message = "The executor/verifier routes accept only the dedicated principals in madhav-astrology."
  }
}

variable "gcp_region" {
  type    = string
  default = "asia-south1"

  validation {
    condition     = var.gcp_region == "asia-south1"
    error_message = "The executor/verifier routes are fixed to the asia-south1 production Cloud Run audience."
  }
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

// Dedicated identity for the Nirmana evidence-command executor route
// (record_definition, freeze_definition, supersede_definition,
// record_label_catalogue, accept_baseline_candidate, and every record_evidence
// event_type EXCEPT the terminal-capsule ones reserved for the verifier
// below). Can invoke only amjis-web; the route itself further restricts which
// commands this principal may submit (per-command allowlist, not just
// audience/principal match).
resource "google_service_account" "nirmana_elevation_executor" {
  account_id   = "amjis-nirmana-executor"
  display_name = "Nirmana elevation executor"
  description  = "Dedicated OIDC identity for non-terminal Nirmana evidence/definition commands, invoked on demand via service-account impersonation."
  project      = var.gcp_project
}

// Dedicated identity for terminal-capsule submission only
// (record_evidence with event_type in {asset_frozen, stage_transition_accepted
// when it represents a layer freeze}). Kept structurally distinct from the
// executor identity so implementer/certifier separation is enforced at the
// route's principal allowlist, not only by the DB-role source_kind trigger
// that already existed. See CAMPAIGN_STATE.md for the one honest residual:
// the same human (native) currently holds serviceAccountTokenCreator on both
// identities, so this is allowlist-enforced separation, not disjoint-human
// separation -- accepted and logged, not claimed as more than it is.
resource "google_service_account" "nirmana_elevation_verifier" {
  account_id   = "amjis-nirmana-verifier"
  display_name = "Nirmana elevation verifier"
  description  = "Dedicated OIDC identity for terminal-capsule Nirmana evidence commands only, invoked on demand via service-account impersonation."
  project      = var.gcp_project
}

// Lets the native's own Google identity mint short-lived ID tokens for the
// executor SA (`gcloud auth print-identity-token
// --impersonate-service-account=amjis-nirmana-executor@... --audiences=...`).
// No standing trigger, no key file, no broader grant: this is the sole
// permission needed for per-action, on-demand impersonation.
resource "google_service_account_iam_member" "native_impersonates_executor" {
  service_account_id = google_service_account.nirmana_elevation_executor.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "user:mail.abhisek.mohanty@gmail.com"
}

// Same, for the verifier SA.
resource "google_service_account_iam_member" "native_impersonates_verifier" {
  service_account_id = google_service_account.nirmana_elevation_verifier.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "user:mail.abhisek.mohanty@gmail.com"
}

output "nirmana_elevation_executor_email" {
  value = google_service_account.nirmana_elevation_executor.email
}

output "nirmana_elevation_verifier_email" {
  value = google_service_account.nirmana_elevation_verifier.email
}
