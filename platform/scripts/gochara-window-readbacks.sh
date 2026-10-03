#!/usr/bin/env bash
# gochara-window-readbacks.sh — the protected-window sitting's READ-ONLY checks as ONE runner (C34/C34b).
#
# Source of truth (unchanged by this script): origin/campaign/pravaha
#   00_ARCHITECTURE/briefs/pravaha/runbooks/PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md (rows 2, 3, 7-preconditions, 8, 9)
#   …/runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md §4.1 (W1–W6)
#   …/runbooks/rehearsal/{window_trigger_manifest.sql, window_privilege_readback.sql, registry_1243_readback.sql,
#                        window_preread_refusals.sql, EXPECTED_WINDOW_TRIGGER_MANIFEST.tsv, EXPECTED_WINDOW_SHA256.txt}
#
# Phases:
#   pre-window   W3 FIRST, then rows 2 + 3: ledger snapshot, 1243 ledger sha, 1206 absent, registry-1243 readback,
#                window preread refusals, routine predecessors (<=1240) applied, W1, W2(a capture, b, c),
#                W6 legacy baseline capture (baseline_legacy.tsv + printed sha256)
#   pre-train    row 7 preconditions: both roles exist, W4 sealer CONNECT, 1206 absent, 1243 ledger sha AND the
#                full registry-1243 readback re-run (all three release-gate items re-read at the sitting)
#   pre-dispatch row 8 preconditions: window preread refusals again, 1206 absent, both roles, the ledger diff
#                against the row-2 snapshot (only the five window files may be new, never a 1241_*), 1243 ledger sha
#   post-window  row 9: positive privilege readback (zero rows), amjis_app CREATE on public = false, the five
#                window files recorded exactly once with EXPECTED_WINDOW_SHA256.txt hashes, ka_gochara_* /
#                kala_gochara_* ownership = amjis_app, PUBLIC EXECUTE revoked on ka_gochara_* functions, ledger
#                diff against the row-2 snapshot, W2(b/c) recheck, W2(a) recheck against --w2a-baseline (any NEW
#                holder = STOP), W5 trigger manifest, W6 post vs --baseline (both directions)
#
# Guarantees:
#   * connects ONLY through the libpq environment (PGHOST/PGUSER/… or the caller's sourced env) — never a DSN
#     on argv, and the DSN/environment is never printed;
#   * forces a read-only session (PGOPTIONS += -c default_transaction_read_only=on) and REFUSES to run when the
#     session is not read-only (SHOW transaction_read_only AND SHOW default_transaction_read_only);
#   * records the session IDENTITY (current_user, session_user, current_database(), inet_server_addr(),
#     inet_server_port(), version()) into the evidence, and refuses (--expect-db) the wrong database;
#   * executes NO SQL file it has not pinned: every file under --sql-dir it runs (and the expected-manifest TSV)
#     must sha256-match the PINNED_SHA256_* constants below BEFORE it is executed, and any file with a line
#     starting with a backslash (a psql meta-command) is refused. A steward-approved change to a rehearsal file
#     must update its pin in the same reviewed change (the pins below match origin/campaign/pravaha @ 2026-10-03);
#   * prints one line per check: 'PASS <id> …', 'REVIEW <id> …' or 'STOP <id> … <observed vs expected>';
#   * exit codes: 0 = all PASS · 1 = a STOP (first STOP, or all with --all) · 2 = a preflight REFUSAL ·
#     3 = all checks ran clean but at least one REVIEW needs the steward's acknowledgement;
#   * writes every raw output under --out plus a sha256 MANIFEST;
#   * NEVER issues a write: every statement here is SELECT/SHOW, and the session is read-only.
#
# MANUAL (not mechanical, by design — listed in the PR body): the ledger COUNT review (row 2's '919 names +
# later routine + 1243' is a steward read), W2(a)'s 'nothing unexpected' review, the W6 baseline REVIEW of every
# row before act 9, W2(d) the code-isolation grep, the zero-gap enforce preflight (registry_1243_gap_preflight.py),
# every gh/git check (MERGEABLE, baseRefName/isDraft, deploy.yml selection via the executing test, hashes on main,
# no 1241_* on main, 'gh run list' drain), every gcloud/IAM/workflow action (rows 1, 4–6, 8), and the trigger
# manifest vs the rehearsal mirror (rehearsal, not production).
set -euo pipefail

