#!/usr/bin/env python3
"""KĀLA-YANTRA v3 migration allocator (relaunch plan v2.7 §5 "Migration allocator", §7, §8.1; packet KV3-B-KYALLOC v1).

An atomic, persistent reservation of migration numbers keyed by (item, branch). Deterministic: every number and
every status comes from git and the store read in that very call; an unreadable source is an exit code, never a
number. Python >= 3.9, standard library only.

  python3 -I -B kyalloc.py reserve --item ID --branch B --repo R [--count N] [--ref REF] [--claims-ref REF]
  python3 -I -B kyalloc.py check   --repo R [--ref REF] [--claims-ref REF]
  python3 -I -B kyalloc.py release --item ID --branch B --reason TEXT
  python3 -I -B kyalloc.py show    [--item ID]

The one authority is $KY_RUN/alloc/migrations.json (KY_RUN defaults to ${KY_ROOT:-/Users/Dev/kalayantra}/run):

  {"schema": "ky.alloc/1", "reservations": [{"item", "branch", "numbers": [int],
    "status": "active" | "consumed" | "released" | "conflicted", "reserved_at",
    "observed": {"ref", "ref_commit", "disk_max", "claims_max", "claims_blob"},
    "conflict": null | {"number", "with"}}]}

Every mutation holds an exclusive flock on $KY_RUN/alloc/.lock, re-reads the store inside the lock, writes it as
temp + fsync + rename and then appends one line to $KY_RUN/alloc/journal.jsonl. A call that changes nothing writes
nothing. A store that cannot be read and validated is never rewritten; a store that is missing while the journal
shows numbers were issued is unreadable too, not empty.

Namespace (the packet's interpretation of "repository-wide migration namespace"): the numbers of the files named
`<digits>_…` directly in platform/migrations/ and platform/supabase/migrations/ at --ref (default origin/main);
the rows under "## 2. MIGRATION NUMBER CLAIMS" of 00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md at --claims-ref
(default origin/campaign-coordination), a first cell being a number, a range or a list of them; and every number
this store ever reserved, whatever its status. A new reservation is N consecutive numbers from the namespace
max + 1: gaps are never filled, a number claimed on the table is never handed out, and there is no adoption verb.
The namespace is unreadable (exit 4) when a ref does not resolve, the claim section is missing, duplicated or
without a claim row, a claim row's number cell is not understood, or --ref holds no numbered migration at all.

Status (applied by `reserve` and `check` to every active reservation; the other statuses are not re-judged):
  conflicted — a reserved number is at --ref under a migration path that is not in the reservation's own branch
               (refs/remotes/origin/B, else refs/heads/B), or under two paths, or beside a migration with that
               number in the own branch that is not at --ref; or a claim-table row names it without the exact
               token `kyalloc:ID@B`. Both parties are recorded; the numbers are neither renumbered nor reissued.
  consumed   — no reserved number is conflicted and at least one is at --ref under its own branch's path.
`claim_row` is the ready-to-paste claim-table row carrying the token. Publishing it stays the existing procedure's
conductor action (platform/scripts/governance/reserve_migration_number.py); this script never writes the table.

git is ${KY_GIT:-/usr/bin/git}, run only as `rev-parse`, `ls-tree` and `show`; never a fetch, push or commit, so
the refs are as fresh as the caller's last fetch. Files are written only under $KY_RUN/alloc/.

Exit: 0 ok · 3 a reservation the call concerns is conflicted (`check`: any; `show`: any it prints) ·
4 namespace unreadable, nothing reserved · 5 store unreadable · 64 usage.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys

SCHEMA = "ky.alloc/1"
JOURNAL_SCHEMA = "ky.alloc.journal/1"
DEFAULT_ROOT = "/Users/Dev/kalayantra"
DEFAULT_GIT = "/usr/bin/git"
DEFAULT_REF = "origin/main"
DEFAULT_CLAIMS_REF = "origin/campaign-coordination"
GIT_VERBS = ("rev-parse", "ls-tree", "show")
GIT_TIMEOUT = 60
# one sequence over both directories, as the existing reservation procedure reads it
MIGRATION_DIRS = ("platform/migrations", "platform/supabase/migrations")
CLAIMS_PATH = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
CLAIM_TABLE_HEADER = "## 2. MIGRATION NUMBER CLAIMS"
STATUSES = ("active", "consumed", "released", "conflicted")
RECORD_KEYS = ("item", "branch", "numbers", "status", "reserved_at", "observed", "conflict")
OBSERVED_KEYS = ("ref", "ref_commit", "disk_max", "claims_max", "claims_blob")
MAX_COUNT = 100
WITH_MAX = 400
EX_OK, EX_CONFLICT, EX_NAMESPACE, EX_STORE, EX_USAGE = 0, 3, 4, 5, 64

ITEM_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
# no `@`, whitespace, `|` or backtick in either half, so the token `kyalloc:ID@B` reads back unambiguously
BRANCH_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*\Z")
OID_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
FILE_NUMBER_RE = re.compile(r"(\d+)_")
CELL_PART_RE = re.compile(r"(\d+)(?:\s*[–—-]\s*(\d+))?\+?\Z")
TOKEN_RE = re.compile(r"(?<![^\s|`])kyalloc:[^\s|`]+")


class Refusal(Exception):
    code = 1

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class Usage(Refusal):
    code = EX_USAGE


class NamespaceUnreadable(Refusal):
    code = EX_NAMESPACE


class StoreUnreadable(Refusal):
    code = EX_STORE


# ---------------------------------------------------------------- git (read-only)

def git(repo: str, verb: str, *args: str) -> tuple:
    if verb not in GIT_VERBS:
        raise AssertionError(f"git {verb} is not a read-only verb of this script")
    exe = os.environ.get("KY_GIT") or DEFAULT_GIT
    # a fixed environment: a caller's GIT_DIR or GIT_WORK_TREE cannot point the observation at another repository
    env = {"PATH": os.environ.get("PATH") or "/usr/bin:/bin", "HOME": os.environ.get("HOME") or "/",
           "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0"}
    try:
        p = subprocess.run([exe, verb, *args], cwd=repo, env=env, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NamespaceUnreadable(f"{exe} {verb} did not run in {repo}: {exc}")
    return p.returncode, p.stdout, p.stderr.decode("utf-8", "replace").strip()


def resolve(repo: str, spec: str):
    """the object id `spec` names, None when it names nothing"""
    rc, out, err = git(repo, "rev-parse", "--verify", "--quiet", spec)
    oid = out.decode("ascii", "replace").strip()
    if rc == 0 and OID_RE.match(oid):
        return oid
    if rc == 1 and not oid:
        return None
    raise NamespaceUnreadable(f"git rev-parse {spec} in {repo}: exit {rc} {err}")


def migration_paths(repo: str, commit: str) -> dict:
    """number -> the paths carrying it, over both migration directories of `commit`"""
    rc, out, err = git(repo, "ls-tree", "-z", "--full-tree", "--name-only", commit, *[d + "/" for d in MIGRATION_DIRS])
    if rc != 0:
        raise NamespaceUnreadable(f"git ls-tree {commit} in {repo}: exit {rc} {err}")
    found: dict = {}
    for raw in out.split(b"\0"):
        path = raw.decode("utf-8", "backslashreplace")
        folder, _, name = path.rpartition("/")
        m = FILE_NUMBER_RE.match(name)
        if folder in MIGRATION_DIRS and m:
            found.setdefault(int(m.group(1)), []).append(path)
    return {n: sorted(paths) for n, paths in found.items()}


def parse_claims(text: str) -> list:
    """the claim rows of the one claim section as (low, high, row); refuses what it does not understand"""
    rows, sections, inside = [], 0, False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(CLAIM_TABLE_HEADER):
            sections, inside = sections + 1, True
            continue
        if inside and line.startswith("## "):
            inside = False
        if not inside or not line.startswith("|"):
            continue
        cell = re.sub(r"[*`_~]", "", line.split("|")[1]).strip()
        if not re.search(r"\d", cell):
            continue  # the header, the separator, a ruling row without a number
        for part in cell.split(","):
            m = CELL_PART_RE.match(part.strip())
            if not m:
                raise NamespaceUnreadable(f"claim table: number cell not understood in row {line[:120]!r}")
            low = int(m.group(1))
            high = int(m.group(2)) if m.group(2) else low
            if high < low:
                raise NamespaceUnreadable(f"claim table: reversed range in row {line[:120]!r}")
            rows.append((low, high, line))
    if sections != 1:
        raise NamespaceUnreadable(f"claim table: {sections} sections {CLAIM_TABLE_HEADER!r}, expected one")
    if not rows:
        raise NamespaceUnreadable("claim table: the section holds no claim row")
    return rows


class Observation:
    """the namespace outside the store, read once per call"""

    def __init__(self, repo: str, ref: str, claims_ref: str):
        self.repo, self.ref, self.claims_ref = repo, ref, claims_ref
        self.ref_commit = resolve(repo, ref + "^{commit}")
        if self.ref_commit is None:
            raise NamespaceUnreadable(f"ref {ref} does not resolve to a commit in {repo}")
        self.ref_paths = migration_paths(repo, self.ref_commit)
        if not self.ref_paths:
            raise NamespaceUnreadable(f"no numbered migration under {' or '.join(MIGRATION_DIRS)} at {ref}")
        self.claims_blob = resolve(repo, f"{claims_ref}:{CLAIMS_PATH}")
        if self.claims_blob is None:
            raise NamespaceUnreadable(f"{claims_ref}:{CLAIMS_PATH} does not resolve in {repo}")
        rc, out, err = git(repo, "show", self.claims_blob)
        if rc != 0:
            raise NamespaceUnreadable(f"git show {self.claims_blob} in {repo}: exit {rc} {err}")
        try:
            text = out.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise NamespaceUnreadable(f"claim table at {claims_ref} is not UTF-8: {exc}")
        self.claim_rows = parse_claims(text)
        self.disk_max = max(self.ref_paths)
        self.claims_max = max(high for _, high, _ in self.claim_rows)
        self._branches: dict = {}

    def record(self) -> dict:
        return {"ref": self.ref, "ref_commit": self.ref_commit, "disk_max": self.disk_max,
                "claims_max": self.claims_max, "claims_blob": self.claims_blob}

    def branch_paths(self, branch: str) -> dict:
        """the migration paths of the reservation's own branch: refs/remotes/origin/B, else refs/heads/B"""
        if branch not in self._branches:
            commit = (resolve(self.repo, f"refs/remotes/origin/{branch}^{{commit}}")
                      or resolve(self.repo, f"refs/heads/{branch}^{{commit}}"))
            self._branches[branch] = migration_paths(self.repo, commit) if commit else {}
        return self._branches[branch]

    def judge(self, rec: dict) -> tuple:
        """(status, conflict) of an active reservation under this observation"""
        token = f"kyalloc:{rec['item']}@{rec['branch']}"
        consumed = False
        for n in rec["numbers"]:
            at_ref = self.ref_paths.get(n, [])
            if at_ref:
                own = self.branch_paths(rec["branch"]).get(n, [])
                foreign = [p for p in at_ref if p not in own]
                unmerged = [p for p in own if p not in at_ref]
                where = f"ref {self.ref}@{self.ref_commit}: "
                if foreign:
                    return "conflicted", conflict(n, where + foreign[0])
                if len(at_ref) > 1:
                    return "conflicted", conflict(n, where + " and ".join(at_ref))
                if unmerged:
                    return "conflicted", conflict(n, where + f"{at_ref[0]} beside unmerged {unmerged[0]} of the own branch")
                consumed = True
            for low, high, row in self.claim_rows:
                if low <= n <= high and token not in TOKEN_RE.findall(row):
                    return "conflicted", conflict(n, f"claims {self.claims_ref}@{self.claims_blob}: {row}")
        return ("consumed" if consumed else "active"), None


