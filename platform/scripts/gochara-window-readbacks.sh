#!/usr/bin/env bash
# gochara-window-readbacks.sh — the protected-window sitting's READ-ONLY checks as ONE runner (C34).
#
# Source of truth (unchanged by this script): origin/campaign/pravaha
#   00_ARCHITECTURE/briefs/pravaha/runbooks/PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md (rows 2, 3, 7-preconditions, 9)
#   …/runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md §4.1 (W1–W6)
#   …/runbooks/rehearsal/{window_trigger_manifest.sql, window_privilege_readback.sql, registry_1243_readback.sql,
#                        EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv}
#
# Phases:
#   pre-window   rows 2 + 3: 1243 ledger sha, 1206 absent, registry-1243 readback, W3, W1, W2(a capture, b, c),
#                ledger snapshot capture, W6 legacy baseline capture
#   pre-train    row 7 preconditions: gochara_verifier + gochara_sealer exist, W4 sealer CONNECT, 1206 still
#                absent, the 1243 ledger sha re-read
#   post-window  row 9: positive privilege readback (zero rows), amjis_app CREATE on public = false, W2(b/c)
#                recheck, W5 trigger manifest (comm -23 empty; comm -13 reported), boundary guard inventory,
#                W6 post capture + BOTH comm directions against --baseline
#
# Guarantees:
#   * connects ONLY through the libpq environment (PGHOST/PGUSER/… or the caller's sourced env) — never a DSN
#     on argv, and the DSN is never printed;
#   * forces a read-only session (PGOPTIONS += -c default_transaction_read_only=on) and REFUSES to run when the
#     session is not read-only (SHOW transaction_read_only);
#   * prints one line per check: 'PASS <id> …' or 'STOP <id> … <observed vs expected>'; exits 1 on the first
#     STOP (or, with --all, runs every check and exits 1 if any STOPped);
#   * writes every raw output under --out plus a sha256 MANIFEST;
#   * NEVER issues a write: every statement here is SELECT/SHOW, and the session is read-only.
#
# MANUAL (not mechanical, by design — listed in the PR body): the ledger COUNT review (row 2's '919 names +
# later routine + 1243' is a steward read), W2(a)'s 'nothing unexpected' review, W2(d) the code-isolation grep,
# the W6 baseline REVIEW before act 9, and row 7's gh MERGEABLE / deploy.yml byte-identity preconditions.
set -euo pipefail

PHASE=""
OUT=""
SQL_DIR="00_ARCHITECTURE/briefs/pravaha/runbooks/rehearsal"
BASELINE=""
RUN_ALL=0

usage() {
  echo "usage: $0 <pre-window|pre-train|post-window> --out DIR [--sql-dir DIR] [--baseline FILE] [--all]" >&2
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    pre-window|pre-train|post-window) [ -z "$PHASE" ] || usage; PHASE="$1" ;;
    --out) OUT="${2:?--out needs a directory}"; shift ;;
    --sql-dir) SQL_DIR="${2:?--sql-dir needs a directory}"; shift ;;
    --baseline) BASELINE="${2:?--baseline needs a file}"; shift ;;
    --all) RUN_ALL=1 ;;
    *) usage ;;
  esac
  shift
done
[ -n "$PHASE" ] && [ -n "$OUT" ] || usage

mkdir -p "$OUT"
EVIDENCE_LOG="$OUT/MANIFEST.sha256"
: > "$EVIDENCE_LOG.tmp"
: > "$OUT/.stops"

# Force a read-only session through the environment (never a DSN on argv).
export PGOPTIONS="${PGOPTIONS:+$PGOPTIONS }-c default_transaction_read_only=on"

PSQL=(psql -X -q -t -A -F "$(printf '\t')" -v ON_ERROR_STOP=1)

_evidence() { # <id> <file> — record the sha256 of a raw output
  (cd "$OUT" && shasum -a 256 "$2") >> "$EVIDENCE_LOG.tmp"
}

_pass() { echo "PASS $1 ${2:-}"; }
_stop() { # prints on stderr (never captured by a $(run_sql …) substitution) and records the STOP
  echo "STOP $1 — $2" >&2
  echo "$1" >> "$OUT/.stops"
}

