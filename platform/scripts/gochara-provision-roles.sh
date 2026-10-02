#!/usr/bin/env bash
# Gochara verifier/sealer ROLE PROVISIONING — one-shot, reviewed (the native's direct ruling #1, 2026-10-02: option A).
# Runbook: 00_ARCHITECTURE/briefs/pravaha/runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md (acts 1, 2a, 2b).
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
#                    live-gate proof. Refuses unless the sealer exists and cannot yet authenticate.
#
# Secrets: nothing secret is ever echoed, put in argv, written to a file or uploaded as an artifact. The password exists only in
# a shell variable inside this process and is piped (stdin) to psql and to gcloud. No xtrace, ever.
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

CREATED_ROLES=()      # roles created by THIS process — rolled back automatically if anything later fails
CREATED_VERSION=""    # the secret version written by THIS process — destroyed if anything later fails
COMPLETED=0
rollback() {
  # Runs on EVERY exit path (trap): secrets never outlive the process, and a half-finished act leaves nothing behind.
  local rc=$?
  unset PW SEALER_PASSWORD_STAGING 2>/dev/null || true
  if [ "$COMPLETED" != 1 ] && { [ "${#CREATED_ROLES[@]}" -gt 0 ] || [ -n "$CREATED_VERSION" ]; }; then
    echo "ROLLING BACK this run's partial work (exit $rc)..." >&2
    if [ -n "$CREATED_VERSION" ]; then
      "$GCLOUD_BIN" secrets versions destroy "$CREATED_VERSION" --secret "$VERIFIER_SECRET" --project "$GCLOUD_PROJECT" --quiet >/dev/null 2>&1 \
        && echo "rolled back: destroyed secret version $CREATED_VERSION" >&2 || echo "ROLLBACK INCOMPLETE: destroy secret version $CREATED_VERSION by hand" >&2
    fi
    local r
    for r in "${CREATED_ROLES[@]}"; do
      "$PSQL_BIN" "$ADMIN_DATABASE_URL" -X -q -v ON_ERROR_STOP=1 -c "DROP ROLE IF EXISTS $r" >/dev/null 2>&1 \
        && echo "rolled back: dropped role $r" >&2 || echo "ROLLBACK INCOMPLETE: DROP OWNED BY $r; DROP ROLE $r; by hand" >&2
    done
  fi
  exit "$rc"
}
trap rollback EXIT
fail() { echo "REFUSED: $*" >&2; exit "${2:-3}"; }
note() { echo "$*"; }
q() { "$PSQL_BIN" "$ADMIN_DATABASE_URL" -X -q -t -A -v ON_ERROR_STOP=1 -c "$1"; }       # read-only fact queries (no secret in them)

# 0. the connection must be the loopback proxy — never a remote or a validation-instance route
case "$ADMIN_DATABASE_URL" in
  postgres://*@127.0.0.1[:/]*|postgres://*@localhost[:/]*|postgresql://*@127.0.0.1[:/]*|postgresql://*@localhost[:/]*) ;;
  *) fail "ADMIN_DATABASE_URL must point at the loopback Cloud SQL proxy (127.0.0.1 / localhost)" 2 ;;
esac

role_exists() { [ "$(q "SELECT count(*) FROM pg_roles WHERE rolname = '$1'")" = "1" ]; }
CREATE_COMMON="NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS"

# the facts of act 1 / act 2a, printed (no secrets)
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
  [ "$member" = "f" ] || fail "$role is a member of cloudsqlsuperuser (post-check failed) — roll back: DROP OWNED BY $role; DROP ROLE $role;" 4
  note "auth_memberships=$(q "SELECT count(*) FROM pg_auth_members WHERE member = (SELECT oid FROM pg_roles WHERE rolname='$role') OR roleid = (SELECT oid FROM pg_roles WHERE rolname='$role')")"
  note "table_grants=$(q "SELECT count(*) FROM information_schema.role_table_grants WHERE grantee = '$role'")"
  note "connection_limit_expected=$limit"
}

