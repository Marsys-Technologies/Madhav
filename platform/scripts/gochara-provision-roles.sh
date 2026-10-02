#!/usr/bin/env bash
# Gochara verifier/sealer ROLE PROVISIONING — one-shot, reviewed (the native's direct ruling #1, 2026-10-02: option A).
# Runbook: 00_ARCHITECTURE/briefs/pravaha/runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md (acts 1, 2a, 2b, 11).
#
# Run ONLY by .github/workflows/gochara-role-provisioning-oneshot.yml (workflow_dispatch, after Codex review), over the
# governed ownership-admin connection. Never `gcloud sql users create` and never the console: both make the new user a
# member of cloudsqlsuperuser; every role here is made with SQL CREATE ROLE and the post-check proves NO membership.
#
# Stages (STAGE):
#   create-roles     act 1 + act 2a: CREATE ROLE gochara_verifier / gochara_sealer (both PASSWORD NULL: they exist, so 1240's
#                    role-guarded grants fire, but neither can authenticate by password); then the verifier's password is
#                    generated HERE, written straight to Secret Manager and set on the role. Refuses if either role exists.
#   sealer-password  act 2b: sets the sealer's password from SEALER_PASSWORD_STAGING (see the runbook, §7.1) — only after the
#                    live-gate proof. ACTIVATION AND ITS POSTCONDITIONS ARE ONE TRANSACTION; anything that goes wrong after the
#                    commit (or an interruption while it is in flight) is COMPENSATED — the password is reset to NULL (and
#                    NOLOGIN restored if the role was NOLOGIN) and the reset is VERIFIED; if that cannot be verified the run
#                    says so loudly (exit 70) and the secrets must NOT be discarded.
#
# THE PASSWORD STATE IS NEVER READ FROM pg_authid (Fable F-R12-3): on Cloud SQL the admin roles are cloudsqlsuperuser members, not superusers, and pg_authid is
#   superuser-only — a predicate that needed it would refuse unconditionally (a fail-closed dead end). Instead the state is (1) RECORDED in a role comment that
#   create-roles writes ('gochara-provision:sealer-password-null') and the activation rewrites ('...-set'), readable by anyone via pg_shdescription, and (2) PROBED by
#   an actual loopback authentication attempt as the sealer, which must FAIL before activation and SUCCEED after it (and fail again after a compensation).
#
# PERMISSION MODEL (act 11 — the workflow identity on the verifier secret ONLY, never project-level): roles/secretmanager.secretVersionManager
#   = secretmanager.versions.{add,get,list,enable,disable,destroy} — NO secretmanager.versions.access (the payload is never readable by this
#   identity). The script uses EXACTLY three Secret Manager verbs: `versions add`, `versions list` (verification) and `versions destroy`
#   (rollback). `roles/secretmanager.secretVersionAdder` alone is NOT sufficient (list and destroy would be denied); the tests run under both models.
#   The binding is TEMPORARY and carries an IAM Condition expiry as a backstop (runbook act 11).
#
# SECRETS: nothing secret is ever echoed, written to a file or uploaded as an artifact. The generated password exists only in a shell
# variable and is piped (stdin) to psql and to gcloud. The admin connection is NEVER passed in argv: it is parsed ONCE into the standard
# libpq environment variables (PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE/PGSSLMODE) of THIS process and inherited by psql — so it is not in
# any process's argument list (it IS in this process's environment, readable only by the same user/root on the runner). No xtrace, ever.
set -Eeuo pipefail
set +x
umask 077

STAGE="${STAGE:?STAGE is required (create-roles | sealer-password)}"
ADMIN_DATABASE_URL="${ADMIN_DATABASE_URL:?ADMIN_DATABASE_URL (the governed ownership-admin connection) is required}"
VERIFIER_ROLE=gochara_verifier
SEALER_ROLE=gochara_sealer
VERIFIER_SECRET="${VERIFIER_SECRET:-gochara-verifier-db-url}"
GCLOUD_PROJECT="${GCLOUD_PROJECT:-madhav-astrology}"
GCLOUD_BIN="${GCLOUD_BIN:-gcloud}"
PSQL_BIN="${PSQL_BIN:-psql}"

CREATED_ROLES=()          # roles created by THIS process — rolled back automatically if anything later fails
CREATED_VERSION=""        # the secret version written by THIS process — destroyed if anything later fails
SEALER_ACTIVATION=0       # 1 from the moment sealer activation is attempted: any non-success exit then COMPENSATES
SEALER_WAS_LOGIN=""       # the sealer's rolcanlogin before activation (the compensation restores it)
COMPLETED=0

