terraform {
  backend "gcs" {
    // Bucket + prefix are supplied via the apply.sh wrapper:
    //   terraform init -backend-config=bucket=... -backend-config=prefix=...
  }
}
