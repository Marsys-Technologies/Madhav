#!/bin/sh
# Installs the three launchd jobs (trackerd KeepAlive, watchdog StartInterval=60,
# serve KeepAlive). Idempotent: safe to re-run (bootout-then-bootstrap).
#
# Two modes:
#
#   ./install.sh
#     IN-PLACE mode (dev/legacy): points the jobs at THIS script's own directory. Fine for
#     local testing, but that directory is whatever checkout you happen to be running from
#     -- a `git checkout` there silently swaps a running daemon's code out from under it,
#     and if it's a /tmp worktree it can vanish on reboot/cleanup. Not recommended for a
#     standing install.
#
#   ./install.sh --install-from-ref <ref> [--prefix <dir>] [--repo <path>]
#                 [--runtime-git-repo <path>]
#     SNAPSHOT mode (recommended): materialises an IMMUTABLE copy of the tracker/ subtree
#     at <ref> via `git archive` (never touches a working tree, never checks anything out)
#     into --prefix (default $HOME/.pariprashna-tracker-code), writes INSTALLED_FROM.json
#     there (source_ref, source_sha, installed_at), and points the jobs at THAT directory.
#     --repo is which local git checkout to archive FROM (default: auto-detected from this
#     script's own location) -- it only needs `<ref>` reachable, e.g. `origin/main` fetched.
#     --runtime-git-repo is a SEPARATE, ideally-permanent checkout the DEPLOYED daemon uses
#     for its own ongoing read-only git operations (for-each-ref, campaign-coordination
#     reads, staleness checks) -- it must still exist after this script exits, so do not
#     point it at a scratch/worktree you are about to remove. Defaults to --repo's value if
#     not given, but you should pass a permanent checkout explicitly for a standing install.
#
#     To update a running snapshot install later: re-run with the same --prefix (or let it
#     default) and a newer <ref>; this script re-renders and reloads all three jobs, with no
#     observability gap longer than one collector cycle (the runtime dir/state.json are
#     untouched by this script -- only the code directory and the launchd jobs change).
set -eu

DEFAULT_LABEL_PREFIX="com.marsys.pariprashna"

MODE="inplace"
INSTALL_FROM_REF=""
PREFIX=""
SRC_REPO=""
RUNTIME_GIT_REPO=""
LABEL_PREFIX="${DEFAULT_LABEL_PREFIX}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

while [ $# -gt 0 ]; do
  case "$1" in
    --install-from-ref) MODE="snapshot"; INSTALL_FROM_REF="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    --repo) SRC_REPO="$2"; shift 2 ;;
    --runtime-git-repo) RUNTIME_GIT_REPO="$2"; shift 2 ;;
    --label-prefix) LABEL_PREFIX="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done

RUNTIME_DIR="${HOME}/.pariprashna-tracker"
PYTHON3="$(command -v python3)"
UID_N="$(id -u)"
LA_DIR="${HOME}/Library/LaunchAgents"

# --- Label-namespace isolation guard -----------------------------------------------
# launchctl labels live in the launchd GUI domain (gui/<uid>/<label>) and are NOT scoped
# by $HOME in any way. RUNTIME_DIR above IS HOME-scoped, so it is easy to believe that
# running this script with HOME overridden (e.g. for an isolated test install) is fully
# isolated from production. It is not: with LABEL_PREFIX left at its default, the
# `launchctl bootout` below still targets the SAME global label the production jobs use,
# and boots them out -- regardless of HOME. This is a real, independently-verified hazard
# (see the selftest below) -- process-forensic follow-up on the 2026-08-19 23m37s blind
# window (README's "2026-08-19 incident" section) found the actual bootout there was 3 BARE
# `launchctl bootout` calls with no bootstrap, matching the OLD undocumented "Stop all
# three" one-liner exactly, not this HOME/label-collision shape (which would show
# bootout+bootstrap pairs). So this guard is NOT confirmed as that incident's cause -- it
# closes a distinct, real gap in this script regardless. Refuse outright either way.
REAL_HOME="$(dscl . -read "/Users/$(id -un)" NFSHomeDirectory 2>/dev/null | awk '{print $2}')"
if [ -z "${REAL_HOME}" ]; then REAL_HOME="${HOME}"; fi
if [ "${HOME}" != "${REAL_HOME}" ] && [ "${LABEL_PREFIX}" = "${DEFAULT_LABEL_PREFIX}" ]; then
  echo "REFUSING: \$HOME is overridden (HOME=${HOME}, real home=${REAL_HOME}) but" >&2
  echo "LABEL_PREFIX is still the production default (${DEFAULT_LABEL_PREFIX})." >&2
  echo "HOME isolation does not isolate launchctl labels -- this run would bootout the" >&2
  echo "PRODUCTION trackerd/watchdog/serve jobs regardless of HOME. Pass" >&2
  echo "--label-prefix <something-not-${DEFAULT_LABEL_PREFIX}> for an isolated test install." >&2
  exit 1
