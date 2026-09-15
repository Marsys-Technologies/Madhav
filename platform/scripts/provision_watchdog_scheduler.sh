#!/usr/bin/env bash
# Converge the watchdog Cloud Scheduler job on audience-bound OIDC.
# Run immediately after deploying the OIDC-only watchdog route.
# Requires Scheduler update plus iam.serviceAccounts.actAs on the scheduler SA.

set -euo pipefail

PROJECT="${GCP_PROJECT:-madhav-astrology}"
REGION="${GCP_REGION:-asia-south1}"
APP_URL="${APP_URL:-https://madhav.marsys.in}"
OIDC_AUDIENCE="${WATCHDOG_OIDC_AUDIENCE:-https://amjis-web-938361928218.asia-south1.run.app}"
SCHEDULER_SERVICE_ACCOUNT="${WATCHDOG_SCHEDULER_SERVICE_ACCOUNT:-amjis-scheduler@${PROJECT}.iam.gserviceaccount.com}"

if ! gcloud iam service-accounts describe "$SCHEDULER_SERVICE_ACCOUNT" \
  --project="$PROJECT" >/dev/null 2>&1; then
  echo "ERROR: watchdog scheduler service account does not exist: $SCHEDULER_SERVICE_ACCOUNT" >&2
  exit 1
fi

echo "==> Creating/updating Cloud Scheduler job watchdog-reaper with OIDC"
if gcloud scheduler jobs describe watchdog-reaper \
  --location="$REGION" --project="$PROJECT" >/dev/null 2>&1; then
  gcloud scheduler jobs update http watchdog-reaper \
    --schedule="*/5 * * * *" \
    --uri="${APP_URL}/api/cockpit/watchdog" \
    --http-method=POST \
    --oidc-service-account-email="$SCHEDULER_SERVICE_ACCOUNT" \
    --oidc-token-audience="$OIDC_AUDIENCE" \
    --clear-headers \
    --location="$REGION" \
    --project="$PROJECT" \
    --quiet
else
  gcloud scheduler jobs create http watchdog-reaper \
    --schedule="*/5 * * * *" \
    --uri="${APP_URL}/api/cockpit/watchdog" \
    --http-method=POST \
    --oidc-service-account-email="$SCHEDULER_SERVICE_ACCOUNT" \
    --oidc-token-audience="$OIDC_AUDIENCE" \
    --location="$REGION" \
    --project="$PROJECT" \
    --quiet
fi

echo "==> Done. Watchdog will fire every 5 minutes with audience-bound OIDC"
echo "    Caller: $SCHEDULER_SERVICE_ACCOUNT"
echo "    Audience: $OIDC_AUDIENCE"
