#!/bin/bash
# Run this once to configure Cloud Logging alerts for production error monitoring.
# Requires: gcloud auth login with appropriate permissions.

PROJECT="${GOOGLE_CLOUD_PROJECT:-amjis-prod}"

echo "Setting up Cloud Logging alert policies for $PROJECT..."

# Alert: pipeline job exits non-zero
gcloud logging sinks create build-job-errors \
  storage.googleapis.com/${PROJECT}-logs-bucket \
  --log-filter='resource.type="cloud_run_job" severity>=ERROR' \
  --project="$PROJECT" || true

echo "Note: Create alert policies in GCP Console → Monitoring → Alerting."
echo "Recommended alerts:"
echo "  1. Log-based metric: build_runs transition to failed"
echo "  2. Cloud Run Job: execution exit_code != 0 for brahma-build-pipeline-job"
echo "  3. Cloud Run Service: error_count > 10/min for amjis-web"
echo "Done."