fi

if [ "${MODE}" = "snapshot" ]; then
  : "${PREFIX:=${HOME}/.pariprashna-tracker-code}"
  if [ -z "${SRC_REPO}" ]; then
    SRC_REPO="$(cd "${SCRIPT_DIR}" && git rev-parse --show-toplevel 2>/dev/null || true)"
  fi
  if [ -z "${SRC_REPO}" ]; then
    echo "ERROR: --repo not given and could not auto-detect a git repo from ${SCRIPT_DIR}." >&2
    echo "       Pass --repo <path-to-a-checkout-with-${INSTALL_FROM_REF}-fetched>." >&2
    exit 1
  fi
  : "${RUNTIME_GIT_REPO:=${SRC_REPO}}"

  SRC_SHA="$(git -C "${SRC_REPO}" rev-parse "${INSTALL_FROM_REF}")"
  echo "archiving 00_ARCHITECTURE/briefs/pariprashna_swarm/tracker @ ${INSTALL_FROM_REF} (${SRC_SHA}) from ${SRC_REPO}"

  NEW_PREFIX="${PREFIX}.new.$$"
  rm -rf "${NEW_PREFIX}"
  mkdir -p "${NEW_PREFIX}"
  git -C "${SRC_REPO}" archive "${SRC_SHA}" 00_ARCHITECTURE/briefs/pariprashna_swarm/tracker \
    | tar -x -C "${NEW_PREFIX}" --strip-components=4

  INSTALLED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cat > "${NEW_PREFIX}/INSTALLED_FROM.json" <<EOF
{
  "source_ref": "${INSTALL_FROM_REF}",
  "source_sha": "${SRC_SHA}",
  "source_repo": "${SRC_REPO}",
  "installed_at": "${INSTALLED_AT}",
  "prefix": "${PREFIX}"
}
EOF

  # Atomic swap: the old snapshot (if any) is fully replaced only once the new one is
  # completely materialised -- no window where the code dir is half-written.
  OLD_PREFIX="${PREFIX}.old.$$"
  if [ -d "${PREFIX}" ]; then
    mv "${PREFIX}" "${OLD_PREFIX}"
  fi
  mv "${NEW_PREFIX}" "${PREFIX}"
  if [ -d "${OLD_PREFIX}" ]; then
    rm -rf "${OLD_PREFIX}"
  fi
  chmod +x "${PREFIX}"/*.py "${PREFIX}/install.sh" \
    "${PREFIX}/tracker-stop" "${PREFIX}/tracker-start" "${PREFIX}/tracker-ack-blind" \
    "${PREFIX}/tracker-cron-watchdog" "${PREFIX}/tracker-health-check" 2>/dev/null || true

  TRACKER_DIR="${PREFIX}"
  echo "snapshot installed: ${TRACKER_DIR} (source ${SRC_SHA}, runtime git repo ${RUNTIME_GIT_REPO})"
else
  TRACKER_DIR="${SCRIPT_DIR}"
  : "${RUNTIME_GIT_REPO:=$(cd "${TRACKER_DIR}" && git rev-parse --show-toplevel 2>/dev/null || echo "")}"
  echo "in-place mode: jobs will point at ${TRACKER_DIR} (a live checkout, not a snapshot)"
fi

# launchd jobs do NOT inherit the interactive shell's PATH (no .zshrc/.zprofile), so `gh`
# and `gcloud` are invisible to collect.py unless the plist sets PATH explicitly. Capture
# the real PATH now (interactive shell, homebrew etc. all resolved) plus the standard
# system dirs as a floor, so it works whether this is run interactively or not.
GH_DIR="$(dirname "$(command -v gh 2>/dev/null || echo /opt/homebrew/bin/gh)")"
GCLOUD_DIR="$(dirname "$(command -v gcloud 2>/dev/null || echo /opt/homebrew/bin/gcloud)")"
PATH_ENV="${PATH}:${GH_DIR}:${GCLOUD_DIR}:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

mkdir -p "${LA_DIR}" "${RUNTIME_DIR}/logs" "${RUNTIME_DIR}/events"

render() {
  template="$1"
  out="$2"
  label_out="$3"
  sed -e "s#__PYTHON3__#${PYTHON3}#g" \
      -e "s#__TRACKER_DIR__#${TRACKER_DIR}#g" \
      -e "s#__RUNTIME_DIR__#${RUNTIME_DIR}#g" \
      -e "s#__PATH_ENV__#${PATH_ENV}#g" \
      -e "s#__TRACKER_GIT_REPO__#${RUNTIME_GIT_REPO}#g" \
      -e "s#__LABEL__#${label_out}#g" \
      "${template}" > "${out}"
}

echo "about to bootout + bootstrap under label prefix '${LABEL_PREFIX}':"
for job in trackerd watchdog serve; do
  echo "  ${LABEL_PREFIX}-${job}"
done

# Item 2: mutual exclusion with tracker-stop/tracker-start/tracker-cron-watchdog -- all four
# scripts source the same lock helper and take the same lock around their own
# bootout/bootstrap window, so a concurrent invocation serializes instead of interleaving.
. "${SCRIPT_DIR}/_tracker_lock.sh"
tracker_lock_acquire_blocking "install.sh" || exit 1
trap 'tracker_lock_release' EXIT

# Also write the intentional-stop marker (same file tracker-stop uses) around this script's
# own bootout window, so T4's cron watcher stands down for a legitimate reinstall instead of
# racing it. Only clear it afterward if THIS run is the one that created it -- if a marker
# already existed (an operator deliberately stopped the tracker via tracker-stop and is now
# separately redeploying code while still meaning to stay stopped), leave it in place; this
# run's own bootout+bootstrap already covered its own window regardless.
MARKER="${RUNTIME_DIR}/STOPPED_INTENTIONALLY.json"
MARKER_PREEXISTED=false
if [ -f "${MARKER}" ]; then
  MARKER_PREEXISTED=true
else
  TRACKER_INSTALL_MARKER_PATH="${MARKER}" python3 -c "
import json, datetime, os
path = os.environ['TRACKER_INSTALL_MARKER_PATH']
record = {
    'ts': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'reason': 'install.sh reinstall in progress',
    'invoking_user': os.environ.get('USER') or os.environ.get('LOGNAME') or 'unknown',
}
tmp = path + '.tmp'
with open(tmp, 'w', encoding='utf-8') as f:
    json.dump(record, f, indent=2, sort_keys=True)
os.replace(tmp, path)
"
fi

for job in trackerd watchdog serve; do
  # LABEL_PREFIX, not a hardcoded string -- see the guard above. HOME isolation does NOT
  # isolate this: the label is global to the launchd domain regardless of $HOME, so a
  # mismatched prefix here is what bootouts the wrong (possibly production) jobs.
  label="${LABEL_PREFIX}-${job}"
  plist="${LA_DIR}/${label}.plist"
  # Template files are named by job (fixed, e.g. com.marsys.pariprashna-trackerd.plist.template)
  # regardless of LABEL_PREFIX -- only the rendered output's Label key and file path vary.
  render "${TRACKER_DIR}/launchd/${DEFAULT_LABEL_PREFIX}-${job}.plist.template" "${plist}" "${label}"
  launchctl bootout "gui/${UID_N}/${label}" 2>/dev/null || true
  launchctl bootstrap "gui/${UID_N}" "${plist}"
  echo "installed + bootstrapped: ${label} -> ${plist}"
done

if [ "${MARKER_PREEXISTED}" = false ]; then
  rm -f "${MARKER}"
fi
tracker_lock_release
trap - EXIT

# T4 (item c): a DIFFERENT subsystem from the launchd jobs above -- cron, not launchd, so
# the exact 2026-08-19 failure mode (a launchd-domain bootout removing all three jobs
# including the watchdog) cannot take this out too. Idempotent: the marker comment scopes
# replacement to entries installed under THIS LABEL_PREFIX only, so a test install's cron
# entry (if --label-prefix was used) never collides with production's.
CRON_MARKER="# pariprashna-tracker-cron-watchdog:${LABEL_PREFIX}"
CRON_LINE="*/5 * * * * LABEL_PREFIX=${LABEL_PREFIX} ${TRACKER_DIR}/tracker-cron-watchdog >>${RUNTIME_DIR}/logs/cron_watchdog.cron.log 2>&1 ${CRON_MARKER}"
( crontab -l 2>/dev/null | grep -vF "${CRON_MARKER}" || true; echo "${CRON_LINE}" ) | crontab -
echo "cron T4 installed (every 5 min): ${CRON_LINE}"

echo
echo "Code dir:    ${TRACKER_DIR}"
echo "Runtime dir: ${RUNTIME_DIR}"
echo "Git repo (runtime reads): ${RUNTIME_GIT_REPO}"
echo "Stop all three (marks the outage intentional -- see tracker-stop): ${TRACKER_DIR}/tracker-stop"
echo "Tail logs:       tail -f ${RUNTIME_DIR}/logs/*.log"
