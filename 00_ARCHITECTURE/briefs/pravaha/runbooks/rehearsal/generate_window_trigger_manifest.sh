#!/usr/bin/env bash
# Regenerates EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv from the rehearsal mirror (database gochara_rehearsal on the DISPOSABLE cluster that run_window_rehearsal.sh just built from the
# FINAL window bytes). Run it after EVERY change to any window file, together with the EXPECTED_WINDOW_SHA256.txt regeneration; commit both. NEVER point it at production: the
# production run is the READ-ONLY diff in the runbook (§4.1 W5), against the committed file.
set -euo pipefail
: "${PGPORT:?disposable cluster port}"
HERE="$(cd "$(dirname "$0")" && pwd)"
case "${PGHOST:-127.0.0.1}" in 127.0.0.1|localhost) ;; *) echo "refusing: PGHOST must be loopback"; exit 2;; esac
psql -X -q -t -A -F $'\t' -v ON_ERROR_STOP=1 -h "${PGHOST:-127.0.0.1}" -p "$PGPORT" -U postgres -d gochara_rehearsal -f "$HERE/window_trigger_manifest.sql" > "$HERE/EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv.new"
mv "$HERE/EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv.new" "$HERE/EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv"
echo "wrote $HERE/EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv: $(grep -c '^REL' "$HERE/EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv") relations, $(grep -c '^TRG' "$HERE/EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv") triggers; $(grep -c 'MISSING' "$HERE/EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv") relation(s) MISSING"
