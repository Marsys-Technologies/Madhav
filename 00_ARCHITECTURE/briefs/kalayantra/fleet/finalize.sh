#!/usr/bin/env bash
# External finalizer v3.3 (relaunch plan v2.7 §12, KU-02 `finalize-v3`) — run by the executor on a `finalize` request after C-2 is done
# and the close PR merged: ["bash", <temporary copy>], cwd $KY_ROOT, 21600 s. A lone copy: it reads nothing next to itself (no dirname "$0");
# every collaborator is found under $KY_FLEET / $KY_ROOT. Exit 0 only after C-4's guarded completion, else 1; an argument exits 64.
# TWO PHASES (v1.2's), and a failure in either is recorded as a failure, never as an accepted receipt:
#   1. DRAIN  — kyctl.sh stop for the four loops (stop new admissions); each recorded job group in R/jobs/*/state.json that is not ended
#               is waited for until its deadline (capped by KY_DRAIN_WAIT_MIN), then TERM -> KY_TERM_GRACE_S (20) -> KILL, ONLY when its
#               recorded PID + process-start identity is proven (kyaction.process_matches is True); gone = leader False AND killpg(pgid,0) ESRCH.
#               Unknown is never signalled and never gone (busy_kept). The group of a job recorded `ended` is measured too: never
#               signalled, and busy_kept unless it is gone. Each owned item worktree is classified absent | clean | dirty_kept |
#               unpushed_kept | busy_kept. -> R/DRAIN_RECEIPT.json (result ACCEPTED only when every loop stopped, every group is gone and
#               nothing is kept). C-3 reads it.
#   2. FINAL  — a finalizer-owned, bounded (60 turns, <= 3600 s) stream-V reviewer accepts the drain receipt's exact digest -> `KY_STREAM=S ky
#               done C-3 --artifact-path R/DRAIN_RECEIPT.json`; then clean + pushed worktrees are removed (git worktree remove, never --force)
#               and `local_db.sh close --session S` runs per recorded session -> R/FINAL_RECEIPT.json (drain digest, close-report evidence, and
#               process / worktree / database absence measured now); then the V-owned C-4: V claim, a second bounded review outside ordinary
#               dispatch, an independent recheck of absence after the reviewer exits, the digest-bound verdict only if the receipt is unchanged,
#               release, `KY_STREAM=S ky done C-4 --artifact-path R/FINAL_RECEIPT.json`, and FINAL_MESSAGE.md. The tracker stays available throughout.
# Every ky event and every reviewer launch is a kyaction record (actor finalizer / supervisor); a re-run reconciles each by observation, and a
# receipt is rewritten only when its decisions changed (so a re-run after a crash keeps the digest the verdict is bound to).
# Never removes $KY_SOURCE_REPO, a branch, evidence, or anything dirty / unpushed / busy; never touches $KY_PRAVAHA_RUN except RUNNER_STOP_{A,B,C}.
# Knobs (tests shorten them): KY_DRAIN_WAIT_MIN (120) KY_FINAL_WAIT_MIN (180; caps the reviewer's wall clock) KY_FINAL_POLL_S (60)
# KY_TERM_GRACE_S (20) KY_VERIFIER_SLOTS ("v1 v2 v3 v4") KY_C4_EXTERNAL_REVIEW (path; needed when only one verifier slot exists)
# KY_FINAL_MODEL KY_FINAL_ROLE KY_SESSION_ID KY_EVENTS KY_GIT.
# Re-run after C-4 is done: FINAL_RECEIPT.json is bound to C-4's digest and nothing is run, rewritten, claimed, reviewed or published.
# Changelog: v3.3 (2026-10-12, KV3-B-FINALIZE loop 4, review b1-builds-r3 B1 + sweep) the drain and the removal measure the group of
# EVERY recorded job whatever its phase: `ended` over a group that is alive or unmeasurable is busy_kept (never signalled), keeps
# its worktree and fails the drain. Unknown ancestry is not "not ours"; a recorded pid that is no number ("pending") is unknown,
# not "no process"; a job directory holding no state is unknown. The event log is read as the tracker reads it (events.py
# validate): a line it refuses is no event, and the count passed over is printed. A DONE record of `ky done` / `ky release` counts
# only with the tracker's event behind it. local_db's hand-over record (local_db/container.json) names a session whose close is
# owed. The final message names a preserved incompatible container instead of calling it removed.
# v3.2 (2026-10-12, KV3-B-FINALIZE loop 3, review b1-builds-r2 B1 + sweep) the reviewer's provider session is MEASURED
# from the init event of its stream-json output (kyjob.sh writes no state) and recorded in its job state by this script; unmeasured,
# the author's, or another recorded job's is not independent. An acceptance counts only when the proposal names the exact digest,
# the boundary evidence is this job's object, and the tracker's latest verdict event on that digest is this job's (a re-run finds it
# there and neither checks a released view nor publishes again). A state that says `ended` is not a group that is gone; a path
# without `.git` is not absent; a `local_db.sh close` report counts only as this session's one line; its session rule is local_db's.
# v3.1 (2026-10-12, KV3-B-FINALIZE loop 2, review b1-builds-r1 B1-B4) the C-4 claim and release are observed from the
# tracker's claim event and kept record (state + claim_id), not from the record's presence; a done C-4 binds FINAL and ends the run by
# observation; absence measures every recorded job group whatever its phase; reviewer independence is measured from its job state
# (job id, provider session, process tree) against the finalizer's identity.
# v3.0 (2026-10-12, KV3-B-FINALIZE) job-state drain with process-identity rule, reviewer-gated C-3 / C-4, kyaction records, KU-02
# session-database close and absence recheck; the lane flocks, the OTHERS list and v1's own final review are gone. v1.2: lane-lock drain, v1 review.
set -u
if [ "$#" -ne 0 ]; then echo "usage: bash finalize.sh   (no arguments)" >&2; exit 64; fi
export KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
export KY_RUN="${KY_RUN:-$KY_ROOT/run}"
export KY_FLEET="${KY_FLEET:-$KY_ROOT/fleet_live}"
export KY_BIN="$KY_ROOT/bin/ky"
export KY_SCRATCH="${KY_SCRATCH:-/Users/Dev/scratch.noindex/claude/madhav/$(/bin/date +%Y%m%d)-kalayantra-v3}"
export KY_SOURCE_REPO="${KY_SOURCE_REPO:-/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign}"
export KY_PRAVAHA_RUN="${KY_PRAVAHA_RUN:-/Users/Dev/pravaha/run}"
export KY_GIT="${KY_GIT:-git}"
PY=/opt/homebrew/bin/python3
if [ ! -x "$PY" ]; then PY="$(command -v python3 || true)"; fi
if [ -z "$PY" ]; then echo "finalize.sh: python3 not found" >&2; exit 1; fi

IFS= read -r -d '' PYLIB <<'PYEOF' || true
import datetime, glob, json, os, re, shutil, signal, subprocess, sys, time, traceback
from pathlib import Path

E = os.environ
KY_ROOT, RUN, FLEET = E["KY_ROOT"], Path(E["KY_RUN"]), Path(E["KY_FLEET"])
KY, SCRATCH, GIT = E["KY_BIN"], E["KY_SCRATCH"], E["KY_GIT"]
SOURCE = os.path.realpath(E["KY_SOURCE_REPO"])
PRAVAHA_RUN = E["KY_PRAVAHA_RUN"]
EVENTS = Path(E.get("KY_EVENTS") or str(RUN / "EVENTS.jsonl"))
DRAIN_PATH, FINAL_PATH = RUN / "DRAIN_RECEIPT.json", RUN / "FINAL_RECEIPT.json"
DRAFT_PATH, MESSAGE_PATH = RUN / "FINAL_MESSAGE_DRAFT.md", RUN / "FINAL_MESSAGE.md"
LOOPS = ("dispatcher", "planner", "conductor", "veto")
SLOT_RE = re.compile(r"^[a-z][a-z0-9]{0,15}\Z")
SESSION_RE = re.compile(r"^(?!.*\.\.)[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")    # local_db.sh's own rule for --session; it refuses any other
TIME_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")
CTRL = "finalize.sh"                      # stable across re-runs: an action record is compared on kind/inputs/target, not on who
AUTHOR_ID = "finalizer:" + CTRL
PHASE = ["start"]


def knob(name, default):
    try:
        value = float(E.get(name, default))
        return value if value >= 0 else float(default)
    except ValueError:
        return float(default)


DRAIN_WAIT_MIN, FINAL_WAIT_MIN = knob("KY_DRAIN_WAIT_MIN", 120), knob("KY_FINAL_WAIT_MIN", 180)
POLL_S, GRACE_S = knob("KY_FINAL_POLL_S", 60), knob("KY_TERM_GRACE_S", 20)
VSLOTS = [s for s in E.get("KY_VERIFIER_SLOTS", "v1 v2 v3 v4").split() if SLOT_RE.match(s)]
OWN_SESSION = E.get("KY_SESSION_ID", "") if SESSION_RE.match(E.get("KY_SESSION_ID", "")) else "finalizer"

