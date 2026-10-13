#!/usr/bin/env bash
# kyboundary.sh v1.2 (plan v2.7 §7 "Verifier boundary", §6 "Verdict publication"; packet KV3-B-KYBOUNDARY) — the ENFORCED
# verifier boundary. A qualification PASS is not this boundary (kyqualify.py BOUNDARY); this is.
# Status: DRAFT — pending independent review (KV3-B-KYBOUNDARY loop 3).
#
#   kyboundary.sh prepare <job_id>            build the verifier's VIEW of the job's worktree at the reviewed head and the
#                                             record S/boundary.json. 0 ready · 1 not established · 64 usage
#   kyboundary.sh exec <job_id> -- <argv…>    cd to the view and BECOME argv inside the boundary (same pid, process group
#                                             and session; every descendant inherits it). 70 = boundary absent or altered
#   kyboundary.sh check <job_id>              after the job's group is gone: print the boundary evidence of §6 and write
#                                             the same to S/boundary.check.json. 0 intact · 1 violated · 3 unknown
#   kyboundary.sh release <job_id>            remove the view; idempotent; 0 only when it is verifiably absent
#
# S = the state's job_scratch. Read from $KY_RUN/jobs/<job_id>/state.json: worktree, head, slot, job_scratch, tmp_path —
# nothing else. $KY_ROOT, $KY_RUN, $KY_FLEET and $HOME come from the caller's environment (plan §7 defaults); $HOME
# only names places that are never writable.
#
# THE MECHANISM: "seatbelt-file-write-deny/1" — the job runs under /usr/bin/sandbox-exec with a profile generated from the
# record at every `exec` (never stored, so there is no profile file to tamper with):
#     (allow default) (deny file-write*) (allow file-write* <writable[]> <a few /dev nodes>)
#     (deny file-write* <the view> <S itself> <S/boundary.json> <S/boundary.check.json> <S/snapshot.json>
#                       <S/boundary.json.tmp.*> <S/boundary.check.json.tmp.*>)
# The kernel applies it to the process and to every descendant; a sandboxed process cannot drop or loosen it (a nested
# sandbox-exec only adds rules). file-write* covers data, create, unlink, rename, mode, flags, xattr, times and link, so
# chmod, chflags, replace-by-rename, delete-and-recreate and hard links are denied by the same rule as a plain edit. It
# is path-based, so it protects the view AND every path outside writable[]: the item worktree, the shared repository,
# $KY_RUN, $KY_FLEET, $KY_ROOT/bin, other jobs' scratch, ~/Library/LaunchAgents. "S itself" is denied (its children are
# not) so the scratch cannot be renamed into a writable place, taking the view with it.
#   The VIEW is S/view: a scratch checkout (`git init` + objects borrowed read-only through objects/info/alternates +
# every ref of the item repository + a detached checkout of the head). It is never a registered worktree, has no remote,
# and its .git is a directory inside the view, so the Git metadata the job sees is under the same deny rule.
#   writable[] is exactly: S, S/cache (the named cache directory), tmp_path (TMPDIR), and S/program — the model
# program's own config and session store, made by `prepare` for this job alone (kyjob.sh points the program at it,
# for Claude Code CLAUDE_CONFIG_DIR=S/program inside its `env -i`). Every entry is this job's own. NOTHING under $HOME is
# writable: not $HOME/.claude.json, and no part of $HOME/.claude — its settings.json would let a job plant a hook or an
# MCP server, and its shell-snapshots, session-env, projects/*/memory and file-history are sourced, loaded or restored
# by every unconfined session of the same user, so a write there runs the job's code OUTSIDE the boundary (review
# KB-R2-01). `prepare` refuses a state whose S or tmp_path overlaps $HOME/.claude or $HOME/.claude.json. Whether the
# real program signs in and runs with its store redirected, and writes nothing else outside writable[], is proven at
# B-2 requalification, not here: here a fake program stands in (packet). The slot DB is loopback TCP, not a path.
#
# WHAT WAS TRIED (ruling P20: first those needing no administrator action), each judged by tests/test_kyboundary.py on
# macOS 27.0.1 (26A434) — the tests are the record, this is its summary:
#   0. same-user chmod only (the control)  → REJECTED. Plain edits fail; chmod-then-write, chmod-the-directory-then-
#      create and -replace succeed (test_control_a_chmod_only_view_is_defeated_and_the_mechanism_rejected).
#   1. the head on a read-only disk image, alone  → REJECTED. Inside the mount all 19 file attacks fail whatever the mode
#      bits, but (a) a path outside the view is unprotected (the $KY_RUN write succeeds) and (b) the same user detaches
#      the image and attaches it writable with no administrator action, then edits the file
#      (test_candidate_read_only_image_alone_is_rejected).
#   2. a Seatbelt profile around the job, alone  → ACCEPTED, and chosen. Every attack fixture fails with all bytes under
#      the test base unchanged and `check` 0; every declared write, git log/diff/status, reading every tracked file and a
#      loopback TCP connection work; the group kill reaches a TERM-ignoring child (test_attack_fails_inside_the_boundary
#      and the tests after it). sandbox-exec is deprecated by Apple: on this host it enforces, and `prepare`, `exec` and
#      `check` each PROBE that it does (under the generated profile a write into a fresh directory of S must succeed and
#      one into the view fail) rather than assume it — a sandbox-exec that runs the command unconfined gives 1 / 70 /
#      violated
#      (test_prepare_is_not_established_when_the_sandbox_does_not_enforce).
#   1+2. the image under the profile  → passes, NOT chosen: the mount adds no layer the job cannot remove. `hdiutil
#      detach` run INSIDE the profile succeeds (the unmount is done by a system daemon, not by the job's process), after
#      which only the profile's path rule still denies the write
#      (test_candidate_read_only_image_under_the_profile_adds_no_layer_the_job_cannot_remove). It would add an image and
#      a mount to leave behind, and nothing a fixture can show.
#   A dedicated OS user was not needed and not tried (owner hard stop, ruling P20).
#
# WHAT THIS DOES NOT CLAIM (no fixture here can show it, so it is not asserted):
#   · The profile confines the job's own processes. It does not stop the job from ASKING an unconfined process of the
#     same user to write for it (the detach above is such a request; launchd and Apple events are others — untested
#     here: the real launchctl is prohibited in this packet). Such a write to the view or the item worktree is still
#     caught afterwards by `check`; one to $KY_RUN, $KY_FLEET or $KY_ROOT/bin is not. Closing that class needs the
#     dedicated OS user (an owner action) or a deny-by-default profile proven against the real program (B-2).
#   · `check` observes the view (HEAD, status, tracked hashes, and a hash of its whole .git) and the item worktree
#     (HEAD commit and branch, status, tracked hashes). It does not fingerprint the repository's SHARED Git metadata
#     (config, hooks, refs/stash, other worktrees): other jobs change it legitimately. There the write-denial is the
#     protection, and the fixtures show the denial.
#   · Network access is not narrowed (the model program needs it).
#
# INTERPRETATION (packet): `prepare` requires the item worktree to be clean and AT the reviewed head, and the view's
# tracked bytes to equal the worktree's, so one tracked_sha256 is the baseline of both. An existing view is verified,
# never rebuilt over: altered → 1 until `release`. boundary.json carries one key beyond the packet's seven, `git_state`
# {view_git_sha256, worktree_head_ref}: the baseline `check` needs for the view's Git metadata and the worktree's branch.
# tracked_sha256 = sha256 over, for each tracked path in byte order, `<path> NUL <sha256 hex> LF`, where the second is
# the sha256 of the work-tree file's bytes (a symlink: of "link:" + its target).
# CONTROLLER-SIDE WRITES INSIDE S (S is the job's to write): never through a name the job can create. The record and
# the check file are written to an unpredictable temporary name created O_CREAT|O_EXCL|O_NOFOLLOW (a planted file or
# link there is refused, never followed), renamed into place and confirmed to be that same regular file; any refusal
# is 1 (prepare) / unknown (check). The profile also denies the job those temporary names. The probe works in a fresh
# directory of S with an unpredictable name and removes what it made through a descriptor of that directory, so a
# link the job put in S (its cache, say) is neither written nor removed through.
# KY_BOUNDARY_SANDBOX_EXEC is honoured only with the tests-only gate KY_BOUNDARY_TEST_OVERRIDE=1, and then the mechanism
# is recorded as "test-override:…", which `exec` refuses and `check` never reports intact.
#
# Changelog: v1.0 (2026-10-12) first version. v1.1 (2026-10-12) review KB-R1-01: the controller no longer writes
# through a link planted at its predictable temporary name (write_json, the probe); the profile denies those names.
# v1.2 (2026-10-12) review KB-R2-01: writable[] no longer grants the shared $HOME/.claude/* directories; the program's
# store is the per-job S/program, and $HOME/.claude and $HOME/.claude.json join the paths no writable may overlap.
set -u
PY=/opt/homebrew/bin/python3
[ -x "$PY" ] || PY=/usr/bin/python3
IFS= read -r -d '' KYBOUNDARY_PY <<'PYEOF'
import datetime, hashlib, json, os, re, secrets, shutil, stat, subprocess, sys

