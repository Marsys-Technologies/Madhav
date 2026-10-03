#!/usr/bin/env bash
# rehearsal_cluster.sh — E5.6 phase 1: the off-production rehearsal PostgreSQL cluster.
#
#   rehearsal_cluster.sh init | start | stop | status | reset --yes | url
#
# A local PostgreSQL 15 cluster run as the CURRENT user, loopback only (127.0.0.1:55432), data dir
# OUTSIDE the repo. It never connects to anything else and holds no production data or credentials.
#
# Hygiene: every PostgreSQL tool runs under `env -i` with an explicit environment and a PRIVATE EMPTY
# HOME (PATH, HOME, LANG, PGPASSFILE=<empty-home>/.no-pgpass, PGSERVICEFILE=<empty-home>/.no-pg-service; psql alone also gets
# PGOPTIONS). Nothing is inherited, so PG*/DATABASE_URL in the caller's shell cannot redirect a command.
#
# Access control — the truth: the unix socket is mode 0700 (owner only, no group), but TCP
# 127.0.0.1/32 is `trust`: ANY local process of ANY local user can connect as the superuser (`Dev`),
# and a superuser can run programs as Dev (COPY ... PROGRAM). Accepted residual for a disposable
# cluster holding no production data and no secrets; do not run it on a shared machine.
set -euo pipefail

