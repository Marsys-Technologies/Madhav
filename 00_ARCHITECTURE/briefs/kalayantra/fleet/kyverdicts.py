#!/usr/bin/env python3
"""kyverdicts.py — controller-owned verdict publication and the ONE reviewed-patch inheritance predicate for
KĀLA-YANTRA v3 (relaunch plan v2.7 §6 "Verdict publication (controller-owned)" and "Inheritance predicate",
§4a.1 "Action records" / "Recovery"; KU-01, of whose fixtures this file owns "invalid inheritance fails").

A verifier job only PROPOSES a verdict in its result file. The controller publishes it — through `ky verdict`,
under a crash-safe action record — and only after it has itself observed that the reviewed tree is the one
proposed about: at the reviewed head, clean. An unmet requirement publishes nothing at all (not REJECTED either:
nothing was reviewed that a rejection could be about). Importing this module runs nothing.

Amendment A8 (2026-10-17): verdicts bind to the DIFF. The predicate compares `git patch-id --stable` of the two
reviewed patches and asks `git merge-tree` whether the new head still merges onto main; descent is not required
(a rebase of the same patch inherits). Publication observes six things (below); the pre-job snapshot, the
tracked-file hash set and the `kyboundary.sh check` evidence are no longer requirements (`--snapshot` and
`--boundary` are still accepted, for the callers of v2.7, and not read).

── Contract A: the predicate (one implementation; the dispatcher and the tracker both import it) ──────────────
    inherits(repo, old_head, new_head) -> bool            fail-closed: inheritance(…)["inherits"] is True
    inheritance(repo, old_head, new_head, *, old_base=None, new_base=None, timeout=60)
        -> {"inherits": bool, "reason", "old_head", "new_head", "old_base", "new_base", "patch_id"}  never raises
  A verdict at old_head still holds at new_head ("identical_patch") only if ALL of this is observed:
    * the four commits are 40-hex commits in `repo`; <main> = origin/main, else main, must exist ("unproven_base":
      without it there is no base to derive and nothing to merge onto); a base that is not given is
      `git merge-base <main> <head>` (no common ancestor or more than one: "unproven_base");
    * no base equals its head, given or derived ("unproven_base": a head main already contains derives itself as
      its base, and an empty comparison proves nothing);
    * each base is an ancestor of its head ("base_not_ancestor");
    * nothing binary changed on either side ("binary_change": "Binary files differ" says nothing about content);
    * the reviewed patch is not empty ("unproven_base");
    * patch_id(old_base, old_head) == patch_id(new_base, new_head) ("patch_differs" otherwise), where
      patch_id(b, h) = `git patch-id --stable` of `git diff --no-color --no-ext-diff --no-textconv --no-renames
      b h`. The id is over the file headers and every hunk line, context included, with hunk positions (the `@@`
      headers) and blob ids (the `index` lines) left out — so the line shifts main causes do not count, a changed
      context line does, and so does a hunk moved to another file. `git patch-id` hashes each line with its white
      space removed: a white-space-only difference does not count either (A8 chose patch-id; `--verbatim` and
      `--stable` exclude each other in git);
    * and new_head merges onto <main> without a conflict: `git merge-tree --write-tree <main> new_head` exits 0
      ("conflicts_with_main" when it reports a conflict). The reviewed change still applies to what main is now.
  old_head == new_head has no shortcut: it is held to the same rules. Anything else — an unknown commit
  ("unknown_commit"), a git that cannot be run, fails or times out ("git_failed") — is False. Ancestry alone is
  never enough: a merge commit whose conflict resolution or whose own content changes the reviewed patch does not
  inherit, and neither does one added commit; ancestry is not needed either: a rebase of the identical patch onto
  a moved main inherits, a rebase that changed the patch does not.

── Contract B: the verbs — stdout is ONE JSON object {"published", "result", "reasons", "action_id"} ─────────
    snapshot   --worktree W --out S
    publish    --job-id J --item I --phase pre_merge|post_deploy|artifact
               (--head H | --artifact-digest D --artifact-path P)
               --vslot V --author-id AU --reviewer-id RV --worktree W --job-exit N --result RES --as CID
               [--snapshot S] [--boundary BD] [--events E] [--external-review-path X --external-review-sha256 Y]
    invalidate --item I --phase PH (--head H | --artifact-digest D) --vslot V --reason TEXT --as CID [--events E]
    inherit    --repo G --old-head H1 --new-head H2 [--old-base B1 --new-base B2]     prints inheritance(…)

  snapshot (BEFORE the job) writes S = {schema, worktree, head, status_porcelain, tracked_sha256, taken_at}.
    tracked_sha256 = sha256 over the sorted (path, work-tree file sha256) list of the tracked files, read from
    the work tree itself. An existing S is never replaced (exit 1). Since A8 the snapshot is a record the
    launchers keep for the job's scratch directory; publish does not read it.
  publish requires, each observed by this process (reason when unmet):
    N = 0 (job_exit_nonzero) · RES is a valid ky.job_result/1 of job J and item I (result_missing,
    result_invalid, result_job_mismatch) with status done (result_not_done) and proposed_verdict.verdict ACCEPTED
    or REJECTED (verdict_not_proposed) whose head / phase / artifact_digest, where given, are the ones being
    published (verdict_head_mismatch, verdict_phase_mismatch, verdict_digest_mismatch) · AU ≠ RV
    (author_is_reviewer) · for pre_merge, W's HEAD is H at publish time (head_not_reviewed) · `git status
    --porcelain --untracked-files=all` of W is empty (tree_dirty) · artifact: sha256(P) = D (artifact_missing,
    artifact_digest_mismatch) · X, when given, is a file whose sha256 is Y (external_review_missing,
    external_review_sha_mismatch). W must be observable at all (worktree_unobservable). S and BD, when given,
    must be absolute paths and are otherwise ignored.
    Then, under the action record VERDICT-<J> (actor: role dispatcher, holder_kind controller, controller_id CID)
    and with an allow-listed environment:
        KY_STREAM=V KY_LANE=<V> $KY_BIN verdict <I> (--head H | --artifact-digest D) --phase <phase>
            --result <proposed> --detail "job <J>; <summary>" [--external-review-path X --external-review-sha256 Y]
    `published` is true only once that verdict event has been READ BACK from the ledger E (default
    $KY_RUN/EVENTS.jsonl): ky's exit code alone is not the publication.
    The record decides before the requirements are looked at again: DONE → nothing is run (exit 0, reason
    already_published) · unfinished → reconciled against E: a verdict event of this identity and result whose
    detail starts "job <J>;" completes the record; none → the requirements are checked afresh and the verdict is
    published under the same record (or the record is failed when they no longer hold); E unreadable → exit 3 ·
    another process is publishing it → exit 3 · FAILED → exit 1.
  invalidate appends REJECTED (detail "invalidated: <reason>", record INVALIDATE-<I>-<phase>-<first 12 hex of H
    or D>) only if the LATEST verdict of that identity in E is ACCEPTED; otherwise nothing is appended (exit 1:
    no_prior_verdict, latest_not_accepted — and only those). The dispatcher runs it before any queue action.
    Whenever it ends without the REJECTED observed while ACCEPTED is in force (ky refused or timed out, a record
    conflict, a FAILED record) it exits 3, never 1; a FAILED record is retried (kyaction.retry) by the next
    call once a fresh read shows ACCEPTED still in force (review round 2, R2-B-01). The record id is one
    per identity: an acceptance published AFTER a recorded invalidation cannot be invalidated under it — that
    is reported as unknown (exit 3, accepted_again_after_invalidation), never appended outside a record.
  inherit publishes nothing: exit 0 inherits · 1 does not (VERIFY the new head).

  Exit codes: 0 done · 1 refused or negative · 3 unknown, nothing may proceed · 64 usage · 66 an installation
  input is missing ($KY_RUN, the ky or git program, the worktree directory). Evidence that is missing — the job
  result, the artifact — is an unmet requirement (exit 1), not exit 66.
  Environment: KY_RUN (required: the run directory, absolute) · KY_BIN (default $KY_ROOT/bin/ky) · KY_GIT
  (default /usr/bin/git). Every path argument is absolute.

INTERPRETATION (packet KV3-B-KYVERDICTS, as amended by A8; each is stricter than the text, never laxer):
  * the patch-id comparison above and the base derivation; the conflict probe merges onto <main> as it is now;
  * a degenerate comparison (a base equal to its head, an empty reviewed patch) is "unproven_base";
  * an unmet publication requirement publishes nothing, not REJECTED;
  * the proposal's phase and artifact_digest are bound like its head; RES must be job J's result for item I;
  * `git status` is asked with --untracked-files=all, so a work-tree config cannot hide a file from it;
  * a complete but malformed ledger line is skipped exactly as the tracker skips it; an unterminated last line,
    a missing ledger or one that is not a regular file is "unreadable".

Uses kyaction.py (begin / complete / fail / reconcile) for the two publishing verbs only; the predicate needs
nothing but git. Python >= 3.9, standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
import time

DEFAULT_GIT = "/usr/bin/git"
MAIN_REFS = ("refs/remotes/origin/main", "refs/heads/main")
IDENTICAL = "identical_patch"
REFUSALS = ("patch_differs", "conflicts_with_main", "binary_change", "base_not_ancestor", "unknown_commit",
            "unproven_base", "git_failed")
PHASES = ("pre_merge", "post_deploy", "artifact")
VERDICTS = ("ACCEPTED", "REJECTED")
KIND_PUBLISH = "ky.verdict"
KIND_INVALIDATE = "ky.verdict.invalidate"
SNAPSHOT_SCHEMA = "ky.verdict_snapshot/1"
JOB_RESULT_SCHEMA = "ky.job_result/1"
VERDICT_STREAM = "V"                                         # plan §6: KY_STREAM=V KY_LANE=<vslot> ky verdict …
KY_ENV_NAMES = ("HOME", "USER", "LANG", "TMPDIR", "KY_ROOT", "KY_RUN")      # passed on to ky when set; nothing else
KY_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
GIT_TIMEOUT_S = 120
KY_TIMEOUT_S = 120
EVIDENCE_LIMIT = 1 << 20
_SHA1 = re.compile(r"^[0-9a-f]{40}\Z")
_SHA256 = re.compile(r"^[0-9a-f]{64}\Z")
_JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_ITEM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}\Z")
_SLOT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_JOB_RESULT_KEYS = ("schema", "job_id", "item", "status", "branch", "head_sha", "pr_number", "tests",
                    "blocked_reason", "notes")


class _GitFailed(Exception):
    """git could not be run, timed out, or answered something that is not an answer."""


class _Unreadable(Exception):
    """The ledger cannot be read as a ledger: what it says about a verdict is unknown."""


class _Usage(Exception):
    pass


# ───────────────────────────────────────── processes ─────────────────────────────────────────

def _kill_group(proc):
    """End a child this process started, with everything it started (it leads its own session)."""
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.kill()
    except OSError:
        pass
    try:
        proc.communicate(timeout=5)
    except (subprocess.SubprocessError, OSError, ValueError):
        pass


def _run(argv, cwd, env, timeout, input=None):
    """→ (returncode, stdout, stderr) in bytes; `input` bytes, when given, are the child's stdin (else nothing is).
    subprocess.TimeoutExpired after the child's group has been killed; OSError when it could not be started."""
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = proc.communicate(input=input, timeout=timeout)
    except BaseException:
        _kill_group(proc)
        raise
    return proc.returncode, out, err