SCHEMA, CHECK_SCHEMA = "ky.boundary/1", "ky.boundary_check/1"
MECHANISM = "seatbelt-file-write-deny/1"
ACCEPTED = (MECHANISM,)          # the mechanisms the fixtures accepted; anything else is never ready and never intact
SANDBOX_EXEC = "/usr/bin/sandbox-exec"
if os.environ.get("KY_BOUNDARY_TEST_OVERRIDE") == "1" and os.environ.get("KY_BOUNDARY_SANDBOX_EXEC"):
    SANDBOX_EXEC = os.environ["KY_BOUNDARY_SANDBOX_EXEC"]
    MECHANISM = "test-override:" + SANDBOX_EXEC
SCRATCH_DENIED = ("boundary.json", "boundary.check.json", "snapshot.json")     # the controller's files inside S
SCRATCH_DENIED_RE = r"/boundary(\.check)?\.json\.tmp\."                      # and its temporary names beside them
DEV_WRITABLE = ("/dev/null", "/dev/zero", "/dev/tty", "/dev/ptmx", "/dev/dtracehelper")
GIT = next((g for g in ("/opt/homebrew/bin/git", "/usr/bin/git") if os.access(g, os.X_OK)), None)
JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA = re.compile(r"^[0-9a-f]{40}$")