PHASE=""
OUT=""
SQL_DIR="00_ARCHITECTURE/briefs/pravaha/runbooks/rehearsal"
MIGRATIONS_DIR="platform/migrations"
BASELINE=""
LEDGER_SNAPSHOT=""
W2A_BASELINE=""
EXPECT_DB=""
EXPECT_REGISTRY_ROWS="131"
EXPECT_WRITERS="124"
RUN_ALL=0

usage() {
  echo "usage: $0 <pre-window|pre-train|pre-dispatch|post-window> --out DIR [--sql-dir DIR] [--migrations-dir DIR]" >&2
  echo "          [--baseline FILE] [--ledger-snapshot FILE] [--w2a-baseline FILE] [--expect-db NAME]" >&2
  echo "          [--expect-registry-rows N] [--expect-writers N] [--all]" >&2
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    pre-window|pre-train|pre-dispatch|post-window) [ -z "$PHASE" ] || usage; PHASE="$1" ;;
    --out) OUT="${2:?--out needs a directory}"; shift ;;
    --sql-dir) SQL_DIR="${2:?--sql-dir needs a directory}"; shift ;;
    --migrations-dir) MIGRATIONS_DIR="${2:?--migrations-dir needs a directory}"; shift ;;
    --baseline) BASELINE="${2:?--baseline needs a file}"; shift ;;
    --ledger-snapshot) LEDGER_SNAPSHOT="${2:?--ledger-snapshot needs a file}"; shift ;;
    --w2a-baseline) W2A_BASELINE="${2:?--w2a-baseline needs a file}"; shift ;;
    --expect-db) EXPECT_DB="${2:?--expect-db needs a database name}"; shift ;;
    --expect-registry-rows) EXPECT_REGISTRY_ROWS="${2:?}"; shift ;;
    --expect-writers) EXPECT_WRITERS="${2:?}"; shift ;;
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
: > "$OUT/.reviews"

# Force a read-only session through the environment (never a DSN on argv).
export PGOPTIONS="${PGOPTIONS:+$PGOPTIONS }-c default_transaction_read_only=on"

PSQL=(psql -X -q -t -A -F "$(printf '\t')" -v ON_ERROR_STOP=1)

# B5 — the ONLY SQL files this runner may execute, each pinned by sha256 (origin/campaign/pravaha @ 2026-10-03).
# Referenced indirectly in _verify_pinned via PINNED_SHA256_${base//[.-]/_}.
# shellcheck disable=SC2034
PINNED_SHA256_registry_1243_readback_sql="75e5901895f8d68c7ce23034b7ea4a5c601c35124a24a6b4041f707f614c8b07"
# shellcheck disable=SC2034
PINNED_SHA256_window_privilege_readback_sql="d425136ee91ee76acbfef8b44865d69b7d864dcd1fb80f1e168cb445674113b4"
# shellcheck disable=SC2034
PINNED_SHA256_window_trigger_manifest_sql="3d4df48e5881d580492d2185088eafba523789412bd6a16e574ed4445355a1a5"
# shellcheck disable=SC2034
PINNED_SHA256_window_preread_refusals_sql="73db79463a93f5794fdfe01a3a66accce9b230949b8bea6a926cab7aedc554a0"
# shellcheck disable=SC2034
PINNED_SHA256_EXPECTED_WINDOW_TRIGGER_MANIFEST_tsv="2a00af09f3db783f4975c03ea925baff7cf60be5630d235bffdfd77eac4bd73e"

WINDOW_FILES="1204_gochara_av_qualifier_object_role.sql 1206_gochara_search_inventory_completeness.sql 1232_gochara_search_moon_scope_domain.sql 1233_gochara_p1_period_anchor.sql 1240_gochara_window_verification_gate.sql"