sys.path.insert(0, str(FLEET))
try:
    import kyaction
except Exception as exc:                  # without the process-identity rule nothing may be signalled or called gone
    kyaction = None
    KYACTION_ERROR = "%s: %s" % (type(exc).__name__, exc)


def say(text):
    print(text, flush=True)


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def read_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle), None
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError):
        return None, "unreadable"


def atomic_write(path, text):
    tmp = "%s.tmp.%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def sha_file(path):
    return kyaction.sha_file(path)


def tail(text, n=300):
    return " ".join((text or "").split())[-n:]


def run(argv, env=None, timeout=300, cwd=None):
    """(returncode, stdout, stderr); returncode None when the program could not be run or timed out (unknown)."""
    try:
        r = subprocess.run([str(a) for a in argv], env=env, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return None, "", "timeout"
    except OSError as exc:
        return None, "", "oserror:%s" % exc.errno
    return r.returncode, r.stdout, r.stderr


def posint(v):
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def parse_time(text):
    """Epoch seconds of `YYYY-MM-DDTHH:MM:SSZ` and nothing else; any other form is unknown (None)."""
    if not isinstance(text, str) or not TIME_RE.match(text):
        return None
    return kyaction.parse_utc(text)


# ───────────────────────────── receipts: write-then-rename, rewritten only when the decisions changed ─────────────────────────────

GONE_JOB = {"exited", "terminated", "killed", "ended"}


def canon(doc):
    """What a receipt decides, without the clock, the raw evidence and the ways a thing came to be gone."""
    d = {k: v for k, v in doc.items() if k not in ("ts", "absence_detail")}
    if isinstance(d.get("jobs"), list):
        d["jobs"] = [dict(j, result="gone" if j.get("result") in GONE_JOB else j.get("result"), reason=None) for j in d["jobs"]]
    if isinstance(d.get("lanes"), dict):
        d["lanes"] = {k: "gone" if v in ("removed", "absent") else v for k, v in d["lanes"].items()}
    if isinstance(d.get("worktrees"), list):
        d["worktrees"] = [dict(w, state="gone" if w.get("state") in ("removed", "absent") else w.get("state"), reason=None) for w in d["worktrees"]]
    return json.dumps(d, sort_keys=True)


def receipt(path, schema, result, lanes, extra, frozen_digest=None):
    """Write `path` (tmp file + rename) → (doc as it is on disk, sha256, written). Keys of v1.2 kept: ts result lanes branches
    campaign_worktree phase. A file already bound to `frozen_digest`, or equal in decisions, is left byte for byte."""
    doc = {"schema": schema, "ts": now_iso(), "result": result, "lanes": lanes, "branches": "kept", "campaign_worktree": "kept"}
    doc.update(extra)
    old, _ = read_json(path)
    if isinstance(old, dict) and ((frozen_digest and sha_file(path) == frozen_digest) or canon(old) == canon(doc)):
        return old, sha_file(path), False
    atomic_write(str(path), json.dumps(doc, indent=1) + "\n")
    return doc, sha_file(path), True


# ───────────────────────────── job states, process identity, signalling ─────────────────────────────

def job_states():
    states, problems = [], []
    for folder in sorted(glob.glob(str(RUN / "jobs" / "*"))):       # a job this script cannot read is not "no job"
        if not os.path.isdir(folder):
            continue                              # a file beside the job directories (kyd_jobs.py's failures.json) is no job
        try:
            if not os.path.lexists(os.path.join(folder, "state.json")) and os.listdir(folder):
                problems.append({"path": folder, "problem": "job_directory_without_state"})
        except OSError:
            problems.append({"path": folder, "problem": "job_directory_unreadable"})
    for path in sorted(glob.glob(str(RUN / "jobs" / "*" / "state.json"))):
        doc, err = read_json(path)
        if err or not isinstance(doc, dict):
            problems.append({"path": path, "problem": "state_unreadable"})
        elif doc.get("job_id") != Path(path).parent.name:
            problems.append({"path": path, "problem": "job_id_differs_from_directory"})
        else:
            states.append((path, doc))
    return states, problems


def identity_ok(s):
    return (posint(s.get("pid")) and posint(s.get("pgid")) and s["pgid"] > 1
            and isinstance(s.get("process_start"), str) and bool(s["process_start"].strip()))


def group_absent(pgid):
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    return False


def group_state(pid, pgid, start):
    """'gone' = the leader is positively not that process AND killpg(pgid, 0) says ESRCH · 'alive' · 'unknown'."""
    if not (posint(pid) and posint(pgid) and pgid > 1 and isinstance(start, str) and start.strip()):
        return "unknown"
    leader = kyaction.process_matches(pid, start)
    if leader is None:
        return "unknown"
    if leader is True:
        return "alive"
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return "gone"
    except PermissionError:
        return "alive"
    except OSError:
        return "unknown"
    return "alive"


def recorded_group(s):
    """The group a job state records, measured now and whatever the state's phase says: 'none' (no pid and no pgid were
    ever recorded: both null) · 'gone' · 'alive' · 'unknown' (an identity that cannot be compared, or a recorded pid that
    is no number, as the "pending" kyd_jobs.py writes while it launches). A reviewer of this script whose start identity
    was never read is judged by its group alone: this script started it as its own group leader."""
    if s.get("pid") is None and s.get("pgid") is None:
        return "none"
    if identity_ok(s):
        return group_state(s["pid"], s["pgid"], s["process_start"])
    if posint(s.get("pgid")) and s["pgid"] > 1 and str(s.get("key", "")).startswith("finalize-"):
        return "gone" if group_absent(s["pgid"]) else "alive"
    return "unknown"


def wait_gone(pid, pgid, start, seconds):
    end = time.time() + seconds
    while True:
        if group_state(pid, pgid, start) == "gone":
            return True
        if time.time() >= end:
            return False
        time.sleep(0.05)


def terminate(pid, pgid, start):
    """TERM -> grace -> KILL, only for a leader proven to be the recorded process. → (result, reason)."""
    if kyaction.process_matches(pid, start) is not True:
        return "busy_kept", "leader_not_proven_alive_group_not_signalled"
    try:
        if os.getpgid(pid) != pgid:
            return "busy_kept", "pgid_is_not_the_recorded_group"
    except OSError:
        return "busy_kept", "pgid_unreadable"
    for sig, seconds, done in ((signal.SIGTERM, GRACE_S, "terminated"), (signal.SIGKILL, 10.0, "killed")):
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            pass
        except OSError as exc:
            return "busy_kept", "signal_failed:%s" % exc.errno
        if wait_gone(pid, pgid, start, seconds):
            return done, None
    return "busy_kept", "survived_kill"


def drain_one(path, s, signalling):
    if s.get("phase") not in ("prepared", "live", "terminating"):
        return "busy_kept", "unknown_phase"
    missing = [k for k in ("job_id", "item", "slot", "worktree", "pid", "pgid", "process_start", "deadline") if k not in s]
    if missing:
        return "busy_kept", "missing_keys:" + ",".join(missing)
    if not identity_ok(s):
        return "busy_kept", "unknown_identity"
    deadline = parse_time(s["deadline"])
    if deadline is None:
        return "busy_kept", "deadline_not_utc_text"
    pid, pgid, start = s["pid"], s["pgid"], s["process_start"]
    if pgid == os.getpgrp() or kyaction.is_self_or_ancestor(pid) is not False:      # unknown ancestry is not "not ours"
        return "busy_kept", "own_process_tree_or_unknown"
    state = group_state(pid, pgid, start)
    if state == "gone":
        return "exited", None
    if state == "unknown":
        return "busy_kept", "identity_unknown"
    if not signalling:
        return "busy_kept", "loops_not_confirmed_stopped"
    end = min(deadline, time.time() + DRAIN_WAIT_MIN * 60)
    while time.time() < end:
        time.sleep(max(0.0, min(POLL_S, 5.0, end - time.time())))
        fresh, _ = read_json(path)
        state = group_state(pid, pgid, start)
        if state == "gone":                       # the record saying `ended` is not the measurement: only a gone group is
            return ("ended" if isinstance(fresh, dict) and fresh.get("phase") == "ended" else "exited"), None
        if state == "unknown":
            return "busy_kept", "identity_unknown"
    return terminate(pid, pgid, start)


# ───────────────────────────── worktrees ─────────────────────────────

def git(path, *args):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    return run([GIT, "-C", path, *args], env=env, timeout=180)


def owned_worktrees(states):
    """{realpath: recorded path}: every worktree a job state names, except the campaign checkout (never removed)."""
    protected = {SOURCE, os.path.realpath(os.path.join(KY_ROOT, "wt", "campaign"))}
    seen, problems = {}, []
    for path, s in states:
        wt = s.get("worktree")
        if wt in (None, ""):
            continue
        if not isinstance(wt, str) or not os.path.isabs(wt):
            problems.append({"path": path, "problem": "worktree_not_an_absolute_path"})
            continue
        key = os.path.realpath(wt)
        if key not in protected:
            seen.setdefault(key, key)
    return seen, problems


def lane_names(paths):
    counts = {}
    for p in paths:
        counts[os.path.basename(p)] = counts.get(os.path.basename(p), 0) + 1
    return {p: (os.path.basename(p) if counts[os.path.basename(p)] == 1 else p) for p in paths}


def worktree_state(path, busy):
    if path in busy:
        return "busy_kept", "a_job_of_this_worktree_is_not_proven_gone"
    if not os.path.lexists(path):
        return "absent", None
    if not os.path.lexists(os.path.join(path, ".git")):
        return "dirty_kept", "present_but_not_a_git_worktree"
    rc, out, _ = git(path, "status", "--porcelain")
    if rc != 0:
        return "dirty_kept", "git_status_failed"
    if out.strip():
        return "dirty_kept", "uncommitted_changes"
    rc, out, _ = git(path, "rev-list", "--count", "HEAD", "--not", "--remotes")
    if rc != 0 or not out.strip().isdigit():
        return "unpushed_kept", "git_rev_list_failed"
    if int(out.strip()):
        return "unpushed_kept", "%s_commits_on_no_remote" % out.strip()
    return "clean", None


def busy_worktrees(states, job_results=None):
    """Worktrees of a recorded job whose group is not proven gone, whatever its phase: `job_results` are the drain's
    own measurements; without them each group is measured now (an ended job that never recorded a process has none)."""
    busy = set()
    for path, s in states:
        if not isinstance(s.get("worktree"), str):
            continue
        if job_results is not None:
            gone = job_results.get(s.get("job_id")) in GONE_JOB
        elif s.get("phase") == "ended":
            gone = recorded_group(s) in ("none", "gone")
        else:
            gone = identity_ok(s) and group_state(s["pid"], s["pgid"], s["process_start"]) == "gone"
        if not gone:
            busy.add(os.path.realpath(s["worktree"]))
    return busy


def remove_worktrees(trees, busy):
    """{path: (state, reason)}; a clean + pushed worktree goes through `git worktree remove` (never --force)."""
    out = {}
    for path in sorted(trees):
        state, why = worktree_state(path, busy)
        if state == "clean":
            rc, _, err = run([GIT, "-C", SOURCE, "worktree", "remove", path], timeout=300)
            if rc == 0 and not os.path.lexists(path):
                state, why = "removed", None
            else:
                state, why = "remove_failed", "git_worktree_remove_rc=%s %s" % (rc, tail(err, 120))
        out[path] = (state, why)
    run([GIT, "-C", SOURCE, "worktree", "prune"], timeout=300)
    return out


# ───────────────────────────── absence, measured now ─────────────────────────────

RANK = {"absent": 0, "unknown": 1, "survivor": 2}


def worse(a, b):
    return a if RANK[a] >= RANK[b] else b


def measure_processes():
    states, bad = job_states()
    verdict, detail = "unknown" if bad else "absent", [dict(b) for b in bad]
    for path, s in states:
        state = recorded_group(s)
        if state == "none" and s.get("phase") == "ended":
            continue                              # ended without ever recording a process: there is no group to measure
        if state == "none":
            state = "unknown"                     # not ended and no process recorded: it may be starting
        if state != "gone":
            verdict = worse(verdict, "survivor" if state == "alive" else "unknown")
            detail.append({"job_id": s.get("job_id"), "group": state})
    return verdict, detail


def measure_worktrees(trees):
    rc, out, _ = run([GIT, "-C", SOURCE, "worktree", "list", "--porcelain"], timeout=120)
    registered = set(os.path.realpath(line[9:]) for line in (out or "").splitlines() if line.startswith("worktree "))
    present = [p for p in sorted(trees) if os.path.lexists(p) or p in registered]
    if present:
        return "survivor", present
    return ("absent", []) if rc == 0 else ("unknown", ["git worktree list failed"])


def close_report_line(out, sid):
    """(container, dropped) from the ONE line local_db.sh prints for a close, `close session=S dropped=<n> container=<c>`,
    and only when it names this session; any other output is unknown (None, None)."""
    found = None
    for line in (out or "").splitlines():
        words = line.split()
        if words[:1] != ["close"]:
            continue
        pairs = [w.split("=", 1) for w in words[1:] if "=" in w]
        keys = [k for k, _ in pairs]
        tokens = dict(pairs)
        if len(keys) != len(set(keys)) or tokens.get("session") != sid:
            continue
        if tokens.get("container") and (tokens.get("dropped") or "").isdigit():
            found = (tokens["container"], int(tokens["dropped"]))
        else:
            found = (None, None)
    return found or (None, None)


def db_close(prior=(), recheck=False):
    """local_db.sh close --session S per recorded session (none: once, our own session). → (state, detail)."""
    sessions, unreadable = set(prior), []
    for path in sorted(glob.glob(str(RUN / "local_db" / "*.json"))):
        doc, _ = read_json(path)
        if os.path.basename(path) == "container.json":
            # not a slot receipt: the hand-over record `close` leaves, {"owner": T, "storage": <absolute path>, "from": S}
            # (KV3-B-LOCALDB). Its owner is a session whose close is owed; while the file exists a container is on record.
            known = isinstance(doc, dict) and {"owner", "storage", "from"} <= set(doc) \
                and isinstance(doc["storage"], str) and os.path.isabs(doc["storage"])
            sid = doc["owner"] if known else None
        else:
            sid = doc.get("session_id") if isinstance(doc, dict) else None
        if isinstance(sid, str) and SESSION_RE.match(sid):
            sessions.add(sid)
        else:
            unreadable.append(path)
    sessions = sessions or {OWN_SESSION}
    results, state = [], "unknown" if unreadable else "absent"
    for sid in sorted(sessions):
        rc, out, err = run(["bash", FLEET / "local_db.sh", "close", "--session", sid], timeout=900)
        container, dropped = close_report_line(out, sid)
        row = {"session": sid, "exit": rc, "container": container, "dropped": dropped, "stdout": tail(out, 200)}
        results.append(row)
        if rc is None or rc != 0:                 # no call, or exit 1 / not proven: a survivor
            state = worse(state, "survivor")
        elif container not in ("removed", "absent", "incompatible"):
            state = worse(state, "survivor" if container else "unknown")
        elif recheck and row["dropped"] != 0:
            state = worse(state, "survivor" if row["dropped"] else "unknown")
    remaining = sorted(glob.glob(str(RUN / "local_db" / "*.json")))
    if remaining:
        state = worse(state, "survivor")          # a receipt or hand-over record that outlives its close: stale, or the close is untrue
    return state, {"sessions": results, "receipts_remaining": remaining, "unreadable_receipts": unreadable,
                   "incompatible_containers_preserved": [r["session"] for r in results if r["container"] == "incompatible"]}


# ───────────────────────────── tracker events (observation) and kyaction records ─────────────────────────────

EVENT_KINDS = {"item", "decision", "heartbeat", "note", "metric", "message", "ack", "claim", "verdict"}
ITEM_STATES = {"ready", "running", "review", "blocked", "parked", "failed", "done"}
PASSED_OVER = [0]


def iso_time(text):
    try:
        datetime.datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return False
    return True


def tracker_event(ev):
    """True for a line the tracker's own readers keep (pravaha_tracker/events.py validate, applied by claims.py _read
    and EventLog.refresh), for the kinds read here: item, claim, verdict. A line it refuses is malformed to the
    tracker — it completes, claims and accepts nothing there, so it does nothing here."""
    if not isinstance(ev, dict) or ev.get("kind") not in EVENT_KINDS or not ev.get("actor"):
        return False
    if ev.get("ts") and not iso_time(ev["ts"]):
        return False
    kind = ev["kind"]
    if kind == "item":
        state = ev.get("state")
        return bool(ev.get("item")) and state in ITEM_STATES and not (state == "done" and not ev.get("evidence")) \
            and not (state in ("blocked", "failed", "parked") and not ev.get("detail"))
    if kind == "claim":
        return ev.get("state") in ("acquired", "renewed", "released", "expired") \
            and all(ev.get(k) for k in ("item", "worker_id", "claim_id", "expires_at")) and iso_time(ev["expires_at"])
    if kind == "verdict":
        head, digest = ev.get("head"), ev.get("artifact_digest")
        if not ev.get("item") or ev.get("result") not in ("ACCEPTED", "REJECTED") or not ev.get("detail") \
                or ev.get("phase") not in ("pre_merge", "post_deploy", "artifact") or bool(head) == bool(digest):
            return False
        if head and not (isinstance(head, str) and re.fullmatch(r"[0-9a-f]{40}", head)):
            return False
        if digest and not (isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)):
            return False
        return bool(digest) if ev["phase"] == "artifact" else bool(head)
    return True