def conflict(number: int, other: str) -> dict:
    return {"number": number, "with": other if len(other) <= WITH_MAX else other[:WITH_MAX - 1] + "…"}


# ---------------------------------------------------------------- the store

def run_dir() -> str:
    path = os.environ.get("KY_RUN") or os.path.join(os.environ.get("KY_ROOT") or DEFAULT_ROOT, "run")
    if not os.path.isabs(path) or not os.path.isdir(path):
        raise Usage(f"KY_RUN {path!r} is not an existing absolute directory")
    return path


class Alloc:
    def __init__(self):
        self.dir = os.path.join(run_dir(), "alloc")
        self.store = os.path.join(self.dir, "migrations.json")
        self.temp = os.path.join(self.dir, "migrations.json.tmp")
        self.journal = os.path.join(self.dir, "journal.jsonl")
        self.lock = os.path.join(self.dir, ".lock")

    @contextlib.contextmanager
    def locked(self):
        try:
            os.makedirs(self.dir, exist_ok=True)
            fd = os.open(self.lock, os.O_RDWR | os.O_CREAT, 0o644)
        except OSError as exc:
            raise StoreUnreadable(f"cannot open the lock {self.lock}: {exc}")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)  # closing releases the lock

    def load(self) -> dict:
        try:
            with open(self.store, "rb") as fh:
                raw = fh.read()
        except FileNotFoundError:
            try:
                issued = os.path.getsize(self.journal) > 0
            except FileNotFoundError:
                issued = False
            except OSError as exc:
                raise StoreUnreadable(f"cannot read {self.journal}: {exc}")
            if issued:
                raise StoreUnreadable(f"{self.store} is missing but {self.journal} records issued numbers")
            return {"schema": SCHEMA, "reservations": []}
        except OSError as exc:
            raise StoreUnreadable(f"cannot read {self.store}: {exc}")
        try:
            doc = json.loads(raw.decode("utf-8"))
        except ValueError as exc:
            raise StoreUnreadable(f"{self.store} is not JSON: {exc}")
        problem = store_problem(doc)
        if problem:
            raise StoreUnreadable(f"{self.store} is not a {SCHEMA} store: {problem}")
        return doc

    def commit(self, doc: dict, verb: str, changes: list, observed, reason=None) -> None:
        """temp + fsync + rename, then one journal line; the caller holds the lock"""
        problem = store_problem(doc)
        if problem:
            raise StoreUnreadable(f"refusing to write an invalid store: {problem}")
        data = render(doc)
        line = {"schema": JOURNAL_SCHEMA, "at": now(), "verb": verb, "changes": changes, "observed": observed,
                "reason": reason, "store_sha256": hashlib.sha256(data).hexdigest()}
        try:
            write_synced(self.temp, data, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            os.replace(self.temp, self.store)
            sync_dir(self.dir)
            write_synced(self.journal, (json.dumps(line) + "\n").encode("ascii"), os.O_WRONLY | os.O_CREAT | os.O_APPEND)
        except OSError as exc:
            raise StoreUnreadable(f"cannot write under {self.dir}: {exc}")


def write_synced(path: str, data: bytes, flags: int) -> None:
    fd = os.open(path, flags | os.O_NOFOLLOW, 0o644)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
    finally:
        os.close(fd)


def sync_dir(path: str) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def render(doc: dict) -> bytes:
    return (json.dumps(doc, indent=2) + "\n").encode("ascii")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_int(value) -> bool:
    return type(value) is int


def store_problem(doc):
    """None for a valid store, else what is wrong with it"""
    if not isinstance(doc, dict) or sorted(doc) != ["reservations", "schema"]:
        return "top level is not {schema, reservations}"
    if doc["schema"] != SCHEMA:
        return f"schema is {doc['schema']!r}"
    if not isinstance(doc["reservations"], list):
        return "reservations is not a list"
    held: set = set()
    live: set = set()
    for i, rec in enumerate(doc["reservations"]):
        at = f"reservation {i}"
        if not isinstance(rec, dict) or sorted(rec) != sorted(RECORD_KEYS):
            return f"{at}: keys are not {list(RECORD_KEYS)}"
        if not (isinstance(rec["item"], str) and ITEM_RE.match(rec["item"])
                and isinstance(rec["branch"], str) and BRANCH_RE.match(rec["branch"])):
            return f"{at}: item or branch"
        numbers = rec["numbers"]
        if not (isinstance(numbers, list) and numbers and all(is_int(n) and n > 0 for n in numbers)
                and numbers == list(range(numbers[0], numbers[0] + len(numbers)))):
            return f"{at}: numbers are not consecutive positive integers"
        if rec["status"] not in STATUSES or not isinstance(rec["reserved_at"], str):
            return f"{at}: status or reserved_at"
        obs = rec["observed"]
        if not (isinstance(obs, dict) and sorted(obs) == sorted(OBSERVED_KEYS)
                and all(isinstance(obs[k], str) for k in ("ref", "ref_commit", "claims_blob"))
                and is_int(obs["disk_max"]) and is_int(obs["claims_max"])):
            return f"{at}: observed"
        con = rec["conflict"]
        if con is not None and not (isinstance(con, dict) and sorted(con) == ["number", "with"]
                                    and is_int(con["number"]) and isinstance(con["with"], str)):
            return f"{at}: conflict"
        if rec["status"] == "conflicted" and con is None:
            return f"{at}: conflicted without a conflict"
        if held & set(numbers):
            return f"{at}: a number is held by two reservations"
        held |= set(numbers)
        key = (rec["item"], rec["branch"])
        if rec["status"] != "released":
            if key in live:
                return f"{at}: a second live reservation for {key}"
            live.add(key)
    return None


def live_record(doc: dict, item: str, branch: str):
    for rec in doc["reservations"]:
        if rec["item"] == item and rec["branch"] == branch and rec["status"] != "released":
            return rec
    return None


def change(rec: dict, before) -> dict:
    return {"item": rec["item"], "branch": rec["branch"], "numbers": rec["numbers"], "from": before,
            "to": rec["status"], "conflict": rec["conflict"]}


def refresh(doc: dict, obs: Observation) -> list:
    """apply the status rules to every active reservation; the changes made"""
    changes = []
    for rec in doc["reservations"]:
        if rec["status"] != "active":
            continue
        status, con = obs.judge(rec)
        if status != "active":
            rec["status"], rec["conflict"] = status, con
            changes.append(change(rec, "active"))
    return changes


def claim_row(rec: dict) -> str:
    numbers = rec["numbers"]
    cell = str(numbers[0]) if len(numbers) == 1 else f"{numbers[0]}–{numbers[-1]}"
    return (f"| {cell} | KĀLA-YANTRA / {rec['item']} | reserved by kyalloc for branch `{rec['branch']}` "
            f"| CLAIMED — kyalloc:{rec['item']}@{rec['branch']} reserved {rec['reserved_at']} |")


def emit(obj, indent=None) -> None:
    sys.stdout.write(json.dumps(obj, indent=indent) + "\n")


# ---------------------------------------------------------------- verbs

def cmd_reserve(args) -> int:
    alloc = Alloc()
    with alloc.locked():
        doc = alloc.load()
        rec = live_record(doc, args.item, args.branch)
        if rec is not None and len(rec["numbers"]) != args.count:
            raise Usage(f"{args.item}@{args.branch} already holds {len(rec['numbers'])} number(s); --count {args.count} differs")
        obs = Observation(args.repo, args.ref, args.claims_ref)
        changes = refresh(doc, obs)
        reused = rec is not None
        if rec is None:
            top = max([obs.disk_max, obs.claims_max] + [n for r in doc["reservations"] for n in r["numbers"]])
            rec = {"item": args.item, "branch": args.branch, "numbers": list(range(top + 1, top + 1 + args.count)),
                   "status": "active", "reserved_at": now(), "observed": obs.record(), "conflict": None}
            doc["reservations"].append(rec)
            changes.append(change(rec, None))
        if changes:
            alloc.commit(doc, "reserve", changes, dict(obs.record(), claims_ref=obs.claims_ref))
    emit({"item": rec["item"], "branch": rec["branch"], "numbers": rec["numbers"], "status": rec["status"],
          "reused": reused, "claim_row": claim_row(rec)})
    return EX_CONFLICT if rec["status"] == "conflicted" else EX_OK


def cmd_check(args) -> int:
    alloc = Alloc()
    with alloc.locked():
        doc = alloc.load()
        obs = Observation(args.repo, args.ref, args.claims_ref)
        changes = refresh(doc, obs)
        if changes:
            alloc.commit(doc, "check", changes, dict(obs.record(), claims_ref=obs.claims_ref))
    emit(doc, indent=2)
    return EX_CONFLICT if any(r["status"] == "conflicted" for r in doc["reservations"]) else EX_OK


def cmd_release(args) -> int:
    alloc = Alloc()
    with alloc.locked():
        doc = alloc.load()
        rec = live_record(doc, args.item, args.branch)
        if rec is None:
            raise Usage(f"{args.item}@{args.branch} holds no reservation to release")
        before, rec["status"] = rec["status"], "released"
        alloc.commit(doc, "release", [change(rec, before)], None, reason=args.reason)
    emit(rec)
    return EX_OK


def cmd_show(args) -> int:
    doc = Alloc().load()  # no lock, no directory: the rename makes every read a whole store
    if args.item is not None:
        doc["reservations"] = [r for r in doc["reservations"] if r["item"] == args.item]
    emit(doc, indent=2)
    return EX_CONFLICT if any(r["status"] == "conflicted" for r in doc["reservations"]) else EX_OK


# ---------------------------------------------------------------- command line

class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EX_USAGE, f"kyalloc: {message}\n")


