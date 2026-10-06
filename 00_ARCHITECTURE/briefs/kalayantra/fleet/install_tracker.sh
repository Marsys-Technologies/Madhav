#!/usr/bin/env bash
# Install the KĀLA-YANTRA control plane: a second instance of the Pravāha tracker (port 8767) and the `ky` CLI wrapper.
#   install_tracker.sh                 install/refresh (idempotent); uses the package path in $KY_ROOT/run/TRACKER_GOV
#   install_tracker.sh --gov <path>    set the tracker package parent dir (…/platform/scripts/governance) then install
#   install_tracker.sh --stop          unload the launchd agent
set -euo pipefail
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
RUN="$KY_ROOT/run"; mkdir -p "$RUN" "$KY_ROOT/bin" "$RUN/reviews"
LABEL=com.madhav.kalayantra.tracker
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PY=/opt/homebrew/bin/python3
DEFAULT_GOV=/Users/Dev/madhav-l3/pravaha/platform/scripts/governance      # until B-1 lands the package on main
MODEL="$KY_ROOT/wt/campaign/00_ARCHITECTURE/control/kalayantra/plan_model.json"

if [ "${1:-}" = "--stop" ]; then launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true; rm -f "$PLIST"; echo "tracker stopped"; exit 0; fi
if [ "${1:-}" = "--gov" ]; then echo "$2" > "$RUN/TRACKER_GOV"; shift 2; fi
GOV="$(cat "$RUN/TRACKER_GOV" 2>/dev/null || echo "$DEFAULT_GOV")"
[ -d "$GOV/pravaha_tracker" ] || { echo "tracker package not found under $GOV"; exit 1; }
[ -f "$MODEL" ] || { echo "plan model missing: $MODEL"; exit 1; }
$PY -c "import json,sys; json.load(open(sys.argv[1]))" "$MODEL"
touch "$RUN/EVENTS.jsonl"

cat > "$KY_ROOT/bin/ky" <<EOF
#!/usr/bin/env bash
# KĀLA-YANTRA campaign CLI (a second instance of the Pravāha tracker). Stream comes from KY_STREAM (set per lane by the fleet)
# or --stream. See: ky --help
export PRAVAHA_HOME="$KY_ROOT"
export PRAVAHA_EVENTS="$RUN/EVENTS.jsonl"
export PRAVAHA_PLAN_MODEL="$MODEL"
export PRAVAHA_TRACKER_PORT=8767
export PRAVAHA_URL="http://127.0.0.1:8767"
export PRAVAHA_REPO="$KY_ROOT/wt/campaign"
export PRAVAHA_PGENV="\${PRAVAHA_PGENV:-/Users/Dev/.config/pravaha/pgenv.sh}"
export PRAVAHA_STREAM="\${KY_STREAM:-\${PRAVAHA_STREAM:-}}"
GOV="\$(cat "$RUN/TRACKER_GOV" 2>/dev/null || echo "$DEFAULT_GOV")"
PYTHONPATH="\$GOV\${PYTHONPATH:+:\$PYTHONPATH}" exec $PY -m pravaha_tracker.cli "\$@"
EOF
chmod +x "$KY_ROOT/bin/ky"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>$PY</string><string>-u</string><string>-m</string><string>pravaha_tracker.server</string><string>--port</string><string>8767</string></array>
  <key>WorkingDirectory</key><string>$GOV</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>HOME</key><string>$HOME</string>
    <key>PRAVAHA_HOME</key><string>$KY_ROOT</string>
    <key>PRAVAHA_EVENTS</key><string>$RUN/EVENTS.jsonl</string>
    <key>PRAVAHA_PLAN_MODEL</key><string>$MODEL</string>
    <key>PRAVAHA_TRACKER_PORT</key><string>8767</string>
    <key>PRAVAHA_REPO</key><string>$KY_ROOT/wt/campaign</string>
    <key>PRAVAHA_PGENV</key><string>/Users/Dev/.config/pravaha/pgenv.sh</string>
    <key>PYTHONUNBUFFERED</key><string>1</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ProcessType</key><string>Background</string>
  <key>ThrottleInterval</key><integer>2</integer>
  <key>StandardOutPath</key><string>$RUN/tracker.log</string>
  <key>StandardErrorPath</key><string>$RUN/tracker.log</string>
</dict></plist>
EOF
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl enable "gui/$(id -u)/$LABEL"
sleep 3
if curl -fs -m 5 http://127.0.0.1:8767/api/health >/dev/null; then echo "tracker live on 127.0.0.1:8767 (package: $GOV)"; else echo "tracker not answering yet — see $RUN/tracker.log"; exit 1; fi
"$KY_ROOT/bin/ky" status | head -3
