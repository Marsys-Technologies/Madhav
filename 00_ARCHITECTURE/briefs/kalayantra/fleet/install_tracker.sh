#!/usr/bin/env bash
# Install the KĀLA-YANTRA control plane v1.1: a second instance of the Pravāha tracker (port 8767) and the `ky` CLI wrapper.
#   install_tracker.sh --gov <package-parent-dir>     REQUIRED on first install and when switching packages
#   install_tracker.sh                                 refresh with the previously selected package
#   install_tracker.sh --stop
# Acceptance (charter §4.1): health 200 is not enough — the receipt records package path+hash, model hash, no model error,
# a fresh tick, and (after B-1) that `ky audit` runs. Written to run/TRACKER_INSTALL_RECEIPT.json.
set -euo pipefail
umask 077
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; RUN="$KY_ROOT/run"
mkdir -p "$RUN" "$KY_ROOT/bin" "$RUN/reviews" "$RUN/verdicts" "$RUN/claims" "$RUN/ops" "$HOME/Library/LaunchAgents"
LABEL=com.madhav.kalayantra.tracker; PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"; PY=/opt/homebrew/bin/python3
MODEL="$KY_ROOT/wt/campaign/00_ARCHITECTURE/control/kalayantra/plan_model.json"
if [ "${1:-}" = "--stop" ]; then launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true; rm -f "$PLIST"; echo "tracker stopped"; exit 0; fi
if [ "${1:-}" = "--gov" ]; then [ $# -eq 2 ] || { echo "usage: --gov <package-parent-dir>"; exit 2; }; GOV="$2"; printf '%s\n' "$GOV" > "$RUN/TRACKER_GOV"
elif [ -s "$RUN/TRACKER_GOV" ]; then GOV="$(cat "$RUN/TRACKER_GOV")"
else echo "Select the reviewed tracker package explicitly: $0 --gov <dir containing pravaha_tracker/>"; exit 1; fi
[ -d "$GOV/pravaha_tracker" ] || { echo "tracker package not found under $GOV"; exit 1; }
# The tracker and the `ky` CLI run from a SNAPSHOT of the selected package ($KY_ROOT/tracker_live), so an edit in the working
# tree (B-1b is developed there) can never break the running control plane. Re-run this installer to adopt a new package.
LIVE="$KY_ROOT/tracker_live"; rm -rf "$LIVE.new"; mkdir -p "$LIVE.new"
rsync -a --exclude '__pycache__' "$GOV/pravaha_tracker" "$LIVE.new/"; rm -rf "$LIVE.old"; [ -d "$LIVE" ] && mv "$LIVE" "$LIVE.old"; mv "$LIVE.new" "$LIVE"
[ -f "$MODEL" ] || { echo "plan model missing: $MODEL"; exit 1; }
$PY -c "import json,sys; json.load(open(sys.argv[1]))" "$MODEL"
touch "$RUN/EVENTS.jsonl"
cat > "$KY_ROOT/bin/ky" <<EOF
#!/usr/bin/env bash
# KĀLA-YANTRA campaign CLI (second instance of the Pravāha tracker). Stream from KY_STREAM or --stream. See: ky --help
export PRAVAHA_HOME="$KY_ROOT"
export PRAVAHA_EVENTS="$RUN/EVENTS.jsonl"
export PRAVAHA_PLAN_MODEL="$MODEL"
export PRAVAHA_TRACKER_PORT=8767
export PRAVAHA_URL="http://127.0.0.1:8767"
export PRAVAHA_REPO="$KY_ROOT/wt/campaign"
export PRAVAHA_HOLD="$KY_ROOT/HOLD"
export PRAVAHA_STREAM="\${KY_STREAM:-\${PRAVAHA_STREAM:-}}"
export KY_WORKER="\${KY_LANE:-}"
PYTHONPATH="$LIVE" exec $PY -m pravaha_tracker.cli "\$@"
EOF
chmod +x "$KY_ROOT/bin/ky"
cat > "$KY_ROOT/bin/kybrief" <<EOF
#!/usr/bin/env bash
# kybrief <ID> — print one plan-model item, its brief included (the item's whole specification)
exec $PY -c 'import json, sys
m = json.load(open(sys.argv[1])); i = [x for x in m["items"] if x["id"] == sys.argv[2]]
print(json.dumps(i[0], ensure_ascii=False, indent=1) if i else "no such item: " + sys.argv[2]); sys.exit(0 if i else 1)' "$MODEL" "\${1:?usage: kybrief <ITEM-ID>}"
EOF
chmod +x "$KY_ROOT/bin/kybrief"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>$PY</string><string>-u</string><string>-m</string><string>pravaha_tracker.server</string><string>--port</string><string>8767</string></array>
  <key>WorkingDirectory</key><string>$LIVE</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>HOME</key><string>$HOME</string>
    <key>PRAVAHA_HOME</key><string>$KY_ROOT</string>
    <key>PRAVAHA_EVENTS</key><string>$RUN/EVENTS.jsonl</string>
    <key>PRAVAHA_PLAN_MODEL</key><string>$MODEL</string>
    <key>PRAVAHA_TRACKER_PORT</key><string>8767</string>
    <key>PRAVAHA_REPO</key><string>$KY_ROOT/wt/campaign</string>
    <key>PRAVAHA_PGENV</key><string>/Users/Dev/.config/pravaha/pgenv.sh</string>
    <key>PRAVAHA_HOLD</key><string>$KY_ROOT/HOLD</string>
    <key>PYTHONUNBUFFERED</key><string>1</string>
  </dict>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/><key>ProcessType</key><string>Background</string><key>ThrottleInterval</key><integer>2</integer>
  <key>StandardOutPath</key><string>$RUN/tracker.log</string><key>StandardErrorPath</key><string>$RUN/tracker.log</string>
</dict></plist>
EOF
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"; launchctl enable "gui/$(id -u)/$LABEL"
for i in $(seq 1 20); do curl -fs -m 3 http://127.0.0.1:8767/api/health >/dev/null 2>&1 && break; sleep 1; done
H="$(curl -fs -m 5 http://127.0.0.1:8767/api/health || true)"
$PY - "$H" "$GOV" "$MODEL" "$RUN/TRACKER_INSTALL_RECEIPT.json" "$KY_ROOT/bin/ky" "$LIVE" <<'PYEOF'
import hashlib, json, os, pathlib, subprocess, sys, time
h = json.loads(sys.argv[1]) if sys.argv[1] else {}
gov, model, out, ky, live = sys.argv[2:7]
pkg = pathlib.Path(live) / "pravaha_tracker"      # the hash is of what actually runs
src = subprocess.run(["git", "-C", gov, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", gov, "status", "--porcelain", "--", "pravaha_tracker"], capture_output=True, text=True).stdout.strip() != ""
pkg_hash = hashlib.sha256(b"".join(sorted(p.read_bytes() for p in pkg.glob("*.py")))).hexdigest()
model_hash = hashlib.sha256(pathlib.Path(model).read_bytes()).hexdigest()
audit = subprocess.run([ky, "audit", "--since", "kickoff"], capture_output=True, text=True, env={**os.environ, "KY_STREAM": "S"})
ok = bool(h.get("ok")) and h.get("model_error") in (None, "") and float(h.get("engine_tick_age_s", 999)) < 30
rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "accepted": ok, "health": h, "package_dir": gov, "package_sha256": pkg_hash,
       "running_from": live, "source_commit": src, "source_dirty": dirty,
       "model_sha256": model_hash, "audit_available": audit.returncode in (0, 1) and "usage" not in (audit.stderr or "").lower() and "invalid choice" not in (audit.stderr or "")}
pathlib.Path(out).write_text(json.dumps(rec, indent=1))
print(("ACCEPTED" if ok else "NOT ACCEPTED") + f" — package {gov} ({pkg_hash[:12]}), model {model_hash[:12]}, audit_available={rec['audit_available']}")
sys.exit(0 if ok else 1)
PYEOF