def checked(pattern, what):
    def check(value: str) -> str:
        if not pattern.match(value) or ".." in value or "//" in value:
            raise argparse.ArgumentTypeError(f"{value!r} is not a valid {what}")
        return value
    return check


def count(value: str) -> int:
    if not re.match(r"\d+\Z", value) or not 1 <= int(value) <= MAX_COUNT:
        raise argparse.ArgumentTypeError(f"{value!r} is not a count between 1 and {MAX_COUNT}")
    return int(value)


def reason(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("the reason is empty")
    return value.strip()


def parser() -> Parser:
    ap = Parser(prog="kyalloc.py", allow_abbrev=False,
                description="KĀLA-YANTRA v3 migration allocator: an atomic, persistent reservation keyed by item/branch")
    sub = ap.add_subparsers(dest="verb", metavar="{reserve,check,release,show}")
    sub.required = True
    item, branch = checked(ITEM_RE, "item id"), checked(BRANCH_RE, "branch name")
    ref = checked(BRANCH_RE, "ref")

    def observing(p):
        p.add_argument("--repo", required=True, type=os.path.abspath)
        p.add_argument("--ref", default=DEFAULT_REF, type=ref)
        p.add_argument("--claims-ref", default=DEFAULT_CLAIMS_REF, type=ref)

    p = sub.add_parser("reserve", allow_abbrev=False)
    p.add_argument("--item", required=True, type=item)
    p.add_argument("--branch", required=True, type=branch)
    p.add_argument("--count", default=1, type=count)
    observing(p)
    p.set_defaults(run=cmd_reserve)
    p = sub.add_parser("check", allow_abbrev=False)
    observing(p)
    p.set_defaults(run=cmd_check)
    p = sub.add_parser("release", allow_abbrev=False)
    p.add_argument("--item", required=True, type=item)
    p.add_argument("--branch", required=True, type=branch)
    p.add_argument("--reason", required=True, type=reason)
    p.set_defaults(run=cmd_release)
    p = sub.add_parser("show", allow_abbrev=False)
    p.add_argument("--item", type=item)
    p.set_defaults(run=cmd_show)
    return ap


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.run(args)
    except Refusal as exc:
        sys.stderr.write(f"kyalloc: {exc.message}\n")
        return exc.code


if __name__ == "__main__":
    raise SystemExit(main())
