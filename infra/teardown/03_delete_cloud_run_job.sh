#!/usr/bin/env bash
# =============================================================================
# 03_delete_cloud_run_job.sh — Delete the marsys-build-pipeline-job Cloud Run Job
# OPERATOR-RUN ONLY
#
# Deletes the Cloud Run Job `marsys-build-pipeline-job` in asia-south1.
# Keeps: amjis-web, amjis-sidecar, amjis-mcp (serve shells)
#
# Pre-requisites:
#   - gcloud auth login + project set to amjis-prod
#
# Usage:
#   bash infra/teardown/03_delete_cloud_run_job.sh
# =============================================================================

set -euo pipefail

PROJECT="amjis-prod"
REGION="asia-south1"
JOB_NAME="marsys-build-pipeline-job"

echo "=== Delete Cloud Run Job: ${JOB_NAME} ==="
echo ""

# Confirm the job exists
echo "[1/2] Checking job existence..."
JOB_STATUS=$(gcloud run jobs describe "${JOB_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT}" \
  --format="value(metadata.name)" 2>/dev/null || echo "NOT_FOUND")

if [ "${JOB_STATUS}" = "NOT_FOUND" ]; then
  echo "  Job ${JOB_NAME} not found in ${REGION}. Already deleted or never existed."
  exit 0
fi

echo "  Found: ${JOB_STATUS}"
echo ""
echo "[2/2] Deleting job..."
gcloud run jobs delete "${JOB_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT}" \
  --quiet

echo ""
echo "  ✓ Cloud Run Job '${JOB_NAME}' deleted."
echo ""
echo "  Verify kept services are untouched:"
echo "    gcloud run services list --region=${REGION} --project=${PROJECT}"
echo "    (should still show: amjis-web, amjis-sidecar, amjis-mcp)"
