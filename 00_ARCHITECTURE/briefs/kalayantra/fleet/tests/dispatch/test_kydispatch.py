#!/usr/bin/env python3
"""Tests of kydispatch.py — the dispatcher engine of KĀLA-YANTRA v3 (packet KV3-B-KYDISPATCH v1; relaunch plan v2.7
§4 capacity, §6).

    python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/dispatch/test_kydispatch.py -q -p no:cacheprovider

Real modules, fake commands. The engine runs as its own process against a world built under pytest's tmp_path:

    root/            $KY_ROOT   bin/ky is a fake tracker CLI; HOLD when the case asks for it
    root/run/        $KY_RUN    loops/, EVENTS.jsonl, jobs/, locks/, … as the case seeds them
    fleet/           $KY_FLEET  fake kygate.sh, kynotify.sh, kyjob.sh, kypacket.py, kyroute.py, kyverdicts.py,
                                kyboundary.sh, kyregen.sh, local_db.sh, precheck.sh, kyalloc.py; cards; and the REAL
                                kylock.sh (a copy): the instance lock is never faked
    scratch/         $KY_SCRATCH
    repo/            $KY_SOURCE_REPO  fixture files; Git replies and registrations are fake (no Git writes)
    worktrees/       where the patched driver lets kyd_jobs and kyd_admit put item worktrees
    bin/             first on PATH: fake gh and git (never forwards to a real executable)

The five kyd_*.py modules, kyaction, kycommands and kyloop are the real ones beside kydispatch.py. Nothing here runs
the real claude, ky, gh, launchctl, docker or a database, and nothing is written under /Users/Dev/kalayantra. The
only processes signalled are job processes these tests started, identified by pid and start time.

engine.json holds the cases: a world (`setup`), `steps` and what must be true afterwards (`expect`).
    {"dry": [...]}          the real command line `kydispatch.py --dry` (through the patched driver when the case
                            says `patched`): exit 0 and exactly this job list. A `key` is compared when the case
                            gives one; otherwise it must have the form <kind>.<item>.<12 hex>.
    {"once": N}             `kydispatch.py --once`, exit N
    {"session": [...]}      one controller process: tick · {"sleep": s} · {"wait_jobs": s} · {"clock": s} ·
                            {"patch": {...}} · stop · crash; `ticks` = the job list of each tick
    {"mutate": {...}}       change the world between steps (the keys of `setup`)
"""
from __future__ import annotations

import copy
import hashlib
import http.server
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent.parent
ENGINE = FLEET / "kydispatch.py"
sys.path.insert(0, str(FLEET))

import kyaction as ka  # noqa: E402
import kycommands as kc  # noqa: E402
import kyd_kinds_ops as ops  # noqa: E402
import kyloop  # noqa: E402
import kyschema  # noqa: E402

DOC = json.loads((HERE / "engine.json").read_text(encoding="utf-8"))
CASES = DOC["cases"]
CTL = "CTL-dispatcher-20261012T000000Z-1"       # the controller a --dry reads the run directory as (loop file)
KEY_RE = re.compile(r"^[A-Z][A-Z-]*\.[A-Za-z0-9._:-]+\.[0-9a-f]{12}\Z")
PLAN_MODEL = "00_ARCHITECTURE/control/kalayantra/plan_model.json"
PACKETS = "00_ARCHITECTURE/briefs/kalayantra/packets"
OPS_TABLE = "00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json"

# ───────────────────────────────────────── the fake commands ─────────────────────────────────────────
# One program under many names. Every call is logged to <fake>/calls.jsonl. A case's `replies` rule answers first
# ({cmd, args: tokens that appear in the argv in this order, rc, out, err, sleep, once, after: only once a call
# containing that text has been made}); otherwise the name's built-in behaviour below.

FAKECMD = r'''
import json, os, sys, time, hashlib, shutil

FAKE = %(fake)r
RUN = %(run)r
SCRATCH = %(scratch)r
REPO = %(repo)r
HEAD = %(head)r


def load(name, default):
    try:
        with open(os.path.join(FAKE, name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save(name, obj):
    tmp = os.path.join(FAKE, ".%%s.%%d" %% (name, os.getpid()))
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, os.path.join(FAKE, name))


def append(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, text.encode("utf-8"))
    finally:
        os.close(fd)


def event(obj):
    obj.setdefault("ts", time.strftime("%%Y-%%m-%%dT%%H:%%M:%%SZ", time.gmtime()))
    append(os.path.join(RUN, "EVENTS.jsonl"), json.dumps(obj, ensure_ascii=False) + "\n")
    nxt = load("ky_next.json", None)
    if isinstance(nxt, dict) and isinstance(nxt.get("version"), int):     # the live tracker's version advances
        nxt["version"] += 1
        save("ky_next.json", nxt)
    return obj


def opt(argv, name, default=None):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


def in_order(tokens, argv):
    at = 0
    for token in tokens:
        try:
            at = argv.index(token, at) + 1
        except ValueError:
            return False
    return True


def out(rc, text="", err=""):
    if text:
        sys.stdout.write(text if isinstance(text, str) else json.dumps(text))
        sys.stdout.write("" if isinstance(text, str) and text.endswith(("\n", "\0")) else "\n")
    if err:
        sys.stderr.write(err + "\n")
    sys.stdout.flush()
    sys.exit(rc)


def ky(argv):
    stream, lane = os.environ.get("KY_STREAM", ""), os.environ.get("KY_LANE", "")
    actor = "stream-%%s%%s" %% (stream, ":" + lane if lane else "")
    verb = argv[0] if argv else ""
    if verb == "next":
        nxt = load("ky_next.json", None)
        return out(3, err="tracker unreachable and no snapshot on disk") if nxt is None else out(0, nxt)
    if verb == "inbox":
        rows = load("ky_inbox.json", [])
        return out(0 if rows else 1, json.dumps(rows))                    # cli.py: exit 1 and `[]` when there is none
    if verb == "claim":
        item, worker = argv[1], opt(argv, "--worker")
        n = load("claims_n.json", 0) + 1
        save("claims_n.json", n)
        claim = {"kind": "claim", "item": item, "worker_id": worker, "claim_id": "CL-%%04d" %% n,
                 "state": "acquired", "actor": actor, "lease_s": int(opt(argv, "--lease", "10800")),
                 "expires_at": time.strftime("%%Y-%%m-%%dT%%H:%%M:%%SZ", time.gmtime(time.time() + 10800)),
                 "branch": None, "head": None, "step": None}
        claim = event(claim)
        os.makedirs(os.path.join(RUN, "claims"), exist_ok=True)
        with open(os.path.join(RUN, "claims", worker + ".json"), "w", encoding="utf-8") as f:
            json.dump(claim, f)
        return out(0, claim)
    if verb in ("release", "renew"):
        path = os.path.join(RUN, "claims", lane + ".json")
        try:
            with open(path, encoding="utf-8") as f:
                claim = json.load(f)
        except (OSError, ValueError):
            return out(2, err="refused: no claim of %%s" %% lane)
        claim["state"] = "released" if verb == "release" else "renewed"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(claim, f)
        return out(0, event(claim))
    if verb == "step":
        return out(0, json.dumps(event({"kind": "item", "item": argv[1], "step": argv[2], "state": "done",
                                        "evidence": opt(argv, "--evidence"), "actor": actor})))
    if verb in ("review", "block", "done"):
        return out(0, json.dumps(event({"kind": "item", "item": argv[1], "detail": opt(argv, "--detail", ""),
                                        "state": {"review": "review", "block": "blocked", "done": "done"}[verb], "actor": actor,
                                        "evidence": "fixture typed completion" if verb == "done" else None})))
    return out(64, err="fake ky: no verb %%r" %% verb)


def job_state(job_id):
    with open(os.path.join(RUN, "jobs", job_id, "state.json"), encoding="utf-8") as f:
        return json.load(f)


def kyjob(argv):
    job = job_state(argv[0])
    plan = load("jobs.json", {})
    how = plan.get(job["item"]) or plan.get(job["kind"]) or {"do": "exit", "rc": 0}
    seq = how if isinstance(how, list) else [how]
    n = load("job_runs_%%s.json" %% job["item"].replace("/", "_"), 0)
    save("job_runs_%%s.json" %% job["item"].replace("/", "_"), n + 1)
    how = seq[min(n, len(seq) - 1)]
    session = "sess-%%s" %% job["job_id"]
    append(job["stdout_path"], json.dumps({"type": "system", "subtype": "init", "session_id": session}) + "\n")
    actor = "stream-%%s:%%s" %% (job["stream"], job["slot"])
    do = how.get("do")
    result = {"schema": "ky.job_result/1", "job_id": job["job_id"], "item": job["item"], "status": "done",
              "branch": job.get("branch"), "head_sha": None, "pr_number": None, "tests": [], "blocked_reason": None,
              "notes": "fake job"}
    if do == "sleep":
        time.sleep(how.get("s", 120))
        sys.exit(0)
    if do == "quota":
        append(job["stdout_path"], json.dumps({"type": "rate_limit_event", "rate_limit_info": {
            "status": "rejected", "rateLimitType": "five_hour"}}) + "\n")
        sys.exit(1)
    if do in ("review", "result_only"):
        if do == "review":
            event({"kind": "item", "item": job["item"], "state": "review", "actor": actor,
                   "detail": "PR #%%d @ %%s" %% (how["pr"], how["head"])})
        result.update(head_sha=how["head"], pr_number=how["pr"])
    elif do == "block":
        event({"kind": "item", "item": job["item"], "state": "blocked", "actor": actor, "detail": how.get("detail", "x")})
        result.update(status="blocked", blocked_reason=how.get("detail", "x"))
    elif do == "decide":
        append(os.path.join(RUN, "DECISIONS_SURROGATE.jsonl"), json.dumps({
            "id": how.get("id", "SD-20261012T000000Z-1"), "awaiting": job["item"], "session": session,
            "class": how.get("class", "routine"), "state": how.get("state", "PROPOSED"),
            "decision": how.get("decision", "reconciled"), "rationale": "fixture proposal", "evidence": [],
            "target": {}, "authority": {"source_commit": "a" * 40, "entrypoints_digest": "b" * 64},
            "notification": {"submitted": False, "ts": None}, "veto_deadline": None, "effective_at": None,
            "by": "kalayantra-owner-surrogate"}) + "\n")
    if how.get("result", True):
        with open(os.path.join(job["job_scratch"], "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f)
    sys.exit(how.get("rc", 0))


def packet_front(path):
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")
        return json.loads("\n".join(lines[1:lines.index("```", 1)]))
    except (OSError, ValueError):
        return {}


def builtin(name, argv):
    if name == "git":
        args = argv[2:] if argv[:1] == ["-C"] else argv
        entries = load("git_worktrees.json", [{"path": REPO, "head": HEAD, "branch": "refs/heads/main"}])
        if args[:2] == ["worktree", "list"]:
            return out(0, "\n\n".join("worktree %%s\nHEAD %%s\nbranch %%s" %%
                                      (e["path"], e["head"], e["branch"]) for e in entries) + "\n")
        if args[:2] == ["worktree", "add"]:
            branch, path, head = (args[3], args[4], args[5]) if args[2] == "-b" else (args[3], args[2], HEAD)
            shutil.copytree(REPO, path)
            entries.append({"path": path, "head": head, "branch": "refs/heads/" + branch})
            save("git_worktrees.json", entries)
            return out(0)
        if args[:2] == ["worktree", "remove"]:
            shutil.rmtree(args[2])
            save("git_worktrees.json", [e for e in entries if e["path"] != args[2]])
            return out(0)
        if args[:1] == ["rev-parse"]:
            if args[-1].startswith("refs/heads/"):
                return out(0 if any(e["branch"] == args[-1] for e in entries) else 1)
            return out(0, HEAD)
        if args[:1] == ["merge-base"]:
            return out(0, HEAD)
        if args[:1] == ["merge-tree"]:
            return out(0, HEAD)
        if args[:1] == ["show"]:
            path = os.path.join(REPO, args[1].split(":", 1)[-1])
            if not os.path.isfile(path):
                return out(1, err="fixture has no blob")
            with open(path, encoding="utf-8") as f:
                return out(0, f.read())
        if args[:1] in (["fetch"], ["merge"], ["status"]) or args[:2] == ["worktree", "prune"]:
            return out(0)
        return out(97, err="fake git: no reply for %%r" %% args)
    if name == "ky":
        return ky(argv)
    if name == "kyjob.sh":
        return kyjob(argv)
    if name == "gh":
        return out(0, "[]") if argv[:2] == ["pr", "list"] else out(1, err="fake gh: no reply for %%s" %% " ".join(argv))
    if name == "kygate.sh":
        return out(0, "OPEN") if os.path.exists(os.path.join(FAKE, "gate_open")) else out(75, "WAIT\nreason=fixture: wait")
    if name == "kynotify.sh":
        append(os.path.join(FAKE, "notify.log"), json.dumps(argv, ensure_ascii=False) + "\n")
        return out(0, "notify=dry")
    if name == "kypacket.py":
        return out(0, {"schema": "ky.packet_check/1", "admitted": True, "reasons": []})
    if name == "kyroute.py":
        if argv[:1] == ["packet"]:
            return out(0, {"decision": "ROUTE", "tier": packet_front(opt(argv, "--packet")).get("build_tier") or "opus"})
        if argv[:1] == ["escalate"]:
            return out(0, {"decision": "CONTINUE"})
        return out(0, {"decision": "SAME_TIER"})
    if name == "local_db.sh":
        if argv[:1] == ["db"]:
            slot, session = argv[1], opt(argv, "--session")
            mount = os.path.join(SCRATCH, "local_db", slot)
            os.makedirs(mount, exist_ok=True)
            os.makedirs(os.path.join(RUN, "local_db"), exist_ok=True)
            with open(os.path.join(RUN, "local_db", slot + ".json"), "w", encoding="utf-8") as f:
                json.dump({"schema": "ky.slot_db/1", "slot": slot, "session_id": session, "result": "READY",
                           "mount_source": mount, "seed": {k: "0" * 64 for k in
                                                           ("schema_sha256", "ledger_sha256", "registry_sha256")}}, f)
        return out(0)
    if name == "kyverdicts.py":
        if argv[:1] == ["snapshot"]:
            with open(opt(argv, "--out"), "w", encoding="utf-8") as f:
                f.write("{}")
            return out(0)
        if argv[:1] == ["inherit"]:
            return out(1)
        if argv[:1] == ["publish"]:
            event({"kind": "verdict", "item": opt(argv, "--item"), "phase": opt(argv, "--phase"), "head": opt(argv, "--head"),
                   "artifact_digest": opt(argv, "--artifact-digest"), "result": "ACCEPTED",
                   "actor": "stream-V:%%s" %% opt(argv, "--vslot"), "detail": "fixture measured review"})
            return out(0, {"published": True})
        if argv[:1] == ["invalidate"]:
            event({"kind": "verdict", "item": opt(argv, "--item"), "phase": opt(argv, "--phase"), "head": opt(argv, "--head"),
                   "artifact_digest": None, "result": "REJECTED", "detail": "invalidated: " + str(opt(argv, "--reason")),
                   "actor": "stream-V:%%s" %% opt(argv, "--vslot")})
            return out(0)
    if name in ("kyboundary.sh", "kyregen.sh"):
        return out(0)
    if name == "precheck.sh":
        return out(1, "EXPECTED-RED")
    if name == "kyalloc.py":
        return out(0, {"numbers": [901]})
    return out(97, err="fake %%s: no reply" %% name)


def main(name, argv):
    append(os.path.join(FAKE, "calls.jsonl"), json.dumps({
        "cmd": name, "argv": argv, "cwd": os.getcwd(),
        "env": {k: os.environ[k] for k in ("KY_STREAM", "KY_LANE", "KY_RUN_ID", "KY_ROLE", "KY_SOURCE_REPO") if k in os.environ},
        "credentials": sorted(k for k in os.environ if k in ("DATABASE_URL", "PGPASSWORD", "ANTHROPIC_API_KEY")
                              or k.endswith("_DATABASE_URL"))}, ensure_ascii=False) + "\n")
    rules = load("replies.json", [])
    used = load("used.json", [])
    try:
        with open(os.path.join(FAKE, "calls.jsonl"), encoding="utf-8") as f:
            earlier = ["%%s %%s" %% (c["cmd"], " ".join(c["argv"])) for c in map(json.loads, f.read().splitlines()[:-1])]
    except (OSError, ValueError):
        earlier = []
    for n, rule in enumerate(rules):
        if rule.get("cmd") != name or n in used or not in_order(rule.get("args", []), argv):
            continue
        if rule.get("after") and not any(rule["after"] in line for line in earlier):
            continue
        if rule.get("once"):
            save("used.json", used + [n])
        if rule.get("sleep"):
            time.sleep(rule["sleep"])
        for path, content in rule.get("write_files", {}).items():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        if rule.get("builtin"):
            return builtin(name, argv)
        return out(rule.get("rc", 0), rule.get("out", ""), rule.get("err", ""))
    return builtin(name, argv)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
'''

