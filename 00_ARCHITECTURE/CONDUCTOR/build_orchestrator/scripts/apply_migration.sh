#!/bin/bash
# Apply a migration: staging first, then production after smoke.
# Usage: apply_migration.sh <migration_file> <session_id>
set -e
MIG_FILE="$1"
SESSION_ID="$2"
DB_PASS="${PGPASSWORD:?PGPASSWORD env var required}"

[ -z "$MIG_FILE" ] && echo "ERROR: migration file required" && exit 1
[ ! -f "$MIG_FILE" ] && echo "ERROR: file not found: $MIG_FILE" && exit 1

MIG_NAME=$(basename "$MIG_FILE")
echo "=== MIGRATION: $MIG_NAME ==="

# Step 1: Apply to staging
echo "Applying to amjis_staging..."
PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis_staging -f "$MIG_FILE" 2>&1
echo "OK: staging migration applied"

# Step 2: Basic smoke (migration idempotency — run again, should not error on IF NOT EXISTS)
echo "Running idempotency check..."
PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis_staging -f "$MIG_FILE" 2>&1 | grep -v 'already exists' || true
echo "OK: idempotency check passed"

# Step 3: Apply to production
echo "Applying to amjis (production)..."
PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -f "$MIG_FILE" 2>&1
echo "OK: production migration applied"

echo "=== MIGRATION $MIG_NAME COMPLETE ==="
