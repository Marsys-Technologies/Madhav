"""KV3-B-INSTALL: install.sh (relaunch plan v2.7 §14 B-2, D-9; rulings P6, P9, P29, P39, P40).

Nothing here touches the real launchctl, ~/Library/LaunchAgents, the real `claude`, the real `ps` listing or
/Users/Dev/kalayantra. Every test builds its own world under pytest's basetemp:

  * a source checkout S (a real git repository, two commits: the approved source commit and the components
    commit) holding fake fleet components — each external program install.sh runs (kymanifest.py, kyctl.sh,
    kyloop.py, kyqualify.py, preflight.sh, kyversion.sh, bin/ky) is a test double committed as a component;
  * a bootstrap manifest M, a main review record and one review record per bound area, written by the test;
  * test doubles outside S for launchctl (it starts a fake tracker process this test owns), ps, gh and claude,
    reached only through the hook variables install.sh accepts for a non-real ROOT.

The fake `ps` is essential, not a convenience: the real listing on a machine that still runs the legacy
supervisors would (rightly) make install.sh refuse. No test signals a process it did not start itself.
Behaviour switches for the doubles live in one JSON file (`control.json`) per world; every call a double
receives is appended to `calls.log`.
"""
import hashlib
import json
import os
import plistlib
import pwd
import shutil
import signal
import socket
import stat
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
INSTALL = FLEET / "install.sh"
sys.dont_write_bytecode = True
sys.path.insert(0, str(FLEET))

import kyaction  # noqa: E402

K = "00_ARCHITECTURE/briefs/kalayantra"
FL = K + "/fleet"
TRK = "platform/scripts/governance/pravaha_tracker"
STAGED = "00_ARCHITECTURE/control/kalayantra/STAGED_MODEL_ACTIONS_v2_2.json"
PLAN_MODEL = "00_ARCHITECTURE/control/kalayantra/plan_model.json"
ENTRYPOINTS = {"plan": K + "/KALAYANTRA_RELAUNCH_PLAN_v2_7.md",
               "cockpit_prompt": K + "/KALAYANTRA_V3_COCKPIT_PROMPT_v2_7.md",
               "owner_decisions": K + "/KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md",
               "strategy": K + "/KALAYANTRA_RELAUNCH_STRATEGY_v1_2.md",
               "surrogate_agent": ".claude/agents/kalayantra-owner-surrogate.md"}
LANES = ["sutradhara", "adhikarin", "v1", "v2", "v3"] + ["k%d" % i for i in range(1, 9)]
REAL_ROOT = "/Users/Dev/kalayantra"
REAL_CAMPAIGN = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"
TRACKER_LABEL = "com.madhav.kalayantra.tracker"
LOOPS = ("dispatcher", "planner", "conductor", "veto")
PYBIN = sys.executable


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


# --------------------------------------------------------------------------------------------- the test doubles
FAKE_KYMANIFEST = r'''#!@PYBIN@
import json, sys
argv = sys.argv[1:]
open("@CALLS@", "a").write(json.dumps({"tool": "kymanifest", "argv": argv}) + "\n")
control = json.load(open("@CONTROL@"))
if control.get("kymanifest_rc"):
    sys.stderr.write("refused: fake kymanifest\n")
    sys.exit(control["kymanifest_rc"])
manifest = json.load(open(argv[1]))
print(json.dumps({"ok": True, "manifest_sha256": manifest.get("manifest_sha256"), "components": len(manifest["components"])}))
'''

FAKE_KYLOOP = r'''#!@PYBIN@
import json, sys
argv = sys.argv[1:]
open("@CALLS@", "a").write(json.dumps({"tool": "kyloop", "argv": argv, "isolated": bool(sys.flags.isolated)}) + "\n")
if argv[:2] == ["admin", "launch-config"] and argv[2] in ("planner", "conductor"):
    print(json.dumps({"schema": "ky.launch_config/1", "role": argv[2], "model": "claude-opus-5-5"}))
    sys.exit(0)
sys.exit(64)
'''

FAKE_KYQUALIFY = r'''#!@PYBIN@
import json, os, sys
argv = sys.argv[1:]
control = json.load(open("@CONTROL@"))
open("@CALLS@", "a").write(json.dumps({"tool": "kyqualify", "argv": argv}) + "\n")


def opt(name):
    return argv[argv.index(name) + 1]


if argv[0] == "check":
    try:
        doc = json.load(open(argv[1]))
    except (OSError, ValueError):
        sys.exit(1)
    cfg = json.load(open(opt("--config")))
    ok = doc.get("result") == "PASS" and doc.get("role") == cfg["role"] and doc.get("context") == "launchd" \
        and "--require-context" in argv and opt("--require-context") == "launchd" and "--verify-evidence" in argv
    print(json.dumps({"check": "PASS" if ok else "REFUSED"}))
    sys.exit(0 if ok else 1)
if argv[0] == "qualify":
    cfg = json.load(open(opt("--config")))
    assert opt("--context") == "launchd"
    os.makedirs(opt("--evidence-dir"), exist_ok=True)
    result = control.get("qualify_result", "PASS")
    if control.get("qualify_require_control") and "--control" not in argv:
        result = "unknown"
    json.dump({"schema": "ky.qualification/1", "role": cfg["role"], "model": cfg["model"], "context": "launchd",
               "result": result}, open(opt("--out"), "w"))
    sys.exit(0 if result == "PASS" else 1)
sys.exit(64)
'''

FAKE_KYCTL = r'''#!/bin/bash
set -e
exec @PYBIN@ - "$@" <<'PYEOF'
import json, os, plistlib, sys
argv = sys.argv[1:]
seen = {k: os.environ[k] for k in ("KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SCRATCH", "KY_SOURCE_REPO", "CLAUDE_BIN",
                                   "KY_LAUNCHAGENTS_DIR", "KY_LAUNCHCTL", "KY_LOOP_SLEEP_SCALE") if k in os.environ}
open("@CALLS@", "a").write(json.dumps({"tool": "kyctl", "argv": argv, "env": seen}) + "\n")
control = json.load(open("@CONTROL@"))
if argv != ["install"]:
    sys.exit(64)
if control.get("kyctl_rc"):
    sys.exit(control["kyctl_rc"])
la = os.environ["KY_LAUNCHAGENTS_DIR"]
os.makedirs(la, exist_ok=True)
for loop in ("dispatcher", "planner", "conductor", "veto"):
    env = {k: os.environ[k] for k in ("KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SCRATCH", "KY_SOURCE_REPO", "CLAUDE_BIN")}
    if control.get("plist_hook"):
        env[control["plist_hook"]] = "0.1"
    doc = {"Label": "in.marsys.kalayantra." + loop, "ProgramArguments": ["/usr/bin/true"], "EnvironmentVariables": env}
    data = plistlib.dumps(doc)
    path = os.path.join(la, "in.marsys.kalayantra.%s.plist" % loop)
    if os.path.exists(path) and open(path, "rb").read() == data:
        continue
    open(path, "wb").write(data)
PYEOF
'''

FAKE_PREFLIGHT = r'''#!/bin/bash
exec @PYBIN@ - "$@" <<'PYEOF'
import json, os, sys
run = os.environ["KY_RUN"]
env = {k: os.environ[k] for k in ("KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SCRATCH", "KY_SOURCE_REPO", "CLAUDE_BIN", "PRAVAHA_URL")
       if k in os.environ}
open("@CALLS@", "a").write(json.dumps({"tool": "preflight", "argv": sys.argv[1:], "env": env,
                                        "receipt_present": os.path.exists(os.path.join(run, "INSTALL_RECEIPT.json"))}) + "\n")
control = json.load(open("@CONTROL@"))
if control.get("preflight_spoils_action"):       # another actor ends the record while the installation runs
    path = os.path.join(run, "actions", control["preflight_spoils_action"] + ".json")
    rec = json.load(open(path))
    rec.update(state="FAILED", result={"by": "someone else"}, completed_at="2026-10-12T00:00:00Z")
    json.dump(rec, open(path, "w"), indent=1)
sys.exit(control.get("preflight_rc", 0))
PYEOF
'''

FAKE_KYVERSION = r'''#!/bin/bash
exec @PYBIN@ - "$@" <<'PYEOF'
import json, os, sys
run = os.environ["KY_RUN"]
receipt = os.path.join(run, "INSTALL_RECEIPT.json")
doc = json.load(open(receipt)) if os.path.exists(receipt) else {}
open("@CALLS@", "a").write(json.dumps({"tool": "kyversion", "argv": sys.argv[1:], "receipt_present": bool(doc),
                                        "receipt_mode": doc.get("mode")}) + "\n")
control = json.load(open("@CONTROL@"))
rc = control.get("kyversion_rc", 0)
if rc:
    sys.stderr.write("kyversion: REFUSED B4: fake\n")
    sys.exit(rc)
if control.get("kyversion_stdout") is not None:
    print(control["kyversion_stdout"])
    sys.exit(0)
print("kyversion: OK mode=bootstrap manifest_sha256=%s authorises=bootstrap-only" % doc.get("manifest", {}).get("manifest_sha256"))
PYEOF
'''

FAKE_KY = r'''#!@PYBIN@
import json, os, sys, time
argv = sys.argv[1:]
keep = {k: v for k, v in os.environ.items() if k.startswith("PRAVAHA_") or k in ("KY_LANE", "KY_SCRATCH")}
open("@CALLS@", "a").write(json.dumps({"tool": "ky", "argv": argv, "env": keep}) + "\n")
control = json.load(open("@CONTROL@"))
events = os.environ.get("PRAVAHA_EVENTS")
if not events:
    sys.stderr.write("fake ky: live mode refused in a test\n")
    sys.exit(78)
if control.get("ky_fail_on") == argv[0]:
    sys.stderr.write("fake ky: refused\n")
    sys.exit(2)


def opt(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def append(ev):
    # cli.py write(): keys whose value is None or "" are dropped, `ts` is added, the stored event is printed
    ev = {k: v for k, v in ev.items() if v not in (None, "")}
    ev["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    with open(events, "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False, separators=(",", ":")) + "\n")
    after = control.get("ky_fail_after_append_of")
    if after and after in (ev.get("decision"), ev.get("item")):
        control.pop("ky_fail_after_append_of")
        json.dump(control, open("@CONTROL@", "w"))
        sys.stderr.write("fake ky: crashed after appending %s\n" % after)
        sys.exit(1)
    return ev


if argv[0] == "decide":
    out = append({"kind": "decision", "actor": opt("--as", "native"), "decision": argv[1],
                  "state": "delegated" if "--delegated" in argv else "decided", "outcome": opt("--outcome"),
                  "detail": opt("--detail")})
elif argv[0] in ("park", "block"):
    if control.get("ky_swallow"):
        print(json.dumps({"ok": True}))
        sys.exit(0)
    out = append({"kind": "item", "actor": opt("--as"), "item": argv[1], "state": "parked" if argv[0] == "park" else "blocked",
                  "detail": opt("--detail"), "evidence": None})
elif argv[0] == "release":
    # cli.py cmd_claim_lifecycle + claims.release_claim: the worker's record names item and claim_id; the claim must be
    # the item's latest claim event in the log and active; the released event is appended, then the record rewritten
    worker = os.environ.get("KY_LANE", "")
    path = os.path.join(os.path.dirname(events), "claims", worker + ".json")
    try:
        current = json.load(open(path))
        log = []
        for line in open(events):                  # claims._read: an unreadable line is skipped
            try:
                log.append(json.loads(line))
            except ValueError:
                continue
    except (OSError, ValueError) as exc:
        sys.stderr.write("refused: %s\n" % exc)
        sys.exit(2)
    if control.get("ky_release_noop"):
        sys.exit(0)
    last = next((e for e in reversed(log) if e.get("kind") == "claim" and e.get("item") == current.get("item")), None)
    if not last or last.get("claim_id") != current.get("claim_id") or last.get("worker_id") != worker \
            or last.get("state") not in ("acquired", "renewed"):
        sys.stderr.write("refused: claim is not active for this worker\n")
        sys.exit(2)
    out = dict(last, state="released", ts=time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()))
    if not control.get("ky_release_record_only"):
        with open(events, "a") as f:
            f.write(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    with open(path, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
else:
    sys.exit(2)
print(json.dumps(out, ensure_ascii=False))
'''

FAKE_KYBRIEF = r'''#!@PYBIN@
print("fake kybrief")
'''

FAKE_LAUNCHCTL = r'''#!@PYBIN@
import json, os, plistlib, signal, socket, subprocess, sys, time
argv = sys.argv[1:]
STATE = "@STATE@"
open("@CALLS@", "a").write(json.dumps({"tool": "launchctl", "argv": argv}) + "\n")
control = json.load(open("@CONTROL@"))
pidfile = os.path.join(STATE, "tracker.pid")
pending = os.path.join(STATE, "bootout.pending")


def current():
    try:
        pid = int(open(pidfile).read().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


verb = argv[0] if argv else ""
if verb == "print":
    if os.path.exists(pending):
        remaining = int(open(pending).read())
        if remaining:
            open(pending, "w").write(str(remaining - 1))
            print("%s = {\n\tstate = stopping\n}" % argv[1])
            sys.exit(0)
        os.unlink(pending)
    pid = current()
    if not pid:
        sys.stderr.write("Could not find service\n")
        sys.exit(113)
    print("%s = {\n\tstate = running\n\tpid = %d\n}" % (argv[1], pid))
elif verb == "bootout":
    if control.get("launchctl_bootout_pending_prints"):
        open(pending, "w").write(str(control["launchctl_bootout_pending_prints"]))
    pid = current()
    if control.get("launchctl_bootout_noop"):
        sys.exit(0)
    if pid:
        os.kill(pid, signal.SIGTERM)
        for _ in range(50):
            try:
                os.kill(pid, 0)
            except OSError:
                break
            time.sleep(0.1)
        os.unlink(pidfile)
        sys.exit(0)
    sys.exit(3)
elif verb == "bootstrap":
    if os.path.exists(pending):
        sys.exit(5)
    if control.get("launchctl_bootstrap_fail_once"):
        control.pop("launchctl_bootstrap_fail_once")
        json.dump(control, open("@CONTROL@", "w"))
        sys.exit(5)
    if control.get("launchctl_bootstrap_rc"):
        sys.exit(control["launchctl_bootstrap_rc"])
    if control.get("launchctl_bootstrap_noop"):
        sys.exit(0)
    with open(argv[2], "rb") as f:
        doc = plistlib.load(f)
    args = doc["ProgramArguments"]
    port = args[args.index("--port") + 1]
    events = doc.get("EnvironmentVariables", {}).get("PRAVAHA_EVENTS", "")
    child = subprocess.Popen([sys.executable, "@TRACKER@", port, events], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    open(pidfile, "w").write(str(child.pid))
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", int(port)), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.05)
elif verb == "enable":
    pass
else:
    sys.exit(64)
'''