# run_sql <id> <sql> — execute read-only SQL, raw output to $OUT/<id>.out; echoes the output; STOPs on psql error.
run_sql() {
  local id="$1" sql="$2" out="$OUT/$1.out"
  if ! "${PSQL[@]}" -c "$sql" > "$out" 2> "$out.err"; then
    _evidence "$id" "$id.out.err"
    _stop "$id" "psql failed (see $id.out.err) — expected a clean read-only result"
    return 1
  fi
  rm -f "$out.err"
  _evidence "$id" "$id.out"
  cat "$out"
  return 0
}

# run_file <id> <path> — same, for a committed SQL file (its text is never edited here).
run_file() {
  local id="$1" file="$2" out="$OUT/$1.out"
  [ -f "$file" ] || { _stop "$id" "SQL file not found: $file (pass --sql-dir)"; return 1; }
  if ! "${PSQL[@]}" -f "$file" > "$out" 2> "$out.err"; then
    _evidence "$id" "$id.out.err"
    _stop "$id" "psql failed on $file (see $id.out.err)"
    return 1
  fi
  rm -f "$out.err"
  _evidence "$id" "$id.out"
  cat "$out"
  return 0
}

_finalize() { # idempotent — also runs from the EXIT trap
  if [ -f "$EVIDENCE_LOG.tmp" ]; then mv "$EVIDENCE_LOG.tmp" "$EVIDENCE_LOG"; fi
}
trap '_finalize' EXIT

# ── preflight: the session MUST be read-only ────────────────────────────────
ro="$("${PSQL[@]}" -c "SHOW transaction_read_only" 2>/dev/null || true)"
dro="$("${PSQL[@]}" -c "SHOW default_transaction_read_only" 2>/dev/null || true)"
if [ "$ro" != "on" ] || [ "$dro" != "on" ]; then
  echo "REFUSAL: the session is not read-only (transaction_read_only=$ro, default_transaction_read_only=$dro);" \
       "this runner never writes and refuses anything else" >&2
  exit 2
fi
echo "PASS session-read-only transaction_read_only=on default_transaction_read_only=on"

SHA_1243="88be3ed59aaa0685d65e9b8b6607f3787c3ae65a5e8fb96d51f09ebe63798321"
CANON_CHART="482012f1-710e-4a25-994a-93821f5871aa"
LEGACY_RELATIONS="'public.kala_gochara_coverage'::regclass, 'public.kala_gochara_publication'::regclass, 'public.kala_gochara_contacts'::regclass, 'public.kala_gochara_windows'::regclass"

check_ledger_1243() { # row 2 release gate: the ROWS-ONLY 1243 is in the ledger with its pinned sha
  local got
  got="$(run_sql R2-ledger-1243 "SELECT filename, sha256 FROM public._migrations_applied WHERE filename = '1243_ka_gochara_inert_registry_rows.sql'")" || return 0
  if [ "$got" = "1243_ka_gochara_inert_registry_rows.sql	$SHA_1243" ]; then
    _pass R2-ledger-1243 "1243 applied, sha256 matches the pinned ROWS-ONLY value"
  else
    _stop R2-ledger-1243 "observed '${got:-<no row>}' vs expected '1243_ka_gochara_inert_registry_rows.sql <TAB> $SHA_1243'"
  fi
}

check_1206_absent() { # row 2: 1206 must NOT be applied before the window
  local n reg
  n="$(run_sql R2-1206-ledger "SELECT count(*) FROM public._migrations_applied WHERE filename LIKE '1206%'")" || return 0
  reg="$(run_sql R2-1206-regclass "SELECT to_regclass('public.ka_gochara_search_inventory_verification')")" || return 0
  if [ "$n" = "0" ] && [ -z "$reg" ]; then
    _pass R2-1206-absent "no 1206 ledger row, the verification table does not exist"
  else
    _stop R2-1206-absent "observed count=$n to_regclass='${reg:-NULL}' vs expected 0 and NULL"
  fi
}

check_ledger_snapshot() { # row 2: freeze the ledger (capture; the COUNT review is steward's — MANUAL)
  run_sql R2-ledger-snapshot "SELECT filename FROM public._migrations_applied ORDER BY 1" > /dev/null || return 0
  local n
  n="$(wc -l < "$OUT/R2-ledger-snapshot.out" | tr -d ' ')"
  _pass R2-ledger-snapshot "ledger snapshot saved ($n names) — the count review against '919 + later routine + 1243' is the steward's"
}