fail() { echo "REFUSED: $*" >&2; exit "${2:-3}"; }
note() { echo "$*"; }

# ── 0. the connection: ONE explicit loopback host, nothing that can redirect it, NEVER in argv ───────────────────────────────────────────
for v in PGHOST PGHOSTADDR PGSERVICE PGSERVICEFILE PGPASSFILE PGPASSWORD PGUSER PGDATABASE PGPORT PGSSLMODE; do
  [ -z "${!v:-}" ] || fail "$v is set in the environment: this script derives the whole connection from ADMIN_DATABASE_URL and refuses ambient overrides" 2
done
case "$ADMIN_DATABASE_URL" in
  postgres://*|postgresql://*) ;;
  *) fail "ADMIN_DATABASE_URL must be a postgres:// URL pointing at the loopback Cloud SQL proxy (127.0.0.1 / localhost)" 2 ;;
esac
_rest="${ADMIN_DATABASE_URL#*://}"
_authority="${_rest%%[/?#]*}"
_hostport="${_authority##*@}"
case "$_hostport" in *,*) fail "ADMIN_DATABASE_URL must point at the loopback Cloud SQL proxy: a multi-host URL is refused" 2 ;; esac
case "$_hostport" in
  "["*"]"*) _host="${_hostport%%]*}]" ;;
  *) _host="${_hostport%%:*}" ;;
esac
case "$_host" in
  127.0.0.1|localhost|"[::1]") ;;
  *) fail "ADMIN_DATABASE_URL must point at the loopback Cloud SQL proxy (127.0.0.1 / localhost), not '${_host}'" 2 ;;
esac
case "$_rest" in
  *\?*) case "${_rest#*\?}" in *host=*|*hostaddr=*|*service=*) fail "ADMIN_DATABASE_URL must point at the loopback Cloud SQL proxy: a host/hostaddr/service query option is refused" 2 ;; esac ;;
esac
export ADMIN_DATABASE_URL

# parse ONCE into the libpq environment (the URL is read from this process's ENVIRONMENT by python — never from argv)
_conn_env() {
  python3 -c '
import os, sys
from urllib.parse import urlsplit, unquote, parse_qs
u = urlsplit(os.environ["ADMIN_DATABASE_URL"])
q = parse_qs(u.query)
out = {"PGHOST": u.hostname or "", "PGPORT": str(u.port or 5432), "PGUSER": unquote(u.username or ""), "PGPASSWORD": unquote(u.password or ""),
       "PGDATABASE": unquote(u.path.lstrip("/") or "postgres")}
if "sslmode" in q:
    out["PGSSLMODE"] = q["sslmode"][0]
for k, v in out.items():
    sys.stdout.write(k + "\0" + v + "\0")
'
}
while IFS= read -r -d '' _k && IFS= read -r -d '' _v; do
  export "$_k=$_v"
done < <(_conn_env)
unset ADMIN_DATABASE_URL _rest _authority _hostport _host _k _v          # nothing below can see (or leak) the URL; psql gets its connection from PG*
[ -n "${PGHOST:-}" ] || fail "ADMIN_DATABASE_URL carries no host" 2

psql_admin() { "$PSQL_BIN" -X -q -v ON_ERROR_STOP=1 "$@"; }              # NO connection argument: libpq reads PG* from the environment
q() { psql_admin -t -A -c "$1"; }                                          # read-only fact queries (no secret in them)
MARK_NULL='gochara-provision:sealer-password-null'
MARK_SET='gochara-provision:sealer-password-set'
sealer_marker() { q "SELECT COALESCE(shobj_description(oid, 'pg_authid'), '') FROM pg_roles WHERE rolname = '$SEALER_ROLE'"; }
# can the sealer AUTHENTICATE with this password? (the probe that replaces reading pg_authid; the password goes in the CHILD's environment only, never argv)
login_ok() { PGUSER="$SEALER_ROLE" PGPASSWORD="$1" PGCONNECT_TIMEOUT=10 "$PSQL_BIN" -X -q -t -A -c 'SELECT 1' >/dev/null 2>&1; }