def _program(path):
    return isinstance(path, str) and os.path.isabs(path) and os.path.isfile(path) and os.access(path, os.X_OK)


def _git_program(environ=None):
    return (os.environ if environ is None else environ).get("KY_GIT") or DEFAULT_GIT


def _git_env(environ=None):
    """git's whole environment: no GIT_* of the caller, no user or system configuration."""
    source = os.environ if environ is None else environ
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
           "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"}
    for name in ("HOME", "TMPDIR", "DEVELOPER_DIR"):
        if source.get(name):
            env[name] = source[name]
    return env


class _Git:
    """One repository, one git program, one deadline for everything asked of it."""

    def __init__(self, program, repo, timeout, environ=None):
        if not _program(program):
            raise _GitFailed("git program %r is not an absolute executable file" % (program,))
        if not isinstance(repo, str) or not repo or not os.path.isdir(repo):
            raise _GitFailed("no such repository directory")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not timeout > 0:
            raise _GitFailed("timeout must be a positive number")
        self.program, self.repo, self.env = program, repo, _git_env(environ)
        self.deadline = time.monotonic() + timeout

    def __call__(self, *args, input=None):
        """→ (returncode, stdout bytes); _GitFailed when git cannot be asked or does not answer in time."""
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise _GitFailed("timed out")
        try:
            code, out, _ = _run([self.program, "-c", "core.fsmonitor=false", *args], self.repo, self.env, left,
                                input=input)
        except subprocess.TimeoutExpired:
            raise _GitFailed("timed out") from None
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            raise _GitFailed(type(e).__name__) from None
        return code, out

    def ok(self, *args, input=None):
        """stdout of a command that must succeed."""
        code, out = self(*args, input=input)
        if code != 0:
            raise _GitFailed("git %s: exit %d" % (args[0], code))
        return out

    def yes(self, *args):
        """True on exit 0, False on exit 1 (git's "no"), _GitFailed on anything else."""
        code, _ = self(*args)
        if code not in (0, 1):
            raise _GitFailed("git %s: exit %d" % (args[0], code))
        return code == 0


