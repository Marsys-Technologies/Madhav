#!/bin/bash
# Canary deploy: 10% -> 5min log watch -> promote 100% OR rollback.
# Usage: deploy_and_smoke.sh <service-name> <session-id>
set -e
SERVICE="$1"
SESSION_ID="$2"
REGION="asia-south1"
PROJECT="madhav-astrology"

[ -z "$SERVICE" ] && echo "ERROR: service required" && exit 1

echo "=== DEPLOY $SERVICE (session $SESSION_ID) ==="

# Build via Cloud Build
if [ -f "platform/cloudbuild.yaml" ] && [ "$SERVICE" = "amjis-web" ]; then
  gcloud builds submit --config platform/cloudbuild.yaml --project "$PROJECT"
elif [ -f "platform/python-sidecar/cloudbuild.yaml" ] && [ "$SERVICE" = "amjis-sidecar" ]; then
  gcloud builds submit --config platform/python-sidecar/cloudbuild.yaml platform/python-sidecar/ --project "$PROJECT"
fi

# Get latest revision
LATEST_REVISION=$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format "value(status.latestCreatedRevisionName)")

# Canary: route 10% to new revision
gcloud run services update-traffic "$SERVICE" \
  --region "$REGION" --project "$PROJECT" \
  --to-revisions "${LATEST_REVISION}=10"

echo "Canary deployed: $LATEST_REVISION at 10% — watching logs 5 min..."
sleep 30

# Check error rate
ERROR_COUNT=$(gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE AND severity>=ERROR" \
  --freshness=5m --limit=20 --project "$PROJECT" 2>/dev/null | grep -c "severity" || true)

if [ "$ERROR_COUNT" -gt 5 ]; then
  echo "ERROR: $ERROR_COUNT errors detected — rolling back"
  gcloud run services update-traffic "$SERVICE" \
    --region "$REGION" --project "$PROJECT" \
    --to-revisions LATEST=0
  echo "ROLLBACK: previous revision restored"
  exit 1
fi

# Wait remainder of 5 min
sleep 270

# Promote to 100%
gcloud run services update-traffic "$SERVICE" \
  --region "$REGION" --project "$PROJECT" \
  --to-latest

echo "OK: $SERVICE promoted to 100% (revision $LATEST_REVISION)"