PG_BIN="${REHEARSAL_PG_BIN:-/opt/homebrew/opt/postgresql@15/bin}"   # prod is 15.x (CI pins 15.18)
REHEARSAL_HOME="/Users/Dev/suvarna/rehearsal"
# Test-only sandbox: honoured only for a path under the system temp areas; lets the unit tests run
# this script against stub binaries without ever touching the real cluster directory.
if [ -n "${REHEARSAL_TEST_SANDBOX:-}" ]; then
  case "${REHEARSAL_TEST_SANDBOX}" in
    /private/tmp/*|/private/var/folders/*|/tmp/*) REHEARSAL_HOME="${REHEARSAL_TEST_SANDBOX}" ;;
    *) echo "rehearsal_cluster: REHEARSAL_TEST_SANDBOX must be under /private/tmp or /private/var/folders" >&2; exit 1 ;;
  esac
fi
DATA_DIR="${REHEARSAL_HOME}/pg"
LOG_FILE="${REHEARSAL_HOME}/pg.log"
SOCK_DIR="${REHEARSAL_HOME}/sock"
PORT=55432
DBNAME="rehearsal"
PG_USER="$(id -un)"

die() { echo "rehearsal_cluster: $*" >&2; exit 1; }

# Private empty HOME for every child (never the real one: no ~/.pgpass, ~/.pg_service.conf, ~/.psqlrc).
TMP_HOME="$(mktemp -d "${TMPDIR:-/tmp}/rehearsal-home.XXXXXX")" || die "cannot create a temp HOME"
trap 'rm -rf "${TMP_HOME}"' EXIT

pgenv() {
  env -i PATH="${PG_BIN}:/usr/bin:/bin" HOME="${TMP_HOME}" LANG="en_US.UTF-8" \
      PGPASSFILE="${TMP_HOME}/.no-pgpass" PGSERVICEFILE="${TMP_HOME}/.no-pg-service" "$@"
}
psql_raw() {
  pgenv PGOPTIONS="-c client_min_messages=warning" "${PG_BIN}/psql" -h 127.0.0.1 -p "${PORT}" -U "${PG_USER}" \
        -v ON_ERROR_STOP=1 -X -q "$@"
}
# Every psql call first proves the server behind 127.0.0.1:55432 is THIS cluster (address, port, data dir).
psql_local() {
  local ident
  ident="$(psql_raw -d postgres -Atc "SELECT host(inet_server_addr())||'|'||inet_server_port()||'|'||current_setting('data_directory')")" \
    || die "cannot identify the server on 127.0.0.1:${PORT}"
  [ "${ident}" = "127.0.0.1|${PORT}|${DATA_DIR}" ] || die "server identity '${ident}' is not the rehearsal cluster; refusing"
  psql_raw "$@"
}

# No symlink anywhere in the data dir's path, and the path is its own realpath.
assert_no_symlinks() {
  local p="${REHEARSAL_HOME}/pg" real
  while [ "${p}" != "/" ] && [ "${p}" != "." ]; do
    [ ! -L "${p}" ] || die "refusing: ${p} is a symlink"
    p="$(dirname "${p}")"
  done
  for p in "${REHEARSAL_HOME}" "${DATA_DIR}" "${SOCK_DIR}"; do
    [ -e "${p}" ] || continue
    real="$(cd -P "${p}" && pwd -P)" || die "cannot resolve ${p}"
    [ "${real}" = "${p}" ] || die "refusing: ${p} resolves to ${real}"
  done
}

require_bins() {
  [ -x "${PG_BIN}/initdb" ] && [ -x "${PG_BIN}/pg_ctl" ] || \
    die "PostgreSQL binaries not found at ${PG_BIN} (install nothing automatically; see README)"
}

is_running() { pgenv "${PG_BIN}/pg_ctl" -D "${DATA_DIR}" status >/dev/null 2>&1; }
is_initialised() { [ -f "${DATA_DIR}/PG_VERSION" ]; }

# Port must be free OR held by our own postmaster; refuse to share it with anything else. FAILS CLOSED:
# if the probe itself cannot run or returns anything but a clean "listening"/"nothing", we refuse.
assert_port_ours_or_free() {
  command -v lsof >/dev/null 2>&1 || die "lsof not available; cannot prove port ${PORT} is free (failing closed)"
  local rc=0
  lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1 || rc=$?
  case "${rc}" in
    0) is_running || die "port ${PORT} is in use by another process; refusing to start" ;;
    1) ;;  # nothing listening
    *) die "lsof probe failed (rc=${rc}); failing closed" ;;
  esac
}

cmd_init() {
  require_bins
  mkdir -p "${REHEARSAL_HOME}"
  assert_no_symlinks
  mkdir -p "${SOCK_DIR}"
  chmod 700 "${SOCK_DIR}"
  assert_no_symlinks
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
unix_socket_permissions = 0700
unix_socket_group = ''
max_connections = 40
shared_buffers = 512MB
fsync = off                 # disposable cluster: speed over durability
synchronous_commit = off
full_page_writes = off
CONF
    # Unix socket (mode 0700, owner only) + TCP loopback. The loopback rule is `trust`: any local
    # process can connect as the superuser (accepted residual — see header). No other rule exists.
    cat > "${DATA_DIR}/pg_hba.conf" <<HBA
local   all   all                 trust
host    all   all   127.0.0.1/32  trust
HBA
    echo "init: cluster created at ${DATA_DIR}"
  fi
  cmd_start
  local have
  have="$(psql_local -d postgres -Atc "SELECT count(*) FROM pg_database WHERE datname='${DBNAME}'")" \
    || die "init: could not check whether database ${DBNAME} exists"
  if [ "${have}" = "0" ]; then
    psql_local -d postgres -c "CREATE DATABASE ${DBNAME}" || die "init: CREATE DATABASE failed"
    echo "init: created database ${DBNAME}"
  elif [ "${have}" = "1" ]; then
    echo "init: database ${DBNAME} already exists"
  else
    die "init: unexpected answer '${have}' when checking for database ${DBNAME}"
  fi
  # Extensions the repository schema needs on a vanilla server (pgvector, pgcrypto, uuid-ossp, pg_trgm).
  for ext in pgcrypto uuid-ossp vector pg_trgm; do
    psql_local -d "${DBNAME}" -c "CREATE EXTENSION IF NOT EXISTS \"${ext}\"" || die "init: extension ${ext} failed"
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
    END \$\$;" || die "init: role creation failed"
  echo "init: local stand-in roles present (amjis_app data_plane_builder purna_inquiry_owner service_role anon authenticated)"
}

cmd_start() {
  require_bins
  assert_no_symlinks
  is_initialised || die "not initialised; run: $0 init"
  grep -q "^unix_socket_permissions = 0700" "${DATA_DIR}/postgresql.conf" || \
    die "cluster predates the socket hardening (no unix_socket_permissions = 0700); run: $0 reset --yes"
  mkdir -p "${SOCK_DIR}"
  chmod 700 "${SOCK_DIR}"
  if is_running; then echo "start: already running on ${PORT}"; return 0; fi
  assert_port_ours_or_free
  pgenv "${PG_BIN}/pg_ctl" -D "${DATA_DIR}" -l "${LOG_FILE}" -w -t 60 start >/dev/null
  echo "start: running on 127.0.0.1:${PORT}"
}

cmd_stop() {
  require_bins
  assert_no_symlinks
  if ! is_initialised || ! is_running; then echo "stop: not running"; return 0; fi
  pgenv "${PG_BIN}/pg_ctl" -D "${DATA_DIR}" -m fast -w stop >/dev/null
  echo "stop: stopped"
}

cmd_status() {
  require_bins
  assert_no_symlinks
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
  assert_no_symlinks
  # The only directory this command will ever delete is the rehearsal data dir under REHEARSAL_HOME.
  [ "${DATA_DIR}" = "${REHEARSAL_HOME}/pg" ] && [ -n "${REHEARSAL_HOME}" ] && [ "${REHEARSAL_HOME}" != "/" ] || \
    die "refusing: unexpected data dir ${DATA_DIR}"
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
