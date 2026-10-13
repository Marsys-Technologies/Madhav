#!/bin/bash
# kyctl.sh — install, start, stop and observe the KĀLA-YANTRA v3 launchd loops (relaunch plan §4a.2, §10, §13).
#
#   kyctl.sh status
#   kyctl.sh install
#   kyctl.sh start   <loop> [--clear-stop]
#   kyctl.sh stop    <loop>
#   kyctl.sh restart <loop> [--clear-stop]
#   kyctl.sh uninstall
#   <loop> = dispatcher | planner | conductor | veto | all
#
# install   renders fleet/launchd/*.plist into ${KY_LAUNCHAGENTS_DIR:-~/Library/LaunchAgents}; idempotent;
#           starts nothing. A rendered plist never authorises a run: the controllers also need the durable
#           `enabled` switch ($KY_RUN/loops/<loop>.json), which only `start` sets, after its guards.
#           The planner, conductor and veto plists carry KY_SOURCE_REPO (the git checkout kyveto.py compares the
#           owner-decisions blob in), rendered from $KY_SOURCE_REPO, default the campaign checkout B-2 creates.
# start     idempotent. Each guard refuses by name (stderr `kyctl: REFUSED <loop>: <reason> — …`, exit 2).
#           --clear-stop removes ONLY that loop's STOP file, and only once every other guard has passed.
#           The veto loop is admitted like the model loops: an installation receipt of mode bootstrap or final
#           AND a passing kyversion.sh in the matching mode (`--bootstrap` for a bootstrap receipt, none for a
#           final one); a receipt of any other mode, an unreadable one, and a missing or failing kyversion.sh
#           refuse. (kyloop.py repeats the same gate itself, at start-up and whenever the receipt changes.)
# stop      creates STOP_<loop>, turns the switch off, boots the job out and confirms it is gone (else exit 1).
#           "Gone" includes the child its controller recorded: while that child is alive, pending or cannot be
#           judged, the stop is NOT reported as confirmed — a loaded-or-not launchd job is not the whole loop.
# restart   stop + start; refuses when a STOP file it did not create is present (unless --clear-stop).
# status    one line per loop from what was observed; `running` only when launchctl reported a pid and that
#           pid is alive; anything not observed is `unknown`. Always exits 0. Per loop it also reports
#             child=<none|pending|alive|survivors|gone|unknown> child_pid=<pid|->   the child its controller
#                       recorded, judged by pid + process-start identity and its process group (expected-child
#                       liveness; `waiting=` is the legitimate waiting state when there is none)
#             bundle=<receipt mode>:<manifest digest or receipt-<sha>, 12 hex> bundle_age_s=<n>   the authorised
#                       bundle the controller last VERIFIED (kyversion.sh passed), or `unknown`
#             test_hooks=<none|active>   whether that controller runs with a test hook set
#           The veto line also carries what its controller recorded at its last tick (veto_pending,
#           veto_next_deadline, veto_last_tick).
#
# The veto loop is stopped and observed here (`kyctl.sh stop veto`, `kyctl.sh status`) or through the owner's
# command queue: its running controller (kyloop.py veto) applies a queued `status`, `loops stop veto`, `loops
# status veto` and `decide` addressed to the veto role itself, before each tick; `veto <decision-id>` is settled
# by the veto handler. A veto loop that is not running applies nothing — then only this script stops it.
#
# Never removes $KY_ROOT/HOLD or $KY_RUN/HOLD_MERGES. Every launchctl call goes through ${KY_LAUNCHCTL}.
# Exit: 0 ok · 1 action failed or unconfirmed · 2 refused · 64 usage · 77 run as root.
set -euo pipefail

usage() {
  echo "usage: kyctl.sh status | install | uninstall | start <loop> [--clear-stop] | stop <loop> | restart <loop> [--clear-stop]" >&2
  echo "       <loop> = dispatcher | planner | conductor | veto | all" >&2
  echo "       the veto loop: stopped here, or by a queued command its running controller applies (\`status\`, \`loops stop|status veto\`, \`decide\`); \`veto <decision-id>\` is settled by the veto handler" >&2
  exit 64
}

UID_N="$(/usr/bin/id -u)"
if [ "$UID_N" = "0" ] || [ "${KY_TEST_ASSUME_ROOT:-0}" = "1" ]; then
  echo "kyctl: refusing to run as root (these are per-user launchd agents)" >&2
  exit 77
fi

