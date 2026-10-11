#!/usr/bin/env python3
"""Fake `launchctl` for kyboot tests — never the real one; it touches no launchd domain.

Its whole state is the directory $KY_FAKE_LAUNCHD:
  calls.jsonl                        one line per invocation: the arguments it was given
  loaded/<label>.json                a loaded agent: its plist (parsed), what was started, with which environment
  submit_action_at_bootstrap.json    the ACT-submit-* records as they were when `bootstrap` was called
  mode.json (optional, written by a test) {"bootstrap_exit": N, "start": false, "parent": N, "xpc": "<name>",
                                           "bootout_exit": N, "bootout_unloads": false}

  bootstrap gui/<uid> <plist>   refuses a label that is already loaded (exit 37); otherwise marks it loaded and —
                                like launchd with RunAtLoad — starts the plist's ProgramArguments, detached, with
                                EXACTLY the plist's EnvironmentVariables plus XPC_SERVICE_NAME=<Label> (launchd
                                sets that) plus the two tests-only names that stand in for "launchd is the
                                parent": KY_SCRATCH_ROOT_OVERRIDE (copied from this process) and KY_TEST_PPID
                                (1, or mode "parent"). It does not wait for what it started.
  print gui/<uid>/<label>       exit 0 when loaded, 113 when not
  bootout gui/<uid>/<label>     unloads and exits 0 (mode: another exit, or leave it loaded); exit 3 when not loaded
"""
import glob
import json
import os
import plistlib
import subprocess
import sys

HOME = os.environ.get("KY_FAKE_LAUNCHD")
if not HOME:
    sys.exit("fake launchctl: KY_FAKE_LAUNCHD is not set")
os.makedirs(os.path.join(HOME, "loaded"), exist_ok=True)
ARGS = sys.argv[1:]
with open(os.path.join(HOME, "calls.jsonl"), "a", encoding="utf-8") as log:
    log.write(json.dumps(ARGS) + "\n")
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
    records = [json.load(open(path, encoding="utf-8"))
               for path in sorted(glob.glob(os.path.join(os.environ.get("KY_RUN", "/nonexistent"), "actions",
                                                         "ACT-submit-*.json")))]
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
    if os.environ.get("KY_SCRATCH_ROOT_OVERRIDE") is not None:
        env["KY_SCRATCH_ROOT_OVERRIDE"] = os.environ["KY_SCRATCH_ROOT_OVERRIDE"]
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