def events():
    """The events the tracker itself reads from its log, or None when the log exists and cannot be read; a missing
    log is no events. PASSED_OVER counts the non-empty lines of the latest read that are not events to the tracker."""
    try:
        data = EVENTS.read_bytes()
    except FileNotFoundError:
        return []
    except OSError:
        return None
    out, skipped = [], 0
    for line in data.splitlines():                # line by line, as claims.py _read: one bad line is not an unreadable log
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        if tracker_event(row):
            out.append(row)
        else:
            skipped += 1
    PASSED_OVER[0] = skipped
    return out


def done_event(item, digest=None):
    evs = events()
    if evs is None:
        return "unknown", {"error": "events_unreadable"}
    for e in reversed(evs):
        if e.get("kind") == "item" and e.get("item") == item and e.get("state") == "done" and e.get("guarded") is True:
            completion = e.get("completion") if isinstance(e.get("completion"), dict) else {}
            got = completion.get("artifact_digest")
            if digest is None or got == digest:
                return "done", {"item": item, "artifact_digest": got, "path": completion.get("path")}
    return "not_done", {}


def verdict_of(item, digest, job_id):
    """The tracker's LATEST artifact verdict on (item, digest) — the event its guarded completion reads (verdicts.py
    accepted_verdict; a later rejection at the same identity revokes). → ('published', result) when that event is job
    `job_id`'s (detail `job <J>; …`, as kyverdicts.py publishes it) · ('none', result of another's or None) · ('unknown', None)."""
    evs = events()
    if evs is None:
        return "unknown", None
    last = next((e for e in reversed(evs) if e.get("kind") == "verdict" and e.get("item") == item and e.get("phase") == "artifact"
                 and e.get("head") is None and e.get("artifact_digest") == digest), None)
    if last is None:
        return "none", None
    mine = isinstance(last.get("detail"), str) and last["detail"].startswith("job %s;" % job_id)
    if mine and last.get("result") in ("ACCEPTED", "REJECTED"):
        return "published", last["result"]
    return "none", last.get("result") if isinstance(last.get("result"), str) else None


