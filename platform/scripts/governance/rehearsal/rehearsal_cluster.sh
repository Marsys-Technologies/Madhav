#!/usr/bin/env bash
# rehearsal_cluster.sh — E5.6 phase 1: the off-production rehearsal PostgreSQL cluster.
#
#   rehearsal_cluster.sh init | start | stop | status | reset --yes | url
#
# A local PostgreSQL 15 cluster run as the CURRENT user, loopback only, port 55432, data dir
# OUTSIDE the repo. It never connects to anything else and holds no production data or
# credentials. Every PostgreSQL command runs under an explicit minimal environment (env -i), so
# PG*/DATABASE_URL variables inherited from the caller can never redirect it.
set -euo pipefail

PG_BIN="${REHEARSAL_PG_BIN:-/opt/homebrew/opt/postgresql@15/bin}"   # prod is 15.x (CI pins 15.18)
REHEARSAL_HOME="/Users/Dev/suvarna/rehearsal"
DATA_DIR="${REHEARSAL_HOME}/pg"
LOG_FILE="${REHEARSAL_HOME}/pg.log"
SOCK_DIR="${REHEARSAL_HOME}/sock"
PORT=55432
DBNAME="rehearsal"
PG_USER="$(id -un)"

# Explicit environment for every postgres tool: nothing inherited (no PGHOST/PGPASSWORD/DATABASE_URL).
pgenv() { env -i PATH="${PG_BIN}:/usr/bin:/bin" HOME="${HOME}" LANG="en_US.UTF-8" ${PGOPTIONS:+PGOPTIONS="$PGOPTIONS"} "$@"; }
psql_local() { PGOPTIONS="-c client_min_messages=warning" pgenv "${PG_BIN}/psql" -h 127.0.0.1 -p "${PORT}" -U "${PG_USER}" -v ON_ERROR_STOP=1 -X -q "$@"; }

die() { echo "rehearsal_cluster: $*" >&2; exit 1; }

require_bins() {
  [ -x "${PG_BIN}/initdb" ] && [ -x "${PG_BIN}/pg_ctl" ] || \
    die "PostgreSQL binaries not found at ${PG_BIN} (install nothing automatically; see README)"
}

is_running() { pgenv "${PG_BIN}/pg_ctl" -D "${DATA_DIR}" status >/dev/null 2>&1; }
is_initialised() { [ -f "${DATA_DIR}/PG_VERSION" ]; }

# Port must be free OR held by our own postmaster; refuse to share it with anything else.
assert_port_ours_or_free() {
  if lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1 && ! is_running; then
    die "port ${PORT} is in use by another process; refusing to start"
  fi
}

