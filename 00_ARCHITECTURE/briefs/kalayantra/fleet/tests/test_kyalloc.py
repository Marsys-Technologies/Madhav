"""kyalloc.py — the migration allocator (relaunch plan v2.7 §5; packet KV3-B-KYALLOC v1).

The three tests the plan names, and the packet's six acceptance groups:
  1. concurrent allocation            (tests `test_concurrent_*`)
  2. restart / reuse                  (tests `test_restart_*`, `test_reuse_*`, `test_count_*`)
  3. conflicting external reservation (tests `test_conflict_*`, `test_claim_row_*`, `test_consumed_*`)
  4. namespace                        (tests `test_namespace_*`, `test_p12_*`, `test_adopt_*`, `test_unreadable_*`)
  5. store                            (tests `test_corrupt_*`, `test_lost_*`, `test_released_*`)
  6. git is read-only                 (tests `test_git_*`)

Every test runs the script as the contract states it (`python3 -I -B kyalloc.py <verb> …`) against a fixture
repository built with `git init` under the test's temp directory, with `KY_RUN` (or `KY_ROOT`) inside that same
directory. Nothing here reads the real claim table, the real run directory or the network, and nothing is skipped.
"""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
KYALLOC = FLEET / "kyalloc.py"
EXISTING_PROCEDURE = REPO / "platform" / "scripts" / "governance" / "reserve_migration_number.py"
GIT = shutil.which("git")
CLAIMS_PATH = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
MAIN = "refs/remotes/origin/main"
CLAIMS = "refs/remotes/origin/campaign-coordination"
RESERVE_KEYS = {"item", "branch", "numbers", "status", "reused", "claim_row"}
RECORD_KEYS = {"item", "branch", "numbers", "status", "reserved_at", "observed", "conflict"}
OBSERVED_KEYS = {"ref", "ref_commit", "disk_max", "claims_max", "claims_blob"}
# the standard fixture: disk max 1340 (the supabase directory), claim table max 1348 (a range) -> next is 1349
STD_FILES = {"platform/migrations/001_baseline.sql": "-- 1\n",
             "platform/migrations/1338_a.sql": "-- a\n",
             "platform/supabase/migrations/1340_b.sql": "-- b\n",
             "platform/migrations/README.md": "not a migration\n"}
STD_ROWS = ("| 1339 | OTHER / lane | `platform/migrations/1339_x.sql` | CLAIMED — PR open |",
            "| 1341 | OTHER / lane | 1341_y.sql | **CLAIMED** |",
            "| 1345–1348 | OTHER / lane | four migrations | CLAIMED |")
STD_NEXT = 1349


def claims_md(rows) -> str:
    """a coordination file whose §2 holds `rows`; numbers outside §2 are decoys that must not count"""
    return "\n".join(["# CAMPAIGN COORDINATION", "", "## 1. LEASES", "", "| 9999 | decoy before the claim table |", "",
                      "## 2. MIGRATION NUMBER CLAIMS (claim-at-PR-open; renumber-on-collision stands)", "",
                      "| number | campaign | file | status |", "|---|---|---|---|", *rows, "",
                      "| — | CONDUCTOR RULING | — | a row without a number |", "",
                      "## 3. OTHER", "", "| 8888 | decoy after the claim table |", ""])


class Fixture:
    """one fixture repository and one KY_RUN, both under the test's temp directory"""

    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.repo = tmp / "repo"
        self.run = tmp / "run"
        self.home = tmp / "home"
        self.alloc = self.run / "alloc"
        self.store = self.alloc / "migrations.json"
        self.journal = self.alloc / "journal.jsonl"
        for d in (self.repo, self.run, self.home):
            d.mkdir()
        self._n = 0
        self.git("init", "-q")

    # -- building the repository (test side only; kyalloc itself is held to three read-only verbs)
    def git(self, *args, stdin=None) -> str:
        env = {"PATH": os.environ["PATH"], "HOME": str(self.home), "GIT_CONFIG_GLOBAL": os.devnull,
               "GIT_CONFIG_NOSYSTEM": "1"}
        p = subprocess.run([GIT, *args], cwd=self.repo, env=env, input=stdin, capture_output=True)
        assert p.returncode == 0, (args, p.stderr.decode())
        return p.stdout.decode().strip()

    def commit(self, ref: str, files: dict, base=None, remove=()) -> None:
        """`ref` := a commit of `base`'s tree (none: an empty tree) with `files` written and `remove` deleted"""
        self._n += 1
        message = f"fixture {self._n}".encode()
        stream = [f"commit {ref}\ncommitter t <t@example.invalid> {1700000000 + self._n} +0000\n".encode(),
                  b"data %d\n%s\n" % (len(message), message)]
        if base:
            stream.append(f"from {base}^0\n".encode())
        for path in remove:
            stream.append(f"D {path}\n".encode())
        for path, content in files.items():
            data = content if isinstance(content, bytes) else content.encode("utf-8")
            stream.append(f"M 100644 inline {path}\n".encode() + b"data %d\n%s\n" % (len(data), data))
        self.git("fast-import", "--quiet", "--force", stdin=b"".join(stream))

    def set_claims(self, rows, text=None):
        self.commit(CLAIMS, {CLAIMS_PATH: claims_md(rows) if text is None else text})

    # -- running the allocator
    def env(self, **extra) -> dict:
        env = {"PATH": os.environ["PATH"], "HOME": str(self.home), "KY_RUN": str(self.run), "KY_GIT": GIT}
        env.update({k: str(v) for k, v in extra.items()})
        return {k: v for k, v in env.items() if v != ""}

    def argv(self, *args) -> list:
        return [sys.executable, "-I", "-B", str(KYALLOC), *[str(a) for a in args]]

    def ky(self, *args, **env):
        e = self.env(**env)
        # a run without its own run directory would write to the campaign host's; no test may do that
        assert "KY_RUN" in e or "KY_ROOT" in e
        return subprocess.run(self.argv(*args), env=e, capture_output=True, text=True, timeout=120)

    def reserve(self, item, branch=None, *more, **env):
        return self.ky("reserve", "--item", item, "--branch", branch or f"kalayantra/{item.lower()}",
                       "--repo", self.repo, *more, **env)

    def reserved(self, item, branch=None, *more, **env) -> dict:
        p = self.reserve(item, branch, *more, **env)
        assert p.returncode == 0, p.stderr
        out = json.loads(p.stdout)
        assert set(out) == RESERVE_KEYS
        return out

    def check(self, *more, **env):
        return self.ky("check", "--repo", self.repo, *more, **env)

    # -- reading what it wrote
    def records(self) -> list:
        return json.loads(self.store.read_bytes())["reservations"]

    def record(self, item) -> dict:
        live = [r for r in self.records() if r["item"] == item and r["status"] != "released"]
        assert len(live) == 1, live
        return live[0]

    def journal_lines(self) -> list:
        if not self.journal.exists():
            return []
        return [json.loads(line) for line in self.journal.read_text().splitlines()]

    def written(self) -> dict:
        """every file under alloc/ except the lock file, by content"""
        if not self.alloc.exists():
            return {}
        return {p.name: p.read_bytes() for p in sorted(self.alloc.iterdir()) if p.name != ".lock"}