ACTIVE_CLAIM = ("acquired", "renewed")


def claim_view(item, slot):
    """The tracker's latest claim event on `item` (its locked event log is the authority) and its copy in
    claims/<slot>.json, which the tracker keeps after a release with the state rewritten. → (None, error) or (event, record)."""
    evs = events()
    if evs is None:
        return None, "events_unreadable"
    last = next((e for e in reversed(evs) if e.get("kind") == "claim" and e.get("item") == item), None)
    record, _ = read_json(EVENTS.parent / "claims" / (slot + ".json"))
    return last, (record if isinstance(record, dict) else None)


def claim_brief(e):
    return {k: e.get(k) for k in ("item", "worker_id", "claim_id", "state", "expires_at")} if isinstance(e, dict) else None


def observe_claim(item, slot):
    """'done' only while `slot` holds an active (acquired/renewed), unexpired claim on `item`, the same in the event log and in its record."""
    last, record = claim_view(item, slot)
    if last is None and isinstance(record, str):
        return "unknown", {"error": record}
    if not (last and last.get("worker_id") == slot and last.get("state") in ACTIVE_CLAIM
            and isinstance(last.get("claim_id"), str) and last["claim_id"]):
        return "not_done", {"latest": claim_brief(last)}
    expires = kyaction.parse_utc(last.get("expires_at")) if isinstance(last.get("expires_at"), str) else None
    if expires is None:
        return "unknown", {"latest": claim_brief(last), "error": "expires_at_unreadable"}
    if time.time() >= expires:
        return "not_done", {"latest": claim_brief(last), "error": "lease_expired"}
    if not record or record.get("claim_id") != last["claim_id"] or record.get("state") != last["state"]:
        return "not_done", {"latest": claim_brief(last), "record": claim_brief(record), "error": "record_differs_from_event_log"}
    return "done", {"item": item, "worker": slot, "claim_id": last["claim_id"], "state": last["state"], "expires_at": last.get("expires_at")}


def observe_release(item, slot, claim_id):
    """'done' only when the latest claim event on `item` is claim `claim_id` of `slot` in state released."""
    if not (isinstance(claim_id, str) and claim_id):
        return "unknown", {"error": "claim_id_unknown"}
    last, record = claim_view(item, slot)
    if last is None and isinstance(record, str):
        return "unknown", {"error": record}
    if last and last.get("claim_id") == claim_id and last.get("worker_id") == slot and last.get("state") == "released":
        return "done", {"item": item, "worker": slot, "claim_id": claim_id, "state": "released"}
    return "not_done", {"latest": claim_brief(last)}


ACTOR = {"role": "finalizer", "holder_kind": "supervisor", "controller_id": CTRL}


def act(action_id, kind, inputs, target, transition, effect, observer, confirm=False):
    """One side effect under a kyaction record, reconciled by observation on a re-run → ('done'|'failed'|'unknown', result).
    `confirm`: a record found DONE is this script's own note of an earlier run; it counts only when the observer still
    sees the tracker's event behind it (else unknown: nothing is repeated on a guess and nothing is called done)."""
    run_dir = str(RUN)
    try:
        status, rec = kyaction.begin(run_dir, action_id, kind, ACTOR, inputs, target, transition)
        if status == "failed":
            kyaction.retry(run_dir, action_id, ACTOR)
            status = "new"
        if status == "done":
            if confirm:
                seen, detail = observer(rec)
                if seen != "done":
                    return "unknown", {"error": "record_done_but_not_observed", "observed": seen, "detail": detail, "action_id": action_id}
            return "done", rec["result"]
        if status == "in_progress":
            return "unknown", {"error": "another_process_holds_the_record", "action_id": action_id}
        if status == "unfinished":
            outcome, rec = kyaction.reconcile(run_dir, action_id, observer, by=CTRL)
            if outcome == "done":
                return "done", rec["result"]
            if outcome != "not_done":
                return "unknown", {"error": "reconciliation_%s" % outcome, "action_id": action_id}
        ok, result = effect()
        if ok:
            kyaction.complete(run_dir, action_id, result)
            return "done", result
        kyaction.fail(run_dir, action_id, result)
        return "failed", result
    except kyaction.ActionError as exc:
        return "unknown", {"error": "%s: %s" % (type(exc).__name__, tail(str(exc), 200)), "action_id": action_id}


def ky_effect(argv, stream, lane, observe):
    """Run ky; the record says what was OBSERVED afterwards, never the exit status alone."""
    env = dict(os.environ, KY_STREAM=stream)
    if lane:
        env["KY_LANE"] = lane
    else:
        env.pop("KY_LANE", None)
    rc, out, err = run([KY, *argv], env=env, timeout=900)
    seen, detail = observe()
    if seen == "done":
        return True, dict(detail, exit=rc)
    return False, {"exit": rc, "observed": seen, "detail": detail, "stderr": tail(err, 120)}


def ky_done(item, receipt_path, digest):
    return act("FIN-ky-done-%s-%s" % (item, digest[:12]), "ky_done", {"item": item, "artifact_path": str(receipt_path), "artifact_sha256": digest},
               {"verb": "done", "item": item}, "tracker marks %s done through its guarded completion" % item,
               lambda: ky_effect(["done", item, "--artifact-path", str(receipt_path)], "S", None, lambda: done_event(item, digest)),
               lambda rec: done_event(item, digest), confirm=True)


# ───────────────────────────── the reviewer: a finalizer-owned, bounded stream-V job ─────────────────────────────

CARD = """---
card: FINALIZER_REVIEW
version: 3.0
role: Independent bounded reviewer of one finalizer receipt (stream V, kind ARTIFACT)
model: Opus 5.5
effort: high
status: generated by finalize.sh v3 for this one job
---
Precedence: CLAUDE.md §I/§N > owner decisions > plan > card > packet.

- FR-01 `JOB_SCRATCH` and `KY_SCRATCH` come from the job environment. If either is unset or not an absolute path: stop, write `blocked`, write nothing else.
- FR-02 You are read-only by configuration, not sandboxed: write only under `$JOB_SCRATCH` or `$TMPDIR`; never the repository, the tracker, `/Users/Dev/kalayantra` or the receipt under review.
- FR-03 No tracker verb, no push, no network, no launch command, no credential read, no environment listing. You propose a verdict; the controller publishes it.
- FR-04 Independent: you authored nothing under review. Check the receipt's sha256 now and again at the end; any difference is `blocked`, `receipt-changed`.
- FR-05 Earned signal: a claim in the receipt is true only if you measured the thing it asserts (a process group, a worktree, a database) or recomputed it from files; a file that merely exists, a timestamp or another receipt's result is not a measurement. Otherwise the claim is unproven and the verdict is REJECTED.
- FR-06 Unknown is null. Never fabricate a hash, count or test result.
- FR-07 Last act: with `python3`, write `$JOB_SCRATCH/result.json` = {"schema":"ky.job_result/1","job_id","item","status":"done|blocked|failed","branch":null,"head_sha":null,"pr_number":null,"tests":[{"cmd","exit","summary"}],"blocked_reason":<string|null>,"notes","proposed_verdict":{"verdict":"ACCEPTED|REJECTED","artifact_digest":"<64-hex>","blocking":[...]}}. ACCEPTED only when every check below passed.
"""