cmd_init() {
  require_bins
  mkdir -p "${REHEARSAL_HOME}" "${SOCK_DIR}"
  if is_initialised; then
    echo "init: data dir already initialised at ${DATA_DIR} ($(cat "${DATA_DIR}/PG_VERSION")); nothing done"
  else
    [ ! -e "${DATA_DIR}" ] || [ -z "$(ls -A "${DATA_DIR}" 2>/dev/null)" ] || \
      die "${DATA_DIR} exists, is non-empty and is not a cluster; refusing to touch it"
    pgenv "${PG_BIN}/initdb" -D "${DATA_DIR}" -U "${PG_USER}" -A trust --encoding=UTF8 --locale=en_US.UTF-8 >/dev/null
    cat >> "${DATA_DIR}/postgresql.conf" <<CONF

# --- rehearsal overrides (E5.6) ---
listen_addresses = '127.0.0.1'
port = ${PORT}
unix_socket_directories = '${SOCK_DIR}'
max_connections = 40
shared_buffers = 512MB
fsync = off                 # disposable cluster: speed over durability
synchronous_commit = off
full_page_writes = off
CONF
    # Loopback + owner-only unix socket, password-less. No other rule: nothing remote can match.
    cat > "${DATA_DIR}/pg_hba.conf" <<HBA
local   all   all                 trust
host    all   all   127.0.0.1/32  trust
HBA
    echo "init: cluster created at ${DATA_DIR}"
  fi
  cmd_start
  if [ "$(psql_local -d postgres -Atc "SELECT count(*) FROM pg_database WHERE datname='${DBNAME}'")" = "0" ]; then
    psql_local -d postgres -c "CREATE DATABASE ${DBNAME}"
    echo "init: created database ${DBNAME}"
  else
    echo "init: database ${DBNAME} already exists"
  fi
  # Extensions the repository schema needs on a vanilla server (pgvector, pgcrypto, uuid-ossp, pg_trgm).
  for ext in pgcrypto uuid-ossp vector pg_trgm; do
    psql_local -d "${DBNAME}" -c "CREATE EXTENSION IF NOT EXISTS \"${ext}\""
  done
  echo "init: extensions pgcrypto, uuid-ossp, vector, pg_trgm present in ${DBNAME}"
  # Local stand-ins for roles the repository migrations reference (NOLOGIN, no privileges, no
  # password, cluster-local). They carry none of production's role topology or credentials.
  psql_local -d postgres -c "
    DO \$\$
    DECLARE r text;
    BEGIN
      FOREACH r IN ARRAY ARRAY['amjis_app','data_plane_builder','purna_inquiry_owner','service_role','anon','authenticated'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
          EXECUTE format('CREATE ROLE %I NOLOGIN NOINHERIT', r);
        END IF;
      END LOOP;
    END \$\$;"
  echo "init: local stand-in roles present (amjis_app data_plane_builder purna_inquiry_owner service_role anon authenticated)"
}

cmd_start() {
  require_bins
  is_initialised || die "not initialised; run: $0 init"
  mkdir -p "${SOCK_DIR}"
  if is_running; then echo "start: already running on ${PORT}"; return 0; fi
  assert_port_ours_or_free
  pgenv "${PG_BIN}/pg_ctl" -D "${DATA_DIR}" -l "${LOG_FILE}" -w -t 60 start >/dev/null
  echo "start: running on 127.0.0.1:${PORT}"
}

cmd_stop() {
  require_bins
  if ! is_initialised || ! is_running; then echo "stop: not running"; return 0; fi
  pgenv "${PG_BIN}/pg_ctl" -D "${DATA_DIR}" -m fast -w stop >/dev/null
  echo "stop: stopped"
}

cmd_status() {
  require_bins
  echo "data_dir : ${DATA_DIR}"
  echo "port     : 127.0.0.1:${PORT}"
  echo "binaries : $("${PG_BIN}/postgres" --version)"
  if ! is_initialised; then echo "state    : not initialised"; return 0; fi
  if is_running; then
    echo "state    : running"
    psql_local -d "${DBNAME}" -Atc "SELECT 'database : '||current_database()||'  server_addr='||inet_server_addr()||' port='||inet_server_port()||'  tables='||(SELECT count(*) FROM information_schema.tables WHERE table_schema='public')" 2>/dev/null || echo "database : ${DBNAME} not reachable"
  else
    echo "state    : stopped"
  fi
}

cmd_url() { echo "postgresql://${PG_USER}@127.0.0.1:${PORT}/${DBNAME}"; }

cmd_reset() {
  [ "${1:-}" = "--yes" ] || die "reset destroys ALL rehearsal data; re-run with: $0 reset --yes"
  # The only directory this command will ever delete is the exact rehearsal data dir.
  [ "${DATA_DIR}" = "/Users/Dev/suvarna/rehearsal/pg" ] || die "refusing: unexpected data dir ${DATA_DIR}"
  cmd_stop
  rm -rf "${DATA_DIR}"
  echo "reset: data dir removed"
  cmd_init
}

case "${1:-}" in
  init)   cmd_init ;;
  start)  cmd_start ;;
  stop)   cmd_stop ;;
  status) cmd_status ;;
  url)    cmd_url ;;
  reset)  shift; cmd_reset "${1:-}" ;;
  *) echo "usage: $0 init|start|stop|status|reset --yes|url" >&2; exit 64 ;;
esac