def tree_state(root: Path, skip=None) -> list:
    out = []
    for p in sorted(root.rglob("*")):
        if skip and (p == skip or skip in p.parents):
            continue
        st = p.lstat()
        out.append((str(p.relative_to(root)), st.st_size if p.is_file() else None, st.st_mtime_ns))
    return out


def valid_store(fx: Fixture) -> list:
    """the store is the contract's schema, and no number is held by two reservations"""
    doc = json.loads(fx.store.read_bytes())
    assert set(doc) == {"schema", "reservations"} and doc["schema"] == "ky.alloc/1"
    seen = []
    for r in doc["reservations"]:
        assert set(r) == RECORD_KEYS and set(r["observed"]) == OBSERVED_KEYS
        assert r["status"] in ("active", "consumed", "released", "conflicted")
        assert r["numbers"] and all(type(n) is int for n in r["numbers"])
        assert (r["conflict"] is not None) or r["status"] != "conflicted"
        seen += r["numbers"]
    assert len(seen) == len(set(seen)), seen
    return doc["reservations"]


@pytest.fixture
def bare(tmp_path):
    return Fixture(tmp_path)


@pytest.fixture
def fx(bare):
    bare.commit(MAIN, STD_FILES)
    bare.set_claims(STD_ROWS)
    return bare


def land_on_main(fx: Fixture, path: str, content="-- landed\n"):
    fx.commit(MAIN, {path: content}, base=MAIN)


# ---------------------------------------------------------------- 1. concurrent allocation

def test_concurrent_distinct_keys_get_distinct_gap_free_numbers(fx):
    n = 12
    procs = [subprocess.Popen(fx.argv("reserve", "--item", f"K-{i}", "--branch", f"kalayantra/k-{i}",
                                      "--repo", fx.repo), env=fx.env(), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True) for i in range(n)]
    outs = []
    for p in procs:
        out, err = p.communicate(timeout=120)
        assert p.returncode == 0, err
        outs.append(json.loads(out))
    numbers = sorted(o["numbers"][0] for o in outs)
    assert numbers == list(range(STD_NEXT, STD_NEXT + n))  # distinct, gap-free, above the namespace max
    assert all(o["reused"] is False and o["status"] == "active" and len(o["numbers"]) == 1 for o in outs)
    records = valid_store(fx)
    assert sorted(r["numbers"][0] for r in records) == numbers
    assert {(r["item"], r["numbers"][0]) for r in records} == {(o["item"], o["numbers"][0]) for o in outs}
    lines = fx.journal_lines()
    assert len(lines) == n  # one journal line each
    assert sorted(c["numbers"][0] for line in lines for c in line["changes"]) == numbers
    assert set(fx.written()) == {"migrations.json", "journal.jsonl"}  # no temp file left behind


def test_concurrent_same_key_gets_one_reservation(fx):
    n = 8
    procs = [subprocess.Popen(fx.argv("reserve", "--item", "K-SAME", "--branch", "kalayantra/k-same",
                                      "--repo", fx.repo, "--count", "2"), env=fx.env(), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True) for _ in range(n)]
    outs = []
    for p in procs:
        out, err = p.communicate(timeout=120)
        assert p.returncode == 0, err
        outs.append(json.loads(out))
    assert all(o["numbers"] == [STD_NEXT, STD_NEXT + 1] for o in outs)
    assert sorted(o["reused"] for o in outs) == [False] + [True] * (n - 1)
    assert len(valid_store(fx)) == 1
    assert len(fx.journal_lines()) == 1


def test_concurrent_mixed_counts_never_overlap(fx):
    counts = [1, 3, 2, 1, 4, 2, 1, 3]
    procs = [subprocess.Popen(fx.argv("reserve", "--item", f"M-{i}", "--branch", f"kalayantra/m-{i}",
                                      "--repo", fx.repo, "--count", c), env=fx.env(), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True) for i, c in enumerate(counts)]
    got = []
    for p, c in zip(procs, counts):
        out, err = p.communicate(timeout=120)
        assert p.returncode == 0, err
        numbers = json.loads(out)["numbers"]
        assert len(numbers) == c and numbers == list(range(numbers[0], numbers[0] + c))  # consecutive
        got += numbers
    assert sorted(got) == list(range(STD_NEXT, STD_NEXT + sum(counts)))
    valid_store(fx)


# ---------------------------------------------------------------- 2. restart / reuse

def test_restart_returns_the_same_numbers_and_consumes_nothing(fx):
    first = fx.reserved("K-A", None, "--count", "3")
    assert first["numbers"] == [STD_NEXT, STD_NEXT + 1, STD_NEXT + 2] and first["reused"] is False
    before, mtime = fx.written(), fx.store.stat().st_mtime_ns
    again = fx.reserved("K-A", None, "--count", "3")  # a new process
    assert again == dict(first, reused=True)
    assert fx.written() == before and fx.store.stat().st_mtime_ns == mtime  # not a mutation: no write, no journal line
    assert len(fx.journal_lines()) == 1
    assert fx.reserved("K-B")["numbers"] == [STD_NEXT + 3]  # the reuse consumed nothing


