#!/usr/bin/env bash
# Regenerate the draft SQL + evidence logs from the committed ledgers.  READER-ONLY against production
# (SELECT through the caller-supplied read-only helper) and a DISPOSABLE local PostgreSQL (unix socket)
# that the CALLER starts and stops by its own recorded PID.  Nothing here starts or stops a server.
#
#   regen_all.sh <rq.sh> <snapshot_dir> <pg_socket_dir> <pg_port>
#
# 1. snapshot the tables each asset's draft touches (dump_tables.py)           -> <snapshot_dir>/<asset>/
# 2. transit engine (rules are PR 3049): tools/run_pg_test_draft_engine_curation.py -> drafts/ (SQL, seed patch, evidence)
# 3. other assets: tools/generic_citation_sql.py test <asset> ...                 -> drafts/ (SQL, evidence)
# 4. quote QA of every ledger against the corpus                                  -> prints counts
set -euo pipefail
RQ="$1"; SN="$2"; SOCK="$3"; PORT="$4"
HERE="$(cd "$(dirname "$0")" && pwd)"; CUR="$(dirname "$HERE")"
mkdir -p "$SN"
dump() { python3 "$HERE/dump_tables.py" "$RQ" "$SN/$1" "$2" --registry "$1"; }
dump bg_dignity_reference "bg_dignity_reference,bg_graha_naisargika_friendship,bg_avastha_schemes,bg_motion_state_thresholds,bg_combustion_orbs"
dump bg_reference "reference_planets,reference_signs,reference_houses,reference_aspects,reference_vargas,reference_upagrahas,reference_strength_systems,reference_karakas,reference_constants,reference_glossary,reference_topic_tags"
dump bg_nakshatra "reference_nakshatra,reference_nakshatra_pada,reference_nakshatra_matrix"
dump bg_dasha_systems "brahma_dasha_systems,brahma_ontology@entity_class='dasha_system',reference_dasha_systems"
dump bg_prashna_rules "bg_prashna_lagna_methods,bg_prashna_tajik_yogas,bg_prashna_significators,bg_prashna_fructification_rules,bg_prashna_special_techniques"
python3 "$HERE/dump_chunk_meta.py" "$RQ" "$SN/bg_dasha_systems/chunk_meta.json" "$CUR/assets/bg_dasha_systems_ledger.json"

python3 "$HERE/run_pg_test_draft_engine_curation.py" "$SOCK" "$PORT"
for a in bg_dignity_reference bg_reference bg_nakshatra bg_dasha_systems bg_prashna_rules; do
  python3 "$HERE/generic_citation_sql.py" test "$a" "$CUR/assets/${a}_ledger.json" "$SN/$a" "$SOCK" "$PORT" "$CUR/drafts"
done
python3 "$HERE/qa_ledger_quotes.py" "$RQ" "$CUR"/assets/*_ledger.json || true