FAKE_TRACKER = r'''#!@PYBIN@
import datetime, json, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

STARTED = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
EVENTS = sys.argv[2] if len(sys.argv) > 2 else ""


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        control = json.load(open("@CONTROL@"))
        if self.path != "/api/health" or control.get("health_status", 200) != 200:
            self.send_response(control.get("health_status", 404))
            self.end_headers()
            return
        # server.py: {"ok": tick age < 10, "version": …, **engine.health()}
        health = {"ok": True, "version": 3, "server_started_at": control.get("health_started_at", STARTED),
                  "engine_tick_age_s": 0.4, "db_proxy": False, "db_credentials": False, "power": "ac", "hold": False,
                  "event_log": {"path": control.get("health_events_path", EVENTS), "events": 0, "malformed": 0,
                                "exists": os.path.exists(EVENTS)},
                  "backup": None, "model_error": None, "detector_errors": [], "git_activity_age_s": None, "tick_errors": []}
        health.update(control.get("health_update", {}))
        for key in control.get("health_drop", []):
            health.pop(key, None)
        body = json.dumps(control.get("health", health)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
'''

FAKE_PS = r'''#!@PYBIN@
import json, os, sys
argv = sys.argv[1:]
control = json.load(open("@CONTROL@"))
open("@CALLS@", "a").write(json.dumps({"tool": "ps", "argv": argv}) + "\n")
if control.get("ps_fail"):
    sys.stderr.write("ps: fake failure\n")
    sys.exit(1)
if "-axo" in argv:
    nth = sum(1 for l in open("@CALLS@").read().splitlines() if '"tool": "ps"' in l and "-axo" in l)
    if control.get("ps_fail_from_listing") and nth >= control["ps_fail_from_listing"]:
        sys.stderr.write("ps: fake failure at listing %d\n" % nth)
        sys.exit(1)
    if control.get("ps_link_at_listing") and nth == control["ps_link_at_listing"][0]:
        victim = control["ps_link_at_listing"][1]          # the source changes under the installer after verification
        os.rename(victim, victim + ".moved")
        os.symlink(victim + ".moved", victim)
    lines = ["    1     0 /sbin/launchd", "  100     1 /usr/bin/something --harmless"] + list(control.get("ps_extra", []))
    if control.get("ps_garbage"):
        lines.append("this is not a process line")
    print("\n".join(lines))
    sys.exit(0)
os.execv("/bin/ps", ["/bin/ps"] + argv)
'''

FAKE_GH = r'''#!@PYBIN@
import json, sys
argv = sys.argv[1:]
open("@CALLS@", "a").write(json.dumps({"tool": "gh", "argv": argv}) + "\n")
control = json.load(open("@CONTROL@"))
if control.get("gh_rc"):
    sys.stderr.write("gh: fake failure\n")
    sys.exit(control["gh_rc"])
print(json.dumps(control.get("prs", [])))
'''

FAKE_GIT = r'''#!@PYBIN@
import json, os, shutil, sys
argv = sys.argv[1:]
control = json.load(open("@CONTROL@"))
rule = control.get("git_fail")                     # {"match": text in the joined arguments, "from_call": n, "rc": code}
if rule and rule["match"] in " ".join(argv):
    counter = os.path.join("@STATE@", "git_fail.count")
    n = int(open(counter).read()) + 1 if os.path.exists(counter) else 1
    open(counter, "w").write(str(n))
    if n >= rule.get("from_call", 1):
        if rule.get("remove"):                     # something the rollback will need is gone when the call fails
            shutil.rmtree(rule["remove"], ignore_errors=True)
        sys.stderr.write("fatal: fake git failure\n")
        sys.exit(rule.get("rc", 128))
os.execv("/usr/bin/git", ["/usr/bin/git"] + argv)
'''

FAKE_CLAUDE = '''#!/bin/sh
echo "%s (Claude Code)"
'''


def render(template, w):
    return (template.replace("@PYBIN@", PYBIN).replace("@CONTROL@", str(w.control_path)).replace("@CALLS@", str(w.calls_path))
            .replace("@STATE@", str(w.state)).replace("@TRACKER@", str(w.tools / "fake_tracker.py")))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def tree_state(path):
    """Everything under `path` — type, bytes hash, mode, mtime — so a test can prove nothing was written."""
    out = {}
    path = Path(path)
    if not path.exists():
        return out
    for dp, dns, fns in os.walk(path):
        dns.sort()
        for name in sorted(fns + dns):
            p = Path(dp) / name
            st = os.lstat(p)
            key = str(p.relative_to(path))
            if stat.S_ISLNK(st.st_mode):
                out[key] = ("link", os.readlink(p))
            elif stat.S_ISDIR(st.st_mode):
                out[key] = ("dir", stat.S_IMODE(st.st_mode), st.st_mtime_ns)
            else:
                out[key] = ("file", sha_file(p), stat.S_IMODE(st.st_mode), st.st_mtime_ns)
    return out


class World:
    """One isolated installation: ROOT, a source checkout S, a manifest M and the doubles install.sh may reach."""

    def __init__(self, base):
        self.base = Path(base)
        self.root = self.base / "kyroot"
        self.run = self.root / "run"
        self.wtroot = self.base / "wtroot"
        self.src = self.wtroot / "src"
        self.camp = self.wtroot / "kalayantra-campaign"
        self.la = self.base / "LaunchAgents"
        self.home = self.base / "home"
        self.scratch = self.base / "ky_scratch"
        self.tools = self.base / "tools"
        self.state = self.base / "fake_state"
        self.reviews = self.base / "reviews"
        self.manifest_path = self.base / "VERSIONS.bootstrap.json"
        self.control_path = self.state / "control.json"
        self.calls_path = self.state / "calls.log"
        self.port = free_port()
        self.url = "http://127.0.0.1:%d" % self.port
        for d in (self.wtroot, self.home, self.scratch, self.tools, self.state, self.reviews, self.run):
            d.mkdir(parents=True, exist_ok=True)
        self.control(claude_version="2.1.300")
        self.calls_path.write_text("")
        self.write_tools()
        self.m = None
        self.claim_files = {}

    # ---- doubles
    def control(self, **kw):
        cur = json.loads(self.control_path.read_text()) if self.control_path.exists() else {}
        cur.update(kw)
        for k in [k for k, v in cur.items() if v is None]:
            del cur[k]
        self.control_path.write_text(json.dumps(cur))

    def write_tools(self):
        for name, tpl in (("launchctl", FAKE_LAUNCHCTL), ("ps", FAKE_PS), ("gh", FAKE_GH), ("git", FAKE_GIT),
                          ("fake_tracker.py", FAKE_TRACKER)):
            p = self.tools / name
            p.write_text(render(tpl, self))
            p.chmod(0o755)
        self.write_claude("2.1.300")

    def write_claude(self, version):
        p = self.tools / "claude"
        p.write_text(FAKE_CLAUDE % version)
        p.chmod(0o755)

    def calls(self, tool=None):
        rows = [json.loads(line) for line in self.calls_path.read_text().splitlines() if line.strip()]
        return [r for r in rows if tool is None or r["tool"] == tool]

    def ky_calls(self):
        return [c["argv"] for c in self.calls("ky")]

    def events(self):
        p = self.run / "EVENTS.jsonl"
        return [json.loads(line) for line in p.read_text().splitlines() if line.strip()] if p.exists() else []

    def tracker_pid(self):
        try:
            pid = int((self.state / "tracker.pid").read_text())
            os.kill(pid, 0)
            return pid
        except (OSError, ValueError):
            return None

    def stop_tracker(self):
        pid = self.tracker_pid()
        if pid:
            os.kill(pid, signal.SIGTERM)       # a process the fake launchctl started for this test
            for _ in range(50):
                try:
                    os.kill(pid, 0)
                except OSError:
                    break
                time.sleep(0.1)

    def start_tracker(self):
        subprocess.run([str(self.tools / "launchctl"), "bootstrap", "gui/501", str(self.base / "pre.plist")], check=True)

    def close(self):
        self.stop_tracker()

    # ---- the source checkout, M and the reviews
    def git(self, *args, cwd=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                            "-C", str(cwd or self.src)] + list(args), capture_output=True, text=True, env=env)
        assert r.returncode == 0, (args, r.stderr)
        return r.stdout.strip()

    def put(self, rel, data, mode=0o644):
        p = self.src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
        p.chmod(mode)

    def component_sources(self):
        """{repository path: (bytes, mode)} of every bound component."""
        t = lambda s: render(s, self).encode()           # noqa: E731
        f = {}
        f[FL + "/kymanifest.py"] = (t(FAKE_KYMANIFEST), 0o644)
        f[FL + "/kyaction.py"] = ((FLEET / "kyaction.py").read_bytes(), 0o644)
        f[FL + "/kyloop.py"] = (t(FAKE_KYLOOP), 0o644)
        f[FL + "/kyqualify.py"] = (t(FAKE_KYQUALIFY), 0o644)
        f[FL + "/kyctl.sh"] = (t(FAKE_KYCTL), 0o755)
        f[FL + "/preflight.sh"] = (t(FAKE_PREFLIGHT), 0o755)
        f[FL + "/kyversion.sh"] = (t(FAKE_KYVERSION), 0o755)
        f[FL + "/bin/ky"] = (t(FAKE_KY), 0o755)
        f[FL + "/bin/kybrief"] = (t(FAKE_KYBRIEF), 0o755)
        f[FL + "/mcp.none.json"] = (b'{"mcpServers":{}}\n', 0o644)
        f[FL + "/schemas/packet.json"] = (b'{"title":"packet"}\n', 0o644)
        f[FL + "/cards/BOOTSTRAP.md"] = ("# BOOTSTRAP card — fake\n").encode(), 0o644
        f[FL + "/prompts/PLANNER_LOOP_v2_4.md"] = (b"planner loop prompt\n", 0o644)
        f[FL + "/templates/LAUNCH_CONFIG.bootstrap-builder.json"] = (
            b'{"schema":"ky.launch_config/1","role":"bootstrap-builder","model":"claude-opus-5-5"}\n', 0o644)
        f[FL + "/templates/LAUNCH_CONFIG.area-reviewer.json"] = (
            b'{"schema":"ky.launch_config/1","role":"area-reviewer","model":"claude-opus-5-5"}\n', 0o644)
        for loop in LOOPS:
            f[FL + "/launchd/in.marsys.kalayantra.%s.plist" % loop] = (b"<plist><dict/></plist>\n", 0o644)
        f[FL + "/tests/test_dummy.py"] = (b"def test_dummy():\n    pass\n", 0o644)
        for rel in ("__init__.py", "server.py", "cli.py", "static/app.js"):
            f[TRK + "/" + rel] = (("# tracker file %s\n" % rel).encode(), 0o644)
        return f

    AREAS = {
        "supervisor": ["kymanifest.py", "kyaction.py", "schemas/packet.json", "mcp.none.json", "BOOTSTRAP_COMPONENTS.txt"],
        "qualification": ["kyqualify.py", "kyloop.py", "templates/LAUNCH_CONFIG.bootstrap-builder.json",
                          "templates/LAUNCH_CONFIG.area-reviewer.json"],
        "runtime": ["kyctl.sh", "preflight.sh", "kyversion.sh", "bin/ky", "bin/kybrief", "cards/BOOTSTRAP.md",
                    "prompts/PLANNER_LOOP_v2_4.md", "tests/test_dummy.py"] +
                   ["launchd/in.marsys.kalayantra.%s.plist" % lp for lp in LOOPS],
    }

    def component_list_text(self, extra_bound=(), extra_deferred=("kyveto.py",)):
        lines = ["# KALĀ-YANTRA v3 — fake component list", ""]
        for area, names in self.AREAS.items():
            lines.append("# area: %s — fake" % area)
            lines += [FL + "/" + n for n in names]
        lines.append("# area: tracker — fake")
        lines += [TRK + "/" + n for n in ("__init__.py", "server.py", "cli.py", "static/app.js")]
        lines += list(extra_bound)
        lines += ["", "# tranche: deferred — reviewed separately", "# area: loops — deferred area"]
        lines += [FL + "/" + n for n in extra_deferred]
        return "\n".join(lines) + "\n"

    def build(self):
        """(Re)create S with its two commits, the review records and M."""
        if self.src.exists():
            shutil.rmtree(self.src)
        self.src.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        for role, rel in ENTRYPOINTS.items():
            self.put(rel, ("entrypoint %s\n" % role).encode())
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "approved source")
        self.approved = self.git("rev-parse", "HEAD")
        sources = self.component_sources()
        sources[FL + "/BOOTSTRAP_COMPONENTS.txt"] = (self.component_list_text().encode(), 0o644)
        sources[FL + "/kyveto.py"] = (b"# deferred, unreviewed\n", 0o644)
        sources[STAGED] = ((FLEET.parents[2] / "control" / "kalayantra" / "STAGED_MODEL_ACTIONS_v2_2.json").read_bytes(), 0o644)
        sources[PLAN_MODEL] = (b'{"items":[]}\n', 0o644)
        sources[TRK + "/tests/test_tracker.py"] = (b"def test_t():\n    pass\n", 0o644)     # unbound, never installed
        for rel, (data, mode) in sources.items():
            self.put(rel, data, mode)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "components")
        self.components_commit = self.git("rev-parse", "HEAD")
        self.git("remote", "add", "origin", str(self.base / "no-such-origin.git"))      # never fetched: no network
        self.git("update-ref", "refs/remotes/origin/main", self.approved)
        self.bound = sorted({FL + "/" + n for names in self.AREAS.values() for n in names}
                            | {TRK + "/" + n for n in ("__init__.py", "server.py", "cli.py", "static/app.js")})
        self.write_reviews()
        self.assemble()
        return self

    def hashes(self, paths):
        return {p: sha_file(self.src / p) for p in paths}

    def area_of(self, name):
        names = [FL + "/" + n for n in self.AREAS[name]] if name in self.AREAS else [TRK + "/" + n for n in
                                                                                   ("__init__.py", "server.py", "cli.py", "static/app.js")]
        return names

    def write_reviews(self):
        self.area_names = list(self.AREAS) + ["tracker"]
        for i, area in enumerate(self.area_names):
            self.write_area(area, {"area": area, "reviewer_session_id": "S-area-%d" % i, "review": {"verdict": "ACCEPTED"},
                                   "inputs": self.hashes(self.area_of(area))})

    def write_area(self, area, doc):
        (self.reviews / ("area-%s.json" % area)).write_text(json.dumps(doc, indent=1, sort_keys=True))

    def area_doc(self, area):
        return json.loads((self.reviews / ("area-%s.json" % area)).read_text())

    def edit_area(self, area, fn, resign=True):
        doc = self.area_doc(area)
        fn(doc)
        self.write_area(area, doc)
        if resign:
            self.assemble()

    def assemble(self, review_edit=None, manifest_edit=None):
        """Write the main review record from the area records on disk, then M (its `review` says ACCEPTED always)."""
        areas = []
        for area in self.area_names:
            p = self.reviews / ("area-%s.json" % area)
            if p.exists():
                areas.append({"area": area, "record": str(p), "record_sha256": sha_file(p),
                              "reviewer_session_id": json.loads(p.read_text()).get("reviewer_session_id")})
        review = {"verdict": "ACCEPTED", "reviewer_session_id": "S-main", "source_commit": self.approved,
                  "inputs": self.hashes(self.bound), "area_reviews": [{"record": a["record"], "record_sha256": a["record_sha256"]}
                                                                      for a in areas]}
        if review_edit:
            review_edit(review)
        rpath = self.reviews / "main-review.json"
        rpath.write_text(json.dumps(review, indent=1, sort_keys=True))
        entry = {}
        for role, rel in ENTRYPOINTS.items():
            entry[role] = {"path": rel, "sha256": sha_file(self.src / rel), "git_blob": self.git("rev-parse", "%s:%s" % (self.approved, rel))}
        manifest = {"schema": "ky.versions_bootstrap/1", "mode": "bootstrap", "plan_version": "2.7",
                    "deferred_components": [{"path": FL + "/kyveto.py", "sha256": sha_file(self.src / FL / "kyveto.py")}],
                    "approved_source_commit": self.approved, "entrypoints": entry,
                    "entrypoints_digest": sha_bytes(canonical({r: {"path": e["path"], "git_blob": e["git_blob"]} for r, e in entry.items()})),
                    "components_commit": self.components_commit,
                    "components": [{"path": p, "sha256": sha_file(self.src / p)} for p in self.bound],
                    "generated_pairs": [], "probes": {}, "qualifications": [], "qualifications_all_pass": True,
                    "review": {"path": os.path.relpath(rpath, self.src), "sha256": sha_file(rpath), "verdict": "ACCEPTED",
                               "reviewer_session_id": "S-main", "area_reviews": sorted(areas, key=lambda a: a["area"])}}
        if manifest_edit:
            manifest_edit(manifest)
        self.write_manifest(manifest)

    def write_manifest(self, manifest):
        body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
        manifest = dict(body, manifest_sha256=sha_bytes(canonical(body)))
        self.manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
        self.m = manifest

    def commit_src(self, message="change"):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    # ---- running install.sh
    def env(self, **extra):
        env = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": str(self.home), "LANG": "en_US.UTF-8",
               "KY_SCRATCH": str(self.scratch), "CLAUDE_BIN": str(self.tools / "claude"),
               "KY_LAUNCHAGENTS_DIR": str(self.la), "KY_LAUNCHCTL": str(self.tools / "launchctl"),
               "KY_CAMPAIGN_CHECKOUT": str(self.camp), "PRAVAHA_URL": self.url,
               "KY_PS": str(self.tools / "ps"), "KY_GH": str(self.tools / "gh"), "KY_INSTALL_WAIT_S": "6"}
        env.update(extra)
        return {k: v for k, v in env.items() if v is not None}

    def install(self, *, action=None, root=None, extra_args=(), env=None, manifest=None, source=None, timeout=240):
        args = ["--manifest", str(manifest or self.manifest_path), "--source", str(source or self.src),
                "--root", str(root or self.root)]
        if action:
            args += ["--action", action]
        args += list(extra_args)
        return subprocess.run(["/bin/bash", str(INSTALL)] + args, capture_output=True, text=True, timeout=timeout,
                              env=self.env(**(env or {})), cwd=str(self.base))

    def snapshot(self):
        return {"root": tree_state(self.root), "la": tree_state(self.la), "camp": self.camp.exists(),
                "launchctl": [c for c in self.calls("launchctl") if c["argv"][0] != "print"],
                "ky": self.calls("ky")}

    def receipt(self):
        return json.loads((self.run / "INSTALL_RECEIPT.json").read_text())

    def begin_action(self, action_id="INSTALL-1", inputs=None, kind="install"):
        inputs = inputs if inputs is not None else {"manifest_sha256": sha_file(self.manifest_path),
                                                    "source_commit": self.components_commit}
        status, rec = kyaction.begin(str(self.run), action_id, kind,
                                     {"role": "cockpit", "holder_kind": "cockpit", "session_id": "S-cockpit"},
                                     inputs, {"root": str(self.root)}, "install the bootstrap bundle")
        assert status == "new"
        return rec

    def action_record(self, action_id="INSTALL-1"):
        return json.loads((self.run / "actions" / (action_id + ".json")).read_text())

    def old_installation(self):
        """A previous installation's trees and receipt, so a test can prove the trees come back and the receipt does not."""
        (self.root / "fleet_live").mkdir(parents=True)
        (self.root / "fleet_live" / "old.txt").write_text("old fleet\n")
        (self.root / "bin").mkdir()
        (self.root / "bin" / "ky").write_text("old ky\n")
        (self.root / "bin" / "ky").chmod(0o755)
        (self.run / "VERSIONS.bootstrap.json").write_text("old manifest\n")
        (self.run / "INSTALL_RECEIPT.json").write_text('{"old": true}\n')

    def assert_old_installation_whole(self):
        root = self.root
        assert (root / "fleet_live" / "old.txt").read_text() == "old fleet\n" and not (root / "fleet_live" / "kyctl.sh").exists()
        assert (root / "bin" / "ky").read_text() == "old ky\n" and not (root / "bin" / "kybrief").exists()
        assert (self.run / "VERSIONS.bootstrap.json").read_text() == "old manifest\n"
        assert not (self.run / "INSTALL_RECEIPT.json").exists(), "exit 3 leaves no receipt, the previous one included"
        assert (self.run / "INSTALL_RECEIPT.json.superseded").read_text() == '{"old": true}\n', "it is kept, moved aside"
        for name in ("fleet_live.new", "fleet_live.old", "tracker_live", "tracker_live.new", "tracker_live.old"):
            assert not (root / name).exists(), name

    def append_event(self, ev):
        self.run.mkdir(parents=True, exist_ok=True)
        with open(self.run / "EVENTS.jsonl", "a") as f:
            f.write(json.dumps(ev, ensure_ascii=False, separators=(",", ":")) + "\n")


