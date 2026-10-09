#!/usr/bin/env bash
# KĀLA-YANTRA: create role verifier_principal (NOLOGIN, PASSWORD NULL, no memberships) — one-shot, owner-approved 2026-10-08.
# Run ONLY by .github/workflows/kala-verifier-role-oneshot.yml over the governed ownership-admin connection (never
# `gcloud sql users create`: that makes the user a cloudsqlsuperuser member). Refuses if the role exists. Prints only facts.
# The admin connection is parsed once into libpq environment variables of this process; never in argv, never echoed.
set -Eeuo pipefail
set +x
umask 077
ADMIN_DATABASE_URL="${ADMIN_DATABASE_URL:?ADMIN_DATABASE_URL (the governed ownership-admin connection) is required}"
ROLE=verifier_principal
eval "$(python3 - <<'PY'
import os, shlex, urllib.parse as u
p = u.urlparse(os.environ["ADMIN_DATABASE_URL"]); q = dict(u.parse_qsl(p.query))
env = {"PGHOST": q.get("host") or p.hostname or "127.0.0.1", "PGPORT": str(p.port or 5432),
       "PGUSER": u.unquote(p.username or ""), "PGPASSWORD": u.unquote(p.password or ""),
       "PGDATABASE": (p.path or "/").lstrip("/") or "postgres", "PGSSLMODE": q.get("sslmode", "disable")}
print("\n".join(f"export {k}={shlex.quote(v)}" for k, v in env.items()))
PY
)"
unset ADMIN_DATABASE_URL
q() { psql -X -v ON_ERROR_STOP=1 -At -c "$1"; }
exists="$(q "SELECT count(*) FROM pg_roles WHERE rolname = '$ROLE'")"
if [ "${STAGE:-create-role}" = "grant-usage" ]; then
  # The hardened data plane revokes USAGE on schema public from PUBLIC, so the verifier role can hold table grants (1330/1334)
  # yet reach none of them. This stage grants exactly USAGE on schema public to verifier_principal — nothing broader — the
  # same way the data-plane/nirmana ownership preflights grant it to their roles. Idempotent; refuses if the role is absent.
  [ "$exists" = "1" ] || { echo "REFUSED: role $ROLE does not exist (run stage create-role first)"; exit 3; }
  q "GRANT USAGE ON SCHEMA public TO $ROLE" >/dev/null
  facts="$(q "SELECT 'usage=' || has_schema_privilege('$ROLE','public','USAGE') || ' create=' || has_schema_privilege('$ROLE','public','CREATE') || ' canlogin=' || rolcanlogin FROM pg_roles WHERE rolname = '$ROLE'")"
  echo "granted: $ROLE $facts"
  case "$facts" in *"usage=true create=false canlogin=false"*) echo "POSTCONDITIONS OK"; exit 0;; *) echo "POSTCONDITIONS FAILED"; exit 70;; esac
fi
if [ "$exists" != "0" ]; then echo "REFUSED: role $ROLE already exists (nothing changed)"; exit 3; fi
psql -X -v ON_ERROR_STOP=1 -q <<SQL
BEGIN;
CREATE ROLE $ROLE NOLOGIN NOINHERIT NOCREATEDB NOCREATEROLE NOREPLICATION;
COMMENT ON ROLE $ROLE IS 'kala-yantra: independent verifier for the Kāla layer manifest (K0a-3, migrations 1330/1334); NOLOGIN; owner-approved 2026-10-08';
COMMIT;
SQL
facts="$(q "SELECT rolname || ' canlogin=' || rolcanlogin || ' super=' || rolsuper || ' createrole=' || rolcreaterole || ' cloudsqlsuperuser_member=' || pg_has_role(rolname, 'cloudsqlsuperuser', 'MEMBER') FROM pg_roles WHERE rolname = '$ROLE'")"
echo "created: $facts"
case "$facts" in *"canlogin=false super=false createrole=false cloudsqlsuperuser_member=false"*) echo "POSTCONDITIONS OK";; *) echo "POSTCONDITIONS FAILED"; exit 70;; esac