HERE="$(cd "$(dirname "$0")" && pwd)"
HOME_DIR="${HOME:?HOME is required}"
USER_NAME="${USER:-$(/usr/bin/id -un)}"
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
KY_RUN="${KY_RUN:-$KY_ROOT/run}"
KY_FLEET="${KY_FLEET:-$KY_ROOT/fleet_live}"
KY_SCRATCH="${KY_SCRATCH:-/Users/Dev/scratch.noindex/claude/madhav/$(/bin/date +%Y%m%d)-kalayantra-v3}"
CLAUDE_BIN="${CLAUDE_BIN:-/Users/Dev/.local/bin/claude}"
KY_SOURCE_REPO="${KY_SOURCE_REPO:-/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign}"
GIT="${KY_GIT:-/usr/bin/git}"
LAUNCHCTL="${KY_LAUNCHCTL:-/bin/launchctl}"
LA_DIR="${KY_LAUNCHAGENTS_DIR:-$HOME_DIR/Library/LaunchAgents}"
TEMPLATES="$HERE/launchd"
DOMAIN="gui/$UID_N"
LOOPS="dispatcher planner conductor veto"
CONTROL_MODULES="kyaction.py kycommands.py kyveto.py"   # kyloop.py imports these from its own directory
PY=/opt/homebrew/bin/python3
if [ ! -x "$PY" ]; then PY="$(command -v python3 || true)"; fi
if [ -z "$PY" ]; then echo "kyctl: python3 not found" >&2; exit 1; fi
CONFIRM_SLEEP="$(/usr/bin/awk -v s="${KY_LOOP_SLEEP_SCALE:-1}" 'BEGIN { v = 0.25 * s; if (v <= 0) v = 0.25; printf "%.3f", v }')"

label_of() { echo "in.marsys.kalayantra.$1"; }
plist_of() { echo "$LA_DIR/$(label_of "$1").plist"; }
refuse()   { echo "kyctl: REFUSED $1: $2 — $3" >&2; }
present()  { if [ -e "$1" ]; then echo present; else echo absent; fi; }
have()     { if [ -e "$1" ]; then echo present; else echo unavailable; fi; }

# Read-only JSON observations (stdlib only). Prints one line; an unreadable input prints `unknown`.
kyjson() {
  "$PY" - "$@" <<'PYEOF' 2>/dev/null || echo "unknown"
import json, os, sys, time, calendar
op, args = sys.argv[1], sys.argv[2:]
def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)
if op == "receipt-mode":
    if not os.path.exists(args[0]):
        print("missing")
    else:
        d = load(args[0])
        m = d.get("mode") if isinstance(d, dict) else None
        print(m if isinstance(m, str) and m.replace("_", "").replace("-", "").isalnum() else "unreadable")
elif op == "last-run":
    d, role = args
    names = sorted(n[:-5] for n in os.listdir(d) if n.startswith(role + "-") and n.endswith(".json")) if os.path.isdir(d) else []
    if not names:               # run ids sort by stem: <ROLE>-<ts> before <ROLE>-<ts>-02
        print("none -")
    else:
        try:
            rec = load(os.path.join(d, names[-1] + ".json"))
            p = rec.get("progressed")
            state = "in-progress" if not rec.get("ended_at") else ("true" if p is True else "false" if p is False else "unknown")
        except Exception:
            state = "unknown"
        print(names[-1], state)
elif op == "loop-state":
    p = os.path.join(args[0], "loops", args[1] + ".json")
    if not os.path.exists(p):
        print("unset - - - - - unknown - -")
    else:
        d = load(p)
        en = d.get("enabled")
        br = d.get("breaker") if isinstance(d.get("breaker"), dict) else None
        ctl = d.get("controller") if isinstance(d.get("controller"), dict) else {}
        def age_of(text):
            try:
                return int(time.time() - calendar.timegm(time.strptime(text, "%Y-%m-%dT%H:%M:%SZ")))
            except Exception:
                return "-"
        np = d.get("no_progress_count")
        b = d.get("bundle") if isinstance(d.get("bundle"), dict) else {}
        hexes = lambda v: isinstance(v, str) and len(v) >= 12 and all(c in "0123456789abcdef" for c in v)
        mode = b.get("receipt_mode") if b.get("receipt_mode") in ("bootstrap", "final") else None
        if mode and hexes(b.get("manifest_digest")):
            bundle = "%s:%s" % (mode, b["manifest_digest"][:12])
        elif mode and hexes(b.get("receipt_sha256")):
            bundle = "%s:receipt-%s" % (mode, b["receipt_sha256"][:12])
        else:
            bundle = "unknown"
        print("true" if en is True else "false" if en is False else "unset",
              np if isinstance(np, int) and not isinstance(np, bool) else "-",
              "-" if br is None else ("open" if br.get("open") else "closed"),
              str(d.get("waiting") or "-").replace(" ", "_"), age_of(d.get("last_iteration_at")), ctl.get("pid") or "-",
              bundle, age_of(b.get("verified_at")) if bundle != "unknown" else "-",
              "active" if d.get("test_hooks") else "none")