@pytest.fixture
def w(tmp_path):
    world = World(tmp_path)
    world.build()
    yield world
    world.close()


def ok(r):
    assert r.returncode == 0, "exit %d\nSTDOUT:\n%s\nSTDERR:\n%s" % (r.returncode, r.stdout, r.stderr)
    return r


def refused(r, code=1, text=None):
    assert r.returncode == code, "exit %d (wanted %d)\nSTDOUT:\n%s\nSTDERR:\n%s" % (r.returncode, code, r.stdout, r.stderr)
    if text:
        assert text in r.stderr, "%r not in stderr:\n%s" % (text, r.stderr)
    return r


# ================================================================================ the happy path and its records
def test_install_into_a_scratch_root_writes_everything_in_order(w):
    r = ok(w.install())
    root = w.root
    # 1. F/**: fleet components (bin excluded), the five entrypoints under bundle/<repository path>
    fleet = root / "fleet_live"
    for rel in ("kyctl.sh", "kyloop.py", "kyaction.py", "mcp.none.json", "cards/BOOTSTRAP.md", "prompts/PLANNER_LOOP_v2_4.md",
                "templates/LAUNCH_CONFIG.bootstrap-builder.json", "tests/test_dummy.py", "BOOTSTRAP_COMPONENTS.txt"):
        assert (fleet / rel).read_bytes() == (w.src / FL / rel).read_bytes(), rel
    for rel in ENTRYPOINTS.values():
        assert (fleet / "bundle" / rel).read_bytes() == (w.src / rel).read_bytes(), rel
    assert not (fleet / "bin").exists()
    assert not (fleet / "kyveto.py").exists(), "a deferred component is never installed"
    assert os.access(fleet / "kyctl.sh", os.X_OK) and not os.access(fleet / "kyloop.py", os.X_OK)
    # 2. the tracker package, tests excluded
    live = root / "tracker_live" / "pravaha_tracker"
    assert sorted(str(p.relative_to(live)) for p in live.rglob("*") if p.is_file()) == ["__init__.py", "cli.py", "server.py", "static/app.js"]
    # 3. bin: exactly the two wrappers, byte copies, 0755
    assert sorted(p.name for p in (root / "bin").iterdir()) == ["ky", "kybrief"]
    for name in ("ky", "kybrief"):
        assert (root / "bin" / name).read_bytes() == (w.src / FL / "bin" / name).read_bytes()
        assert stat.S_IMODE((root / "bin" / name).stat().st_mode) == 0o755
    # 4. the manifest
    assert (w.run / "VERSIONS.bootstrap.json").read_bytes() == w.manifest_path.read_bytes()
    # 5. the campaign checkout at the components commit, on its branch
    assert w.git("rev-parse", "HEAD", cwd=w.camp) == w.components_commit
    assert w.git("rev-parse", "--abbrev-ref", "HEAD", cwd=w.camp) == "kalayantra/campaign"
    # first writes: STOP files for every legacy lane
    for lane in LANES:
        assert (w.run / ("STOP_" + lane)).is_file()
    # the order of the external programs
    tools = [c["tool"] for c in w.calls() if c["tool"] in ("kymanifest", "claude", "preflight", "kyversion", "kyctl")]
    assert tools[0] == "kymanifest" and tools.index("kyctl") < tools.index("preflight") < tools.index("kyversion")
    pre = w.calls("preflight")[0]
    assert pre["argv"] == ["launch"] and pre["receipt_present"] is False
    ver = w.calls("kyversion")[0]
    assert ver["argv"] == ["--bootstrap"] and ver["receipt_present"] is True and ver["receipt_mode"] == "bootstrap"
    out = json.loads(r.stdout)
    assert out["installed"] is True and out["receipt"] == str(w.run / "INSTALL_RECEIPT.json")


def test_kymanifest_check_is_run_by_isolated_python_against_s_and_r(w):
    ok(w.install())
    c = w.calls("kymanifest")[0]["argv"]
    assert c == ["check", str(w.manifest_path), "--repo", str(w.src), "--run", str(w.run)]


def test_receipt_records_every_measured_value(w):
    ok(w.install())
    rc = w.receipt()
    assert rc["schema"] == "ky.install_receipt/1" and rc["mode"] == "bootstrap"
    assert rc["source"]["components_commit"] == w.components_commit and rc["source"]["approved_source_commit"] == w.approved
    assert rc["source"].get("merge_commit") in (None, "")
    assert rc["manifest"]["sha256"] == sha_file(w.manifest_path) and rc["manifest"]["manifest_sha256"] == w.m["manifest_sha256"]
    assert rc["manifest"]["path"] == str(w.run / "VERSIONS.bootstrap.json")
    # components: one per installed file, read by kyversion.sh (path = a manifest component, installed_path absolute)
    comps = {c["path"]: c for c in rc["components"]}
    mpaths = {c["path"]: c["sha256"] for c in w.m["components"]}
    assert set(comps) == set(mpaths) - {TRK + "/tests/test_tracker.py"}
    for path, c in comps.items():
        assert c["sha256"] == mpaths[path] and os.path.isabs(c["installed_path"]) and sha_file(c["installed_path"]) == c["sha256"]
    assert comps[FL + "/bin/ky"]["installed_path"] == str(w.root / "bin" / "ky")
    assert comps[FL + "/mcp.none.json"]["installed_path"] == str(w.root / "fleet_live" / "mcp.none.json")
    assert comps[TRK + "/server.py"]["installed_path"] == str(w.root / "tracker_live" / "pravaha_tracker" / "server.py")
    assert FL + "/kyveto.py" not in comps
    # reviews
    assert rc["reviews"]["record"]["sha256"] == sha_file(w.reviews / "main-review.json")
    assert sorted(a["area"] for a in rc["reviews"]["areas"]) == sorted(w.area_names)
    # CLAUDE_BIN
    cb = rc["claude_bin"]
    assert cb["path"] == str(w.tools / "claude") and cb["version"] == "2.1.300" and cb["sha256"] == sha_file(w.tools / "claude")
    # the running tracker
    tr = rc["tracker_revision"]
    assert tr["pid"] == w.tracker_pid() and tr["package_sha256"] and tr["process_start"]
    assert tr["health"]["event_log"] == str(w.run / "EVENTS.jsonl") and tr["health"]["server_started_at"]
    # plists
    labels = {p["label"] for p in rc["plists"]}
    assert labels == {TRACKER_LABEL} | {"in.marsys.kalayantra." + lp for lp in LOOPS}
    for p in rc["plists"]:
        assert sha_file(p["path"]) == p["sha256"] and p["hook_variables"] == []
        assert p["path"].startswith(str(w.la))
    loops = [p for p in rc["plists"] if p["label"] != TRACKER_LABEL]
    assert all(p["ky_scratch"] == str(w.scratch) for p in loops)
    # old supervisors
    osup = rc["old_supervisors"]
    assert sorted(s["lane"] for s in osup["stop_files"]) == sorted(LANES)
    assert osup["processes"]["matching"] == [] and osup["processes"]["answered"] is True
    limits = " ".join(osup["processes"]["limits"])
    assert "ancestor" in limits and "command line" in limits, "what the process evidence does not show is stated"
    # campaign checkout
    cc = rc["campaign_checkout"]
    assert cc["path"] == str(w.camp) and cc["branch"] == "kalayantra/campaign" and cc["head"] == w.components_commit
    assert cc["upstream"] == "origin/main"
    # model actions: 2 decisions, 8 parks, 1 block — each with its event
    kinds = [(m["kind"], m["id"]) for m in rc["model_actions"]["entries"]]
    assert [k for k, _ in kinds].count("decision") == 2 and [k for k, _ in kinds].count("park") == 8
    assert ("block", "KV3-SCHEMA-1") in kinds
    assert all(m["event"]["sha256"] and m["event"]["line"] >= 1 for m in rc["model_actions"]["entries"])
    # qualifications: both templates, both loop roles
    quals = {(q["role"], q["model"]): q for q in rc["qualifications"]}
    assert set(quals) == {("bootstrap-builder", "claude-opus-5-5"), ("area-reviewer", "claude-opus-5-5"),
                          ("planner", "claude-opus-5-5"), ("conductor", "claude-opus-5-5")}
    assert all(q["result"] == "PASS" and sha_file(q["receipt"]) == q["receipt_sha256"] for q in quals.values())
    assert all(Path(q["receipt"]).parent == w.run / "QUALIFICATIONS" for q in quals.values())
    assert "legacy" in rc and rc["legacy"]["unresolved"] == []


def test_the_installed_ky_is_given_the_scratch_root_not_the_live_defaults(w):
    ok(w.install())
    calls = w.calls("ky")
    assert calls, "the staged actions are published with the installed ky"
    env = calls[0]["env"]
    assert env["PRAVAHA_HOME"] == str(w.root) and env["PRAVAHA_EVENTS"] == str(w.run / "EVENTS.jsonl")
    assert env["PRAVAHA_REPO"] == str(w.camp) and env["PRAVAHA_PLAN_MODEL"] == str(w.camp / PLAN_MODEL)
    assert env["PRAVAHA_URL"] == w.url and env["PRAVAHA_TRACKER_PORT"] == str(w.port)
    assert env["PRAVAHA_HOLD"] == str(w.root / "HOLD") and env["KY_SCRATCH"] == str(w.scratch)


