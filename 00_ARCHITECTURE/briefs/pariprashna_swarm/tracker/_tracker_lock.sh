# Item 2: shared advisory lock for the four scripts capable of moving the
# com.marsys.pariprashna-* launchd labels -- install.sh, tracker-stop, tracker-start,
# tracker-cron-watchdog. Without mutual exclusion, two of them running concurrently (a
# human re-running install.sh while T4's cron tick fires, say) can interleave
# bootout/bootstrap calls in an undefined order against the same labels.
#
# Atomic `mkdir` under RUNTIME_DIR (never the repo) -- portable, no flock(1) dependency
# (not reliably present on macOS). Callers must set RUNTIME_DIR before sourcing this file.
#
# Usage:
#   . "$(dirname "$0")/_tracker_lock.sh"
#   tracker_lock_acquire_blocking "my-script-name" || exit 1   # waits up to 30s
#   ... critical section (the actual launchctl bootout/bootstrap calls) ...
#   tracker_lock_release
#
#   tracker_lock_acquire_nonblocking "my-script-name" || { log-and-defer; exit 0; }  # T4 only
#   tracker_lock_release

TRACKER_LOCK_DIR="${RUNTIME_DIR}/label_ops.lock"

tracker_lock_acquire_blocking() {
  waited=0
  timeout="${TRACKER_LOCK_TIMEOUT_S:-30}"
  while ! mkdir "${TRACKER_LOCK_DIR}" 2>/dev/null; do
    if [ "${waited}" -ge "${timeout}" ]; then
      echo "ERROR: could not acquire ${TRACKER_LOCK_DIR} within ${timeout}s (held by: $(cat "${TRACKER_LOCK_DIR}/holder" 2>/dev/null || echo unknown))" >&2
      return 1
    fi
    sleep 1
    waited=$((waited + 1))
  done
  echo "$1 pid=$$ $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${TRACKER_LOCK_DIR}/holder" 2>/dev/null || true
  return 0
}

# Non-blocking, single attempt, no retry -- T4's own contract: defer and exit rather than
# fight whatever legitimately holds the lock.
tracker_lock_acquire_nonblocking() {
  if mkdir "${TRACKER_LOCK_DIR}" 2>/dev/null; then
    echo "$1 pid=$$ $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${TRACKER_LOCK_DIR}/holder" 2>/dev/null || true
    return 0
  fi
  return 1
}

tracker_lock_release() {
  rm -rf "${TRACKER_LOCK_DIR}"
}
