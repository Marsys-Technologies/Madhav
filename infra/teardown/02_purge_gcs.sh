#!/usr/bin/env bash
# =============================================================================
# 02_purge_gcs.sh — Purge the madhav-marsys-build-artifacts GCS bucket
# OPERATOR-RUN ONLY — run AFTER 00_archive.sh completes
#
# Deletes: gs://madhav-marsys-build-artifacts  (all contents + bucket)
# Keeps:   gs://madhav-astrology-chat-attachments
#          gs://madhav-astrology-chart-documents
#          gs://madhav-astrology-tf-state
#
# Pre-requisites:
#   - gcloud auth application-default login (project: amjis-prod)
#   - 00_archive.sh has completed and ARCHIVE_MANIFEST.txt is readable in GCS
#
# Usage:
#   bash infra/teardown/02_purge_gcs.sh
# =============================================================================

set -euo pipefail

PROJECT="amjis-prod"
BUILD_ARTIFACT_BUCKET="gs://madhav-marsys-build-artifacts"
ARCHIVE_BUCKET="gs://madhav-astrology-tf-state/teardown-archive"

echo "=== GCS Build-Artifact Purge ==="
echo "Target: ${BUILD_ARTIFACT_BUCKET}"
echo ""

# Safety check: confirm archive manifest exists before deleting source
echo "[1/3] Verifying archive manifest exists..."
MANIFEST_COUNT=$(gsutil ls "${ARCHIVE_BUCKET}/**/ARCHIVE_MANIFEST.txt" 2>/dev/null | wc -l | tr -d ' ')
if [ "${MANIFEST_COUNT}" -lt 1 ]; then
  echo "ERROR: No ARCHIVE_MANIFEST.txt found under ${ARCHIVE_BUCKET}"
  echo "       Run 00_archive.sh first and verify it completed."
  exit 1
fi
echo "  ✓ Archive manifest found (${MANIFEST_COUNT} run(s))"

# Confirm the bucket to be deleted
echo ""
echo "[2/3] Confirming bucket exists and size..."
gsutil du -sh "${BUILD_ARTIFACT_BUCKET}" 2>/dev/null || {
  echo "  Bucket ${BUILD_ARTIFACT_BUCKET} does not exist or is already empty. Nothing to do."
  exit 0
}

# Delete all objects and the bucket
echo ""
echo "[3/3] Removing all objects from ${BUILD_ARTIFACT_BUCKET}..."
echo "  This will PERMANENTLY delete all build manifests, ephemeris CSVs,"
echo "  extraction YAMLs, M9 Tajaka artifacts, and pipeline state."
echo ""
echo "  Waiting 5 seconds — press Ctrl+C to abort..."
sleep 5

gsutil -m rm -r "${BUILD_ARTIFACT_BUCKET}" && \
  echo "  ✓ Bucket ${BUILD_ARTIFACT_BUCKET} purged and deleted."

echo ""
echo "=== GCS purge complete ==="
echo "  Verify kept buckets are untouched:"
echo "    gsutil ls gs://madhav-astrology-chat-attachments"
echo "    gsutil ls gs://madhav-astrology-chart-documents"
echo "    gsutil ls gs://madhav-astrology-tf-state"
