#!/usr/bin/env bash
# Install (or re-install) the Pravāha tracker as a launchd agent: starts at login, restarts on exit.
#   install:    bash install_launchd.sh
#   uninstall:  bash install_launchd.sh --uninstall
#   restart:    launchctl kickstart -k gui/$(id -u)/com.madhav.pravaha.tracker
# Optional DB checks: set PRAVAHA_PGENV below (decision D-T1) to a chmod-600 read-only env file.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
LABEL=com.madhav.pravaha.tracker
DST="$HOME/Library/LaunchAgents/$LABEL.plist"
mkdir -p /Users/Dev/pravaha/run
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
if [ "${1:-}" = "--uninstall" ]; then rm -f "$DST"; echo "uninstalled"; exit 0; fi
cp "$HERE/$LABEL.plist" "$DST"
if [ -n "${PRAVAHA_PGENV:-}" ]; then
  /usr/libexec/PlistBuddy -c "Add :EnvironmentVariables:PRAVAHA_PGENV string $PRAVAHA_PGENV" "$DST" 2>/dev/null \
    || /usr/libexec/PlistBuddy -c "Set :EnvironmentVariables:PRAVAHA_PGENV $PRAVAHA_PGENV" "$DST"
fi
launchctl bootstrap "gui/$(id -u)" "$DST"
launchctl enable "gui/$(id -u)/$LABEL"
sleep 2
curl -fsS http://127.0.0.1:8766/api/health >/dev/null && echo "Pravāha tracker live: http://127.0.0.1:8766" || { echo "tracker did not come up — see /Users/Dev/pravaha/run/tracker.log"; exit 1; }
