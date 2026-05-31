// Remote state — GCS-backed terraform state for the cloud_scheduler module.
terraform {
  backend "gcs" {
    bucket = "madhav-astrology-tf-state"
    prefix = "infra/cloud_scheduler"
  }
}
