// =============================================================================
// 05_iac_diff.tf — IaC resources to REMOVE after legacy teardown
// OPERATOR GUIDANCE — not a runnable Terraform file on its own
//
// This file documents the Terraform resources that must be removed from the
// live IaC state after the infra teardown scripts (02–04) have been run.
//
// Instructions:
//   1. After running 03_delete_cloud_run_job.sh + 04_delete_scheduler.sh:
//      cd infra/cloud_scheduler
//      terraform state rm google_cloud_scheduler_job.build_reaper
//      terraform state rm google_service_account.build_reaper
//      rm infra/cloud_scheduler/build_reaper.tf   # or empty it
//      terraform apply  # confirms state matches reality
//
//   2. For the builder SA IAM grants in infra/iam/main.tf:
//      The amjis-builder-runtime SA should be retained (it's the deploy SA
//      for GH Actions + Cloud Build). Only the build-pipeline-specific grants
//      below can be removed if the new rebuild pipeline uses a different SA.
//      Operator decision required.
//
// =============================================================================

// ── REMOVE: infra/cloud_scheduler/build_reaper.tf ────────────────────────────
// Delete the entire file after running 04_delete_scheduler.sh.
// These resources are gone from GCP after the script runs:

// REMOVED:
// resource "google_service_account" "build_reaper" {
//   account_id   = "build-reaper"
//   display_name = "Build Reaper (Cloud Scheduler invoker)"
//   project      = var.gcp_project
// }

// REMOVED:
// resource "google_cloud_scheduler_job" "build_reaper" {
//   name        = "build-reaper"
//   schedule    = "*/15 * * * *"
//   ...
// }

// ── REMOVE from infra/iam/main.tf (IF build pipeline SA no longer needed) ────
// amjis-builder-runtime is the GH Actions deploy SA — retain it unless
// the new pipeline uses a dedicated SA. Operator decision.
//
// IF removing the build pipeline grants:
//
// REMOVE:
// resource "google_project_iam_member" "builder_run_admin" { ... }
// resource "google_project_iam_member" "builder_ar_writer" { ... }
// resource "google_service_account_iam_member" "builder_actas_web" { ... }
// resource "google_service_account_iam_member" "builder_actas_sidecar" { ... }
// resource "google_service_account_iam_member" "builder_actas_mcp" { ... }
// resource "google_service_account_iam_member" "wif_impersonates_builder" { ... }
// resource "google_service_account" "amjis_builder_runtime" { ... }

// ── KEEP: Artifact Registry repo for pipeline images (might be reused) ────────
// infra/artifact_registry/ — operator decision whether to delete the
// marsys-pipeline Artifact Registry repo or keep it for the rebuild.
// Safe to keep; costs ~$0/mo empty.