def test_reuse_is_keyed_by_item_and_branch(fx):
    a = fx.reserved("K-A", "kalayantra/one")
    b = fx.reserved("K-A", "kalayantra/two")
    c = fx.reserved("K-C", "kalayantra/one")
    assert [a["numbers"], b["numbers"], c["numbers"]] == [[STD_NEXT], [STD_NEXT + 1], [STD_NEXT + 2]]
    assert fx.reserved("K-A", "kalayantra/two") == dict(b, reused=True)


def test_reuse_beside_a_stale_temp_file(fx):
    first = fx.reserved("K-A")
    stale = fx.alloc / "migrations.json.tmp"
    stale.write_bytes(b'{"schema": "ky.alloc/1", "reservations": [{"item": "K-GHOST", "numb')  # a writer killed mid-write
    assert fx.reserved("K-A") == dict(first, reused=True)
    assert fx.reserved("K-B")["numbers"] == [STD_NEXT + 1]
    assert [r["item"] for r in valid_store(fx)] == ["K-A", "K-B"]
    assert "migrations.json.tmp" not in fx.written()  # the next writer's rename replaced it


def test_restart_after_a_writer_killed_inside_the_lock(fx):
    first = fx.reserved("K-A")
    # a git double that never answers: the writer below holds the lock and is then killed by this test
    marker = fx.tmp / "double.started"
    double = fx.tmp / "git-hang"
    double.write_text(f"#!/bin/sh\n: > '{marker}'\nexec sleep 600\n")
    double.chmod(0o755)
    victim = subprocess.Popen(fx.argv("reserve", "--item", "K-KILLED", "--branch", "kalayantra/k-killed",
                                      "--repo", fx.repo), env=fx.env(KY_GIT=double), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, start_new_session=True)
    try:
        deadline = time.monotonic() + 30
        while not marker.exists():
            assert time.monotonic() < deadline and victim.poll() is None, "the writer never reached git"
            time.sleep(0.02)
    finally:
        os.killpg(victim.pid, signal.SIGKILL)  # the writer and its double: both started by this test
        victim.communicate(timeout=30)
    assert victim.returncode == -signal.SIGKILL
    (fx.alloc / "migrations.json.tmp").write_bytes(b"{")
    assert fx.reserved("K-A") == dict(first, reused=True)  # the kernel released the dead writer's lock
    assert fx.reserved("K-B")["numbers"] == [STD_NEXT + 1]  # the killed writer reserved nothing: no gap
    assert [r["item"] for r in valid_store(fx)] == ["K-A", "K-B"]


def test_count_mismatch_is_usage(fx):
    fx.reserved("K-A", None, "--count", "2")
    before = fx.written()
    for more in (("--count", "3"), ("--count", "1"), ()):  # N defaults to 1
        p = fx.reserve("K-A", None, *more)
        assert p.returncode == 64 and p.stdout == "", (more, p.stdout, p.stderr)
    assert fx.written() == before
    assert fx.reserved("K-A", None, "--count", "2")["reused"] is True


def test_reserve_output_and_record(fx):
    out = fx.reserved("K-A", "kalayantra/k-a", "--count", "2")
    assert out["item"] == "K-A" and out["branch"] == "kalayantra/k-a" and out["status"] == "active"
    r = fx.record("K-A")
    assert r["numbers"] == out["numbers"] and r["status"] == "active" and r["conflict"] is None
    assert r["observed"] == {"ref": "origin/main", "ref_commit": fx.git("rev-parse", MAIN), "disk_max": 1340,
                             "claims_max": 1348, "claims_blob": fx.git("rev-parse", f"{CLAIMS}:{CLAIMS_PATH}")}
    assert r["reserved_at"].endswith("Z")
    line = fx.journal_lines()[-1]
    assert line["verb"] == "reserve" and line["store_sha256"] == hashlib.sha256(fx.store.read_bytes()).hexdigest()


# ---------------------------------------------------------------- 3. conflicting external reservation

def test_conflict_number_lands_on_ref_from_another_branch(fx):
    a = fx.reserved("K-A")
    fx.commit("refs/remotes/origin/kalayantra/k-a", {f"platform/migrations/{STD_NEXT}_mine.sql": "-- mine\n"}, base=MAIN)
    land_on_main(fx, f"platform/migrations/{STD_NEXT}_theirs.sql")
    p = fx.reserve("K-A")
    out = json.loads(p.stdout)
    assert p.returncode == 3 and out["status"] == "conflicted" and out["reused"] is True
    assert out["numbers"] == a["numbers"]  # never silently renumbered
    r = fx.record("K-A")
    assert r["conflict"]["number"] == STD_NEXT  # both parties recorded: the key, and what it collided with
    assert f"platform/migrations/{STD_NEXT}_theirs.sql" in r["conflict"]["with"]
    assert fx.git("rev-parse", MAIN) in r["conflict"]["with"]
    c = fx.reserved("K-C")  # another key: exit 0, and never the conflicted number
    assert c["numbers"] == [STD_NEXT + 1]
    assert fx.check().returncode == 3
    assert fx.reserve("K-A").returncode == 3  # it stays conflicted until it is released
    assert fx.ky("show", "--item", "K-A").returncode == 3 and fx.ky("show", "--item", "K-C").returncode == 0


def test_conflict_on_ref_without_an_own_branch(fx):
    fx.reserved("K-A")
    land_on_main(fx, f"platform/supabase/migrations/{STD_NEXT}_theirs.sql")  # the other directory, same sequence
    p = fx.check()
    assert p.returncode == 3
    assert [r["status"] for r in json.loads(p.stdout)["reservations"]] == ["conflicted"]


def test_conflict_second_number_of_a_reservation(fx):
    a = fx.reserved("K-A", None, "--count", "3")
    land_on_main(fx, f"platform/migrations/{a['numbers'][1]}_theirs.sql")
    assert fx.reserve("K-A", None, "--count", "3").returncode == 3
    assert fx.record("K-A")["conflict"]["number"] == a["numbers"][1]
    assert fx.reserved("K-B")["numbers"] == [a["numbers"][2] + 1]  # none of the three is given to another key


