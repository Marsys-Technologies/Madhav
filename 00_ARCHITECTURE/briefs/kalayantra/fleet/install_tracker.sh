#!/usr/bin/env bash
# Install the KĀLA-YANTRA control plane v1.1: a second instance of the Pravāha tracker (port 8767) and the `ky` CLI wrapper.
#   install_tracker.sh --gov <package-parent-dir>     REQUIRED on first install and when switching packages
#   install_tracker.sh                                 refresh with the previously selected package
#   install_tracker.sh --stop
# Acceptance (charter §4.1): health 200 is not enough — the receipt records package path+hash, model hash, no model error,
# a fresh tick, and (after B-1) that `ky audit` runs. Written to run/TRACKER_INSTALL_RECEIPT.json.
#
# v1.2 (2026-10-21, incident 07:05Z): the plan model and the tracker's repo path come from ONE source, KY_SOURCE_REPO (default: the auto-synced
# campaign checkout, the same default as executor.sh / finalize.sh / bin/ky), never from the stale $KY_ROOT/wt/campaign. Staleness rule —
# the installer refuses (exit 1, before the package, plist or tracker is touched) unless, after `git fetch origin main` in that checkout:
#   E_TRACKER_SOURCE_DIVERGED   HEAD is an ancestor-or-equal of origin/main (a checkout with its own commits is not the live model);
#   E_TRACKER_SOURCE_STALE      HEAD is at most KY_STALE_MAX_COMMITS (default 20) commits behind origin/main;
#   E_TRACKER_MODEL_STALE       at most KY_MODEL_MAX_COMMITS (default 3) commits that change plan_model.json are missing from HEAD.
# v1.3 (2026-10-21, incident 11:14Z): the plist carries PRAVAHA_CALL_TIMEOUT_S (default 20, the installer's own PRAVAHA_CALL_TIMEOUT_S overrides it)
# because the tracker's built-in 5 s is below real GitHub latency (~6 s per gh call) and timed out 115 branch_merged detectors. A value
# outside 0 < s <= 120 (the tracker's MAX_CONFIGURED_S) is refused (E_TRACKER_CALL_TIMEOUT, before anything is touched), never silently dropped by the tracker.
# After bootout it waits for the service to disappear, retries bootstrap once, and exits non-zero unless health answers 200 within
# KY_HEALTH_WAIT_S (default 60) — the tracker is never left down silently.
set -euo pipefail
umask 077
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; RUN="$KY_ROOT/run"
mkdir -p "$RUN" "$KY_ROOT/bin" "$RUN/reviews" "$RUN/verdicts" "$RUN/claims" "$RUN/ops" "$HOME/Library/LaunchAgents"
LABEL=com.madhav.kalayantra.tracker; PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"; PY=/opt/homebrew/bin/python3
KY_SOURCE_REPO="${KY_SOURCE_REPO:-/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign}"
MODEL_REL="00_ARCHITECTURE/control/kalayantra/plan_model.json"; MODEL="$KY_SOURCE_REPO/$MODEL_REL"
FLEET_REL="00_ARCHITECTURE/briefs/kalayantra/fleet"
die() { echo "install_tracker: $1: $2" >&2; exit "${3:-1}"; }
if [ "${1:-}" = "--stop" ]; then launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true; rm -f "$PLIST"; echo "tracker stopped"; exit 0; fi
CALL_TIMEOUT_S="${PRAVAHA_CALL_TIMEOUT_S:-20}"
[[ "$CALL_TIMEOUT_S" =~ ^[0-9]+(\.[0-9]+)?$ ]] && awk -v v="$CALL_TIMEOUT_S" 'BEGIN { exit !(v > 0 && v <= 120) }' \
  || die E_TRACKER_CALL_TIMEOUT "PRAVAHA_CALL_TIMEOUT_S='$CALL_TIMEOUT_S' rejected (need 0 < seconds <= 120, the tracker's MAX_CONFIGURED_S)"
# Source check (runs before the package selection, snapshot, plist or tracker is touched): the live model must come from a current checkout of origin/main.
[ -f "$MODEL" ] || die E_TRACKER_SOURCE_MISSING "plan model missing: $MODEL (KY_SOURCE_REPO=$KY_SOURCE_REPO)"
git -C "$KY_SOURCE_REPO" rev-parse --git-dir >/dev/null 2>&1 || die E_TRACKER_SOURCE_MISSING "$KY_SOURCE_REPO is not a git checkout"
git -C "$KY_SOURCE_REPO" fetch -q origin main || die E_TRACKER_SOURCE_FETCH "cannot refresh origin/main in $KY_SOURCE_REPO"
git -C "$KY_SOURCE_REPO" merge-base --is-ancestor HEAD origin/main \
  || die E_TRACKER_SOURCE_DIVERGED "HEAD of $KY_SOURCE_REPO is not an ancestor of origin/main"
BEHIND="$(git -C "$KY_SOURCE_REPO" rev-list --count HEAD..origin/main)" || die E_TRACKER_SOURCE_FETCH "cannot count commits behind origin/main"
[ "$BEHIND" -le "${KY_STALE_MAX_COMMITS:-20}" ] \
  || die E_TRACKER_SOURCE_STALE "$KY_SOURCE_REPO is $BEHIND commits behind origin/main (limit ${KY_STALE_MAX_COMMITS:-20}); sync it first"
