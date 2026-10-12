#!/bin/bash
# kyregen.sh — the REGEN job script of KĀLA-YANTRA v3 (relaunch plan v2.7 §6 REGEN row and inheritance predicate,
# §4a.1 action records, §8.9; packet KV3-B-KYREGEN).
#
#   kyregen.sh <job_id>
#
# A PR that is DIRTY/CONFLICTING only in declared generated outputs is brought up to its base without a model: merge
# the base, regenerate only the declared outputs with the pinned generator, run the applicable tests, record the
# hashes, push, and register `ky review <item> --detail "PR #<pr> @ <new head>"`. Whether the old verdict is
# inherited is NOT decided here: regen.json carries `inheritance: null`; the patch predicate (kyverdicts.inherits) is
# the dispatcher's and the tracker's, and undecided means VERIFY.
#
# Everything is read from $KY_RUN/jobs/<job_id>/state.json (every path absolute):
#   kind "REGEN" · item · stream · slot · worktree · branch · pr · registered_head · base_sha (the exact base commit
#   to merge, already fetched) · queue_authorised · regen {outputs[] (repository-relative files), generator {argv[],
#   path, sha256}, tests[] (argv lists)}
# Environment: KY_RUN, KY_FLEET (kyaction.py); KY_RUN_ID, KY_ROLE, KY_CONTROLLER_ID (the action records);
#   git = ${KY_GIT:-/usr/bin/git}; tracker CLI = ${KY_BIN:-$KY_ROOT/bin/ky}. Nothing has a built-in default root.
#
# Steps, in order. Any refusal before step 6 leaves the worktree clean at registered_head (observed, not assumed):
#   1  preconditions (else 73): queue_authorised is false; HEAD == registered_head; `git status --porcelain` is
#      empty and no merge is in progress; base_sha is a commit with a common ancestor that HEAD does not yet
#      contain; $KY_RUN/locks/item.<item>/owner.json names a LIVE owner that is this process or an ancestor (the
#      liveness rule is kyaction.process_matches itself; unknown refuses). The dispatcher holds the item lock;
#      kyregen takes none. sha256(generator.path) == generator.sha256, else 4.
#   2  git merge --no-commit --no-ff <base_sha>. Every unmerged path must be a declared output, and the merge must
#      leave nothing else behind; otherwise the merge is undone, exit 3.
#   3  the pin is checked again (the merge may have changed a generator that lives in the repository), then
#      generator.argv runs in the worktree and the declared outputs are staged. Exit 4 (merge undone) when the
#      generator fails, a conflicted output is still exactly what the merge left, HEAD moved, or anything but a
#      declared output changed beyond what the merge itself staged (modified, staged, deleted or untracked).
#   4  each tests[] argv runs in the worktree; a non-zero exit, or a test that changes the worktree: undone, exit 5.
#   5  queue_authorised is read once more (73 if it turned true), then the merge is committed:
#      "REGEN <item>: merge <base_sha>, regenerate declared outputs". New head = HEAD.
#   6  push, never forced, inside the action record JOB-$KY_RUN_ID-push (kind git_push, inputs {remote, ref,
#      commit}) through the kyaction.py job verbs: `begin` (any exit but 0: do not push), `git push origin
#      HEAD:refs/heads/<branch>`, then `complete` only when `git ls-remote origin refs/heads/<branch>` shows the new
#      head, `fail` when it shows anything else. A remote that cannot be read is unknown: the record stays INTENDED.
#   7  register inside the action record JOB-$KY_RUN_ID-review (kind tracker_event):
#      KY_STREAM=<stream> KY_LANE=<slot> ky review <item> --detail "PR #<pr> @ <new head>"; exit 0: `complete`;
#      non-zero: `fail`; no exit status observed: the record stays INTENDED.
#   8  once step 5 is done — first with pushed/review_registered null, again after steps 6 and 7 —
#      $KY_RUN/jobs/<job_id>/regen.json is written (temp + rename):
#      {"schema": "ky.regen/1", "job_id", "item", "pr", "old_head", "new_head", "old_base" (merge-base of the old
#       head and base_sha), "new_base" (base_sha), "conflicted_paths", "outputs": [{"path", "sha256_before",
#       "sha256_after"}], "generator": {"argv", "sha256"}, "tests": [{"argv", "exit"}], "pushed",
#       "review_registered", "inheritance": null}
#      sha256_* is null where the output did not exist. pushed: true/false only from the observed remote head.
#      review_registered: true/false only from the exit status of `ky`. null: not observed (not attempted, or unknown).
#
# A re-run finds regen.json for the same registered_head first and repeats nothing: pushed and registered → 0;
# otherwise 6, until both action records of this run are DONE for that new head (then 0; regen.json stays the first
# run's own observation). An unreadable regen.json is 6. regen.json of another registered_head is replaced.
#
# Exit: 0   pushed and registered
#       3   conflict outside the declared outputs
#       4   generator pin, generator failure, or the generator wrote elsewhere
#       5   tests failed
#       6   push or registration failed or unknown (the action record stays for reconciliation; nothing is retried)
#       64  usage, environment or invalid state
#       70  stopped by a signal or an unexpected failure before step 6; stderr says whether the worktree could be
#           put back (if it could not, it needs attention before any further job on this item)
#       73  precondition
# stdout: one line on exit 0. Diagnostics, and the output of the generator and the tests, go to stderr.
# Not cleaned up: files the generator or a test leaves that .gitignore hides, and directories they emptied.
set -euo pipefail