def packet_text(phase, item, receipt_path, digest):
    what = {"drain": ("DRAIN_RECEIPT.json", "every loop `stopped`; every job group gone (a recorded PID + process-start identity, leader not that process AND `killpg(pgid, 0)` ESRCH); no worktree dirty, unpushed or busy; `result` ACCEPTED follows from those facts and from nothing else"),
            "final": ("FINAL_RECEIPT.json", "`drain_sha256` equals the sha256 of the drain receipt in the same directory; `close_report.sha256` equals the sha256 of the file at `close_report.path`; every `lanes` entry is `removed` or `absent`; `absence.processes`, `absence.worktrees` and `absence.databases` are each `absent` and agree with what you can observe now (job states under `jobs/`, the paths in `lanes`)")}[phase]
    return """# Review of %s (item %s)

Receipt: %s
Exact digest under review (sha256): %s

Verify, by measuring or recomputing:
- the file's sha256 is exactly the digest above;
- %s;
- the receipt asserts nothing it does not measure (BS-09 / FR-05); anything unmeasured is null or unknown, not a pass.

Propose ACCEPTED only if every point holds; otherwise REJECTED with the blocking points.
""" % (what[0], item, receipt_path, digest, what[1])


def new_job_id(slot):
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    os.makedirs(RUN / "jobs", exist_ok=True)
    n = 0
    while True:
        job_id = "J-%s-%s" % (stamp, slot) + (".%d" % n if n else "")
        try:
            os.mkdir(RUN / "jobs" / job_id)
        except FileExistsError:
            n += 1
            continue
        return job_id


READ_ONLY = ("--allowedTools=Bash(shasum:*),Bash(wc:*),Bash(ls:*),Bash(python3:*),Bash(git show:*),Bash(git diff:*),"
             "Bash(git log:*),Bash(git status:*)")
DISALLOWED = ["Edit", "Write", "NotebookEdit", "Task", "Workflow", "CronCreate", "CronDelete", "RemoteTrigger", "ScheduleWakeup",
              "PushNotification", "SendMessage", "EnterWorktree", "ExitWorktree", "WebFetch", "WebSearch", "Skill",
              "Bash(git add*)", "Bash(git commit*)", "Bash(git push*)", "Bash(git merge*)", "Bash(git switch*)",
              "Bash(git checkout*)", "Bash(git worktree*)", "Bash(git branch*)", "Bash(git reset*)", "Bash(git rebase*)",
              "Bash(git stash*)", "Bash(git tag*)", "Bash(git fetch*)", "Bash(git pull*)", "Bash(git config*)",
              "Bash(git remote*)", "Bash(*--output*)", "Bash(gh *)", "Bash(npm *)", "Bash(psql*)", "Bash(launchctl*)", "Bash(curl*)"]


def reviewer_env():
    keep = ("PATH", "HOME", "USER", "LANG", "KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SCRATCH", "SE_EPHE_PATH", "SWE_EPHE_PATH")
    env = {k: E[k] for k in keep if k in E}
    env["TERM"] = "dumb"
    return env


def stop_started_group(proc):
    """TERM -> grace -> KILL on the group of a process THIS script started (identity is certain); True when it is gone."""
    pgid = proc.pid
    for sig, seconds in ((signal.SIGTERM, GRACE_S), (signal.SIGKILL, 10.0)):
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            break
        except OSError:
            pass
        end = time.time() + seconds
        while time.time() < end and not group_absent(pgid):
            proc.poll()
            time.sleep(0.05)
        if group_absent(pgid):
            break
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    return group_absent(pgid)


def provider_session(stdout_path):
    """The provider session the reviewer's program itself reported: `session_id` of the init event of its stream-json
    output (kyjob.sh redirects it to stdout_path and writes no state). None — unknown — when the stream is missing or
    unreadable, carries no init event, an init event names no session, or its init events disagree."""
    seen = set()
    try:
        with open(stdout_path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict) and row.get("type") == "system" and row.get("subtype") == "init":
                    sid = row.get("session_id")
                    seen.add(sid if isinstance(sid, str) and sid.strip() else None)
    except OSError:
        return None
    return next(iter(seen)) if len(seen) == 1 and None not in seen else None


def save_state(path, state):
    atomic_write(str(path), json.dumps(state, indent=1) + "\n")


def result_of(state, slot, timed_out, group_gone, scratch=None):
    scratch = Path(scratch or state["job_scratch"])
    result = scratch / "result.json"
    return {"job_id": state["job_id"], "vslot": slot, "exit_code": state.get("exit_code"), "timed_out": timed_out,
            "group_gone": group_gone, "scratch": str(scratch), "result_path": str(result) if result.is_file() else None,
            "state_path": str(RUN / "jobs" / state["job_id"] / "state.json"), "snapshot_path": str(scratch / "snapshot.json"),
            "receipt_sha256": state.get("digest")}


def launch_reviewer(phase, item, receipt_path, digest, slot):
    key = "finalize-%s-%s" % (phase, digest[:12])
    job_id = new_job_id(slot)
    state_path = RUN / "jobs" / job_id / "state.json"
    scratch = Path(SCRATCH) / "jobs" / job_id
    try:
        (scratch / "tmp").mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        os.rmdir(RUN / "jobs" / job_id)
        return False, {"job_id": job_id, "error": "scratch_not_created:%s" % exc.errno}
    snapshot = scratch / "snapshot.json"
    rc, out, err = run([sys.executable, FLEET / "kyverdicts.py", "snapshot", "--worktree", SOURCE, "--out", snapshot], timeout=600)
    if rc != 0:
        shutil.rmtree(scratch, ignore_errors=True)
        os.rmdir(RUN / "jobs" / job_id)
        return False, {"job_id": job_id, "error": "snapshot_failed", "exit": rc, "stderr": tail(err)}
    review_s = max(1.0, min(3600.0, FINAL_WAIT_MIN * 60))
    deadline_epoch = time.time() + review_s
    header = {"job_id": job_id, "item": item, "kind": "ARTIFACT", "slot": slot, "worktree": SOURCE, "branch": None,
              "base_sha": None, "deadline": kyaction.utc(deadline_epoch), "job_scratch": str(scratch),
              "result_path": str(scratch / "result.json"), "receipt_path": str(receipt_path), "receipt_sha256": digest}
    card, packet = scratch / "card.md", scratch / "packet.md"
    card.write_text(CARD, encoding="utf-8")
    packet.write_text(packet_text(phase, item, receipt_path, digest), encoding="utf-8")
    prompt = scratch / "prompt.md"
    prompt.write_bytes(card.read_bytes() + packet.read_bytes() + b"--- job header ---\n" + json.dumps(header, indent=1).encode() + b"\n")
    state = {"schema": "ky.job/1", "job_id": job_id, "key": key, "item": item, "kind": "ARTIFACT", "role": E.get("KY_FINAL_ROLE", "reviewer"),
             "stream": "V", "slot": slot, "worktree": SOURCE, "branch": None, "base_sha": None, "head": None, "digest": digest,
             "verdict_phase": "artifact", "evidence_fp": None, "pr": None, "registered_head": None, "queue_authorised": False,
             "prerequisites": [], "test_digests": [], "migration_number": None, "loop": 1, "max_loops": 1,
             "model": E.get("KY_FINAL_MODEL", "claude-opus-5-5"), "effort": "high", "permission_mode": "default", "max_turns": 60,
             "deadline": header["deadline"], "claude_bin": E.get("CLAUDE_BIN", "/Users/Dev/.local/bin/claude"),
             "mcp_config": str(FLEET / "mcp.none.json"), "extra_lean_flags": [READ_ONLY], "disallowed_tools": DISALLOWED,
             "job_scratch": str(scratch), "prompt_path": str(prompt), "stdout_path": str(scratch / "stdout.jsonl"),
             "stderr_path": str(scratch / "stderr.log"), "tmp_path": str(scratch / "tmp"), "tests": [],
             "se_ephe_path": E.get("SE_EPHE_PATH"), "swe_ephe_path": E.get("SWE_EPHE_PATH"), "card_path": str(card),
             "packet_path": str(packet), "boundary": "verifier", "regen": None, "fixture": None, "locks": [], "controller_id": CTRL,
             "phase": "prepared", "pid": None, "pgid": None, "process_start": None, "provider_session_id": None, "claim_id": None,
             "renewed_at": None, "exit_code": None, "outcome": None, "result_path": None, "result_event": None, "checkpoint": None,
             "failure_fp": None, "attempt": 1, "requeued": False, "ended_at": None}
    save_state(state_path, state)
    try:
        with open(scratch / "kyjob.out", "wb") as out_f, open(scratch / "kyjob.err", "wb") as err_f:
            proc = subprocess.Popen(["/bin/bash", str(FLEET / "kyjob.sh"), job_id], cwd=KY_ROOT, env=reviewer_env(),
                                    stdin=subprocess.DEVNULL, stdout=out_f, stderr=err_f, start_new_session=True)
    except OSError as exc:
        state.update(phase="ended", outcome="failed", ended_at=kyaction.utc())
        save_state(state_path, state)
        return False, {"job_id": job_id, "error": "launch_failed:%s" % exc.errno}
    ident = kyaction.ps_identity(proc.pid)
    state.update(phase="live", pid=proc.pid, pgid=proc.pid, process_start=ident[1] if ident else None)
    save_state(state_path, state)
    timed_out = False
    while proc.poll() is None:
        if time.time() >= deadline_epoch:
            timed_out = True
            break
        time.sleep(max(0.01, min(POLL_S, 0.2)))
    if timed_out or not group_absent(proc.pid):
        group_gone = stop_started_group(proc)         # the deadline, or a child left behind in the reviewer's group
    else:
        group_gone = True
    rc = proc.returncode
    outcome = "timed_out" if timed_out else ("done" if rc == 0 else "failed")
    disk, _err = read_json(state_path)          # what the reviewer left, not our copy: a tampered stream must stay visible
    if not isinstance(disk, dict):
        return False, {"job_id": job_id, "error": "reviewer_state_unreadable_after_exit", "exit_code": rc}
    disk.update(phase="ended", exit_code=rc, outcome=outcome, ended_at=kyaction.utc(),
                provider_session_id=provider_session(scratch / "stdout.jsonl"),      # measured now, or null: never a default
                result_path=str(scratch / "result.json") if (scratch / "result.json").is_file() else None)
    save_state(state_path, disk)
    result = result_of(disk, slot, timed_out, group_gone, scratch)
    return rc == 0 and not timed_out and group_gone, result