check_registry_1243() { # row 2: registry_1243_readback.sql expectations, asserted one scalar at a time
  run_file R2-registry-1243-file "$SQL_DIR/registry_1243_readback.sql" > /dev/null || return 0
  local fps rows writers deps ev
  fps="$(run_sql R2-1243-fingerprints "SELECT count(*) FROM (SELECT asset_id, md5(row(asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, count_sql, size_sql, target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation, depends_on, scope, is_active, estimated_seconds, asset_type, layer_name, layer_index, provides_apis, health_probe, catalog_status, asset_kind, has_writer, has_substeps, writer_timeout_seconds)::text) AS fingerprint, is_active, has_writer, depends_on FROM public.asset_registry WHERE asset_id IN ('ka_gochara_v4_41_candidate','ka_gochara_v5')) t WHERE (asset_id = 'ka_gochara_v4_41_candidate' AND fingerprint = 'a0f3e234dff2fdd9e4c9a90897e00e13' AND is_active = false AND has_writer = true AND depends_on = '{}') OR (asset_id = 'ka_gochara_v5' AND fingerprint = '49995b52b7c416c8e0ef8f43b1158b57' AND is_active = false AND has_writer = true AND depends_on = '{}')")" || return 0
  rows="$(run_sql R2-1243-rowcount "SELECT count(*) FROM public.asset_registry")" || return 0
  writers="$(run_sql R2-1243-writers "SELECT count(*) FROM public.asset_registry WHERE has_writer")" || return 0
  deps="$(run_sql R2-1243-dependents "SELECT count(*) FROM public.asset_registry WHERE depends_on && ARRAY['ka_gochara_v4_41_candidate','ka_gochara_v5']::text[]")" || return 0
  ev="$(run_sql R2-1243-evidence "SELECT (SELECT count(*) FROM public.asset_provenance_receipts WHERE asset_id IN ('ka_gochara_v4_41_candidate','ka_gochara_v5')), (SELECT count(*) FROM public.build_run_assets WHERE asset_id IN ('ka_gochara_v4_41_candidate','ka_gochara_v5')), (SELECT count(*) FROM public.asset_throughput WHERE asset_id IN ('ka_gochara_v4_41_candidate','ka_gochara_v5'))")" || return 0
  local bad=""
  [ "$fps" = "2" ] || bad="$bad fingerprints=$fps/2;"
  [ "$rows" = "131" ] || bad="$bad registry_rows=$rows/131;"
  [ "$writers" = "124" ] || bad="$bad writers=$writers/124;"
  [ "$deps" = "0" ] || bad="$bad dependents=$deps/0;"
  [ "$ev" = "0	0	0" ] || bad="$bad evidence='$ev'/'0 0 0';"
  if [ -z "$bad" ]; then
    _pass R2-registry-1243 "both inert rows seed-identical, 131 rows / 124 writers, zero dependents, zero evidence"
  else
    _stop R2-registry-1243 "observed vs expected:$bad"
  fi
}

check_w3() { # runbook W3 FIRST: the four legacy relations exist
  local got
  got="$(run_sql W3-legacy-relations "SELECT to_regclass('public.kala_gochara_coverage'), to_regclass('public.kala_gochara_publication'), to_regclass('public.kala_gochara_contacts'), to_regclass('public.kala_gochara_windows')")" || return 0
  if [ "$got" = "kala_gochara_coverage	kala_gochara_publication	kala_gochara_contacts	kala_gochara_windows" ]; then
    _pass W3-legacy-relations "all four legacy relations exist"
  else
    _stop W3-legacy-relations "observed '$got' vs expected all four non-NULL"
  fi
}

