#!/usr/bin/env bash
# fn-1235-readbacks.sh — the post-apply READ-ONLY readback for migration
# 1235_ka_gochara_staged_candidate_evidence_function.sql (PR #3018, protected-class), as ONE runner (C49).
#
# Proves, after 1235 is applied:
#   * the function exists with the expected signature (p_asset_id text → boolean), owner
#     amjis_app, SECURITY DEFINER, search_path pinned to pg_catalog, pg_temp;
#   * EXECUTE is held by EXACTLY the three intended roles (amjis_app,
#     nirmana_campaign_control_writer, nirmana_evidence_ingress_writer) — never PUBLIC;
#   * no grant option anywhere for a non-owner;
#   * the ledger row is present with the applied file's sha256 (pinned below as SHA_1235,
#     PR #3018 head — a steward-approved change to the migration file updates the pin in
#     the same reviewed change).
#
# Safety pattern (identical to gochara-window-readbacks.sh):
#   * connects ONLY through the libpq environment (PGHOST/PGUSER/… or the caller's sourced
#     env) — never a DSN on argv, and the DSN/environment is never printed;
#   * forces a read-only session (PGOPTIONS += -c default_transaction_read_only=on) and
#     REFUSES to run when the session is not read-only;
#   * records the session IDENTITY into the evidence and refuses (--expect-db) the wrong
#     database;
#   * executes the ONE pinned SQL file only after its sha256 matches PINNED_SHA256_fn_1235_evidence_readback_sql
#     and it carries no backslash-led line (a psql meta-command);
#   * prints 'PASS <id>' / 'STOP <id>' per check; exit 0 = all PASS, 1 = a STOP,
#     2 = a preflight REFUSAL;
#   * writes every raw output under --out plus a sha256 MANIFEST and its OWN sha256 as
#     RUNNER_SHA256;
#   * NEVER issues a write: every statement is SELECT/SHOW and the session is read-only.
set -euo pipefail

OUT=""
EXPECT_DB=""
SQL_FILE="platform/scripts/readbacks/fn_1235_evidence_readback.sql"

usage() {
  echo "usage: $0 --out DIR [--sql-file PATH] [--expect-db NAME]" >&2
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="${2:?--out needs a directory}"; shift ;;
    --sql-file) SQL_FILE="${2:?--sql-file needs a path}"; shift ;;
    --expect-db) EXPECT_DB="${2:?--expect-db needs a database name}"; shift ;;
    *) usage ;;
  esac
  shift
done
[ -n "$OUT" ] || usage

mkdir -p "$OUT"
EVIDENCE_LOG="$OUT/MANIFEST.sha256"
: > "$EVIDENCE_LOG.tmp"
: > "$OUT/.stops"

# The migration file's sha256 as applied (PR #3018 head; the ledger must carry exactly this).
SHA_1235="930902f6af470d3a6cdfd1b707ea23e6e365ad8c464004b9ed2a924194353682"
LEDGER_NAME="1235_ka_gochara_staged_candidate_evidence_function.sql"

# B5: the ONLY SQL file this runner may execute, pinned by sha256.
PINNED_SHA256_fn_1235_evidence_readback_sql="0523e577292020d3ad820f63e4a14e41431f039d1b00be6a9502c115874a76d3"

# Force a read-only session through the environment (never a DSN on argv).
export PGOPTIONS="${PGOPTIONS:+$PGOPTIONS }-c default_transaction_read_only=on"

PSQL=(psql -X -q -t -A -F "$(printf '\t')" -v ON_ERROR_STOP=1)

_evidence() { # <id> <file> — record the sha256 of a raw output
  (cd "$OUT" && shasum -a 256 "$2") >> "$EVIDENCE_LOG.tmp"
}

_pass() { echo "PASS $1 ${2:-}"; }
_stop() { # prints on stderr and records the STOP
  echo "STOP $1 — $2" >&2
  echo "$1" >> "$OUT/.stops"
}

# _verify_pinned <id> <path> — pinned sha256 + no backslash-led line; STOPs and returns 1.
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

