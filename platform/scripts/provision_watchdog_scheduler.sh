#!/usr/bin/env bash
# provision_watchdog_scheduler.sh — one-time setup for the watchdog Cloud Scheduler job.
# Run once by the operator after deploying the watchdog endpoint.
# Requires: gcloud CLI authenticated with project admin permissions.

set -euo pipefail

PROJECT="${GCP_PROJECT:-madhav-astrology}"
REGION="${GCP_REGION:-asia-south1}"
APP_URL="${APP_URL:-https://madhav.marsys.in}"
SECRET_NAME="watchdog-secret"

echo "==> Creating/rotating watchdog secret in project $PROJECT"
gcloud secrets create "$SECRET_NAME" \
  --replication-policy=automatic \
  --project="$PROJECT" 2>/dev/null || true

SECRET_VALUE="$(openssl rand -hex 32)"
echo -n "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" \
  --data-file=- \
  --project="$PROJECT"

echo "==> Adding WATCHDOG_SECRET to Cloud Run service amjis-web"
gcloud run services update amjis-web \
  --region="$REGION" \
  --project="$PROJECT" \
  --update-env-vars "WATCHDOG_SECRET=${SECRET_VALUE}"

echo "==> Creating/updating Cloud Scheduler job watchdog-reaper"
RESOLVED_SECRET="$(gcloud secrets versions access latest \
  --secret="$SECRET_NAME" \
  --project="$PROJECT")"

gcloud scheduler jobs create http watchdog-reaper \
  --schedule="*/5 * * * *" \
  --uri="${APP_URL}/api/cockpit/watchdog" \
  --http-method=POST \
  --headers="x-watchdog-auth=${RESOLVED_SECRET}" \
  --location="$REGION" \
  --project="$PROJECT" 2>/dev/null || \
gcloud scheduler jobs update http watchdog-reaper \
  --schedule="*/5 * * * *" \
  --uri="${APP_URL}/api/cockpit/watchdog" \
  --http-method=POST \
  --headers="x-watchdog-auth=${RESOLVED_SECRET}" \
  --location="$REGION" \
  --project="$PROJECT"

echo "==> Done. Watchdog will fire every 5 minutes at ${APP_URL}/api/cockpit/watchdog"
echo "    Secret stored in Secret Manager as: $SECRET_NAME"