# ───────────────────────────────── Contract A: the inheritance predicate ─────────────────────────────────

def _hex40(value):
    return isinstance(value, str) and _SHA1.match(value) is not None


def _is_commit(git, sha):
    """The repository is known to answer (rev-parse --git-dir succeeded): any refusal here is "no such commit"."""
    return git("cat-file", "-e", sha + "^{commit}")[0] == 0


def _main_ref(git):
    for ref in MAIN_REFS:
        code, out = git("rev-parse", "--verify", "--quiet", ref + "^{commit}")
        if code == 0 and _hex40(out.decode("ascii", "replace").strip()):
            return ref
    return None


def _derived_base(git, main, head):
    """The one merge base of <main> and `head`, or None when there is none or more than one."""
    code, out = git("merge-base", "--all", main, head)
    if code == 1:
        return None
    if code != 0:
        raise _GitFailed("git merge-base: exit %d" % code)
    found = out.decode("ascii", "replace").split()
    return found[0] if len(found) == 1 and _hex40(found[0]) else None


def _patch(git, base, head):
    """→ (the reviewed patch as `git diff` prints it, True when something binary changed)."""
    raw = git.ok("diff", "--no-color", "--no-ext-diff", "--no-textconv", "--no-renames", base, head)
    binary = any(line.startswith(b"Binary files ") or line == b"GIT binary patch" for line in raw.split(b"\n"))
    return raw, binary


def _patch_id(git, patch):
    """`git patch-id --stable` of one patch → its 40-hex id, or None for a patch that identifies nothing (empty)."""
    out = git.ok("patch-id", "--stable", input=patch)
    words = out.decode("ascii", "replace").split()
    return words[0] if words and _hex40(words[0]) else None


def _same_patch(old, new):
    """THE comparison: the two reviewed patches, by their patch-id (A8)."""
    return old is not None and old == new


def _clean_merge(git, main, head):
    """THE conflict probe: `git merge-tree --write-tree <main> <head>` → True (a tree, no conflict), False (git
    reports a conflict); _GitFailed on any other answer."""
    code, out = git("merge-tree", "--write-tree", "--no-messages", main, head)
    if code == 1:
        return False
    if code != 0:
        raise _GitFailed("git merge-tree: exit %d" % code)
    tree = out.decode("ascii", "replace").split("\n", 1)[0].strip()
    if not _hex40(tree):
        raise _GitFailed("git merge-tree: no tree")
    return True


def _compare(repo, result, timeout):
    """→ IDENTICAL or one of REFUSALS; fills the derived bases and the patch id into `result`. Raises _GitFailed."""
    git = _Git(_git_program(), repo, timeout)
    old_head, new_head = result["old_head"], result["new_head"]
    if not _hex40(old_head) or not _hex40(new_head):
        return "unknown_commit"
    git.ok("rev-parse", "--git-dir")
    if not _is_commit(git, old_head) or not _is_commit(git, new_head):
        return "unknown_commit"
    main = _main_ref(git)
    if main is None:
        return "unproven_base"                      # nothing to derive a base from, nothing to merge onto
    for key, head in (("old_base", old_head), ("new_base", new_head)):
        if result[key] is None:
            result[key] = _derived_base(git, main, head)
            if result[key] is None:
                return "unproven_base"
        elif not _hex40(result[key]) or not _is_commit(git, result[key]):
            return "unknown_commit"
    if result["old_base"] == old_head or result["new_base"] == new_head:
        return "unproven_base"                      # a head already in main, or a base given as its head
    if not git.yes("merge-base", "--is-ancestor", result["old_base"], old_head) \
            or not git.yes("merge-base", "--is-ancestor", result["new_base"], new_head):
        return "base_not_ancestor"
    old_patch, old_binary = _patch(git, result["old_base"], old_head)
    new_patch, new_binary = _patch(git, result["new_base"], new_head)
    if old_binary or new_binary:
        return "binary_change"
    if not old_patch.strip():
        return "unproven_base"                      # nothing was reviewed: an empty patch equals any empty patch
    result["patch_id"] = _patch_id(git, old_patch)
    if _same_patch(result["patch_id"], _patch_id(git, new_patch)) is not True:
        return "patch_differs"
    return IDENTICAL if _clean_merge(git, main, new_head) is True else "conflicts_with_main"


