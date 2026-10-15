# Source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/launchers/cockpit/kyfinish.py
# Original sha256: a744b32b784faec24dd8968faf4f43f21692b54413a9fe90de767bb2ed9344fe; date: 2026-10-14
#!/usr/bin/env python3
"""The launcher's commit for a Codex build or fix (cockpit ruling E7: prevent, not detect).

A Codex BUILDER has no write access to any git directory and no network. It leaves its changes in the item's working
copy and writes result.json with status, tests and `commit_message`. finish(job_id) is what the launcher then does
OUTSIDE the sandbox, in this order, stopping at the first thing that is not as it must be:

  1. the job is over (state.json: phase ended, exit 0, no guard failure; and where kyboot.py wrote
     `awaiting_launcher_commit`, it is true) and its result.json is this job's, status done;
  2. the working copy's .git pointer is byte for byte the one recorded at launch (read as a file, before any git runs);
  3. the engine's git guard again (kyboot.codex_guards, compared with the fleet's own rule), once more after 2 s if
     it differs, against the record taken before the job;
  4. the working copy is on the launch's branch at the launch's HEAD;
  5. something changed, and — when the packet front matter lists `d1_paths` — every changed path is one of them;
     the packet file itself must still have the bytes the launch hashed;
  6. `git add -A -- .` in the working copy, then `git commit -F <file>`: the message is result.json's
     commit_message plus the TRAILER, written to a file. It never passes through a shell and never appears in an
     argument list;
  7. `git push origin refs/heads/<branch>:refs/heads/<branch>` — no force, no other branch — and origin must then
     hold the commit;
  8. `gh pr list` for the branch; only if no open pull request exists, `gh pr create --base main` with the body
     from a file (the title is the launcher's own: item, kind and job id — see PR_TITLE);
  9. result.json (head_sha, pr_number) and state.json get `launcher_commit` {committed_by, head_sha, pr_number, at, …}.

It never merges, never enables auto-merge, never pushes another branch. If a step fails the job is marked
`launcher_commit_failed` {step, reason, at} in state.json and the working tree is left as the builder left it (a
failed commit is unstaged again; a commit that was made but not pushed is kept, and the next run resumes at the
push). A second run after success changes nothing and says so.

What the launch must have recorded (b1/launch_build.py does, for every Codex build): <job folder>/launch_git.json.
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import kyengine  # noqa: E402

TRAILER = "Co-Authored-By: GPT-6.1-Sol (Codex) <[REDACTED_EMAIL]>"     # the one place the builder is credited
COMMITTED_BY = "cockpit-launcher"
PLAN = "launch_git.json"
PLAN_SCHEMA = "ky.launcher_commit_plan/1"
WORK = "launcher_commit"                                                  # folder in the job folder: message, PR body
GIT = "/usr/bin/git"
DEFAULT_GH = "/opt/homebrew/bin/gh"
REMOTE, PR_BASE = "origin", "main"
PR_TITLE = "%(item)s: Codex %(kind)s (job %(job_id)s)"                    # launcher-owned words only; no job text
PATHS_KEY = "d1_paths"                                                    # packet front matter: the enumerated paths
MESSAGE_MAX = 20000
GUARD_RETRY_SECONDS = 2.0
JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
ITEM = re.compile(r"^KV3-B-[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
HEX40 = re.compile(r"^[0-9a-f]{40}\Z")
EXIT_OK, EXIT_FAILED, EXIT_SKIPPED = 0, 3, 4


class Stop(Exception):
    """a step is not as it must be: the job is marked launcher_commit_failed"""

    def __init__(self, step, reason):
        super().__init__(reason)
        self.step, self.reason = step, reason


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def jload(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def wj(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def tool_env():
    """the whole environment of git and gh: no GIT_* redirection, no token variable, never the caller's"""
    return {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": kyengine.HOME, "USER": kyengine.USER, "LANG": "en_US.UTF-8"}


def gh_program():
    """/opt/homebrew/bin/gh; in the tests' sandbox only, KY_GH beneath the sandbox (and nothing else)"""
    if kyengine.SANDBOX is None:
        return DEFAULT_GH
    program = os.environ.get("KY_GH") or ""
    if not program.startswith(kyengine.SANDBOX + "/"):
        raise Stop("pull_request", "KY_LAUNCHERS_SANDBOX is set (a test run) and KY_GH is not a program beneath it")
    return program


def git(wt, *args):
    """(exit, stdout, stderr) of git in the working copy; an argument list, never a shell"""
    done = subprocess.run([GIT, "-C", wt] + list(args), capture_output=True, env=tool_env(), stdin=subprocess.DEVNULL)
    return done.returncode, done.stdout.decode("utf-8", "replace"), done.stderr.decode("utf-8", "replace").strip()


def need(step, wt, *args):
    code, out, err = git(wt, *args)
    if code != 0:
        raise Stop(step, "git %s failed (exit %d): %s" % (args[0], code, err[-400:]))
    return out


def job_dir(job_id):
    return os.path.join(os.path.realpath(kyengine.KY_SCRATCH), "jobs", job_id)


def state_path(job_id):
    return os.path.join(kyengine.KY_RUN, "jobs", job_id, "state.json")


def pointer_sha(wt):
    """sha256 of the working copy's .git pointer FILE, read without git; None when it is not a regular file"""
    path = os.path.join(wt, ".git")
    if os.path.islink(path) or not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return sha_bytes(f.read())


def record_launch(folder, job_id, item, kind, wt, branch, packet_path, packet_sha256):
    """written when a Codex build is prepared: what the finisher holds the working copy to after the job"""
    code, head, err = git(wt, "rev-parse", "HEAD")
    code2, gitdir, err2 = git(wt, "rev-parse", "--absolute-git-dir")
    if code != 0 or code2 != 0 or pointer_sha(wt) is None:
        sys.exit("the item's working copy cannot be recorded for the launcher's commit (it must be a linked working "
                 "copy with a .git pointer file): " + (err or err2 or "no .git pointer file"))
    wj(os.path.join(folder, PLAN), {"schema": PLAN_SCHEMA, "job_id": job_id, "item": item, "kind": kind, "worktree": wt,
                                   "branch": branch, "head": head.strip(), "git_dir": gitdir.strip(),
                                   "dot_git_sha256": pointer_sha(wt), "packet_path": packet_path,
                                   "packet_sha256": packet_sha256, "recorded_at": utc()})


def is_launcher_commit_job(job_id):
    """a job the launcher commits for: its folder holds the launch record"""
    return os.path.isfile(os.path.join(job_dir(job_id), PLAN))


def changed_paths(wt):
    """every path `git add -A` would stage, from `git status --porcelain=v1 -z` (untracked files one by one)"""
    out = need("changes", wt, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    paths, parts, i = [], out.split("\0"), 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        paths.append(entry[3:])
        if entry[0] in "RC" or entry[1] in "RC":           # a rename or copy carries its other path in the next field
            if i < len(parts) and parts[i]:
                paths.append(parts[i])
            i += 1
    return sorted(set(paths))


def packet_paths(packet_path):
    """(the packet's enumerated paths, None) or (None, why they are not machine-readable)"""
    try:
        text = open(packet_path, encoding="utf-8").read()
        front = json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0])
    except (OSError, ValueError, IndexError) as bad:
        return None, "the packet has no readable JSON front matter (%s)" % type(bad).__name__
    paths = front.get(PATHS_KEY) if isinstance(front, dict) else None
    if not isinstance(paths, list) or not paths or not all(isinstance(p, str) and p and not p.startswith("/") for p in paths):
        return None, "the packet front matter has no %s list of relative paths" % PATHS_KEY
    return paths, None