PY=/opt/homebrew/bin/python3
[ "$#" -eq 1 ] || { echo "usage: kyregen.sh <job_id>" >&2; exit 64; }
[ -x "$PY" ] || { echo "kyregen: $PY is not executable" >&2; exit 64; }

exec "$PY" -I -B - "$1" <<'PYEOF'
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys

PROG = "kyregen"
SCHEMA = "ky.regen/1"
OK, CONFLICT, GENERATOR, TESTS, PUBLISH, USAGE, INTERNAL, PRECONDITION = 0, 3, 4, 5, 6, 64, 70, 73
HEX40 = re.compile(r"^[0-9a-f]{40}\Z")
HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
JOB_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
ITEM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z")
BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}\Z")
REMOTE = "origin"
LOCAL_TIMEOUT_S = 600           # one local git command
NETWORK_TIMEOUT_S = 900         # git push / git ls-remote
VERB_TIMEOUT_S = 120            # one kyaction.py job verb, the tracker CLI
# what would point git at another repository than the worktree it is run in
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR",
                 "GIT_NAMESPACE", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX")


class Stop(Exception):
    """A refusal: exit `code` with one line on stderr."""

    def __init__(self, code, text):
        super().__init__(text)
        self.code, self.text = code, text


class Signalled(BaseException):
    pass


def say(text):
    sys.stderr.write("%s: %s\n" % (PROG, text))
    sys.stderr.flush()


def on_signal(signum, _frame):
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, signal.SIG_IGN)            # the clean-up that follows is not interrupted a second time
    raise Signalled(signal.Signals(signum).name)


def read_json(path):
    """(object, None) or (None, reason)."""
    try:
        with open(path, "rb") as f:
            return json.loads(f.read().decode("utf-8")), None
    except FileNotFoundError:
        return None, "absent"
    except (OSError, ValueError, RecursionError) as e:
        return None, "unreadable (%s)" % type(e).__name__