def review_run(phase, item, receipt_path, claim_slot):
    """Snapshot, launch, bound and reap the reviewer under one kyaction record → (status, result, slot, digest)."""
    digest = sha_file(receipt_path)
    if not digest or not VSLOTS:
        return "failed", {"error": "receipt_unreadable_or_no_verifier_slot"}, None, digest
    slot = next((s for s in VSLOTS if s != claim_slot), VSLOTS[0])
    key = "finalize-%s-%s" % (phase, digest[:12])

    def observer(rec):
        states, bad = job_states()
        mine = [(p, s) for p, s in states if s.get("key") == key]
        if bad:
            return "unknown", {"error": "job_state_unreadable"}
        for p, s in mine:
            if s.get("phase") != "ended":
                if not identity_ok(s):
                    return "unknown", {"job_id": s.get("job_id"), "error": "identity_unknown"}
                g = group_state(s["pid"], s["pgid"], s["process_start"])
                if g != "gone":
                    return "unknown", {"job_id": s.get("job_id"), "group": g}
                s.update(phase="ended", outcome="interrupted", ended_at=kyaction.utc())
                save_state(p, s)
        for p, s in reversed(mine):
            if s.get("phase") == "ended" and s.get("outcome") == "done" and s.get("exit_code") == 0 and s.get("digest") == digest:
                return "done", result_of(s, s.get("slot"), False, True)
        return "not_done", {}

    status, result = act("FIN-review-%s-%s" % (phase, digest[:12]), "reviewer_launch",
                         {"item": item, "phase": phase, "receipt_path": str(receipt_path), "receipt_sha256": digest},
                         {"kind": "headless_reviewer", "stream": "V", "worktree": SOURCE},
                         "bounded stream-V reviewer exits and its process group is gone",
                         lambda: launch_reviewer(phase, item, receipt_path, digest, slot), observer)
    return status, result, (result.get("vslot") if isinstance(result, dict) and result.get("vslot") else slot), digest


def not_independent(state, job_id, scratch):
    """Why the reviewer is NOT proven independent of the receipt's author; [] only when its identity was measured and
    ties it to no one. The identity is the provider session its program reported in its own output stream (read again
    here, and equal to what this script recorded in the job state), compared with the finalizer's identities and with
    the session of every other recorded job (the jobs whose work the receipt covers, and the other review). A session
    that cannot be measured is not independent."""
    why = []
    authors = {AUTHOR_ID, CTRL, OWN_SESSION} | ({E["KY_SESSION_ID"]} if E.get("KY_SESSION_ID") else set())
    if job_id in authors or state.get("job_id") != job_id:
        why.append("reviewer_id")
    session = provider_session(Path(scratch) / "stdout.jsonl") if scratch else None
    if session is None:
        why.append("provider_session_unmeasured")
    else:
        if state.get("provider_session_id") != session:
            why.append("provider_session_differs_from_its_record")
        if session in authors:
            why.append("provider_session_is_the_authors")
        states, bad = job_states()
        if bad:
            why.append("other_job_states_unreadable")
        if session in {s.get("provider_session_id") for _p, s in states if s.get("job_id") != job_id}:
            why.append("provider_session_is_another_jobs")
    pid, pgid = state.get("pid"), state.get("pgid")
    if not posint(pid) or not posint(pgid):
        why.append("process_unrecorded")
    elif pgid == os.getpgrp() or kyaction.is_self_or_ancestor(pid) is not False:
        why.append("process_is_the_authors")
    return why


def review_publish(phase, item, receipt_path, res, digest, slot, claim_slot, external):
    """Every condition of §6's verdict publication, then kyverdicts.py publish → dict(accepted, reasons, ...)."""
    reasons, published, proposed = [], False, None
    job_id = res.get("job_id")
    state, _ = read_json(RUN / "jobs" / str(job_id) / "state.json") if job_id else (None, None)
    if not isinstance(state, dict):
        return {"accepted": False, "reasons": ["reviewer_state_unreadable"]}
    if sha_file(receipt_path) != digest:
        reasons.append("receipt_changed_after_review")
    if state.get("stream") != "V" or state.get("slot") not in VSLOTS or state.get("item") != item or state.get("key") != "finalize-%s-%s" % (phase, digest[:12]):
        reasons.append("reviewer_not_stream_v_or_not_this_review")
    dependent = not_independent(state, job_id, res.get("scratch"))
    if dependent:
        reasons.append("reviewer_not_independent(%s)" % "+".join(dependent))
    if res.get("exit_code") != 0 or res.get("timed_out") or res.get("group_gone") is not True:
        reasons.append("reviewer_did_not_exit_cleanly")
    if posint(state.get("pgid")):
        gone = (group_state(state["pid"], state["pgid"], state["process_start"]) == "gone") if state.get("process_start") else group_absent(state["pgid"])
        if not gone:
            reasons.append("reviewer_group_not_gone")
    else:
        reasons.append("reviewer_group_unknown")
    result_path = res.get("result_path")
    doc, _ = read_json(result_path) if result_path else (None, None)
    if not (isinstance(doc, dict) and doc.get("schema") == "ky.job_result/1" and doc.get("job_id") == job_id and doc.get("item") == item
            and doc.get("status") == "done" and isinstance(doc.get("proposed_verdict"), dict)
            and doc["proposed_verdict"].get("verdict") in ("ACCEPTED", "REJECTED")):
        reasons.append("reviewer_result_missing_or_not_this_job")
    else:
        proposed = doc["proposed_verdict"]["verdict"]
        if doc["proposed_verdict"].get("artifact_digest") != digest:       # §12: the reviewer accepts this exact digest, or nothing
            reasons.append("reviewer_verdict_not_on_this_digest")
    need_external = claim_slot is not None and slot == claim_slot
    ext_args = []
    if need_external:
        if not external or not os.path.isabs(external) or not sha_file(external):
            reasons.append("external_review_required_no_separate_verifier_lane")
        else:
            ext_args = ["--external-review-path", external, "--external-review-sha256", sha_file(external)]
    seen, observed = verdict_of(item, digest, job_id)
    if seen == "unknown":
        reasons.append("events_unreadable")
    if seen == "published":
        # a re-run: the tracker's latest verdict on this digest is already this job's. Its boundary was checked before
        # that publication and its view released since, so there is nothing to check again and nothing to publish.
        published = True
    else:
        boundary_path = Path(state["job_scratch"]) / "finalize.boundary.json"
        rc, out, err = run(["bash", FLEET / "kyboundary.sh", "check", job_id], timeout=900)
        boundary_path.write_text(out or "", encoding="utf-8")
        try:
            evidence = json.loads(out)
        except ValueError:
            evidence = None
        if rc != 0:
            reasons.append("boundary_%s" % ("unobservable" if rc is None else "exit_%s" % rc))
        elif not (isinstance(evidence, dict) and evidence.get("result") == "intact" and evidence.get("job_id") == job_id):
            reasons.append("boundary_evidence_not_this_jobs_intact_object")
    if not reasons and not published:
        env = dict(os.environ, KY_RUN=str(RUN), KY_BIN=KY, KY_GIT=GIT)
        argv = [sys.executable, FLEET / "kyverdicts.py", "publish", "--job-id", job_id, "--item", item, "--phase", "artifact",
                "--artifact-digest", digest, "--artifact-path", receipt_path, "--vslot", state["slot"], "--author-id", AUTHOR_ID,
                "--reviewer-id", job_id, "--worktree", SOURCE, "--snapshot", res.get("snapshot_path") or "", "--job-exit", "0",
                "--result", result_path, "--boundary", boundary_path, "--as", CTRL] + ext_args
        rc, out, err = run(argv, env=env, timeout=900)
        try:
            answer = json.loads((out or "").strip().splitlines()[-1])
        except (ValueError, IndexError):
            answer = None
        answer = answer if isinstance(answer, dict) else {}
        refusal = [r for r in answer.get("reasons") or [] if isinstance(r, str)] if isinstance(answer.get("reasons"), list) else []
        if not (rc == 0 and answer.get("published") is True):
            reasons.append("publish_%s" % ("unknown" if rc in (None, 3) else "refused") + (":" + ",".join(refusal) if refusal else ""))
        else:
            seen, observed = verdict_of(item, digest, job_id)      # the answer is a line of output; the verdict is the tracker's event
            published = seen == "published"
            if not published:
                reasons.append("verdict_event_not_observed(%s)" % seen)
    if published and observed != proposed:
        reasons.append("verdict_event_is_%s_proposal_is_%s" % (observed, proposed))
    rc, _, _ = run(["bash", FLEET / "kyboundary.sh", "release", job_id], timeout=900)
    view_released = rc == 0
    if not view_released:
        reasons.append("boundary_view_release_failed")
    return {"accepted": not reasons and published and observed == "ACCEPTED" and proposed == "ACCEPTED", "published": published,
            "proposed": proposed, "observed": observed, "reasons": reasons,
            "job_id": job_id, "vslot": state.get("slot"), "view_released": view_released}