def allowed(path, paths):
    """exact file paths; an entry ending in "/" names a folder and everything beneath it"""
    return any(path == p or (p.endswith("/") and path.startswith(p)) for p in paths)


def commit_message(result):
    message = result.get("commit_message")
    if not isinstance(message, str) or not message.strip():
        raise Stop("message", "result.json has no commit_message (a non-empty string)")
    if "\0" in message or len(message) > MESSAGE_MAX:
        raise Stop("message", "commit_message holds a NUL or is longer than %d characters" % MESSAGE_MAX)
    message = message.strip("\n").rstrip()
    if TRAILER not in message.splitlines():
        message += "\n\n" + TRAILER
    return message + "\n"


def remote_head(wt, branch, step):
    out = need(step, wt, "ls-remote", REMOTE, "refs/heads/" + branch)
    return out.split("\t")[0].strip() if out.strip() else None


def open_pull_request(wt, branch):
    """the number of the open pull request of this branch into PR_BASE, or None"""
    done = subprocess.run([gh_program(), "pr", "list", "--head", branch, "--base", PR_BASE, "--state", "open", "--json",
                           "number,headRefName", "--limit", "20"], capture_output=True, text=True, env=tool_env(), cwd=wt,
                          stdin=subprocess.DEVNULL)
    if done.returncode != 0:
        raise Stop("pull_request", "gh pr list failed (exit %d): %s" % (done.returncode, done.stderr.strip()[-400:]))
    try:
        rows = json.loads(done.stdout or "[]")
    except ValueError:
        raise Stop("pull_request", "gh pr list did not print JSON")
    numbers = [r.get("number") for r in rows if isinstance(r, dict) and r.get("headRefName", branch) == branch
               and isinstance(r.get("number"), int) and not isinstance(r.get("number"), bool)]
    return numbers[0] if numbers else None