elif op == "veto-state":
    p = os.path.join(args[0], "loops", "veto.json")
    v = load(p).get("veto") if os.path.exists(p) else None
    if not isinstance(v, dict):
        print("- - -")
    else:
        n = v.get("pending")
        print(n if isinstance(n, int) and not isinstance(n, bool) else "-",
              str(v.get("next_deadline") or "-").replace(" ", "_"), str(v.get("last_tick_at") or "-").replace(" ", "_"))
else:
    sys.exit(2)
PYEOF
}

# launchd observation for one loop → Q_LOADED (yes|no|unknown) Q_STATE (running|stopped|unknown) Q_PID Q_LAST_EXIT
lc_query() {
  local label out rc state pid last
  label="$(label_of "$1")"
  Q_LOADED=unknown; Q_STATE=unknown; Q_PID=-; Q_LAST_EXIT=-
  if [ ! -x "$LAUNCHCTL" ]; then return 0; fi
  rc=0
  out="$("$LAUNCHCTL" print "$DOMAIN/$label" 2>&1)" || rc=$?
  if [ "$rc" -ne 0 ]; then
    case "$out" in
      *"Could not find service"*) Q_LOADED=no; Q_STATE=stopped ;;
    esac
    return 0
  fi
  state="$(/usr/bin/sed -n '/^[[:space:]]*state = /{s/^[[:space:]]*state = //p;q;}' <<<"$out")"
  pid="$(/usr/bin/sed -n '/^[[:space:]]*pid = [0-9][0-9]*$/{s/^[[:space:]]*pid = //p;q;}' <<<"$out")"
  last="$(/usr/bin/sed -n '/^[[:space:]]*last exit code = /{s/^[[:space:]]*last exit code = //p;q;}' <<<"$out")"
  if [ -z "$state" ]; then return 0; fi
  Q_LOADED=yes
  if [ -n "$last" ]; then Q_LAST_EXIT="${last// /_}"; fi
  if [ "$state" = "running" ]; then
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then Q_STATE=running; Q_PID="$pid"; fi
  elif [ "$state" = "not running" ]; then
    Q_STATE=stopped
  fi
  return 0
}

# The child a loop's controller recorded → "<state> <pid|-> <run id|->" (state: none|pending|alive|survivors|gone|
# unknown). kyloop.py judges it (pid + process-start identity, process group); without kyloop.py it is unknown.
child_of() {
  if [ "$1" = dispatcher ]; then echo "none - -"; return 0; fi     # kydispatch.py owns its own jobs
  if [ ! -f "$KY_FLEET/kyloop.py" ]; then echo "unknown - -"; return 0; fi
  "$PY" "$KY_FLEET/kyloop.py" admin child "$1" 2>/dev/null || echo "unknown - -"
}

