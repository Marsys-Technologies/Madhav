#!/usr/bin/env bash
# restore_irreplaceable_tables.sh — symmetric counterpart to
# export_irreplaceable_tables.sh. Restores a .dump file produced by that
# script into a target database (a scratch/DR-drill database — never point
# this at production without the explicit clean/merge decision that implies).
#
# Usage:
#   restore_irreplaceable_tables.sh --dump PATH --target-db DATABASE_URL [--clean]
#
# --clean passes --clean --if-exists to pg_restore, dropping+recreating the
# tables in the dump before loading (use for a full restore into an empty or
# throwaway database). Without --clean, pg_restore will fail on tables that
# already exist — the safer default for a target that already has other data.
#
# Verifies the sha256 sidecar before touching the target database, so a
# truncated/corrupted transfer is caught before any DDL runs.

set -euo pipefail

DUMP=""
TARGET_DB=""
CLEAN_FLAGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dump) DUMP="$2"; shift 2 ;;
    --target-db) TARGET_DB="$2"; shift 2 ;;
    --clean) CLEAN_FLAGS=(--clean --if-exists); shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$DUMP" || -z "$TARGET_DB" ]]; then
  echo "Usage: $0 --dump PATH --target-db DATABASE_URL [--clean]" >&2
  exit 2
fi

if [[ ! -f "$DUMP" ]]; then
  echo "ERROR: dump file not found: $DUMP" >&2
  exit 1
fi

if [[ -f "${DUMP}.sha256" ]]; then
  echo "==> Verifying integrity against ${DUMP}.sha256"
  EXPECTED="$(cat "${DUMP}.sha256")"
  ACTUAL="$(shasum -a 256 "$DUMP" | awk '{print $1}')"
  if [[ "$EXPECTED" != "$ACTUAL" ]]; then
    echo "ERROR: checksum mismatch. Expected ${EXPECTED}, got ${ACTUAL}." \
         "This dump is not trustworthy — do not restore it." >&2
    exit 1
  fi
  echo "    OK (sha256 ${ACTUAL})"
else
  echo "WARNING: no .sha256 sidecar found next to ${DUMP} — proceeding" \
       "without integrity verification." >&2
fi

echo "==> Restoring ${DUMP} into target database"
# NOTE: "${CLEAN_FLAGS[@]+"${CLEAN_FLAGS[@]}"}" (not a plain "${CLEAN_FLAGS[@]}")
# is deliberate — under `set -u`, bash 3.2 (macOS's /bin/bash, still the
# default on developer machines and some minimal containers) treats a
# reference to an EMPTY array as an unbound-variable error even though the
# array itself was declared. The +alternate-value form sidesteps that bug on
# 3.2 while still expanding correctly on modern bash. Do not "simplify" this
# back to the plain form.
pg_restore \
  --dbname="$TARGET_DB" \
  --no-owner \
  --no-privileges \
  "${CLEAN_FLAGS[@]+"${CLEAN_FLAGS[@]}"}" \
  "$DUMP"

echo "==> Restore complete. Run the row-count/checksum verification pass" \
     "described in the DR runbook §4 before declaring the drill successful."