def write_json(path, obj):
    """temp + rename, in the same directory."""
    tmp = "%s.tmp.%d" % (path, os.getpid())
    try:
        with open(tmp, "wb") as f:
            f.write((json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def file_sha(path):
    """sha256 of a regular file · None when nothing is there · ValueError for a link, a directory or the like."""
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return None
    except NotADirectoryError:
        return None
    if not os.path.isfile(path) or os.path.islink(path) or st.st_nlink < 1:
        raise ValueError("%s is not a regular file" % path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def need(cond, text, code=USAGE):
    if not cond:
        raise Stop(code, text)


def is_argv(value):
    return isinstance(value, list) and len(value) > 0 and all(isinstance(a, str) and a and "\0" not in a for a in value)


def is_output(path):
    if not isinstance(path, str) or not path or "\0" in path or "\n" in path or path.startswith("/"):
        return False
    parts = path.split("/")
    return os.path.normpath(path) == path and not any(p in ("", ".", "..") or p.lower() == ".git" for p in parts)


class Regen:
    def __init__(self, job_id, environ):
        self.job_id = job_id
        self.stage = "before"                       # before → merging (step 2..5) → committed (step 5 done)
        self.pushed = self.review_registered = None
        self.new_head = self.old_base = None
        self.conflicted, self.tests_run, self.before, self.after = [], [], {}, {}
        self.generator_sha = None

        def absolute_dir(name):
            value = environ.get(name) or ""
            need(os.path.isabs(value) and os.path.isdir(value), "$%s must name an existing directory (absolute)" % name)
            return value

        self.run, self.fleet = absolute_dir("KY_RUN"), absolute_dir("KY_FLEET")
        self.kyaction_py = os.path.join(self.fleet, "kyaction.py")
        need(os.path.isfile(self.kyaction_py), "%s is not a file" % self.kyaction_py)
        self.run_id = environ.get("KY_RUN_ID") or ""
        need(RUN_ID_RE.match(self.run_id), "$KY_RUN_ID is unset or not a run id")
        for name in ("KY_ROLE", "KY_CONTROLLER_ID"):
            need(environ.get(name), "$%s is unset (the action records need it)" % name)
        self.git_bin = environ.get("KY_GIT") or "/usr/bin/git"
        need(os.path.isabs(self.git_bin) and os.access(self.git_bin, os.X_OK), "git (%s) is not an executable "
             "absolute path" % self.git_bin)
        self.ky_bin = environ.get("KY_BIN") or ""
        if not self.ky_bin:
            root = environ.get("KY_ROOT") or ""
            need(os.path.isabs(root), "neither $KY_BIN nor an absolute $KY_ROOT names the tracker CLI")
            self.ky_bin = os.path.join(root, "bin", "ky")
        need(os.path.isabs(self.ky_bin) and os.path.isfile(self.ky_bin) and os.access(self.ky_bin, os.X_OK),
             "the tracker CLI (%s) is not an executable absolute path" % self.ky_bin)
        self.child_env = {k: v for k, v in environ.items() if k not in GIT_REDIRECTS}
        self.git_env = dict(self.child_env, GIT_TERMINAL_PROMPT="0")
        self.push_id = "JOB-%s-push" % self.run_id
        self.review_id = "JOB-%s-review" % self.run_id
        self.job_dir = os.path.join(self.run, "jobs", job_id)
        self.state_path = os.path.join(self.job_dir, "state.json")
        self.regen_path = os.path.join(self.job_dir, "regen.json")
        self.load_state()

    # ─────────────────────────────── state.json ───────────────────────────────

    def read_state(self):
        state, err = read_json(self.state_path)
        need(err is None and isinstance(state, dict), "%s is %s" % (self.state_path, err or "not an object"))
        return state

    def load_state(self):
        s = self.read_state()
        need(s.get("kind") == "REGEN", "state.json: kind is not \"REGEN\"")
        need(s.get("job_id", self.job_id) == self.job_id, "state.json: job_id is not %s" % self.job_id)
        self.item, self.stream, self.slot = s.get("item"), s.get("stream"), s.get("slot")
        need(isinstance(self.item, str) and ITEM_RE.match(self.item), "state.json: item is not an item id")
        for name in ("stream", "slot"):
            need(isinstance(s.get(name), str) and s[name] and "\0" not in s[name], "state.json: %s is not a "
                 "non-empty string" % name)
        self.worktree = s.get("worktree")
        need(isinstance(self.worktree, str) and os.path.isabs(self.worktree) and os.path.isdir(self.worktree),
             "state.json: worktree is not an existing absolute directory")
        self.branch = s.get("branch")
        need(isinstance(self.branch, str) and BRANCH_RE.match(self.branch) and ".." not in self.branch,
             "state.json: branch is not a plain branch name")
        self.ref = "refs/heads/" + self.branch
        self.pr = s.get("pr")
        need(isinstance(self.pr, int) and not isinstance(self.pr, bool) and self.pr > 0, "state.json: pr is not a "
             "positive integer")
        self.old_head, self.base = s.get("registered_head"), s.get("base_sha")
        for name, value in (("registered_head", self.old_head), ("base_sha", self.base)):
            need(isinstance(value, str) and HEX40.match(value), "state.json: %s is not a 40-hex commit id" % name)
        self.queue_authorised = s.get("queue_authorised")
        need(isinstance(self.queue_authorised, bool), "state.json: queue_authorised is not true or false")
        regen = s.get("regen")
        need(isinstance(regen, dict), "state.json: regen is not an object")
        self.outputs = regen.get("outputs")
        need(isinstance(self.outputs, list) and self.outputs and all(is_output(p) for p in self.outputs)
             and len(set(self.outputs)) == len(self.outputs),
             "state.json: regen.outputs is not a non-empty list of distinct repository-relative file paths")
        generator = regen.get("generator")
        need(isinstance(generator, dict), "state.json: regen.generator is not an object")
        self.generator_argv, self.generator_path = generator.get("argv"), generator.get("path")
        self.generator_pin = generator.get("sha256")
        need(is_argv(self.generator_argv), "state.json: regen.generator.argv is not a non-empty list of strings")
        need(isinstance(self.generator_path, str) and os.path.isabs(self.generator_path),
             "state.json: regen.generator.path is not absolute")
        need(isinstance(self.generator_pin, str) and HEX64.match(self.generator_pin),
             "state.json: regen.generator.sha256 is not 64 lower-case hex digits")
        self.tests = regen.get("tests")
        need(isinstance(self.tests, list) and all(is_argv(t) for t in self.tests),
             "state.json: regen.tests is not a list of argv lists")
        for path in self.outputs:
            need(not os.path.isdir(os.path.join(self.worktree, path)) or os.path.islink(os.path.join(self.worktree, path)),
                 "state.json: declared output %s is a directory" % path)

    # ─────────────────────────────── processes ───────────────────────────────

    def git(self, *args, timeout=LOCAL_TIMEOUT_S):
        """(exit status or None when git could not be run or timed out, stdout, stderr)."""
        try:
            r = subprocess.run([self.git_bin] + list(args), cwd=self.worktree, env=self.git_env,
                               stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout)
        except (OSError, ValueError, subprocess.SubprocessError):
            return None, "", ""
        return r.returncode, os.fsdecode(r.stdout), os.fsdecode(r.stderr)

    def git_line(self, *args):
        rc, out, _ = self.git(*args)
        return out.strip() if rc == 0 else None

    def git_paths(self, *args):
        """The NUL-separated paths git prints, or None when it failed."""
        rc, out, _ = self.git(*args)
        return [p for p in out.split("\0") if p] if rc == 0 else None

    def in_worktree(self, argv):
        """Exit status of one generator or test command run in the worktree (its output goes to stderr)."""
        try:
            return subprocess.run(argv, cwd=self.worktree, env=self.child_env, stdin=subprocess.DEVNULL,
                                  stdout=sys.stderr, stderr=sys.stderr).returncode
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            say("%s could not be run (%s)" % (argv[0], type(e).__name__))
            return None

    def verb(self, verb, doc):
        """Exit status of one kyaction.py job verb (None: it could not be run)."""
        try:
            r = subprocess.run([sys.executable, "-I", "-B", self.kyaction_py, verb], env=self.child_env,
                               input=json.dumps(doc).encode("utf-8"), capture_output=True, timeout=VERB_TIMEOUT_S)
        except (OSError, ValueError, subprocess.SubprocessError):
            return None
        if r.returncode != 0:
            say("kyaction.py %s %s: exit %d %s" % (verb, doc.get("action_id"), r.returncode,
                                                   " ".join(os.fsdecode(r.stderr or r.stdout).split())[:300]))
        return r.returncode

    # ─────────────────────────────── a re-run ───────────────────────────────

    def record_done(self, action_id, kind, bound):
        record, err = read_json(os.path.join(self.run, "actions", action_id + ".json"))
        return (err is None and isinstance(record, dict) and record.get("action_id") == action_id
                and record.get("kind") == kind and record.get("state") == "DONE"
                and isinstance(record.get("inputs"), dict) and bound(record["inputs"]))

    def rerun(self):
        """None: no regen.json for this registered head (a first run). Otherwise the exit status; nothing is done."""
        if not os.path.lexists(self.regen_path):
            return None
        prev, err = read_json(self.regen_path)
        if err is not None or not isinstance(prev, dict) or prev.get("schema") != SCHEMA:
            raise Stop(PUBLISH, "%s exists and cannot be read: nothing is retried" % self.regen_path)
        if prev.get("old_head") != self.old_head:
            return None
        new = prev.get("new_head")
        if prev.get("pushed") is True and prev.get("review_registered") is True:
            say("%s: already pushed and registered at %s; nothing to do" % (self.item, new))
            return OK
        detail = self.detail(new)
        if isinstance(new, str) and HEX40.match(new) \
                and self.record_done(self.push_id, "git_push", lambda i: i.get("commit") == new and i.get("ref") == self.ref) \
                and self.record_done(self.review_id, "tracker_event", lambda i: i.get("detail") == detail):
            say("%s: both action records are settled DONE for %s; nothing to do" % (self.item, new))
            return OK
        raise Stop(PUBLISH, "%s: an earlier run stopped with pushed=%s review_registered=%s at %s; its action records "
                            "are not both settled DONE; nothing is retried"
                   % (self.item, json.dumps(prev.get("pushed")), json.dumps(prev.get("review_registered")), new))

    # ─────────────────────────────── step 1 ───────────────────────────────

    def pin_holds(self):
        try:
            self.generator_sha = file_sha(self.generator_path)
        except (OSError, ValueError):
            self.generator_sha = None
        return self.generator_sha is not None and self.generator_sha == self.generator_pin

    def clean_at_registered(self):
        """True only when observed: HEAD is the registered head, no merge is in progress, the status is empty."""
        if self.git_line("rev-parse", "--verify", "HEAD") != self.old_head:
            return False
        rc, _, _ = self.git("rev-parse", "-q", "--verify", "MERGE_HEAD")
        if rc != 1:                                 # 1 = there is none; 0 = a merge is in progress; else unknown
            return False
        rc, out, _ = self.git("status", "--porcelain")
        return rc == 0 and out == ""

    def item_lock_is_ours(self):
        """(True, None) or (False, why). The rule is kyaction's own: unknown refuses."""
        try:
            spec = importlib.util.spec_from_file_location("kyaction", self.kyaction_py)
            ka = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ka)
            owner, err = ka.lock_owner(self.run, "item." + self.item)
            if err:
                return False, "it has no readable owner record (%s)" % err
            alive = ka.process_matches(owner.get("pid"), owner.get("process_start"))
            if alive is not True:
                return False, "its owner (pid %r) is %s" % (owner.get("pid"), "gone" if alive is False else
                                                            "neither confirmed alive nor gone")
            ours = ka.is_self_or_ancestor(owner["pid"])
            if ours is not True:
                return False, "its owner (pid %r) is %s" % (owner["pid"], "another process, not an ancestor of this job"
                                                            if ours is False else "of unknown relation to this job")
            return True, None
        except Exception as e:                      # the lock could not be judged at all
            return False, "it could not be judged (%s)" % type(e).__name__

    def preconditions(self):
        top = self.git_line("rev-parse", "--show-toplevel")
        need(top is not None and os.path.realpath(top) == os.path.realpath(self.worktree),
             "state.json: worktree is not the top of a git worktree")
        rc, _, _ = self.git("check-ref-format", self.ref)
        need(rc == 0, "state.json: branch is not a valid branch name")
        need(self.queue_authorised is False, "%s: a queue authorisation is outstanding; nothing is pushed under it"
             % self.item, PRECONDITION)
        head = self.git_line("rev-parse", "--verify", "HEAD")
        need(head == self.old_head, "the worktree is at %s, not at the registered head %s" % (head, self.old_head),
             PRECONDITION)
        need(self.clean_at_registered(), "the worktree is not clean (git status --porcelain), or a merge is in "
             "progress", PRECONDITION)
        rc, _, _ = self.git("cat-file", "-e", self.base + "^{commit}")
        need(rc == 0, "base_sha %s is not a commit in the worktree's repository" % self.base, PRECONDITION)
        rc, _, _ = self.git("merge-base", "--is-ancestor", self.base, "HEAD")
        need(rc == 1, "base_sha %s is already contained in HEAD, or that cannot be told" % self.base, PRECONDITION)
        self.old_base = self.git_line("merge-base", self.old_head, self.base)
        need(self.old_base is not None and HEX40.match(self.old_base), "the registered head and base_sha have no "
             "merge base", PRECONDITION)
        ours, why = self.item_lock_is_ours()
        need(ours, "the item lock item.%s is not held for this job: %s" % (self.item, why), PRECONDITION)
        need(self.pin_holds(), "the generator %s is not the pinned one (sha256 %s, pin %s)"
             % (self.generator_path, self.generator_sha, self.generator_pin), GENERATOR)
        try:
            self.before = {p: file_sha(os.path.join(self.worktree, p)) for p in self.outputs}
        except (OSError, ValueError) as e:
            raise Stop(USAGE, "state.json: a declared output is not a file (%s)" % e)

    # ─────────────────────────────── steps 2–5 ───────────────────────────────

    def restore(self):
        """Undo the uncommitted merge and whatever the generator and the tests left. → True only when the worktree
        is then OBSERVED clean at the registered head. Step 1 saw no untracked file, so every one found now was
        made by this run."""
        self.git("merge", "--abort")
        if not self.clean_at_registered():
            self.git("reset", "--hard", self.old_head)
            for path in self.git_paths("ls-files", "--others", "--exclude-standard", "-z") or []:
                try:
                    os.unlink(os.path.join(self.worktree, path))
                except OSError:
                    pass
                parent = os.path.dirname(path)
                while parent:                       # a directory this file was alone in (rmdir refuses any other)
                    try:
                        os.rmdir(os.path.join(self.worktree, parent))
                    except OSError:
                        break
                    parent = os.path.dirname(parent)
        return self.clean_at_registered()

    def index_entries(self):
        """{path: [mode sha stage, …]} of every index entry outside the declared outputs, or None when unreadable."""
        rc, out, _ = self.git("ls-files", "-s", "-z")
        if rc != 0:
            return None
        entries = {}
        for entry in out.split("\0"):
            if entry:
                meta, _, path = entry.partition("\t")
                if path not in self.outputs:
                    entries.setdefault(path, []).append(meta)
        return entries

    def strays(self, staged):
        """What differs from the merge's own result outside the declared outputs: a list of reasons ([] = nothing).
        `staged` is index_entries() as the merge left it."""
        found = []
        if self.git_line("rev-parse", "--verify", "HEAD") != self.old_head:
            found.append("HEAD moved")
        if self.git_line("rev-parse", "-q", "--verify", "MERGE_HEAD") != self.base:
            found.append("the merge is no longer in progress")
        now = self.index_entries()
        if now is None or staged is None:
            found.append("the index cannot be read")
        else:
            found += ["staged: " + p for p in sorted(set(now) | set(staged)) if now.get(p) != staged.get(p)]
        modified = self.git_paths("diff", "--name-only", "-z")
        untracked = self.git_paths("ls-files", "--others", "--exclude-standard", "-z")
        if modified is None or untracked is None:
            found.append("the worktree cannot be compared")
        else:
            found += ["modified: " + p for p in sorted(set(modified))] + ["untracked: " + p for p in sorted(untracked)]
        return found

    def merge(self):
        self.stage = "merging"
        rc, _, err = self.git("merge", "--no-commit", "--no-ff", self.base)
        if self.git_line("rev-parse", "-q", "--verify", "MERGE_HEAD") != self.base:
            raise Stop(PRECONDITION, "git merge %s did not start (exit %s): %s" % (self.base, rc, " ".join(err.split())[:300]))
        unmerged = self.git_paths("ls-files", "-u", "-z")
        modified = self.git_paths("diff", "--name-only", "-z")
        untracked = self.git_paths("ls-files", "--others", "--exclude-standard", "-z")
        if unmerged is None or modified is None or untracked is None or rc not in (0, 1):
            raise Stop(INTERNAL, "the result of git merge (exit %s) cannot be read" % rc)
        self.conflicted = sorted({entry.partition("\t")[2] for entry in unmerged})
        outside = sorted(set(self.conflicted) - set(self.outputs))
        if outside:
            raise Stop(CONFLICT, "%s: conflict outside the declared outputs: %s" % (self.item, ", ".join(outside)))
        left = sorted((set(modified) - set(self.conflicted)) | set(untracked))
        if left:
            raise Stop(CONFLICT, "%s: the merge left paths outside its conflicts behind: %s" % (self.item, ", ".join(left)))
        if rc == 1 and not self.conflicted:
            raise Stop(INTERNAL, "git merge exited 1 without an unmerged path")

    def regenerate(self):
        staged = self.index_entries()
        try:
            as_merged = {p: file_sha(os.path.join(self.worktree, p)) for p in self.conflicted}
        except (OSError, ValueError) as e:
            raise Stop(CONFLICT, "%s: a conflicted output is not a file (%s)" % (self.item, e))
        if not self.pin_holds():
            raise Stop(GENERATOR, "after the merge the generator %s is not the pinned one (sha256 %s, pin %s)"
                       % (self.generator_path, self.generator_sha, self.generator_pin))
        rc = self.in_worktree(self.generator_argv)
        if rc != 0:
            raise Stop(GENERATOR, "%s: the generator exited %s" % (self.item, rc))
        try:
            self.after = {p: file_sha(os.path.join(self.worktree, p)) for p in self.outputs}
        except (OSError, ValueError) as e:
            raise Stop(GENERATOR, "%s: the generator left a declared output that is not a file (%s)" % (self.item, e))
        remaining = [p for p in self.conflicted if self.after[p] == as_merged[p]]
        if remaining:
            raise Stop(GENERATOR, "%s: the generator left a conflict in %s" % (self.item, ", ".join(remaining)))
        tracked = set(self.git_paths("ls-files", "-z", "--", *self.outputs) or [])
        present = [p for p in self.outputs if self.after[p] is not None or p in tracked]
        if present:
            rc, _, err = self.git("--literal-pathspecs", "add", "-A", "--", *present)
            if rc != 0:
                raise Stop(GENERATOR, "%s: the declared outputs could not be staged: %s" % (self.item, " ".join(err.split())[:300]))
        unmerged = self.git_paths("ls-files", "-u", "-z")
        if unmerged is None or unmerged:
            raise Stop(GENERATOR, "%s: a conflict remains after the generator" % self.item)
        found = self.strays(staged)
        if found:
            raise Stop(GENERATOR, "%s: the generator changed more than the declared outputs: %s"
                       % (self.item, "; ".join(found[:20])))
        return staged

    def run_tests(self, staged):
        for argv in self.tests:
            rc = self.in_worktree(argv)
            self.tests_run.append({"argv": argv, "exit": rc})
            if rc != 0:
                raise Stop(TESTS, "%s: test %s exited %s" % (self.item, json.dumps(argv), rc))
        try:
            unchanged = {p: file_sha(os.path.join(self.worktree, p)) for p in self.outputs} == self.after
        except (OSError, ValueError):
            unchanged = False
        found = self.strays(staged) + ([] if unchanged else ["a declared output"])
        if found:
            raise Stop(TESTS, "%s: the tests changed the worktree: %s" % (self.item, "; ".join(found[:20])))

    def commit(self):
        if self.read_state().get("queue_authorised") is not False:
            raise Stop(PRECONDITION, "%s: a queue authorisation appeared while regenerating; nothing is pushed under it"
                       % self.item)
        message = "REGEN %s: merge %s, regenerate declared outputs" % (self.item, self.base)
        rc, _, err = self.git("commit", "-q", "-m", message)
        new = self.git_line("rev-parse", "--verify", "HEAD")
        parents = (self.git_line("rev-list", "--parents", "-n", "1", "HEAD") or "").split()
        if rc != 0 or new is None or not HEX40.match(new) or parents != [new, self.old_head, self.base]:
            raise Stop(INTERNAL, "the merge could not be committed (exit %s): %s" % (rc, " ".join(err.split())[:300]))
        self.new_head, self.stage = new, "committed"

    # ─────────────────────────────── steps 6–8 ───────────────────────────────

    def detail(self, head):
        return "PR #%d @ %s" % (self.pr, head)

    def write_regen(self):
        write_json(self.regen_path, {
            "schema": SCHEMA, "job_id": self.job_id, "item": self.item, "pr": self.pr, "old_head": self.old_head,
            "new_head": self.new_head, "old_base": self.old_base, "new_base": self.base,
            "conflicted_paths": self.conflicted,
            "outputs": [{"path": p, "sha256_before": self.before[p], "sha256_after": self.after[p]} for p in self.outputs],
            "generator": {"argv": self.generator_argv, "sha256": self.generator_sha},
            "tests": self.tests_run, "pushed": self.pushed, "review_registered": self.review_registered,
            "inheritance": None})

    def push(self):
        target = {"item": self.item, "pr": self.pr, "branch": self.branch, "job_id": self.job_id}
        begun = self.verb("begin", {
            "action_id": self.push_id, "kind": "git_push",
            "inputs": {"remote": REMOTE, "ref": self.ref, "commit": self.new_head}, "target": target,
            "intended_transition": "%s/%s: %s -> %s" % (REMOTE, self.branch, self.old_head, self.new_head)})
        if begun != 0:
            say("%s: the push record %s was not begun by this run (exit %s): not pushing" % (self.item, self.push_id, begun))
            return
        push_rc, _, push_err = self.git("push", REMOTE, "HEAD:" + self.ref, timeout=NETWORK_TIMEOUT_S)
        rc, out, _ = self.git("ls-remote", REMOTE, self.ref, timeout=NETWORK_TIMEOUT_S)
        if rc != 0:
            say("%s: git push exited %s and the remote head cannot be read: unknown; %s stays for reconciliation"
                % (self.item, push_rc, self.push_id))
            return
        at = [parts[0] for parts in (line.split() for line in out.splitlines()) if len(parts) == 2 and parts[1] == self.ref]
        if at == [self.new_head]:
            self.pushed = True
            self.verb("complete", {"action_id": self.push_id, "result": {
                "remote": REMOTE, "ref": self.ref, "commit": self.new_head, "observed_by": "git ls-remote",
                "push_exit": push_rc}})
        else:
            self.pushed = False
            say("%s: not pushed (git push exit %s; %s is at %s): %s" % (self.item, push_rc, self.ref, at[0] if at else None,
                                                                         " ".join(push_err.split())[:300]))
            self.verb("fail", {"action_id": self.push_id, "result": {
                "remote": REMOTE, "ref": self.ref, "intended": self.new_head, "observed": at[0] if len(at) == 1 else None,
                "observed_by": "git ls-remote", "push_exit": push_rc}})

    def register(self):
        detail = self.detail(self.new_head)
        argv = [self.ky_bin, "review", self.item, "--detail", detail]
        begun = self.verb("begin", {
            "action_id": self.review_id, "kind": "tracker_event",
            "inputs": {"verb": "review", "item": self.item, "stream": self.stream, "lane": self.slot, "detail": detail},
            "target": {"item": self.item, "pr": self.pr, "head": self.new_head, "job_id": self.job_id},
            "intended_transition": "%s: review registered for PR #%d at %s" % (self.item, self.pr, self.new_head)})
        if begun != 0:
            say("%s: the review record %s was not begun by this run (exit %s): not registering"
                % (self.item, self.review_id, begun))
            return
        try:
            rc = subprocess.run(argv, cwd=self.worktree, env=dict(self.child_env, KY_STREAM=self.stream, KY_LANE=self.slot),
                                stdin=subprocess.DEVNULL, stdout=sys.stderr, stderr=sys.stderr,
                                timeout=VERB_TIMEOUT_S).returncode
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            say("%s: `ky review` gave no exit status (%s): unknown; %s stays for reconciliation"
                % (self.item, type(e).__name__, self.review_id))
            return
        self.review_registered = rc == 0
        self.verb("complete" if rc == 0 else "fail", {"action_id": self.review_id, "result": {
            "exit": rc, "detail": detail, "observed_by": "ky review exit status"}})
        if rc != 0:
            say("%s: `ky review` exited %d: not registered" % (self.item, rc))

    def publish(self):
        self.write_regen()                          # before the first side effect: a crash from here on reads as 6
        try:
            self.push()
            if self.pushed is True:
                self.register()
        finally:
            self.write_regen()
        if self.pushed is True and self.review_registered is True:
            print("%s: %s regenerated: PR #%d @ %s pushed and registered" % (PROG, self.item, self.pr, self.new_head))
            return OK
        raise Stop(PUBLISH, "%s: merged and regenerated at %s but pushed=%s review_registered=%s; nothing is retried"
                   % (self.item, self.new_head, json.dumps(self.pushed), json.dumps(self.review_registered)))

    def main(self):
        again = self.rerun()
        if again is not None:
            return again
        self.preconditions()
        self.merge()
        staged = self.regenerate()
        self.run_tests(staged)
        self.commit()
        return self.publish()


def main(argv):
    if len(argv) != 1 or not JOB_RE.match(argv[0]):
        say("usage: kyregen.sh <job_id>")
        return USAGE
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, on_signal)
    job = None
    try:
        job = Regen(argv[0], dict(os.environ))
        return job.main()
    except Stop as e:
        code, text = e.code, e.text
    except Signalled as e:
        code, text = INTERNAL, "stopped by %s" % e
    except Exception as e:                          # nothing below may leave a half-made merge behind unreported
        code, text = INTERNAL, "unexpected failure (%s: %s)" % (type(e).__name__, " ".join(str(e).split())[:300])
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, signal.SIG_IGN)
    if job is not None and job.stage == "merging":
        if job.restore():
            text += " [worktree clean at the registered head %s]" % job.old_head
        else:
            code = INTERNAL
            text += " [THE WORKTREE COULD NOT BE PUT BACK to the registered head %s: it needs attention]" % job.old_head
    elif job is not None and job.stage == "committed":
        if code != PUBLISH:                         # a signal or a failure after the commit: what is known is recorded
            try:
                job.write_regen()
            except Exception:
                text += " [regen.json could not be written]"
            code = PUBLISH
            text += " [after the merge commit %s; pushed=%s review_registered=%s]" % (
                job.new_head, json.dumps(job.pushed), json.dumps(job.review_registered))
    say(text)
    return code


sys.exit(main(sys.argv[1:]))
PYEOF
