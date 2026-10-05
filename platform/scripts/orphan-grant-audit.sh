#!/usr/bin/env bash
# orphan-grant-audit.sh — the role_orchestrator follow-through READ-ONLY audit (C51).
#
# Runs the pinned audit SQL and writes its TSV evidence: every NOLOGIN role with no members
# that holds INSERT/UPDATE/DELETE/TRUNCATE on any table in schema public, with table owner
# and grantor. NO changes are proposed and none are made; the output is for the owner to
# judge whether role_orchestrator's leftover grants are a one-off or a pattern.
#
# Safety pattern (identical to gochara-window-readbacks.sh / fn-1235-readbacks.sh):
#   * connects ONLY through the libpq environment — never a DSN on argv, never printed;
#   * forces a read-only session (PGOPTIONS += -c default_transaction_read_only=on) and
#     REFUSES to run when the session is not read-only;
#   * records the session IDENTITY into the evidence and refuses (--expect-db) the wrong
#     database;
#   * executes the ONE pinned SQL file only after its sha256 matches
#     PINNED_SHA256_orphan_dml_grant_audit_sql and it carries no psql meta-command;
#   * exit 0 = the audit ran clean (the row count is a fact for the owner, not a verdict);
#     1 = the audit could not run; 2 = a preflight REFUSAL;
#   * writes the raw TSV under --out plus a sha256 MANIFEST and its OWN sha256 as
#     RUNNER_SHA256;
#   * NEVER issues a write: the audit is one SELECT and the session is read-only.
set -euo pipefail

OUT=""
EXPECT_DB=""
SQL_FILE="platform/scripts/readbacks/orphan_dml_grant_audit.sql"

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

PINNED_SHA256_orphan_dml_grant_audit_sql="dd40255957255c50ecfd530a8d073d256817f8fccfd9763cb380cef74363a7db"

export PGOPTIONS="${PGOPTIONS:+$PGOPTIONS }-c default_transaction_read_only=on"

PSQL=(psql -X -q -t -A -F "$(printf '\t')" -v ON_ERROR_STOP=1)

_evidence() { (cd "$OUT" && shasum -a 256 "$2") >> "$EVIDENCE_LOG.tmp"; }

refuse() { echo "REFUSAL: $1" >&2; exit 2; }
fail() { echo "FAIL: $1" >&2; exit 1; }

# pin + no-meta-command check BEFORE anything is executed
base="$(basename "$SQL_FILE")"
[ -f "$SQL_FILE" ] || fail "SQL file not found: $SQL_FILE (pass --sql-file)"
got="$(shasum -a 256 "$SQL_FILE" | awk '{print $1}')"
[ "$got" = "$PINNED_SHA256_orphan_dml_grant_audit_sql" ] \
  || fail "$base sha256 $got != the pinned $PINNED_SHA256_orphan_dml_grant_audit_sql — refusing a tampered or stale file BEFORE executing it"
grep -q '^\\' "$SQL_FILE" && fail "$base carries a line starting with a backslash (a psql meta-command) — refusing"

shasum -a 256 "$0" | awk '{print $1}' > "$OUT/RUNNER_SHA256"
_evidence RUNNER "RUNNER_SHA256"
echo "PASS RUNNER-sha256 self-check: $(cat "$OUT/RUNNER_SHA256")"

ro="$("${PSQL[@]}" -c "SHOW transaction_read_only" 2>/dev/null || true)"
dro="$("${PSQL[@]}" -c "SHOW default_transaction_read_only" 2>/dev/null || true)"
if [ "$ro" != "on" ] || [ "$dro" != "on" ]; then
  refuse "the session is not read-only (transaction_read_only=$ro, default_transaction_read_only=$dro); this runner never writes and refuses anything else"
fi
echo "PASS session-read-only transaction_read_only=on default_transaction_read_only=on"

"${PSQL[@]}" -c "SELECT current_user, session_user, current_database(), inet_server_addr()::text, inet_server_port(), version()" \
  > "$OUT/SESSION-identity.out" 2>/dev/null || fail "could not record the session identity"
_evidence SESSION "SESSION-identity.out"
echo "PASS SESSION-identity identity recorded to evidence (SESSION-identity.out)"
if [ -n "$EXPECT_DB" ]; then
  db="$("${PSQL[@]}" -c "SELECT current_database()" 2>/dev/null || true)"
  [ "$db" = "$EXPECT_DB" ] \
    || refuse "current_database() is '$db', --expect-db says '$EXPECT_DB' — this evidence would not name the right database"
  echo "PASS SESSION-expect-db current_database()=$db matches --expect-db"
fi

"${PSQL[@]}" -f "$SQL_FILE" > "$OUT/orphan_dml_grants.tsv" 2> "$OUT/orphan_dml_grants.tsv.err" \
  || { _evidence AUDIT "orphan_dml_grants.tsv.err"; fail "psql failed on the audit (see orphan_dml_grants.tsv.err)"; }
rm -f "$OUT/orphan_dml_grants.tsv.err"
LC_ALL=C sort "$OUT/orphan_dml_grants.tsv" > "$OUT/orphan_dml_grants.tsv.sorted"
mv "$OUT/orphan_dml_grants.tsv.sorted" "$OUT/orphan_dml_grants.tsv"
_evidence AUDIT "orphan_dml_grants.tsv"

n="$(wc -l < "$OUT/orphan_dml_grants.tsv" | tr -d ' ')"
echo "PASS AUDIT-complete $n NOLOGIN/memberless role-row(s) with DML grants on public tables — evidence: orphan_dml_grants.tsv (review is the owner's)"
exit 0
