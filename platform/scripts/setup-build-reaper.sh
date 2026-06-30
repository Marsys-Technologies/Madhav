#!/bin/bash
# Create the Cloud Scheduler job that calls the watchdog endpoint every 5 minutes.
# This must be configured in the target GCP project.
# NOTE: As of 2026-06-30 the reaper job already exists as 'watchdog-reaper'
# in asia-south1. This script is retained for documentation and re-creation
# if the job is ever deleted.
PROJECT="${GOOGLE_CLOUD_PROJECT:-amjis-prod}"
PLATFORM_URL="${PLATFORM_URL:-https://your-platform-url.run.app}"

gcloud scheduler jobs create http brahma-build-reaper \
  --location=asia-south1 \
  --schedule="*/5 * * * *" \
  --uri="${PLATFORM_URL}/api/cockpit/watchdog" \
  --http-method=POST \
  --headers="Content-Type=application/json,x-watchdog-auth=${WATCHDOG_SECRET}" \
  --message-body='{}' \
  --time-zone="Asia/Kolkata" \
  --project="$PROJECT"

echo "Build reaper scheduled at */5 (every 5 minutes)"