def guards_hold(boot, wt, before):
    """[] when the engine's guards are what they were before the job; the differences otherwise"""
    def differences():
        after = kyengine.guards(boot, wt, False)
        return kyengine.guard_failures({"git": before.get("git")}, after, boot)
    found = differences()
    if found:
        time.sleep(GUARD_RETRY_SECONDS)                    # ruling E2: once more, to rule out a mid-write read
        found = differences()
    return found


def mark(job_id, key, value, drop=()):
    path = state_path(job_id)
    state = jload(path)
    if not isinstance(state, dict):
        return False
    for name in drop:
        state.pop(name, None)
    state[key] = value
    wj(path, state)
    return True


def finish(job_id, check_only=False):
    """(exit status, what was done) — see the module documentation"""
    try:
        return _finish(job_id, check_only)
    except Stop as stop:
        failure = {"step": stop.step, "reason": stop.reason, "at": utc()}
        recorded = (not check_only) and JOB_ID.match(job_id or "") is not None and mark(job_id, "launcher_commit_failed", failure)
        return EXIT_FAILED, {"job_id": job_id, "outcome": "launcher_commit_failed", "recorded_in_state": bool(recorded), **failure}


def _finish(job_id, check_only):
    if not JOB_ID.match(job_id or ""):
        raise Stop("records", "not a job id")
    folder = job_dir(job_id)
    plan = jload(os.path.join(folder, PLAN))
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA or plan.get("job_id") != job_id:
        raise Stop("records", "no %s of this job in %s: not a job the launcher commits for" % (PLAN, folder))
    item, branch, wt, kind = plan.get("item"), plan.get("branch"), plan.get("worktree"), str(plan.get("kind") or "BUILD")
    if not (isinstance(item, str) and ITEM.match(item)) or branch != "kalayantra/" + str(item).lower() or branch == PR_BASE:
        raise Stop("records", "the launch record's item and branch are not an item branch")
    if not isinstance(wt, str) or os.path.realpath(wt) != wt or not wt.startswith(kyengine.WT_ROOT + "/") or not os.path.isdir(wt):
        raise Stop("records", "the launch record's working copy is not an existing folder beneath %s" % kyengine.WT_ROOT)
    state = jload(state_path(job_id))
    result = jload(os.path.join(folder, "result.json"))
    if not isinstance(state, dict):
        raise Stop("records", "no readable state.json of the job")
    if state.get("phase") != "ended" or state.get("exit_code") != 0 or state.get("guard_failures") or state.get("job_failed"):
        raise Stop("records", "the job is not over cleanly: phase %r, exit %r, guard failures %r"
                   % (state.get("phase"), state.get("exit_code"), state.get("guard_failures")))
    if "awaiting_launcher_commit" in state and state["awaiting_launcher_commit"] is not True and "launcher_commit" not in state:
        raise Stop("records", "the supervisor's state.json says awaiting_launcher_commit %r: it did not hand this job "
                   "over for a commit" % (state["awaiting_launcher_commit"],))
    if not isinstance(result, dict) or result.get("job_id") not in (None, job_id) or result.get("item") not in (None, item):
        raise Stop("records", "no readable result.json of this job and item")
    # ---- already done: say so and change nothing
    done = state.get("launcher_commit")
    if isinstance(done, dict):
        head = need("records", wt, "rev-parse", "HEAD").strip()
        if done.get("head_sha") != head or remote_head(wt, branch, "records") != head:
            raise Stop("records", "state.json says the launcher committed %r, but the working copy or origin is elsewhere"
                       % done.get("head_sha"))
        return EXIT_OK, {"job_id": job_id, "outcome": "already_committed", "launcher_commit": done}
    if result.get("status") != "done":
        note = {"reason": "the builder's status is %r: nothing is committed" % result.get("status"), "at": utc()}
        if not check_only:
            mark(job_id, "launcher_commit_skipped", note)
        return EXIT_SKIPPED, {"job_id": job_id, "outcome": "skipped", **note}
    # ---- the working copy's git identity, before any git command runs in it
    if pointer_sha(wt) is None or pointer_sha(wt) != plan.get("dot_git_sha256"):
        raise Stop("guards", "the working copy's .git pointer is not the file recorded at launch")
    if need("guards", wt, "rev-parse", "--absolute-git-dir").strip() != plan.get("git_dir"):
        raise Stop("guards", "the working copy's git directory is not the one recorded at launch")
    before = (state.get("guards") or {}).get("before") if isinstance(state.get("guards"), dict) else None
    if not isinstance(before, dict) or before.get("git") is None:
        raise Stop("guards", "state.json holds no git guard taken before the job: nothing to compare with")
    boot = kyengine.kyboot()
    differences = guards_hold(boot, wt, before)
    if differences:
        raise Stop("guards", "; ".join(differences))
    # ---- branch and HEAD of the launch (or the commit a previous run made and could not push)
    if need("head", wt, "rev-parse", "--abbrev-ref", "HEAD").strip() != branch:
        raise Stop("head", "the working copy is not on %s" % branch)
    head = need("head", wt, "rev-parse", "HEAD").strip()
    work = os.path.join(folder, WORK)
    progress = jload(os.path.join(work, "progress.json")) or {}
    resumed = head != plan.get("head")
    if resumed:
        parent = git(wt, "rev-parse", "HEAD^")[1].strip()
        if not (progress.get("commit") == head and parent == plan.get("head") and not changed_paths(wt)):
            raise Stop("head", "the working copy's HEAD %s is not the launch's %s (and not a commit this launcher made)"
                       % (head, plan.get("head")))
        changed, checked = progress.get("paths") or [], progress.get("paths_checked")
    else:
        if sha_bytes(open(plan["packet_path"], "rb").read()) != plan.get("packet_sha256"):
            raise Stop("paths", "the packet file in the working copy no longer has the bytes the launch hashed")
        changed = changed_paths(wt)
        if not changed:
            raise Stop("changes", "the builder reports status done, and nothing changed in the working copy")
        paths, why_not = packet_paths(plan["packet_path"])
        checked = paths is not None
        outside = [p for p in changed if not allowed(p, paths)] if checked else []
        if outside:
            raise Stop("paths", "changed path(s) outside the packet's %s: %s" % (PATHS_KEY, ", ".join(outside[:40])))
    message = commit_message(result)
    if check_only:
        return EXIT_OK, {"job_id": job_id, "outcome": "would_commit" if not resumed else "would_resume_at_push",
                         "branch": branch, "changed": changed, "paths_checked": checked, "message_sha256": sha_bytes(message.encode())}
    os.makedirs(work, exist_ok=True)
    if not resumed:
        message_file = os.path.join(work, "COMMIT_MSG")
        with open(message_file, "w", encoding="utf-8") as f:
            f.write(message)
        need("stage", wt, "add", "-A", "--", ".")
        staged = sorted(p for p in need("stage", wt, "diff", "--cached", "--name-only", "-z").split("\0") if p)
        if not staged or (checked and [p for p in staged if not allowed(p, paths)]):
            git(wt, "reset", "-q")
            raise Stop("stage", "what was staged is not what was checked: %s" % ", ".join(staged[:40]))
        code, _out, err = git(wt, "commit", "-q", "--cleanup=whitespace", "-F", message_file)
        if code != 0:
            git(wt, "reset", "-q")                         # unstage: the working tree is as the builder left it
            raise Stop("commit", "git commit failed (exit %d): %s" % (code, err[-400:]))
        head = need("commit", wt, "rev-parse", "HEAD").strip()
        wj(os.path.join(work, "progress.json"), {"commit": head, "parent": plan["head"], "paths": changed,
                                                 "paths_checked": checked, "at": utc()})
    if not HEX40.match(head):
        raise Stop("commit", "the commit's id cannot be read")
    code, _out, err = git(wt, "push", REMOTE, "refs/heads/%s:refs/heads/%s" % (branch, branch))
    if code != 0:
        raise Stop("push", "git push of %s was refused (exit %d); the commit %s is kept in the working copy: %s"
                   % (branch, code, head, err[-400:]))
    if remote_head(wt, branch, "push") != head:
        raise Stop("push", "origin does not hold %s on %s after the push" % (head, branch))
    number = open_pull_request(wt, branch)
    how = "existing"
    if number is None:
        body_file = os.path.join(work, "PR_BODY.md")
        with open(body_file, "w", encoding="utf-8") as f:
            f.write(message + "\n---\nCommitted and pushed by the cockpit launcher for Codex job %s (cockpit ruling E7); "
                    "the builder had no git write access and no network. Held: not merged by this wave.\n" % job_id)
        title = PR_TITLE % {"item": item, "kind": kind.lower(), "job_id": job_id}
        done = subprocess.run([gh_program(), "pr", "create", "--base", PR_BASE, "--head", branch, "--title", title,
                               "--body-file", body_file], capture_output=True, text=True, env=tool_env(), cwd=wt,
                              stdin=subprocess.DEVNULL)
        if done.returncode != 0:
            raise Stop("pull_request", "gh pr create failed (exit %d): %s" % (done.returncode, done.stderr.strip()[-400:]))
        number, how = open_pull_request(wt, branch), "created"
        if number is None:
            raise Stop("pull_request", "gh pr create exited 0 but no open pull request of %s is listed" % branch)
    record = {"committed_by": COMMITTED_BY, "head_sha": head, "pr_number": number, "at": utc(), "parent": plan["head"],
              "branch": branch, "paths": changed, "paths_checked": bool(checked), "pull_request": how, "trailer": TRAILER,
              "qualification": state.get("qualification"), "launcher": state.get("launcher"), "sandbox": state.get("sandbox")}
    if not checked:
        record["paths_note"] = "the packet's paths are not machine-readable; changed paths were not held to them"
    result_path = os.path.join(folder, "result.json")
    keep = os.path.join(folder, "result.builder.json")
    if not os.path.exists(keep):                           # the builder's own bytes are kept beside the result
        with open(result_path, "rb") as src, open(keep, "wb") as dst:
            dst.write(src.read())
    wj(result_path, dict(result, branch=branch, head_sha=head, pr_number=number, launcher_commit=record,
                         qualification=state.get("qualification"), launcher=state.get("launcher"), sandbox=state.get("sandbox")))
    if not mark(job_id, "launcher_commit", record, drop=("launcher_commit_failed",)):
        raise Stop("records", "state.json could not be updated")
    return EXIT_OK, {"job_id": job_id, "outcome": "committed", "launcher_commit": record}


def reviewable(job_id, state, head, pushed):
    """[] or why a build the launcher commits for is not reviewable yet (review_build.py, pipeline.py)"""
    done = state.get("launcher_commit") if isinstance(state, dict) else None
    if not isinstance(done, dict):
        failed = (state or {}).get("launcher_commit_failed")
        return ["Codex build: the launcher has not committed it (%s); run b1/finish_build.py %s"
                % (("last attempt failed at %s: %s" % (failed.get("step"), failed.get("reason"))) if isinstance(failed, dict)
                   else "no launcher_commit in state.json", job_id)]
    if done.get("head_sha") != head or pushed != head:
        return ["Codex build: launcher_commit %r is not the working copy's head %s and the pushed head %r"
                % (done.get("head_sha"), head, pushed)]
    return []