def test_conflict_claim_row_without_the_token(fx):
    a = fx.reserved("K-A")
    foreign = f"| {STD_NEXT} | OTHER / lane | {STD_NEXT}_theirs.sql | CLAIMED — PR open |"
    fx.set_claims(STD_ROWS + (foreign,))
    p = fx.reserve("K-A")
    out = json.loads(p.stdout)
    assert p.returncode == 3 and out["status"] == "conflicted" and out["numbers"] == a["numbers"]
    r = fx.record("K-A")
    assert r["conflict"]["number"] == STD_NEXT and "OTHER / lane" in r["conflict"]["with"]
    assert fx.reserved("K-C")["numbers"] == [STD_NEXT + 1]  # not reissued
    journal = fx.journal_lines()
    assert [c["to"] for c in journal[1]["changes"]] == ["conflicted"]


def test_conflict_claim_range_covering_the_number(fx):
    fx.reserved("K-A")
    fx.set_claims(STD_ROWS + (f"| {STD_NEXT - 1}–{STD_NEXT + 3} | OTHER | a range | CLAIMED |",))
    assert fx.check().returncode == 3 and fx.record("K-A")["status"] == "conflicted"


@pytest.mark.parametrize("token", ["kyalloc:K-B@kalayantra/k-a", "kyalloc:K-A@kalayantra/k-a-2",
                                   "kyalloc:K-A@kalayantra/k", "kyalloc:K-A", "kyalloc:k-a@kalayantra/k-a",
                                   "xkyalloc:K-A@kalayantra/k-a", "kyalloc:K-A@kalayantra/k-a.",
                                   "K-A@kalayantra/k-a"])
def test_conflict_near_miss_token(fx, token):
    fx.reserved("K-A", "kalayantra/k-a")
    fx.set_claims(STD_ROWS + (f"| {STD_NEXT} | KY | x | CLAIMED — {token} |",))
    assert fx.check().returncode == 3 and fx.record("K-A")["status"] == "conflicted"


def test_claim_row_with_the_token_stays_active(fx):
    a = fx.reserved("K-A", None, "--count", "2")
    assert "kyalloc:K-A@kalayantra/k-a" in a["claim_row"]
    fx.set_claims(STD_ROWS + (a["claim_row"],))  # the ready-to-paste row, published by the conductor
    p = fx.reserve("K-A", None, "--count", "2")
    assert p.returncode == 0 and json.loads(p.stdout) == dict(a, reused=True)
    assert fx.check().returncode == 0 and fx.record("K-A")["status"] == "active"
    assert len(fx.journal_lines()) == 1  # nothing changed
    assert fx.reserved("K-B")["numbers"] == [a["numbers"][1] + 1]


def test_claim_row_is_understood_by_the_existing_procedure(fx):
    ns = {"__name__": "reserve_migration_number"}  # executed from source: no bytecode beside a read-only reference
    exec(compile(EXISTING_PROCEDURE.read_text(), str(EXISTING_PROCEDURE), "exec"), ns)
    existing = types.SimpleNamespace(**ns)
    one = fx.reserved("K-A")
    three = fx.reserved("K-B", None, "--count", "3")
    assert existing.ccd_ceiling(claims_md([one["claim_row"]])) == one["numbers"][0]
    assert existing.ccd_ceiling(claims_md([three["claim_row"]])) == three["numbers"][-1]
    assert existing.ccd_ceiling(claims_md(STD_ROWS)) == 1348  # and both read the fixture table alike
    assert "\n" not in three["claim_row"] and three["claim_row"].startswith(f"| {three['numbers'][0]}–{three['numbers'][-1]} |")


def test_consumed_when_merged_from_its_own_branch(fx):
    a = fx.reserved("K-A")
    own = f"platform/migrations/{STD_NEXT}_mine.sql"
    fx.commit("refs/remotes/origin/kalayantra/k-a", {own: "-- mine\n"}, base=MAIN)
    assert fx.check().returncode == 0 and fx.record("K-A")["status"] == "active"  # authored, not yet at --ref
    land_on_main(fx, own, "-- mine\n")
    p = fx.reserve("K-A")
    assert p.returncode == 0 and json.loads(p.stdout) == dict(a, reused=True, status="consumed")
    assert fx.record("K-A")["conflict"] is None
    assert fx.reserved("K-B")["numbers"] == [STD_NEXT + 1]


def test_consumed_from_a_local_branch_when_no_remote_branch_exists(fx):
    fx.reserved("K-A")
    own = f"platform/supabase/migrations/{STD_NEXT}_mine.sql"
    fx.commit("refs/heads/kalayantra/k-a", {own: "-- mine\n"}, base=MAIN)
    land_on_main(fx, own, "-- mine\n")
    assert fx.check().returncode == 0 and fx.record("K-A")["status"] == "consumed"


def test_conflict_remote_branch_decides_before_the_local_one(fx):
    fx.reserved("K-A")
    path = f"platform/migrations/{STD_NEXT}_x.sql"
    fx.commit("refs/remotes/origin/kalayantra/k-a", {"platform/migrations/README.md": "no migration here\n"}, base=MAIN)
    fx.commit("refs/heads/kalayantra/k-a", {path: "-- local only\n"}, base=MAIN)
    land_on_main(fx, path)
    assert fx.check().returncode == 3 and fx.record("K-A")["status"] == "conflicted"


def test_conflict_two_migrations_with_the_number_at_ref(fx):
    fx.reserved("K-A")
    own = f"platform/migrations/{STD_NEXT}_mine.sql"
    fx.commit("refs/remotes/origin/kalayantra/k-a", {own: "-- mine\n"}, base=MAIN)
    land_on_main(fx, own, "-- mine\n")
    land_on_main(fx, f"platform/supabase/migrations/{STD_NEXT}_theirs.sql")
    assert fx.check().returncode == 3
    assert "theirs" in fx.record("K-A")["conflict"]["with"]


def test_conflict_own_unmerged_migration_beside_a_foreign_one_from_ref(fx):
    """the branch took the foreign file in with a merge of main; its own migration with that number is not at --ref"""
    fx.reserved("K-A")
    theirs = f"platform/migrations/{STD_NEXT}_theirs.sql"
    land_on_main(fx, theirs)
    fx.commit("refs/remotes/origin/kalayantra/k-a", {f"platform/migrations/{STD_NEXT}_mine.sql": "-- mine\n"}, base=MAIN)
    assert fx.check().returncode == 3 and fx.record("K-A")["status"] == "conflicted"


