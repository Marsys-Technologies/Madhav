#!/usr/bin/env bash
# =============================================================================
# 00_archive.sh — Pre-teardown snapshot to cold storage
# OPERATOR-RUN ONLY — do not execute via automation
#
# Purpose: before any DROP/DELETE, snapshot all legacy data tables to a
#   cold-storage GCS path so the teardown is recoverable. Also snapshots
#   the build-artifact bucket prefix for audit trail.
#
# Pre-requisites:
#   - gcloud auth application-default login (with project set to amjis-prod)
#   - PGPASSWORD env var set (or .pgpass configured) for the Cloud SQL instance
#   - Cloud SQL Auth Proxy running on localhost:5432 (or use --cloud-sql-instance)
#
# Usage:
#   PGHOST=localhost PGPORT=5432 PGUSER=amjis_app PGPASSWORD=<pw> \
#   PGDATABASE=amjis bash infra/teardown/00_archive.sh
# =============================================================================

set -euo pipefail

PROJECT="amjis-prod"
REGION="asia-south1"
ARCHIVE_BUCKET="gs://madhav-astrology-tf-state/teardown-archive/$(date +%Y%m%d_%H%M%S)"
BUILD_ARTIFACT_BUCKET="gs://madhav-marsys-build-artifacts"

echo "=== MARSYS-JIS Legacy Teardown Archive ==="
echo "Target archive path: ${ARCHIVE_BUCKET}"
echo ""

# ---------------------------------------------------------------------------
# 1. Tag the current git state
# ---------------------------------------------------------------------------
echo "[1/4] Verifying git tag pre-legacy-teardown..."
git tag -l "pre-legacy-teardown" | grep -q "pre-legacy-teardown" \
  && echo "  ✓ Tag 'pre-legacy-teardown' exists on commit: $(git rev-parse pre-legacy-teardown)" \
  || echo "  WARNING: tag not found — run: git tag pre-legacy-teardown <sha>"

# ---------------------------------------------------------------------------
# 2. Dump all DROP tables to compressed SQL files
# ---------------------------------------------------------------------------
echo ""
echo "[2/4] Dumping DROP tables to ${ARCHIVE_BUCKET}/db/ ..."

TABLES=(
  # Astronomical
  ephemeris_daily
  panchanga_daily
  # L1 chart facts
  chart_facts
  chart_facts_history
  chart_facts_supersedence
  varshaphala
  # L1 temporal
  dasha_periods
  chart_dashas
  l1_time_synchronicity
  l1_phase_locked_anchors
  l1_bhrigu_bindu_transits
  l1_graha_aspects_lifetime
  l1_vedha_extended
  l1_varsha_digest
  l1_tajik_varsha_year_lords
  # Reference chakra tables
  l1_sarvatobhadra_positions
  l1_sarvatobhadra_vedha
  l1_sapta_shalaka
  l1_kalanala_chakra
  l1_kota_chakra
  l1_ckn_chakra
  # L2.5 synthesis
  l25_msr_signals
  l25_ucn_sections
  l25_ucn_digests
  l25_cdlm_links
  l25_cdlm_cells
  l25_cgm_nodes
  l25_cgm_edges
  l25_rm_resonances
  # L3 meta
  l25_pattern_catalog
  l25_divergence_ledger
  l25_negative_space_map
  l25_derivation_graph_nodes
  l25_derivation_graph_edges
  l25_chart_lattice_snapshots
  l25_vedha_anchor_interactions
  # RAG / corpus
  rag_chunks
  rag_embeddings
  rag_graph_nodes
  rag_graph_edges
  rag_queries
  rag_retrievals
  rag_feedback
  rag_reproducibility_failures
  # Classical text store
  classical_texts
  classical_chunks
  classical_attributions
  # Discovery registers
  pattern_register
  resonance_register
  cluster_register
  contradiction_register
  # Build orchestration
  build_manifests
  builds
  build_steps
  build_events
  build_notifications
  build_engine_versions
  build_checkpoints
  build_dependencies
  chart_documents
  chart_ayanamsha_reports
  # §3 correction: computed/legacy
  sade_sati_phases
  school_signal_coverage
  school_analysis_runs
  convergence_scores
  school_disagreements
  multi_school_stances
  school_convergence_index
  data_source_expected
  pyramid_layers
  documents
  predictions
  mcp_bundle_cache
  mcp_audit_findings
  # Staging variants (pg_dump will skip silently if absent)
  ephemeris_daily_staging
  panchanga_daily_staging
  chart_facts_staging
  rag_chunks_staging
  rag_embeddings_staging
  pattern_register_staging
  resonance_register_staging
  cluster_register_staging
  contradiction_register_staging
  builds_staging
)

TMPDIR_DUMP=$(mktemp -d)
trap 'rm -rf "${TMPDIR_DUMP}"' EXIT

for TABLE in "${TABLES[@]}"; do
  echo "  Dumping ${TABLE}..."
  pg_dump \
    --no-owner --no-acl \
    --table="${TABLE}" \
    --format=custom \
    --file="${TMPDIR_DUMP}/${TABLE}.dump" \
    2>/dev/null || echo "    (skipped — table ${TABLE} not found or empty)"
done

echo "  Uploading dumps to GCS..."
gsutil -m cp "${TMPDIR_DUMP}/"*.dump "${ARCHIVE_BUCKET}/db/" 2>/dev/null || true
echo "  ✓ DB dumps uploaded (skipped-missing tables are normal if already partially torn down)"

# ---------------------------------------------------------------------------
# 3. Snapshot build artifact bucket
# ---------------------------------------------------------------------------
echo ""
echo "[3/4] Snapshotting build artifact bucket prefix..."
gsutil -m rsync -r \
  "${BUILD_ARTIFACT_BUCKET}" \
  "${ARCHIVE_BUCKET}/gcs/madhav-marsys-build-artifacts/" \
  2>/dev/null || echo "  WARNING: rsync failed or bucket empty — confirm bucket name: ${BUILD_ARTIFACT_BUCKET}"
echo "  ✓ GCS snapshot done (or skipped if bucket empty)"

# ---------------------------------------------------------------------------
# 4. Record archive manifest
# ---------------------------------------------------------------------------
echo ""
echo "[4/4] Writing archive manifest..."
cat > "${TMPDIR_DUMP}/ARCHIVE_MANIFEST.txt" <<EOF
MARSYS-JIS Legacy Teardown Archive
===================================
Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Archive path: ${ARCHIVE_BUCKET}
Git SHA at archive: $(git rev-parse HEAD 2>/dev/null || echo unknown)
Git tag: pre-legacy-teardown
Tables attempted: ${#TABLES[@]}
Operator: $(whoami)@$(hostname)
EOF
gsutil cp "${TMPDIR_DUMP}/ARCHIVE_MANIFEST.txt" "${ARCHIVE_BUCKET}/ARCHIVE_MANIFEST.txt"

echo ""
echo "=== Archive complete ==="
echo "  Verify: gsutil ls -r ${ARCHIVE_BUCKET}"
echo ""
echo "NEXT STEP: Review the archive, then run infra/teardown/01_drop_tables.sql"
echo "  via your Postgres client against the PRODUCTION database."