def test_tracker_plist_has_the_install_tracker_block_with_fleet_on_pythonpath(w):
    ok(w.install())
    plist = plistlib.loads((w.la / (TRACKER_LABEL + ".plist")).read_bytes())
    assert plist["Label"] == TRACKER_LABEL
    assert plist["ProgramArguments"][-3:] == ["pravaha_tracker.server", "--port", str(w.port)]
    assert plist["WorkingDirectory"] == str(w.root / "tracker_live")
    env = plist["EnvironmentVariables"]
    assert env["PYTHONPATH"].split(":") == [str(w.root / "tracker_live"), str(w.root / "fleet_live")]
    assert env["PRAVAHA_REPO"] == str(w.camp) and env["PRAVAHA_PLAN_MODEL"] == str(w.camp / PLAN_MODEL)
    assert env["PRAVAHA_EVENTS"] == str(w.run / "EVENTS.jsonl") and env["PRAVAHA_HOME"] == str(w.root)
    assert not [k for k in env if k.startswith("KY_")], "no KY_* (test hook) variable in the tracker plist"
    assert plist["KeepAlive"] is True and plist["RunAtLoad"] is True


def test_the_loop_plists_come_from_kyctl_install_without_starting_anything(w):
    ok(w.install())
    ctl = w.calls("kyctl")
    assert len(ctl) == 1 and ctl[0]["argv"] == ["install"]
    assert ctl[0]["env"]["KY_SOURCE_REPO"] == str(w.camp) and ctl[0]["env"]["KY_FLEET"] == str(w.root / "fleet_live")
    assert "KY_LOOP_SLEEP_SCALE" not in ctl[0]["env"]
    started = [c["argv"] for c in w.calls("launchctl") if c["argv"][0] in ("bootstrap", "kickstart", "load")]
    assert started == [["bootstrap", "gui/%d" % os.getuid(), str(w.la / (TRACKER_LABEL + ".plist"))]], "only the tracker is loaded"


