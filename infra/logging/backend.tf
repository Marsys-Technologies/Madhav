// Remote state — GCS-backed terraform state for the logging exclusions module.
terraform {
  backend "gcs" {
    bucket = "madhav-astrology-tf-state"
    prefix = "infra/logging"
  }
}