# ── rollback / compensation: runs on EVERY exit path ──────────────────────────────────────────────────────────────────────────────────────
rollback() {
  local rc=$?
  unset PW 2>/dev/null || true             # (SEALER_PASSWORD_STAGING is needed below to VERIFY a compensation by a failed authentication; it is unset last)
  if [ "$COMPLETED" != 1 ]; then
    if [ "$SEALER_ACTIVATION" = 1 ]; then
      # COMPENSATE the activation (idempotent: safe whether or not the ALTER committed): password back to NULL, NOLOGIN restored if it was NOLOGIN, then VERIFY.
      echo "COMPENSATING the sealer activation (exit $rc)..." >&2
      local restore="PASSWORD NULL"
      [ "$SEALER_WAS_LOGIN" = "f" ] && restore="NOLOGIN PASSWORD NULL"
      if psql_admin -c "ALTER ROLE $SEALER_ROLE $restore" >/dev/null 2>&1 \
         && psql_admin -c "COMMENT ON ROLE $SEALER_ROLE IS '$MARK_NULL'" >/dev/null 2>&1 \
         && [ "$(sealer_marker 2>/dev/null)" = "$MARK_NULL" ] \
         && ! login_ok "${SEALER_PASSWORD_STAGING:-}"; then
        echo "compensated and VERIFIED: $SEALER_ROLE can no longer authenticate with the staged password and its recorded state is password-null (login restored to '$SEALER_WAS_LOGIN'). The stored secrets are recovery material until you re-run." >&2
      else
        echo "ROLLBACK INCOMPLETE — THE SEALER MAY BE ACTIVE. Run 'ALTER ROLE $SEALER_ROLE $restore;' by hand and prove the staged password no longer authenticates BEFORE deleting any secret; treat as an incident." >&2
        rc=70
      fi
    fi
    if [ -n "$CREATED_VERSION" ]; then
      if "$GCLOUD_BIN" secrets versions destroy "$CREATED_VERSION" --secret "$VERIFIER_SECRET" --project "$GCLOUD_PROJECT" --quiet >/dev/null 2>&1; then
        echo "rolled back: destroyed secret version $CREATED_VERSION" >&2
      else
        echo "ROLLBACK INCOMPLETE: destroy secret version $CREATED_VERSION by hand (needs secretmanager.versions.destroy: the secretVersionManager binding of act 11)" >&2; rc=70
      fi
    fi
    local r
    for r in ${CREATED_ROLES[@]+"${CREATED_ROLES[@]}"}; do          # (portable to bash 3.2: an empty array is "unbound" under set -u)
      if psql_admin -c "DROP ROLE IF EXISTS $r" >/dev/null 2>&1; then
        echo "rolled back: dropped role $r" >&2
      else
        echo "ROLLBACK INCOMPLETE: DROP OWNED BY $r; DROP ROLE $r; by hand" >&2; rc=70
      fi
    done
  fi
  unset SEALER_PASSWORD_STAGING 2>/dev/null || true
  exit "$rc"
}
trap rollback EXIT
trap 'exit 143' TERM          # a cancelled workflow run must still run the EXIT trap (the compensation)
trap 'exit 130' INT HUP

role_exists() { [ "$(q "SELECT count(*) FROM pg_roles WHERE rolname = '$1'")" = "1" ]; }
CREATE_COMMON="NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS"

# the facts of act 1 / act 2a, printed (no secrets). Any failure here is a failure of the act.
verification_facts() {
  local role="$1" limit="$2"
  note "--- non-secret verification facts for $role ---"
  q "SELECT rolname, rolcanlogin, rolinherit, rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls, rolconnlimit FROM pg_roles WHERE rolname = '$role'"
  local member
  if [ "$(q "SELECT count(*) FROM pg_roles WHERE rolname = 'cloudsqlsuperuser'")" != "1" ]; then
    fail "role cloudsqlsuperuser is absent: this is not a Cloud SQL instance — the membership post-check cannot run" 4
  fi
  member="$(q "SELECT pg_has_role('$role','cloudsqlsuperuser','MEMBER')")"
  note "member_of_cloudsqlsuperuser=$member"
  [ "$member" = "f" ] || fail "$role is a member of cloudsqlsuperuser (post-check failed) — rolling back this run's work" 4
  note "auth_memberships=$(q "SELECT count(*) FROM pg_auth_members WHERE member = (SELECT oid FROM pg_roles WHERE rolname='$role') OR roleid = (SELECT oid FROM pg_roles WHERE rolname='$role')")"
  note "table_grants=$(q "SELECT count(*) FROM information_schema.role_table_grants WHERE grantee = '$role'")"
  note "connection_limit_expected=$limit"
}