create_role() {   # $1 role, $2 connection limit; prints which form was used
  local role="$1" limit="$2" form="LOGIN PASSWORD NULL"
  if ! "$PSQL_BIN" "$ADMIN_DATABASE_URL" -X -q -v ON_ERROR_STOP=1 \
        -c "CREATE ROLE $role LOGIN $CREATE_COMMON CONNECTION LIMIT $limit PASSWORD NULL" >/dev/null 2>&1; then   # (the statement carries no secret)
    if [ "$role" = "$SEALER_ROLE" ]; then
      # the runbook's fallback: the role must still EXIST for 1240's role-guarded grants; act 2b then does ALTER ROLE ... LOGIN PASSWORD
      "$PSQL_BIN" "$ADMIN_DATABASE_URL" -X -q -v ON_ERROR_STOP=1 \
        -c "CREATE ROLE $role NOLOGIN $CREATE_COMMON CONNECTION LIMIT $limit" >/dev/null
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
    # the sealer cannot authenticate by password at all: rolpassword IS NULL (pg_authid is readable by the admin path; if it is not, say so)
    pw_null="$(q "SELECT rolpassword IS NULL FROM pg_authid WHERE rolname = '$SEALER_ROLE'" 2>/dev/null || echo unreadable)"
    note "sealer_rolpassword_is_null=$pw_null"
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
    # stderr of the ALTER is discarded: a server error message can quote the statement (and so the password)
    printf "ALTER ROLE %s PASSWORD '%s';\n" "$VERIFIER_ROLE" "$PW" \
      | "$PSQL_BIN" "$ADMIN_DATABASE_URL" -X -q -v ON_ERROR_STOP=1 -f - >/dev/null 2>&1 \
      || fail "ALTER ROLE PASSWORD failed (server message suppressed: it can quote the statement) — rolling back this run's roles and secret version" 5
    unset PW
    note "verifier password set; DSN written to Secret Manager secret $VERIFIER_SECRET"
    "$GCLOUD_BIN" secrets versions list "$VERIFIER_SECRET" --project "$GCLOUD_PROJECT" --format='value(name,state)' | sed 's/^/secret_version: /'
    COMPLETED=1
    note "NEXT: the steward reports acts 1 and 2a (non-secret facts above) to the owner; the sealer stays PASSWORD NULL until act 2b."
    ;;
  sealer-password)
    : "${SEALER_PASSWORD_STAGING:?SEALER_PASSWORD_STAGING (the staged sealer password) is required}"
    role_exists "$SEALER_ROLE" || fail "role $SEALER_ROLE does not exist — run create-roles first"
    [ "${#SEALER_PASSWORD_STAGING}" -ge 64 ] || fail "the staged sealer password is too short" 2
    printf '%s' "$SEALER_PASSWORD_STAGING" | grep -Eq '^[0-9a-f]+$' || fail "the staged sealer password must be hex (no quoting hazard)" 2
    echo "::add-mask::$SEALER_PASSWORD_STAGING"
    can_login="$(q "SELECT rolcanlogin FROM pg_roles WHERE rolname = '$SEALER_ROLE'")"
    pw_null="$(q "SELECT rolpassword IS NULL FROM pg_authid WHERE rolname = '$SEALER_ROLE'" 2>/dev/null || echo unreadable)"
    if [ "$can_login" = "t" ] && [ "$pw_null" != "t" ]; then fail "the sealer already has a password — refusing to overwrite"; fi
    printf "ALTER ROLE %s LOGIN PASSWORD '%s';\n" "$SEALER_ROLE" "$SEALER_PASSWORD_STAGING" \
      | "$PSQL_BIN" "$ADMIN_DATABASE_URL" -X -q -v ON_ERROR_STOP=1 -f - >/dev/null 2>&1 \
      || fail "ALTER ROLE for the sealer failed (server message suppressed: it can quote the statement) — nothing was changed; the sealer still cannot authenticate" 5
    verification_facts "$SEALER_ROLE" 2
    COMPLETED=1
    note "sealer password set. NEXT: the steward deletes the staging secret (and verifies it is absent) and reports act 2b."
    ;;
  *) fail "unknown STAGE '$STAGE'" 2 ;;
esac