# ───────────────────────────── the two phases ─────────────────────────────

def phase_drain():
    PHASE[0] = "drain"
    loops = {}
    for loop in LOOPS:
        rc, _, _ = run(["bash", FLEET / "kyctl.sh", "stop", loop], timeout=600)
        loops[loop] = "stopped" if rc == 0 else ("unknown" if rc is None else "not_stopped")
    signalling = all(v == "stopped" for v in loops.values())
    states, problems = job_states()
    problems = [dict(p) for p in problems]
    trees, bad_trees = owned_worktrees(states)
    problems += bad_trees
    jobs, job_result = [], {}
    for path, s in states:
        if s.get("phase") == "ended":             # the record is not the measurement: its group is measured, never signalled
            group = recorded_group(s)
            if group in ("none", "gone"):
                job_result[s.get("job_id")] = "ended"
                continue
            result, why = "busy_kept", "recorded_ended_but_group_%s" % group
        else:
            result, why = drain_one(path, s, signalling)
        entry = {k: s.get(k) for k in ("job_id", "item", "slot", "worktree", "pid", "pgid", "process_start", "deadline")}
        entry.update(phase=s.get("phase"), result=result, reason=why)
        jobs.append(entry)
        job_result[s.get("job_id")] = result
    busy = busy_worktrees(states, job_result)
    names = lane_names(trees)
    worktrees, lanes = [], {}
    for path in sorted(trees):
        state, why = worktree_state(path, busy)
        worktrees.append({"path": path, "state": state, "reason": why})
        lanes[names[path]] = state
    written = []
    for letter in "ABC":
        stop = Path(PRAVAHA_RUN) / ("RUNNER_STOP_" + letter)
        try:
            stop.touch()
        except OSError:
            pass
        written.append(stop.exists())
    pravaha = "frozen (RUNNER_STOP_{A,B,C} written)" if all(written) else "unknown: RUNNER_STOP_%s absent" % "".join(l for l, w in zip("ABC", written) if not w)
    jobs_ok = all(j["result"] in GONE_JOB for j in jobs)
    ok = signalling and jobs_ok and not problems and all(w["state"] in ("absent", "clean") for w in worktrees)
    extra = {"phase": "drain", "loops": loops, "jobs": jobs, "worktrees": worktrees, "problems": problems,
             "v1": "not a lane in v3: the independent reviewer is the finalizer-owned stream-V job (step 5)", "pravaha_writers": pravaha}
    c3_seen, c3 = done_event("C-3")
    frozen = c3.get("artifact_digest") if c3_seen == "done" else None
    doc, digest, wrote = receipt(DRAIN_PATH, "ky.drain_receipt/1", "ACCEPTED" if ok else "FAILED", lanes, extra, frozen_digest=frozen)
    say(DRAIN_PATH.read_text())
    if not wrote and frozen and sha_file(DRAIN_PATH) == frozen and not ok:
        say("DRAIN FAILED on the re-check after C-3 was completed — the accepted drain receipt is kept as it is")
        return 1, None
    if not ok:
        say("DRAIN FAILED — nothing further is removed; the final receipt is not written")
        return 1, None
    if doc.get("result") != "ACCEPTED":
        say("DRAIN receipt on disk is not ACCEPTED — stopping")
        return 1, None
    return 0, digest


def close_report():
    evs = events()
    for e in reversed(evs or []):
        if e.get("kind") == "item" and e.get("item") == "C-1" and e.get("state") == "done" and e.get("guarded") is True:
            c = e.get("completion") or {}
            path, digest = c.get("path"), c.get("artifact_digest")
            if isinstance(path, str) and os.path.isabs(path) and isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) \
                    and sha_file(path) == digest:
                return {"path": path, "sha256": digest}
            return None
    return None


def final_message(ok):
    if DRAFT_PATH.exists() and DRAFT_PATH.stat().st_size > 0:
        done = "all job groups stopped, their worktrees and test databases removed"
        final, _ = read_json(FINAL_PATH)          # KU-02: a preserved container is reported, not called removed
        try:
            kept = [k for k in final["absence_detail"]["databases"]["incompatible_containers_preserved"] if isinstance(k, str)]
        except (KeyError, TypeError):
            kept = []
        if kept:
            done += "; an incompatible pre-existing container preserved, not removed (reported by the close of: %s)" % ", ".join(kept)
        text = DRAFT_PATH.read_text() + "\n\n---\nPhysical shutdown (measured by the finalizer, not by an agent): %s. Receipt: %s\n" % (
            done if ok else "INCOMPLETE — see the receipt", FINAL_PATH)
        atomic_write(str(MESSAGE_PATH), text)


def phase_completed(c4):
    """C-4 is done: FINAL_RECEIPT.json is bound to the digest its guarded completion recorded (as the drain receipt is to
    C-3's) and is never rewritten; nothing is stopped, signalled, removed, claimed, reviewed or published again. An
    unfinished record of that completion is reconciled by observation. → 0 only when the receipt on disk is the bound one."""
    PHASE[0] = "completed"
    bound, on_disk = c4.get("artifact_digest"), sha_file(FINAL_PATH)
    if not (isinstance(bound, str) and bound) or on_disk != bound:
        say("C-4 is done on a FINAL_RECEIPT.json with sha256 %s, but the file now has %s — it is not rewritten; exit 1" % (bound, on_disk))
        return 1
    action_id = "FIN-ky-done-C-4-%s" % bound[:12]
    try:
        record = kyaction.peek(str(RUN), action_id)
        if record is not None and record.get("state") == "INTENDED":
            kyaction.reconcile(str(RUN), action_id, lambda rec: done_event("C-4", bound), by=CTRL)
    except kyaction.ActionError as exc:
        say("the record of the C-4 completion could not be reconciled (%s); C-4 is done on the bound receipt" % tail(str(exc), 200))
    final_message(True)
    say("C-4 is done on FINAL_RECEIPT.json (sha256 %s): the finalization is complete; nothing was changed" % bound)
    return 0