class NotEstablished(Exception):
    pass


def say(msg):
    sys.stderr.write("kyboundary: %s\n" % msg)


def usage():
    say("usage: kyboundary.sh prepare|check|release <job_id>  |  kyboundary.sh exec <job_id> -- <argv…>")
    sys.exit(64)


def inside(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


def abs_env(name, default):
    v = os.environ.get(name) or default
    if not os.path.isabs(v):
        raise NotEstablished("%s is not an absolute path" % name)
    return os.path.realpath(v)


def load(job_id):
    """the state's five keys and every path the boundary is made of, canonical and absolute"""
    ky_root = abs_env("KY_ROOT", "/Users/Dev/kalayantra")
    ky_run = abs_env("KY_RUN", os.path.join(ky_root, "run"))
    ky_fleet = abs_env("KY_FLEET", os.path.join(ky_root, "fleet_live"))
    home = abs_env("HOME", "")
    try:
        with open(os.path.join(ky_run, "jobs", job_id, "state.json")) as f:
            st = json.load(f)
    except (OSError, ValueError) as e:
        raise NotEstablished("state: unreadable (%s)" % e)
    if not isinstance(st, dict):
        raise NotEstablished("state: not an object")
    p = {"job_id": job_id, "head": st.get("head")}
    for key in ("worktree", "job_scratch", "tmp_path"):
        v = st.get(key)
        if not isinstance(v, str) or not os.path.isabs(v) or re.search(r"[\x00-\x1f]", v):
            raise NotEstablished("state: %s is not an absolute path" % key)
        if inside(v, "/tmp") or inside(os.path.realpath(v), "/private/tmp"):
            raise NotEstablished("state: %s is under /tmp" % key)
        p[key] = os.path.realpath(v)
    if re.search(r'[\[\]\\^"]', p["job_scratch"]):
        raise NotEstablished("state: job_scratch has a character the profile cannot express: %s" % p["job_scratch"])
    if p["head"] is not None and not (isinstance(p["head"], str) and SHA.match(p["head"])):
        raise NotEstablished("state: head is neither null nor a 40-hex commit")
    S = p["job_scratch"]
    p["view"], p["cache"], p["program"] = os.path.join(S, "view"), os.path.join(S, "cache"), os.path.join(S, "program")
    p["record"], p["check"] = os.path.join(S, "boundary.json"), os.path.join(S, "boundary.check.json")
    p["writable"] = [S, p["cache"], p["tmp_path"], p["program"]]          # this job's own, nothing shared (KB-R2-01)
    p["protected"] = [p["worktree"], ky_run, ky_fleet, os.path.join(ky_root, "bin"),
                      os.path.join(home, "Library", "LaunchAgents"), os.path.join(home, ".claude"),
                      os.path.join(home, ".claude.json")]
    return p


def validate_layout(p):
    for name in ("job_scratch", "tmp_path", "worktree"):
        if not os.path.isdir(p[name]):
            raise NotEstablished("state: %s is not a directory: %s" % (name, p[name]))
    for w in p["writable"]:
        for q in p["protected"] + [p["common"]]:
            if inside(w, q) or inside(q, w):
                raise NotEstablished("a writable path and a protected path overlap: %s / %s" % (w, q))
        if inside(w, p["view"]):
            raise NotEstablished("a writable path is inside the view: %s" % w)


# ── observation ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def git(tree, *args):
    """(exit, stdout bytes); never takes a lock, runs no hook, and is None when Git itself cannot be run"""
    env = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": os.environ.get("HOME", "/nonexistent"),
           "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}
    try:
        r = subprocess.run([GIT, "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", tree] + list(args),
                           env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900)
    except (OSError, TypeError, subprocess.SubprocessError):
        return None, b""
    return r.returncode, r.stdout


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tracked_sha256(tree):
    rc, out = git(tree, "ls-files", "-z")
    if rc != 0:
        return None
    h = hashlib.sha256()
    try:
        for path in sorted(set(x for x in out.split(b"\0") if x)):
            full = os.path.join(os.fsencode(tree), path)
            st = os.lstat(full) if os.path.lexists(full) else None
            if st is None:
                digest = "absent"
            elif stat.S_ISLNK(st.st_mode):
                digest = hashlib.sha256(b"link:" + os.readlink(full)).hexdigest()
            elif stat.S_ISREG(st.st_mode):
                digest = file_sha256(full)
            else:
                digest = "not-a-file"
            h.update(path + b"\0" + digest.encode() + b"\n")
    except OSError:
        return None
    return h.hexdigest()


def tree_sha256(root):
    """sha256 over every entry under root (kind, mode, bytes or link target), or None when any of it cannot be read"""
    h = hashlib.sha256()
    failed = []
    try:
        for d, dirs, files in os.walk(os.fsencode(root), onerror=failed.append):
            dirs.sort()
            for name in sorted(dirs + files):
                full = os.path.join(d, name)
                st = os.lstat(full)
                if stat.S_ISLNK(st.st_mode):
                    body = b"link:" + os.readlink(full)
                elif stat.S_ISDIR(st.st_mode):
                    body = b"dir"
                elif stat.S_ISREG(st.st_mode):
                    body = file_sha256(full).encode()
                else:
                    body = b"other"
                h.update(os.path.relpath(full, os.fsencode(root)) + b"\0" + oct(stat.S_IMODE(st.st_mode)).encode() + b"\0" + body + b"\n")
    except OSError:
        return None
    return None if failed else h.hexdigest()


OBSERVED = {}        # one observation of each tree per run


def observe(tree):
    """what can be seen of a work tree now; each value None when it could not be observed"""
    if tree in OBSERVED:
        return OBSERVED[tree]
    o = OBSERVED[tree] = {"present": os.path.isdir(tree), "ref_seen": False, "ref": None, "head": None, "status": None,
                          "tracked": None}
    if not o["present"] or GIT is None:
        return o
    rc, out = git(tree, "rev-parse", "--show-toplevel")
    o["toplevel"] = os.path.realpath(os.fsdecode(out).rstrip("\n")) if rc == 0 else None
    rc, out = git(tree, "symbolic-ref", "-q", "HEAD")
    if rc in (0, 1):                                   # 1 = detached
        o["ref_seen"], o["ref"] = True, (os.fsdecode(out).strip() if rc == 0 else None)
    rc, out = git(tree, "rev-parse", "--verify", "-q", "HEAD^{commit}")
    if rc == 0:
        o["head"] = out.decode().strip()
    rc, out = git(tree, "status", "--porcelain", "-z", "--untracked-files=all")
    if rc == 0:
        o["status"] = os.fsdecode(out)
    o["tracked"] = tracked_sha256(tree)
    return o


# ── the mechanism ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def sb(path):
    return '"%s"' % path.replace("\\", "\\\\").replace('"', '\\"')


def profile(p, writable):
    S = p["job_scratch"]
    allow = " ".join("(subpath %s)" % sb(w) for w in writable) + " " + " ".join("(literal %s)" % sb(d) for d in DEV_WRITABLE)
    deny = "(subpath %s) (literal %s) " % (sb(p["view"]), sb(S)) + " ".join("(literal %s)" % sb(os.path.join(S, n)) for n in SCRATCH_DENIED)
    deny += ' (regex #"^%s%s")' % ("".join("[%s]" % c if c in ".*+?(){}|$" else c for c in S), SCRATCH_DENIED_RE)
    return ("(version 1)\n(allow default)\n(deny file-write*)\n"
            "(allow file-write* %s (regex #\"^/dev/ttys[0-9]+$\") (regex #\"^/dev/fd/[0-9]+$\"))\n"
            "(deny file-write* %s)\n" % (allow, deny))


def enforces(p, writable):
    """the detector behind `ready`: under the generated profile a write into a fresh directory of S succeeds and one into
    the view fails. Both names are unpredictable; what the probe made is examined and removed through a descriptor of
    the directory it created, never through a path the job could have redirected. True / False, or None when the probe
    itself could not be run"""
    tag = ".kyboundary-probe-" + secrets.token_hex(16)
    box, bad = os.path.join(p["job_scratch"], tag), os.path.join(p["view"], tag)
    script = 'echo p > "$1" 2>/dev/null && echo CACHE_WRITTEN; echo p > "$2" 2>/dev/null && echo VIEW_WRITTEN; exit 0'
    try:
        os.mkdir(box, 0o700)
        fd = os.open(box, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return None
    try:
        r = subprocess.run([SANDBOX_EXEC, "-p", profile(p, writable), "/bin/sh", "-c", script, "sh",
                            os.path.join(box, "w"), bad],
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
                           env={"PATH": "/usr/bin:/bin"})
        words = r.stdout.decode(errors="replace").split()
        leaked = os.path.lexists(bad)
        if leaked:
            os.unlink(bad)
        names = os.listdir(fd)
        wrote = names == ["w"] and stat.S_ISREG(os.stat("w", dir_fd=fd, follow_symlinks=False).st_mode)
        for name in names:
            os.unlink(name, dir_fd=fd)
        os.rmdir(box)
    except (OSError, subprocess.SubprocessError):
        return None
    finally:
        os.close(fd)
    if leaked or "VIEW_WRITTEN" in words:
        return False
    return True if (r.returncode == 0 and words == ["CACHE_WRITTEN"] and wrote) else None


def read_record(p):
    try:
        with open(p["record"]) as f:
            rec = json.load(f)
    except (OSError, ValueError):
        return None
    return rec if isinstance(rec, dict) else None


def record_faults(p, rec):
    """why the record is not the boundary this state describes ([] = it is)"""
    if rec is None:
        return ["no readable %s" % p["record"]]
    faults = []
    if rec.get("schema") != SCHEMA:
        faults.append("schema is not %s" % SCHEMA)
    if rec.get("mechanism") != MECHANISM or MECHANISM not in ACCEPTED:
        faults.append("mechanism %r is not the accepted %r" % (rec.get("mechanism"), ACCEPTED[0]))
    if rec.get("view") != p["view"]:
        faults.append("view is not %s" % p["view"])
    if rec.get("writable") != p["writable"]:
        faults.append("writable[] is not the declared list")
    if not (isinstance(rec.get("head"), str) and SHA.match(rec["head"])) or (p["head"] is not None and rec["head"] != p["head"]):
        faults.append("head is not the state's")
    if not isinstance(rec.get("tracked_sha256"), str) or not isinstance(rec.get("git_state"), dict):
        faults.append("no baseline")
    return faults


def view_faults(p, rec, files=True):
    """why the view is not as prepared ([] = it is); a fault that is only unobservable starts with '?'. files=False
    leaves out what `check` reports under its own keys (HEAD, status, tracked hashes): the mechanism alone"""
    view = p["view"]
    if os.path.islink(view) or not os.path.isdir(view) or os.path.ismount(view) or not os.path.isdir(os.path.join(view, ".git")):
        return ["the view is not a plain directory with its own .git: %s" % view]
    faults = []
    o = observe(view)
    if o.get("toplevel") != view:
        faults.append("the view is not the top of its own work tree")
    if files and (not o["ref_seen"] or o["ref"] is not None or o["head"] != rec["head"]):
        faults.append("the view is not detached at %s" % rec["head"])
    if files and (o["status"] is None or o["tracked"] is None):
        faults.append("?the view cannot be read")
    elif files and (o["status"] != "" or o["tracked"] != rec["tracked_sha256"]):
        faults.append("the view's files are not the prepared ones")
    meta = tree_sha256(os.path.join(view, ".git"))
    if meta is None:
        faults.append("?the view's Git metadata cannot be read")
    elif meta != rec["git_state"].get("view_git_sha256"):
        faults.append("the view's Git metadata changed")
    e = enforces(p, p["writable"])
    if e is not True:
        faults.append(("?the sandbox probe could not be run" if e is None else "sandbox-exec does not enforce the profile"))
    return faults


def remove_view(p):
    view = p["view"]
    if os.path.islink(view):
        os.unlink(view)
    elif os.path.ismount(view):
        raise NotEstablished("%s is a mount point: not removed" % view)
    elif os.path.isdir(view):
        def retry(func, path, _exc):
            os.chmod(os.path.dirname(path), 0o700)
            os.chmod(path, 0o700)
            func(path)
        shutil.rmtree(view, onerror=retry)
    elif os.path.lexists(view):
        os.unlink(view)
    return not os.path.lexists(view)


def write_json(path, doc):
    """never through a name the job can create: an unpredictable temporary name created O_CREAT|O_EXCL|O_NOFOLLOW (an
    existing file or link there is refused, not followed), renamed into place, then confirmed to be that same regular
    file. Any refusal raises OSError"""
    tmp = "%s.tmp.%s" % (path, secrets.token_hex(16))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        with open(fd, "w") as f:
            json.dump(doc, f, indent=1)
            f.write("\n")
            f.flush()
            made = os.fstat(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.lexists(tmp):
            os.unlink(tmp)
        raise
    st = os.lstat(path)
    if not stat.S_ISREG(st.st_mode) or (st.st_dev, st.st_ino) != (made.st_dev, made.st_ino):
        raise OSError("%s is not the regular file this run wrote" % path)


# ── the verbs ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def prepare(job_id):
    try:
        p = load(job_id)
        if GIT is None:
            raise NotEstablished("git not found")
        if os.path.lexists(p["view"]):                 # verified, never rebuilt over
            rc, out = git(p["worktree"], "rev-parse", "--path-format=absolute", "--git-common-dir")
            p["common"] = os.path.realpath(os.fsdecode(out).rstrip("\n")) if rc == 0 else p["worktree"]
            validate_layout(p)
            rec = read_record(p)
            faults = record_faults(p, rec) or view_faults(p, rec)
            if faults:
                raise NotEstablished("a view exists and is not the prepared boundary (release it first): " + "; ".join(faults))
            return 0
    except NotEstablished as e:
        say("prepare: not established: %s" % e)
        return 1
    try:
        for stale in (p["record"], p["check"]):
            if os.path.lexists(stale):
                os.unlink(stale)
        w = observe(p["worktree"]) if os.path.isdir(p["worktree"]) else None
        if w is None or w.get("toplevel") != p["worktree"]:
            raise NotEstablished("state: worktree is not the top of a Git work tree: %s" % p["worktree"])
        head = p["head"] or w["head"]
        if w["head"] is None or w["head"] != head or not w["ref_seen"]:
            raise NotEstablished("the item worktree is not at the reviewed head %s (HEAD %s)" % (head, w["head"]))
        if w["status"] != "" or w["tracked"] is None:
            raise NotEstablished("the item worktree is not clean, or cannot be read")
        rc, out = git(p["worktree"], "rev-parse", "--path-format=absolute", "--git-common-dir")
        if rc != 0:
            raise NotEstablished("the item repository cannot be found")
        p["common"] = os.path.realpath(os.fsdecode(out).rstrip("\n"))
        validate_layout(p)
        os.makedirs(p["cache"], exist_ok=True)
        os.makedirs(p["program"], exist_ok=True)

        def must(*args, **kw):
            rc, out = git(kw.get("tree", p["view"]), *args)
            if rc != 0:
                raise NotEstablished("git %s failed in the view" % args[0])
        os.mkdir(p["view"])
        must("-c", "init.defaultBranch=kyboundary-unborn", "init", "-q", "--template=", ".")
        with open(os.path.join(p["view"], ".git", "objects", "info", "alternates"), "w") as f:
            f.write(os.path.join(p["common"], "objects") + "\n")
        must("fetch", "-q", "--no-tags", "--update-head-ok", "--no-write-fetch-head", p["common"],
             "+refs/heads/*:refs/heads/*", "+refs/remotes/*:refs/remotes/*", "+refs/tags/*:refs/tags/*")
        must("-c", "advice.detachedHead=false", "checkout", "-q", "--detach", head)
        v = observe(p["view"])
        if v["head"] != head or v["ref"] is not None or v["status"] != "" or v["tracked"] is None:
            raise NotEstablished("the view is not a clean checkout of %s" % head)
        if v["tracked"] != w["tracked"]:
            raise NotEstablished("the view's tracked bytes differ from the item worktree's")
        meta = tree_sha256(os.path.join(p["view"], ".git"))
        if meta is None:
            raise NotEstablished("the view's Git metadata cannot be read")
        if MECHANISM not in ACCEPTED:
            say("prepare: tests-only override in force: mechanism %s" % MECHANISM)
        e = enforces(p, p["writable"])
        if e is not True:
            raise NotEstablished("sandbox-exec does not enforce the profile on this host (probe: %s)" % ("not run" if e is None else "the view was writable"))
        write_json(p["record"], {
            "schema": SCHEMA, "mechanism": MECHANISM, "view": p["view"], "writable": p["writable"], "head": head,
            "tracked_sha256": v["tracked"], "prepared_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "git_state": {"view_git_sha256": meta, "worktree_head_ref": w["ref"]}})
        if MECHANISM not in ACCEPTED:
            raise NotEstablished("mechanism %s is not an accepted boundary" % MECHANISM)
        return 0
    except (NotEstablished, OSError) as e:             # a partial boundary is never ready: undo it
        say("prepare: not established: %s" % e)
        try:
            if os.path.lexists(p["record"]):
                os.unlink(p["record"])
            remove_view(p)
        except (NotEstablished, OSError) as e2:
            say("prepare: and the partial view could not be removed: %s" % e2)
        return 1


def exec_(job_id, argv):
    try:
        p = load(job_id)
        rec = read_record(p)
        faults = record_faults(p, rec) or view_faults(p, rec)
        if faults:
            raise NotEstablished("; ".join(f.lstrip("?") for f in faults))
        os.chdir(p["view"])
        sys.stdout.flush()
        sys.stderr.flush()
        os.execv(SANDBOX_EXEC, [SANDBOX_EXEC, "-p", profile(p, p["writable"])] + argv)
    except (NotEstablished, OSError) as e:
        say("exec: the prepared boundary is absent or altered: %s" % e)
    return 70


def check(job_id):
    doc = {"schema": CHECK_SCHEMA, "job_id": job_id, "mechanism": None, "head_unchanged": None, "status_clean": None,
           "tracked_hashes_unchanged": None, "mechanism_intact": None, "result": "unknown", "view": None, "worktree": None,
           "reasons": [], "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    keys = ("head_unchanged", "status_clean", "tracked_hashes_unchanged")
    p = None
    try:
        p = load(job_id)
        if os.path.lexists(p["check"]):                # whatever is there is not this check's
            os.unlink(p["check"])
        rec = read_record(p)
        faults = record_faults(p, rec)
        if rec is not None:
            doc["mechanism"] = rec.get("mechanism")
        if faults:
            doc["mechanism_intact"] = False
            doc["reasons"] += faults
        else:
            vf = view_faults(p, rec, files=False)
            doc["reasons"] += [f.lstrip("?") for f in vf]
            doc["mechanism_intact"] = False if any(not f.startswith("?") for f in vf) else (None if vf else True)
            for side, tree, ref in (("view", p["view"], None), ("worktree", p["worktree"], rec["git_state"].get("worktree_head_ref"))):
                o = observe(tree)
                if not o["present"]:                   # it was there at prepare: its absence is a change, not a gap
                    d = dict.fromkeys(keys, False)
                    doc["reasons"].append("%s is gone: %s" % (side, tree))
                else:
                    d = {"head_unchanged": (False if (o["ref_seen"] and o["ref"] != ref) else
                                            (o["head"] == rec["head"] if (o["head"] is not None and o["ref_seen"]) else None)),
                         "status_clean": None if o["status"] is None else o["status"] == "",
                         "tracked_hashes_unchanged": None if o["tracked"] is None else o["tracked"] == rec["tracked_sha256"]}
                    if o["ref_seen"] and o["ref"] == ref and o["head"] is None and o["status"] is not None:
                        d["head_unchanged"] = False    # the same branch name, now without a commit
                doc[side] = dict(d, path=tree)
            for k in keys:
                both = [doc["view"][k], doc["worktree"][k]]
                doc[k] = False if False in both else (None if None in both else True)
    except NotEstablished as e:
        doc["reasons"].append(str(e))
    except OSError as e:
        doc["reasons"].append("check could not complete: %s" % e)
        doc["mechanism_intact"] = None
    verdicts = [doc[k] for k in keys + ("mechanism_intact",)]
    doc["result"] = "violated" if False in verdicts else ("intact" if all(v is True for v in verdicts) else "unknown")
    if p is not None and os.path.isdir(p["job_scratch"]):
        try:
            write_json(p["check"], doc)
        except OSError as e:                           # the controller is handed that file: without it nothing is intact
            doc["reasons"].append("%s could not be written: %s" % (p["check"], e))
            if doc["result"] == "intact":
                doc["result"] = "unknown"
    elif doc["result"] == "intact":
        doc["result"] = "unknown"
    print(json.dumps(doc, indent=1))
    return {"intact": 0, "violated": 1}.get(doc["result"], 3)


def release(job_id):
    try:
        p = load(job_id)
        return 0 if remove_view(p) else 1
    except (NotEstablished, OSError) as e:
        say("release: the view is not verifiably absent: %s" % e)
        return 1


def main(a):
    if len(a) < 2 or a[0] not in ("prepare", "exec", "check", "release") or not JOB_ID.match(a[1]):
        usage()
    if a[0] == "exec":
        if len(a) < 4 or a[2] != "--":
            usage()
        return exec_(a[1], a[3:])
    if len(a) != 2:
        usage()
    return {"prepare": prepare, "check": check, "release": release}[a[0]](a[1])


sys.exit(main(sys.argv[1:]))
PYEOF
exec "$PY" -I -B -c "$KYBOUNDARY_PY" "$@"