def test_conflict_and_consumed_are_not_re_judged(fx):
    fx.reserved("K-A")
    fx.reserved("K-B")
    own = f"platform/migrations/{STD_NEXT + 1}_b.sql"
    fx.commit("refs/remotes/origin/kalayantra/k-b", {own: "-- b\n"}, base=MAIN)
    land_on_main(fx, own, "-- b\n")
    fx.set_claims(STD_ROWS + (f"| {STD_NEXT} | OTHER | x | CLAIMED |",))
    assert fx.check().returncode == 3
    assert [fx.record("K-A")["status"], fx.record("K-B")["status"]] == ["conflicted", "consumed"]
    lines = len(fx.journal_lines())
    fx.set_claims(STD_ROWS)  # the foreign row disappears; the reservation is still conflicted until released
    fx.commit("refs/remotes/origin/kalayantra/k-b", {}, base=MAIN, remove=[own])
    assert fx.check().returncode == 3
    assert [fx.record("K-A")["status"], fx.record("K-B")["status"]] == ["conflicted", "consumed"]
    assert len(fx.journal_lines()) == lines


def test_check_prints_the_store_and_updates_statuses(fx):
    fx.reserved("K-A")
    fx.reserved("K-B")
    p = fx.check()
    assert p.returncode == 0 and json.loads(p.stdout) == json.loads(fx.store.read_bytes())
    land_on_main(fx, f"platform/migrations/{STD_NEXT + 1}_theirs.sql")
    p = fx.check()
    assert p.returncode == 3 and json.loads(p.stdout) == json.loads(fx.store.read_bytes())
    assert [r["status"] for r in valid_store(fx)] == ["active", "conflicted"]
    line = fx.journal_lines()[-1]
    assert line["verb"] == "check" and [(c["item"], c["from"], c["to"]) for c in line["changes"]] == [("K-B", "active", "conflicted")]
    assert line["store_sha256"] == hashlib.sha256(fx.store.read_bytes()).hexdigest()


# ---------------------------------------------------------------- 4. namespace

@pytest.mark.parametrize("files, rows, expected", [
    ({"platform/migrations/1400_x.sql": ""}, STD_ROWS, 1401),                       # platform/migrations
    ({"platform/supabase/migrations/1500_x.sql": ""}, STD_ROWS, 1501),              # platform/supabase/migrations
    ({}, STD_ROWS + ("| 1600–1610 | OTHER | a range | CLAIMED |",), 1611),         # a claim-table range (en dash)
    ({}, STD_ROWS + ("| 1600-1612 | OTHER | a range | CLAIMED |",), 1613),         # … with a hyphen
    ({}, STD_ROWS + ("| 1700 | OTHER | single | CLAIMED |",), 1701),               # a single claimed number
    ({}, STD_ROWS + ("| 1333, 1735 | OTHER | a list | MERGED |",), 1736),          # a list cell
    ({}, STD_ROWS + ("| **1750** | OTHER | emphasised | CLAIMED |",), 1751),
    ({}, STD_ROWS + ("| 1760+ | OTHER | open-ended, as the existing procedure reads it | CLAIMED |",), 1761),
    ({"platform/migrations/1800_x.txt": ""}, STD_ROWS, 1801),                       # any `<digits>_` file name counts
    ({"platform/migrations/sub/1900_x.sql": "", "other/1950_x.sql": "", "platform/1960_x.sql": ""}, STD_ROWS, STD_NEXT),
])
def test_namespace_sources_raise_the_max(bare, files, rows, expected):
    bare.commit(MAIN, dict(STD_FILES, **files))
    bare.set_claims(rows)
    assert bare.reserved("K-A")["numbers"] == [expected]


def test_namespace_gaps_are_never_filled(fx):
    # 1342–1344 are free below the claim-table max; they stay free
    assert fx.reserved("K-A", None, "--count", "2")["numbers"] == [STD_NEXT, STD_NEXT + 1]
    land_on_main(fx, "platform/migrations/1400_theirs.sql")
    assert fx.reserved("K-B")["numbers"] == [1401]
    assert fx.reserved("K-C")["numbers"] == [1402]


def test_namespace_other_refs(fx):
    fx.commit("refs/remotes/origin/release", dict(STD_FILES, **{"platform/migrations/2000_x.sql": ""}))
    fx.commit("refs/remotes/origin/coord2", {CLAIMS_PATH: claims_md(["| 2100 | OTHER | x | CLAIMED |"])})
    a = fx.reserved("K-A", None, "--ref", "origin/release")
    assert a["numbers"] == [2001] and fx.record("K-A")["observed"]["ref"] == "origin/release"
    assert fx.reserved("K-B", None, "--claims-ref", "origin/coord2")["numbers"] == [2101]


def test_p12_claimed_numbers_are_never_issued(bare):
    bare.commit(MAIN, STD_FILES)  # disk max 1340
    bare.set_claims(("| 1350 | KĀLA-YANTRA / k2 | 1350_x.sql | CLAIMED |",
                     "| 1351–1356 | KĀLA-YANTRA | six held numbers | CLAIMED |",
                     "| 1362 | KĀLA-YANTRA / k2 / K-CERT-2 | 1362_x.sql | CLAIMED |"))
    seven = {1351, 1352, 1353, 1354, 1355, 1356, 1362}
    issued = []
    for i in range(6):
        issued += bare.reserved(f"K-{i}", None, "--count", str(1 + i % 2))["numbers"]
    assert issued == list(range(1363, 1363 + len(issued)))  # the next number is above them
    assert not seven & set(issued)
    assert not seven & {n for r in valid_store(bare) for n in r["numbers"]}
    assert bare.check().returncode == 0


