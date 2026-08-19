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

MODE="inplace"
INSTALL_FROM_REF=""
PREFIX=""
SRC_REPO=""
RUNTIME_GIT_REPO=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

while [ $# -gt 0 ]; do
  case "$1" in
    --install-from-ref) MODE="snapshot"; INSTALL_FROM_REF="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    --repo) SRC_REPO="$2"; shift 2 ;;
    --runtime-git-repo) RUNTIME_GIT_REPO="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done

RUNTIME_DIR="${HOME}/.pariprashna-tracker"
PYTHON3="$(command -v python3)"
UID_N="$(id -u)"
LA_DIR="${HOME}/Library/LaunchAgents"

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
  chmod +x "${PREFIX}"/*.py "${PREFIX}/install.sh" 2>/dev/null || true

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
  sed -e "s#__PYTHON3__#${PYTHON3}#g" \
      -e "s#__TRACKER_DIR__#${TRACKER_DIR}#g" \
      -e "s#__RUNTIME_DIR__#${RUNTIME_DIR}#g" \
      -e "s#__PATH_ENV__#${PATH_ENV}#g" \
      -e "s#__TRACKER_GIT_REPO__#${RUNTIME_GIT_REPO}#g" \
      "${template}" > "${out}"
}

for job in trackerd watchdog serve; do
  label="com.marsys.pariprashna-${job}"
  plist="${LA_DIR}/${label}.plist"
  render "${TRACKER_DIR}/launchd/${label}.plist.template" "${plist}"
  launchctl bootout "gui/${UID_N}/${label}" 2>/dev/null || true
  launchctl bootstrap "gui/${UID_N}" "${plist}"
  echo "installed + bootstrapped: ${label} -> ${plist}"
done

echo
echo "Code dir:    ${TRACKER_DIR}"
echo "Runtime dir: ${RUNTIME_DIR}"
echo "Git repo (runtime reads): ${RUNTIME_GIT_REPO}"
echo "Stop all three:  for j in trackerd watchdog serve; do launchctl bootout gui/${UID_N}/com.marsys.pariprashna-\$j; done"
echo "Tail logs:       tail -f ${RUNTIME_DIR}/logs/*.log"
