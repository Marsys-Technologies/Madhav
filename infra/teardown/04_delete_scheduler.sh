#!/usr/bin/env bash
# =============================================================================
# 04_delete_scheduler.sh — Delete build-reaper + build-trigger Cloud Scheduler jobs
#                          and their dedicated service accounts
# OPERATOR-RUN ONLY
#
# Deletes:
#   - Cloud Scheduler job: build-reaper (*/15 * * * * → POST /api/build/reap)
#   - Service Account: build-reaper@madhav-astrology.iam.gserviceaccount.com
#   - Any build-trigger scheduler jobs (e.g. build-pipeline-trigger)
#
# Keeps all serve-side SAs (amjis-web-runtime, amjis-sidecar-runtime, amjis-mcp-runtime).
#
# IaC NOTE: After running this script, also remove the corresponding
#   `google_cloud_scheduler_job.build_reaper` and
#   `google_service_account.build_reaper` resources from
#   infra/cloud_scheduler/build_reaper.tf and run `terraform apply`.
#   See infra/teardown/05_iac_diff.tf for the exact removal diff.
#
# Pre-requisites:
#   - gcloud auth login + project set to amjis-prod
#   - terraform state accessible (to match TF SA deletion)
#
# Usage:
#   bash infra/teardown/04_delete_scheduler.sh
# =============================================================================

set -euo pipefail

PROJECT="amjis-prod"
REGION="asia-south1"
REAPER_JOB="build-reaper"
REAPER_SA="build-reaper@${PROJECT}.iam.gserviceaccount.com"

echo "=== Delete Cloud Scheduler: build jobs ==="
echo ""

# 1. Delete build-reaper scheduler job
echo "[1/4] Deleting Cloud Scheduler job: ${REAPER_JOB}..."
REAPER_EXISTS=$(gcloud scheduler jobs describe "${REAPER_JOB}" \
  --location="${REGION}" \
  --project="${PROJECT}" \
  --format="value(name)" 2>/dev/null || echo "NOT_FOUND")

if [ "${REAPER_EXISTS}" = "NOT_FOUND" ]; then
  echo "  Job ${REAPER_JOB} not found. Already deleted."
else
  gcloud scheduler jobs delete "${REAPER_JOB}" \
    --location="${REGION}" \
    --project="${PROJECT}" \
    --quiet
  echo "  ✓ Scheduler job '${REAPER_JOB}' deleted."
fi

# 2. Delete any build-trigger scheduler jobs
echo ""
echo "[2/4] Checking for other build-trigger scheduler jobs..."
BUILD_JOBS=$(gcloud scheduler jobs list \
  --location="${REGION}" \
  --project="${PROJECT}" \
  --format="value(name)" 2>/dev/null | grep -i "build" || true)

if [ -z "${BUILD_JOBS}" ]; then
  echo "  No additional build scheduler jobs found."
else
  echo "  Found build-related jobs:"
  echo "${BUILD_JOBS}"
  echo "  Deleting..."
  while IFS= read -r JOB_FULL_NAME; do
    JOB_SHORT=$(basename "${JOB_FULL_NAME}")
    gcloud scheduler jobs delete "${JOB_SHORT}" \
      --location="${REGION}" \
      --project="${PROJECT}" \
      --quiet && echo "  ✓ Deleted: ${JOB_SHORT}"
  done <<< "${BUILD_JOBS}"
fi

# 3. Delete build-reaper service account
echo ""
echo "[3/4] Deleting service account: ${REAPER_SA}..."
SA_EXISTS=$(gcloud iam service-accounts describe "${REAPER_SA}" \
  --project="${PROJECT}" \
  --format="value(email)" 2>/dev/null || echo "NOT_FOUND")

if [ "${SA_EXISTS}" = "NOT_FOUND" ]; then
  echo "  SA ${REAPER_SA} not found. Already deleted."
else
  gcloud iam service-accounts delete "${REAPER_SA}" \
    --project="${PROJECT}" \
    --quiet
  echo "  ✓ Service account '${REAPER_SA}' deleted."
fi

# 4. Remove build_reaper TF state (must be run after terraform destroy or import-to-null)
echo ""
echo "[4/4] Terraform IaC cleanup required:"
echo "  cd infra/cloud_scheduler"
echo "  # Review 05_iac_diff.tf for the resource removals"
echo "  terraform state rm google_cloud_scheduler_job.build_reaper 2>/dev/null || true"
echo "  terraform state rm google_service_account.build_reaper     2>/dev/null || true"
echo "  # Then delete infra/cloud_scheduler/build_reaper.tf and run terraform apply"
echo ""
echo "=== Scheduler + SA teardown complete ==="