SHA_1243="88be3ed59aaa0685d65e9b8b6607f3787c3ae65a5e8fb96d51f09ebe63798321"
# Row 3: 1302 (revoke role_orchestrator's windows DML) is applied BEFORE the row-2 ledger snapshot,
# so it belongs to the baseline — and the page precondition is its ledger record.
SHA_1302="35af45d0d545f7705f9bd8fd91635f715a2f27c288c83e999a5cd98c7983cb9e"
CANON_CHART="482012f1-710e-4a25-994a-93821f5871aa"
LEGACY_RELATIONS="'public.kala_gochara_coverage'::regclass, 'public.kala_gochara_publication'::regclass, 'public.kala_gochara_contacts'::regclass, 'public.kala_gochara_windows'::regclass"

_evidence() { # <id> <file> — record the sha256 of a raw output
  (cd "$OUT" && shasum -a 256 "$2") >> "$EVIDENCE_LOG.tmp"
}

_pass() { echo "PASS $1 ${2:-}"; }
_stop() { # prints on stderr (never captured by a $(run_sql …) substitution) and records the STOP
  echo "STOP $1 — $2" >&2
  echo "$1" >> "$OUT/.stops"
}
_review() { # a clean check whose output needs the steward's acknowledgement (exit 3 at the end)
  echo "REVIEW $1 — $2"
  echo "$1" >> "$OUT/.reviews"
}