def test_adopt_is_not_a_verb(fx):
    fx.reserved("K-A")
    before = fx.written()
    for args in (("adopt",), ("adopt", "--item", "K-X", "--branch", "b", "--repo", fx.repo, "--number", "1351"),
                 ("reserve", "--item", "K-X", "--branch", "b", "--repo", fx.repo, "--number", "1351"),
                 ("reserve", "--item", "K-X", "--branch", "b", "--repo", fx.repo, "--adopt", "1351")):
        p = fx.ky(*args)
        assert p.returncode == 64 and p.stdout == "", args
    assert fx.written() == before


def unreadable_cases():
    return {
        "ref missing": lambda fx: ("--ref", "origin/nope"),
        "claims ref missing": lambda fx: ("--claims-ref", "origin/nope"),
        "claim file missing at the claims ref": lambda fx: fx.commit(CLAIMS, {"README.md": "x"}) or (),
        "claim section missing": lambda fx: fx.set_claims((), text="# CAMPAIGN COORDINATION\n\n| 1339 | x |\n") or (),
        "claim section twice": lambda fx: fx.set_claims((), text=claims_md(STD_ROWS) + claims_md(STD_ROWS)) or (),
        "claim section without a row": lambda fx: fx.set_claims(()) or (),
        "claim number not understood": lambda fx: fx.set_claims(STD_ROWS + ("| 1349 or 1350 | OTHER | x | CLAIMED |",)) or (),
        "claim number with text": lambda fx: fx.set_claims(STD_ROWS + ("| 13x9 | OTHER | x | CLAIMED |",)) or (),
        "claim range reversed": lambda fx: fx.set_claims(STD_ROWS + ("| 1360–1355 | OTHER | x | CLAIMED |",)) or (),
        "claim file not text": lambda fx: fx.set_claims((), text=claims_md(STD_ROWS).encode() + b"\xff\xfe") or (),
        "claim path is a directory": lambda fx: fx.commit(CLAIMS, {CLAIMS_PATH + "/x.md": claims_md(STD_ROWS)}) or (),
        "no migration at the ref": lambda fx: fx.commit(MAIN, {"README.md": "x"}) or (),
        "ref is not a commit": lambda fx: ("--ref", fx.git("rev-parse", f"{MAIN}:platform/migrations/001_baseline.sql")),
    }


@pytest.mark.parametrize("case", sorted(unreadable_cases()))
@pytest.mark.parametrize("had_store", [False, True])
def test_unreadable_namespace_reserves_nothing(fx, case, had_store):
    if had_store:
        fx.reserved("K-A")
    before = fx.written()
    more = unreadable_cases()[case](fx)
    for p in (fx.reserve("K-NEW", None, *more), fx.reserve("K-A", None, *more), fx.check(*more)):
        assert p.returncode == 4 and p.stdout == "", (case, p.stdout, p.stderr)
        assert p.stderr.startswith("kyalloc: ")
    assert fx.written() == before  # the store is byte-identical (absent stays absent), the journal too
    assert ("migrations.json" in before) == had_store


@pytest.mark.parametrize("kind", ["not a repository", "repository path missing", "git missing", "git fails"])
def test_unreadable_repository_or_git_reserves_nothing(fx, kind):
    fx.reserved("K-A")
    before = fx.written()
    plain = fx.tmp / "plain"
    plain.mkdir()
    failing = fx.tmp / "git-fail"
    failing.write_text("#!/bin/sh\nexit 128\n")
    failing.chmod(0o755)
    repo, env = {"not a repository": (plain, {}), "repository path missing": (fx.tmp / "absent", {}),
                 "git missing": (fx.repo, {"KY_GIT": fx.tmp / "no-such-git"}),
                 "git fails": (fx.repo, {"KY_GIT": failing})}[kind]
    for args in (("reserve", "--item", "K-NEW", "--branch", "b", "--repo", repo), ("check", "--repo", repo)):
        p = fx.ky(*args, **env)
        assert p.returncode == 4 and p.stdout == "", (kind, p.stderr)
    assert fx.written() == before


def test_unreadable_namespace_recovers(fx):
    fx.reserved("K-A")
    good = fx.git("rev-parse", CLAIMS)
    fx.set_claims(STD_ROWS + ("| 13x9 | OTHER | x | CLAIMED |",))
    assert fx.reserve("K-B").returncode == 4
    fx.git("update-ref", CLAIMS, good)
    assert fx.reserved("K-B")["numbers"] == [STD_NEXT + 1]


# ---------------------------------------------------------------- 5. store