check_w1() { # runbook W1: zero governed-generation rows for any other chart, on all four relations
  local rel bad=""
  for rel in kala_gochara_publication kala_gochara_coverage kala_gochara_contacts kala_gochara_windows; do
    local out
    out="$(run_sql "W1-$rel" "SELECT chart_id, generation FROM public.$rel WHERE generation ~ '^([5-9]|[1-9][0-9]+)[.][0-9]+\$' AND chart_id <> '$CANON_CHART'")" || return 0
    [ -z "$out" ] || bad="$bad $rel:$(echo "$out" | wc -l | tr -d ' ')row(s);"
  done
  if [ -z "$bad" ]; then
    _pass W1-governed-rows "zero governed rows for any chart other than the canonical one, on all four relations"
  else
    _stop W1-governed-rows "observed rows vs expected zero:$bad"
  fi
}

W2A_SQL="SELECT c.relname, r.rolname, r.rolsuper, (c.relowner = r.oid) AS is_owner, has_table_privilege(r.oid, c.oid, 'UPDATE') AS tbl_update, has_table_privilege(r.oid, c.oid, 'DELETE') AS tbl_delete, (SELECT string_agg(a.attname, ',' ORDER BY a.attnum) FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped AND has_column_privilege(r.oid, c.oid, a.attnum, 'UPDATE')) AS col_update FROM pg_class c CROSS JOIN pg_roles r WHERE c.oid IN ($LEGACY_RELATIONS) AND r.rolname !~ '^pg_' AND (c.relowner = r.oid OR r.rolsuper OR has_table_privilege(r.oid, c.oid, 'UPDATE') OR has_table_privilege(r.oid, c.oid, 'DELETE') OR EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped AND has_column_privilege(r.oid, c.oid, a.attnum, 'UPDATE'))) ORDER BY 1, 2"

check_w2a() { # runbook W2(a): effective UPDATE/DELETE holders — capture for the steward's review (MANUAL)
  run_sql W2a-holders "$W2A_SQL" > /dev/null || return 0
  _pass W2a-holders "holder listing saved ($(wc -l < "$OUT/W2a-holders.out" | tr -d ' ') rows) — the 'nothing unexpected' review is the steward's"
}

check_w2b() { # runbook W2(b): every (a) holder can EXECUTE ka_gochara_lock_chart (deferred pre-1153)
  local fn
  fn="$(run_sql W2b-lock-fn-exists "SELECT to_regprocedure('public.ka_gochara_lock_chart(uuid)')")" || return 0
  if [ -z "$fn" ]; then
    _pass W2b-lock-execute "ka_gochara_lock_chart does not exist yet (pre-1153) — deferred: run on the mirror, and again post-window"
    return 0
  fi
  local out
  out="$(run_sql W2b-lock-execute "WITH holders AS (SELECT DISTINCT r.oid, r.rolname FROM pg_class c CROSS JOIN pg_roles r WHERE c.oid IN ($LEGACY_RELATIONS) AND r.rolname !~ '^pg_' AND (c.relowner = r.oid OR r.rolsuper OR has_table_privilege(r.oid, c.oid, 'UPDATE') OR has_table_privilege(r.oid, c.oid, 'DELETE') OR EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped AND has_column_privilege(r.oid, c.oid, a.attnum, 'UPDATE')))) SELECT rolname, has_function_privilege(oid, 'public.ka_gochara_lock_chart(uuid)', 'EXECUTE') FROM holders ORDER BY 1")" || return 0
  if [ -z "$out" ]; then
    _pass W2b-lock-execute "no effective UPDATE/DELETE holders — nothing to check"
  elif echo "$out" | awk -F '\t' '$2 != "t" {bad=1} END {exit bad}'; then
    _pass W2b-lock-execute "every holder can EXECUTE ka_gochara_lock_chart"
  else
    _stop W2b-lock-execute "a holder lacks EXECUTE on ka_gochara_lock_chart: $(echo "$out" | awk -F '\t' '$2 != "t"' | tr '\n' ' ')"
  fi
}

check_w2c() { # runbook W2(c): no role-/db-level isolation overrides
  local out
  out="$(run_sql W2c-isolation "SELECT coalesce(r.rolname, '(all roles)'), coalesce(d.datname, '(all databases)'), s.setconfig FROM pg_db_role_setting s LEFT JOIN pg_roles r ON r.oid = s.setrole LEFT JOIN pg_database d ON d.oid = s.setdatabase WHERE array_to_string(s.setconfig, ',') ~* 'isolation'")" || return 0
  if [ -z "$out" ]; then
    _pass W2c-isolation "no role- or database-level isolation settings"
  else
    _stop W2c-isolation "observed $(echo "$out" | wc -l | tr -d ' ') row(s) vs expected zero: $(echo "$out" | head -3 | tr '\n' ' ')"
  fi
}