def inheritance(repo, old_head, new_head, *, old_base=None, new_base=None, timeout=60):
    """Does the verdict reviewed at `old_head` still hold at `new_head`? See the module docstring. Never raises;
    `inherits` is True for exactly one reason, "identical_patch"."""
    def text(value):
        return value if isinstance(value, str) else None

    result = {"inherits": False, "reason": "git_failed", "old_head": text(old_head), "new_head": text(new_head),
              "old_base": text(old_base), "new_base": text(new_base), "patch_id": None}
    given_bases = (old_base, new_base)
    try:
        if any(b is not None and not isinstance(b, str) for b in given_bases):
            reason = "unknown_commit"
        else:
            reason = _compare(os.fspath(repo) if isinstance(repo, os.PathLike) else repo, result, timeout)
    except Exception:                               # fail-closed: whatever went wrong, nothing was proven
        reason = "git_failed"
    result["reason"] = reason if reason == IDENTICAL or reason in REFUSALS else "git_failed"
    result["inherits"] = result["reason"] == IDENTICAL
    return result


def inherits(repo, old_head, new_head):
    """The shared predicate (ruling P4), fail-closed: True only when inheritance() proved the identical patch."""
    try:
        return inheritance(repo, old_head, new_head)["inherits"] is True
    except Exception:
        return False


# ───────────────────────────────────────── observations ─────────────────────────────────────────

def _flat(text, limit=400):
    return " ".join(str(text if text is not None else "").split())[:limit]


def _sha_file(path):
    """sha256 hex of a regular file (symbolic links followed), or None when it cannot be read as one."""
    try:
        if not stat.S_ISREG(os.stat(path).st_mode):
            return None
        digest = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except (OSError, ValueError):
        return None


def _no_constant(name):
    raise ValueError("%s is not JSON" % name)


def _no_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError("duplicate key %r" % key)
        seen[key] = value
    return seen


def _evidence(path):
    """A small JSON evidence file the job or the controller wrote → (document, None) or (None, "missing" |
    "invalid"). A symbolic link is refused unread; so is anything that is not strict JSON."""
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            return None, "invalid"
        with open(path, "rb") as f:
            raw = f.read(EVIDENCE_LIMIT + 1)
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError):
        return None, "invalid"
    if len(raw) > EVIDENCE_LIMIT:
        return None, "invalid"
    try:
        return json.loads(raw.decode("utf-8"), parse_constant=_no_constant, object_pairs_hook=_no_duplicates), None
    except (ValueError, RecursionError):
        return None, "invalid"


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def job_result_problem(doc):
    """None when `doc` is a ky.job_result/1 document exactly as schemas/job_result.json defines one, else what is
    wrong with it (the first thing found). tests/test_kyverdicts.py holds this against the schema itself."""
    if not isinstance(doc, dict):
        return "not an object"
    extra = sorted(set(doc) - set(_JOB_RESULT_KEYS) - {"proposed_verdict"})
    missing = [key for key in _JOB_RESULT_KEYS if key not in doc]
    if extra or missing:
        return "keys: unexpected %s, missing %s" % (extra, missing)
    if doc["schema"] != JOB_RESULT_SCHEMA or not isinstance(doc["schema"], str):
        return "schema is not %s" % JOB_RESULT_SCHEMA
    if not isinstance(doc["job_id"], str) or not _JOB_ID.match(doc["job_id"]):
        return "job_id"
    if not isinstance(doc["item"], str) or not doc["item"]:
        return "item"
    if not isinstance(doc["status"], str) or doc["status"] not in ("done", "blocked", "failed"):
        return "status"
    if doc["branch"] is not None and (not isinstance(doc["branch"], str) or not doc["branch"]):
        return "branch"
    if doc["head_sha"] is not None and not _hex40(doc["head_sha"]):
        return "head_sha"
    if doc["pr_number"] is not None and (not _integer(doc["pr_number"]) or doc["pr_number"] < 1):
        return "pr_number"
    if not isinstance(doc["tests"], list):
        return "tests"
    for row in doc["tests"]:
        if not isinstance(row, dict) or set(row) != {"cmd", "exit", "summary"} or not isinstance(row["cmd"], str) \
                or not row["cmd"] or not _integer(row["exit"]) or not isinstance(row["summary"], str):
            return "tests[]"
    if doc["blocked_reason"] is not None and not isinstance(doc["blocked_reason"], str):
        return "blocked_reason"
    if not isinstance(doc["notes"], str):
        return "notes"
    if "proposed_verdict" in doc and not isinstance(doc["proposed_verdict"], dict):
        return "proposed_verdict"
    if doc["status"] == "blocked" and not doc["blocked_reason"]:
        return "a blocked job must say why"
    if doc["pr_number"] is not None and doc["head_sha"] is None:
        return "a job that names a PR must name its head"
    return None


def _tracked_sha256(git, top):
    """sha256 over the sorted (path, work-tree file sha256) list of the tracked files of the work tree `top`."""
    paths = sorted(p for p in git.ok("ls-files", "-z").split(b"\0") if p)
    digest = hashlib.sha256()
    for path in paths:
        full = os.path.join(os.fsencode(top), path)
        try:
            mode = os.lstat(full).st_mode
        except FileNotFoundError:
            entry = "absent"
        except OSError as e:
            raise _GitFailed("tracked file unreadable: %s" % type(e).__name__) from None
        else:
            if stat.S_ISLNK(mode):
                try:
                    entry = "link:" + hashlib.sha256(os.fsencode(os.readlink(full))).hexdigest()
                except OSError as e:
                    raise _GitFailed("tracked link unreadable: %s" % type(e).__name__) from None
            elif stat.S_ISREG(mode):
                file_sha = _sha_file(full)
                if file_sha is None:
                    raise _GitFailed("tracked file unreadable")
                entry = "file:" + file_sha
            else:
                entry = "dir" if stat.S_ISDIR(mode) else "other"       # a submodule's directory, or a surprise
        digest.update(path + b"\0" + entry.encode("ascii") + b"\n")
    return digest.hexdigest()