def corrupt_stores(good: bytes) -> dict:
    doc = json.loads(good)

    def edit(fn) -> bytes:
        d = json.loads(good)
        fn(d)
        return json.dumps(d).encode()

    return {
        "empty file": b"",
        "truncated": good[: len(good) // 2],
        "not json": b"reservations: none\n",
        "not utf-8": b"\xff\xfe" + good,
        "a list": b"[]",
        "empty object": b"{}",
        "other schema": edit(lambda d: d.update(schema="ky.alloc/2")),
        "reservations not a list": edit(lambda d: d.update(reservations={})),
        "unknown top-level key": edit(lambda d: d.update(extra=1)),
        "record without numbers": edit(lambda d: d["reservations"][0].pop("numbers")),
        "record with an unknown key": edit(lambda d: d["reservations"][0].update(note="x")),
        "numbers empty": edit(lambda d: d["reservations"][0].update(numbers=[])),
        "number a string": edit(lambda d: d["reservations"][0].update(numbers=[str(STD_NEXT)])),
        "number a boolean": edit(lambda d: d["reservations"][0].update(numbers=[True])),
        "unknown status": edit(lambda d: d["reservations"][0].update(status="adopted")),
        "conflicted without a conflict": edit(lambda d: d["reservations"][0].update(status="conflicted")),
        "observed incomplete": edit(lambda d: d["reservations"][0]["observed"].pop("claims_blob")),
        "one number in two reservations": edit(lambda d: d["reservations"][1].update(numbers=doc["reservations"][0]["numbers"])),
        "two live reservations for one key": edit(lambda d: d["reservations"][1].update(item="K-A", branch="kalayantra/k-a")),
    }


CORRUPT_KINDS = sorted(corrupt_stores(json.dumps({"schema": "ky.alloc/1", "reservations": [
    {"numbers": [1], "observed": {"claims_blob": ""}}, {"numbers": [2]}]}).encode()))


@pytest.mark.parametrize("kind", CORRUPT_KINDS)
def test_corrupt_store_is_never_rewritten(fx, kind):
    fx.reserved("K-A")
    fx.reserved("K-B")
    fx.store.write_bytes(corrupt_stores(fx.store.read_bytes())[kind])
    before = fx.written()
    calls = (("reserve", "--item", "K-NEW", "--branch", "b", "--repo", fx.repo),
             ("reserve", "--item", "K-A", "--branch", "kalayantra/k-a", "--repo", fx.repo),
             ("check", "--repo", fx.repo),
             ("release", "--item", "K-A", "--branch", "kalayantra/k-a", "--reason", "x"),
             ("show",), ("show", "--item", "K-A"))
    for args in calls:
        p = fx.ky(*args)
        assert p.returncode == 5 and p.stdout == "", (kind, args, p.stdout, p.stderr)
        assert p.stderr.startswith("kyalloc: ")
    assert fx.written() == before  # bytes unchanged, no journal line, no temp file


def test_corrupt_store_wins_over_an_unreadable_namespace(fx):
    fx.reserved("K-A")
    fx.store.write_bytes(b"{")
    assert fx.reserve("K-B", None, "--ref", "origin/nope").returncode == 5


def test_lost_store_is_not_restarted_from_empty(fx):
    """the journal shows numbers were issued; a missing store is then unreadable, not empty"""
    fx.reserved("K-A")
    fx.store.unlink()
    before = fx.written()
    for args in (("reserve", "--item", "K-B", "--branch", "b", "--repo", fx.repo), ("check", "--repo", fx.repo),
                 ("release", "--item", "K-A", "--branch", "kalayantra/k-a", "--reason", "x"), ("show",)):
        p = fx.ky(*args)
        assert p.returncode == 5 and p.stdout == "", (args, p.stderr)
    assert fx.written() == before and not fx.store.exists()


def test_store_that_is_a_directory_is_unreadable(fx):
    fx.alloc.mkdir()
    fx.store.mkdir()
    assert fx.reserve("K-A").returncode == 5 and fx.ky("show").returncode == 5
    assert fx.store.is_dir() and list(fx.store.iterdir()) == [] and not fx.journal.exists()


def test_released_numbers_never_return(fx):
    a = fx.reserved("K-A", None, "--count", "2")
    p = fx.ky("release", "--item", "K-A", "--branch", "kalayantra/k-a", "--reason", "job abandoned")
    assert p.returncode == 0 and json.loads(p.stdout)["status"] == "released"
    line = fx.journal_lines()[-1]
    assert line["verb"] == "release" and line["reason"] == "job abandoned"
    assert [(c["from"], c["to"]) for c in line["changes"]] == [("active", "released")]
    again = fx.reserved("K-A", None, "--count", "2")  # the same key: a new reservation, new numbers
    assert again["reused"] is False and again["numbers"] == [a["numbers"][1] + 1, a["numbers"][1] + 2]
    b = fx.reserved("K-B", None, "--count", "3")
    issued = again["numbers"] + b["numbers"]
    assert not set(a["numbers"]) & set(issued)
    assert [r["status"] for r in valid_store(fx)] == ["released", "active", "active"]
    assert fx.check().returncode == 0
    assert [r["status"] for r in valid_store(fx)] == ["released", "active", "active"]


def test_released_conflict_lets_the_key_reserve_anew(fx):
    fx.reserved("K-A")
    land_on_main(fx, f"platform/migrations/{STD_NEXT}_theirs.sql")
    assert fx.reserve("K-A").returncode == 3
    assert fx.ky("release", "--item", "K-A", "--branch", "kalayantra/k-a", "--reason", "collided").returncode == 0
    assert fx.check().returncode == 0  # no reservation is conflicted any more
    out = fx.reserved("K-A")
    assert out["numbers"] == [STD_NEXT + 1] and out["reused"] is False and out["status"] == "active"
    released = [r for r in fx.records() if r["status"] == "released"]
    assert len(released) == 1 and released[0]["conflict"]["number"] == STD_NEXT  # the history is kept


def test_release_of_nothing_is_usage(fx):
    fx.reserved("K-A")
    assert fx.ky("release", "--item", "K-A", "--branch", "kalayantra/k-a", "--reason", "x").returncode == 0
    before = fx.written()
    for args in (("release", "--item", "K-A", "--branch", "kalayantra/k-a", "--reason", "again"),
                 ("release", "--item", "K-Z", "--branch", "kalayantra/k-z", "--reason", "x"),
                 ("release", "--item", "K-A", "--branch", "kalayantra/k-a"),
                 ("release", "--item", "K-A", "--branch", "kalayantra/k-a", "--reason", "  ")):
        assert fx.ky(*args).returncode == 64, args
    assert fx.written() == before


def test_show_changes_nothing(fx):
    p = fx.ky("show")  # before anything was reserved: an empty store, and no directory made for it
    assert p.returncode == 0 and json.loads(p.stdout) == {"schema": "ky.alloc/1", "reservations": []}
    assert not fx.alloc.exists()
    fx.reserved("K-A")
    fx.reserved("K-B")
    land_on_main(fx, f"platform/migrations/{STD_NEXT}_theirs.sql")  # show does not observe: K-A stays as stored
    before = tree_state(fx.tmp)
    p = fx.ky("show")
    assert p.returncode == 0 and json.loads(p.stdout) == json.loads(fx.store.read_bytes())
    p = fx.ky("show", "--item", "K-B")
    assert p.returncode == 0 and [r["item"] for r in json.loads(p.stdout)["reservations"]] == ["K-B"]
    p = fx.ky("show", "--item", "K-NONE")
    assert p.returncode == 0 and json.loads(p.stdout)["reservations"] == []
    assert tree_state(fx.tmp) == before


# ---------------------------------------------------------------- 6. git is read-only; writes stay under alloc/

def recording_double(fx: Fixture) -> tuple:
    log = fx.tmp / "git.log"
    double = fx.tmp / "git-recording"
    double.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> '{log}'\nexec '{GIT}' \"$@\"\n")
    double.chmod(0o755)
    return double, log


def recorded_verbs(log: Path) -> list:
    return [line.split(" ")[0] for line in log.read_text().splitlines()]