def phase_final(drain_digest):
    PHASE[0] = "final"
    base = {"phase": "final", "drain_sha256": drain_digest, "close_report": None, "absence": None, "absence_detail": None,
            "fleet_processes_remaining": None, "worktrees_remaining": None, "final_review_result": "pending: the independent close review runs after this receipt is written"}
    lanes = {}
    state = {"base": base, "lanes": lanes}

    def emit(result, **updates):
        state["base"] = dict(state["base"], **updates)
        doc, digest, _ = receipt(FINAL_PATH, "ky.final_receipt/1", result, state["lanes"], state["base"])
        say(FINAL_PATH.read_text())
        return digest

    def fail(step, reason, **updates):
        emit("FAILED", failed_step=step, reason=reason if isinstance(reason, str) else "; ".join(reason), **updates)
        final_message(False)
        return 1

    # step 5: the drain receipt's exact digest is accepted by an independent reviewer, then C-3 through the tracker's guard
    status, res, slot, digest = review_run("drain", "C-3", DRAIN_PATH, None)
    if status != "done":
        return fail("drain_review", "reviewer did not run to a clean exit: %s" % json.dumps(res, sort_keys=True)[:300])
    pub = review_publish("drain", "C-3", DRAIN_PATH, res, digest, slot, None, None)
    state["base"]["drain_review"] = {"job_id": res.get("job_id"), "vslot": pub.get("vslot"), "proposed": pub.get("proposed")}
    if not pub["accepted"]:
        return fail("drain_review", "no accepted verdict: %s (proposed %s)" % (",".join(pub["reasons"]) or "none", pub.get("proposed")))
    status, res = ky_done("C-3", DRAIN_PATH, digest)
    if status != "done":
        return fail("done_C-3", "ky done C-3 not observed: %s" % json.dumps(res, sort_keys=True)[:300])

    # step 6: remove clean + pushed worktrees, then the session databases
    states, problems = job_states()
    trees, bad_trees = owned_worktrees(states)
    removal = remove_worktrees(trees, busy_worktrees(states))
    names = lane_names(trees)
    state["lanes"].update({names[p]: removal[p][0] for p in removal})
    db_state, db_detail = db_close()
    sessions = [r["session"] for r in db_detail["sessions"]]

    # step 7: FINAL_RECEIPT from what is measured now
    proc_state, proc_detail = measure_processes()
    wt_state, wt_detail = measure_worktrees(trees)
    report = close_report()
    draft_ok = DRAFT_PATH.exists() and DRAFT_PATH.stat().st_size > 0
    reasons = ["worktree %s: %s%s" % (names[p], st, " (%s)" % why if why else "") for p, (st, why) in sorted(removal.items()) if st not in ("removed", "absent")]
    reasons += ["job states unreadable"] * bool(problems or bad_trees)
    reasons += ["%s not proven absent: %s" % (k, v) for k, v in (("processes", proc_state), ("worktrees", wt_state), ("databases", db_state)) if v != "absent"]
    reasons += ["close report (C-1) evidence missing or changed"] * (report is None)
    reasons += ["final message draft missing"] * (not draft_ok)
    absence = {"processes": proc_state, "worktrees": wt_state, "databases": db_state}
    detail = {"processes": proc_detail, "worktrees": wt_detail, "databases": db_detail}
    common = dict(close_report=report, absence=absence, absence_detail=detail, fleet_processes_remaining=len(proc_detail),
                  worktrees_remaining=" ".join(names[p] for p in wt_detail if p in names))
    if reasons:
        return fail("final_receipt", reasons, **common)
    final_digest = emit("ACCEPTED", **common)
    final_message(False)

    # step 8: C-4 is V-owned — a V claim, an independent close review outside ordinary dispatch, a recheck, the verdict, the release
    claim_slot = VSLOTS[0] if VSLOTS else None
    if not claim_slot:
        return fail("claim_C-4", "no verifier slot configured")
    tag, gen, claimed = final_digest[:12], 0, False
    while gen < 4 and not claimed:
        suffix = "" if gen == 0 else "-r%d" % gen
        status, cres = act("FIN-ky-claim-C-4-%s%s" % (tag, suffix), "ky_claim", {"item": "C-4", "worker": claim_slot, "receipt_sha256": final_digest},
                           {"verb": "claim", "item": "C-4", "worker": claim_slot}, "V claim on C-4 for the close review",
                           lambda: ky_effect(["claim", "C-4", "--worker", claim_slot, "--lease", "10800"], "V", claim_slot,
                                             lambda: observe_claim("C-4", claim_slot)),
                           lambda rec: observe_claim("C-4", claim_slot))
        if status != "done":
            return fail("claim_C-4", "no V claim on C-4: %s" % json.dumps(cres, sort_keys=True)[:300])
        claimed = observe_claim("C-4", claim_slot)[0] == "done"       # a DONE record of an earlier, since released claim is not a claim
        gen += 0 if claimed else 1
    if not claimed:
        return fail("claim_C-4", "the V claim on C-4 is not held")
    suffix = "" if gen == 0 else "-r%d" % gen
    claim_id = observe_claim("C-4", claim_slot)[1].get("claim_id")

    def abort(step, reason, **updates):
        act("FIN-ky-abort-release-C-4-%s%s" % (tag, suffix), "ky_release", {"item": "C-4", "worker": claim_slot, "claim_id": claim_id, "why": step},
            {"verb": "release", "item": "C-4", "worker": claim_slot}, "V claim on C-4 released without completion",
            lambda: ky_effect(["release"], "V", claim_slot, lambda: observe_release("C-4", claim_slot, claim_id)),
            lambda rec: observe_release("C-4", claim_slot, claim_id), confirm=True)
        return fail(step, reason, **updates)

    status, res, slot, digest = review_run("final", "C-4", FINAL_PATH, claim_slot)
    if status != "done" or digest != final_digest:
        return abort("close_review", "reviewer did not run to a clean exit: %s" % json.dumps(res, sort_keys=True)[:300])
    # after the reviewer has exited: process, worktree and database absence are measured again, independently of the receipt
    again_proc, again_proc_detail = measure_processes()
    states_now, _bad = job_states()
    trees_now, _bad_trees = owned_worktrees(states_now)       # a job state or a worktree that appeared since step 6 counts too
    again_wt, again_wt_detail = measure_worktrees(set(trees) | set(trees_now))
    again_db, again_db_detail = db_close(prior=sessions, recheck=True)
    now_absent = {"processes": again_proc, "worktrees": again_wt, "databases": again_db}
    recheck = dict(absence=now_absent, absence_detail={"processes": again_proc_detail, "worktrees": again_wt_detail, "databases": again_db_detail},
                   fleet_processes_remaining=len(again_proc_detail))
    if any(v != "absent" for v in now_absent.values()):
        return abort("close_review", "present or unproven at the recheck: %s — no verdict" % json.dumps(now_absent, sort_keys=True), **recheck)
    if sha_file(FINAL_PATH) != final_digest:
        return abort("close_review", "receipt changed after review — no verdict", **recheck)
    external = E.get("KY_C4_EXTERNAL_REVIEW") or None
    pub = review_publish("final", "C-4", FINAL_PATH, res, final_digest, slot, claim_slot, external)
    if not pub["accepted"]:
        reasons = ",".join(pub["reasons"]) or "none"
        if "external_review_required_no_separate_verifier_lane" in pub["reasons"]:
            reasons += " (external review required: a lone verifier slot has no separate lane)"
        return abort("close_review", "no accepted verdict: %s (proposed %s)" % (reasons, pub.get("proposed")), **recheck)
    status, rres = act("FIN-ky-release-C-4-%s%s" % (tag, suffix), "ky_release", {"item": "C-4", "worker": claim_slot, "claim_id": claim_id},
                       {"verb": "release", "item": "C-4", "worker": claim_slot}, "V claim on C-4 released",
                       lambda: ky_effect(["release"], "V", claim_slot, lambda: observe_release("C-4", claim_slot, claim_id)),
                       lambda rec: observe_release("C-4", claim_slot, claim_id), confirm=True)
    if status != "done":
        return fail("release_C-4", "the V claim on C-4 was not released: %s" % json.dumps(rres, sort_keys=True)[:300], **recheck)
    status, dres = ky_done("C-4", FINAL_PATH, final_digest)
    if status != "done":
        return fail("done_C-4", "ky done C-4 not observed: %s" % json.dumps(dres, sort_keys=True)[:300], **recheck)
    final_message(True)
    return 0


def main():
    if kyaction is None:
        PHASE[0] = "drain"
        atomic_write(str(DRAIN_PATH), json.dumps({"schema": "ky.drain_receipt/1", "ts": now_iso(), "result": "FAILED", "lanes": {},
                     "branches": "kept", "campaign_worktree": "kept", "phase": "drain", "problems": ["kyaction unavailable: " + KYACTION_ERROR]}, indent=1) + "\n")
        say("DRAIN FAILED — kyaction.py (the process-identity rule) cannot be imported from %s" % FLEET)
        return 1
    c4_seen, c4 = done_event("C-4")
    if c4_seen == "unknown":
        PHASE[0] = "completed"                    # whether FINAL is bound to a completion cannot be told: write nothing
        say("EVENTS.jsonl is unreadable: whether C-4 is done cannot be observed — nothing is run or rewritten")
        return 1
    if c4_seen == "done":
        return phase_completed(c4)
    rc, digest = phase_drain()
    if rc:
        return rc
    return phase_final(digest)


if __name__ == "__main__":
    try:
        code = main()
    except Exception as exc:      # unknown is FAILED: record it in the receipt of the phase that was running
        traceback.print_exc()
        try:
            if PHASE[0] == "completed":
                raise RuntimeError("C-4 is done or cannot be observed: no receipt is rewritten")
            target = DRAIN_PATH if PHASE[0] in ("start", "drain") else FINAL_PATH
            atomic_write(str(target), json.dumps({"schema": "ky.%s_receipt/1" % ("drain" if target == DRAIN_PATH else "final"),
                         "ts": now_iso(), "result": "FAILED", "lanes": {}, "branches": "kept", "campaign_worktree": "kept",
                         "phase": PHASE[0], "failed_step": "internal_error", "reason": "%s: %s" % (type(exc).__name__, tail(str(exc), 200))}, indent=1) + "\n")
        except Exception:
            pass
        code = 1
    if PASSED_OVER[0]:
        say("EVENTS.jsonl: %d line%s the tracker's reader refuses (pravaha_tracker/events.py validate) — not events, passed over"
            % (PASSED_OVER[0], "" if PASSED_OVER[0] == 1 else "s"))
    sys.exit(code)
PYEOF

exec "$PY" -I -c "$PYLIB"