def _observe_worktree(worktree, environ, tracked=True):
    """What the work tree is right now → {"worktree", "head", "status_porcelain"} plus, with `tracked`,
    "tracked_sha256" (the snapshot's record; publish does not ask for it). _GitFailed when any part of it cannot be
    observed, or when `worktree` is not the top of a Git work tree."""
    git = _Git(_git_program(environ), worktree, GIT_TIMEOUT_S, environ)
    top = os.fsdecode(git.ok("rev-parse", "--show-toplevel")).rstrip("\n")
    if not top or os.path.realpath(top) != os.path.realpath(worktree):
        raise _GitFailed("not the top of a work tree")
    head = git.ok("rev-parse", "--verify", "--quiet", "HEAD^{commit}").decode("ascii", "replace").strip()
    if not _hex40(head):
        raise _GitFailed("HEAD is not a commit")
    status = git.ok("status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none")
    seen = {"worktree": os.path.realpath(worktree), "head": head, "status_porcelain": status.decode("utf-8", "replace")}
    if tracked:
        seen["tracked_sha256"] = _tracked_sha256(git, top)
    return seen


def _read_ledger(path):
    """The ledger's events in order (as the tracker reads them: a complete line that is not a JSON object is
    skipped). _Unreadable when the file is missing, not a regular file, or ends in an unterminated line."""
    try:
        if not stat.S_ISREG(os.stat(path).st_mode):
            raise _Unreadable("not a regular file")
        with open(path, "rb") as f:
            data = f.read()
    except (OSError, ValueError) as e:
        raise _Unreadable(type(e).__name__) from None
    if data and not data.endswith(b"\n"):
        raise _Unreadable("the last line is not terminated")
    events = []
    for raw in data.split(b"\n"):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw.decode("utf-8"), parse_constant=_no_constant)
        except (ValueError, RecursionError):
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _of_identity(event, identity):
    return event.get("kind") == "verdict" and event.get("item") == identity["item"] \
        and event.get("phase") == identity["phase"] and (event.get("head") or None) == identity["head"] \
        and (event.get("artifact_digest") or None) == identity["artifact_digest"]


def _job_verdict(events, identity, result, job_id):
    """The verdict event job `job_id` is the source of: this identity, this result, detail "job <job_id>; …"."""
    prefix = "job %s;" % job_id
    for event in reversed(events):
        if _of_identity(event, identity) and event.get("result") == result \
                and isinstance(event.get("detail"), str) and event["detail"].startswith(prefix):
            return event
    return None


def _latest_verdict(events, identity):
    return next((event for event in reversed(events) if _of_identity(event, identity)), None)


# ───────────────────────────────────────── publication ─────────────────────────────────────────