run_sql() { # <id> <sql> — read-only SQL, raw output to $OUT/<id>.out; echoes it; STOPs on error.
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

run_file() { # <id> <path> — the PINNED SQL file (its bytes are verified BEFORE it runs).
  local id="$1" file="$2" out="$OUT/$1.out"
  [ -f "$file" ] || { _stop "$id" "SQL file not found: $file (pass --sql-file)"; return 1; }
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

_finalize() { if [ -f "$EVIDENCE_LOG.tmp" ]; then mv "$EVIDENCE_LOG.tmp" "$EVIDENCE_LOG"; fi; }
trap '_finalize' EXIT

shasum -a 256 "$0" | awk '{print $1}' > "$OUT/RUNNER_SHA256"
_evidence RUNNER "RUNNER_SHA256"
echo "PASS RUNNER-sha256 self-check: $(cat "$OUT/RUNNER_SHA256")"

# ── preflight: the session MUST be read-only ────────────────────────────────
ro="$("${PSQL[@]}" -c "SHOW transaction_read_only" 2>/dev/null || true)"
dro="$("${PSQL[@]}" -c "SHOW default_transaction_read_only" 2>/dev/null || true)"
if [ "$ro" != "on" ] || [ "$dro" != "on" ]; then
  echo "REFUSAL: the session is not read-only (transaction_read_only=$ro, default_transaction_read_only=$dro);" \
       "this runner never writes and refuses anything else" >&2
  exit 2
fi
echo "PASS session-read-only transaction_read_only=on default_transaction_read_only=on"

# ── session identity into the evidence; refuse the wrong database ───────────
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

# ── the readback itself ─────────────────────────────────────────────────────
raw="$(run_file FN1235-readback "$SQL_FILE")" || raw=""

_expect_row() { # <label> <expected-rest-of-line> — assert one labeled TSV row is present
  local label="$1" want="$2" id="FN1235-$3"
  if [ -z "$raw" ]; then _stop "$id" "the readback did not run (see FN1235-readback)"; return; fi
  if printf '%s\n' "$raw" | grep -qxF "$label	$want"; then
    _pass "$id" "$label = $want"
  else
    _stop "$id" "expected '$label	$want'; observed: $(printf '%s\n' "$raw" | grep -F "$label	" | tr '\n' ' ' | sed 's/ $//')"
  fi
}

if [ -n "$raw" ]; then
  if printf '%s\n' "$raw" | grep -qxF "function	MISSING"; then
    _stop FN1235-exists "public.ka_gochara_staged_candidate_has_runtime_evidence(text) does not exist — 1235 is not applied here"
  elif ! printf '%s\n' "$raw" | grep -qxF "function	present"; then
    _stop FN1235-exists "the function probe row is absent or unexpected: $(printf '%s\n' "$raw" | head -1)"
  else
    _pass FN1235-exists "the evidence function exists"
  fi
fi

_expect_row signature "p_asset_id text	boolean" signature
_expect_row owner "amjis_app" owner
_expect_row security_definer "t" secdef
_expect_row search_path "search_path=pg_catalog, pg_temp" search-path
_expect_row acl_public_entries "0" acl-no-public
_expect_row acl_non_owner_grant_options "0" acl-no-grant-option
_expect_row ledger "$LEDGER_NAME	$SHA_1235" ledger

# The ACL set must be EXACTLY the three intended EXECUTE grants (the owner's implicit
# entry never appears here: proacl is non-NULL after 1235's explicit grants).
if [ -n "$raw" ] && ! printf '%s\n' "$raw" | grep -qxF "function	MISSING"; then
  want_acl="$(printf 'acl\tamjis_app\tEXECUTE\tf\nacl\tnirmana_campaign_control_writer\tEXECUTE\tf\nacl\tnirmana_evidence_ingress_writer\tEXECUTE\tf\n' | LC_ALL=C sort)"
  got_acl="$(printf '%s\n' "$raw" | grep '^acl	' | LC_ALL=C sort)"
  if [ "$got_acl" = "$want_acl" ]; then
    _pass FN1235-acl-exact "EXECUTE held by exactly amjis_app, nirmana_campaign_control_writer, nirmana_evidence_ingress_writer"
  else
    _stop FN1235-acl-exact "observed acl rows: $(printf '%s' "$got_acl" | tr '\n' ' ')| expected: $(printf '%s' "$want_acl" | tr '\n' ' ')"
  fi
fi

if [ -s "$OUT/.stops" ]; then
  echo "fn-1235-readbacks: $(wc -l < "$OUT/.stops" | tr -d ' ') STOP(s)" >&2
  exit 1
fi
echo "fn-1235-readbacks: all checks PASS"
exit 0