W6_SQL="SELECT c.relname, t.tgname, t.tgenabled, pn.nspname || '.' || p.proname AS fn, pg_get_triggerdef(t.oid) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_proc p ON p.oid = t.tgfoid JOIN pg_namespace pn ON pn.oid = p.pronamespace WHERE c.relnamespace = 'public'::regnamespace AND c.relname IN ('kala_gochara_coverage','kala_gochara_publication','kala_gochara_contacts','kala_gochara_windows') AND NOT t.tgisinternal ORDER BY 1, 2"

check_w6_capture() { # <file-label> — capture production's actual legacy triggers, sorted LC_ALL=C
  local label="$1"
  run_sql "W6-$label" "$W6_SQL" > /dev/null || return 1
  LC_ALL=C sort "$OUT/W6-$label.out" -o "$OUT/W6-$label.out"
  _evidence "W6-$label" "W6-$label.out"
  return 0
}

check_roles_exist() { # row 7 STOP precondition: both roles exist
  local got
  got="$(run_sql R7-roles-exist "SELECT rolname FROM pg_roles WHERE rolname IN ('gochara_verifier','gochara_sealer') ORDER BY 1")" || return 0
  if [ "$got" = "gochara_sealer
gochara_verifier" ]; then
    _pass R7-roles-exist "gochara_verifier and gochara_sealer both exist"
  else
    _stop R7-roles-exist "observed '$(echo "$got" | tr '\n' ' ')' vs expected both roles (1240's role-guarded grants SKIP an absent role and still COMMIT)"
  fi
}

check_w4() { # runbook W4 / P-CONN: the sealer can CONNECT
  local got
  got="$(run_sql W4-sealer-connect "SELECT has_database_privilege('gochara_sealer', current_database(), 'CONNECT')")" || return 0
  if [ "$got" = "t" ]; then
    _pass W4-sealer-connect "gochara_sealer holds CONNECT on the current database"
  else
    _stop W4-sealer-connect "observed '$got' vs expected t"
  fi
}

check_privilege_readback() { # row 9 STOP: the positive privilege readback prints NOTHING
  local out
  out="$(run_file P9-privilege-readback "$SQL_DIR/window_privilege_readback.sql")" || return 0
  if [ -z "$out" ]; then
    _pass P9-privilege-readback "zero rows — all 92 grants of 1206 §7 / 1240 §7 held"
  else
    _stop P9-privilege-readback "observed $(echo "$out" | wc -l | tr -d ' ') row(s) vs expected zero: $(echo "$out" | head -3 | tr '\n' ' ')"
  fi
}

check_schema_create() { # row 9: amjis_app must NOT hold CREATE on public
  local got
  got="$(run_sql P9-schema-create "SELECT has_schema_privilege('amjis_app','public','CREATE')")" || return 0
  if [ "$got" = "f" ]; then
    _pass P9-schema-create "amjis_app holds no CREATE on public"
  else
    _stop P9-schema-create "observed '$got' vs expected f — the bounded capability was not revoked"
  fi
}

check_w5() { # row 9 W5: production's trigger manifest vs the committed expected one
  run_file W5-prod-manifest "$SQL_DIR/window_trigger_manifest.sql" > /dev/null || return 0
  cp "$OUT/W5-prod-manifest.out" "$OUT/prod_manifest.tsv"
  local trg
  trg="$(grep -c '^TRG' "$OUT/prod_manifest.tsv" || true)"
  if [ "$trg" -eq 0 ]; then
    _stop W5-manifest "the manifest query returned no TRG lines — refusing to compare an empty production output"
    return 0
  fi
  local expected="$SQL_DIR/EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv"
  [ -f "$expected" ] || { _stop W5-manifest "expected manifest not found: $expected (pass --sql-dir)"; return 0; }
  LC_ALL=C sort "$OUT/prod_manifest.tsv" -o "$OUT/prod_manifest.tsv"
  local missing extra
  missing="$(LC_ALL=C comm -23 <(LC_ALL=C sort "$expected") "$OUT/prod_manifest.tsv")"
  extra="$(LC_ALL=C comm -13 <(LC_ALL=C sort "$expected") "$OUT/prod_manifest.tsv")"
  echo "$extra" > "$OUT/W5-production-only.tsv"
  _evidence W5-manifest "W5-production-only.tsv"
  local gi
  gi="$(run_sql W5-guard-inventory "SELECT * FROM public.ka_gochara_boundary_guard_inventory()")" || return 0
  local gi_bad
  gi_bad="$(echo "$gi" | awk -F '\t' 'NF < 4 || $2 != "t" || $3 != "t" || $4 != "t" {print}')"
  if [ -n "$missing" ]; then
    _stop W5-manifest "expected-minus-production is NOT empty (a missing/changed/disabled trigger): $(echo "$missing" | head -3 | tr '\n' ' ')"
  elif [ "$(echo "$gi" | grep -c .)" != "4" ] || [ -n "$gi_bad" ]; then
    _stop W5-guard-inventory "observed '$(echo "$gi" | tr '\n' ' ')' vs expected 4 rows each (t,t,t)"
  else
    _pass W5-manifest "every expected line present, guard inventory 4×(t,t,t); $(grep -c . "$OUT/W5-production-only.tsv" || true) production-only line(s) recorded for the steward"
  fi
}

check_w6_post() { # row 9 W6 BOTH directions against --baseline
  [ -n "$BASELINE" ] || { _stop W6-post "post-window W6 needs --baseline FILE (the pre-window baseline_legacy.tsv)"; return 0; }
  [ -f "$BASELINE" ] || { _stop W6-post "baseline not found: $BASELINE"; return 0; }
  check_w6_capture post || { _stop W6-post "the post-window capture failed"; return 0; }
  local gone added bad_added
  gone="$(LC_ALL=C comm -23 <(LC_ALL=C sort "$BASELINE") "$OUT/W6-post.out")"
  added="$(LC_ALL=C comm -13 <(LC_ALL=C sort "$BASELINE") "$OUT/W6-post.out")"
  echo "$added" > "$OUT/W6-additions.tsv"
  _evidence W6-post "W6-additions.tsv"
  bad_added="$(echo "$added" | grep -v $'\tka_gochara_boundary_' | grep -v '^$' || true)"
  if [ -n "$gone" ]; then
    _stop W6-post "preservation failed — baseline trigger(s) gone or changed: $(echo "$gone" | head -3 | tr '\n' ' ')"
  elif [ -n "$bad_added" ]; then
    _stop W6-post "added trigger(s) that are not 1240's ka_gochara_boundary_*: $(echo "$bad_added" | head -3 | tr '\n' ' ')"
  else
    _pass W6-post "preservation empty both ways; $(echo "$added" | grep -c . || true) addition(s), all ka_gochara_boundary_*"
  fi
}

# run_check <fn> [args…] — run one check; without --all, exit 1 right after the first STOP.
run_check() {
  local rc=0
  "$@" || rc=$?
  if [ "$RUN_ALL" -eq 0 ] && [ -s "$OUT/.stops" ]; then exit 1; fi
  return "$rc"
}

case "$PHASE" in
  pre-window)
    run_check check_ledger_snapshot
    run_check check_ledger_1243
    run_check check_1206_absent
    run_check check_registry_1243
    run_check check_w3
    run_check check_w1
    run_check check_w2a
    run_check check_w2b
    run_check check_w2c
    if run_check check_w6_capture baseline; then
      _pass W6-baseline "legacy baseline captured (baseline_legacy.tsv + sha256) — the steward reviews every row before act 9"
    fi
    ;;
  pre-train)
    run_check check_roles_exist
    run_check check_w4
    run_check check_1206_absent
    run_check check_ledger_1243
    ;;
  post-window)
    run_check check_privilege_readback
    run_check check_schema_create
    run_check check_w2b
    run_check check_w2c
    run_check check_w5
    run_check check_w6_post
    ;;
esac

_finalize
STOPS="$(grep -c . "$OUT/.stops" || true)"
if [ "$STOPS" -gt 0 ]; then
  echo "RESULT: $STOPS STOP(s) — evidence under $OUT" >&2
  exit 1
fi
echo "RESULT: all checks PASS — evidence under $OUT"