# _verify_pinned <id> <path> — B5: pinned sha256 + no backslash-led line; STOPs and returns 1 on a violation.
_verify_pinned() {
  local id="$1" file="$2" base var pinned got
  base="$(basename "$file")"
  var="PINNED_SHA256_${base//[.-]/_}"
  pinned="${!var:-}"
  if [ -z "$pinned" ]; then
    _stop "$id" "no pinned sha256 for $base — refusing to execute an unpinned SQL file"
    return 1
  fi
  got="$(shasum -a 256 "$file" | awk '{print $1}')"
  if [ "$got" != "$pinned" ]; then
    _stop "$id" "$base sha256 $got != the pinned $pinned — refusing a tampered or stale file BEFORE executing it"
    return 1
  fi
  if grep -q '^\\' "$file"; then
    _stop "$id" "$base carries a line starting with a backslash (a psql meta-command) — refusing"
    return 1
  fi
  return 0
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

# run_file <id> <path> — same, for a PINNED SQL file (its bytes are verified BEFORE it is executed).
run_file() {
  local id="$1" file="$2" out="$OUT/$1.out"
  [ -f "$file" ] || { _stop "$id" "SQL file not found: $file (pass --sql-dir)"; return 1; }
  _verify_pinned "$id" "$file" || return 1
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

# ── B6: record the session identity into the evidence; refuse the wrong database ──
run_sql SESSION-identity "SELECT current_user, session_user, current_database(), inet_server_addr()::text, inet_server_port(), version()" > /dev/null
echo "PASS SESSION-identity identity recorded to evidence (SESSION-identity.out)"
if [ -n "$EXPECT_DB" ]; then
  db="$("${PSQL[@]}" -c "SELECT current_database()" 2>/dev/null || true)"
  if [ "$db" != "$EXPECT_DB" ]; then
    echo "REFUSAL: current_database() is '$db', --expect-db says '$EXPECT_DB' — this evidence would not name the right database" >&2
    exit 2
  fi
  echo "PASS SESSION-expect-db current_database()=$db matches --expect-db"
fi

check_w3() { # runbook W3 FIRST: the four legacy relations exist
  local got
  got="$(run_sql W3-legacy-relations "SELECT to_regclass('public.kala_gochara_coverage'), to_regclass('public.kala_gochara_publication'), to_regclass('public.kala_gochara_contacts'), to_regclass('public.kala_gochara_windows')")" || return 0
  if [ "$got" = "kala_gochara_coverage	kala_gochara_publication	kala_gochara_contacts	kala_gochara_windows" ]; then
    _pass W3-legacy-relations "all four legacy relations exist"
  else
    _stop W3-legacy-relations "observed '$got' vs expected all four non-NULL"
  fi
}

check_ledger_snapshot() { # row 2: freeze the ledger (capture; the COUNT review is steward's — MANUAL)
  run_sql R2-ledger-snapshot "SELECT filename FROM public._migrations_applied ORDER BY 1" > /dev/null || return 0
  local n
  n="$(wc -l < "$OUT/R2-ledger-snapshot.out" | tr -d ' ')"
  _pass R2-ledger-snapshot "ledger snapshot saved ($n names) — the count review against '919 + later routine + 1243' is the steward's"
}

check_ledger_1243() { # row 2 release gate: the ROWS-ONLY 1243 is in the ledger with its pinned sha
  local got
  got="$(run_sql R2-ledger-1243 "SELECT filename, sha256 FROM public._migrations_applied WHERE filename = '1243_ka_gochara_inert_registry_rows.sql'")" || return 0
  if [ "$got" = "1243_ka_gochara_inert_registry_rows.sql	$SHA_1243" ]; then
    _pass R2-ledger-1243 "1243 applied, sha256 matches the pinned ROWS-ONLY value"
  else
    _stop R2-ledger-1243 "observed '${got:-<no row>}' vs expected '1243_ka_gochara_inert_registry_rows.sql <TAB> $SHA_1243'"
  fi
}

check_revoke_1302() { # row 3 page precondition: the revoke migration is recorded in the ledger (pre-window, pre-train, pre-dispatch)
  local got
  got="$(run_sql R3-revoke-1302 "SELECT filename, sha256 FROM public._migrations_applied WHERE filename = '1302_revoke_role_orchestrator_windows_dml.sql'")" || return 0
  if [ "$got" = "1302_revoke_role_orchestrator_windows_dml.sql	$SHA_1302" ]; then
    _pass R3-revoke-1302 "1302 applied, sha256 matches the pinned value"
  else
    _stop R3-revoke-1302 "observed '${got:-<no row>}' vs expected '1302_revoke_role_orchestrator_windows_dml.sql <TAB> $SHA_1302'"
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
  [ "$rows" = "$EXPECT_REGISTRY_ROWS" ] || bad="$bad registry_rows=$rows/$EXPECT_REGISTRY_ROWS;"
  [ "$writers" = "$EXPECT_WRITERS" ] || bad="$bad writers=$writers/$EXPECT_WRITERS;"
  [ "$deps" = "0" ] || bad="$bad dependents=$deps/0;"
  [ "$ev" = "0	0	0" ] || bad="$bad evidence='$ev'/'0 0 0';"
  if [ -z "$bad" ]; then
    _pass R2-registry-1243 "both inert rows seed-identical, $EXPECT_REGISTRY_ROWS rows / $EXPECT_WRITERS writers (expectations in use: --expect-registry-rows $EXPECT_REGISTRY_ROWS --expect-writers $EXPECT_WRITERS), zero dependents, zero evidence"
  else
    _stop R2-registry-1243 "observed vs expected:$bad"
  fi
}

PREREAD_EXPECTED="$(printf 't\n0\n0\n1\tt\tt\tt\n0\n0')"
check_preread_refusals() { # B1 (rows 2 + 8): the window files' OWN forward refusal pre-reads, each scalar asserted
  local got
  got="$(run_file R-preread-refusals "$SQL_DIR/window_preread_refusals.sql")" || return 0
  if [ "$got" = "$PREREAD_EXPECTED" ]; then
    _pass R-preread-refusals "every window file's own forward refusal pre-read is clear (t | 0 | 0 | 1,t,t,t | 0 | 0)"
  else
    _stop R-preread-refusals "observed '$(echo "$got" | tr '\n' ' ')' vs expected 't 0 0 1<t>t<t>t 0 0' — a window file WOULD REFUSE at apply"
  fi
}

check_routine_predecessors() { # B2 (row 2): every repo migration numbered <= 1240 that is not a window file is applied
  [ -d "$MIGRATIONS_DIR" ] || { _stop R2-routine-predecessors "migrations dir not found: $MIGRATIONS_DIR (pass --migrations-dir)"; return 0; }
  local ledger f base n missing=""
  ledger="$(run_sql R2-predecessors-ledger "SELECT filename FROM public._migrations_applied")" || return 0
  for f in "$MIGRATIONS_DIR"/[0-9][0-9][0-9][0-9]_*.sql; do
    [ -e "$f" ] || continue
    base="$(basename "$f")"
    n="${base%%_*}"
    [ "$((10#$n))" -le 1240 ] || continue
    case "$base" in 1204_*|1206_*|1232_*|1233_*|1240_*) continue ;; esac
    echo "$ledger" | grep -qxF "$base" || missing="$missing $base"
  done
  if [ -z "$missing" ]; then
    _pass R2-routine-predecessors "every routine migration numbered <= 1240 (the five window files excluded) is recorded applied"
  else
    _stop R2-routine-predecessors "repo migration(s) numbered <= 1240 missing from _migrations_applied:$missing"
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

check_w2a_recheck() { # B4 (row 9): re-capture and diff against the pre-window capture; any NEW holder = STOP
  [ -n "$W2A_BASELINE" ] || { _stop P9-w2a-recheck "needs --w2a-baseline FILE (the pre-window W2(a) capture)"; return 0; }
  [ -f "$W2A_BASELINE" ] || { _stop P9-w2a-recheck "baseline not found: $W2A_BASELINE"; return 0; }
  run_sql W2a-recheck "$W2A_SQL" > /dev/null || return 0
  LC_ALL=C sort "$OUT/W2a-recheck.out" -o "$OUT/W2a-recheck.out"
  _evidence W2a-recheck "W2a-recheck.out"
  local new
  new="$(LC_ALL=C comm -13 <(LC_ALL=C sort "$W2A_BASELINE") "$OUT/W2a-recheck.out")"
  if [ -n "$new" ]; then
    _stop P9-w2a-recheck "NEW effective UPDATE/DELETE holder(s) since the pre-window capture: $(echo "$new" | head -3 | tr '\n' ' ')"
  else
    _pass P9-w2a-recheck "no new UPDATE/DELETE holder since the pre-window capture"
  fi
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
    return 0
  fi
  if echo "$out" | awk -F '\t' '$2 != "t" {bad=1} END {exit bad}'; then
    _pass W2b-lock-execute "every holder can EXECUTE ka_gochara_lock_chart"
    return 0
  fi
  _stop W2b-lock-execute "a holder lacks EXECUTE on ka_gochara_lock_chart: $(echo "$out" | awk -F '\t' '$2 != "t"' | tr '\n' ' ')— always a STOP (there is no dormant-holder exception)"
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

check_window_files_ledger() { # B3a (row 9): the five window files recorded exactly once, sha256 as expected
  local expected_sha_file="$SQL_DIR/EXPECTED_WINDOW_SHA256.txt"
  [ -f "$expected_sha_file" ] || { _stop P9-window-files-ledger "expected sha file not found: $expected_sha_file (pass --sql-dir)"; return 0; }
  local got exp gots
  got="$(run_sql P9-window-files-ledger "SELECT filename, sha256 FROM public._migrations_applied WHERE filename IN ('1204_gochara_av_qualifier_object_role.sql','1206_gochara_search_inventory_completeness.sql','1232_gochara_search_moon_scope_domain.sql','1233_gochara_p1_period_anchor.sql','1240_gochara_window_verification_gate.sql')")" || return 0
  exp="$(awk -v names="$WINDOW_FILES" 'BEGIN { n = split(names, a, " "); for (i = 1; i <= n; i++) want[a[i]] = 1 } want[$2] { print $2 "\t" $1 }' "$expected_sha_file" | LC_ALL=C sort)"
  gots="$(echo "$got" | LC_ALL=C sort)"
  if [ "$gots" = "$exp" ] && [ "$(echo "$gots" | grep -c .)" = "5" ]; then
    _pass P9-window-files-ledger "all five window files recorded exactly once, sha256 matching EXPECTED_WINDOW_SHA256.txt"
  else
    _stop P9-window-files-ledger "observed '$(echo "$gots" | tr '\n' ' ')' vs expected '$(echo "$exp" | tr '\n' ' ')'"
  fi
}

check_ownership() { # B3b (row 9): every ka_gochara_*/kala_gochara_* relation and function is owned by amjis_app
  local out
  out="$(run_sql P9-ka-gochara-ownership "SELECT 'relation' AS kind, c.relname, pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname ~ '^ka(la)?_gochara_' AND pg_get_userbyid(c.relowner) <> 'amjis_app' UNION ALL SELECT 'function', p.proname, pg_get_userbyid(p.proowner) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public' AND p.proname ~ '^ka_gochara_' AND pg_get_userbyid(p.proowner) <> 'amjis_app' ORDER BY 1, 2")" || return 0
  if [ -z "$out" ]; then
    _pass P9-ka-gochara-ownership "every ka_gochara_*/kala_gochara_* relation and function is owned by amjis_app"
  else
    _stop P9-ka-gochara-ownership "observed $(echo "$out" | wc -l | tr -d ' ') object(s) not owned by amjis_app: $(echo "$out" | head -3 | tr '\n' ' ')"
  fi
}

check_public_execute() { # B3c (row 9): PUBLIC EXECUTE revoked on every ka_gochara_* function
  local out
  out="$(run_sql P9-public-execute "SELECT p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public' AND p.proname ~ '^ka_gochara_' AND has_function_privilege('PUBLIC', p.oid, 'EXECUTE') ORDER BY 1")" || return 0
  if [ -z "$out" ]; then
    _pass P9-public-execute "PUBLIC holds EXECUTE on no ka_gochara_* function"
  else
    _stop P9-public-execute "PUBLIC still holds EXECUTE on: $(echo "$out" | tr '\n' ' ')"
  fi
}

check_ledger_diff() { # B3d (rows 8 + 9) <id>: new ledger entries vs the row-2 snapshot = ONLY the five window files
  local id="$1"
  [ -n "$LEDGER_SNAPSHOT" ] || { _stop "$id" "needs --ledger-snapshot FILE (the row-2 ledger snapshot)"; return 0; }
  [ -f "$LEDGER_SNAPSHOT" ] || { _stop "$id" "snapshot not found: $LEDGER_SNAPSHOT"; return 0; }
  run_sql "$id-current" "SELECT filename FROM public._migrations_applied ORDER BY 1" > /dev/null || return 0
  local new bad
  new="$(LC_ALL=C comm -13 <(LC_ALL=C sort "$LEDGER_SNAPSHOT") <(LC_ALL=C sort "$OUT/$id-current.out"))"
  echo "$new" > "$OUT/$id-new-entries.tsv"
  _evidence "$id" "$id-new-entries.tsv"
  bad="$(echo "$new" | grep -Ev '^(1204_gochara_av_qualifier_object_role|1206_gochara_search_inventory_completeness|1232_gochara_search_moon_scope_domain|1233_gochara_p1_period_anchor|1240_gochara_window_verification_gate)[.]sql$' | grep . || true)"
  if [ -n "$bad" ]; then
    _stop "$id" "ledger entries since the row-2 snapshot that are NOT one of the five window files (a 1241_* or a protected file would appear here): $(echo "$bad" | tr '\n' ' ')"
  else
    _pass "$id" "every new ledger entry since the row-2 snapshot is one of the five window files ($(echo "$new" | grep -c . || true) new)"
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
  _verify_pinned W5-manifest "$expected" || return 0
  LC_ALL=C sort "$OUT/prod_manifest.tsv" -o "$OUT/prod_manifest.tsv"
  local missing extra
  missing="$(LC_ALL=C comm -23 <(LC_ALL=C sort "$expected") "$OUT/prod_manifest.tsv")"
  extra="$(LC_ALL=C comm -13 <(LC_ALL=C sort "$expected") "$OUT/prod_manifest.tsv")"
  echo "$extra" > "$OUT/W5-production-only.tsv"
  _evidence W5-manifest "W5-production-only.tsv"
  local gi gi_bad
  gi="$(run_sql W5-guard-inventory "SELECT * FROM public.ka_gochara_boundary_guard_inventory()")" || return 0
  gi_bad="$(echo "$gi" | awk -F '\t' 'NF < 4 || $2 != "t" || $3 != "t" || $4 != "t" {print}')"
  if [ -n "$missing" ]; then
    _stop W5-manifest "expected-minus-production is NOT empty (a missing/changed/disabled trigger): $(echo "$missing" | head -3 | tr '\n' ' ')"
  elif [ "$(echo "$gi" | grep -c .)" != "4" ] || [ -n "$gi_bad" ]; then
    _stop W5-guard-inventory "observed '$(echo "$gi" | tr '\n' ' ')' vs expected 4 rows each (t,t,t)"
  elif [ -n "$extra" ]; then
    _review W5-production-only "$(echo "$extra" | grep -c .) production-only line(s) — each must match a baseline row or be explained by the steward (full list in W5-production-only.tsv): $(echo "$extra" | head -5 | tr '\n' ' ')"
  else
    _pass W5-manifest "every expected line present, guard inventory 4×(t,t,t); 0 production-only line(s)"
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
  elif [ -n "$added" ]; then
    _review W6-additions "$(echo "$added" | grep -c .) addition(s), all ka_gochara_boundary_* — the steward acknowledges each (full list in W6-additions.tsv): $(echo "$added" | head -5 | tr '\n' ' ')"
  else
    _pass W6-post "preservation empty both ways; 0 addition(s)"
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
    run_check check_w3                        # M6: W3 FIRST, as the runbook says
    run_check check_ledger_snapshot
    run_check check_ledger_1243
    run_check check_revoke_1302               # row 3 page precondition
    run_check check_1206_absent
    run_check check_registry_1243
    run_check check_preread_refusals          # B1
    run_check check_routine_predecessors      # B2
    run_check check_w1
    run_check check_w2a
    run_check check_w2b
    run_check check_w2c
    if run_check check_w6_capture baseline; then
      cp "$OUT/W6-baseline.out" "$OUT/baseline_legacy.tsv"          # M4: named as the checklist names it
      _evidence W6-baseline "baseline_legacy.tsv"
      _pass W6-baseline "legacy baseline captured: $(cd "$OUT" && shasum -a 256 baseline_legacy.tsv) — the steward reviews every row before act 9"
    fi
    ;;
  pre-train)
    run_check check_roles_exist
    run_check check_w4
    run_check check_1206_absent
    run_check check_ledger_1243
    run_check check_revoke_1302               # row 3 page precondition
    run_check check_registry_1243             # M1: all three release-gate items re-read at the sitting
    ;;
  pre-dispatch)                               # M7: row 8 preconditions
    run_check check_preread_refusals
    run_check check_1206_absent
    run_check check_roles_exist
    run_check check_ledger_diff R8-ledger-diff
    run_check check_ledger_1243
    run_check check_revoke_1302               # row 3 page precondition
    ;;
  post-window)
    run_check check_privilege_readback
    run_check check_schema_create
    run_check check_window_files_ledger       # B3a
    run_check check_ownership                 # B3b
    run_check check_public_execute            # B3c
    run_check check_ledger_diff P9-ledger-diff # B3d
    run_check check_w2b
    run_check check_w2c
    run_check check_w2a_recheck               # B4
    run_check check_w5
    run_check check_w6_post
    ;;
esac

_finalize
STOPS="$(grep -c . "$OUT/.stops" || true)"
REVIEWS="$(grep -c . "$OUT/.reviews" || true)"
if [ "$STOPS" -gt 0 ]; then
  echo "RESULT: $STOPS STOP(s) — evidence under $OUT" >&2
  exit 1
fi
if [ "$REVIEWS" -gt 0 ]; then
  echo "RESULT: checks PASS with $REVIEWS REVIEW(s) needing the steward's acknowledgement — evidence under $OUT"
  exit 3
fi
echo "RESULT: all checks PASS — evidence under $OUT"