def _kyaction():
    """kyaction.py — the copy beside this file. Loaded on first use: the predicate does not need it."""
    module = sys.modules.get("kyaction")
    if module is None:
        import importlib.util
        beside = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kyaction.py")
        spec = importlib.util.spec_from_file_location("kyaction", beside)
        if spec is None or spec.loader is None:
            raise ImportError("kyaction.py is not beside kyverdicts.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["kyaction"] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop("kyaction", None)
            raise
    return module


def _out(published, result, reasons, action_id):
    return {"published": published is True, "result": result, "reasons": list(reasons), "action_id": action_id}


def _refusal(code, action_id, *reasons):
    return code, _out(False, None, reasons, action_id)


def _installation(environ, action_id):
    """→ (run_dir, ky, None) or (None, None, the exit-66 refusal)."""
    run_dir = environ.get("KY_RUN") or ""
    if not os.path.isabs(run_dir) or not os.path.isdir(run_dir):
        return None, None, _refusal(66, action_id, "input_missing: $KY_RUN must name the existing run directory")
    ky = environ.get("KY_BIN") or (os.path.join(environ["KY_ROOT"], "bin", "ky") if environ.get("KY_ROOT") else "")
    if not _program(ky):
        return None, None, _refusal(66, action_id, "input_missing: the ky program ($KY_BIN, else $KY_ROOT/bin/ky)")
    return run_dir, ky, None


def _ky_env(environ, vslot):
    env = {name: environ[name] for name in KY_ENV_NAMES if environ.get(name)}
    env.update(PATH=KY_PATH, KY_STREAM=VERDICT_STREAM, KY_LANE=vslot)
    return env


def _run_ky(ky, args, env):
    """Run `ky <args>` → (exit code or None, None | "ky_timeout" | "ky_not_run", stderr text)."""
    try:
        code, _, err = _run([ky, *args], None, env, KY_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, "ky_timeout", ""
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        return None, "ky_not_run", type(e).__name__
    return code, None, err.decode("utf-8", "replace")


def _verdict_args(inputs):
    args = ["verdict", inputs["item"]]
    args += ["--head", inputs["head"]] if inputs["head"] else ["--artifact-digest", inputs["artifact_digest"]]
    args += ["--phase", inputs["phase"], "--result", inputs["result"], "--detail", inputs["detail"]]
    review = inputs.get("external_review")
    if review:
        args += ["--external-review-path", review["path"], "--external-review-sha256", review["sha256"]]
    return args


def _execute(ka, run_dir, action_id, ky, environ, inputs, ledger, observed):
    """The side effect of an INTENDED record, then what the ledger says became of it. `observed(events)` returns
    the event that IS this action's effect, or None."""
    code, why, stderr = _run_ky(ky, _verdict_args(inputs), _ky_env(environ, inputs["vslot"]))
    try:
        event = observed(_read_ledger(ledger))
    except _Unreadable:
        return _refusal(3, action_id, "ledger_unreadable")
    if event is not None:
        ka.complete(run_dir, action_id, {"result": inputs["result"], "ledger": ledger, "event": event,
                                         "ky_exit": code})
        return 0, _out(True, inputs["result"], [], action_id)
    if code == 0:                                    # ky says done, the ledger does not show it: nothing is known
        return _refusal(3, action_id, "event_not_observed")
    reason = why or "ky_refused: exit %d" % code
    ka.fail(run_dir, action_id, {"published": False, "reason": reason, "ky_exit": code, "stderr": _flat(stderr, 300)})
    return _refusal(1, action_id, reason)


def _requirements(a, environ):
    """Every publication requirement, each observed here → (reasons, facts). Nothing is published on any reason."""
    reasons, facts = [], {"result": None, "summary": "", "evidence": {}}
    if a.job_exit != 0:
        reasons.append("job_exit_nonzero")

    doc, why = _evidence(a.result)
    if why == "missing":
        reasons.append("result_missing")
    elif why or job_result_problem(doc) is not None:
        reasons.append("result_invalid")
    else:
        facts["evidence"]["job_result_sha256"] = _sha_file(a.result)
        if doc["job_id"] != a.job_id or doc["item"] != a.item:
            reasons.append("result_job_mismatch")
        if doc["status"] != "done":
            reasons.append("result_not_done")
        proposed = doc.get("proposed_verdict")
        verdict = proposed.get("verdict") if isinstance(proposed, dict) else None
        if not isinstance(verdict, str) or verdict not in VERDICTS:
            reasons.append("verdict_not_proposed")
        else:
            facts["result"] = verdict
            summary = proposed.get("summary")
            facts["summary"] = _flat(summary if isinstance(summary, str) and summary.strip() else doc["notes"])
            if proposed.get("head") is not None and proposed["head"] != a.head:
                reasons.append("verdict_head_mismatch")
            if proposed.get("phase") is not None and proposed["phase"] != a.phase:
                reasons.append("verdict_phase_mismatch")
            if proposed.get("artifact_digest") is not None and proposed["artifact_digest"] != a.artifact_digest:
                reasons.append("verdict_digest_mismatch")

    if a.author_id.strip().casefold() == a.reviewer_id.strip().casefold():
        reasons.append("author_is_reviewer")

    try:                                             # A8: the tree is observed NOW; no pre-job snapshot is compared
        now = _observe_worktree(a.worktree, environ, tracked=False)
    except _GitFailed:
        reasons.append("worktree_unobservable")
    else:
        if a.phase == "pre_merge" and now["head"] != a.head:
            reasons.append("head_not_reviewed")
        if now["status_porcelain"] != "":
            reasons.append("tree_dirty")
        facts["evidence"]["worktree_head"] = now["head"]

    if a.phase == "artifact":
        if not os.path.exists(a.artifact_path):
            reasons.append("artifact_missing")
        elif _sha_file(a.artifact_path) != a.artifact_digest:
            reasons.append("artifact_digest_mismatch")

    if a.external_review_path:
        if not os.path.exists(a.external_review_path):
            reasons.append("external_review_missing")
        elif _sha_file(a.external_review_path) != a.external_review_sha256:
            reasons.append("external_review_sha_mismatch")
    return reasons, facts


def _identity(a):
    return {"item": a.item, "phase": a.phase, "head": a.head or None, "artifact_digest": a.artifact_digest or None}


def _actor(a):
    return {"role": "dispatcher", "holder_kind": "controller", "controller_id": a.as_}


def _guarded(ka, action_id, body, conflict=1):
    """Run a publishing verb; whatever the action records refuse or cannot tell becomes its exit code."""
    try:
        return body()
    except ka.ActionConflict:
        return _refusal(conflict, action_id, "action_conflict")
    except ka.ActionUnreadable:
        return _refusal(3, action_id, "action_record_unreadable")
    except ka.LockBusy:
        return _refusal(3, action_id, "action_in_progress")
    except ka.LockUnknown:
        return _refusal(3, action_id, "action_lock_unknown")
    except ka.ActionInvalid as e:
        return _refusal(64, action_id, "usage: %s" % _flat(e, 200))
    except ka.ActionError as e:
        return _refusal(3, action_id, "action_record_error: %s" % type(e).__name__)


def _recorded_result(record):
    result = record.get("result")
    value = result.get("result") if isinstance(result, dict) else None
    return value if isinstance(value, str) and value in VERDICTS else None


def _same_target(ka, record, kind, target):
    try:
        return record.get("kind") == kind and ka.canonical(record.get("target")) == ka.canonical(target)
    except (TypeError, ValueError):
        return False


def _cmd_publish(a, environ):
    action_id = "VERDICT-" + a.job_id
    run_dir, ky, missing = _installation(environ, action_id)
    if missing:
        return missing
    if not _program(_git_program(environ)) or not os.path.isdir(a.worktree):
        return _refusal(66, action_id, "input_missing: the git program ($KY_GIT) or the worktree directory")
    ka = _kyaction()
    ledger = a.events or os.path.join(run_dir, "EVENTS.jsonl")
    identity = _identity(a)
    target = dict(identity, kind="verdict", ledger=ledger)

    def observer(record):
        inputs = record.get("inputs") or {}
        try:
            event = _job_verdict(_read_ledger(ledger), identity, inputs.get("result"), inputs.get("job_id"))
        except _Unreadable:
            return "unknown", {"error": "ledger_unreadable", "ledger": ledger}
        if event is None:
            return "not_done", {"ledger": ledger}
        return "done", {"result": inputs.get("result"), "ledger": ledger, "event": event, "ky_exit": None}

    def settle(record):
        """What an existing record already decides, or None: its effect is positively absent and may be made."""
        if not _same_target(ka, record, KIND_PUBLISH, target):
            return _refusal(1, action_id, "action_conflict")
        if record["state"] == "FAILED":
            return _refusal(1, action_id, "action_failed")
        if record["state"] == "INTENDED":
            if ka.in_progress(record):
                return _refusal(3, action_id, "action_in_progress")
            outcome, record = ka.reconcile(run_dir, action_id, observer, by=a.as_)
            if outcome == "not_done":
                return None
            if outcome == "failed":
                return _refusal(1, action_id, "action_failed")
            if outcome != "done":
                return _refusal(3, action_id, "ledger_unreadable")
        published = _recorded_result(record)
        if record["state"] != "DONE" or published is None:
            return _refusal(3, action_id, "action_record_unreadable")
        return 0, _out(True, published, ["already_published"], action_id)

    def body():
        record, absent = ka.peek(run_dir, action_id), False
        if record is not None:
            settled = settle(record)
            if settled is not None:
                return settled
            absent = True                            # unfinished, reconciled: the verdict is not in the ledger
        reasons, facts = _requirements(a, environ)
        if reasons:
            if absent:
                ka.fail(run_dir, action_id, {"published": False, "reasons": reasons})
            return _refusal(1, action_id, *reasons)
        inputs = {"job_id": a.job_id, "item": a.item, "phase": a.phase, "head": identity["head"],
                  "artifact_digest": identity["artifact_digest"], "result": facts["result"],
                  "detail": "job %s; %s" % (a.job_id, facts["summary"] or "no summary given"),
                  "vslot": a.vslot, "author_id": a.author_id, "reviewer_id": a.reviewer_id,
                  "external_review": ({"path": a.external_review_path, "sha256": a.external_review_sha256}
                                      if a.external_review_path else None),
                  "artifact_path": a.artifact_path or None, "evidence": facts["evidence"]}
        status, record = ka.begin(run_dir, action_id, KIND_PUBLISH, _actor(a), inputs, target,
                                  "no verdict of job %s at this identity -> %s published" % (a.job_id, facts["result"]))
        if status != "new" and not (status == "unfinished" and absent):
            settled = settle(record)
            if settled is not None:
                return settled
        return _execute(ka, run_dir, action_id, ky, environ, inputs, ledger,
                        lambda events: _job_verdict(events, identity, inputs["result"], a.job_id))

    return _guarded(ka, action_id, body)


def _cmd_invalidate(a, environ):
    identity = _identity(a)
    action_id = "INVALIDATE-%s-%s-%s" % (a.item, a.phase, (identity["head"] or identity["artifact_digest"])[:12])
    run_dir, ky, missing = _installation(environ, action_id)
    if missing:
        return missing
    ka = _kyaction()
    ledger = a.events or os.path.join(run_dir, "EVENTS.jsonl")
    target = dict(identity, kind="verdict", ledger=ledger, result="REJECTED")
    seen = {}

    def latest():
        seen["latest"] = _latest_verdict(_read_ledger(ledger), identity)
        return seen["latest"]

    def is_effect(event, inputs):
        return event is not None and event.get("result") == "REJECTED" and event.get("detail") == inputs["detail"]

    def not_accepted(event):
        return "no_prior_verdict" if event is None else "latest_not_accepted"

    def in_force(event):
        return event is not None and event.get("result") == "ACCEPTED"

    def run(inputs):
        """Exit 1 means 'nothing to invalidate'; an attempt that appended nothing while ACCEPTED was in force is
        not that (R2-B-01): exit 3, and the FAILED record is retried by the next call."""
        code, out = _execute(ka, run_dir, action_id, ky, environ, inputs, ledger,
                             lambda events: (lambda event: event if is_effect(event, inputs) else None)(
                                 _latest_verdict(events, identity)))
        return (3 if code == 1 else code), out

    def body():
        try:
            last = latest()
        except _Unreadable:
            return _refusal(3, action_id, "ledger_unreadable")
        record = ka.peek(run_dir, action_id)
        if record is None:
            if not in_force(last):
                return _refusal(1, action_id, not_accepted(last))
            inputs = dict(identity, result="REJECTED", detail="invalidated: " + _flat(a.reason, 600),
                          vslot=a.vslot, external_review=None)
            status, record = ka.begin(run_dir, action_id, KIND_INVALIDATE, _actor(a), inputs, target,
                                      "ACCEPTED in force at this identity -> explicit REJECTED appended")
            if status == "new":
                return run(inputs)
        if not _same_target(ka, record, KIND_INVALIDATE, target) or not isinstance(record.get("inputs"), dict) \
                or not isinstance(record["inputs"].get("detail"), str):
            return _refusal(3 if in_force(last) else 1, action_id,
                            "action_conflict" if in_force(last) else not_accepted(last))
        inputs = record["inputs"]                    # the invalidation this record intends, whatever is asked now
        if record["state"] == "FAILED":
            if not in_force(last):
                return _refusal(1, action_id, not_accepted(last))
            ka.retry(run_dir, action_id, _actor(a))  # ACCEPTED in force, read just now: the REJECTED is still owed
            return run(inputs)
        if record["state"] == "INTENDED":
            if ka.in_progress(record):
                return _refusal(3, action_id, "action_in_progress")

            def observer(_record):
                try:
                    event = latest()
                except _Unreadable:
                    return "unknown", {"error": "ledger_unreadable", "ledger": ledger}
                if is_effect(event, inputs):
                    return "done", {"result": "REJECTED", "ledger": ledger, "event": event, "ky_exit": None}
                return "not_done", {"ledger": ledger}

            outcome, record = ka.reconcile(run_dir, action_id, observer, by=a.as_)
            if outcome == "not_done":
                last = seen.get("latest")
                if not in_force(last):
                    ka.fail(run_dir, action_id, {"published": False, "reasons": [not_accepted(last)]})
                    return _refusal(1, action_id, not_accepted(last))
                return run(inputs)
            if outcome == "failed":                  # failed meanwhile by another call: the next call decides
                return _refusal(3, action_id, "action_failed")
            if outcome != "done":
                return _refusal(3, action_id, "ledger_unreadable")
            return 0, _out(True, "REJECTED", ["already_published"], action_id)
        if record["state"] != "DONE" or _recorded_result(record) != "REJECTED":
            return _refusal(3, action_id, "action_record_unreadable")
        if is_effect(last, inputs):
            return 0, _out(True, "REJECTED", ["already_published"], action_id)
        if in_force(last):
            return _refusal(3, action_id, "accepted_again_after_invalidation")
        return _refusal(1, action_id, not_accepted(last))

    return _guarded(ka, action_id, body, conflict=3)


def _write_exclusive(path, text):
    """Create `path` with `text` only if nothing is there (hard link from a complete temporary file)."""
    tmp = os.path.join(os.path.dirname(path), ".%s.tmp.%d" % (os.path.basename(path), os.getpid()))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(text.encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        os.link(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _cmd_snapshot(a, environ):
    if not _program(_git_program(environ)) or not os.path.isdir(a.worktree) \
            or not os.path.isdir(os.path.dirname(a.out)):
        return _refusal(66, None, "input_missing: the git program ($KY_GIT), the worktree or the directory of --out")
    if os.path.lexists(a.out):
        return _refusal(1, None, "snapshot_exists")
    try:
        seen = _observe_worktree(a.worktree, environ)
    except _GitFailed:
        return _refusal(3, None, "worktree_unobservable")
    snapshot = dict(seen, schema=SNAPSHOT_SCHEMA, taken_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    try:
        _write_exclusive(a.out, json.dumps(snapshot, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    except FileExistsError:
        return _refusal(1, None, "snapshot_exists")
    except OSError as e:
        return _refusal(3, None, "snapshot_not_written: %s" % type(e).__name__)
    return 0, _out(False, "snapshot_written", [], None)


def _cmd_inherit(a, _environ):
    result = inheritance(a.repo, a.old_head, a.new_head, old_base=a.old_base, new_base=a.new_base)
    return (0 if result["inherits"] is True else 1), result


# ───────────────────────────────────────── CLI ─────────────────────────────────────────

USAGE = """usage: kyverdicts.py snapshot --worktree W --out S
       kyverdicts.py publish --job-id J --item I --phase pre_merge|post_deploy|artifact
                             (--head H | --artifact-digest D --artifact-path P)
                             --vslot V --author-id AU --reviewer-id RV --worktree W --job-exit N
                             --result RES --as CID [--snapshot S] [--boundary BD] [--events E]
                             [--external-review-path X --external-review-sha256 Y]
       kyverdicts.py invalidate --item I --phase PH (--head H | --artifact-digest D) --vslot V --reason TEXT
                             --as CID [--events E]
       kyverdicts.py inherit --repo G --old-head H1 --new-head H2 [--old-base B1 --new-base B2]
exit: 0 done / inherits · 1 refused or negative · 3 unknown, nothing may proceed · 64 usage · 66 input missing"""


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise _Usage(message)


def _parser():
    parser = _Parser(prog="kyverdicts.py", add_help=False, allow_abbrev=False)
    sub = parser.add_subparsers(dest="verb", required=True, parser_class=_Parser)

    def verb(name, required, optional=()):
        p = sub.add_parser(name, add_help=False, allow_abbrev=False)
        for flag in required:
            p.add_argument(flag, required=True)
        for flag in optional:
            p.add_argument(flag)
        return p

    verb("snapshot", ("--worktree", "--out"))
    p = verb("publish", ("--job-id", "--item", "--vslot", "--author-id", "--reviewer-id", "--worktree", "--result"),
             ("--head", "--artifact-digest", "--artifact-path", "--events", "--external-review-path",
              "--external-review-sha256", "--snapshot", "--boundary"))      # the last two: accepted, not read (A8)
    p.add_argument("--phase", required=True, choices=PHASES)
    p.add_argument("--job-exit", required=True, type=int)
    p.add_argument("--as", required=True, dest="as_")
    p = verb("invalidate", ("--item", "--vslot", "--reason"), ("--head", "--artifact-digest", "--events"))
    p.add_argument("--phase", required=True, choices=PHASES)
    p.add_argument("--as", required=True, dest="as_")
    verb("inherit", ("--repo", "--old-head", "--new-head"), ("--old-base", "--new-base"))
    return parser


def _want(condition, message):
    if not condition:
        raise _Usage(message)


def _absolute(a, *names):
    for name in names:
        value = getattr(a, name, None)
        _want(value is None or (value and os.path.isabs(value)), "--%s must be an absolute path" % name.replace("_", "-"))


def _check_identity(a):
    _want(_ITEM.match(a.item), "--item is not an item id")
    _want(_SLOT.match(a.vslot), "--vslot is not a slot name")
    _want(a.as_.strip() == a.as_ and a.as_, "--as needs the controller id")
    if a.phase == "artifact":
        _want(a.head is None and a.artifact_digest is not None, "phase artifact takes --artifact-digest, not --head")
        _want(_SHA256.match(a.artifact_digest), "--artifact-digest is not a sha256")
    else:
        _want(a.artifact_digest is None and a.head is not None, "phase %s takes --head, not --artifact-digest" % a.phase)
        _want(_SHA1.match(a.head), "--head is not a full commit id")


def _parse(argv):
    a = _parser().parse_args(argv)
    if a.verb == "snapshot":
        _absolute(a, "worktree", "out")
    elif a.verb == "inherit":
        _absolute(a, "repo")
    elif a.verb == "publish":
        _check_identity(a)
        _want(_JOB_ID.match(a.job_id), "--job-id is not a job id")
        _want(a.author_id.strip() and a.reviewer_id.strip(), "--author-id and --reviewer-id must not be empty")
        _want((a.phase == "artifact") == (a.artifact_path is not None),
              "--artifact-path goes with phase artifact, and only with it")
        _want((a.external_review_path is None) == (a.external_review_sha256 is None),
              "--external-review-path and --external-review-sha256 go together")
        _want(a.external_review_sha256 is None or _SHA256.match(a.external_review_sha256),
              "--external-review-sha256 is not a sha256")
        _absolute(a, "worktree", "snapshot", "result", "boundary", "events", "artifact_path", "external_review_path")
    else:
        _check_identity(a)
        _want(a.reason.strip(), "--reason must say why")
        _absolute(a, "events")
    return a


def main(argv=None, environ=None, stdout=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    environ = os.environ if environ is None else environ
    stdout = sys.stdout if stdout is None else stdout
    try:
        a = _parse(argv)
    except _Usage as e:
        print("kyverdicts: %s\n%s" % (e, USAGE), file=sys.stderr)
        code, out = _refusal(64, None, "usage: %s" % _flat(e, 200))
    else:
        handler = {"snapshot": _cmd_snapshot, "publish": _cmd_publish, "invalidate": _cmd_invalidate,
                   "inherit": _cmd_inherit}[a.verb]
        try:
            code, out = handler(a, environ)
        except Exception as e:                       # nothing is claimed about what an unexpected error left behind
            code, out = _refusal(3, None, "internal_error: %s" % type(e).__name__)
    print(json.dumps(out, ensure_ascii=False, sort_keys=True), file=stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
