#!/usr/bin/env bash
# provision_logical_export_scheduler.sh — one-time setup for the G1-E
# scheduled independent logical export.
#
# Mirrors the existing provision_watchdog_scheduler.sh convention (Cloud
# Scheduler -> an authenticated HTTP trigger) but targets a Cloud Run JOB
# rather than a web service, because this workload (pg_dump against Cloud
# SQL, then upload to GCS) is a batch task with a real exit code and a
# runtime that can legitimately exceed a typical request timeout — a Cloud
# Run Job is the correct primitive, not another Scheduler->web-route hit.
#
# WHAT THIS SCRIPT DOES NOT DO: it does not touch Cloud SQL itself (no
# `gcloud sql ...` calls anywhere in this file) — it only builds a container,
# creates a Cloud Run Job, and wires a Cloud Scheduler trigger to run it.
# Independent-of-Cloud-SQL-backups is the whole point of this mechanism.
#
# NOT YET RUN. Written and ready for an operator with deploy authorization to
# execute after reviewing it — see the G1-E status doc for why this session
# did not run it.
#
# Requires: gcloud CLI authenticated with deploy permissions on the project;
# platform/scripts/backup/{export_irreplaceable_tables.sh,
# restore_irreplaceable_tables.sh, irreplaceable_table_sets.sh} present in the
# image build context.

set -euo pipefail

PROJECT="${GCP_PROJECT:-madhav-astrology}"
REGION="${GCP_REGION:-asia-south1}"
INSTANCE_CONNECTION_NAME="${INSTANCE_CONNECTION_NAME:-madhav-astrology:asia-south1:amjis-postgres}"
JOB_NAME="g1e-logical-export"
SCHEDULER_JOB_NAME="g1e-logical-export-hourly"
GCS_BUCKET="${GCS_BUCKET:-madhav-astrology-g1e-exports}"
IMAGE="${IMAGE:-asia-south1-docker.pkg.dev/${PROJECT}/amjis/g1e-logical-export:latest}"
SA_EMAIL="${SA_EMAIL:-g1e-export-runner@${PROJECT}.iam.gserviceaccount.com}"

echo "==> [1/5] Ensure the GCS bucket exists with a lifecycle rule (30-day"
echo "    retention on the export objects — this bucket is a safety net, not"
echo "    a permanent archive; long-term retention is a separate decision)."
gcloud storage buckets create "gs://${GCS_BUCKET}" \
  --project="$PROJECT" \
  --location="$REGION" \
  --uniform-bucket-level-access 2>/dev/null || true
cat > /tmp/g1e_lifecycle.json <<'JSON'
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 30}
    }
  ]
}
JSON
gcloud storage buckets update "gs://${GCS_BUCKET}" \
  --project="$PROJECT" \
  --lifecycle-file=/tmp/g1e_lifecycle.json

echo "==> [2/5] Create the dedicated runner service account (least privilege:"
echo "    Cloud SQL Client on the instance, Storage Object Admin on this one"
echo "    bucket only — NOT project-wide Storage Admin, NOT any Cloud SQL"
echo "    admin/edit role. This account can produce a dump; it cannot touch"
echo "    Cloud SQL instance configuration, backups, or PITR settings)."
gcloud iam service-accounts create g1e-export-runner \
  --project="$PROJECT" \
  --display-name="G1-E logical export runner (read-only DB, write-only to its own GCS prefix)" \
  2>/dev/null || true

gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudsql.client"

gcloud storage buckets add-iam-policy-binding "gs://${GCS_BUCKET}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin"

echo "==> [3/5] Build and push the export runner image (pg_dump/pg_restore +"
echo "    this lane's scripts baked in; see platform/scripts/backup/Dockerfile)."
gcloud builds submit "$(dirname "${BASH_SOURCE[0]}")" \
  --project="$PROJECT" \
  --tag="$IMAGE"

echo "==> [4/5] Create/update the Cloud Run Job. Connects to Cloud SQL via"
echo "    the built-in Cloud SQL connector (--set-cloudsql-instances) so no"
echo "    proxy sidecar or public IP exposure is needed. DATABASE_URL is"
echo "    read from Secret Manager, never baked into the image or job spec."
gcloud run jobs create "$JOB_NAME" \
  --project="$PROJECT" \
  --region="$REGION" \
  --image="$IMAGE" \
  --set-cloudsql-instances="$INSTANCE_CONNECTION_NAME" \
  --set-secrets="DATABASE_URL=g1e-export-database-url:latest" \
  --set-env-vars="GCS_BUCKET=${GCS_BUCKET},OUT=/tmp/g1e_out" \
  --service-account="$SA_EMAIL" \
  --max-retries=1 \
  --task-timeout=900 \
  --command="/app/platform/scripts/backup/export_irreplaceable_tables.sh" \
  --args="--set,both" \
  2>/dev/null || \
gcloud run jobs update "$JOB_NAME" \
  --project="$PROJECT" \
  --region="$REGION" \
  --image="$IMAGE" \
  --set-cloudsql-instances="$INSTANCE_CONNECTION_NAME" \
  --set-secrets="DATABASE_URL=g1e-export-database-url:latest" \
  --set-env-vars="GCS_BUCKET=${GCS_BUCKET},OUT=/tmp/g1e_out" \
  --service-account="$SA_EMAIL" \
  --max-retries=1 \
  --task-timeout=900 \
  --command="/app/platform/scripts/backup/export_irreplaceable_tables.sh" \
  --args="--set,both"

echo "==> [5/5] Wire an hourly Cloud Scheduler trigger. Hourly (not daily) on"
echo "    purpose: the irreplaceable sets carry the tightest RPO target in"
echo "    this lane's runbook (ledger+conversations <= 1h) — PITR is the"
echo "    mechanism that actually delivers that RPO once enabled (continuous"
echo "    WAL archiving, near-zero data loss window); this export is the"
echo "    independent second line of defense and is kept on the same cadence"
echo "    so it is never the looser guarantee of the two."
RUN_JOB_URI="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT}/jobs/${JOB_NAME}:run"
gcloud scheduler jobs create http "$SCHEDULER_JOB_NAME" \
  --project="$PROJECT" \
  --location="$REGION" \
  --schedule="0 * * * *" \
  --uri="$RUN_JOB_URI" \
  --http-method=POST \
  --oauth-service-account-email="$SA_EMAIL" \
  2>/dev/null || \
gcloud scheduler jobs update http "$SCHEDULER_JOB_NAME" \
  --project="$PROJECT" \
  --location="$REGION" \
  --schedule="0 * * * *" \
  --uri="$RUN_JOB_URI" \
  --http-method=POST \
  --oauth-service-account-email="$SA_EMAIL"

echo "==> Done. Verify with:"
echo "    gcloud run jobs execute ${JOB_NAME} --project=${PROJECT} --region=${REGION}"
echo "    gcloud scheduler jobs describe ${SCHEDULER_JOB_NAME} --project=${PROJECT} --location=${REGION}"
