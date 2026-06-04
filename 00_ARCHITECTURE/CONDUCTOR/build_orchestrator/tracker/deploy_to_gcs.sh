#!/usr/bin/env bash
# Deploy the tracker to a public GCS bucket. Run once for setup, then per state.json change.
# Production URL: https://storage.googleapis.com/marsys-tracker-public/index.html
#
# Usage:
#   bash deploy_to_gcs.sh setup     # one-time bucket creation + index.html upload + public access
#   bash deploy_to_gcs.sh state     # upload state.json only (called by Conductor after every update)
#   bash deploy_to_gcs.sh all       # upload both
set -euo pipefail

BUCKET="${TRACKER_BUCKET:-marsys-tracker-public}"
DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-state}"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "ERROR: gcloud not installed" >&2
  exit 1
fi

if [ "$MODE" = "setup" ] || [ "$MODE" = "all" ]; then
  echo "Setting up bucket gs://$BUCKET ..."
  gcloud storage buckets create "gs://$BUCKET" --location=asia-south1 --uniform-bucket-level-access 2>/dev/null || echo "Bucket exists, continuing"
  gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --member=allUsers --role=roles/storage.objectViewer
  gcloud storage buckets update "gs://$BUCKET" --web-main-page-suffix=index.html
  echo "Uploading index.html (with production state URL injected)..."
  TMP="$(mktemp)"
  # Inject window.TRACKER_STATE_URL so the page fetches state.json from its own GCS origin
  sed "s|<body>|<body><script>window.TRACKER_STATE_URL='https://storage.googleapis.com/$BUCKET/state.json';</script>|" "$DIR/index.html" > "$TMP"
  gcloud storage cp "$TMP" "gs://$BUCKET/index.html" --content-type=text/html --cache-control="no-cache, max-age=60"
  rm -f "$TMP"
fi

if [ "$MODE" = "state" ] || [ "$MODE" = "all" ]; then
  # state.json must update fast — no cache
  gcloud storage cp "$DIR/state.json" "gs://$BUCKET/state.json" --content-type=application/json --cache-control="no-cache, no-store, must-revalidate, max-age=0"
fi

echo ""
echo "Public URL:  https://storage.googleapis.com/$BUCKET/index.html"
echo "State JSON:  https://storage.googleapis.com/$BUCKET/state.json"