cmd_install() {
  local loop label src dst tmp v
  if [ ! -d "$TEMPLATES" ]; then echo "kyctl: install failed: no templates at $TEMPLATES" >&2; return 1; fi
  for v in "$KY_ROOT" "$KY_RUN" "$KY_FLEET" "$KY_SCRATCH" "$HOME_DIR" "$CLAUDE_BIN" "$KY_SOURCE_REPO"; do
    case "$v" in /*) ;; *) echo "kyctl: install failed: not an absolute path: $v" >&2; return 1 ;; esac
  done
  mkdir -p "$LA_DIR" "$KY_SCRATCH/dispatcher" "$KY_SCRATCH/loops/planner" "$KY_SCRATCH/loops/conductor" "$KY_SCRATCH/loops/veto"
  for loop in $LOOPS; do
    label="$(label_of "$loop")"; src="$TEMPLATES/$label.plist"; dst="$(plist_of "$loop")"; tmp="$dst.tmp.$$"
    if [ ! -f "$src" ]; then echo "kyctl: install failed: missing template $src" >&2; return 1; fi
    if ! "$PY" - "$src" "$tmp" "KY_ROOT=$KY_ROOT" "KY_RUN=$KY_RUN" "KY_FLEET=$KY_FLEET" "KY_SCRATCH=$KY_SCRATCH" \
         "HOME=$HOME_DIR" "USER=$USER_NAME" "CLAUDE_BIN=$CLAUDE_BIN" "KY_SOURCE_REPO=$KY_SOURCE_REPO" <<'PYEOF'
import re, sys
from xml.sax.saxutils import escape
src, dst = sys.argv[1:3]
values = dict(a.split("=", 1) for a in sys.argv[3:])
sys.dont_write_bytecode = True
sys.path.insert(0, values["KY_FLEET"])
from kyloop import SYSTEM_PATH
values["SYSTEM_PATH"] = SYSTEM_PATH
def sub(m):
    if m.group(1) not in values:
        raise SystemExit("unknown placeholder @%s@" % m.group(1))
    return escape(values[m.group(1)])
with open(src, encoding="utf-8") as f:
    text = re.sub(r"@([A-Z_]+)@", sub, f.read())
with open(dst, "w", encoding="utf-8") as f:
    f.write(text)
PYEOF
    then rm -f "$tmp"; echo "kyctl: install failed: could not render $src" >&2; return 1; fi
    if ! /usr/bin/plutil -lint "$tmp" >/dev/null 2>&1; then
      rm -f "$tmp"; echo "kyctl: install failed: rendered $label.plist does not pass plutil -lint" >&2; return 1
    fi
    if [ -f "$dst" ] && /usr/bin/cmp -s "$tmp" "$dst"; then
      rm -f "$tmp"; echo "kyctl: install $loop: unchanged ($dst)"
    else
      mv "$tmp" "$dst"; echo "kyctl: install $loop: written ($dst) — nothing started; a loaded job keeps its old definition until restart"
    fi
  done
}

start_one() {   # start_one <loop> <clear-stop 0|1> → 0 started/already running · 1 failed · 2 refused
  local loop="$1" clear="$2" label plist stop mode logp verb rc m repo varg
  label="$(label_of "$loop")"; plist="$(plist_of "$loop")"; stop="$KY_RUN/STOP_$loop"
  if [ ! -f "$plist" ]; then refuse "$loop" plist-not-installed "$plist (run: kyctl.sh install)"; return 2; fi
  lc_query "$loop"
  if [ "$Q_STATE" = running ]; then echo "kyctl: start $loop: already running (pid $Q_PID)"; return 0; fi
  if [ "$Q_LOADED" = unknown ]; then refuse "$loop" launchd-state-unknown "launchctl could not be observed ($LAUNCHCTL)"; return 2; fi
  if [ -e "$stop" ] && [ "$clear" != 1 ]; then refuse "$loop" stop-file-present "$stop (pass --clear-stop to remove it)"; return 2; fi
  mode="$(kyjson receipt-mode "$KY_RUN/INSTALL_RECEIPT.json")"
  case "$loop" in
    dispatcher)
      if [ ! -f "$KY_FLEET/kydispatch.py" ]; then refuse "$loop" dispatcher-missing "$KY_FLEET/kydispatch.py"; return 2; fi
      case "$mode" in
        bootstrap|final) ;;
        missing) refuse "$loop" install-receipt-missing "$KY_RUN/INSTALL_RECEIPT.json (only an accepted receipt permits activation)"; return 2 ;;
        *) refuse "$loop" install-receipt-mode "mode is $mode; need bootstrap or final"; return 2 ;;
      esac ;;
    planner)
      case "$mode" in
        bootstrap|final) ;;
        missing) refuse "$loop" install-receipt-missing "$KY_RUN/INSTALL_RECEIPT.json"; return 2 ;;
        *) refuse "$loop" install-receipt-mode "mode is $mode; need bootstrap or final"; return 2 ;;
      esac
      if [ -e "$KY_RUN/WAVE_B_DONE" ]; then refuse "$loop" wave-b-done "$KY_RUN/WAVE_B_DONE is present"; return 2; fi ;;
    conductor)
      if [ "$mode" != final ]; then refuse "$loop" install-receipt-not-final "INSTALL_RECEIPT.json mode is $mode; the conductor needs final"; return 2; fi
      if [ ! -f "$KY_RUN/OWNER_RESUME.json" ]; then refuse "$loop" owner-resume-missing "$KY_RUN/OWNER_RESUME.json"; return 2; fi ;;
    veto)
      # the same gate as the model loops: a receipt of mode bootstrap|final AND a passing kyversion.sh in that mode
      case "$mode" in
        bootstrap) varg="--bootstrap" ;;
        final) varg="" ;;
        missing) refuse "$loop" install-receipt-missing "$KY_RUN/INSTALL_RECEIPT.json (the veto handler runs only from an accepted installation)"; return 2 ;;
        unknown|unreadable) refuse "$loop" install-receipt-unreadable "$KY_RUN/INSTALL_RECEIPT.json cannot be read, or states no usable mode"; return 2 ;;
        *) refuse "$loop" install-receipt-mode "mode is $mode; need bootstrap or final"; return 2 ;;
      esac
      if [ ! -f "$KY_FLEET/kyversion.sh" ]; then refuse "$loop" kyversion-missing "$KY_FLEET/kyversion.sh (the installed bundle cannot be verified)"; return 2; fi
      rc=0
      if [ -n "$varg" ]; then
        /bin/bash "$KY_FLEET/kyversion.sh" "$varg" >/dev/null 2>&1 || rc=$?
      else
        /bin/bash "$KY_FLEET/kyversion.sh" >/dev/null 2>&1 || rc=$?
      fi
      if [ "$rc" -ne 0 ]; then refuse "$loop" kyversion-failed "kyversion.sh $varg exited $rc for a $mode receipt"; return 2; fi
      # what the job will really be given: the KY_SOURCE_REPO of the INSTALLED plist, not this shell's variable
      repo="$(/usr/bin/plutil -extract EnvironmentVariables.KY_SOURCE_REPO raw -o - "$plist" 2>/dev/null || true)"
      if [ -z "$repo" ]; then refuse "$loop" source-repo-missing "the installed plist carries no KY_SOURCE_REPO (run: kyctl.sh install)"; return 2; fi
      if [ ! -d "$repo" ]; then refuse "$loop" source-repo-missing "$repo is not a directory (kyveto.py compares the owner-decisions blob there)"; return 2; fi
      if [ "$("$GIT" -C "$repo" rev-parse --is-inside-work-tree 2>/dev/null || true)" != true ]; then
        refuse "$loop" source-repo-missing "$repo is not a git work tree"; return 2
      fi ;;
  esac
  if [ ! -f "$KY_FLEET/kyloop.py" ]; then refuse "$loop" kyloop-missing "$KY_FLEET/kyloop.py (it owns the enabled switch)"; return 2; fi
  if [ "$loop" != dispatcher ]; then
    for m in $CONTROL_MODULES; do
      if [ ! -f "$KY_FLEET/$m" ]; then refuse "$loop" control-module-missing "$KY_FLEET/$m (kyloop.py is wired to it)"; return 2; fi
    done
  fi
  # every guard has passed: only now clear the STOP file, enable, and hand over to launchd
  if [ -e "$stop" ]; then rm -f "$stop"; echo "kyctl: start $loop: cleared $stop"; fi
  if ! "$PY" "$KY_FLEET/kyloop.py" admin enable "$loop" --reason "kyctl start" --by "kyctl:$USER_NAME"; then
    echo "kyctl: start $loop: failed to record the enabled switch" >&2; return 1
  fi
  logp="$(/usr/bin/plutil -extract StandardOutPath raw -o - "$plist" 2>/dev/null || true)"
  if [ -n "$logp" ]; then mkdir -p "$(dirname "$logp")"; fi
  rc=0
  if [ "$Q_LOADED" = yes ]; then
    verb=kickstarted; "$LAUNCHCTL" kickstart "$DOMAIN/$label" || rc=$?
  else
    verb=bootstrapped; "$LAUNCHCTL" bootstrap "$DOMAIN" "$plist" || rc=$?
  fi
  if [ "$rc" -ne 0 ]; then
    "$PY" "$KY_FLEET/kyloop.py" admin disable "$loop" --reason "kyctl start failed: launchctl rc=$rc" --by "kyctl:$USER_NAME" || true
    echo "kyctl: start $loop: launchctl failed (rc=$rc); switch turned off again" >&2; return 1
  fi
  lc_query "$loop"
  echo "kyctl: start $loop: $verb; observed state=$Q_STATE pid=$Q_PID"
  return 0
}

stop_one() {    # stop_one <loop> → 0 confirmed gone · 1 unconfirmed
  local loop="$1" label stop i child cpid rest
  label="$(label_of "$loop")"; stop="$KY_RUN/STOP_$loop"
  if [ ! -d "$KY_RUN" ]; then echo "kyctl: stop $loop: no run directory $KY_RUN" >&2; return 1; fi
  if [ ! -e "$stop" ]; then
    printf '%s kyctl stop by %s\n' "$(/bin/date -u +%Y-%m-%dT%H:%M:%SZ)" "$USER_NAME" > "$stop.tmp.$$"
    mv "$stop.tmp.$$" "$stop"
  fi
  if [ -f "$KY_FLEET/kyloop.py" ]; then
    if ! "$PY" "$KY_FLEET/kyloop.py" admin disable "$loop" --reason "kyctl stop" --by "kyctl:$USER_NAME"; then
      echo "kyctl: stop $loop: warning — enabled switch not written (the STOP file still stops the loop)" >&2
    fi
  else
    echo "kyctl: stop $loop: warning — kyloop.py unavailable, enabled switch not written (the STOP file still stops the loop)" >&2
  fi
  if [ -x "$LAUNCHCTL" ]; then "$LAUNCHCTL" bootout "$DOMAIN/$label" >/dev/null 2>&1 || true; fi
  i=0; child=unknown; cpid=-
  while [ "$i" -lt 40 ]; do
    lc_query "$loop"
    if [ "$Q_LOADED" = no ]; then
      # the launchd job is gone — but a loop is stopped only when the child its controller recorded is gone too
      read -r child cpid rest <<<"$(child_of "$loop") - -"
      case "$child" in
        none|gone) echo "kyctl: stop $loop: STOP file present, job not loaded, no recorded child left (confirmed)"; return 0 ;;
      esac
    fi
    i=$((i + 1)); /bin/sleep "$CONFIRM_SLEEP"
  done
  if [ "$Q_LOADED" = no ]; then
    echo "kyctl: stop $loop: stop-unconfirmed — the job is not loaded, but the child its controller recorded is $child (pid $cpid); STOP file left in place" >&2
  else
    echo "kyctl: stop $loop: stop-unconfirmed — launchd still reports the job (loaded=$Q_LOADED state=$Q_STATE); STOP file left in place" >&2
  fi
  return 1
}

restart_one() {
  local loop="$1" clear="$2" stop="$KY_RUN/STOP_$1"
  if [ -e "$stop" ] && [ "$clear" != 1 ]; then
    refuse "$loop" stop-file-present "$stop was set before this restart; restart does not clear a STOP it did not create (pass --clear-stop)"
    return 2
  fi
  stop_one "$loop" || return 1
  start_one "$loop" 1
}

cmd_uninstall() {
  local loop rc=0
  for loop in $LOOPS; do
    lc_query "$loop"
    if [ "$Q_LOADED" = yes ]; then refuse "$loop" still-loaded "stop it first: kyctl.sh stop $loop"; rc=2; fi
    if [ "$Q_LOADED" = unknown ] && [ -f "$(plist_of "$loop")" ]; then refuse "$loop" launchd-state-unknown "cannot confirm the job is not loaded"; rc=2; fi
  done
  if [ "$rc" -ne 0 ]; then return "$rc"; fi
  for loop in $LOOPS; do
    if [ -f "$(plist_of "$loop")" ]; then rm -f "$(plist_of "$loop")"; echo "kyctl: uninstall $loop: removed $(plist_of "$loop")"; else echo "kyctl: uninstall $loop: not installed"; fi
  done
}

cmd_status() {
  local loop plist pl state enabled np breaker waiting age cpid last progressed stop ctl n f rest extra vp vd vt m answered helpers
  local bundle bage hooks child childpid
  for loop in $LOOPS; do
    plist="$(plist_of "$loop")"
    lc_query "$loop"
    if [ -f "$plist" ]; then pl=installed; else pl=missing; fi
    if [ "$Q_LOADED" = unknown ]; then state=unknown
    elif [ "$pl" = missing ] && [ "$Q_LOADED" = no ]; then state=not-installed
    else state="$Q_STATE"; fi
    read -r enabled np breaker waiting age cpid bundle bage hooks rest <<<"$(kyjson loop-state "$KY_RUN" "$loop") - - - - - unknown - -"
    read -r child childpid rest <<<"$(child_of "$loop") - -"
    extra=""
    if [ "$loop" = dispatcher ]; then
      last=n/a; progressed=n/a; ctl=n/a
    else
      if [ "$loop" = veto ]; then        # the veto role launches no model: it has ticks, not runs
        last=n/a; progressed=n/a
        read -r vp vd vt rest <<<"$(kyjson veto-state "$KY_RUN") - - -"
        extra=" veto_pending=$vp veto_next_deadline=$vd veto_last_tick=$vt"
      else
        read -r last progressed rest <<<"$(kyjson last-run "$KY_RUN/loops/$loop" "$(printf '%s' "$loop" | /usr/bin/tr '[:lower:]' '[:upper:]')") - -"
      fi
      if [ "$state" != running ]; then ctl=-
      elif [ "$cpid" = "$Q_PID" ]; then ctl=match
      else ctl=mismatch; fi
    fi
    if [ -e "$KY_RUN/STOP_$loop" ]; then stop=yes; else stop=no; fi
    echo "$loop state=$state pid=$Q_PID last_exit=$Q_LAST_EXIT loaded=$Q_LOADED plist=$pl enabled=$enabled stop=$stop controller=$ctl waiting=$waiting last_iteration_age_s=$age last_run=$last progressed=$progressed no_progress=$np breaker=$breaker child=$child child_pid=$childpid bundle=$bundle bundle_age_s=$bage test_hooks=$hooks$extra"
  done
  n=0; answered=0
  if [ -d "$KY_RUN/awaiting" ]; then
    for f in "$KY_RUN/awaiting"/*.json; do
      if [ ! -e "$f" ]; then continue; fi
      case "$f" in
        *.owner_decision.json) answered=$((answered + 1)) ;;   # the owner's recorded answer beside an item, not an item
        *) n=$((n + 1)) ;;
      esac
    done
  fi
  echo "flags HOLD=$(present "$KY_ROOT/HOLD") HOLD_MERGES=$(present "$KY_RUN/HOLD_MERGES") WAVE_B_DONE_file=$(present "$KY_RUN/WAVE_B_DONE") awaiting_open=$n owner_decisions=$answered"
  helpers="helpers kyloop.py=$(have "$KY_FLEET/kyloop.py")"
  for m in $CONTROL_MODULES; do helpers="$helpers $m=$(have "$KY_FLEET/$m")"; done
  echo "$helpers kydispatch.py=$(have "$KY_FLEET/kydispatch.py") kyversion.sh=$(have "$KY_FLEET/kyversion.sh") kygate.sh=$(have "$KY_FLEET/kygate.sh") kylock.sh=$(have "$KY_FLEET/kylock.sh") kynotify.sh=$(have "$KY_FLEET/kynotify.sh")"
  return 0
}

for_loops() {   # for_loops <fn> <loop|all> [extra] → worst exit code
  local fn="$1" target="$2" extra="${3:-}" loop rc worst=0
  case "$target" in
    all) set -- $LOOPS ;;
    dispatcher|planner|conductor|veto) set -- "$target" ;;
    *) usage ;;
  esac
  for loop in "$@"; do
    rc=0
    if [ -n "$extra" ]; then "$fn" "$loop" "$extra" || rc=$?; else "$fn" "$loop" || rc=$?; fi
    if [ "$rc" -gt "$worst" ]; then worst="$rc"; fi
  done
  return "$worst"
}

cmd="${1:-}"
if [ -z "$cmd" ]; then usage; fi
shift
case "$cmd" in
  status)    if [ "$#" -ne 0 ]; then usage; fi; cmd_status ;;
  install)   if [ "$#" -ne 0 ]; then usage; fi; cmd_install ;;
  uninstall) if [ "$#" -ne 0 ]; then usage; fi; cmd_uninstall ;;
  start|stop|restart)
    target=""; clear=0
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --clear-stop) if [ "$cmd" = stop ]; then usage; fi; clear=1 ;;
        -*) usage ;;
        *) if [ -n "$target" ]; then usage; fi; target="$1" ;;
      esac
      shift
    done
    if [ -z "$target" ]; then usage; fi
    case "$cmd" in
      start)   for_loops start_one "$target" "$clear" ;;
      stop)    for_loops stop_one "$target" ;;
      restart) for_loops restart_one "$target" "$clear" ;;
    esac ;;
  *) usage ;;
esac
