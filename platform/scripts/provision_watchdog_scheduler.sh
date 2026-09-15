#!/usr/bin/env bash
# provision_watchdog_scheduler.sh — one-time setup for the watchdog Cloud Scheduler job.
# Run once by the operator after deploying the watchdog endpoint.
# Requires: gcloud CLI authenticated with project admin permissions.

set -euo pipefail

PROJECT="${GCP_PROJECT:-madhav-astrology}"
REGION="${GCP_REGION:-asia-south1}"
APP_URL="${APP_URL:-https://madhav.marsys.in}"
SECRET_NAME="watchdog-secret"
WEB_SERVICE_ACCOUNT="amjis-web-runtime@${PROJECT}.iam.gserviceaccount.com"

echo "==> Ensuring watchdog secret exists in project $PROJECT"
if ! gcloud secrets describe "$SECRET_NAME" --project="$PROJECT" >/dev/null 2>&1; then
  gcloud secrets create "$SECRET_NAME" \
    --replication-policy=automatic \
    --project="$PROJECT" \
    --quiet
fi

if [[ "${ROTATE_WATCHDOG_SECRET:-false}" == "true" ]]; then
  SECRET_VALUE="$(openssl rand -hex 32)"
  SECRET_VERSION_RESOURCE="$(printf '%s' "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" \
    --data-file=- \
    --project="$PROJECT" \
    --format='value(name)')"
  SECRET_VERSION="${SECRET_VERSION_RESOURCE##*/}"
else
  SECRET_VERSION="$(gcloud secrets versions list "$SECRET_NAME" \
    --project="$PROJECT" \
    --filter='state=ENABLED' \
    --sort-by='~createTime' \
    --limit=1 \
    --format='value(name)')"
  if [[ -z "$SECRET_VERSION" ]]; then
    SECRET_VALUE="$(openssl rand -hex 32)"
    SECRET_VERSION_RESOURCE="$(printf '%s' "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" \
      --data-file=- \
      --project="$PROJECT" \
      --format='value(name)')"
    SECRET_VERSION="${SECRET_VERSION_RESOURCE##*/}"
  fi
fi

gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --member="serviceAccount:${WEB_SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$PROJECT" \
  --quiet >/dev/null

echo "==> Binding WATCHDOG_SECRET to Cloud Run service amjis-web from Secret Manager version $SECRET_VERSION"
gcloud run services update amjis-web \
  --region="$REGION" \
  --project="$PROJECT" \
  --remove-env-vars WATCHDOG_SECRET \
  --update-secrets "WATCHDOG_SECRET=${SECRET_NAME}:${SECRET_VERSION}" \
  --quiet

echo "==> Creating/updating Cloud Scheduler job watchdog-reaper"
if [[ -z "${SECRET_VALUE:-}" ]]; then
  SECRET_VALUE="$(gcloud secrets versions access "$SECRET_VERSION" \
    --secret="$SECRET_NAME" \
    --project="$PROJECT")"
fi

if gcloud scheduler jobs describe watchdog-reaper \
  --location="$REGION" --project="$PROJECT" >/dev/null 2>&1; then
  gcloud scheduler jobs update http watchdog-reaper \
    --schedule="*/5 * * * *" \
    --uri="${APP_URL}/api/cockpit/watchdog" \
    --http-method=POST \
    --update-headers="x-watchdog-auth=${SECRET_VALUE}" \
    --location="$REGION" \
    --project="$PROJECT" \
    --quiet
else
  gcloud scheduler jobs create http watchdog-reaper \
    --schedule="*/5 * * * *" \
    --uri="${APP_URL}/api/cockpit/watchdog" \
    --http-method=POST \
    --headers="x-watchdog-auth=${SECRET_VALUE}" \
    --location="$REGION" \
    --project="$PROJECT" \
    --quiet
fi
unset SECRET_VALUE

echo "==> Done. Watchdog will fire every 5 minutes at ${APP_URL}/api/cockpit/watchdog"
echo "    Secret stored in Secret Manager as: $SECRET_NAME"