def test_tracker_restarted_with_health_ok_after_the_swap(w):
    ok(w.install())
    verbs = [c["argv"][0] for c in w.calls("launchctl")]
    assert "bootout" in verbs and "bootstrap" in verbs and verbs.index("bootout") < verbs.index("bootstrap")
    pid = w.tracker_pid()
    assert pid
    newest = max((p.stat().st_mtime for p in (w.root / "tracker_live").rglob("*.py")), default=0)
    start = subprocess.run(["/bin/ps", "-ww", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    assert time.mktime(time.strptime(start, "%a %b %d %H:%M:%S %Y")) > newest


def test_model_actions_are_published_with_the_installed_ky_in_the_staged_form(w):
    ok(w.install())
    calls = w.ky_calls()
    staged = json.loads((w.src / STAGED).read_text())
    assert len(calls) == len(staged["decisions"]) + len(staged["parks"]) + len(staged["blocks"]) == 11
    d = staged["decisions"][0]
    assert calls[0] == ["decide", d["decision"], "--outcome", "refused", "--as", "steward", "--delegated", "--detail", d["detail"]]
    p = staged["parks"][0]
    assert ["park", p["item"], "--as", "steward", "--detail", p["detail"]] in calls
    assert ["block", "KV3-SCHEMA-1", "--as", "steward", "--detail", staged["blocks"][0]["detail"]] in calls
    assert [c[0] for c in calls].count("decide") == 2
    assert len(w.events()) == 11


# ================================================================================ idempotence and resumption
def test_a_second_run_changes_and_republishes_nothing(w):
    ok(w.install())
    before = w.snapshot()
    receipt_before = (w.run / "INSTALL_RECEIPT.json").read_bytes()
    r = ok(w.install())
    after = w.snapshot()
    assert after["ky"] == before["ky"], "no second ky decide/park/block"
    assert after["launchctl"] == before["launchctl"], "the running tracker is not restarted"
    for key in ("root", "la", "camp"):
        changed = {k for k in set(before[key]) | set(after[key]) if before[key].get(k) != after[key].get(k)} if isinstance(before[key], dict) \
            else (before[key] != after[key])
        assert not changed, (key, sorted(changed) if isinstance(changed, set) else changed)
    assert (w.run / "INSTALL_RECEIPT.json").read_bytes() == receipt_before
    assert not (w.root / "fleet_live.old").exists() and not (w.root / "tracker_live.old").exists()
    assert len([c for c in w.calls("kyqualify") if c["argv"][0] == "qualify"]) == 4, "four configs qualified once, none again"
    assert json.loads(r.stdout)["installed"] is True


def test_a_crash_after_the_tracker_step_resumes_without_a_second_decide(w):
    w.control(ky_fail_after_append_of="J-7")          # the 3rd entry's event is written, then the process dies
    refused(w.install(), 3)
    assert not (w.run / "INSTALL_RECEIPT.json").exists()
    before = [e.get("decision") or e.get("item") for e in w.events()]
    assert before[:3] == ["D-RETIRE-B-K-INBOX", "D-RETIRE-B-CLAIM-RECOVERY", "J-7"]
    ok(w.install())
    ids = [e.get("decision") or e.get("item") for e in w.events()]
    assert len(ids) == len(set(ids)) == 11, "every staged action exactly once"
    decides = [c for c in w.ky_calls() if c[0] == "decide"]
    assert len(decides) == 2
    assert (w.run / "INSTALL_RECEIPT.json").exists()


def test_an_existing_event_is_skipped_and_reported(w):
    staged = json.loads((w.src / STAGED).read_text())
    d = staged["decisions"][0]
    w.run.mkdir(parents=True, exist_ok=True)
    (w.run / "EVENTS.jsonl").write_text(json.dumps({"kind": "decision", "actor": "steward", "decision": d["decision"], "state": "delegated",
                                                     "outcome": "refused", "detail": d["detail"], "ts": "2026-10-12T00:00:00+00:00"}) + "\n")
    r = ok(w.install())
    assert [c for c in w.ky_calls() if c[0] == "decide"] == [c for c in w.ky_calls() if c[0] == "decide" and c[1] != d["decision"]]
    summary = json.loads(r.stdout)
    status = {m["id"]: m["status"] for m in summary["model_actions"]}
    assert status[d["decision"]] == "skipped_existing" and status["J-7"] == "published"
    assert w.receipt()["model_actions"]["entries"][0]["event"]["line"] == 1


def test_unreadable_event_log_line_blocks_publication_it_cannot_exclude(w):
    (w.run / "EVENTS.jsonl").write_text("{broken\n")
    refused(w.install(), 3, "event log")
    assert w.ky_calls() == []


# ================================================================================ usage and the P29 / P39 decisions
@pytest.mark.parametrize("args", [[], ["--manifest"], ["--manifest", "relative.json", "--source", "/x"],
                                   ["--manifest", "/m", "--source", "rel/src"], ["--bogus"], ["stray"],
                                   ["--manifest", "/m", "--manifest", "/n", "--source", "/s", "--root", "/r"],
                                   ["--manifest", "/m", "--source", "/s", "--root", "rel/root"],
                                   ["--manifest", "/m", "--source", "/s", "--root", "/r", "--action", ""]])
def test_usage_errors_exit_64(w, args):
    r = subprocess.run(["/bin/bash", str(INSTALL)] + args, capture_output=True, text=True, env=w.env(), cwd=str(w.base))
    assert r.returncode == 64, r.stderr
    assert "usage" in r.stderr.lower()
    assert not w.root.joinpath("fleet_live").exists()


def test_real_root_without_an_action_is_refused_first_with_e_action(w):
    r = subprocess.run(["/bin/bash", str(INSTALL), "--manifest", "/nonexistent/m.json", "--source", "/nonexistent/s",
                        "--root", REAL_ROOT], capture_output=True, text=True, env=w.env(), cwd=str(w.base))
    refused(r, 1, "E_ACTION")
    assert "nonexistent" not in r.stderr, "M and S were not read"


def test_real_root_via_the_environment_default_is_also_the_real_root(w):
    env = w.env(KY_ROOT=REAL_ROOT)
    r = subprocess.run(["/bin/bash", str(INSTALL), "--manifest", "/nonexistent/m.json", "--source", "/nonexistent/s"],
                       capture_output=True, text=True, env=env, cwd=str(w.base))
    refused(r, 1, "E_ACTION")


def test_real_root_with_a_test_hook_is_refused_before_anything_is_read(w):
    r = subprocess.run(["/bin/bash", str(INSTALL), "--manifest", "/nonexistent/m.json", "--source", "/nonexistent/s",
                        "--root", REAL_ROOT, "--action", "INSTALL-1"], capture_output=True, text=True,
                       env=w.env(KY_LAUNCHAGENTS_DIR=None, KY_LAUNCHCTL=None, KY_CAMPAIGN_CHECKOUT=None, PRAVAHA_URL=None), cwd=str(w.base))
    refused(r, 1, "E_HOOK KY_PS")


@pytest.mark.parametrize("var", ["KY_LAUNCHAGENTS_DIR", "KY_LAUNCHCTL", "KY_CAMPAIGN_CHECKOUT", "PRAVAHA_URL"])
def test_a_scratch_root_needs_each_variable_explicitly(w, var):
    env = w.env(**{var: None})
    r = subprocess.run(["/bin/bash", str(INSTALL), "--manifest", "/nonexistent/m.json", "--source", "/nonexistent/s",
                        "--root", str(w.root)], capture_output=True, text=True, env=dict(env, HOME=str(w.base)), cwd=str(w.base))
    refused(r, 1, "E_UNSET " + var)
    assert "nonexistent" not in r.stderr
    assert not (w.root / "fleet_live").exists() and not list(w.run.glob("STOP_*"))


def real_defaults(base):
    return {"KY_LAUNCHAGENTS_DIR": str(Path(base) / "Library" / "LaunchAgents"), "KY_LAUNCHCTL": "/bin/launchctl",
            "KY_CAMPAIGN_CHECKOUT": REAL_CAMPAIGN, "PRAVAHA_URL": "http://127.0.0.1:8767"}


@pytest.mark.parametrize("var", ["KY_LAUNCHAGENTS_DIR", "KY_LAUNCHCTL", "KY_CAMPAIGN_CHECKOUT", "PRAVAHA_URL"])
def test_a_scratch_root_refuses_a_variable_equal_to_its_real_default(w, var):
    env = w.env(**{var: real_defaults(w.base)[var]})
    r = subprocess.run(["/bin/bash", str(INSTALL), "--manifest", "/nonexistent/m.json", "--source", "/nonexistent/s",
                        "--root", str(w.root)], capture_output=True, text=True, env=dict(env, HOME=str(w.base)), cwd=str(w.base))
    refused(r, 1, "E_REAL " + var)
    assert "nonexistent" not in r.stderr
    assert not (w.root / "fleet_live").exists() and not list(w.run.glob("STOP_*")) and w.calls("launchctl") == []


@pytest.mark.parametrize("url", ["http://127.0.0.1:8767/", "http://localhost:8767", "HTTP://127.0.0.1:8767"])
def test_the_real_tracker_url_is_recognised_in_its_spellings(w, url):
    r = subprocess.run(["/bin/bash", str(INSTALL), "--manifest", "/nonexistent/m.json", "--source", "/nonexistent/s",
                        "--root", str(w.root)], capture_output=True, text=True, env=w.env(PRAVAHA_URL=url), cwd=str(w.base))
    refused(r, 1, "E_REAL PRAVAHA_URL")


def test_a_symlink_to_the_real_launchctl_is_the_real_launchctl(w):
    link = w.tools / "launchctl_link"
    link.symlink_to("/bin/launchctl")
    r = subprocess.run(["/bin/bash", str(INSTALL), "--manifest", "/nonexistent/m.json", "--source", "/nonexistent/s",
                        "--root", str(w.root)], capture_output=True, text=True, env=w.env(KY_LAUNCHCTL=str(link)), cwd=str(w.base))
    refused(r, 1, "E_REAL KY_LAUNCHCTL")


def first_decision(w, env, *extra):
    return subprocess.run(["/bin/bash", str(INSTALL), "--manifest", "/nonexistent/m.json", "--source", "/nonexistent/s"] + list(extra),
                          capture_output=True, text=True, env=env, cwd=str(w.base))


def test_a_scratch_root_refuses_the_accounts_launchagents_whatever_home_says(w):
    account = Path(pwd.getpwuid(os.getuid()).pw_dir) / "Library" / "LaunchAgents"
    assert str(w.home) != str(account.parents[1]), "HOME points elsewhere in this test, as in every test here"
    r = first_decision(w, w.env(KY_LAUNCHAGENTS_DIR=str(account)), "--root", str(w.root))
    refused(r, 1, "E_REAL KY_LAUNCHAGENTS_DIR")
    assert "nonexistent" not in r.stderr and not list(w.run.glob("STOP_*"))


@pytest.mark.parametrize("var,value", [("KY_LAUNCHAGENTS_DIR", REAL_ROOT + "/LaunchAgents"),
                                       ("KY_CAMPAIGN_CHECKOUT", REAL_ROOT + "/wt/campaign"),
                                       ("KY_LAUNCHCTL", REAL_ROOT + "/bin/launchctl"),
                                       ("KY_SCRATCH", REAL_ROOT + "/run/scratch")])
def test_a_scratch_root_refuses_a_value_inside_the_real_root(w, var, value):
    r = first_decision(w, w.env(**{var: value}), "--root", str(w.root))
    refused(r, 1, "E_REAL " + var)
    assert "nonexistent" not in r.stderr and not list(w.run.glob("STOP_*"))


def test_ky_scratch_is_never_defaulted(w):
    r = first_decision(w, w.env(KY_SCRATCH=None), "--root", str(w.root))
    refused(r, 1, "E_UNSET KY_SCRATCH")
    assert "nonexistent" not in r.stderr
    real = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": pwd.getpwuid(os.getuid()).pw_dir, "LANG": "en_US.UTF-8"}
    r = first_decision(w, real, "--root", REAL_ROOT, "--action", "INSTALL-1")
    refused(r, 1, "E_UNSET KY_SCRATCH")
    assert "nonexistent" not in r.stderr, "decided before M, S or the action record is read"


def test_the_real_root_needs_the_accounts_own_home(w):
    env = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": str(w.home), "LANG": "en_US.UTF-8", "KY_SCRATCH": str(w.scratch)}
    r = first_decision(w, env, "--root", REAL_ROOT, "--action", "INSTALL-1")
    refused(r, 1, "E_VALUE HOME")
    assert "nonexistent" not in r.stderr


def test_a_root_inside_the_real_root_is_refused(w):
    r = subprocess.run(["/bin/bash", str(INSTALL), "--manifest", "/nonexistent/m.json", "--source", "/nonexistent/s",
                        "--root", REAL_ROOT + "/sub"], capture_output=True, text=True, env=w.env(), cwd=str(w.base))
    refused(r, 1, "E_REAL")


# ================================================================================ verification: nothing written on refusal
def assert_nothing_written(w, before):
    after = w.snapshot()
    assert after["root"] == before["root"], sorted(set(after["root"]) ^ set(before["root"]))
    assert after["la"] == before["la"] and after["camp"] == before["camp"]
    assert after["launchctl"] == [] and after["ky"] == []
    assert not list(w.run.glob("STOP_*"))


def refuse_cleanly(w, text=None):
    before = w.snapshot()
    r = refused(w.install(), 1, text)
    assert_nothing_written(w, before)
    return r


def test_area_review_rejected_while_the_manifest_says_accepted(w):
    w.edit_area("qualification", lambda d: d["review"].update(verdict="REJECTED"))
    assert w.m["review"]["verdict"] == "ACCEPTED"
    refuse_cleanly(w, "not ACCEPTED")


def test_area_review_missing(w):
    (w.reviews / "area-runtime.json").unlink()
    refuse_cleanly(w, "missing or changed")


def test_area_review_changed_after_it_was_signed(w):
    path = w.reviews / "area-supervisor.json"
    doc = json.loads(path.read_text())
    doc["reviewer_session_id"] = "S-someone-else"
    path.write_text(json.dumps(doc))
    refuse_cleanly(w, "missing or changed")


def test_one_session_signs_twice(w):
    w.edit_area("runtime", lambda d: d.update(reviewer_session_id=w.area_doc("supervisor")["reviewer_session_id"]))
    refuse_cleanly(w, "signs twice")


def test_the_main_reviewer_may_not_also_sign_an_area(w):
    w.edit_area("runtime", lambda d: d.update(reviewer_session_id="S-main"))
    refuse_cleanly(w, "signs twice")


def test_area_review_without_a_session(w):
    w.edit_area("runtime", lambda d: d.pop("reviewer_session_id"))
    refuse_cleanly(w, "session")


def test_the_areas_must_equal_the_bound_area_names_of_the_component_list(w):
    (w.reviews / "area-tracker.json").unlink()
    w.assemble()                                     # a consistent set of records that omits the bound area "tracker"
    refuse_cleanly(w, "area")


def test_an_extra_area_review_for_a_deferred_area_is_not_accepted_in_place_of_a_bound_one(w):
    w.write_area("loops", {"area": "loops", "reviewer_session_id": "S-loops", "review": {"verdict": "ACCEPTED"}, "inputs": {}})
    w.area_names.append("loops")
    w.assemble()
    refuse_cleanly(w, "area")


def test_no_accepted_area_record_covers_a_component(w):
    victim = FL + "/kyctl.sh"
    w.edit_area("runtime", lambda d: d["inputs"].pop(victim))
    refuse_cleanly(w, "kyctl.sh")


def test_main_review_not_accepted(w):
    w.assemble(review_edit=lambda r: r.update(verdict="REJECTED"))
    refuse_cleanly(w, "ACCEPTED")


def test_main_review_bound_to_another_approved_commit(w):
    w.assemble(review_edit=lambda r: r.update(source_commit="0" * 40))
    refuse_cleanly(w, "approved")


def test_main_review_file_changed_after_the_manifest_bound_it(w):
    p = w.reviews / "main-review.json"
    p.write_text(p.read_text() + "\n")
    refuse_cleanly(w, "review")


def test_component_bytes_differ_from_the_reviewed_hash(w):
    victim = w.src / FL / "kyctl.sh"
    victim.write_bytes(victim.read_bytes() + b"# changed after review\n")
    w.commit_src()                                    # S is clean again, but no longer at M's components commit
    refuse_cleanly(w, "components commit")


def test_component_bytes_differ_in_a_dirty_checkout(w):
    victim = w.src / FL / "kyctl.sh"
    victim.write_bytes(victim.read_bytes() + b"# not committed\n")
    refuse_cleanly(w, "clean")


def test_an_untracked_file_in_s_means_it_is_not_clean(w):
    (w.src / "stray.txt").write_text("x")
    refuse_cleanly(w, "clean")


def test_the_manifest_hash_of_a_component_is_checked_against_the_bytes(w):
    def edit(m):
        for c in m["components"]:
            if c["path"].endswith("kyloop.py"):
                c["sha256"] = "0" * 64
    w.assemble(manifest_edit=edit)
    refuse_cleanly(w, "kyloop.py")


def test_the_manifests_own_digest_must_match_its_content(w):
    m = json.loads(w.manifest_path.read_text())
    m["plan_version"] = "9.9"
    w.manifest_path.write_text(json.dumps(m))
    refuse_cleanly(w, "manifest")


def test_a_non_bootstrap_manifest_is_refused(w):
    w.assemble(manifest_edit=lambda m: m.update(mode="final"))
    refuse_cleanly(w, "bootstrap")


def test_kymanifest_check_must_exit_zero(w):
    w.control(kymanifest_rc=1)
    refuse_cleanly(w, "kymanifest")


def test_an_entrypoint_that_differs_from_its_blob_is_refused(w):
    (w.src / ENTRYPOINTS["plan"]).write_text("edited plan\n")
    w.commit_src()
    w.components_commit = w.git("rev-parse", "HEAD")
    w.assemble()
    refuse_cleanly(w, "entrypoint")


def test_an_unbound_tracker_file_to_install_is_refused(w):
    w.put(TRK + "/extra.py", "# never reviewed\n")
    w.commit_src()
    w.components_commit = w.git("rev-parse", "HEAD")
    w.assemble()
    refuse_cleanly(w, "unbound")


def test_a_modified_tracker_file_is_refused(w):
    w.put(TRK + "/server.py", "# modified after review\n")
    w.commit_src()
    w.components_commit = w.git("rev-parse", "HEAD")
    w.assemble(manifest_edit=lambda m: m.update(components_commit=w.components_commit))
    refuse_cleanly(w, "server.py")


def test_an_unbound_file_among_the_wrappers_is_refused(w):
    w.put(FL + "/bin/extra", "#!/bin/sh\n", 0o755)
    w.commit_src()
    w.components_commit = w.git("rev-parse", "HEAD")
    w.assemble()
    refuse_cleanly(w, "unbound")


def test_a_bound_component_with_no_destination_is_refused(w):
    w.put("platform/other/thing.py", "x = 1\n")
    w.commit_src()
    w.components_commit = w.git("rev-parse", "HEAD")
    w.bound.append("platform/other/thing.py")
    w.bound.sort()
    w.assemble()
    refuse_cleanly(w, "destination")


def test_a_required_component_missing_from_the_manifest_is_refused(w):
    w.bound.remove(FL + "/preflight.sh")
    w.assemble()
    refuse_cleanly(w, "preflight.sh")


def test_the_staged_actions_file_must_be_the_committed_one(w):
    p = w.src / STAGED
    doc = json.loads(p.read_text())
    doc["blocks"][0]["detail"] = "tampered"
    p.write_text(json.dumps(doc))
    refuse_cleanly(w, "clean")


def test_a_staged_action_published_as_the_native_is_refused(w):
    p = w.src / STAGED
    doc = json.loads(p.read_text())
    doc["parks"][0]["as"] = "native"                  # the installer never speaks as the owner
    p.write_text(json.dumps(doc))
    w.commit_src()
    w.components_commit = w.git("rev-parse", "HEAD")
    w.assemble()
    refuse_cleanly(w, "steward")


def test_claude_bin_not_executable(w):
    (w.tools / "claude").chmod(0o644)
    refuse_cleanly(w, "CLAUDE_BIN")


def test_claude_bin_below_the_version_pin(w):
    w.write_claude("2.1.295")
    refuse_cleanly(w, "version")


def test_claude_bin_version_unreadable(w):
    (w.tools / "claude").write_text("#!/bin/sh\necho hello\n")
    refuse_cleanly(w, "version")


def test_claude_bin_exactly_at_the_pin_is_accepted(w):
    w.write_claude("2.1.296")
    ok(w.install())
    assert w.receipt()["claude_bin"]["version"] == "2.1.296"


@pytest.mark.parametrize("line", [
    "  200   100 bash /Users/Dev/kalayantra/fleet_live/kalayantra_fleet.sh lane-locked k6",
    "  201   100 python3 /x/claude_cycle.py --lane k1",
    "  202   100 python3 /Users/Dev/kalayantra/conductor/sweep.py",
])
def test_a_live_legacy_supervisor_refuses_and_nothing_is_written(w, line):
    w.control(ps_extra=[line])
    refuse_cleanly(w, "legacy supervisor")


def test_a_codex_exec_under_the_root_wt_is_a_legacy_supervisor(w):
    w.control(ps_extra=["  203   100 codex exec --cd %s/wt/k3 do-the-thing" % w.root])
    refuse_cleanly(w, "legacy supervisor")


def test_a_codex_exec_elsewhere_is_not(w):
    w.control(ps_extra=["  203   100 codex exec --cd /somewhere/else do-the-thing"])
    ok(w.install())


def test_an_unobservable_process_listing_refuses(w):
    w.control(ps_fail=True)
    refuse_cleanly(w, "process listing")


def test_a_garbled_process_listing_refuses(w):
    w.control(ps_garbage=True)
    refuse_cleanly(w, "process listing")


def test_the_install_kills_nothing(w):
    w.control(ps_extra=["  200   100 bash /x/kalayantra_fleet.sh"])
    before = os.getpid()
    refuse_cleanly(w)
    assert os.getpid() == before
    assert [c for c in w.calls("ps") if c["argv"][0] != "-ww"] == []


def test_stop_files_absent_are_created_but_existing_ones_are_left_alone(w):
    (w.run / "STOP_k1").write_text("owner put this here\n")
    ok(w.install())
    assert (w.run / "STOP_k1").read_text() == "owner put this here\n"
    assert (w.run / "STOP_sutradhara").is_file()
    rc = w.receipt()
    by = {s["lane"]: s for s in rc["old_supervisors"]["stop_files"]}
    assert by["k1"]["path"] == str(w.run / "STOP_k1")


@pytest.mark.parametrize("kind", ["directory", "dangling_link"])
def test_a_stop_path_the_legacy_supervisor_would_not_read_as_a_stop_is_refused(w, kind):
    p = w.run / "STOP_k1"                              # kalayantra_fleet.sh: [ -f "$RUN/STOP_$lane" ]
    if kind == "directory":
        p.mkdir()
    else:
        p.symlink_to(w.base / "nowhere")
    before = w.snapshot()
    refused(w.install(), 1, "STOP_k1")
    assert w.snapshot() == before, "nothing written: no other STOP file either"


def test_a_process_that_appears_after_the_stop_files_fails_the_install(w):
    # the double of ps answers differently from the second listing on: the first sees nothing, the second a supervisor
    ps = w.tools / "ps"
    ps.write_text(ps.read_text().replace('if "-axo" in argv:', '''if "-axo" in argv:
    n = sum(1 for l in open("%s").read().splitlines() if '"tool": "ps"' in l and '-axo' in l)
    if n >= 2:
        control["ps_extra"] = ["  300   100 bash /x/kalayantra_fleet.sh"]
''' % w.calls_path))
    r = refused(w.install(), 3, "legacy supervisor")
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


# ================================================================================ failures after writing began
def test_a_deferred_component_listed_in_the_manifest_is_never_installed(w):
    ok(w.install())
    assert not list((w.root).rglob("kyveto.py"))


def test_failure_at_the_campaign_step_restores_the_trees(w):
    w.old_installation()
    for i in range(15):                               # the Claude/Madhav worktree count is already over the ceiling
        w.git("worktree", "add", "-q", "-b", "filler-%d" % i, str(w.wtroot / ("filler-%d" % i)))
    refused(w.install(), 3, "capacity")
    w.assert_old_installation_whole()
    assert not w.camp.exists() and w.ky_calls() == []
    assert [c for c in w.calls("launchctl") if c["argv"][0] != "print"] == []


def test_fifteen_registrations_are_over_the_ceiling(w):
    for i in range(14):                                # with src: exactly 15, one more than the 14 the packet allows
        w.git("worktree", "add", "-q", "-b", "filler-%d" % i, str(w.wtroot / ("filler-%d" % i)))
    refused(w.install(), 3, "capacity")
    assert not w.camp.exists() and not (w.run / "INSTALL_RECEIPT.json").exists()


# ---- B-01: after the first write nothing ends as exit 1
def test_an_unanswerable_second_process_listing_is_a_failure_not_a_refusal(w):
    w.begin_action()
    w.control(ps_fail_from_listing=2)                  # verification's listing answers; the one after the STOP files does not
    r = refused(w.install(action="INSTALL-1"), 3, "FAILED step 0")
    assert "process listing" in r.stderr and "REFUSED" not in r.stderr
    assert sorted(p.name for p in w.run.glob("STOP_*")) == sorted("STOP_" + lane for lane in LANES), "writing had begun"
    assert not (w.root / "fleet_live").exists() and not (w.run / "INSTALL_RECEIPT.json").exists()
    rec = w.action_record()
    assert rec["state"] == "FAILED" and rec["result"]["step"] == 0 and rec["result"]["exit"] == 3


def test_a_refusal_at_the_wrappers_step_restores_the_trees_and_fails_the_action(w):
    w.old_installation()
    w.begin_action()
    w.control(ps_link_at_listing=[2, str(w.src / FL / "bin" / "ky")])     # bin/ky becomes a link after verification
    r = refused(w.install(action="INSTALL-1"), 3, "FAILED step 3")
    assert "not a regular file" in r.stderr and "REFUSED" not in r.stderr and "trees restored" in r.stderr
    w.assert_old_installation_whole()
    assert not w.camp.exists() and w.ky_calls() == []
    rec = w.action_record()
    assert rec["state"] == "FAILED" and rec["result"]["step"] == 3 and rec["result"]["trees_restored"] is True


def test_a_refusal_at_the_campaign_step_restores_the_trees_and_fails_the_action(w):
    w.old_installation()
    w.begin_action()
    w.control(git_fail={"match": "worktree list", "from_call": 2, "rc": 128})      # verification's listing answers, step 5's does not
    r = refused(w.install(action="INSTALL-1", env={"KY_GIT": str(w.tools / "git")}), 3, "FAILED step 5")
    assert "worktree list" in r.stderr and "REFUSED" not in r.stderr and "trees restored" in r.stderr
    w.assert_old_installation_whole()
    assert not w.camp.exists() and w.ky_calls() == []
    assert [c for c in w.calls("launchctl") if c["argv"][0] != "print"] == []
    rec = w.action_record()
    assert rec["state"] == "FAILED" and rec["result"]["step"] == 5 and rec["result"]["trees_restored"] is True


def test_a_failure_before_the_tracker_restart_names_the_campaign_checkout_it_leaves(w):
    w.old_installation()
    r = refused(w.install(env={"KY_LAUNCHCTL": str(w.base / "no-such-launchctl")}), 3, "FAILED step 6")
    w.assert_old_installation_whole()
    assert w.camp.is_dir(), "step 5 created it; a failure does not remove a checkout"
    assert "campaign checkout" in r.stderr and str(w.camp) in r.stderr and "left in place" in r.stderr
    assert not (w.la / (TRACKER_LABEL + ".plist")).exists()


def test_a_campaign_branch_lookup_that_fails_is_not_read_as_no_branch(w):
    w.control(git_fail={"match": "refs/heads/kalayantra/campaign", "rc": 128})
    before = w.snapshot()
    r = refused(w.install(env={"KY_GIT": str(w.tools / "git")}), 1, "campaign")
    assert_nothing_written(w, before)
    assert "cannot be told" in r.stderr


def test_a_campaign_branch_that_cannot_track_origin_main_means_no_receipt(w):
    w.git("update-ref", "-d", "refs/remotes/origin/main")
    refused(w.install(), 3, "origin/main")
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


def test_fourteen_registrations_leave_room_for_the_campaign_checkout(w):
    for i in range(13):                                # src itself is the 14th registration under the policy root
        w.git("worktree", "add", "-q", "-b", "filler-%d" % i, str(w.wtroot / ("filler-%d" % i)))
    ok(w.install())
    assert w.camp.is_dir()


def test_an_existing_campaign_checkout_at_the_components_commit_is_reused(w):
    w.git("worktree", "add", "-q", "-b", "kalayantra/campaign", str(w.camp), w.components_commit)
    ok(w.install())
    assert w.receipt()["campaign_checkout"]["head"] == w.components_commit


def test_a_campaign_checkout_at_another_commit_is_refused_not_fast_forwarded(w):
    w.git("worktree", "add", "-q", "-b", "kalayantra/campaign", str(w.camp), w.approved)
    refuse_cleanly(w, "campaign")


def test_a_campaign_branch_at_another_commit_is_refused(w):
    w.git("branch", "kalayantra/campaign", w.approved)
    refuse_cleanly(w, "campaign")


def test_staged_action_unpublished_means_no_receipt(w):
    w.control(ky_fail_on="park")
    refused(w.install(), 3)
    assert not (w.run / "INSTALL_RECEIPT.json").exists()
    assert w.calls("preflight") == [] and w.calls("kyversion") == []


def test_ky_exit_zero_without_the_event_is_not_published(w):
    w.control(ky_swallow=True)
    refused(w.install(), 3, "not found in the event log")
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


@pytest.mark.parametrize("hook", ["KY_LOOP_SLEEP_SCALE", "KY_LOOP_TEST_CONTEXT"])
def test_a_test_hook_variable_in_a_plist_means_no_receipt(w, hook):
    w.control(plist_hook=hook)
    refused(w.install(), 3, hook)
    assert not (w.run / "INSTALL_RECEIPT.json").exists()
    assert w.calls("preflight") == []


def test_a_missing_loop_plist_means_no_receipt(w):
    w.control(kyctl_rc=1)
    refused(w.install(), 3, "kyctl")
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


def test_qualification_not_pass_means_no_receipt(w):
    w.control(qualify_result="FAIL")
    refused(w.install(), 3, "qualif")
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


def test_qualification_runs_positive_controls_for_every_role(w):
    w.control(qualify_require_control=True)
    ok(w.install())
    qualified = [c["argv"] for c in w.calls("kyqualify") if c["argv"][0] == "qualify"]
    assert len(qualified) == 4 and all("--control" in argv for argv in qualified)
    assert all(q["result"] == "PASS" for q in w.receipt()["qualifications"])


def test_a_qualification_receipt_that_passes_the_check_is_not_redone(w):
    q = w.run / "QUALIFICATIONS"
    q.mkdir(parents=True)
    (q / "bootstrap-builder-claude-opus-5-5.json").write_text(json.dumps(
        {"role": "bootstrap-builder", "model": "claude-opus-5-5", "context": "launchd", "result": "PASS", "schema": "ky.qualification/1"}))
    ok(w.install())
    qualified = [c["argv"] for c in w.calls("kyqualify") if c["argv"][0] == "qualify"]
    assert len(qualified) == 3 and not [a for a in qualified if "bootstrap-builder" in a[a.index("--out") + 1]]
    checks = [c["argv"] for c in w.calls("kyqualify") if c["argv"][0] == "check"]
    assert all("--require-context" in a and "--verify-evidence" in a for a in checks)


def test_the_loop_roles_are_qualified_from_the_config_kyloop_prints(w):
    ok(w.install())
    assert [c["argv"] for c in w.calls("kyloop")] == [["admin", "launch-config", "planner"], ["admin", "launch-config", "conductor"]]
    assert all(c["isolated"] is True for c in w.calls("kyloop")), "python -I, like every other reviewed program"


def test_preflight_failure_means_no_receipt(w):
    w.control(preflight_rc=1)
    refused(w.install(), 3, "preflight")
    assert not (w.run / "INSTALL_RECEIPT.json").exists() and w.calls("kyversion") == []


def test_kyversion_failure_renames_the_receipt_refused(w):
    w.control(kyversion_rc=1)
    refused(w.install(), 3, "kyversion")
    assert not (w.run / "INSTALL_RECEIPT.json").exists()
    assert (w.run / "INSTALL_RECEIPT.json.refused").is_file()


def test_kyversion_exit_zero_is_the_pass_whatever_it_prints(w):
    w.control(kyversion_stdout="kyversion: accepted (bootstrap)")       # the packet's interface is the exit code
    ok(w.install())
    assert (w.run / "INSTALL_RECEIPT.json").is_file() and not (w.run / "INSTALL_RECEIPT.json.refused").exists()


def test_a_health_answer_from_a_tracker_serving_another_event_log_is_not_this_installation(w):
    w.control(health_events_path="/somewhere/else/run/EVENTS.jsonl")
    refused(w.install(env={"KY_INSTALL_WAIT_S": "2"}), 3, "another event log")
    assert not (w.run / "INSTALL_RECEIPT.json").exists() and w.ky_calls() == []


@pytest.mark.parametrize("drop", ["event_log", "server_started_at"])
def test_a_health_answer_in_a_shape_the_tracker_does_not_emit_is_unknown(w, drop):
    w.control(health_drop=[drop])
    refused(w.install(env={"KY_INSTALL_WAIT_S": "2"}), 3, drop)
    assert not (w.run / "INSTALL_RECEIPT.json").exists() and w.ky_calls() == []


def test_a_health_answer_older_than_the_recorded_process_is_not_its_answer(w):
    w.control(health_started_at="2020-01-01T00:00:00+00:00")
    refused(w.install(env={"KY_INSTALL_WAIT_S": "2"}), 3, "server_started_at")
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


def test_unhealthy_tracker_means_no_receipt(w):
    w.control(health_update={"model_error": "plan model rejected"})
    refused(w.install(env={"KY_INSTALL_WAIT_S": "2"}), 3, "model_error")
    assert not (w.run / "INSTALL_RECEIPT.json").exists() and w.ky_calls() == []


def test_a_tracker_that_never_answers_means_no_receipt(w):
    w.control(health_status=503)
    refused(w.install(env={"KY_INSTALL_WAIT_S": "2"}), 3, "health")
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


def test_a_tracker_process_older_than_the_swap_is_not_the_installed_revision(w):
    (w.base / "pre.plist").write_bytes(plistlib.dumps({"Label": TRACKER_LABEL, "ProgramArguments": ["x", "--port", str(w.port)],
                                                       "EnvironmentVariables": {"PRAVAHA_EVENTS": str(w.run / "EVENTS.jsonl")}}))
    w.start_tracker()
    old_pid = w.tracker_pid()
    time.sleep(1.2)
    w.control(launchctl_bootout_noop=True, launchctl_bootstrap_noop=True)
    refused(w.install(env={"KY_INSTALL_WAIT_S": "2"}), 3, "after the swap")
    assert w.tracker_pid() == old_pid
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


def test_launchctl_bootstrap_failure_means_no_receipt(w):
    w.control(launchctl_bootstrap_rc=5)
    refused(w.install(), 3, "FAILED step 6")
    assert len([c for c in w.calls("launchctl") if c["argv"][0] == "bootstrap"]) == 3
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


@pytest.mark.parametrize("control,attempts", [("launchctl_bootstrap_fail_once", 2),
                                             ("launchctl_bootout_pending_prints", 1)])
def test_tracker_restart_survives_launchctl_unload_race(w, control, attempts):
    w.control(**{control: 2 if control.endswith("prints") else True})
    ok(w.install(env={"KY_INSTALL_WAIT_S": "2"}))
    calls = [c["argv"] for c in w.calls("launchctl")]
    bootout = next(i for i, argv in enumerate(calls) if argv[0] == "bootout")
    bootstrap = next(i for i, argv in enumerate(calls) if argv[0] == "bootstrap")
    assert len([argv for argv in calls if argv[0] == "bootstrap"]) == attempts
    assert len([argv for argv in calls[bootout + 1:bootstrap] if argv[0] == "print"]) >= (
        3 if control.endswith("prints") else 1)
    rc = w.receipt()
    assert rc["tracker_revision"]["pid"] == w.tracker_pid() and rc["tracker_revision"]["health"]["ok"] is True
    newest = max(p.stat().st_mtime for p in (w.root / "tracker_live").rglob("*.py"))
    started = time.mktime(time.strptime(rc["tracker_revision"]["process_start"], "%a %b %d %H:%M:%S %Y"))
    assert started >= int(newest) + 1


def test_tracker_unload_that_never_finishes_fails_step_6_without_bootstrap(w):
    w.control(launchctl_bootout_pending_prints=1000)
    refused(w.install(env={"KY_INSTALL_WAIT_S": "1"}), 3, "FAILED step 6")
    assert not [c for c in w.calls("launchctl") if c["argv"][0] == "bootstrap"]
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


# ================================================================================ the legacy step
def claim(w, worker, item, state="acquired", branch="kalayantra/x", head="a" * 40, log=True, claim_id=None):
    """A claim as claims.py leaves it: the event in the log and the same event as the worker's record."""
    d = w.run / "claims"
    d.mkdir(parents=True, exist_ok=True)
    ev = {"kind": "claim", "actor": "stream-K:" + worker, "item": item, "state": state, "worker_id": worker,
          "claim_id": claim_id or "c-" + worker, "lease_s": 10800, "expires_at": "2026-10-12T10:53:12+00:00",
          "ts": "2026-10-12T07:53:12+00:00", "branch": branch, "head": head, "step": None}
    if log:
        w.append_event(ev)
    (d / (worker + ".json")).write_text(json.dumps(ev, ensure_ascii=False, indent=2) + "\n")


def test_active_legacy_claims_are_released_with_ky_after_the_supervisors_are_known_gone(w):
    claim(w, "k1", "K8-R26")
    claim(w, "k2", "K1-1", state="released")
    claim(w, "k3", "K1-2", state="expired")
    ok(w.install())
    releases = [c for c in w.calls("ky") if c["argv"] == ["release"]]
    assert [c["env"]["KY_LANE"] for c in releases] == ["k1"]
    assert json.loads((w.run / "claims" / "k1.json").read_text())["state"] == "released"
    legacy = w.receipt()["legacy"]
    by = {c["worker_id"]: c for c in legacy["claims"]}
    assert by["k1"]["action"] == "released" and by["k1"]["state_after"] == "released"
    assert by["k2"]["action"] == "already_ended" and by["k3"]["action"] == "already_ended"
    assert legacy["unresolved"] == []
    order = [c["tool"] for c in w.calls()]
    assert order.index("ps") < order.index("ky"), "a legacy claim is released only after the process check"
    assert by["k1"]["release_event"]["line"] >= 1 and by["k1"]["release_event"]["sha256"]
    released = [e for e in w.events() if e.get("kind") == "claim" and e.get("state") == "released"]
    assert [e["claim_id"] for e in released] == ["c-k2", "c-k1"], "the fixture's k2, then the one release this run made"


def test_a_release_the_event_log_does_not_show_is_unresolved(w):
    claim(w, "k1", "K8-R26")
    w.control(ky_release_record_only=True)             # the record says released, the log (the authority) does not
    ok(w.install())
    legacy = w.receipt()["legacy"]
    assert legacy["claims"][0]["action"] == "unresolved" and legacy["claims"][0]["state_after"] == "released"
    assert [u["worker_id"] for u in legacy["unresolved"]] == ["k1"] and "event log" in legacy["unresolved"][0]["reason"]


def test_a_claim_in_a_state_the_tracker_does_not_write_is_unresolved_not_already_ended(w):
    claim(w, "k2", "K1-1", state="handed-over", log=False)
    (w.run / "claims" / "k3.json").write_text(json.dumps({"worker_id": "k3", "item": "K1-2"}))     # no state at all
    ok(w.install())
    legacy = w.receipt()["legacy"]
    by = {c["worker_id"]: c for c in legacy["claims"]}
    assert by["k2"]["action"] == "unresolved" and by["k3"]["action"] == "unresolved"
    assert sorted(u["worker_id"] for u in legacy["unresolved"]) == ["k2", "k3"]
    assert [c for c in w.calls("ky") if c["argv"] == ["release"]] == []


def test_a_claim_of_a_worker_that_is_not_a_legacy_lane_is_never_released(w):
    claim(w, "J-20261012T000000Z-kyroute", "KV3-B-KYROUTE")
    claim(w, "k1", "K8-R26")
    ok(w.install())
    assert [c["env"]["KY_LANE"] for c in w.calls("ky") if c["argv"] == ["release"]] == ["k1"]
    job = json.loads((w.run / "claims" / "J-20261012T000000Z-kyroute.json").read_text())
    assert job["state"] == "acquired", "a v3 job's claim is its own, not a legacy claim"
    legacy = w.receipt()["legacy"]
    by = {c["worker_id"]: c for c in legacy["claims"]}
    assert by["J-20261012T000000Z-kyroute"]["action"] == "unresolved" and by["k1"]["action"] == "released"
    assert [u["worker_id"] for u in legacy["unresolved"]] == ["J-20261012T000000Z-kyroute"]


def test_unreadable_event_lines_mean_no_pr_is_adopted(w):
    head = "b" * 40
    ok(w.install())                                    # every staged action is published: step 6 owes the log nothing more
    w.append_event({"kind": "item", "actor": "stream-K:k1", "item": "K1-1", "state": "review",
                    "detail": "PR #3300 @ %s. ready" % head, "ts": "2026-10-12T00:00:00+00:00"})
    with open(w.run / "EVENTS.jsonl", "a") as f:
        f.write("{a later registration that cannot be read\n")
    w.control(prs=[{"number": 3300, "headRefName": "kalayantra/k1-1", "headRefOid": head, "url": "u"}])
    ok(w.install())
    assert not (w.run / "legacy" / "legacy-3300").exists()
    legacy = w.receipt()["legacy"]
    assert legacy["prs"]["adopted"] == []
    assert [(u["kind"], u["number"]) for u in legacy["unresolved"]] == [("pr", 3300)]
    assert "unreadable" in legacy["unresolved"][0]["reason"]


def test_a_release_that_did_not_end_the_claim_is_unresolved_not_reported_released(w):
    claim(w, "k1", "K8-R26")
    w.control(ky_release_noop=True)
    ok(w.install())
    legacy = w.receipt()["legacy"]
    assert [u["kind"] for u in legacy["unresolved"]] == ["claim"] and legacy["unresolved"][0]["worker_id"] == "k1"
    assert legacy["claims"][0]["action"] == "unresolved"


def test_an_unreadable_claim_is_unresolved(w):
    (w.run / "claims").mkdir()
    (w.run / "claims" / "k4.json").write_text("{nope")
    ok(w.install())
    assert w.receipt()["legacy"]["unresolved"][0]["kind"] == "claim"


def test_open_prs_with_a_registered_head_are_adopted_one_state_file_each(w):
    head = "b" * 40
    (w.run / "EVENTS.jsonl").write_text(json.dumps({"kind": "item", "actor": "stream-K", "item": "K1-1", "state": "review",
                                                     "detail": "PR #3300 @ %s" % head, "ts": "2026-10-12T00:00:00+00:00"}) + "\n")
    claim(w, "k5", "K1-1", state="released", branch="kalayantra/k1-1", head="c" * 40)
    w.control(prs=[{"number": 3300, "headRefName": "kalayantra/k1-1", "headRefOid": head, "url": "u"},
                   {"number": 3301, "headRefName": "kalayantra/k2-2", "headRefOid": "d" * 40, "url": "u"},
                   {"number": 3302, "headRefName": "feature/other", "headRefOid": "e" * 40, "url": "u"}])
    ok(w.install())
    state = json.loads((w.run / "legacy" / "legacy-3300" / "state.json").read_text())
    assert state["job_id"] == "legacy-3300" and state["item"] == "K1-1" and state["pr"] == 3300
    assert state["head"] == head and state["branch"] == "kalayantra/k1-1"
    assert state["session_id"] is None and state["attempts"] is None, "unknown stays null"
    assert not (w.run / "legacy" / "legacy-3301").exists() and not (w.run / "legacy" / "legacy-3302").exists()
    legacy = w.receipt()["legacy"]
    assert [p["number"] for p in legacy["prs"]["adopted"]] == [3300]
    assert [(u["kind"], u["number"]) for u in legacy["unresolved"]] == [("pr", 3301)]
    gh = w.calls("gh")[0]["argv"]
    assert gh[:2] == ["pr", "list"] and "--state" in gh and "open" in gh


def test_a_pr_whose_head_moved_since_registration_is_not_adopted(w):
    (w.run / "EVENTS.jsonl").write_text(json.dumps({"kind": "item", "actor": "stream-K", "item": "K1-1", "state": "review",
                                                     "detail": "PR #3300 @ %s" % ("b" * 40), "ts": "2026-10-12T00:00:00+00:00"}) + "\n")
    w.control(prs=[{"number": 3300, "headRefName": "kalayantra/k1-1", "headRefOid": "f" * 40, "url": "u"}])
    ok(w.install())
    assert not (w.run / "legacy" / "legacy-3300").exists()
    assert "moved" in w.receipt()["legacy"]["unresolved"][0]["reason"]


def test_an_existing_legacy_job_state_is_never_overwritten(w):
    head = "b" * 40
    (w.run / "EVENTS.jsonl").write_text(json.dumps({"kind": "item", "actor": "stream-K", "item": "K1-1", "state": "review",
                                                     "detail": "PR #3300 @ %s" % head, "ts": "2026-10-12T00:00:00+00:00"}) + "\n")
    (w.run / "legacy" / "legacy-3300").mkdir(parents=True)
    (w.run / "legacy" / "legacy-3300" / "state.json").write_text('{"dispatcher": "was here"}')
    w.control(prs=[{"number": 3300, "headRefName": "kalayantra/k1-1", "headRefOid": head, "url": "u"}])
    ok(w.install())
    assert (w.run / "legacy" / "legacy-3300" / "state.json").read_text() == '{"dispatcher": "was here"}'
    legacy = w.receipt()["legacy"]
    assert legacy["prs"]["adopted"] == [], "a file that is not this PR's adoption record is not an adoption"
    assert [(u["kind"], u["number"]) for u in legacy["unresolved"]] == [("pr", 3300)]


def test_a_second_run_keeps_the_adoption_it_wrote(w):
    head = "b" * 40
    w.append_event({"kind": "item", "actor": "stream-K:k1", "item": "K1-1", "state": "review",
                    "detail": "PR #3300 @ %s" % head, "ts": "2026-10-12T00:00:00+00:00"})
    w.control(prs=[{"number": 3300, "headRefName": "kalayantra/k1-1", "headRefOid": head, "url": "u"}])
    ok(w.install())
    first = (w.run / "legacy" / "legacy-3300" / "state.json").read_bytes()
    ok(w.install())
    assert (w.run / "legacy" / "legacy-3300" / "state.json").read_bytes() == first
    adopted = w.receipt()["legacy"]["prs"]["adopted"]
    assert [(a["number"], a["existing_state_kept"]) for a in adopted] == [(3300, True)]
    assert w.receipt()["legacy"]["unresolved"] == []


def test_an_unanswerable_pr_listing_means_no_receipt(w):
    w.control(gh_rc=1)
    refused(w.install(), 3, "gh")
    assert not (w.run / "INSTALL_RECEIPT.json").exists()


def test_legacy_checkpoints_are_listed_with_hashes(w):
    for name in ("adhikarin.cycle106.state.json", "k3.cycle9.state.json", "unrelated.state.json"):
        (w.run / name).write_text(json.dumps({"n": name}))
    ok(w.install())
    cp = w.receipt()["legacy"]["checkpoints"]
    assert cp["count"] == 2 and sorted(f["path"] for f in cp["files"]) == [str(w.run / "adhikarin.cycle106.state.json"),
                                                                             str(w.run / "k3.cycle9.state.json")]
    assert all(f["sha256"] for f in cp["files"])


# ================================================================================ the action record
def test_an_install_action_is_completed_with_the_receipt(w):
    w.begin_action()
    ok(w.install(action="INSTALL-1"))
    rec = w.action_record()
    assert rec["state"] == "DONE" and rec["result"]["receipt"] == str(w.run / "INSTALL_RECEIPT.json")
    assert rec["result"]["receipt_sha256"] == sha_file(w.run / "INSTALL_RECEIPT.json")


def installed_state(w):
    """The snapshot without the action records and their locks (a new record is the one thing a later run adds)."""
    snap = w.snapshot()
    snap["root"] = {k: v for k, v in snap["root"].items()
                    if k != "run" and not k.startswith(("run/actions", "run/locks"))}
    return snap


def test_a_rerun_with_a_done_action_changes_nothing(w):
    w.begin_action()
    ok(w.install(action="INSTALL-1"))
    assert w.action_record()["state"] == "DONE"
    claim(w, "k1", "K8-R26")                           # work a second run WOULD do: it must not be done under a DONE record
    before, record = w.snapshot(), (w.run / "actions" / "INSTALL-1.json").read_bytes()
    r = refused(w.install(action="INSTALL-1"), 1, "E_ACTION_STATE")
    assert "DONE" in r.stderr and "INTENDED" in r.stderr
    after = w.snapshot()
    assert after == before, "a completed action id opens nothing: no tree, receipt, tracker or claim was touched"
    assert (w.run / "actions" / "INSTALL-1.json").read_bytes() == record
    assert json.loads((w.run / "claims" / "k1.json").read_text())["state"] == "acquired"


def test_a_second_run_under_a_fresh_intended_action_changes_and_republishes_nothing(w):
    w.begin_action()
    ok(w.install(action="INSTALL-1"))
    before = installed_state(w)
    receipt = (w.run / "INSTALL_RECEIPT.json").read_bytes()
    w.begin_action("INSTALL-2")
    ok(w.install(action="INSTALL-2"))
    after = installed_state(w)
    assert after["ky"] == before["ky"] and after["launchctl"] == before["launchctl"]
    assert after["root"] == before["root"] and after["la"] == before["la"]
    assert (w.run / "INSTALL_RECEIPT.json").read_bytes() == receipt
    rec = w.action_record("INSTALL-2")
    assert rec["state"] == "DONE" and rec["result"]["receipt_sha256"] == sha_bytes(receipt), "the later run is on record"
    assert w.action_record("INSTALL-1")["state"] == "DONE"


def test_an_action_in_a_state_other_than_intended_is_refused_before_anything_is_written(w):
    w.begin_action()
    path = w.run / "actions" / "INSTALL-1.json"
    rec = json.loads(path.read_text())
    rec["state"] = "PAUSED"
    path.write_text(json.dumps(rec))
    before = w.snapshot()
    refused(w.install(action="INSTALL-1"), 1, "E_ACTION_STATE")
    assert w.snapshot() == before


def test_an_action_that_cannot_be_completed_leaves_no_receipt(w):
    w.begin_action()
    w.control(preflight_spoils_action="INSTALL-1")     # the record is ended by someone else while the installation runs
    r = refused(w.install(action="INSTALL-1"), 3, "action record could not be completed")
    assert not (w.run / "INSTALL_RECEIPT.json").exists(), "exit 3 means no receipt"
    assert (w.run / "INSTALL_RECEIPT.json.refused").is_file()
    assert r.stdout.strip() == ""


def test_a_failed_install_fails_its_action(w):
    w.begin_action()
    w.control(preflight_rc=1)
    refused(w.install(action="INSTALL-1"), 3)
    rec = w.action_record()
    assert rec["state"] == "FAILED" and "preflight" in json.dumps(rec["result"])


def test_a_failed_action_must_be_retried_by_its_owner_first(w):
    w.begin_action()
    w.control(preflight_rc=1)
    refused(w.install(action="INSTALL-1"), 3)
    w.control(preflight_rc=0)
    before = w.snapshot()
    refused(w.install(action="INSTALL-1"), 1, "E_ACTION_STATE")
    assert w.snapshot()["root"] == before["root"]
    kyaction.retry(str(w.run), "INSTALL-1")
    ok(w.install(action="INSTALL-1"))
    assert w.action_record()["state"] == "DONE"


@pytest.mark.parametrize("what", ["missing", "kind", "manifest", "commit", "malformed"])
def test_an_action_that_does_not_bind_this_manifest_and_source_is_refused(w, what):
    if what == "kind":
        w.begin_action(kind="push")
    elif what == "manifest":
        w.begin_action(inputs={"manifest_sha256": "0" * 64, "source_commit": w.components_commit})
    elif what == "commit":
        w.begin_action(inputs={"manifest_sha256": sha_file(w.manifest_path), "source_commit": "1" * 40})
    elif what == "malformed":
        w.begin_action()
        (w.run / "actions" / "INSTALL-1.json").write_text("{nope")
    before = w.snapshot()
    refused(w.install(action="INSTALL-1"), 1, "action")
    assert w.snapshot()["root"] == before["root"] and w.snapshot()["la"] == before["la"]


def test_a_refused_install_leaves_its_action_intended(w):
    w.begin_action()
    w.control(kymanifest_rc=1)
    refused(w.install(action="INSTALL-1"), 1)
    assert w.action_record()["state"] == "INTENDED"


# ================================================================================ the environment given to children
@pytest.fixture
def installer_program():
    """Load the real installer helpers without running main or an installation."""
    program = INSTALL.read_text().split("\n: <<'KYINSTALL_PY'\n", 1)[1].rsplit("\nKYINSTALL_PY\n", 1)[0]
    program = program.rsplit("\nsys.exit(main(sys.argv[1:]))", 1)[0]
    namespace = {"__file__": str(INSTALL)}
    exec(compile(program, str(INSTALL), "exec"), namespace)
    return namespace


def preflight_environment(installer, monkeypatch, tmp_path, real_root):
    """Capture step 10's launch boundary; no child runs and no receipt is written."""
    fixture = tmp_path / "fixture"
    root = REAL_ROOT if real_root else str(fixture / "kyroot")
    env = {"HOME": pwd.getpwuid(os.getuid()).pw_dir, "KY_SCRATCH": str(tmp_path),
           "CLAUDE_BIN": str(fixture / "tools" / "claude")}
    if not real_root:
        env.update(KY_LAUNCHAGENTS_DIR=str(fixture / "LaunchAgents"), KY_LAUNCHCTL=str(fixture / "tools" / "launchctl"),
                   KY_CAMPAIGN_CHECKOUT=str(fixture / "campaign"), PRAVAHA_URL="http://127.0.0.1:18767")
    ctx = installer["decide_environment"]({"--root": root, "--source": str(fixture / "source"),
                                           "--manifest": str(fixture / "manifest.json"), "--action": "INSTALL-1"}, env)
    assert ctx.is_real is real_root
    calls = []

    def capture(argv, child_env, **kwargs):
        calls.append((argv, child_env))
        return installer["Out"](1, "", "stop before receipt")

    monkeypatch.setitem(installer, "run", capture)
    with pytest.raises(installer["Failed"]):
        installer["step_receipt"](ctx)
    assert len(calls) == 1
    assert calls[0][0] == ["/bin/bash", str(Path(ctx.fleet_live) / "preflight.sh"), "launch"]
    return calls[0][1]


@pytest.fixture
def wrapper_decision():
    """Execute the repository wrapper's refusal logic, stopping before its execve."""
    wrapper = FLEET / "bin" / "ky"
    program = wrapper.read_text().split("# --- mode decision: end ---", 1)[0]
    namespace = {"__file__": str(wrapper)}
    exec(compile(program, str(wrapper), "exec"), namespace)
    return namespace["decide"]


def test_real_root_preflight_gets_no_pravaha_override(installer_program, monkeypatch, tmp_path):
    env = preflight_environment(installer_program, monkeypatch, tmp_path, real_root=True)
    assert {name for name in env if name.startswith("PRAVAHA_")} == set()
    assert env["KY_ROOT"] == REAL_ROOT and env["KY_RUN"] == REAL_ROOT + "/run"


@pytest.mark.parametrize("real_root,mode", [(True, "live"), (False, "fixture")])
def test_preflight_environment_is_accepted_by_the_real_wrapper_rule(
        installer_program, wrapper_decision, monkeypatch, tmp_path, capsys, real_root, mode):
    env = preflight_environment(installer_program, monkeypatch, tmp_path, real_root)
    assert wrapper_decision(env)[0] == mode
    if not real_root:
        fixture = tmp_path / "fixture"
        assert {name: value for name, value in env.items() if name.startswith("PRAVAHA_")} == {
            "PRAVAHA_HOME": str(fixture / "kyroot"), "PRAVAHA_EVENTS": str(fixture / "kyroot" / "run" / "EVENTS.jsonl"),
            "PRAVAHA_PLAN_MODEL": str(fixture / "campaign" / PLAN_MODEL), "PRAVAHA_REPO": str(fixture / "campaign"),
            "PRAVAHA_HOLD": str(fixture / "kyroot" / "HOLD"), "PRAVAHA_TRACKER_PORT": "18767",
            "PRAVAHA_URL": "http://127.0.0.1:18767"}
    # Negative control: the old lone-URL environment must still fail closed.
    partial = {name: value for name, value in env.items() if not name.startswith("PRAVAHA_")}
    partial["PRAVAHA_URL"] = "http://127.0.0.1:8767" if real_root else "http://127.0.0.1:18767"
    with pytest.raises(SystemExit) as refused_override:
        wrapper_decision(partial)
    assert refused_override.value.code == 78
    assert "PRAVAHA_HOME: not set" in capsys.readouterr().err


def test_children_get_a_whitelisted_environment_and_credentials_never_pass(w):
    ok(w.install(env={"DATABASE_URL": "postgres://secret", "PGPASSWORD": "secret", "ANTHROPIC_API_KEY": "secret",
                      "PYTHONPATH": "/evil", "GIT_DIR": "/evil"}))
    log = w.calls_path.read_text()
    assert "secret" not in log and "/evil" not in log
    pre = w.calls("preflight")[0]["env"]
    assert pre["KY_ROOT"] == str(w.root) and pre["KY_RUN"] == str(w.run) and pre["KY_FLEET"] == str(w.root / "fleet_live")
    assert pre["KY_SOURCE_REPO"] == str(w.camp) and pre["CLAUDE_BIN"] == str(w.tools / "claude") and pre["PRAVAHA_URL"] == w.url


def test_install_writes_nothing_outside_the_scratch_world(w):
    before_home = tree_state(w.home)
    ok(w.install())
    assert tree_state(w.home) == before_home
    assert not Path(REAL_ROOT + "/fleet_live.new").exists()


# ================================================================================ review round 2
# ---- R2-B-01: exit 3 leaves no receipt — not this run's, and not an earlier run's that this run did not re-earn
RECEIPT = "INSTALL_RECEIPT.json"


def install_once(w):
    ok(w.install())
    return (w.run / RECEIPT).read_bytes()


def assert_failed_without_a_receipt(w, r, step, earlier):
    refused(r, 3, "FAILED step %d" % step)
    assert not (w.run / RECEIPT).exists(), "exit 3 left a receipt this run did not earn:\n" + r.stderr
    assert "there is no receipt" in r.stderr
    assert (w.run / (RECEIPT + ".superseded")).read_bytes() == earlier, "the earlier receipt is kept, moved aside"


def test_a_second_run_that_cannot_publish_a_staged_action_leaves_no_receipt(w):
    earlier = install_once(w)
    log = w.run / "EVENTS.jsonl"
    lines = log.read_text().splitlines(keepends=True)
    assert json.loads(lines[-1])["item"] == "KV3-SCHEMA-1"
    log.write_text("".join(lines[:-1]))                # the block is unpublished again, and ky will refuse it
    w.control(ky_fail_on="block")
    assert_failed_without_a_receipt(w, w.install(), 6, earlier)
    assert len(w.calls("preflight")) == 1 and len(w.calls("kyversion")) == 1, "the failed run reached neither"


@pytest.mark.parametrize("step,control", [(7, {"gh_rc": 1}), (8, {"plist_hook": "KY_LOOP_TEST_CONTEXT"}),
                                          (8, {"plist_hook": "KY_LOOP_SLEEP_SCALE"}), (8, {"kyctl_rc": 1}),
                                          (10, {"preflight_rc": 1})])
def test_a_second_run_that_fails_after_changing_nothing_leaves_no_receipt(w, step, control):
    earlier = install_once(w)
    w.control(**control)
    assert_failed_without_a_receipt(w, w.install(), step, earlier)


def test_a_second_run_whose_qualification_is_not_pass_leaves_no_receipt(w):
    earlier = install_once(w)
    for p in (w.run / "QUALIFICATIONS").iterdir():
        p.unlink()
    w.control(qualify_result="FAIL")
    assert_failed_without_a_receipt(w, w.install(), 9, earlier)


def test_a_second_run_that_restarts_a_dead_tracker_and_then_fails_leaves_no_receipt(w):
    earlier = install_once(w)
    dead = json.loads(earlier)["tracker_revision"]["pid"]
    w.stop_tracker()
    w.control(preflight_rc=1)
    r = w.install()
    assert_failed_without_a_receipt(w, r, 10, earlier)
    assert w.tracker_pid() not in (None, dead), "the rerun restarted the tracker: the earlier receipt names a dead process"
    assert "was restarted" in r.stderr


def test_a_second_run_that_sees_a_legacy_supervisor_after_the_stop_files_leaves_no_receipt(w):
    earlier = install_once(w)                          # listings 1 and 2; the second run's are 3 (verification) and 4 (step 0)
    w.control(ps_fail_from_listing=4)
    assert_failed_without_a_receipt(w, w.install(), 0, earlier)


def test_a_second_run_that_fails_at_the_campaign_step_leaves_no_receipt(w):
    earlier = install_once(w)
    w.control(git_fail={"match": "worktree list", "from_call": 2, "rc": 128})
    assert_failed_without_a_receipt(w, w.install(env={"KY_GIT": str(w.tools / "git")}), 5, earlier)


def test_a_second_run_under_an_action_that_fails_leaves_no_receipt_and_says_so_in_the_record(w):
    w.begin_action()
    ok(w.install(action="INSTALL-1"))
    earlier = (w.run / RECEIPT).read_bytes()
    w.begin_action("INSTALL-2")
    w.control(preflight_rc=1)
    assert_failed_without_a_receipt(w, w.install(action="INSTALL-2"), 10, earlier)
    rec = w.action_record("INSTALL-2")
    assert rec["state"] == "FAILED" and rec["result"]["receipt_present"] is False


def test_a_run_that_succeeds_after_a_failed_one_writes_its_own_receipt(w):
    earlier = install_once(w)
    w.control(preflight_rc=1)
    assert_failed_without_a_receipt(w, w.install(), 10, earlier)
    w.control(preflight_rc=0)
    ok(w.install())
    assert (w.run / RECEIPT).is_file() and not (w.run / (RECEIPT + ".superseded")).exists()
    assert w.calls("kyversion")[-1]["receipt_present"] is True


# ---- the sweep: a sentence, a state or a record is said only when this run observed it
def test_a_restart_that_did_not_complete_is_not_reported_as_a_restart(w):
    w.control(launchctl_bootstrap_rc=5)
    r = refused(w.install(), 3, "FAILED step 6")
    assert w.tracker_pid() is None
    assert "was restarted" not in r.stderr, r.stderr
    assert "restart was begun and did not complete" in r.stderr and "there is no receipt" in r.stderr


def test_a_rollback_that_could_not_restore_a_tree_is_not_reported_as_restored(w):
    w.old_installation()
    w.begin_action()
    w.control(git_fail={"match": "worktree list", "from_call": 2, "rc": 128, "remove": str(w.root / "fleet_live.old")})
    r = refused(w.install(action="INSTALL-1", env={"KY_GIT": str(w.tools / "git")}), 3, "FAILED step 5")
    assert "trees NOT restored" in r.stderr and "fleet_live.old" in r.stderr, r.stderr
    assert "install.sh: trees restored" not in r.stderr
    assert not (w.root / "fleet_live" / "old.txt").exists(), "the old fleet tree could not come back"
    assert w.action_record()["result"]["trees_restored"] is False
    assert not (w.run / RECEIPT).exists()


def test_a_claim_record_that_reads_released_while_the_event_log_shows_it_active_is_unresolved(w):
    claim(w, "k2", "K1-1")                             # the log (the tracker's authority): acquired
    record = w.run / "claims" / "k2.json"
    record.write_text(json.dumps(dict(json.loads(record.read_text()), state="released"), indent=2) + "\n")
    claim(w, "k3", "K1-2", state="expired", log=False)     # a record no event backs at all
    ok(w.install())
    legacy = w.receipt()["legacy"]
    by = {c["worker_id"]: c for c in legacy["claims"]}
    assert by["k2"]["action"] == "unresolved" and by["k3"]["action"] == "unresolved"
    assert "event log" in by["k2"]["reason"] and "'acquired'" in by["k2"]["reason"]
    assert sorted(u["worker_id"] for u in legacy["unresolved"] if u["kind"] == "claim") == ["k2", "k3"]
    assert [c for c in w.calls("ky") if c["argv"] == ["release"]] == []


def test_an_active_claim_in_the_event_log_that_no_record_shows_is_unresolved(w):
    claim(w, "k1", "K8-R25", claim_id="c-first")       # claims._record keeps ONE record per worker: the second claim
    claim(w, "k1", "K8-R26", claim_id="c-second")      # overwrites it, and the first stays active in the log only
    ok(w.install())
    legacy = w.receipt()["legacy"]
    assert [(c["worker_id"], c["claim_id"], c["action"]) for c in legacy["claims"]] == [("k1", "c-second", "released")]
    assert [(u["kind"], u["item"], u["claim_id"], u["worker_id"]) for u in legacy["unresolved"]] == \
        [("claim_event", "K8-R25", "c-first", "k1")]
    assert "no record" in legacy["unresolved"][0]["reason"]
    assert ok(w.install()) and w.receipt()["legacy"]["unresolved"][0]["claim_id"] == "c-first", "still owed on a rerun"


def test_a_pr_registration_its_item_has_since_replaced_adopts_nothing(w):
    old, new = "b" * 40, "c" * 40
    for number, head in ((3300, old), (3305, new)):    # completion.py reads the item's LATEST review event, as here
        w.append_event({"kind": "item", "actor": "stream-K:k1", "item": "K1-1", "state": "review",
                        "detail": "PR #%d @ %s" % (number, head), "ts": "2026-10-12T00:00:00+00:00"})
    w.control(prs=[{"number": 3300, "headRefName": "kalayantra/k1-1", "headRefOid": old, "url": "u"},
                   {"number": 3305, "headRefName": "kalayantra/k1-1b", "headRefOid": new, "url": "u"}])
    ok(w.install())
    legacy = w.receipt()["legacy"]
    assert [a["number"] for a in legacy["prs"]["adopted"]] == [3305]
    assert not (w.run / "legacy" / "legacy-3300").exists()
    assert [(u["kind"], u["number"]) for u in legacy["unresolved"]] == [("pr", 3300)]
    assert "latest review" in legacy["unresolved"][0]["reason"]


def test_reinstall_does_not_recreate_old_dispatcher_adoption_folder(w):
    head = "b" * 40
    w.append_event({"kind": "item", "actor": "stream-K:k1", "item": "K1-1", "state": "review",
                    "detail": "PR #3300 @ " + head, "ts": "2026-10-12T00:00:00+00:00"})
    w.control(prs=[{"number": 3300, "headRefName": "kalayantra/k1-1", "headRefOid": head, "url": "u"}])
    old = w.run / "jobs" / "legacy-3300" / "state.json"
    old.parent.mkdir(parents=True)
    old.write_text('{"schema":"ky.legacy_job_state/1","sentinel":"old"}')
    ok(w.install())
    assert old.read_text() == '{"schema":"ky.legacy_job_state/1","sentinel":"old"}'
    old.rename(w.run / "old-adoption.json")
    old.parent.rmdir()
    ok(w.install())
    assert not old.parent.exists()
    assert w.receipt()["legacy"]["prs"]["adopted"][0]["state_path"] == str(w.run / "legacy" / "legacy-3300" / "state.json")


@pytest.mark.parametrize("role,stream,lane", [
    ("build", "K", "b1"), ("rework", "K", "b1"), ("verify", "V", "v1"),
    ("artifact", "V", "v1"), ("pre-accept", "V", "v1"), ("post-readback", "V", "v1"),
    ("ruling", "N", "b1"), ("request-prep", "N", "b1"), ("model", "S", "b1"),
    ("plan", "S", "b1"), ("surrogate", "steward", "b1")])
@pytest.mark.parametrize("engine,variant", [("claude", ""), ("claude", ".chart.tests"), ("codex", ".tests.codex")])
def test_job_qualification_supplies_conventional_environment(installer_program, monkeypatch, tmp_path, role, stream, lane, engine, variant):
    from types import SimpleNamespace
    fleet = tmp_path / "fleet"
    templates = fleet / "templates"
    templates.mkdir(parents=True)
    cfg = templates / ("LAUNCH_CONFIG." + role + variant + ".json")
    model = "gpt-6.1-sol" if engine == "codex" else "claude-opus-5-5"
    cfg.write_text(json.dumps({"role": role, "model": model, "engine": engine}))
    ctx = SimpleNamespace(fleet_live=str(fleet), run_dir=str(tmp_path / "run"), scratch=str(tmp_path / "scratch"), changed={})
    monkeypatch.setitem(installer_program, "child_env", lambda c: {"PATH": "/usr/bin:/bin"})
    monkeypatch.setitem(installer_program, "ky_dir_env", lambda c: {})
    calls = []

    def harness(argv, env, **kwargs):
        if "launch-config" in argv:
            return installer_program["Out"](0, json.dumps({"role": argv[-1], "model": "claude-opus-5-5"}), "")
        if "--config" in argv and argv[argv.index("--config") + 1] == str(cfg):
            calls.append((argv, env.copy()))
        if "qualify" in argv:
            Path(argv[argv.index("--out") + 1]).write_text(json.dumps({"result": "PASS"}))
            return installer_program["Out"](0, "", "")
        return installer_program["Out"](0 if Path(argv[argv.index("check") + 1]).exists() else 1, "", "")

    monkeypatch.setitem(installer_program, "run", harness)
    installer_program["step_qualify"](ctx)
    assert len(calls) == 3  # initial check, qualification, evidence check all get the same environment
    for argv, env in calls:
        if lane:
            assert {k: env.get(k) for k in ("KY_STREAM", "KY_LANE", "KY_CONTROLLER_ID")} == {
                "KY_STREAM": stream, "KY_LANE": lane, "KY_CONTROLLER_ID": "CTL-qualification"}
        else:
            assert not {"KY_STREAM", "KY_LANE", "KY_CONTROLLER_ID"} & env.keys()



def test_step_nine_qualifies_all_bound_templates_without_variant_overwrites(installer_program, monkeypatch, tmp_path):
    from types import SimpleNamespace
    import kymanifest
    source = Path(__file__).resolve().parent.parent
    bound, deferred = kymanifest.read_component_list(str(source.parents[3]))
    names = sorted(Path(rel).name for rel in bound if "/templates/LAUNCH_CONFIG." in rel)
    assert len(names) == 20
    fleet = tmp_path / "fleet"
    templates = fleet / "templates"
    templates.mkdir(parents=True)
    for name in names:
        (templates / name).write_bytes((source / "templates" / name).read_bytes())
    ctx = SimpleNamespace(fleet_live=str(fleet), run_dir=str(tmp_path / "run"), scratch=str(tmp_path / "scratch"), changed={})
    monkeypatch.setitem(installer_program, "child_env", lambda c: {"PATH": "/usr/bin:/bin"})
    monkeypatch.setitem(installer_program, "ky_dir_env", lambda c: {})
    qualified = []
    def harness(argv, env, **kwargs):
        if "launch-config" in argv:
            return installer_program["Out"](0, json.dumps({"role": argv[-1], "model": "claude-opus-5-5"}), "")
        if "qualify" in argv:
            cfg = Path(argv[argv.index("--config") + 1])
            doc = json.loads(cfg.read_text())
            import kyqualify
            if "env_names" in doc:
                resolved, errors = kyqualify.resolve_env(doc, dict(env, HOME="/h", USER="u"))
                assert errors == []
                assert set(resolved) == set(doc["env_names"])
            receipt = Path(argv[argv.index("--out") + 1])
            qualified.append((cfg.name, receipt.name, argv[argv.index("--evidence-dir") + 1]))
            receipt.write_text(json.dumps({"result": "PASS"}))
            return installer_program["Out"](0, "", "")
        receipt = Path(argv[argv.index("check") + 1])
        return installer_program["Out"](0 if receipt.exists() else 1, "", "")
    monkeypatch.setitem(installer_program, "run", harness)
    installer_program["step_qualify"](ctx)
    assert len(qualified) == 22 and len(ctx.qualifications) == 22
    assert len({receipt for _, receipt, _ in qualified}) == 22
    assert len({evidence for _, _, evidence in qualified}) == 22
    assert {name for name, _, _ in qualified if name.startswith("LAUNCH_CONFIG.")} == set(names)
    receipts = {r[1] for r in qualified}
    assert {"build-tests-gpt-6.1-sol.json", "build-tests-claude-opus-5-5.json",
            "verify-tests-gpt-6.1-sol.json", "verify-tests-claude-opus-5-5.json",
            "rework-tests-gpt-6.1-sol.json", "surrogate-claude-fable-5-1.json"} <= receipts
    assert not ({Path(rel).name for rel in deferred} & {name for name, _, _ in qualified})
