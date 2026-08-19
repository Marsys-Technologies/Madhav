#!/bin/sh
# Installs the three launchd jobs (trackerd KeepAlive, watchdog StartInterval=60,
# serve KeepAlive) pointed at THIS checkout of the tracker code. Re-run after moving the
# repo. Idempotent: safe to run again (bootout-then-bootstrap).
set -eu

TRACKER_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="${HOME}/.pariprashna-tracker"
PYTHON3="$(command -v python3)"
UID_N="$(id -u)"
LA_DIR="${HOME}/Library/LaunchAgents"

mkdir -p "${LA_DIR}" "${RUNTIME_DIR}/logs" "${RUNTIME_DIR}/events"

render() {
  template="$1"
  out="$2"
  sed -e "s#__PYTHON3__#${PYTHON3}#g" \
      -e "s#__TRACKER_DIR__#${TRACKER_DIR}#g" \
      -e "s#__RUNTIME_DIR__#${RUNTIME_DIR}#g" \
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
echo "Runtime dir: ${RUNTIME_DIR}"
echo "Stop all three:  for j in trackerd watchdog serve; do launchctl bootout gui/${UID_N}/com.marsys.pariprashna-\$j; done"
echo "Tail logs:       tail -f ${RUNTIME_DIR}/logs/*.log"
