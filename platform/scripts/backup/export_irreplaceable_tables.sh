#!/usr/bin/env bash
# export_irreplaceable_tables.sh — G1-E Durability lane.
#
# Scheduled INDEPENDENT logical export of the two irreplaceable table sets
# (conversations, ledger — see irreplaceable_table_sets.sh). "Independent"
# means: this does NOT depend on Cloud SQL's own backup/PITR subsystem at all.
# It is a plain pg_dump against the running database, using whatever
# DATABASE_URL / Cloud SQL Auth Proxy connection the caller already has. If
# Cloud SQL backups or PITR are ever silently misconfigured (the exact GAP-4
# failure this lane exists to close), this export keeps working regardless,
# because it never asks Cloud SQL's backup subsystem for anything.
#
# Usage:
#   export_irreplaceable_tables.sh [--set conversations|ledger|both] [--out DIR]
#
# Env:
#   DATABASE_URL   postgres connection string (required)
#   GCS_BUCKET     if set, the dump is also uploaded there via `gcloud storage
#                  cp` (or `gsutil cp` as a fallback) after a successful local
#                  write. Optional — the local file is always produced first
#                  and is a complete, valid export on its own.
#
# Output: one pg_dump custom-format (-Fc) file per table set, named
#   <set>_<UTC-timestamp>.dump
# in $OUT (default: ./backup_out), plus a .sha256 sidecar for each dump so a
# later restore can verify the file was not truncated/corrupted in transit.
#
# Restore: see restore_irreplaceable_tables.sh (same directory) — it is the
# tested, symmetric counterpart to this script; DO NOT hand-roll pg_restore
# flags at restore time, use that script so the compression/format/owner
# handling always matches what this script produced.
#
# This script only ever reads from the database (pg_dump). It has no code
# path that can enable Cloud SQL PITR, create/clone/delete a Cloud SQL
# instance, or write anything back to the source database. It is safe to run
# against a real database at any time by anyone with read access.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/irreplaceable_table_sets.sh"

SET="both"
OUT="${OUT:-./backup_out}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --set) SET="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set." >&2
  exit 1
fi

mkdir -p "$OUT"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

dump_set() {
  local set_name="$1"
  shift
  local tables=("$@")
  local table_args=()
  for t in "${tables[@]}"; do
    table_args+=(--table="$t")
  done

  local outfile="${OUT}/${set_name}_${TS}.dump"
  echo "==> Exporting set '${set_name}' (${#tables[@]} tables) -> ${outfile}"

  # -Fc: custom format — compressed, and the only format pg_restore can
  # selectively restore/reorder from. --no-owner/--no-privileges: a scratch
  # or DR-target instance will not have the exact same role graph as
  # production; dumping owner/grants would make restore fail on role lookup
  # for no benefit (roles are reprovisioned by G1-C tooling, not by this
  # export). --serializable-deferrable would be nicer but pg_dump already
  # takes one consistent snapshot via its own transaction; no extra flag
  # needed for logical-dump consistency across the listed tables.
  # See restore_irreplaceable_tables.sh's comment on the same pattern: the
  # "${arr[@]+"${arr[@]}"}" form (not the plain "${arr[@]}") avoids bash
  # 3.2's (macOS default) empty-array-under-`set -u` unbound-variable bug.
  # table_args is never actually empty here (the caller always passes a
  # non-empty table list) but the guard costs nothing and keeps this script
  # consistent with its restore counterpart.
  pg_dump "$DATABASE_URL" \
    -Fc \
    --no-owner \
    --no-privileges \
    "${table_args[@]+"${table_args[@]}"}" \
    -f "$outfile"

  # Fail loudly rather than silently producing a PARTIAL export. This check
  # exists because of a verified real defect in the naive approach: pg_dump,
  # given multiple --table flags, does NOT error when some (not all) of the
  # patterns match zero relations — it just dumps whatever it found and
  # exits 0. Confirmed directly against pg_dump 15.17 while building this
  # script (a dump requested against 9 conversations-set tables where only 1
  # existed produced a "successful", non-empty .dump file containing just
  # that 1 table — no error, no non-zero exit, no stderr). A size-only
  # sanity check would have missed this: 1-of-9 tables is not empty, it is
  # silently wrong. So: read the archive's own table of contents back and
  # confirm every table this function was asked to export actually landed
  # in it — the exact "does a real detector back this claim" test from
  # CLAUDE.md §N.8.
  local toc
  toc=$(pg_restore --list "$outfile")
  local missing=()
  local t
  for t in "${tables[@]}"; do
    if ! grep -qE "[[:space:]]public[[:space:]]${t}([[:space:]]|\$)" <<<"$toc"; then
      missing+=("$t")
    fi
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "ERROR: ${outfile} is missing ${#missing[@]} of ${#tables[@]}" \
         "requested tables from set '${set_name}': ${missing[*]}." \
         "pg_dump does not error when a --table pattern matches nothing, so" \
         "this dump silently omitted them rather than failing on its own." \
         "This means either the live schema has dropped/renamed a table" \
         "still listed in irreplaceable_table_sets.sh (update that file), or" \
         "DATABASE_URL points at the wrong database. Refusing to treat this" \
         "as a successful export; the partial .dump file has been left on" \
         "disk for inspection at ${outfile}." >&2
    exit 1
  fi

  local size_bytes
  size_bytes=$(stat -f%z "$outfile" 2>/dev/null || stat -c%s "$outfile")

  shasum -a 256 "$outfile" | awk '{print $1}' > "${outfile}.sha256"
  echo "    ${size_bytes} bytes; sha256 recorded at ${outfile}.sha256"

  if [[ -n "${GCS_BUCKET:-}" ]]; then
    echo "    Uploading to gs://${GCS_BUCKET}/g1e-exports/${set_name}/"
    if command -v gcloud >/dev/null 2>&1; then
      gcloud storage cp "$outfile" "$outfile.sha256" \
        "gs://${GCS_BUCKET}/g1e-exports/${set_name}/"
    elif command -v gsutil >/dev/null 2>&1; then
      gsutil cp "$outfile" "$outfile.sha256" \
        "gs://${GCS_BUCKET}/g1e-exports/${set_name}/"
    else
      echo "    WARNING: GCS_BUCKET set but neither gcloud nor gsutil found" \
           "on PATH — upload skipped, local file retained." >&2
    fi
  fi
}

case "$SET" in
  conversations)
    dump_set conversations "${CONVERSATIONS_TABLES[@]}"
    ;;
  ledger)
    dump_set ledger "${LEDGER_TABLES[@]}"
    ;;
  both)
    dump_set conversations "${CONVERSATIONS_TABLES[@]}"
    dump_set ledger "${LEDGER_TABLES[@]}"
    ;;
  *)
    echo "ERROR: --set must be conversations|ledger|both (got: $SET)" >&2
    exit 2
    ;;
esac

echo "==> Done."