MODEL_BEHIND="$(git -C "$KY_SOURCE_REPO" rev-list --count HEAD..origin/main -- "$MODEL_REL")" || die E_TRACKER_SOURCE_FETCH "cannot count model commits"
[ "$MODEL_BEHIND" -le "${KY_MODEL_MAX_COMMITS:-3}" ] \
  || die E_TRACKER_MODEL_STALE "plan model in $KY_SOURCE_REPO is $MODEL_BEHIND model commits behind origin/main (limit ${KY_MODEL_MAX_COMMITS:-3}); sync it first"
# Run from a fleet_live copy without bin/, the wrappers are taken from the source checkout's fleet directory (2026-10-21).
if [ -z "${KY_WRAPPER_SRC:-}" ] && [ ! -f "$(dirname "${BASH_SOURCE[0]}")/bin/ky" ]; then
  KY_WRAPPER_SRC="$KY_SOURCE_REPO/$FLEET_REL"
  [ -f "$KY_WRAPPER_SRC/bin/ky" ] && [ -f "$KY_WRAPPER_SRC/bin/kybrief" ] || die E_TRACKER_NO_WRAPPERS "no bin/ky beside this script and none under $KY_WRAPPER_SRC"
fi
if [ "${1:-}" = "--gov" ]; then [ $# -eq 2 ] || { echo "usage: --gov <package-parent-dir>"; exit 2; }; GOV="$2"; printf '%s\n' "$GOV" > "$RUN/TRACKER_GOV"
elif [ -s "$RUN/TRACKER_GOV" ]; then GOV="$(cat "$RUN/TRACKER_GOV")"
else echo "Select the reviewed tracker package explicitly: $0 --gov <dir containing pravaha_tracker/>"; exit 1; fi
[ -d "$GOV/pravaha_tracker" ] || { echo "tracker package not found under $GOV"; exit 1; }
# The tracker and the `ky` CLI run from a SNAPSHOT of the selected package ($KY_ROOT/tracker_live), so an edit in the working
# tree (B-1b is developed there) can never break the running control plane. Re-run this installer to adopt a new package.
LIVE="$KY_ROOT/tracker_live"; rm -rf "$LIVE.new"; mkdir -p "$LIVE.new"
rsync -a --exclude '__pycache__' "$GOV/pravaha_tracker" "$LIVE.new/"; rm -rf "$LIVE.old"; [ -d "$LIVE" ] && mv "$LIVE" "$LIVE.old"; mv "$LIVE.new" "$LIVE"
$PY -c "import json,sys; json.load(open(sys.argv[1]))" "$MODEL"
touch "$RUN/EVENTS.jsonl"
# wrappers: begin — ky and kybrief are static, reviewed files (bin/ beside this script); installing them is a byte copy.
HERE="${KY_WRAPPER_SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)}"
for w in ky kybrief; do install -m 0755 "$HERE/bin/$w" "$KY_ROOT/bin/$w"; done
# wrappers: end
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
    <key>PRAVAHA_REPO</key><string>$KY_SOURCE_REPO</string>
    <key>PRAVAHA_PGENV</key><string>/Users/Dev/.config/pravaha/pgenv.sh</string>
    <key>PRAVAHA_HOLD</key><string>$KY_ROOT/HOLD</string>
    <key>PRAVAHA_CALL_TIMEOUT_S</key><string>$CALL_TIMEOUT_S</string>
    <key>PYTHONUNBUFFERED</key><string>1</string>
  </dict>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/><key>ProcessType</key><string>Background</string><key>ThrottleInterval</key><integer>2</integer>
  <key>StandardOutPath</key><string>$RUN/tracker.log</string><key>StandardErrorPath</key><string>$RUN/tracker.log</string>
</dict></plist>
EOF
UIDD="gui/$(id -u)"; POLL="${KY_POLL_S:-1}"
loaded() { launchctl print "$UIDD/$LABEL" >/dev/null 2>&1; }
unload_and_wait() {   # bootout is asynchronous: wait until the service is really gone before bootstrapping again
  launchctl bootout "$UIDD/$LABEL" 2>/dev/null || true
  for _ in $(seq 1 "${KY_BOOTOUT_WAIT_S:-30}"); do loaded || return 0; sleep "$POLL"; done
  ! loaded
}
unload_and_wait || die E_TRACKER_BOOTOUT "service $LABEL still loaded after ${KY_BOOTOUT_WAIT_S:-30}s; tracker NOT restarted"
if ! launchctl bootstrap "$UIDD" "$PLIST"; then
  echo "install_tracker: bootstrap failed; retrying once" >&2
  unload_and_wait || die E_TRACKER_BOOTOUT "service $LABEL still loaded before the bootstrap retry; tracker is DOWN"
  sleep "$POLL"
  launchctl bootstrap "$UIDD" "$PLIST" || die E_TRACKER_BOOTSTRAP "launchctl bootstrap failed twice; tracker is DOWN"
fi
launchctl enable "$UIDD/$LABEL"
UP=0
for _ in $(seq 1 "${KY_HEALTH_WAIT_S:-60}"); do curl -fs -m 3 http://127.0.0.1:8767/api/health >/dev/null 2>&1 && { UP=1; break; }; sleep "$POLL"; done
[ "$UP" = 1 ] || die E_TRACKER_DOWN "no health 200 within ${KY_HEALTH_WAIT_S:-60}s; tracker is DOWN (see $RUN/tracker.log)"
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
