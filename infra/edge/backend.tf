// Remote state — GCS-backed terraform state for the edge LB+CDN+Armor module.
// Backend config (bucket/prefix) supplied via `-backend-config` from apply.sh.

terraform {
  backend "gcs" {}
}