def test_git_double_records_whatever_is_run(fx):
    """the detector of the next test, shown red: a verb outside the three is seen by the recording double"""
    double, log = recording_double(fx)
    subprocess.run([str(double), "version"], env=fx.env(), capture_output=True, check=True)
    subprocess.run([str(double), "-C", str(fx.repo), "status"], env=fx.env(), capture_output=True, check=True)
    assert recorded_verbs(log) == ["version", "-C"]
    assert not set(recorded_verbs(log)) <= {"rev-parse", "ls-tree", "show"}


def test_git_only_read_only_verbs_and_writes_only_under_alloc(fx):
    double, log = recording_double(fx)
    env = {"KY_GIT": double}
    a = fx.reserved("K-A", **env)
    b = fx.reserved("K-B", None, "--count", "2", **env)
    c = fx.reserved("K-C", **env)
    fx.reserved("K-D", **env)
    own = f"platform/migrations/{a['numbers'][0]}_mine.sql"
    fx.commit("refs/remotes/origin/kalayantra/k-a", {own: "-- mine\n"}, base=MAIN)
    land_on_main(fx, own, "-- mine\n")                                                      # K-A consumed
    land_on_main(fx, f"platform/migrations/{b['numbers'][1]}_theirs.sql")                   # K-B conflicted (ref)
    fx.set_claims(STD_ROWS + (f"| {c['numbers'][0]} | OTHER | x | CLAIMED |",))             # K-C conflicted (claims)
    log.write_text("")
    outside = tree_state(fx.tmp, skip=fx.alloc)
    assert fx.reserve("K-A", **env).returncode == 0
    assert fx.reserve("K-B", None, "--count", "2", **env).returncode == 3
    assert fx.check(**env).returncode == 3
    assert fx.ky("release", "--item", "K-B", "--branch", "kalayantra/k-b", "--reason", "x", **env).returncode == 0
    assert fx.ky("show", **env).returncode == 3
    assert fx.reserve("K-E", None, "--ref", "origin/nope", **env).returncode == 4
    assert fx.reserve("K-E", **env).returncode == 0
    verbs = recorded_verbs(log)
    log.unlink()
    assert {r["status"] for r in valid_store(fx)} == {"active", "consumed", "conflicted", "released"}
    assert len(verbs) >= 10 and set(verbs) == {"rev-parse", "ls-tree", "show"}, verbs
    assert tree_state(fx.tmp, skip=fx.alloc) == [e for e in outside if e[0] != "git.log"]  # nothing written outside alloc/
    assert set(fx.written()) == {"migrations.json", "journal.jsonl"}


def test_git_environment_cannot_redirect_the_repository(fx, tmp_path_factory):
    other = Fixture(tmp_path_factory.mktemp("other"))
    other.commit(MAIN, {"platform/migrations/7000_x.sql": ""})
    other.set_claims(("| 7100 | OTHER | x | CLAIMED |",))
    out = fx.reserved("K-A", GIT_DIR=other.repo / ".git", GIT_WORK_TREE=other.repo)
    assert out["numbers"] == [STD_NEXT]


# ---------------------------------------------------------------- usage and run directory

def test_usage_errors_are_64(fx):
    fx.reserved("K-A")
    before = fx.written()
    r = ("--repo", fx.repo)
    cases = [(), ("frobnicate",), ("reserve",), ("reserve", "--item", "K-X", *r), ("reserve", "--branch", "b", *r),
             ("reserve", "--item", "K-X", "--branch", "b"), ("check",), ("show", "--repo", fx.repo),
             ("reserve", "--item", "K-X", "--branch", "b", *r, "--count", "0"),
             ("reserve", "--item", "K-X", "--branch", "b", *r, "--count", "-1"),
             ("reserve", "--item", "K-X", "--branch", "b", *r, "--count", "two"),
             ("reserve", "--item", "K-X", "--branch", "b", *r, "--count", "100000"),
             ("reserve", "--item", "K X", "--branch", "b", *r), ("reserve", "--item", "K@X", "--branch", "b", *r),
             ("reserve", "--item", "", "--branch", "b", *r), ("reserve", "--item", "K|X", "--branch", "b", *r),
             ("reserve", "--item", "K-X", "--branch", "a..b", *r), ("reserve", "--item", "K-X", "--branch", "a b", *r),
             ("reserve", "--item", "K-X", "--branch", "a`b", *r), ("reserve", "--item", "K-X", "--branch", "-b", *r),
             ("reserve", "--item", "K-X", "--branch", "b", *r, "--ref", "-x"),
             ("reserve", "--item", "K-X", "--branch", "b", *r, "--ref", "origin/main:x"),
             ("reserve", "--item", "K-X", "--branch", "b", *r, "--claims-ref", "a b"),
             ("reserve", "--item", "K-X", "--branch", "b", *r, "--bran", "c"), ("check", *r, "--fix")]
    for args in cases:
        p = fx.ky(*args)
        assert p.returncode == 64 and p.stdout == "", (args, p.returncode, p.stderr)
    assert fx.written() == before


@pytest.mark.parametrize("ky_run", ["relative/run", "{tmp}/absent"])
def test_run_directory_must_exist_and_be_absolute(fx, ky_run):
    value = ky_run.format(tmp=fx.tmp)
    for args in (("reserve", "--item", "K-A", "--branch", "b", "--repo", fx.repo), ("show",)):
        p = subprocess.run(fx.argv(*args), env=fx.env(KY_RUN=value), cwd=fx.tmp, capture_output=True, text=True)
        assert p.returncode == 64 and p.stdout == "", p.stderr
    assert not (fx.tmp / "absent").exists() and not (fx.tmp / "relative").exists()


def test_run_directory_defaults_to_ky_root_run(fx):
    root = fx.tmp / "root"
    (root / "run").mkdir(parents=True)
    p = fx.ky("reserve", "--item", "K-A", "--branch", "b", "--repo", fx.repo, KY_RUN="", KY_ROOT=root)
    assert p.returncode == 0 and json.loads(p.stdout)["numbers"] == [STD_NEXT]
    assert (root / "run" / "alloc" / "migrations.json").exists() and not fx.alloc.exists()
