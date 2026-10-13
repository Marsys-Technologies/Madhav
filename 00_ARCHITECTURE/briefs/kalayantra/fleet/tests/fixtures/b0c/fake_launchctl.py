#!/usr/bin/env python3
"""Fake `launchctl` for kyboot tests — never the real one; it touches no launchd domain.

kyboot gives launchctl a fixed, minimal environment (PATH, HOME, USER, LANG), so this fake reads NOTHING from its
environment: it finds its whole state from where it was invoked. Each test links `<its root>/bin/launchctl` to
the one copy of this file, and the state is the directory `<its root>/fake-launchd/`:
  config.json (written by the test)  {"ky_run": "<KY_RUN>", "agent_env": {tests-only names the stand-in for
                                      launchd adds to an agent it starts}}
  calls.jsonl                        one line per invocation: the arguments it was given
  env.jsonl                          one line per invocation: the sorted NAMES of the environment it was given
  loaded/<label>.json                a loaded agent: its plist (parsed), what was started, with which environment
  submit_action_at_bootstrap.json    the ACT-submit-* records as they were when `bootstrap` was called
  mode.json (optional, written by a test) {"bootstrap_exit": N, "start": false, "parent": N, "xpc": "<name>",
                                           "bootout_exit": N, "bootout_unloads": false, "print_exit": N}

  bootstrap gui/<uid> <plist>   refuses a label that is already loaded (exit 37); otherwise marks it loaded and —
                                like launchd with RunAtLoad — starts the plist's ProgramArguments, detached, with
                                EXACTLY the plist's EnvironmentVariables plus XPC_SERVICE_NAME=<Label> (launchd
                                sets that) plus config.json's `agent_env` (the tests-only overrides that stand in
                                for the real roots) plus KY_TEST_PPID (1, or mode "parent"), which stands in for
                                "launchd is the parent". It does not wait for what it started.
  print gui/<uid>/<label>       exit 0 when loaded, 113 when not (mode "print_exit": that status instead, always)
  bootout gui/<uid>/<label>     unloads and exits 0 (mode: another exit, or leave it loaded); exit 3 when not loaded
"""
import glob
import json
import os
import plistlib
import subprocess
import sys

HOME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))), "fake-launchd")
try:
    with open(os.path.join(HOME, "config.json"), encoding="utf-8") as handle:
        CONFIG = json.load(handle)
except OSError:
    sys.exit("fake launchctl: no fake-launchd/config.json beside the folder it was run from (%s)" % HOME)
os.makedirs(os.path.join(HOME, "loaded"), exist_ok=True)
ARGS = sys.argv[1:]
with open(os.path.join(HOME, "calls.jsonl"), "a", encoding="utf-8") as log:
    log.write(json.dumps(ARGS) + "\n")
with open(os.path.join(HOME, "env.jsonl"), "a", encoding="utf-8") as log:
    log.write(json.dumps(sorted(os.environ)) + "\n")
try:
    with open(os.path.join(HOME, "mode.json"), encoding="utf-8") as handle:
        MODE = json.load(handle)
except OSError:
    MODE = {}
DOMAIN = "gui/%d" % os.getuid()


def marker(label):
    return os.path.join(HOME, "loaded", label + ".json")


if len(ARGS) == 3 and ARGS[0] == "bootstrap" and ARGS[1] == DOMAIN:
    with open(ARGS[2], "rb") as handle:
        plist = plistlib.load(handle)
    label = plist["Label"]
    records = []
    for path in sorted(glob.glob(os.path.join(CONFIG["ky_run"], "actions", "ACT-submit-*.json"))):
        with open(path, encoding="utf-8") as handle:
            records.append(json.load(handle))
    with open(os.path.join(HOME, "submit_action_at_bootstrap.json"), "w", encoding="utf-8") as handle:
        json.dump(records, handle)
    if MODE.get("bootstrap_exit"):
        sys.stderr.write("Bootstrap failed: %d: Input/output error\n" % MODE["bootstrap_exit"])
        sys.exit(MODE["bootstrap_exit"])
    if os.path.exists(marker(label)):
        sys.stderr.write("Bootstrap failed: 37: Operation already in progress\n")
        sys.exit(37)
    env = dict(plist.get("EnvironmentVariables", {}))
    env["XPC_SERVICE_NAME"] = MODE.get("xpc", label)
    env.update(CONFIG.get("agent_env", {}))
    env["KY_TEST_PPID"] = str(MODE.get("parent", 1))
    pid = None
    if MODE.get("start", True):
        with open(plist["StandardOutPath"], "ab") as out, open(plist["StandardErrorPath"], "ab") as err:
            pid = subprocess.Popen(plist["ProgramArguments"], env=env, stdin=subprocess.DEVNULL, stdout=out,
                                   stderr=err, start_new_session=True, cwd="/").pid
    with open(marker(label), "w", encoding="utf-8") as handle:
        json.dump({"plist_path": ARGS[2], "plist": plist, "pid": pid, "env_names": sorted(env)}, handle)
    sys.exit(0)

if len(ARGS) == 2 and ARGS[0] in ("print", "bootout") and ARGS[1].startswith(DOMAIN + "/"):
    label = ARGS[1][len(DOMAIN) + 1:]
    loaded = os.path.exists(marker(label))
    if ARGS[0] == "print":
        if "print_exit" in MODE:
            sys.stderr.write("fake launchctl: print fails as the test asked (exit %d)\n" % MODE["print_exit"])
            sys.exit(MODE["print_exit"])
        if loaded:
            print("%s = {\n\tstate = fake\n}" % ARGS[1])
            sys.exit(0)
        sys.stderr.write("Bad request.\nCould not find service \"%s\" in domain for user gui\n" % label)
        sys.exit(113)
    if not loaded:
        sys.stderr.write("Boot-out failed: 3: No such process\n")
        sys.exit(3)
    if MODE.get("bootout_unloads", True):
        os.unlink(marker(label))
    sys.exit(MODE.get("bootout_exit", 0))

sys.stderr.write("fake launchctl: unsupported invocation %r\n" % (ARGS,))
sys.exit(64)
