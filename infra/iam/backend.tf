// Remote state — GCS-backed terraform state for the per-service IAM module.
terraform {
  backend "gcs" {}
}
