#!/usr/bin/env bash
# apply_schema.sh — apply the repository schema to the REHEARSAL database only.
#
#   apply_schema.sh replay [--url URL]     bootstrap + best-effort replay of every migration file
#   apply_schema.sh verify [--url URL]     ledger (sha256) vs files on disk; table count
#   apply_schema.sh migrate [--dry-run] [--url URL]
#                                          the repo's real runner (platform/scripts/migrate.ts),
#                                          for INCREMENTS after a replay (it cannot bootstrap an empty
#                                          database — see replay_schema.py)
#
# URL defaults to the cluster's own (`rehearsal_cluster.sh url`). Any URL is FIRST passed through
# rehearsal_guard.py, which returns the NORMALISED URL; only that returned value is used from then on
# (never the original string). The guard accepts 127.0.0.1:55432 and database rehearsal[_x] only, no
# password, no libpq overrides, no production-like names. The LIVE server identity (port, database,
# data_directory) is then verified before anything is applied. Every command runs under `env -i` with an
# explicit environment and a private EMPTY HOME (PGPASSFILE=<empty-home>/.no-pgpass, PGSERVICEFILE=<empty-home>/.no-pg-service): nothing
# is inherited (no PG*/DATABASE_URL/credentials); the migration runner receives only PATH, HOME and
# DATABASE_URL.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM="$(cd "${HERE}/../../.." && pwd)"
PG_BIN="${REHEARSAL_PG_BIN:-/opt/homebrew/opt/postgresql@15/bin}"
PY="$(command -v python3)"

die() { echo "apply_schema: $*" >&2; exit 1; }

cmd="${1:-}"; [ -n "${cmd}" ] || die "usage: $0 replay|verify|migrate [--dry-run] [--url URL]"
shift || true
URL=""; URL_GIVEN=0; DRY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --url) URL="${2:-}"; URL_GIVEN=1; shift 2 ;;
    --dry-run) DRY="--dry-run"; shift ;;
    *) die "unknown argument: $1" ;;
  esac
done
# An explicit --url (even an empty one) is judged by the guard as given; only an ABSENT --url defaults.
[ "${URL_GIVEN}" = 1 ] || URL="$("${HERE}/rehearsal_cluster.sh" url)"

# 1. Guard FIRST — before any process receives the URL. The returned NORMALISED value replaces URL.
URL="$(env -i PATH="/usr/bin:/bin" HOME=/var/empty "${PY}" "${HERE}/rehearsal_guard.py" "${URL}")" \
  || die "URL refused by rehearsal guard; nothing was run"
[ -n "${URL}" ] || die "URL refused by rehearsal guard; nothing was run"

# Private empty HOME for every child (never the real HOME).
TMP_HOME="$(mktemp -d "${TMPDIR:-/tmp}/rehearsal-home.XXXXXX")" || die "cannot create a temp HOME"
trap 'rm -rf "${TMP_HOME}"' EXIT

case "${cmd}" in
  replay|verify)
    env -i PATH="${PG_BIN}:/usr/bin:/bin" HOME="${TMP_HOME}" LANG="en_US.UTF-8" \
      PGPASSFILE="${TMP_HOME}/.no-pgpass" PGSERVICEFILE="${TMP_HOME}/.no-pg-service" REHEARSAL_PG_BIN="${PG_BIN}" \
      "${PY}" "${HERE}/replay_schema.py" "${cmd}" --url "${URL}"
    ;;
  migrate)
    # Verify the live server is the rehearsal cluster before the runner sees the URL.
    ident="$(env -i PATH="${PG_BIN}:/usr/bin:/bin" HOME="${TMP_HOME}" PGPASSFILE="${TMP_HOME}/.no-pgpass" PGSERVICEFILE="${TMP_HOME}/.no-pg-service" \
      "${PG_BIN}/psql" "${URL}" -X -Atqc \
      "SELECT inet_server_port()||'|'||current_database()||'|'||current_setting('data_directory')")" \
      || die "cannot reach the rehearsal cluster"
    case "${ident}" in
      "55432|rehearsal"*"|/Users/Dev/suvarna/rehearsal/pg") ;;
      *) die "server identity ${ident} is not the rehearsal cluster" ;;
    esac
    echo "server verified: ${ident}"
    command -v node >/dev/null || die "node not found on PATH"
    NODE_DIR="$(dirname "$(command -v node)")"
    TSX="${REHEARSAL_TSX:-${PLATFORM}/node_modules/.bin/tsx}"   # override is for the unit tests' stub
    cd "${PLATFORM}"
    # The runner receives ONLY PATH, HOME (empty) and DATABASE_URL (the normalised, verified URL).
    env -i PATH="${NODE_DIR}:/usr/bin:/bin" HOME="${TMP_HOME}" DATABASE_URL="${URL}" \
      "${TSX}" scripts/migrate.ts ${DRY}
    ;;
  *) die "unknown command ${cmd}" ;;
esac