# The patched driver: the engine with the two work-worktree roots moved under tmp_path (kyd_jobs and kyd_admit hard-
# code the policy root). One argument: {"argv": [...]} runs the real main(); {"session": [...]} drives one controller.
DRIVER = r'''
import json, os, sys, time
sys.path.insert(0, %(fleet)r)
import kyd_admit, kyd_jobs, kyloop
import kydispatch

kyd_jobs.WORKTREES = kyd_admit.WORKTREE_ROOT = %(worktrees)r
kyd_admit.GIT = %(git)r
plan = json.loads(sys.argv[1])
if "argv" in plan:
    sys.exit(kydispatch.main(plan["argv"]))
engine = kydispatch.Engine(dict(os.environ))
rc = engine.acquire()
if rc != 0:
    sys.exit(rc)
ticks, shift = [], [0.0]
engine.clock = lambda: time.time() + shift[0]
for step in plan["session"]:
    if step == "tick":
        ticks.append(engine.tick()["jobs"])
    elif step == "stop":
        engine.stop()
    elif step == "crash":
        sys.stdout.write(json.dumps({"ticks": ticks}) + "\n")
        sys.stdout.flush()
        os._exit(0)
    elif "sleep" in step:
        time.sleep(step["sleep"])
    elif "clock" in step:
        shift[0] += step["clock"]
    elif "patch" in step:
        for name, value in step["patch"].items():
            setattr(kyd_jobs, name, value)
    elif "wait_jobs" in step:
        end = time.monotonic() + step["wait_jobs"]
        while time.monotonic() < end:
            live = [j for j in kyd_jobs.load(engine.ctx) if j["phase"] == "live"]
            if all(kyd_jobs._process(j) == "gone" for j in live):
                break
            time.sleep(0.05)
sys.stdout.write(json.dumps({"ticks": ticks}) + "\n")
'''


# ───────────────────────────────────────── the tracker's /api/verify, as a loopback fixture ─────────────────────────────────────────

class _Verify(http.server.BaseHTTPRequestHandler):
    table = {}

    def do_GET(self):                                   # noqa: N802
        from urllib.parse import parse_qs, urlparse
        url = urlparse(self.path)
        q = parse_qs(url.query)
        item, step = (q.get("id") or [""])[0], (q.get("step") or [""])[0]
        how = self.table.get("%s/%s" % (item, step))
        if url.path != "/api/verify" or how is None:
            body, code = {"error": "unknown item or no detector"}, 404
        else:
            # server.py:368-376 ignores step and verifies the ITEM. Never invent a step-specific success.
            body, code = {"item": item, "detector": {"status": "done" if how == "no_echo" else how,
                "detail": "fixture detector", "checked_at": "2026-10-12T10:00:00+00:00",
                "source": "fixture", "progress": None}}, 200
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def tracker():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Verify)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield "http://127.0.0.1:%d" % server.server_address[1]
    server.shutdown()


@pytest.fixture(scope="session")
def template(tmp_path_factory):
    """Fixture files only: no repository, branch, worktree, commit or push is created by the tests."""
    base = tmp_path_factory.mktemp("template")
    repo = base / "repo"
    repo.mkdir()
    table = json.loads((HERE / "kinds_ops.json").read_text(encoding="utf-8"))["table"]    # one production kind enabled
    (repo / OPS_TABLE).parent.mkdir(parents=True)
    (repo / OPS_TABLE).write_text(json.dumps({"ops": table}), encoding="utf-8")
    (repo / "README").write_text("throwaway\n", encoding="utf-8")
    return base


# ───────────────────────────────────────── the world ─────────────────────────────────────────

def gh_pr(pr):
    """A case's PR as `gh pr view --json …` prints it (checks: name → conclusion, or {status, url})."""
    rollup = []
    for name, check in (pr.get("checks") or {}).items():
        check = check if isinstance(check, dict) else {"status": check}
        done = check["status"] not in ("IN_PROGRESS", "QUEUED", "PENDING")
        rollup.append({"__typename": "CheckRun", "name": name, "status": "COMPLETED" if done else check["status"],
                       "conclusion": check["status"] if done else "", "detailsUrl": check.get("url", "")})
    return {"number": pr["number"], "headRefOid": pr["head"], "baseRefName": pr.get("base", "main"),
            "title": pr.get("title", "a title"), "state": pr.get("state", "OPEN"),
            "mergeable": pr.get("mergeable", "MERGEABLE"), "mergeStateStatus": pr.get("merge_state", "CLEAN"),
            "statusCheckRollup": rollup, "mergeCommit": {"oid": pr["merge_commit"]} if pr.get("merge_commit") else None,
            "files": [{"path": p} for p in pr.get("files", [])],
            "autoMergeRequest": {"mergeMethod": "SQUASH"} if pr.get("auto_merge") else None}