create_role() {   # $1 role, $2 connection limit; prints which form was used
  local role="$1" limit="$2" form="LOGIN PASSWORD NULL"
  if ! psql_admin -c "CREATE ROLE $role LOGIN $CREATE_COMMON CONNECTION LIMIT $limit PASSWORD NULL" >/dev/null 2>&1; then   # (the statement carries no secret)
    if [ "$role" = "$SEALER_ROLE" ]; then
      # the runbook's fallback: the role must still EXIST for 1240's role-guarded grants; act 2b then does ALTER ROLE ... LOGIN PASSWORD
      psql_admin -c "CREATE ROLE $role NOLOGIN $CREATE_COMMON CONNECTION LIMIT $limit" >/dev/null
      form="NOLOGIN (fallback: PASSWORD NULL was not accepted)"
    else
      fail "CREATE ROLE $role (LOGIN, PASSWORD NULL) was rejected by the server" 4
    fi
  fi
  CREATED_ROLES+=("$role")
  note "created $role: $form"
}

case "$STAGE" in
  create-roles)
    VERIFIER_CONNECTION_LIMIT="${VERIFIER_CONNECTION_LIMIT:-4}"
    DSN_TAIL="${DSN_TAIL:?DSN_TAIL (the non-secret host/database/params of the verifier DSN, starting with @) is required}"
    # the tail carries NO credential: it must start with @ and must not contain another @ or a userinfo-looking part
    printf '%s' "$DSN_TAIL" | grep -Eq '^@[A-Za-z0-9._/:%=&?-]+$' || fail "DSN_TAIL is not a plain @host/db?params string" 2
    case "${DSN_TAIL#@}" in *@*) fail "DSN_TAIL must not contain a second @ (no credentials)" 2;; esac
    for r in "$VERIFIER_ROLE" "$SEALER_ROLE"; do
      if role_exists "$r"; then fail "role $r already exists — this one-shot refuses (idempotent by refusal); inspect, then roll back by the runbook if it is a failed earlier run"; fi
    done
    create_role "$VERIFIER_ROLE" "$VERIFIER_CONNECTION_LIMIT"
    create_role "$SEALER_ROLE" 2
    verification_facts "$VERIFIER_ROLE" "$VERIFIER_CONNECTION_LIMIT"
    verification_facts "$SEALER_ROLE" 2
    # the sealer's password state is RECORDED (a role comment — readable without pg_authid) and PROBED (an authentication attempt with a random password must FAIL)
    psql_admin -c "COMMENT ON ROLE $SEALER_ROLE IS '$MARK_NULL'" >/dev/null
    note "sealer_recorded_state=$(sealer_marker)"
    if login_ok "$(openssl rand -hex 32)"; then fail "the sealer AUTHENTICATED with a random password: it is not password-protected — rolling back this run's roles" 4; fi
    note "sealer_authentication_with_a_random_password=refused"
    # the verifier's password: generated here, secret store FIRST (so a failure leaves a NULL-password role and an unused version, never an
    # unknown password), then the role. Never echoed; masked as defence in depth.
    PW="$(openssl rand -hex 48)"
    [ "${#PW}" -eq 96 ] || fail "password generation failed" 5
    echo "::add-mask::$PW"
    VERSION_OUT="$(printf '%s' "postgresql://${VERIFIER_ROLE}:${PW}${DSN_TAIL}" \
      | "$GCLOUD_BIN" secrets versions add "$VERIFIER_SECRET" --project "$GCLOUD_PROJECT" --data-file=- --format='value(name)')" \
      || fail "writing the verifier DSN to Secret Manager failed — rolling back this run's roles" 5
    CREATED_VERSION="${VERSION_OUT##*/versions/}"
    [ -n "$CREATED_VERSION" ] || fail "the secret version id was not returned — rolling back this run's roles" 5
    # stderr of the ALTER is discarded: a server error can quote the statement (and so the password)
    printf "ALTER ROLE %s PASSWORD '%s';\n" "$VERIFIER_ROLE" "$PW" \
      | psql_admin -f - >/dev/null 2>&1 \
      || fail "ALTER ROLE PASSWORD failed (server message suppressed: it can quote the statement) — rolling back this run's roles and secret version" 5
    unset PW
    note "verifier password set; DSN written to Secret Manager secret $VERIFIER_SECRET"
    # verification (needs secretmanager.versions.list — the secretVersionManager binding): a failure here is a failure of the act and rolls everything back
    "$GCLOUD_BIN" secrets versions list "$VERIFIER_SECRET" --project "$GCLOUD_PROJECT" --format='value(name,state)' | sed 's/^/secret_version: /' \
      || fail "listing the secret versions failed (needs secretmanager.versions.list) — rolling back this run's roles and secret version" 5
    COMPLETED=1
    note "NEXT: the steward reports acts 1 and 2a (non-secret facts above) to the owner; the sealer stays PASSWORD NULL until act 2b. The act-11 binding is removed and verified after this run reaches ANY terminal state."
    ;;
  sealer-password)
    : "${SEALER_PASSWORD_STAGING:?SEALER_PASSWORD_STAGING (the staged sealer password) is required}"
    role_exists "$SEALER_ROLE" || fail "role $SEALER_ROLE does not exist — run create-roles first"
    [ "${#SEALER_PASSWORD_STAGING}" -ge 64 ] || fail "the staged sealer password is too short" 2
    printf '%s' "$SEALER_PASSWORD_STAGING" | grep -Eq '^[0-9a-f]+$' || fail "the staged sealer password must be hex (no quoting hazard)" 2
    echo "::add-mask::$SEALER_PASSWORD_STAGING"
    SEALER_WAS_LOGIN="$(q "SELECT rolcanlogin FROM pg_roles WHERE rolname = '$SEALER_ROLE'")"
    state="$(sealer_marker)"
    case "$state" in
      "$MARK_NULL") ;;
      "$MARK_SET") fail "the sealer's recorded state is password-SET — refusing to overwrite" ;;
      *) fail "the sealer carries no recorded password-null state ('$state'): it was not created by this one-shot, or its state is unknown — refusing" ;;
    esac
    if login_ok "$SEALER_PASSWORD_STAGING"; then fail "the sealer already authenticates with the staged password — refusing"; fi
    SEALER_ACTIVATION=1       # from here on, any non-success exit (a failed statement, a failed postcondition, a cancelled run) COMPENSATES
    # ONE transaction: the activation AND its postconditions. ALTER ROLE is transactional in PostgreSQL, so a failed postcondition aborts the whole thing and the
    # password is NEVER left set by a failed check. (stderr discarded: a server error can quote the statement.)
    {
      printf "BEGIN;\n"
      printf "ALTER ROLE %s LOGIN PASSWORD '%s';\n" "$SEALER_ROLE" "$SEALER_PASSWORD_STAGING"
      printf "COMMENT ON ROLE %s IS '%s';\n" "$SEALER_ROLE" "$MARK_SET"
      cat <<SQL
DO \$post\$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cloudsqlsuperuser') THEN RAISE EXCEPTION 'postcondition: cloudsqlsuperuser absent (not Cloud SQL)'; END IF;
  IF pg_has_role('$SEALER_ROLE', 'cloudsqlsuperuser', 'MEMBER') THEN RAISE EXCEPTION 'postcondition: sealer is a member of cloudsqlsuperuser'; END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$SEALER_ROLE' AND (rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls OR rolinherit OR NOT rolcanlogin)) THEN
    RAISE EXCEPTION 'postcondition: sealer attributes are not the least-privilege set'; END IF;
  IF EXISTS (SELECT 1 FROM pg_auth_members WHERE member = (SELECT oid FROM pg_roles WHERE rolname = '$SEALER_ROLE') OR roleid = (SELECT oid FROM pg_roles WHERE rolname = '$SEALER_ROLE')) THEN
    RAISE EXCEPTION 'postcondition: sealer has role memberships'; END IF;
END \$post\$;
COMMIT;
SQL
    } | psql_admin -f - >/dev/null 2>&1 \
      || fail "sealer activation or its postconditions failed (server message suppressed) — nothing was committed; compensating anyway" 5
    # the activation must be OBSERVABLE: the sealer can now authenticate with the staged password (otherwise: compensate)
    login_ok "$SEALER_PASSWORD_STAGING" || fail "the sealer cannot authenticate after activation — compensating" 5
    # informational facts AFTER the commit: a failure here still compensates (the trap resets the password and verifies it)
    verification_facts "$SEALER_ROLE" 2
    COMPLETED=1
    note "sealer password set. NEXT: the steward deletes the staging secret (and verifies it is absent) and reports act 2b."
    ;;
  *) fail "unknown STAGE '$STAGE'" 2 ;;
esac