class World:
    def __init__(self, tmp, template, tracker_url):
        self.tmp = Path(os.path.realpath(tmp))
        self.root, self.fleet, self.scratch = self.tmp / "root", self.tmp / "fleet", self.tmp / "scratch"
        self.run, self.repo, self.fake = self.root / "run", self.tmp / "repo", self.tmp / "fake"
        self.bin, self.worktrees = self.tmp / "bin", self.tmp / "worktrees"
        self.tracker_url = tracker_url
        for d in (self.root / "bin", self.run / "loops", self.fleet / "cards", self.scratch, self.fake, self.bin,
                  self.worktrees):
            d.mkdir(parents=True)
        shutil.copytree(template / "repo", self.repo, symlinks=True)
        self.head = "1" * 40                                               # synthetic Git reply, never a measured head
        (self.fake / "fakecmd.py").write_text(FAKECMD % {"fake": str(self.fake), "run": str(self.run),
                                                         "scratch": str(self.scratch), "repo": str(self.repo),
                                                         "head": self.head}, encoding="utf-8")
        (self.tmp / "driver.py").write_text(DRIVER % {"fleet": str(FLEET), "worktrees": str(self.worktrees),
                                                     "git": str(self.bin / "git")},
                                            encoding="utf-8")
        for name in ("kygate.sh", "kynotify.sh", "kyjob.sh", "local_db.sh", "kyboundary.sh", "kyregen.sh", "precheck.sh"):
            self._stub(self.fleet / name, name, shell=True)
        for name in ("kypacket.py", "kyroute.py", "kyverdicts.py", "kyalloc.py"):
            self._stub(self.fleet / name, name, shell=False)
        self._stub(self.root / "bin" / "ky", "ky", shell=True)
        self._stub(self.bin / "gh", "gh", shell=True)
        self._stub(self.bin / "git", "git", shell=True)
        os.symlink(sys.executable, self.bin / "python3")
        shutil.copy(FLEET / "kylock.sh", self.fleet / "kylock.sh")           # the real instance lock
        shutil.copy(FLEET / "mcp.none.json", self.fleet / "mcp.none.json")
        (self.fleet / "templates").mkdir()
        shutil.copy(FLEET / "templates/LAUNCH_CONFIG.surrogate.json",
                    self.fleet / "templates/LAUNCH_CONFIG.surrogate.json")
        for card in ("KARAKA.md", "PARIKSAKA.md", "ADHIKARIN.md", "OWNER_SURROGATE.md"):
            (self.fleet / "cards" / card).write_text("card %s\n" % card, encoding="utf-8")
        (self.run / "EVENTS.jsonl").write_text("", encoding="utf-8")
        self.started = []                                                  # background controllers of this test

    def _stub(self, path, name, shell):
        fake = str(self.fake / "fakecmd.py")
        if shell:
            path.write_text("#!/bin/bash\nexec %s -B %s %s \"$@\"\n" % (sys.executable, fake, name), encoding="utf-8")
        else:
            path.write_text("import sys, runpy\nsys.argv = [%r, %r] + sys.argv[1:]\nrunpy.run_path(%r, run_name='__main__')\n"
                            % (fake, name, fake), encoding="utf-8")
        path.chmod(0o755)

    # ── placeholders ──
    def sub(self, value):
        if isinstance(value, str):
            for name, text in (("$RUN", self.run), ("$ROOT", self.root), ("$REPO", self.repo), ("$FLEET", self.fleet),
                               ("$SCRATCH", self.scratch), ("$WT", self.worktrees), ("$CTL", CTL), ("$HEAD", self.head)):
                value = value.replace(name, str(text))
            value = re.sub(r"\$H([0-9a-f])", lambda m: m.group(1) * 40, value)
            return re.sub(r"\$D([0-9a-f])", lambda m: m.group(1) * 64, value)
        if isinstance(value, list):
            return [self.sub(v) for v in value]
        if isinstance(value, dict):
            return {self.sub(k): self.sub(v) for k, v in value.items()}
        return value

    def write(self, path, content):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, (dict, list)) or content is None or isinstance(content, (int, bool)):
            content = json.dumps(content, ensure_ascii=False, indent=1) + "\n"
        path.write_text(content, encoding="utf-8")

    def packet(self, item, front):
        front = dict({"id": item, "kind": "fix", "build_tier": "sonnet", "max_loops": 3, "needs_chart_data": False}, **front)
        self.write(self.repo / PACKETS / ("PACKET_%s_v1.md" % item), "```json\n%s\n```\n# %s\n" % (json.dumps(front), item))

    def qualification(self, role, model, seconds=3600):
        self.write(self.run / "QUALIFICATIONS" / ("%s-%s.json" % (role, model)), {
            "schema": "ky.qualification/1", "role": role, "model": model, "result": "PASS", "context": "launchd",
            "binds": {"model": model, "effort": "high", "permission_mode": "bypassPermissions",
                      "claude_bin": "/nonexistent/claude", "max_turns": 30, "deadline_seconds": seconds,
                      "extra_flags": [], "disallowed_tools": [],
                      "mcp_config_sha256": ka.sha_file(self.fleet / "mcp.none.json")}})

    def slot(self, slot, session=CTL):
        mount = self.scratch / "local_db" / slot
        mount.mkdir(parents=True, exist_ok=True)
        self.write(self.run / "local_db" / (slot + ".json"), {
            "schema": "ky.slot_db/1", "slot": slot, "session_id": session, "result": "READY", "mount_source": str(mount),
            "seed": {k: "0" * 64 for k in ("schema_sha256", "ledger_sha256", "registry_sha256")}})

    def loop(self, **fields):
        doc, _ = kyloop.loop_state(self.run, "dispatcher")
        doc = dict(doc or {}, **fields)
        self.write(self.run / "loops" / "dispatcher.json", doc)

    # ── a case's setup, and its mutations ──
    def apply(self, setup, first=False):
        setup = self.sub(copy.deepcopy(setup))
        if first:
            self.loop(enabled=True, controller={"id": CTL, "pid": 1})
            for role in ("build", "rework", "verify", "artifact", "pre-accept", "post-readback", "ruling", "surrogate",
                         "plan", "model", "request-prep"):
                for model in (("claude-fable-5-1",) if role == "surrogate" else
                              ("claude-sonnet-5-5", "claude-opus-5-5")):
                    self.qualification(role, model, setup.get("deadline_seconds", 3600))
            for item, front in DOC["defaults"]["packets"].items():
                self.packet(item, front)
            self.write(self.repo / PLAN_MODEL, {"items": self.sub(copy.deepcopy(DOC["defaults"]["model"])) + setup.get("model", [])})
            self.write(self.fake / "replies.json", [])
            self.write(self.fake / "jobs.json", {})
        elif "model" in setup:
            self.write(self.repo / PLAN_MODEL, {"items": self.sub(copy.deepcopy(DOC["defaults"]["model"])) + setup["model"]})
        if "next" in setup:
            nxt = setup["next"]
            if nxt is None:
                (self.fake / "ky_next.json").unlink(missing_ok=True)
            else:
                nxt = dict({"running": [], "ready": [], "blocked": []}, **nxt)
                if not nxt.pop("snapshot", False):
                    nxt = dict({"stream": "", "version": 5}, **nxt)
                self.write(self.fake / "ky_next.json", nxt)
        if "prs" in setup:                                                 # `gh pr view <n>` answers, in gh's own shape
            setup["replies"] = [{"cmd": "gh", "args": ["pr", "view", str(pr["number"])], "out": gh_pr(pr),
                                 **({"after": pr["after"]} if pr.get("after") else {})}
                                for pr in setup["prs"]] + setup.get("replies", [])
        for key, name in (("replies", "replies.json"), ("jobs", "jobs.json"), ("inbox", "ky_inbox.json")):
            if key in setup:
                self.write(self.fake / name, setup[key])
        if "gate" in setup:
            (self.fake / "gate_open").unlink(missing_ok=True)
            if setup["gate"] == "OPEN":
                self.write(self.fake / "gate_open", "")
        for key, path in (("hold", self.root / "HOLD"), ("hold_merges", self.run / "HOLD_MERGES"),
                          ("stop", self.run / "STOP_dispatcher")):
            if key in setup:
                path.unlink(missing_ok=True)
                if setup[key]:
                    self.write(path, "fixture\n")
        if "enabled" in setup:
            self.loop(enabled=setup["enabled"])
        if "loop" in setup:
            self.loop(**setup["loop"])
        for slot in setup.get("slots", []):
            self.slot(slot)
        for event in setup.get("events", []):
            with open(self.run / "EVENTS.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(dict({"ts": "2026-10-12T10:00:00Z"}, **event), ensure_ascii=False) + "\n")
        if "events_raw" in setup:
            with open(self.run / "EVENTS.jsonl", "a", encoding="utf-8") as f:
                f.write(setup["events_raw"])
        for item, front in setup.get("packets", {}).items():
            self.packet(item, front)
        for path, content in setup.get("files", {}).items():
            if content is None:
                Path(path).unlink(missing_ok=True)
            else:
                self.write(path, content)
        for record in setup.get("prepared", []):                           # ky.op_prepared/1, digest by the real module
            request = record["request"]
            self.write(self.run / "ops" / "prepared" / (request["operation_id"] + ".json"), {
                "schema": "ky.op_prepared/1", "operation_id": request["operation_id"], "item": request["item_id"],
                "step": 1, "request": request, "request_sha256": ops.request_digest(request),
                "prepared_by": CTL, "prepared_by_slot": record.get("slot")})
            if record.get("receipt"):
                output = self.run / "ops" / "receipts" / (request["operation_id"] + ".output.txt")
                self.write(output, "rows=12\n")
                self.write(self.run / "ops" / "done" / (request["operation_id"] + ".json"), request)
                self.write(self.run / "ops" / "receipts" / (request["operation_id"] + ".json"), {
                    "operation_id": request["operation_id"], "kind": request["kind"], "item_id": request["item_id"],
                    "status": record["receipt"], "exit_code": 0, "request_sha256": ops.request_digest(request),
                    "requested_by": request["requested_by"], "output_file": str(output),
                    "output_sha256": ka.sha_file(output), "output_bytes": 8})
        for doc in setup.get("awaiting", []):
            self.write(self.run / "awaiting" / (doc["id"] + ".json"), dict({
                "schema": "ky.awaiting/1", "created_at": "2026-10-12T10:00:00Z",
                "raised_by": {"role": "conductor", "session_id": "S-1", "job_id": None}, "item": None,
                "options": [{"id": "reconciled", "text": "done"}], "recommendation": None, "evidence": [],
                "deadline": None, "class_hint": "unknown", "blocks": "none"}, **doc))
        for command in setup.get("commands", []):
            kc.submit(self.run, command.get("role", "dispatcher"), command["command"], command.get("args", {}),
                      {"kind": "cockpit", "session_id": "owner-cockpit"})
        if setup.get("pause_applied"):                                     # an owner pause in force: APPLIED, no later resume
            cid = kc.submit(self.run, "campaign", "pause", {}, {"kind": "cockpit", "session_id": "owner-cockpit"})
            entry = kc.find(self.run, cid)
            self.write(entry["path"], dict(entry["doc"], state="APPLIED", applied_at=ka.utc(), result={},
                                           applied_by={"holder_kind": "controller", "controller_id": "CTL-campaign-1",
                                                       "role": "campaign"}))
            assert kc.owner_paused(self.run) is True
        if "worktrees" in setup:                                           # fake registrations, no real Git command
            self.write(self.fake / "git_worktrees.json", [{"path": str(self.repo), "head": self.head,
                                                            "branch": "refs/heads/main"}] + [
                {"path": str(self.worktrees / ("kalayantra-old-%d" % n)), "head": self.head,
                 "branch": "refs/heads/kalayantra/old-%d" % n} for n in range(setup["worktrees"])])
        for name in setup.get("plain_dirs", []):
            Path(name).mkdir(parents=True, exist_ok=True)
        _Verify.table = setup.get("verify", _Verify.table if not first else {})

    # ── running the engine ──
    def env(self, extra=None):
        env = {"HOME": str(self.tmp / "home"), "USER": os.environ.get("USER", "t"), "LANG": "en_US.UTF-8", "TERM": "dumb",
               "PATH": "%s:/usr/bin:/bin:/usr/sbin:/sbin" % self.bin, "TMPDIR": os.environ.get("TMPDIR", str(self.tmp)),
               "KY_ROOT": str(self.root), "KY_RUN": str(self.run), "KY_FLEET": str(self.fleet),
               "KY_SCRATCH": str(self.scratch), "KY_SOURCE_REPO": str(self.repo), "KY_TRACKER_URL": self.tracker_url,
               "GIT_OPTIONAL_LOCKS": "0",
               "PYTHONPYCACHEPREFIX": str(self.tmp.parent / "pycache")}        # bytecode beside the worlds, never in the repo
        (self.tmp / "home").mkdir(exist_ok=True)
        env.update(extra or {})
        return env

    def _run(self, cmd, extra=None, timeout=900):
        """Run one engine process. Its output goes to files, not pipes: a job the engine starts inherits the
        engine's stdout and stderr (the real kyjob.sh redirects its own), and a pipe would stay open with it."""
        self.runs = getattr(self, "runs", 0) + 1
        paths = [self.tmp / ("engine.%d.%s" % (self.runs, name)) for name in ("out", "err")]
        with open(paths[0], "w") as out, open(paths[1], "w") as err:
            done = subprocess.run(cmd, env=self.env(extra), stdout=out, stderr=err, timeout=timeout, cwd=str(self.tmp),
                                  stdin=subprocess.DEVNULL)
        done.stdout, done.stderr = (p.read_text(encoding="utf-8") for p in paths)
        return done

    def cli(self, argv, patched=False, extra=None):
        return self._run([sys.executable, "-B", str(self.tmp / "driver.py"), json.dumps({"argv": argv})], extra)

    def session(self, steps):
        return self._run([sys.executable, str(self.tmp / "driver.py"), json.dumps({"session": steps})])

    def background(self, steps):
        proc = subprocess.Popen([sys.executable, str(self.tmp / "driver.py"), json.dumps({"session": steps})],
                                env=self.env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                cwd=str(self.tmp), stdin=subprocess.DEVNULL)
        self.started.append(proc)
        return proc

    # ── what happened ──
    def calls(self):
        try:
            lines = (self.fake / "calls.jsonl").read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        return [json.loads(line) for line in lines]

    def call_lines(self):
        return ["%s %s" % (c["cmd"], " ".join(c["argv"])) for c in self.calls()]

    def jobs(self):
        out = []
        directory = self.run / "jobs"
        for name in sorted(os.listdir(directory)) if directory.is_dir() else []:
            try:
                out.append(json.loads((directory / name / "state.json").read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass                                                       # a case's unreadable state, or no state
        return out

    def journal(self):
        try:
            return (self.run / "JOURNAL_DISPATCHER.md").read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def cleanup(self):
        """End what this test started: its background controllers, and job processes recorded in ITS run directory
        whose pid still has the recorded start identity (a pid alone is never signalled)."""
        for proc in self.started:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
        for job in self.jobs():
            if not isinstance(job, dict):
                continue  # a quarantined fixture has no process identity this test may signal
            pid, start = job.get("pid"), job.get("process_start")
            if isinstance(pid, int) and pid > 1 and job.get("pgid") == pid and ka.process_matches(pid, start) is True:
                try:
                    os.killpg(pid, signal.SIGKILL)
                except OSError:
                    pass


@pytest.fixture
def world(tmp_path, template, tracker):
    w = World(tmp_path, template, tracker)
    yield w
    w.cleanup()


# ───────────────────────────────────────── the cases of engine.json ─────────────────────────────────────────

def _same_jobs(got, want, label):
    assert [(j["kind"], j["item"], j["pool"], j["decision"]) for j in got] == \
        [(j["kind"], j["item"], j.get("pool"), j["decision"]) for j in want], "%s: %s" % (label, json.dumps(got))
    for have, expected in zip(got, want):
        assert set(have) == {"kind", "item", "key", "pool", "decision"}, label
        assert KEY_RE.match(have["key"]) and have["key"].startswith("%s.%s." % (have["kind"], have["item"])), have["key"]
        if "key" in expected:
            assert have["key"] == expected["key"], label


def _subset(have, want):
    """Every key of `want` is in `have` with that value; an object value is compared the same way."""
    if not isinstance(have, dict):
        return False
    return all(_subset(have.get(k), v) if isinstance(v, dict) and v else have.get(k) == v for k, v in want.items())


def _expect(world, expect, label):
    expect = world.sub(copy.deepcopy(expect))
    lines = world.call_lines()
    at = 0
    for wanted in expect.get("calls", []):                                 # in this order
        found = next((n for n in range(at, len(lines)) if wanted in lines[n]), None)
        assert found is not None, "%s: no call %r after position %d in\n%s" % (label, wanted, at, "\n".join(lines))
        at = found + 1
    for unwanted in expect.get("no_calls", []):
        assert not [x for x in lines if unwanted in x], "%s: a call %r was made" % (label, unwanted)
    for text, count in expect.get("call_counts", {}).items():
        assert len([x for x in lines if text in x]) == count, "%s: %r not called %d times\n%s" % (label, text, count, "\n".join(lines))
    if "jobs" in expect:
        jobs = world.jobs()
        assert len(jobs) == len(expect["jobs"]), "%s: job states %s" % (label, [(j["kind"], j["item"], j["phase"], j["outcome"]) for j in jobs])
        for have, want in zip(jobs, expect["jobs"]):
            assert _subset(have, want), "%s: job %s is %s, wanted %s" % (
                label, have["job_id"], {k: have.get(k) for k in want}, want)
            assert have["schema"] == "ky.job/1"
    journal = world.journal()
    for text in expect.get("journal", []):
        assert text in journal, "%s: journal lacks %r:\n%s" % (label, text, journal)
    for text in expect.get("no_journal", []):
        assert text not in journal, "%s: journal has %r:\n%s" % (label, text, journal)
    notify = (world.fake / "notify.log").read_text(encoding="utf-8") if (world.fake / "notify.log").exists() else ""
    for text in expect.get("notify", []):
        assert text in notify, "%s: no notification %r in\n%s" % (label, text, notify)
    for text, count in expect.get("notify_counts", {}).items():
        assert notify.count(text) == count, "%s: %r notified %d times, wanted %d" % (label, text, notify.count(text), count)
    for path, want in expect.get("files", {}).items():
        if isinstance(want, bool):
            assert os.path.lexists(path) is want, "%s: %s %s" % (label, path, "is missing" if want else "exists")
        elif isinstance(want, str):
            assert Path(path).read_text(encoding="utf-8").strip() == want, "%s: %s" % (label, path)
        else:
            have = json.loads(Path(path).read_text(encoding="utf-8"))
            assert _subset(have, want), "%s: %s is %s" % (label, path, have)
    for slug, count in expect.get("awaiting", {}).items():
        found = sorted((world.run / "awaiting").glob("AW-*-%s.json" % slug)) if (world.run / "awaiting").is_dir() else []
        assert len(found) == count, "%s: %d awaiting item(s) %s, wanted %d" % (label, len(found), slug, count)
        schema = kyschema.load_json(FLEET / "schemas" / "awaiting.json")
        for path in found:
            assert not kyschema.validate(schema, json.loads(path.read_text(encoding="utf-8"))), path
    if "loop" in expect:
        doc, err = kyloop.loop_state(world.run, "dispatcher")
        assert err is None and _subset(doc, expect["loop"]), "%s: loop file %s" % (label, doc)
    if "command_states" in expect:
        assert [e["doc"]["state"] for e in kc.scan(world.run)[0]] == expect["command_states"], \
            "%s: %s" % (label, [(e["doc"]["command"], e["doc"]["state"], e["doc"].get("result")) for e in kc.scan(world.run)[0]])
    if expect.get("adopted"):
        doc, _ = kyloop.loop_state(world.run, "dispatcher")
        live = [j for j in world.jobs() if j["phase"] == "live"]
        assert live and all(j["controller_id"] == doc["controller"]["id"] != CTL for j in live), label
    if "lock" in expect:
        assert os.path.lexists(world.run / "locks" / "dispatcher") is expect["lock"], "%s: instance lock" % label
    for call in world.calls():
        assert call["credentials"] == [], "a credential variable reached %s" % call["cmd"]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_case(case, world):
    world.apply(case.get("setup", {}), first=True)
    patched = bool(case.get("patched"))
    for n, step in enumerate(case["steps"]):
        label = "%s step %d" % (case["name"], n + 1)
        if "mutate" in step:
            world.apply(step["mutate"])
        elif "dry" in step:
            events = (world.run / "EVENTS.jsonl").read_bytes()
            before = sorted(str(p) for p in world.run.rglob("*"))
            done = world.cli(["--dry"], patched=patched)
            assert done.returncode == step.get("exit", 0), "%s: exit %d\n%s" % (label, done.returncode, done.stderr)
            plan = json.loads(done.stdout)
            assert set(plan) == {"schema", "jobs"} and plan["schema"] == "ky.dispatch_plan/1", label
            _same_jobs(plan["jobs"], world.sub(copy.deepcopy(step["dry"])), label)
            assert sorted(str(p) for p in world.run.rglob("*")) == before, "%s: --dry wrote under $KY_RUN" % label
            assert (world.run / "EVENTS.jsonl").read_bytes() == events, label
        elif "once" in step:
            done = world.cli(["--once"], patched=True)
            assert done.returncode == step["once"], "%s: exit %d\n%s" % (label, done.returncode, done.stderr)
        elif "session" in step:
            done = world.session(world.sub(copy.deepcopy(step["session"])))
            assert done.returncode == step.get("exit", 0), "%s: exit %d\n%s\n%s" % (label, done.returncode, done.stdout, done.stderr)
            if "ticks" in step:
                ticks = json.loads(done.stdout.strip().splitlines()[-1])["ticks"]
                want = world.sub(copy.deepcopy(step["ticks"]))
                assert len(ticks) == len(want), "%s: %d ticks: %s" % (label, len(ticks), json.dumps(ticks))
                for t, (got, expected) in enumerate(zip(ticks, want)):
                    _same_jobs(got, expected, "%s tick %d" % (label, t + 1))
        if "expect" in step:
            _expect(world, step["expect"], label)
    _expect(world, case.get("expect", {}), case["name"])


def test_every_listed_item_has_a_case():
    """The packet's acceptance: at least one case per item of the plan's "Tests (B-1)" list, per negative case and
    for a refusal after J.open; and a case per kind."""
    covered = {tag for case in CASES for tag in case["covers"]}
    for tag, test in DOC["covered_elsewhere"].items():                     # by a test of this file, named there
        assert callable(globals().get(test)), test
        covered.add(tag)
    kinds = {"BUILD", "REWORK", "STEP", "VERIFY", "ARTIFACT", "REGEN", "MERGE", "COMPLETE", "REQUEST-PREP", "PRE-ACCEPT",
             "EXECUTE", "POST-READBACK", "MODEL", "RULING", "SURROGATE", "PLAN"}
    transitions = {"done", "blocked", "failed", "interrupted", "timed_out", "refused"}
    listed = {"recovery", "timeout reaping", "hold precedence", "gate WAIT with bootstrap exemption", "ceiling refusal",
              "stale-snapshot refusal", "duplicate instance refusal", "head-match guard", "inheritance predicate",
              "failure fingerprint persistence"}
    negative = {"STOP_dispatcher", "global HOLD", "HOLD_MERGES", "gate WAIT", "snapshot fallback", "second instance",
                "refusal after J.open"}
    missing = (kinds | transitions | listed | negative) - covered
    assert not missing, "no case covers: %s" % ", ".join(sorted(missing))
    assert len({c["name"] for c in CASES}) == len(CASES)


# ───────────────────────────────────────── what a case file cannot say ─────────────────────────────────────────

BUILD_READY = {"next": {"ready": [{"id": "K-1", "owner": "K", "status": "ready", "completion_kind": "code",
                                   "deps_open": [], "deps_open_strict": []}]},
               "files": {"$RUN/PRIORITY.txt": "K-1\n"}, "gate": "OPEN", "slots": ["b1"]}


@pytest.mark.parametrize("name,state", [
    ("legacy-3337", '{"schema":"ky.legacy_job_state/1"}'),
    ("J-20261013T000000Z-b1", '{"schema":"ky.bootstrap_job_state/3","slot":"b1","item":"K-1"}'),
    ("J-20261013T000000Z-b1", '{"launcher":"cockpit-direct","phase":"starting","slot":"b1","item":"K-1"}'),
])
def test_quarantined_folder_keeps_unrelated_build_intent(world, name, state):
    import kydispatch as d
    world.apply(dict(BUILD_READY, slots=[]), first=True)
    broken = world.run / "jobs" / name / "state.json"
    broken.parent.mkdir(parents=True)
    if state is not None:
        broken.write_text(state)
    e = d.Engine(world.env())
    jobs = e.tick()["jobs"]
    assert any(j["kind"] == "BUILD" and j["item"] == "K-1" for j in jobs), world.journal()
    assert world.journal().count(name) == 1



@pytest.mark.parametrize("name", ["J-20261013T000000Z-b1", "legacy-2", "adopted-native"])
@pytest.mark.parametrize("state", [None, "not json", "[]", "{}", '{"schema":"ky.unrecognized/1"}',
                                    '{"schema":"ky.job/1","phase":"bad","item":"K-1","slot":null}'])
def test_native_state_error_keeps_build_visible_but_refuses_admission(world, name, state):
    import kydispatch as d
    world.apply(dict(BUILD_READY, files=dict(BUILD_READY["files"], **{"$RUN/KY_WORKERS": "1\n"})), first=True)
    path = world.run / "jobs" / name / "state.json"
    path.parent.mkdir(parents=True)
    if state is not None:
        path.write_text(state)
    original = path.read_bytes() if path.exists() else None
    e = d.Engine(world.env())
    for _ in range(2):
        jobs = e.tick()["jobs"]
        build = next(j for j in jobs if j["kind"] == "BUILD" and j["item"] == "K-1")
        assert build["decision"] in ("refused:open", "wait:slot"), jobs
    assert world.journal().count(path.parent.name) == 1
    assert (path.read_bytes() if path.exists() else None) == original
    assert not any(c["cmd"] in ("local_db.sh", "kyjob.sh") for c in world.calls())


def test_j_folder_encoded_slot_refuses_unrelated_item_with_null_declared_slot(world):
    import kydispatch as d
    world.apply(dict(BUILD_READY, files=dict(BUILD_READY["files"], **{"$RUN/KY_WORKERS": "1\n"})), first=True)
    path = world.run / "jobs" / "J-20261013T000000Z-b1" / "state.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"schema":"ky.job/1","phase":"bad","item":"K-2","slot":null}')
    original = path.read_bytes()
    e = d.Engine(world.env())
    for _ in range(2):
        jobs = e.tick()["jobs"]
        assert next(j for j in jobs if j["kind"] == "BUILD" and j["item"] == "K-1")["decision"] == "wait:slot"
    assert world.journal().count(path.parent.name) == 1
    assert path.read_bytes() == original
    assert not any(c["cmd"] in ("local_db.sh", "kyjob.sh") for c in world.calls())


@pytest.mark.parametrize("name", ["legacy-2", "adopted-native"])
@pytest.mark.parametrize("reservation,decision", [("slot", "wait:slot"), ("key", "refused:open"),
                                                  ("item", "refused:open")])
def test_malformed_native_non_j_job_refuses_each_reservation(world, name, reservation, decision):
    import kydispatch as d
    world.apply(dict(BUILD_READY, files=dict(BUILD_READY["files"], **{"$RUN/KY_WORKERS": "1\n"})), first=True)
    preview = d.Engine(world.env(), dry=True)
    build = next(j for j in preview.tick()["jobs"] if j["kind"] == "BUILD" and j["item"] == "K-1")
    calls_before = len(world.calls())
    path = world.run / "jobs" / name / "state.json"
    path.parent.mkdir(parents=True)
    doc = dict(schema="ky.job/1", job_id=name, phase="bad", key="unrelated-key", item="K-2", slot="b3")
    doc[reservation] = {"key": build["key"], "item": "K-1", "slot": "b1"}[reservation]
    path.write_text(json.dumps(doc))
    original = path.read_bytes()
    e = d.Engine(world.env())
    for _ in range(2):
        jobs = e.tick()["jobs"]
        build = next(j for j in jobs if j["kind"] == "BUILD" and j["item"] == "K-1")
        assert build["decision"] == decision, jobs
    assert world.journal().count(name) == 1
    assert path.read_bytes() == original
    assert not any(c["cmd"] in ("local_db.sh", "kyjob.sh") for c in world.calls()[calls_before:])


@pytest.mark.parametrize("where", ["before_read", "after_read", "kind"])
def test_error_then_clean_ticks_rederive_build_on_same_controller(world, monkeypatch, where):
    import kydispatch as d
    world.apply(dict(BUILD_READY, slots=[]), first=True)
    e = d.Engine(world.env())
    # A prior valid reading is deliberately made stale by an event arriving during the failed tick.
    assert e.ctx.next is not None
    original = e.tracker_seen.copy()
    fired = False
    target, attr = (e, "_settle") if where == "before_read" else (d.J, "load") if where == "after_read" else (d.B, "intents")
    real = getattr(target, attr)

    def once(*args, **kwargs):
        nonlocal fired
        # For load(), fail at admission, after recover/supervise and tracker reading.
        if not fired and (where != "after_read" or e._next[0]):
            fired = True
            with (world.run / "EVENTS.jsonl").open("a") as out:
                out.write('{"kind":"decision","actor":"steward","ts":"2026-10-13T00:00:00Z","decision":"D-TEST","state":"decided","outcome":"approved","detail":"fixture event during failed tick"}\n')
            raise RuntimeError("injected late tick failure")
        return real(*args, **kwargs)

    monkeypatch.setattr(target, attr, once)
    e.tick()
    assert fired
    assert e.tracker_seen == original
    assert kyloop.loop_state(world.run, "dispatcher")[0]["tracker"] == original
    # The async tracker has not consumed the appended event yet: the previous version must wait.
    assert e.tick()["jobs"] == []
    assert e.tracker_seen == original
    assert "waiting for tracker version above" in world.journal()
    world.apply({"next": dict(BUILD_READY["next"], version=original["version"] + 1)})
    for _ in range(2):
        jobs = e.tick()["jobs"]
        assert any(j["kind"] == "BUILD" and j["item"] == "K-1" for j in jobs), jobs


@pytest.mark.parametrize("bad", ["older", "equal_changed", "snapshot", "changing", "missing", "checkpoint"])
def test_error_retry_keeps_freshness_fences(world, monkeypatch, bad):
    import kydispatch as d
    world.apply(BUILD_READY, first=True)
    world.loop(tracker_retry=True, tracker={"version": 6 if bad == "older" else "bad" if bad == "checkpoint" else 5,
                                          "events_size": 1, "events_sha256": "0" * 64})
    e = d.Engine(world.env())
    if bad == "snapshot":
        world.apply({"next": dict(BUILD_READY["next"], snapshot=True)})
    elif bad == "missing":
        (world.run / "EVENTS.jsonl").unlink()
    elif bad == "changing":
        real = e.ky

        def append_during_read(*args, **kwargs):
            result = real(*args, **kwargs)
            with (world.run / "EVENTS.jsonl").open("a") as out:
                out.write("\n")
            return result

        monkeypatch.setattr(e, "ky", append_during_read)
    checkpoint = copy.deepcopy(e.tracker_seen)
    assert e.ctx.next is None
    assert e.tracker_seen == checkpoint


def test_error_recovery_checkpoint_survives_restart(world, monkeypatch):
    import kydispatch as d
    world.apply(dict(BUILD_READY, slots=[]), first=True)
    e = d.Engine(world.env())
    assert e.ctx.next is not None

    def fail():
        (world.run / "EVENTS.jsonl").write_text("\n")
        raise RuntimeError("fixture error before reading")

    monkeypatch.setattr(e, "_settle", fail)
    e.tick()
    assert kyloop.loop_state(world.run, "dispatcher")[0]["tracker_retry"] is True
    original = e.tracker_seen.copy()
    restarted = d.Engine(world.env())
    assert restarted.tick()["jobs"] == []
    assert restarted.tracker_seen == original
    world.apply({"next": dict(BUILD_READY["next"], version=original["version"] + 1)})
    jobs = restarted.tick()["jobs"]
    assert any(j["kind"] == "BUILD" and j["item"] == "K-1" for j in jobs)


def test_a_second_instance_exits_75_and_changes_nothing(world):
    """Duplicate instance refusal: while one controller holds the real instance lock, `--once` exits 75."""
    world.apply(dict(BUILD_READY, jobs={"K-1": {"do": "sleep", "s": 60}}), first=True)
    first = world.background(["tick", {"sleep": 60}])
    end = time.monotonic() + 300                                           # until its first tick is over
    while time.monotonic() < end and (kyloop.loop_state(world.run, "dispatcher")[0].get("controller") or {}).get("pid") != first.pid:
        time.sleep(0.05)
    owner = json.loads((world.run / "locks" / "dispatcher" / "owner.json").read_text(encoding="utf-8"))
    assert owner["pid"] == first.pid and owner["session_or_run_id"].endswith("-%d" % first.pid)
    before = len(world.calls())
    second = world.cli(["--once"], patched=True)
    assert second.returncode == 75, second.stderr
    after = [c for c in world.calls()[before:] if c["cmd"] != "kygate.sh"]
    assert not [c for c in after if c["cmd"] in ("ky", "gh", "kyjob.sh", "local_db.sh")], after
    assert json.loads((world.run / "locks" / "dispatcher" / "owner.json").read_text(encoding="utf-8")) == owner
    assert first.poll() is None


def test_usage_and_credential_refusals(world):
    world.apply(BUILD_READY, first=True)
    assert world.cli(["--bogus"]).returncode == 64
    assert world.cli(["--dry", "extra"]).returncode == 64
    for name in ("ANTHROPIC_API_KEY", "PGPASSWORD", "DATABASE_URL", "KALA_DATABASE_URL"):
        done = world.cli(["--dry"], extra={name: "not-a-real-value"})
        assert done.returncode == 78 and name in done.stderr and "not-a-real-value" not in done.stderr + done.stdout
    assert world.cli(["--dry"], extra={"KY_SCRATCH": "relative/path"}).returncode == 64
    assert world.calls() == []                                             # refused before anything was asked


def test_the_real_command_line_needs_no_lock_for_dry_and_takes_it_for_once(world):
    world.apply(BUILD_READY, first=True)
    dry = world.cli(["--dry"])
    assert dry.returncode == 0 and json.loads(dry.stdout)["jobs"][0]["decision"] == "launch"
    assert not (world.run / "locks").exists()
    once = world.cli(["--once"], patched=True)
    assert once.returncode == 0, once.stderr
    lines = world.call_lines()
    assert any(x.startswith("local_db.sh close --session CTL-dispatcher-") for x in lines)       # kylock.sh release
    assert not (world.run / "locks" / "dispatcher").exists()
    loop, _ = kyloop.loop_state(world.run, "dispatcher")
    assert loop["enabled"] is True and loop["controller"]["id"].startswith("CTL-dispatcher-")
    assert re.match(r"^CTL-dispatcher-[0-9]{8}T[0-9]{6}Z-[0-9]+\Z", loop["controller"]["id"])
    assert os.path.isabs(loop["log_path"]) and loop["log_path"].startswith(str(world.scratch / "dispatcher"))
    assert kyloop.SHA_RE.match(loop["tracker"]["events_sha256"]) and loop["tracker"]["version"] == 5


def test_pr_is_mapped_to_the_shape_the_modules_document():
    import kydispatch
    doc = {"number": 7, "headRefOid": "a" * 40, "baseRefName": "main", "title": "t", "state": "OPEN",
           "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN", "mergeCommit": {"oid": "b" * 40},
           "files": [{"path": "platform/x.py", "additions": 1}], "autoMergeRequest": None,
           "statusCheckRollup": [
               {"__typename": "CheckRun", "name": "Kāla DB Tests (throwaway Postgres)", "status": "COMPLETED",
                "conclusion": "SUCCESS", "detailsUrl": "https://github.com/o/r/actions/runs/123/job/9"},
               {"__typename": "CheckRun", "name": "lint", "status": "COMPLETED", "conclusion": "FAILURE",
                "detailsUrl": "https://github.com/o/r/actions/runs/124/attempts/2/job/9"},
               {"__typename": "CheckRun", "name": "build", "status": "IN_PROGRESS", "conclusion": "",
                "detailsUrl": "https://example.invalid/elsewhere"},
               {"__typename": "StatusContext", "context": "ci/ext", "state": "PENDING", "targetUrl": None}]}
    assert kydispatch.map_pr(doc) == {
        "number": 7, "head": "a" * 40, "base": "main", "title": "t", "state": "OPEN", "mergeable": "MERGEABLE",
        "merge_state": "CLEAN", "merge_commit": "b" * 40, "files": ["platform/x.py"], "auto_merge": None,
        "checks": {"Kāla DB Tests (throwaway Postgres)": {"status": "SUCCESS", "run_id": 123, "attempt": None},
                   "lint": {"status": "FAILURE", "run_id": 124, "attempt": 2},
                   "build": {"status": "IN_PROGRESS", "run_id": None, "attempt": None},
                   "ci/ext": {"status": "PENDING", "run_id": None, "attempt": None}}}
    for broken in ({}, dict(doc, number="7"), dict(doc, headRefOid=None), dict(doc, statusCheckRollup="x"),
                   dict(doc, statusCheckRollup=[{"name": None}]), dict(doc, files=[{"nopath": 1}]), [], None):
        assert kydispatch.map_pr(broken) == "unknown"
    failure = {"__typename": "CheckRun", "name": "test", "status": "COMPLETED", "conclusion": "FAILURE",
               "detailsUrl": "https://github.com/o/r/actions/runs/1/job/9"}
    success = dict(failure, conclusion="SUCCESS", detailsUrl="https://github.com/o/r/actions/runs/2/job/9")
    for entries in ([failure, success], [success, failure]):
        assert kydispatch.map_pr(dict(doc, statusCheckRollup=entries)) == "unknown"
    assert kydispatch.map_pr(dict(doc, mergeCommit=None, statusCheckRollup=None, files=None))["checks"] == {}


@pytest.mark.parametrize("control", ["HOLD", "STOP_dispatcher", "pause", "unknown", "disabled"])
@pytest.mark.parametrize("during", ["precheck", "admit", "start"])
def test_control_changes_during_admission_hold_every_remaining_intent(world, monkeypatch, control, during):
    import kydispatch as d
    world.apply(BUILD_READY, first=True)
    e = d.Engine(world.env(), dry=True)
    e.ctx.priority = ["K-1"]
    intent = d.B.intents(e.ctx)[0]
    e.dry = False
    e.journal = lambda *args: None
    state = {"hold": False, "gate": "OPEN", "hold_merges": False, "open_keys": set(), "busy": set(),
             "short": set(), "sizes": {"builder": 6, "verifier": 4}, "provisioned": False}
    calls, closed = [], []

    def activate():
        if control == "HOLD":
            (world.root / "HOLD").touch()
        elif control == "STOP_dispatcher":
            (world.run / control).touch()
        elif control == "disabled":
            world.loop(enabled=False)
        else:
            monkeypatch.setattr(d.kc, "owner_paused", lambda run: True if control == "pause" else None)

    def check(*args):
        if during == "precheck":
            activate()
        return {"admitted": True, "refusals": [], "facts": {}}

    def opened(*args):
        calls.append("open")
        return dict(intent, job_id="J-test", slot="b1", phase="prepared", pid=None)

    def admitted(*args):
        if during == "admit":
            activate()
        return {"admitted": True, "refusals": [], "facts": {}}

    def started(*args):
        if during == "start":
            activate()
        return None

    def close(ctx, job, result):
        closed.append(result)
        return dict(job, phase="ended", **result)

    monkeypatch.setattr(d.A, "precheck", check)
    monkeypatch.setattr(d.A, "admit", admitted)
    monkeypatch.setattr(d.J, "open", opened)
    monkeypatch.setattr(d.J, "close", close)
    monkeypatch.setattr(d.B, "start", started)
    def launch(ctx, job):
        calls.append("launch")
        return dict(job, phase="live")

    monkeypatch.setattr(d.J, "launch", launch)
    assert e._admit(intent, state) == "wait:hold"
    assert e._admit(dict(intent, key="another-key"), state) == "wait:hold"
    assert "launch" not in calls
    assert calls == ([] if during == "precheck" else ["open"])
    assert [r["outcome"] for r in closed] == ([] if during == "precheck" else ["refused"])
    assert not state["busy"] and not state["open_keys"]


def test_pool_sizes_and_backoff_steps(tmp_path):
    import kydispatch
    assert kydispatch.BACKOFF_MINUTES == (5, 10, 20, 30)
    for text, want in (("3\n", 3), ("8", 8), ("1", 1), ("0", 0), ("9", 0), ("six", 0), ("", 0), ("3.0", 0), ("-2", 0)):
        (tmp_path / "KY_WORKERS").write_text(text, encoding="utf-8")
        assert kydispatch.pool_size(tmp_path / "KY_WORKERS", 6) == want, text
    assert kydispatch.pool_size(tmp_path / "absent", 6) == 6 and kydispatch.pool_size(tmp_path / "absent", 4) == 4
    (tmp_path / "dir").mkdir()
    assert kydispatch.pool_size(tmp_path / "dir", 6) == 0                  # unreadable is no capacity, not the default


def test_fresh_is_only_a_live_version_that_advanced_or_stands_on_unchanged_events():
    import kydispatch
    live = {"stream": "", "version": 5, "running": [], "ready": [], "blocked": []}
    seen = {"version": 5, "events_size": 10, "events_sha256": "a" * 64}
    now = {"events_size": 10, "events_sha256": "a" * 64}
    assert kydispatch.fresh(live, None, now) is True                       # the first reading of this run directory
    assert kydispatch.fresh(dict(live, version=6), seen, dict(now, events_size=99)) is True
    assert kydispatch.fresh(live, seen, now) is True
    assert kydispatch.fresh(live, seen, dict(now, events_sha256="b" * 64)) is False
    assert kydispatch.fresh(live, seen, dict(now, events_size=11)) is False
    assert kydispatch.fresh(live, seen, None) is False                     # EVENTS unreadable: unchanged is not shown
    assert kydispatch.fresh(dict(live, version=4), seen, now) is False
    for not_live in ({k: v for k, v in live.items() if k != "version"}, dict(live, version=True),
                     dict(live, version="5"), dict(live, version=None), [], None, "x"):
        assert kydispatch.fresh(not_live, None, now) is False              # the snapshot fallback carries no version


@pytest.mark.parametrize("reply", ["notify=failed\n", "notify=dry\n", "", "notify=submitted\nextra\n"])
def test_notification_zero_exit_is_not_submission(world, monkeypatch, reply):
    import kydispatch as d
    e = d.Engine(world.env())
    monkeypatch.setattr(e, "sh", lambda *args, **kwargs: (0, reply, ""))
    e.journal("dispatcher error", "fixture failure")
    actions, problems = ka.scan(world.run)
    assert not problems and len(actions) == 1
    assert actions[0]["state"] != "DONE"


@pytest.mark.parametrize("mutation", [
    {"stream": "K"}, {"ready": None}, {"running": {}}, {"blocked": "unknown"}, {"version": -1},
    {"ready": [{"id": "K-1", "owner": "K", "status": "done"}]},
    {"ready": [{"id": "K-1", "status": "ready"}]},
])
def test_tracker_shape_unknown_is_journalled(world, monkeypatch, mutation):
    import kydispatch as d
    e = d.Engine(world.env())
    reply = dict(stream="", version=5, running=[], ready=[], blocked=[], **{})
    reply.update(mutation)
    monkeypatch.setattr(e, "ky", lambda *args: (0, json.dumps(reply), ""))
    assert e.tracker_next() is None
    assert "tracker" in world.journal().lower() and "unknown" in world.journal().lower()


@pytest.mark.parametrize("event", [
    {}, {"kind": "guess", "actor": "steward"},
    {"kind": "item", "item": "K-1", "state": "review", "detail": "PR #7 @ " + "a" * 40},
    {"kind": "item", "item": "K-1", "actor": "stream-K:b1", "state": "done"},
    {"kind": "claim", "item": "K-1", "actor": "stream-K:b1", "state": "acquired", "claim_id": "c"},
    {"kind": "verdict", "item": "K-1", "actor": "stream-V:v1", "phase": "pre_merge",
     "head": "a" * 40, "result": "ACCEPTED"},
])
def test_event_objects_must_be_producer_records(world, event):
    import kydispatch as d
    event = dict(event, ts="2026-10-12T00:00:00Z")
    (world.run / "EVENTS.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
    e = d.Engine(world.env())
    assert e.events("K-1") is None
    assert "events" in world.journal().lower() and "unknown" in world.journal().lower()


def test_duplicate_json_keys_do_not_turn_failure_into_success(world, monkeypatch):
    import kydispatch as d
    e = d.Engine(world.env())
    doc = json.dumps(gh_pr({"number": 7, "head": "a" * 40, "checks": {"test": "SUCCESS"}}))
    doc = doc.replace('"conclusion": "SUCCESS"', '"conclusion": "FAILURE", "conclusion": "SUCCESS"')
    monkeypatch.setattr(e, "sh", lambda *args, **kwargs: (0, "[" + doc + "]", ""))
    assert e.pr("K-1") == "unknown"
    assert "unknown" in world.journal().lower()


def test_unknown_check_shapes_cannot_read_success():
    import kydispatch as d
    doc = gh_pr({"number": 7, "head": "a" * 40, "checks": {"test": "SUCCESS"}})
    for check in ({"name": "test", "status": "SUCCESS"},
                  {"name": "test", "state": "SUCCESS", "status": "SUCCESS"},
                  {"name": "test", "status": "COMPLETED", "conclusion": "UNRECOGNISED"}):
        assert d.map_pr(dict(doc, statusCheckRollup=[check])) == "unknown"


def test_pr_ambiguity_is_unknown_and_journalled(world, monkeypatch):
    import kydispatch as d
    e = d.Engine(world.env())
    replies = [gh_pr({"number": n, "head": "a" * 40}) for n in (7, 8)]
    monkeypatch.setattr(e, "sh", lambda *args, **kwargs: (0, json.dumps(replies), ""))
    assert e.pr("K-1") == "unknown"
    assert "unknown" in world.journal().lower()


def test_awaiting_answer_needs_owner_command(world):
    import kydispatch as d
    e = d.Engine(world.env())
    args = ("fixture", "The question", [{"id": "leave", "text": "leave it"}], [], None, "unknown")
    aid = e.awaiting(*args)
    world.write(world.run / "awaiting" / (aid + kyloop.OWNER_DECISION_SUFFIX),
                {"schema": kyloop.OWNER_DECISION_SCHEMA, "awaiting_id": aid, "command_id": "not-owner", "answer": "leave"})
    assert e.awaiting(*args) == aid
    assert "owner" in world.journal().lower() and "unknown" in world.journal().lower()


def test_unreadable_awaiting_does_not_create_a_second_wait(world):
    import kydispatch as d
    e = d.Engine(world.env())
    world.write(world.run / "awaiting" / "AW-20261012T000000Z-fixture.json", "{broken")
    assert e.awaiting("fixture", "q", [], [], None, "unknown") is None
    assert "unknown" in world.journal().lower()
    assert len(list((world.run / "awaiting").glob("AW-*-fixture.json"))) == 1


def test_handled_job_marker_requires_closed_backing_job(world, capsys):
    import kydispatch as d
    world.apply(BUILD_READY, first=True)
    e = d.Engine(world.env(), dry=True)
    e.ctx.priority = ["K-1"]
    intent = d.B.intents(e.ctx)[0]
    world.write(world.run / "handled" / ("job." + intent["key"] + ".json"),
                {"schema": "ky.handled/1", "id": "job." + intent["key"],
                 "checkpoint": {"job_id": "J-invented", "outcome": "done"}})
    state = {"hold": False, "gate": "OPEN", "hold_merges": False, "open_keys": set(), "busy": set(),
             "short": set(), "sizes": {"builder": 6, "verifier": 4}, "provisioned": False}
    assert e._admit(intent, state) == "wait:stale"
    assert "unknown" in capsys.readouterr().err.lower()


def test_item_detector_never_verifies_a_step_and_is_journalled(world):
    import kydispatch as d
    world.apply({"verify": {"K-1/tests": "no_echo"}}, first=True)
    e = d.Engine(world.env())
    assert e.verify("K-1", "tests") is None
    assert "unknown" in world.journal().lower() and "step" in world.journal().lower()


def test_veto_status_problems_are_unknown(world):
    import kydispatch as d
    world.write(world.run / "DECISIONS_SURROGATE.jsonl", "{broken\n")
    e = d.Engine(world.env())
    assert e.veto_status() is None
    assert "veto" in world.journal().lower() and "unknown" in world.journal().lower()


def test_unknown_action_status_runs_no_effect(world, monkeypatch):
    import kydispatch as d
    e = d.Engine(world.env())
    begin = ka.begin
    monkeypatch.setattr(ka, "begin", lambda *args: ("unknown", begin(*args)[1]))
    effects = []
    status, result = e.act("TEST", "effect", {}, {}, lambda: effects.append("ran"), lambda r: ("done", {}))
    assert status == "unknown" and not effects


def test_nonserializable_action_result_is_unknown(world):
    import kydispatch as d
    e = d.Engine(world.env())
    status, result = e.act("TEST", "effect", {}, {}, lambda: ("done", {"bad": {1, 2}}), lambda r: ("done", {}))
    assert status == "unknown"
    actions, problems = ka.scan(world.run)
    assert not problems and next(a for a in actions if a["action_id"] == "TEST")["state"] == "INTENDED"


def test_hold_merges_during_fetch_prevents_fast_forward(world, monkeypatch):
    import kydispatch as d
    e = d.Engine(world.env())
    calls = []

    def sh(argv, **kwargs):
        calls.append(argv)
        if "fetch" in argv:
            (world.run / "HOLD_MERGES").touch()
        return 0, "", ""

    monkeypatch.setattr(e, "sh", sh)
    e._refresh_checkout(False)
    assert not any("merge" in argv for argv in calls)


@pytest.mark.parametrize("backoff", [{}, {"level": 2, "until": "not a time", "job": "J-old"},
                                      {"level": "2", "until": "2026-10-12T23:00:00Z", "job": "J-old"}])
def test_unreadable_backoff_never_means_launch_now(world, backoff):
    import kydispatch as d
    world.loop(enabled=True, backoff=backoff)
    e = d.Engine(world.env())
    assert e._in_backoff() is True
    assert "unknown" in world.journal().lower()


def test_unreadable_tracker_checkpoint_cannot_reset_freshness(world, monkeypatch):
    import kydispatch as d
    world.loop(enabled=True, tracker={"version": "99"})
    e = d.Engine(world.env())
    monkeypatch.setattr(e, "ky", lambda *args: (0, json.dumps(
        {"stream": "", "version": 5, "running": [], "ready": [], "blocked": []}), ""))
    assert e.tracker_next() is None
    assert "unknown" in world.journal().lower()


def test_unknown_loop_file_is_a_reported_stop(world):
    import kydispatch as d
    world.write(world.run / "loops" / "dispatcher.json", '{"enabled": false, "enabled": true}')
    e = d.Engine(world.env())
    assert e._stopped() is True
    assert "loop" in world.journal().lower() and "unknown" in world.journal().lower()


def test_boundary_intent_is_not_wave_completion(world, capsys):
    import kydispatch as d
    world.apply({"next": {"blocked": [{"id": "K-1", "owner": "K", "status": "blocked"}]},
                 "gate": "OPEN", "slots": ["b1"]}, first=True)
    e = d.Engine(world.env(), dry=True)
    jobs = e.tick()["jobs"]
    assert any(j["kind"] == "PLAN" and j["item"] == "WAVE-BOUNDARY" for j in jobs)
    assert "[wave complete]" not in capsys.readouterr().err


@pytest.mark.parametrize("state", ["EFFECTIVE", "EXECUTED"])
def test_model_written_surrogate_state_needs_handler_record(world, monkeypatch, state):
    import kydispatch as d
    e = d.Engine(world.env())
    aid = "AW-20261012T100000Z-check"
    session = "fixture-session"
    world.write(world.run / "DECISIONS_SURROGATE.jsonl", json.dumps({
        "id": "SD-20261012T000000Z-1", "awaiting": aid, "class": "routine", "state": state,
        "decision": "reconciled", "rationale": "fixture proposal", "evidence": [],
        "target": {"kind": "capacity", "builders": 6}, "authority": {"source_commit": "a" * 40,
        "entrypoints_digest": "b" * 64}, "notification": {"submitted": False, "ts": None},
        "veto_deadline": None, "effective_at": "2026-10-12T10:00:00Z",
        "by": "kalayantra-owner-surrogate", "session": session}) + "\n")
    job = {"kind": "SURROGATE", "item": aid, "job_id": "J-test", "digest": "c" * 64,
           "provider_session_id": session, "pid": 123}
    result = e._finish(job)
    assert result["outcome"] == "interrupted"
    assert not (world.run / "handled" / ("awaiting." + aid + ".json")).exists()
    assert "unknown" in world.journal().lower()


def test_real_tracker_producers_match_the_next_inbox_and_event_fixtures(world, monkeypatch, capsys):
    import kydispatch as d
    monkeypatch.syspath_prepend(str(FLEET.parents[3] / "platform/scripts/governance"))
    from pravaha_tracker import cli, events

    live = {"stream": "", "version": 5, "running": [], "ready": [], "blocked": []}
    monkeypatch.setenv("PRAVAHA_STREAM", "")
    monkeypatch.setattr(cli, "get", lambda *args: (live, "live"))
    assert cli.cmd_next(SimpleNamespace(stream="", json=True)) == 0
    assert d.next_known(json.loads(capsys.readouterr().out))
    monkeypatch.setattr(cli, "get", lambda *args: ({"_snapshot": {"tracks": []}}, "stale-snapshot"))
    assert cli.cmd_next(SimpleNamespace(stream="", json=True)) == 0
    assert not d.next_known(json.loads(capsys.readouterr().out))
    message = events.validate({"kind": "message", "msg_id": "M-1", "to": "N", "actor": "steward",
                               "detail": "ruling", "ts": "2026-10-12T10:00:00+00:00"}, allow_model_party=True)
    monkeypatch.setattr(cli, "_read_events", lambda: [message])
    args = SimpleNamespace(stream="N", json=True, steward=False, wait=0)
    assert cli.cmd_inbox(args) == 0
    assert json.loads(capsys.readouterr().out) == [message]
    assert d.event_known(message)
    monkeypatch.setattr(cli, "_read_events", lambda: [message, {"kind": "ack", "actor": "stream-N:b1", "msg_id": "M-1"}])
    assert cli.cmd_inbox(args) == 1
    assert json.loads(capsys.readouterr().out) == []


def test_real_tracker_http_producer_has_no_step_detector(world, monkeypatch):
    import kydispatch as d
    monkeypatch.syspath_prepend(str(FLEET.parents[3] / "platform/scripts/governance"))
    from pravaha_tracker import server, detectors

    row = {"id": "K-1", "owner": "K", "status": "ready"}
    producer = SimpleNamespace(cond=threading.Condition(), snapshot={"version": 5, "tracks": [{"items": [row]}]},
        model={"items": [{"id": "K-1", "detector": {"type": "file_exists", "path": str(world.tmp / "fixture")}}]},
        det=SimpleNamespace(verify=lambda spec: detectors.DetectorResult("done", "fixture", "2026-10-12T10:00:00Z", "fixture")))
    listener = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server.make_handler(producer))
    worker = threading.Thread(target=listener.serve_forever, daemon=True)
    worker.start()
    try:
        e = d.Engine(world.env({"KY_TRACKER_URL": "http://127.0.0.1:%d" % listener.server_address[1]}))
        assert e.verify("K-1", "tests") is None
        assert "step detector unknown" in world.journal()
    finally:
        listener.shutdown()
        listener.server_close()
        worker.join(timeout=5)


def test_executor_receipt_matches_the_real_producer_and_requires_measured_output(world, monkeypatch):
    import executor
    receipts = world.run / "ops/receipts"
    receipts.mkdir(parents=True)
    monkeypatch.setattr(executor, "REC", receipts)
    monkeypatch.setattr(executor, "log", lambda text: None)
    request = {"operation_id": "OP-test", "kind": "readback_sql", "item_id": "N-OP-1", "requested_by": "adhikarin",
               "kyd": "K-1", "args": {}, "idempotency_key": "OP-test"}
    executor.receipt(request, "COMPLETED", rc=0, out="rows=12\n")
    path = receipts / "OP-test.json"
    receipt = json.loads(path.read_text())
    assert receipt["request_sha256"] == ops.request_digest(request)
    assert ops._measured_receipt(path, receipt) is True
    Path(receipt["output_file"]).write_text("changed output\n")
    assert ops._measured_receipt(path, receipt) is False
    executor.receipt(request, "COMPLETED", rc=None, out="rows=12\n")
    assert ops._measured_receipt(path, json.loads(path.read_text())) is False


@pytest.mark.parametrize("producer", ["kyboundary.sh", "kyverdicts.py"])
def test_absent_boundary_or_verdict_producer_never_succeeds(world, producer):
    import kydispatch as d
    case = next(c for c in CASES if c["name"] == "verify_of_a_registered_green_head_runs_and_publishes")
    world.apply(case["setup"], first=True)
    (world.fleet / producer).unlink()
    e = d.Engine(world.env())
    job = {"kind": "VERIFY", "item": "K-1", "job_id": "J-20261012T100000Z-verify", "head": "a" * 40,
           "job_scratch": str(world.scratch), "worktree": str(world.repo), "slot": "v1", "exit_code": 0,
           "result_path": str(world.scratch / "result.json"), "controller_id": e.controller_id, "verdict_phase": "pre_merge"}
    result = e._finish(job)
    assert result["outcome"] != "done"
    assert not any(ev.get("kind") == "verdict" and ev.get("result") == "ACCEPTED" for ev in e.events("K-1"))


def test_legacy_local_db_receipt_is_unknown_and_journalled(world, capsys, monkeypatch):
    import kydispatch as d
    world.apply(BUILD_READY, first=True)
    # The producer in this checkout is local_db.sh v1.1: lane/result/seed_sha256, no session or v3 bound hashes.
    world.write(world.run / "local_db/b1.json", {"lane": "k1", "result": "READY", "tables": 500,
        "kala_tables": 100, "ledger": 900, "unexpected_restore_errors": 0, "runner_rc": 0,
        "seed_sha256": "a" * 64, "ts": "2026-10-12T10:00:00Z"})
    e = d.Engine(world.env(), dry=True)
    monkeypatch.setattr(d.A, "GIT", str(world.bin / "git"))
    e.ctx.priority = ["K-1"]
    intent = d.B.intents(e.ctx)[0]
    state = {"hold": False, "gate": "OPEN", "hold_merges": False, "open_keys": set(), "busy": set(),
             "short": set(), "sizes": {"builder": 1, "verifier": 1}, "provisioned": False}
    assert e._admit(intent, state) == "wait:slot"
    assert "slot readiness unknown" in capsys.readouterr().err
    assert not world.jobs()


def test_ambiguous_command_observation_never_acks_the_command(world):
    import kydispatch as d
    world.loop(enabled=True)
    e = d.Engine(world.env())
    world.write(world.run / "loops/dispatcher.json", '{"priority": ["K-2"], "priority": ["K-1"]}')
    status, result = e._observe_command({"command": "priority", "args": {"item": "K-1"}})
    assert status == "unknown"
    assert "unknown" in world.journal().lower()


def test_event_cache_compares_bytes_not_only_metadata(world):
    import kydispatch as d
    e = d.Engine(world.env())
    path = world.run / "EVENTS.jsonl"
    event = {"kind": "item", "item": "K-1", "state": "review", "actor": "stream-K:b1",
             "ts": "2026-10-12T10:00:00Z", "detail": "PR #7 @ " + "a" * 40}
    path.write_text(json.dumps(event) + "\n")
    before = path.stat()
    assert e.events("K-1")[0]["detail"] == event["detail"]
    event["detail"] = "PR #7 @ " + "b" * 40
    path.write_text(json.dumps(event) + "\n")
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert path.stat().st_size == before.st_size
    assert e.events("K-1")[0]["detail"] == event["detail"]


def test_real_tracker_rows_get_declarations_from_the_plan_model(world):
    import kydispatch as d
    # state.py:304-310 emits status/steps, but no completion_kind or step_evidence declaration.
    world.apply({"next": {"ready": [{"id": "K-1", "owner": "K", "status": "ready"}]},
                 "gate": "OPEN"}, first=True)
    e = d.Engine(world.env(), dry=True)
    e.ctx.priority = ["K-1"]
    assert e.ctx.next["ready"][0]["completion_kind"] == "code"
    assert [i["kind"] for i in d.B.intents(e.ctx)] == ["BUILD"]


def test_tracker_cannot_override_the_declared_completion_kind(world):
    import kydispatch as d
    world.apply({"next": {"ready": [{"id": "K-1", "owner": "K", "status": "ready", "completion_kind": "artifact"}]}}, first=True)
    e = d.Engine(world.env())
    assert e.ctx.next is None
    assert "declaration" in world.journal().lower() and "unknown" in world.journal().lower()


POST_INSTALL = json.loads((HERE / "post_install_tracker.json").read_text(encoding="utf-8"))


def test_post_install_decision_does_not_blind_rehearsal_build(world, capsys):
    """A parked non-executable decision must not invalidate the actual all-stream reading."""
    import kydispatch as d
    world.apply({"next": POST_INSTALL["next"], "model": POST_INSTALL["model"]["items"],
                 "gate": "WAIT"}, first=True)
    world.write(world.run / "PRIORITY.txt", "KV3-B-REHEARSAL\n")
    world.packet("KV3-B-REHEARSAL", POST_INSTALL["packet"])
    e = d.Engine(world.env(), dry=True)
    answer = e.ctx.next
    assert answer is not None
    assert next(r for r in answer["blocked"] if r["id"] == "D-T2")["completion_kind"] is None
    jobs = e.tick()["jobs"]
    rehearsal = [j for j in jobs if j["item"] == "KV3-B-REHEARSAL"]
    assert len(rehearsal) == 1 and rehearsal[0]["kind"] == "BUILD"
    assert rehearsal[0]["decision"] != "wait:gate"
    assert "tracker unknown" not in capsys.readouterr().err


@pytest.mark.parametrize("done_by,join", [("decision", False), ("join", False), (None, True)])
def test_non_executable_declarations_are_known(world, done_by, join):
    import kydispatch as d
    decision = next(i for i in POST_INSTALL["model"]["items"] if i["id"] == "D-T2")
    decision = dict(decision, done_by=done_by, join=join)
    row = next(r for r in POST_INSTALL["next"]["blocked"] if r["id"] == "D-T2")
    world.apply({"next": {"blocked": [row]}, "model": [decision]}, first=True)
    assert d.Engine(world.env(), dry=True).ctx.next is not None


def test_executable_missing_declaration_still_invalidates_tick(world, capsys):
    import kydispatch as d
    fixture = copy.deepcopy(POST_INSTALL)
    for i in fixture["model"]["items"]:
        if i["id"] == "D-T2":
            del i["done_by"]
    world.apply({"next": fixture["next"], "model": fixture["model"]["items"]}, first=True)
    assert d.Engine(world.env(), dry=True).ctx.next is None
    assert "D-T2 lacks a usable declaration" in capsys.readouterr().err


@pytest.mark.parametrize("partial", [False, True])
def test_dispatcher_preserves_fixture_overrides_for_child_commands(world, partial):
    """Dropping even one override sends the CLI toward defaults or wrapper refusal."""
    import kydispatch as d
    overrides = {"PRAVAHA_HOME": str(world.scratch / "fixture"),
                 "PRAVAHA_EVENTS": str(world.run / "EVENTS.jsonl"),
                 "PRAVAHA_PLAN_MODEL": str(world.repo / PLAN_MODEL),
                 "PRAVAHA_REPO": str(world.repo), "PRAVAHA_HOLD": str(world.root / "HOLD"),
                 "PRAVAHA_TRACKER_PORT": "8768", "PRAVAHA_URL": "http://127.0.0.1:8768"}
    if partial:
        del overrides["PRAVAHA_URL"]  # forwarded unchanged; the wrapper must refuse it, never fill it in
    env = world.env(overrides)
    e = d.Engine(env, dry=True)
    names = list(overrides) + (["PRAVAHA_URL"] if partial else []) + ["KY_SOURCE_REPO", "KY_TRACKER_URL"]
    code = "import json, os; print(json.dumps({n:os.environ.get(n) for n in " + repr(names) + "}))"
    rc, out, err = e.sh([sys.executable, "-B", "-c", code])
    assert rc == 0, err
    assert json.loads(out) == {n: env.get(n) for n in names}



def test_dry_launch_refusal_names_the_missing_qualification(world, capsys):
    import kydispatch as d
    world.apply({"next": {"ready": [{"id": "KV3-B-X", "owner": "K", "status": "ready"}]},
                 "slots": ["b1"], "gate": "WAIT"}, first=True)
    world.write(world.run / "PRIORITY.txt", "KV3-B-X\n")
    (world.run / "QUALIFICATIONS" / "build-claude-sonnet-5-5.json").unlink()
    jobs = d.Engine(world.env(), dry=True).tick()["jobs"]
    assert len(jobs) == 1 and jobs[0]["decision"] == "refused:launch"
    err = capsys.readouterr().err
    assert "BUILD KV3-B-X" in err and "qualification receipt" in err


@pytest.mark.parametrize("message", ["docker cannot be observed", "slot helper failed"])
def test_provision_failure_is_named_and_journalled_once_per_change(world, monkeypatch, message):
    import kydispatch as d
    world.apply(dict(BUILD_READY, slots=[]), first=True)
    script = world.fleet / "local_db.sh"
    script.write_text("#!/bin/bash\necho '" + message + "' >&2\nexit 1\n")
    monkeypatch.setattr(d.A, "GIT", str(world.bin / "git"))
    e = d.Engine(world.env())
    for _ in range(2):
        jobs = e.tick()["jobs"]
        build = next(j for j in jobs if j["kind"] == "BUILD" and j["item"] == "K-1")
        assert build["decision"].startswith("wait:slot")
        assert message in build["decision"]
        assert "exit 1" in build["decision"]
    assert world.journal().count(message) == 1
    # The deduplication checkpoint also survives a controller restart.
    e = d.Engine(world.env())
    e.tick()
    assert world.journal().count(message) == 1
    script.write_text("#!/bin/bash\necho 'changed helper failure' >&2\nexit 2\n")
    e.tick()
    assert world.journal().count("changed helper failure") == 1
    assert not world.jobs()


def test_tick_logs_non_gate_job_in_full_before_gate_summary(world, monkeypatch):
    import kydispatch as d
    e = d.Engine(world.env())
    gates = [{"kind": "MODEL", "item": "K-%d" % n, "key": "gate-" + "x" * 80 + str(n),
              "pool": "builder", "decision": "wait:gate"} for n in range(60)]
    build = {"kind": "BUILD", "item": "KV3-B-OPS-CONTRACT", "key": "build-" + "y" * 80,
             "pool": "builder", "decision": "wait:slot (docker cannot be observed)"}
    monkeypatch.setattr(e, "_tick", lambda: {"stop": False, "jobs": gates + [build]})
    e.tick()
    lines = Path(e.log_path).read_text().splitlines()
    assert json.dumps(build, ensure_ascii=False) in lines[0]
    assert '"wait:gate": 60' in lines[-1]
    assert all(len(line) < 4025 for line in lines)


def test_lock_release_failure_is_journalled_once_with_helper_words(world, monkeypatch):
    import kydispatch as d
    e = d.Engine(world.env())
    monkeypatch.setattr(e, "sh", lambda *a, **kw: (74, "", "docker cannot be observed"))
    assert e.stop() is False
    assert e.stop() is False
    assert world.journal().count("docker cannot be observed") == 1
    assert "kylock.sh release exit 74" in world.journal()


def finish_fix_setup(world):
    """External Git/PR observations only: registration/release are the real dispatcher lifecycle."""
    head = world.head
    return dict(BUILD_READY,
                packets={'K-1': {'d1_paths': ['platform/src/a.py']}},
                jobs={'K-1': {'do': 'result_only', 'head': head, 'pr': 1}},
                replies=[{'cmd': 'gh', 'args': ['pr', 'list'], 'after': 'kyjob.sh',
                          'out': [gh_pr({'number': 1, 'head': head})]},
                         {'cmd': 'gh', 'args': ['pr', 'list'], 'out': '[]'},
                         {'cmd': 'gh', 'args': ['pr', 'view', '1'], 'out': gh_pr({'number': 1, 'head': head})},
                         {'cmd': 'git', 'args': ['ls-remote', 'origin', 'refs/heads/kalayantra/k-1'],
                          'out': head + '\trefs/heads/kalayantra/k-1\n'},
                         {'cmd': 'git', 'args': ['diff', '--name-only', '--no-renames', '-z'],
                          'out': 'platform/src/a.py\0'}])


def test_done_build_controller_registers_before_claim_release_in_real_lifecycle(world):
    setup = finish_fix_setup(world)
    world.apply(setup, first=True)
    done = world.session(['tick', {'wait_jobs': 5}, 'tick', {'wait_jobs': 5}, 'tick'])
    assert done.returncode == 0, done.stderr
    jobs = [doc for doc in world.jobs() if doc['kind'] == 'BUILD']
    assert len(jobs) == 1 and jobs[0]['outcome'] == 'done', jobs
    assert jobs[0]['head'] == world.head and jobs[0]['pr'] == 1
    ledger = [json.loads(line) for line in (world.run / 'EVENTS.jsonl').read_text().splitlines()]
    review_at = next(n for n, e in enumerate(ledger) if e.get('state') == 'review')
    release_at = next(n for n, e in enumerate(ledger) if e.get('state') == 'released')
    assert review_at < release_at
    assert ledger[review_at]['actor'] == 'stream-K:' + jobs[0]['slot']


def test_restart_recovers_two_no_post_action_jobs_without_a_third_model_build(world):
    setup = finish_fix_setup(world)
    world.apply(setup, first=True)
    done = world.session(['tick', {'wait_jobs': 5}, 'tick', {'wait_jobs': 5}, 'tick'])
    assert done.returncode == 0, done.stderr
    old = next(doc for doc in world.jobs() if doc['kind'] == 'BUILD')
    path = world.run / 'jobs' / old['job_id'] / 'state.json'
    old.update(outcome='interrupted', failure_fp='no_post_action', result_path=None)
    world.write(path, old)
    second = copy.deepcopy(old)
    second['job_id'] = 'J-20261013T103505Z-b1'
    second['job_scratch'] = str(world.scratch / 'jobs' / second['job_id'])
    world.write(world.run / 'jobs' / second['job_id'] / 'state.json', second)
    result = json.loads(Path(old['job_scratch'], 'result.json').read_text())
    result['job_id'] = second['job_id']
    world.write(Path(second['job_scratch'], 'result.json'), result)
    (world.run / 'handled' / ('job.' + old['key'] + '.json')).unlink()
    events = [json.loads(line) for line in (world.run / 'EVENTS.jsonl').read_text().splitlines()]
    world.write(world.run / 'EVENTS.jsonl', ''.join(json.dumps(e) + '\n' for e in events
                                                  if e.get('state') != 'review'))
    world.write(world.run / 'jobs' / 'failures.json', {'K-1': {'no_post_action': {
        'count': 2, 'evidence_fp': old['evidence_fp'], 'last_job': second['job_id']}}})
    world.apply({'next': {'version': 100, 'running': [{'id': 'K-1', 'status': 'running', 'owner': 'K',
                                                     'completion_kind': 'code', 'deps_open': [], 'deps_open_strict': []}],
                          'ready': [{'id': 'K-2', 'status': 'ready', 'owner': 'K'}]},
                 'replies': [{'cmd': 'gh', 'args': ['pr', 'list'],
                              'out': [gh_pr({'number': 1, 'head': world.head})]}] + setup['replies'][2:]})
    before = len([c for c in world.calls() if c['cmd'] == 'kyjob.sh'])
    done = world.session(['tick', 'tick'])
    assert done.returncode == 0, done.stderr
    after = len([c for c in world.calls() if c['cmd'] == 'kyjob.sh'])
    assert before == after == 1
    recovered = [doc for doc in world.jobs() if doc['kind'] == 'BUILD' and doc['outcome'] == 'done']
    assert len(recovered) == 1 and recovered[0]['pid'] is None, world.jobs()
    assert recovered[0]['checkpoint']['review_recovery']['job_id'] in (old['job_id'], second['job_id'])
    assert 'no_post_action' not in json.loads((world.run / 'jobs' / 'failures.json').read_text())['K-1']
    assert json.loads((world.run / 'claims' / (recovered[0]['slot'] + '.json')).read_text())['state'] == 'released'
    assert any(json.loads(line).get('state') == 'review' for line in (world.run / 'EVENTS.jsonl').read_text().splitlines())
