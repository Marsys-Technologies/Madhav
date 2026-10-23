"""TRIAL_READY/1 evaluator (PLAN_A10_1 §2, A10.1 B7): one oracle per semantic rule, each with a planted reversion that fails it.

Source of the rules (plan §2): "true iff every required check reads true at that commit; a check whose evidence cannot be read is null and counts as not
ready (N.7.6)"; "a check reads true only from its detector's run" (§N.8); "TR1/TR may not be started from any other signal". The claims:
  C1 ready needs all 25 checks true; the output is exactly the five-key schema.
  C2 null is not pass: unreadable evidence / skipped oracle / unbound part / missing oracle file read null and the run is not ready.
  C3 a check absent from (or duplicated in) the registry is not ready.
  C4 a planted false detector (a failing oracle, a forbidden string present) reads false and the run is not ready, even beside nulls.
  C5 one commit: a work tree that is not the evaluated commit, is dirty, or moves while the detectors run yields no true.
  C6 a database part never reads true from a remote host, an unset DSN, or an unreadable database.
  C7 a stale trial_ready.json never survives a failed run; exit codes follow `ready`.
  C8 the shipped registry names the 25 required checks and points only at oracle files that exist (nothing invented) -- or, for a lane not yet on this branch,
     says which branch lands the file (`lands_with`) -- and keeps no check unbound except the four whose detector is another job's (TR-BIND).
  C9 `json_field_eq` (TR-BIND: a record outside the repository -- T21 verdict, T24 readiness) reads true only when every field holds, false when a field is
     present and differs (a record made for another head, 1 for true), null when the record, a field or a value is absent.
  C10 `db_migrations` with `mode: "all"` (T25) reads false when the ledger lacks ANY file the commit lists, null when the commit lists none.
  C11 a `pytest` part passes `env` with `{repo}` expanded and (the mechanism only; the shipped registry may not use it, C18) `--deselect` for each named node id; a part whose every test is deselected is null;
     a relative scratch directory is resolved first (the part runs in another cwd, so its junit file would otherwise be written elsewhere and read null).
  C12 the trial harness landed under fleet/trial_harness is the accepted v3.1 + B4 overlay the trial runs (content digest pinned), not a later or edited copy.
  C13 (PR #3874 review B-1) T24 reads true only from the amd64_slice run's OWN evidence (report, pinned runtime, EQUIVALENCE_RECORD) at this head -- never from a
     readiness record, which only says the inputs are named.
  C14 (review B-2; reworked by SR-NO-DESELECT) T20's a53 DB-suite part runs the one test that used to skip by design (the sky-convention content digest) as a real, unskipped test.
  C15 (review N-2) T21 also matches the verdict's patch_id to a patch-id recomputed from the repository; N-3/N-4 T10 part 2 pins its locale, T20 names the geometry-pin rule.
  C16 (SR-EVALUATOR-SKIP-IS-NULL, DECISIONS_SURROGATE) a `pytest` part reads true only if EVERY bound test PASSED: a skip or xfail beside passes, or a bound file none of whose tests ran, is null;
     a skip is tolerated only when the part's `optional_skips` names that exact test WITH a reason.
  C17 (SR-T24-NATIVE) T24 reads the native VM run's OWN EQUIVALENCE_RECORD (named by TRIAL_READY_EQ_RECORD, with the eq_pinned_inputs.json beside it): true only when the record is
     complete, a qualifying_run of THIS head, its arch read inside the run as linux/amd64 and not emulated; null when the record is not named or not there; the Docker amd64 slice
     stays a documented fallback alternative (`any_of`: any true alternative qualifies, no evidence never does).
  C18 (SR-NO-DESELECT, DECISIONS_SURROGATE) the shipped registry carries no `deselect` key anywhere: a test that cannot run at a head is fixed or named in `optional_skips`
     with a reason, never excluded by name (an excluded node is a claim nothing measures).
Every test builds a throw-away git repository; none touches the shared repository or a database (the database answer is replaced where the claim is
about how the evaluator READS it).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import trial_ready as tr  # noqa: E402
from git_env_scrub import scrubbed  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[4]
IDS = list(tr.REQUIRED_IDS)
GOOD = {"kind": "git_file", "path": "evidence.txt", "contains": ["green"]}
PASSING = "def test_ok():\n    assert 1 + 1 == 2\n"
FAILING = "def test_planted_false():\n    assert 1 + 1 == 3\n"
SKIPPING = "import pytest\n\ndef test_needs_db():\n    pytest.skip('no database')\n"


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                       capture_output=True, env=scrubbed(), check=True)
    return r.stdout.decode().strip()


def registry(parts_by_id=None, drop=(), duplicate=()):
    checks = []
    for cid in IDS:
        if cid in drop:
            continue
        checks.append({"id": cid, "claim": "claim " + cid, "parts": (parts_by_id or {}).get(cid, [dict(GOOD)])})
    for cid in duplicate:
        checks.append({"id": cid, "claim": "dup " + cid, "parts": [dict(GOOD)]})
    return {"schema": "trial_ready.checks/1", "checks": checks}


def commit(repo, files, message="c"):
    for rel, text in files.items():
        p = Path(repo) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def make(tmp_path, reg=None, files=None, name="repo"):
    repo = tmp_path / name
    repo.mkdir()
    git(repo, "init", "-q")
    base = {"evidence.txt": "all green\n", tr.DEFAULT_REGISTRY: json.dumps(reg if reg is not None else registry())}
    base.update(files or {})
    return repo, commit(repo, base)


def run(repo, tmp_path, ref="HEAD"):
    return tr.evaluate(repo, ref, tmp_path / "work", python=sys.executable)


def values(result):
    return {c["id"]: c["value"] for c in result["checks"]}


# ── C1 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_c1_all_25_true_at_one_commit_is_ready_and_the_output_is_the_schema(tmp_path):
    repo, sha = make(tmp_path)
    res = run(repo, tmp_path)
    assert res["ready"] is True
    assert list(res) == ["predicate", "head_sha", "evaluated_at", "checks", "ready"]
    assert res["predicate"] == "TRIAL_READY/1" and res["head_sha"] == sha and len(sha) == 40
    assert [c["id"] for c in res["checks"]] == IDS
    for c in res["checks"]:
        assert list(c) == ["id", "claim", "value", "evidence_ref", "sha256"]
        assert c["value"] is True and c["claim"] == "claim " + c["id"] and c["evidence_ref"] and len(c["sha256"]) == 64


# ── C2 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_c2_unreadable_evidence_is_null_and_null_is_not_ready(tmp_path):
    bad = {"kind": "git_file", "path": "no/such/file.txt", "contains": ["x"]}
    repo, _ = make(tmp_path, registry({"T07": [bad]}))
    res = run(repo, tmp_path)
    v = values(res)
    assert v["T07"] is None and all(v[i] is True for i in IDS if i != "T07")
    assert res["ready"] is False


def test_c2_an_unbound_part_and_an_oracle_absent_from_the_commit_are_null(tmp_path):
    parts = {"T01": [{"kind": "unbound", "needs": "lane R1"}],
             "T02": [{"kind": "pytest", "tests": ["tests/test_not_there.py"]}],
             "T03": [dict(GOOD), {"kind": "unbound"}]}                     # one true part beside an unbound one is still null
    repo, _ = make(tmp_path, registry(parts))
    v = values(run(repo, tmp_path))
    assert v["T01"] is None and v["T02"] is None and v["T03"] is None
    assert tr.is_ready(run(repo, tmp_path)["checks"]) is False


def test_c2_a_skipped_oracle_is_not_a_pass(tmp_path):
    repo, _ = make(tmp_path, registry({"T04": [{"kind": "pytest", "tests": ["tests/test_skip.py"]}]}), {"tests/test_skip.py": SKIPPING})
    res = run(repo, tmp_path)
    assert values(res)["T04"] is None and res["ready"] is False


def test_c2_a_passing_oracle_that_ran_reads_true(tmp_path):
    repo, _ = make(tmp_path, registry({"T04": [{"kind": "pytest", "tests": ["tests/test_ok.py"]}]}), {"tests/test_ok.py": PASSING})
    res = run(repo, tmp_path)
    assert values(res)["T04"] is True and res["ready"] is True


def test_c2_the_three_valued_and_never_turns_a_null_into_true():
    assert tr.combine([True, True]) is True
    assert tr.combine([True, None]) is None
    assert tr.combine([None, None]) is None
    assert tr.combine([]) is None
    assert tr.combine([True, None, False]) is False


# ── C3 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_c3_a_check_missing_from_the_registry_is_not_ready(tmp_path):
    repo, _ = make(tmp_path, registry(drop=("T13",)))
    res = run(repo, tmp_path)
    c = next(x for x in res["checks"] if x["id"] == "T13")
    assert c["value"] is None and c["claim"] is None and c["evidence_ref"] is None and c["sha256"] is None
    assert res["ready"] is False and len(res["checks"]) == 25


def test_c3_a_missing_registry_file_and_a_duplicated_check_are_not_ready(tmp_path):
    repo, _ = make(tmp_path, registry(duplicate=("T05",)))
    res = run(repo, tmp_path)
    assert values(res)["T05"] is None and res["ready"] is False
    repo2 = tmp_path / "bare"
    repo2.mkdir()
    git(repo2, "init", "-q")
    commit(repo2, {"evidence.txt": "all green\n"})
    res2 = tr.evaluate(repo2, "HEAD", tmp_path / "work2", python=sys.executable)
    assert all(c["value"] is None for c in res2["checks"]) and res2["ready"] is False


def test_c3_ready_needs_each_required_id_exactly_once_whatever_the_caller_passes():
    def row(i, v=True):
        return {"id": i, "claim": "c", "value": v, "evidence_ref": "e", "sha256": "s"}
    full = [row(i) for i in IDS]
    assert tr.is_ready(full) is True
    assert tr.is_ready(full[:-1]) is False                                               # 24 true checks, one required id absent
    assert tr.is_ready(full + [row("T05")]) is False                                     # one id twice
    assert tr.is_ready(full + [row("T99", None)]) is False                               # an unknown extra that is not true
    assert tr.is_ready(full + [row("T99")]) is True


# ── C4 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_c4_a_planted_false_detector_reads_false_and_is_not_ready(tmp_path):
    forbidden = {"kind": "git_file", "path": "evidence.txt", "absent": ["green"]}                 # the forbidden string IS present
    parts = {"T14": [{"kind": "pytest", "tests": ["tests/test_bad.py"]}], "T15": [forbidden]}
    repo, _ = make(tmp_path, registry(parts), {"tests/test_bad.py": FAILING})
    res = run(repo, tmp_path)
    v = values(res)
    assert v["T14"] is False and v["T15"] is False and res["ready"] is False


def test_c4_a_false_part_beside_an_unreadable_one_is_false_not_null(tmp_path):
    parts = {"T16": [{"kind": "unbound"}, {"kind": "git_file", "path": "evidence.txt", "contains": ["red"]}]}
    repo, _ = make(tmp_path, registry(parts))
    assert values(run(repo, tmp_path))["T16"] is False


# ── C5 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_c5_a_work_tree_at_another_commit_yields_no_true(tmp_path):
    repo, first = make(tmp_path)
    commit(repo, {"other.txt": "later\n"}, "second")
    res = tr.evaluate(repo, first, tmp_path / "work", python=sys.executable)         # the ref is the first commit, the tree is at the second
    assert res["head_sha"] == first and not any(c["value"] is True for c in res["checks"]) and res["ready"] is False
    tr_ok = {"T08": [{"kind": "pytest", "tests": ["tests/test_ok.py"]}]}
    repo2, _ = make(tmp_path, registry(tr_ok), {"tests/test_ok.py": PASSING}, name="r2")
    git(repo2, "checkout", "-q", "--detach", "HEAD")
    assert values(run(repo2, tmp_path))["T08"] is True                                  # control: at the commit it does read true


def test_c5_a_dirty_tracked_file_yields_no_true(tmp_path):
    repo, _ = make(tmp_path)
    (repo / "evidence.txt").write_text("edited after the commit\n")
    res = run(repo, tmp_path)
    assert not any(c["value"] is True for c in res["checks"]) and res["ready"] is False


def test_c5_a_detector_that_moves_the_tree_voids_the_run(tmp_path):
    mutator = "import pathlib\n\ndef test_ok():\n    pathlib.Path(__file__).parent.parent.joinpath('evidence.txt').write_text('mutated\\n')\n"
    repo, _ = make(tmp_path, registry({"T09": [{"kind": "pytest", "tests": ["tests/test_mut.py"]}]}), {"tests/test_mut.py": mutator})
    res = run(repo, tmp_path)
    assert not any(c["value"] is True for c in res["checks"]) and res["ready"] is False


def test_c5_the_registry_of_the_evaluated_commit_is_the_one_that_decides(tmp_path):
    repo, first = make(tmp_path)
    weaker = registry({i: [{"kind": "git_file", "path": "evidence.txt", "contains": []}] for i in IDS})
    commit(repo, {tr.DEFAULT_REGISTRY: json.dumps(weaker)}, "weaken the registry")
    git(repo, "checkout", "-q", "--detach", first)
    assert run(repo, tmp_path)["ready"] is True                                          # the first commit's own registry decides
    git(repo, "checkout", "-q", "-")
    assert run(repo, tmp_path)["ready"] is False                                         # the weaker registry declares nothing to look for: null


# ── C6 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _db_check(monkeypatch, tmp_path, answer, dsn="postgresql://u:dummy@127.0.0.1:55433/lane", env="TRIAL_READY_TEST_DSN"):
    monkeypatch.setenv(env, dsn) if dsn else monkeypatch.delenv(env, raising=False)
    monkeypatch.setattr(tr, "_run_sql", lambda d, s: (answer, "ok" if answer is not None else "database not readable"))
    part = {"kind": "db_sql", "dsn_env": env, "sql": "SELECT true", "expect": "t"}
    repo, _ = make(tmp_path, registry({"T25": [part]}), name="db%d" % abs(hash((answer, dsn))))
    res = run(repo, tmp_path)
    return next(c for c in res["checks"] if c["id"] == "T25"), res


def test_c6_a_database_part_reads_true_only_from_the_expected_answer(monkeypatch, tmp_path):
    c, res = _db_check(monkeypatch, tmp_path, "t")
    assert c["value"] is True and res["ready"] is True
    assert "dummy" not in json.dumps(res) and c["evidence_ref"] == "db:127.0.0.1:55433/lane"
    assert _db_check(monkeypatch, tmp_path, "f")[0]["value"] is False
    assert _db_check(monkeypatch, tmp_path, None)[0]["value"] is None
    assert _db_check(monkeypatch, tmp_path, "")[0]["value"] is None


def test_c6_an_unset_or_remote_dsn_is_null_and_never_queried(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(tr, "_run_sql", lambda d, s: calls.append(d) or ("t", "ok"))
    part = {"kind": "db_sql", "dsn_env": "TRIAL_READY_TEST_DSN2", "sql": "SELECT true"}
    repo, _ = make(tmp_path, registry({"T25": [part]}))
    monkeypatch.delenv("TRIAL_READY_TEST_DSN2", raising=False)
    assert values(run(repo, tmp_path))["T25"] is None
    monkeypatch.setenv("TRIAL_READY_TEST_DSN2", "postgresql://u:pw@db.example.com:5432/prod")
    assert values(run(repo, tmp_path))["T25"] is None
    assert calls == []


def test_c6_the_migration_ledger_must_hold_every_file_the_commit_lists(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIAL_READY_TEST_DSN3", "postgresql://u@127.0.0.1:55433/lane")
    part = {"kind": "db_migrations", "dsn_env": "TRIAL_READY_TEST_DSN3", "prefixes": ["1401_", "1402_"]}
    files = {"platform/migrations/1401_a.sql": "--", "platform/migrations/1402_b.sql": "--"}
    repo, _ = make(tmp_path, registry({"T23": [part]}), files)

    def applied(names):
        monkeypatch.setattr(tr, "_run_sql", lambda d, s: ("\n".join(names), "ok"))
        return values(run(repo, tmp_path))["T23"]
    assert applied(["1401_a.sql", "1402_b.sql", "001_baseline.sql"]) is True
    assert applied(["1401_a.sql"]) is False                                              # the ledger lacks a file the commit lists
    repo2, _ = make(tmp_path, registry({"T23": [dict(part, prefixes=["1403_"])]}), files, name="r2")
    assert values(run(repo2, tmp_path))["T23"] is False                                  # the commit lists no 1403 file at all


def test_c6_the_allocation_ledger_part_needs_every_number_recorded(tmp_path):
    ledger = tmp_path / "alloc.json"
    ledger.write_text(json.dumps({"allocated": {"1400": "A", "1401": "B"}}))
    part = {"kind": "json_keys", "path": str(ledger), "keys": ["1400", "1401"]}
    repo, _ = make(tmp_path, registry({"T23": [part]}))
    assert values(run(repo, tmp_path))["T23"] is True
    ledger.write_text(json.dumps({"allocated": {"1400": "A"}}))
    assert values(run(repo, tmp_path))["T23"] is False
    ledger.unlink()
    assert values(run(repo, tmp_path))["T23"] is None


# ── C7 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_c7_exit_code_follows_ready_and_a_stale_file_never_survives_a_failed_run(tmp_path, capsys):
    repo, _ = make(tmp_path)
    out = tmp_path / "out" / "trial_ready.json"
    out.parent.mkdir()
    assert tr.main(["--repo", str(repo), "--ref", "HEAD", "--out", str(out), "--python", sys.executable]) == 0
    assert json.loads(out.read_text())["ready"] is True
    assert tr.main(["--repo", str(repo), "--ref", "no-such-ref", "--out", str(out)]) == 2
    assert not out.exists()                                                              # the earlier ready:true is gone
    repo2, _ = make(tmp_path, registry(drop=("T01",)), name="r2")
    assert tr.main(["--repo", str(repo2), "--ref", "HEAD", "--out", str(out), "--python", sys.executable]) == 1
    assert json.loads(out.read_text())["ready"] is False


# ── C8 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# TR-BIND (SR madhav-44, 2026-10-23): "an unbound check is a TR auto-arm blocker" -- T11 NDH, T12 SELECT-130, T13 DASH readback and T22 lane ledger are bound to their lanes' oracles
# (a part that cannot run reads null, never true); no check may be unbound, so a new `unbound` part fails
STILL_UNBOUND: set = set()


def test_c8_the_shipped_registry_names_the_25_checks_and_points_only_at_real_oracles():
    doc = json.loads((REPO_ROOT / tr.DEFAULT_REGISTRY).read_text(encoding="utf-8"))
    assert [c["id"] for c in doc["checks"]] == IDS
    for c in doc["checks"]:
        assert c["claim"] and c["detector"] and c["parts"], c["id"]
        for p in c["parts"]:
            assert p["kind"] in tr.DETECTORS, (c["id"], p)
            if p["kind"] == "pytest":
                for t in p["tests"]:
                    cwd = p.get("cwd", ".")
                    present = (REPO_ROOT / cwd / t.split("::")[0]).is_file()
                    # an oracle of a lane that has not reached this branch is named with the branch that lands it; once it is here the name must resolve
                    assert present or p.get("lands_with"), (c["id"], t)
                    assert "NOT-FOUND" not in str(p.get("lands_with")), (c["id"], t)
            if p["kind"] == "git_file":
                assert (REPO_ROOT / p["path"]).is_file(), (c["id"], p["path"])
            if p["kind"] == "json_field_eq":
                assert p["fields"] and all(sum(1 for k in ("equals", "equals_head", "equals_patch_id_of") if k in f and (k != "equals_head" or f[k])) == 1 for f in p["fields"]), (c["id"], p)
            if p["kind"] == "db_migrations":
                assert p.get("mode") == "all" or p.get("prefixes"), (c["id"], p)


def test_c8_no_check_of_the_shipped_registry_is_unbound():
    doc = json.loads((REPO_ROOT / tr.DEFAULT_REGISTRY).read_text(encoding="utf-8"))
    unbound = {c["id"] for c in doc["checks"] if any(p["kind"] == "unbound" for p in c["parts"])}
    assert unbound <= STILL_UNBOUND, sorted(unbound - STILL_UNBOUND)


def test_c8_a_check_with_no_bound_detector_cannot_read_true_from_the_shipped_registry(tmp_path):
    """Plan: 'Nothing in the list is a rolling run is green' - the shipped registry binds nothing to a lane state."""
    doc = json.loads((REPO_ROOT / tr.DEFAULT_REGISTRY).read_text(encoding="utf-8"))
    repo, _ = make(tmp_path, doc)
    v = values(run(repo, tmp_path))
    unbound_only = [c["id"] for c in doc["checks"] if all(p["kind"] == "unbound" for p in c["parts"])]
    assert all(v[i] is None for i in unbound_only)
    assert not tr.is_ready(run(repo, tmp_path)["checks"])


# ── C9 json_field_eq (TR-BIND) ───────────────────────────────────────────────────────────────────────────────────────────────────────

def _jf(tmp_path, record, fields, path="rec.json", repo_name="jf", raw=None):
    f = tmp_path / path
    if raw is not None:
        f.write_text(raw)
    elif record is not None:
        f.write_text(json.dumps(record))
    part = {"kind": "json_field_eq", "path": str(f), "fields": fields}
    repo, sha = make(tmp_path, registry({"T24": [part]}), name=repo_name)
    return values(run(repo, tmp_path))["T24"], sha


def test_c9_a_record_reads_true_only_when_every_field_holds_for_this_head(tmp_path):
    fields = [{"field": "ready", "equals": True}, {"field": "inputs.head.value", "equals_head": True}]
    repo, sha = make(tmp_path, registry(), name="probe")                         # any commit: its sha is what the record must name
    rec = {"ready": True, "inputs": {"head": {"value": sha}}}
    (tmp_path / "rec.json").write_text(json.dumps(rec))
    part = {"kind": "json_field_eq", "path": str(tmp_path / "rec.json"), "fields": fields}
    repo, sha2 = make(tmp_path, registry({"T24": [part]}), name="r2")
    assert sha2 != sha
    assert values(run(repo, tmp_path))["T24"] is False                           # the record names ANOTHER head: stale evidence is false, not true
    rec["inputs"]["head"]["value"] = sha2
    (tmp_path / "rec.json").write_text(json.dumps(rec))
    assert values(run(repo, tmp_path))["T24"] is True
    rec["ready"] = False
    (tmp_path / "rec.json").write_text(json.dumps(rec))
    assert values(run(repo, tmp_path))["T24"] is False


def test_c9_the_type_must_match_so_one_is_not_true(tmp_path):
    assert _jf(tmp_path, {"ready": 1}, [{"field": "ready", "equals": True}])[0] is False
    assert _jf(tmp_path, {"ready": "true"}, [{"field": "ready", "equals": True}], repo_name="b")[0] is False
    assert _jf(tmp_path, {"ready": True}, [{"field": "ready", "equals": True}], repo_name="c")[0] is True


def test_c9_unreadable_evidence_is_null_never_true(tmp_path):
    f = [{"field": "a.b", "equals": "x"}]
    assert _jf(tmp_path, None, f)[0] is None                                      # no record at all
    assert _jf(tmp_path, None, f, raw="{not json", repo_name="b")[0] is None
    assert _jf(tmp_path, {"a": {}}, f, repo_name="c")[0] is None                  # field absent
    assert _jf(tmp_path, {"a": {"b": None}}, f, repo_name="d")[0] is None        # JSON null is no evidence
    assert _jf(tmp_path, {"a": "scalar"}, f, repo_name="e")[0] is None           # the path runs through a non-object
    assert _jf(tmp_path, {"a": {"b": "x"}}, [], repo_name="f")[0] is None         # a part that declares no field proves nothing
    both = [{"field": "a.b", "equals": "x", "equals_head": True}]
    assert _jf(tmp_path, {"a": {"b": "x"}}, both, repo_name="g")[0] is None      # ambiguous declaration
    neither = [{"field": "a.b"}]
    assert _jf(tmp_path, {"a": {"b": "x"}}, neither, repo_name="h")[0] is None


def test_c9_a_false_field_beside_a_missing_one_is_false(tmp_path):
    f = [{"field": "a", "equals": 1}, {"field": "missing", "equals": 2}]
    assert _jf(tmp_path, {"a": 9}, f)[0] is False
    assert _jf(tmp_path, {"a": 1}, f, repo_name="b")[0] is None


def test_c9_the_head_placeholder_names_a_per_head_file(tmp_path):
    repo, sha = make(tmp_path, registry({"T24": [{"kind": "json_field_eq", "path": str(tmp_path / "{head}.json"), "fields": [{"field": "ok", "equals": True}]}]}))
    assert values(run(repo, tmp_path))["T24"] is None                             # no file for this head yet
    (tmp_path / (sha + ".json")).write_text(json.dumps({"ok": True}))
    assert values(run(repo, tmp_path))["T24"] is True


# ── C10 db_migrations mode all (TR-BIND) ─────────────────────────────────────────────────────────────────────────────────────────────

def test_c10_every_file_the_commit_lists_must_be_in_the_ledger(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIAL_READY_TEST_DSN4", "postgresql://u@127.0.0.1:55433/lane")
    part = {"kind": "db_migrations", "dsn_env": "TRIAL_READY_TEST_DSN4", "mode": "all"}
    files = {"platform/migrations/001_a.sql": "--", "platform/migrations/1401_b.sql": "--", "platform/migrations/README.md": "not a migration"}
    repo, _ = make(tmp_path, registry({"T25": [part]}), files)

    def applied(names):
        monkeypatch.setattr(tr, "_run_sql", lambda d, s: ("\n".join(names), "ok"))
        return values(run(repo, tmp_path))["T25"]
    assert applied(["001_a.sql", "1401_b.sql", "extra_from_an_older_head.sql"]) is True
    assert applied(["001_a.sql"]) is False                                       # a protected file that was skipped reads as missing
    assert applied([""]) is False


def test_c10_an_empty_list_an_unknown_mode_or_a_prefix_less_part_is_null(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIAL_READY_TEST_DSN5", "postgresql://u@127.0.0.1:55433/lane")
    monkeypatch.setattr(tr, "_run_sql", lambda d, s: ("001_a.sql", "ok"))
    base = {"kind": "db_migrations", "dsn_env": "TRIAL_READY_TEST_DSN5"}
    repo, _ = make(tmp_path, registry({"T25": [dict(base, mode="all")]}), name="empty")        # the commit lists no migration at all
    assert values(run(repo, tmp_path))["T25"] is None
    repo2, _ = make(tmp_path, registry({"T25": [dict(base, mode="everything")]}), {"platform/migrations/001_a.sql": "--"}, name="mode")
    assert values(run(repo2, tmp_path))["T25"] is None
    repo3, _ = make(tmp_path, registry({"T25": [dict(base)]}), {"platform/migrations/001_a.sql": "--"}, name="noprefix")
    assert values(run(repo3, tmp_path))["T25"] is None
    monkeypatch.delenv("TRIAL_READY_TEST_DSN5")
    repo4, _ = make(tmp_path, registry({"T25": [dict(base, mode="all")]}), {"platform/migrations/001_a.sql": "--"}, name="nodsn")
    assert values(run(repo4, tmp_path))["T25"] is None


# ── C11 pytest env and deselect (TR-BIND) ────────────────────────────────────────────────────────────────────────────────────────────

TWO = "def test_good():\n    assert True\n\ndef test_env_dependent():\n    assert False\n"


def test_c11_a_deselected_test_is_not_run_and_the_rest_decide(tmp_path):
    part = {"kind": "pytest", "tests": ["t_two.py"], "deselect": ["t_two.py::test_env_dependent"]}
    repo, _ = make(tmp_path, registry({"T14": [part]}), {"t_two.py": TWO})
    assert values(run(repo, tmp_path))["T14"] is True
    repo2, _ = make(tmp_path, registry({"T14": [{"kind": "pytest", "tests": ["t_two.py"]}]}), {"t_two.py": TWO}, name="plain")
    assert values(run(repo2, tmp_path))["T14"] is False                          # without the deselect the same file fails: the option is what changes the verdict


def test_c11_a_part_whose_every_test_is_deselected_is_null_not_true(tmp_path):
    part = {"kind": "pytest", "tests": ["t_one.py"], "deselect": ["t_one.py::test_only"]}
    repo, _ = make(tmp_path, registry({"T14": [part]}), {"t_one.py": "def test_only():\n    assert True\n"})
    assert values(run(repo, tmp_path))["T14"] is None


def test_c11_the_repo_placeholder_in_env_is_the_evaluated_work_tree(tmp_path):
    probe = "import os\nfrom pathlib import Path\n\ndef test_env():\n    assert Path(os.environ['KY_TEST_CHECKOUT']).resolve() == Path(__file__).resolve().parent\n"
    part = {"kind": "pytest", "tests": ["t_env.py"], "env": {"KY_TEST_CHECKOUT": "{repo}"}}
    repo, _ = make(tmp_path, registry({"T14": [part]}), {"t_env.py": probe})
    assert values(run(repo, tmp_path))["T14"] is True
    repo2, _ = make(tmp_path, registry({"T14": [dict(part, env={"KY_TEST_CHECKOUT": "/nowhere"})]}), {"t_env.py": probe}, name="lit")
    assert values(run(repo2, tmp_path))["T14"] is False


def test_c11_a_relative_scratch_directory_still_lets_a_passing_oracle_read_true(tmp_path, monkeypatch):
    repo, _ = make(tmp_path, registry({"T14": [{"kind": "pytest", "cwd": "sub", "tests": ["t_ok.py"]}]}), {"sub/t_ok.py": PASSING})
    monkeypatch.chdir(tmp_path)
    res = tr.evaluate(repo, "HEAD", Path("rel_work"), python=sys.executable)
    assert values(res)["T14"] is True


# ── C12 the landed harness is the accepted v3.1 ──────────────────────────────────────────────────────────────────────────────────────

HARNESS_DIR = "00_ARCHITECTURE/briefs/kalayantra/fleet/trial_harness"
# v3.1 (review X-20261022T075423Z-review-t1b-harness2, ACCEPTED round 2 = efb0922a...787c) + the cockpit's B4 lane-db overlay (TR_GAPS B4.3: run_trial.sh, trial_slice.py,
# tests/test_lane_db_overlay.py) = the harness the trial actually runs (installed copy of job X-20261021T105440Z-od1-T1-harness; PR #3874 review N-1)
# + the G5-CPU attributed-CPU method for TR gate G-5 (fleet/trial_harness/g5_cpu.py, SR-G5-LOAD; PR #3880) = c38d93f5... (tr-bind's pin was 7d8fbd87...)
# HARNESS-3.2 (item H-1, PRETR-3a D-8/D-9/D-10; previous pins 7d8fbd87...1f91, 7c3218b8...2c8b, c38d93f5...9be): the cross-check rebuilds P2/P1 windows with the writer's own sources under the final profile,
# G-4 is scoped to the trial classes, G-5 reads NOT_EVALUATED for a slice or a loaded machine (tests/test_harness_32.py, mutants_h32.py), on top of the G5-CPU harness
# HARNESS-3.2b (item harness-32b; previous pin f8f71805...fd0e): the closed G-2 set carries no_aspect_rule_defined_at_offset (SR-D6-OBJECTIVE-UNKNOWN), and G-3 stops with
# near_station_tie_cap_exceeded above 0.5 % of a class's windows, NOT_EVALUATED where the count is unavailable (SR-NEAR-STATION-TIE; tests/test_harness_32b.py)
# HARNESS-3.3 (item harness-33; previous pin 2cf47ce9...7c29; PRETR-early O-1, O-2): a raised substep is booked under its own stage kind (never `empty`), and a COLLECT mode (--collect /
# TRIAL_COLLECT=1) lets a diagnostic run continue past a class's first defect, failing the class at the END with the full list (tests/test_harness_33.py, mutants_h33.py)
# AMD64-DOCKER (item amd64-docker; previous pin 55c3a775...418d; ruling SR-T24-AMD64-DOCKER): the one amd64 slice runs in a linux/amd64 Docker container (Rosetta/QEMU emulation) against a PG 15 locale-C
# sibling container; the arch is read by an in-container probe, the emulation is recorded (platform_notes), G-5 reads NOT_EVALUATED for such a run (tests/test_amd64_docker.py, mutants_amd64.py)
# G6-P1-CROSSCHECK (item g6-p1; previous pin 4822bcf0...fa7a; ruling SR-NEARMISS-DOMAIN-TAIL-AMEND-1, G-6): the cross-check rebuilds a P1 window through the builder's own
# per-instant agent_nature channel (draft_windows' has_channel_fn path), never record_channel's P1 refusal (job X-20261023T111950Z-g6-p1-crosscheck; tests/test_harness_32.py test_h_a3)
# SR-BASELINE-OVERLAY-SKIP (harness-only change; previous pin f4cffcd8...0cc6; job X-20261023T121013Z-baseline-overlay-skip): in BASELINE mode only (make_baseline.sh -> TRIAL_BASELINE_MODE=1, default policy,
# label baseline) a mandatory overlay migration the checkout lacks is skipped BY NAME and recorded in baseline_12.json when the checkout also lacks the code that requires it; a trial run still refuses
# (trial_slice.py plan_overlay/requiring_code, run_trial.sh, make_baseline.sh, tests/test_baseline_overlay_skip.py)
# SR-BASELINE-OVERLAY-SKIP review close (previous pin a1b81add...e800242; job X-20261023T124421Z-g-fix): the requiring-code probe's tests exclusion reads the path relative to the code root (a checkout
# under a directory named tests is no longer skipped); new oracles: stored mode governs setup_lane, a resume under another mode is refused, an absent code root refuses
# BASELINE-12-SNAPSHOT (cockpit 2026-10-23; previous pin 20c54873...2999): baseline_12.json re-made WITH the noninterference snapshot on linux/amd64 (default policy, main c23cda8ab, harness 6816b4572; 4,509 windows; 1402 skipped by name, SR-BASELINE-OVERLAY-SKIP) so G-7 reads a real value
# TR-READY-FIXES (cockpit 2026-10-23; previous pin 9ad94476...fb6c; SR-T14-FIX-NOT-EXCLUDE, harness TEST-only change; job X-20261023T134421Z-tr-ready-fixes): tests/test_driver.py states the solver-probe claim for a
# solver-carrying head (present + counts at the real window_solver; absent + counts nothing at a package copy with none) instead of asserting the pre-solver export; tests/test_g5_cpu.py test_c2 judges the
# CPU growth against the wall GROWTH of the same experiment and retries an attempt in which the hogs did not starve the builder; test_c4 judges the wall/CPU agreement
# normalised by a same-process calibrated reference (a pure burn's wall per CPU second), so an ambient load cannot fail either
HARNESS_V31_DIGEST = "7859ed763e18428d3cf6c3065880c896fa5796ede2a28b6487e01e6f24aea7eb"


def harness_digest(root):
    """The reviewer's recipe: sha256 over the sorted `sha256sum`-style per-file lines ('<hash>  ./<path>'), `__pycache__` excluded."""
    root = Path(root)
    rels = sorted("./" + p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    lines = "".join("%s  %s\n" % (hashlib.sha256((root / r).read_bytes()).hexdigest(), r) for r in rels)
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def test_c12_the_landed_trial_harness_is_the_accepted_v3_1():
    assert harness_digest(REPO_ROOT / HARNESS_DIR) == HARNESS_V31_DIGEST


def test_c12_the_digest_moves_when_any_harness_byte_changes(tmp_path):
    import shutil
    copy = tmp_path / "h"
    shutil.copytree(str(REPO_ROOT / HARNESS_DIR), str(copy), ignore=shutil.ignore_patterns("__pycache__"))
    assert harness_digest(copy) == HARNESS_V31_DIGEST
    gates = copy / "gates.py"
    gates.write_bytes(gates.read_bytes() + b"\n")
    assert harness_digest(copy) != HARNESS_V31_DIGEST


# ── C13-C15 PR #3874 review fixes ────────────────────────────────────────────────────────────────────────────────────────────────────

RUN_TR = "/Users/Dev/kalayantra/run/TR"


def shipped():
    return json.loads((REPO_ROOT / tr.DEFAULT_REGISTRY).read_text(encoding="utf-8"))


def shipped_check(cid):
    return next(c for c in shipped()["checks"] if c["id"] == cid)


def retarget(check, run_dir):
    """The shipped check with its external record directory moved under a scratch directory (the parts are otherwise exactly the shipped ones)."""
    return json.loads(json.dumps(check).replace(RUN_TR, str(run_dir)))


def slice_records(run_dir, sha, *, head=None, arch="linux/amd64", kind="qualifying_run", status="COMPLETE", complete=True, eq_head=None):
    """What a finished amd64_slice run leaves: <label>_report.json, equivalence/eq_pinned_inputs.json and equivalence/equivalence_record.json (trial_slice.py / equivalence_record.py)."""
    base = Path(run_dir) / "amd64_slice"
    (base / "equivalence").mkdir(parents=True, exist_ok=True)
    (base / "amd64_slice_report.json").write_text(json.dumps({"code": {"head": head or sha}, "equivalence_record": {"status": status, "head": eq_head or head or sha}}))
    (base / "equivalence" / "eq_pinned_inputs.json").write_text(json.dumps({"runtime": {"kind": kind, "arch": arch}}))
    (base / "equivalence" / "equivalence_record.json").write_text(json.dumps({"complete": complete, "runtime_kind": kind, "E6": {"commit": head or sha}}))


def t24_value(tmp_path, name, write):
    repo, sha = make(tmp_path, registry({"T24": retarget(shipped_check("T24"), tmp_path / name)["parts"]}), name=name)
    write(tmp_path / name, sha)
    return values(run(repo, tmp_path))["T24"]


def test_c13_a_readiness_record_alone_never_reads_true_for_t24(tmp_path):
    """Review B-1: `trial_slice.py amd64-readiness` writes ready:true for any well-formed 64-hex digest with no image and no run (it says `not_run: true`).
    Reversion: bind T24 back to amd64_readiness.json -> this record reads true and the assertion fails."""
    def only_readiness(d, sha):
        d.mkdir(parents=True, exist_ok=True)
        (d / "amd64_readiness.json").write_text(json.dumps({"schema": "ky.amd64_slice_readiness/1", "not_run": True, "ready": True,
                                                            "inputs": {"head": {"value": sha, "present": True}, "image_digest": {"value": "sha256:" + "0" * 64, "present": True}}}))
    assert t24_value(tmp_path, "ro", only_readiness) is None


def test_c13_t24_reads_true_from_the_complete_qualifying_amd64_run_of_this_head(tmp_path):
    assert t24_value(tmp_path, "ok", lambda d, sha: slice_records(d, sha)) is True


@pytest.mark.parametrize("name,over", [("arm64", {"arch": "linux/arm64"}), ("rolling", {"kind": "rolling_diagnostic"}), ("incomplete", {"complete": False}),
                                       ("refused", {"status": "REFUSED"}), ("other_head", {"head": "1" * 40}), ("eq_other_head", {"eq_head": "2" * 40})])
def test_c13_t24_reads_false_when_the_slice_ran_elsewhere_or_for_another_head(tmp_path, name, over):
    """Each field the claim names (arch, runtime kind, completeness, status, head) is measured: a record that says otherwise reads false, not true."""
    assert t24_value(tmp_path, name, lambda d, sha: slice_records(d, sha, **over)) is False


def test_c13_t24_is_null_without_the_slice_run(tmp_path):
    assert t24_value(tmp_path, "none", lambda d, sha: None) is None


T20_SKY_NODE = "tests/l3/gochara/test_a53_input_vector.py::test_the_sky_convention_content_digest_moves_when_the_stored_content_does_with_the_same_id"


def test_c14_t20_runs_the_sky_convention_content_digest_test_instead_of_excluding_or_skipping_it():
    """SR-NO-DESELECT. The claim "the sky convention's content digest moves when the stored content does, with the same id" is measured by this test at T20, not
    excluded: the node is bound by file (no name-level deselect, no optional_skips), and its body stages the edit by switching off the insert-only trigger
    (platform/migrations/1153_gochara_sky_event_substrate.sql:609-611, ka_gochara_sky_convention_immutable) in the per-test database, with no `pytest.skip` left to hide it.
    Reversion: restore the `except Exception: pytest.skip(...)` -> this test fails."""
    parts = [p for p in shipped_check("T20")["parts"] if p["kind"] == "pytest" and T20_SKY_NODE.split("::")[0] in p["tests"]]
    assert len(parts) == 1 and "deselect" not in parts[0] and "optional_skips" not in parts[0]
    mig = (REPO_ROOT / "platform/migrations/1153_gochara_sky_event_substrate.sql").read_text(encoding="utf-8").splitlines()[608:611]
    assert any("ka_gochara_sky_convention_immutable" in l for l in mig) and any("BEFORE UPDATE OR DELETE" in l for l in mig)
    src = (REPO_ROOT / "platform/python-sidecar" / T20_SKY_NODE.split("::")[0]).read_text(encoding="utf-8")
    start = src.index("def " + T20_SKY_NODE.split("::")[1] + "(")
    body = src[start:src.index("\ndef ", start + 1)]
    assert "pytest.skip" not in body and "DISABLE TRIGGER ka_gochara_sky_convention_immutable" in body and "ENABLE TRIGGER ka_gochara_sky_convention_immutable" in body


def test_c14_t20_claim_states_the_pin_once_rule_in_full():
    """Review N-4; ruling SR-GEOMETRY-PIN-ONCE (DECISIONS_SURROGATE 2026-10-22T09:15:49Z)."""
    claim = shipped_check("T20")["claim"]
    assert "SR-GEOMETRY-PIN-ONCE" in claim and "recorded in the EQUIVALENCE_RECORD changelog with both causes; any further geometry change refuses" in claim


def test_c14_t10_locale_sensitive_part_pins_its_locale():
    """Review N-3: the throwaway postgres of test_sr_doctrine_h_node_dignity_1401.py refuses to start without a valid locale ('postmaster became multithreaded')."""
    part = next(p for p in shipped_check("T10")["parts"] if p["kind"] == "pytest" and "test_sr_doctrine_h_node_dignity_1401.py" in p["tests"][0])
    assert part["env"]["LC_ALL"] == "en_US.UTF-8" and part["env"]["LANG"] == "en_US.UTF-8"


def _t21_repo(tmp_path, name):
    repo = tmp_path / name
    repo.mkdir()
    git(repo, "init", "-q")
    base = commit(repo, {"a.txt": "one\n"})
    git(repo, "update-ref", "refs/remotes/origin/main", base)
    head = commit(repo, {"a.txt": "one\ntwo\n", tr.DEFAULT_REGISTRY: json.dumps(registry({"T21": retarget(shipped_check("T21"), tmp_path / name / "..")["parts"]}))})
    return repo, head


def test_c15_t21_matches_the_verdict_patch_id_against_one_recomputed_from_the_repo(tmp_path):
    """Review N-2. Source: the reviewer's recipe `git patch-id --stable` of base...head. Reversion: drop the patch_id field -> a verdict naming another patch reads true."""
    repo, head = _t21_repo(tmp_path, "r")
    real = tr._patch_id(repo, "origin/main", head)
    assert real and len(real) == 40
    verdict = tmp_path / "r" / ".." / "RVINT_VERDICT.json"
    verdict.write_text(json.dumps({"proposed_verdict": {"verdict": "ACCEPTED", "head": head, "patch_id": real}}))
    assert values(run(repo, tmp_path))["T21"] is True
    verdict.write_text(json.dumps({"proposed_verdict": {"verdict": "ACCEPTED", "head": head, "patch_id": "f" * 40}}))
    assert values(run(repo, tmp_path))["T21"] is False                            # a verdict for another patch with the right head label
    verdict.write_text(json.dumps({"proposed_verdict": {"verdict": "ACCEPTED", "head": head}}))
    assert values(run(repo, tmp_path))["T21"] is None                             # no patch_id recorded: no evidence


def test_c15_an_unresolvable_base_makes_the_patch_id_field_null(tmp_path):
    repo, head = _t21_repo(tmp_path, "r2")
    git(repo, "update-ref", "-d", "refs/remotes/origin/main")
    (tmp_path / "RVINT_VERDICT.json").write_text(json.dumps({"proposed_verdict": {"verdict": "ACCEPTED", "head": head, "patch_id": "a" * 40}}))
    assert values(run(repo, tmp_path))["T21"] is None


# ── C16 lane_ledger (TR-BIND: T22) ───────────────────────────────────────────────────────────────────────────────────────────────────────

STUB_CHECKER = "import json, sys\na = sys.argv\nout = a[a.index('--json-out') + 1]\nopen(out, 'w').write(json.dumps({'value': %s}))\nsys.exit(%d)\n"


def _ledger_repo(tmp_path, exit_code, value, name="ll"):
    """A repo whose T22 part runs a STAND-IN checker at the commit (the shipped checker's own proof is test_lane_ledger_selftest.py)."""
    part = {"kind": "lane_ledger", "ledger_env": "TR_TEST_LEDGER", "checker": "stub_checker.py"}
    repo, _ = make(tmp_path, registry({"T22": [part]}), {"stub_checker.py": STUB_CHECKER % (value, exit_code)}, name=name)
    return repo


def test_c16_the_checker_exit_and_reading_map_to_true_false_and_null(tmp_path, monkeypatch):
    (tmp_path / "ledger.json").write_text("{}")
    monkeypatch.setenv("TR_TEST_LEDGER", str(tmp_path / "ledger.json"))
    assert values(run(_ledger_repo(tmp_path, 0, "True", "a"), tmp_path))["T22"] is True
    assert values(run(_ledger_repo(tmp_path, 1, "False", "b"), tmp_path))["T22"] is False
    assert values(run(_ledger_repo(tmp_path, 2, "None", "c"), tmp_path))["T22"] is None                 # exit 2: the checker could not run -> null
    assert values(run(_ledger_repo(tmp_path, 0, "False", "d"), tmp_path))["T22"] is None                # exit 0 but a false reading: they disagree -> no evidence
    assert values(run(_ledger_repo(tmp_path, 1, "True", "e"), tmp_path))["T22"] is None


def test_c16_no_ledger_a_missing_checker_and_a_dirty_tree_read_null(tmp_path, monkeypatch):
    monkeypatch.delenv("TR_TEST_LEDGER", raising=False)
    assert values(run(_ledger_repo(tmp_path, 0, "True", "a"), tmp_path))["T22"] is None                 # no ledger rebuilt at this commit
    monkeypatch.setenv("TR_TEST_LEDGER", str(tmp_path / "ledger.json"))
    part = {"kind": "lane_ledger", "ledger_env": "TR_TEST_LEDGER", "checker": "nowhere.py"}
    repo, _ = make(tmp_path, registry({"T22": [part]}), name="b")
    assert values(run(repo, tmp_path))["T22"] is None
    repo = _ledger_repo(tmp_path, 0, "True", "c")
    (repo / "stub_checker.py").write_text("# edited after the commit\n")
    assert values(run(repo, tmp_path))["T22"] is None


def test_c16_the_shipped_checker_reads_false_for_a_ledger_built_at_another_head_and_null_for_one_it_cannot_read(tmp_path, monkeypatch):
    """The real checker, run by the real part, at a throwaway commit: an empty ledger names no lane (every required lane is missing) and was built at no head -> FALSE; garbage -> null."""
    shipped = (REPO_ROOT / "platform/scripts/governance/lane_ledger_check.py").read_text(encoding="utf-8")
    part = {"kind": "lane_ledger", "ledger_env": "TR_TEST_LEDGER"}
    repo, _ = make(tmp_path, registry({"T22": [part]}), {"platform/scripts/governance/lane_ledger_check.py": shipped})
    ledger = tmp_path / "ledger.json"
    monkeypatch.setenv("TR_TEST_LEDGER", str(ledger))
    ledger.write_text(json.dumps({"schema": "ky.lane_ledger/1", "integration_head": "0" * 40, "lanes": []}))
    assert values(run(repo, tmp_path))["T22"] is False
    ledger.write_text("not json")
    assert values(run(repo, tmp_path))["T22"] is None


def test_c16_the_shipped_t22_has_a_recomputing_detector_and_names_its_missing_input():
    t22 = shipped_check("T22")
    assert {p["kind"] for p in t22["parts"]} == {"pytest", "lane_ledger"}
    assert (REPO_ROOT / "platform/scripts/governance/lane_ledger_check.py").is_file() and "LANE_LEDGER.json rebuilt at this commit" in t22["note"]
    assert all(p["kind"] != "unbound" for c in json.loads((REPO_ROOT / tr.DEFAULT_REGISTRY).read_text(encoding="utf-8"))["checks"] for p in c["parts"])


# ── C16 skip / xfail / not-run is null unless declared optional (SR-EVALUATOR-SKIP-IS-NULL; N.8) ───────────────────────────────────────

MIXED = "import pytest\n\ndef test_ok():\n    assert True\n\ndef test_needs_db():\n    pytest.skip('no database')\n"
XFAILING = "import pytest\n\ndef test_ok():\n    assert True\n\n@pytest.mark.xfail(reason='known')\ndef test_known_bad():\n    assert False\n"
OPT = "t_mixed.py::test_needs_db"


def _c16(tmp_path, part, files, name="repo"):
    repo, _ = make(tmp_path, registry({"T04": [part]}), files, name=name)
    return values(run(repo, tmp_path))["T04"]


def test_c16_a_skip_beside_passing_tests_makes_the_part_null(tmp_path):
    """Ruling: any SKIP of a bound test makes the part null. Reversion: count only failures -> the part reads true."""
    assert _c16(tmp_path, {"kind": "pytest", "tests": ["t_mixed.py"]}, {"t_mixed.py": MIXED}) is None


def test_c16_an_xfail_beside_passing_tests_makes_the_part_null(tmp_path):
    """Ruling: xfail is not a pass. Reversion: treat xfail as passed -> true."""
    assert _c16(tmp_path, {"kind": "pytest", "tests": ["t_xf.py"]}, {"t_xf.py": XFAILING}) is None


def test_c16_a_declared_optional_skip_with_a_reason_keeps_the_part_true(tmp_path):
    """Ruling: unless that test's skip is explicitly declared optional with a reason. Reversion: ignore optional_skips -> null."""
    part = {"kind": "pytest", "tests": ["t_mixed.py"], "optional_skips": [{"test": OPT, "reason": "needs a database the lane does not have"}]}
    assert _c16(tmp_path, part, {"t_mixed.py": MIXED}) is True


def test_c16_an_optional_declaration_without_a_reason_or_for_another_test_declares_nothing(tmp_path):
    """Reversion: accept an empty reason / match any skip -> true."""
    for i, decl in enumerate(({"test": OPT, "reason": "  "}, {"test": OPT}, {"test": "t_mixed.py::test_other", "reason": "x"})):
        part = {"kind": "pytest", "tests": ["t_mixed.py"], "optional_skips": [decl]}
        assert _c16(tmp_path, part, {"t_mixed.py": MIXED}, name="r%d" % i) is None


def test_c16_a_declared_optional_skip_is_no_substitute_for_a_pass_of_the_bound_file(tmp_path):
    """Every bound test must have a passing case: a file whose only test is a declared-optional skip was not run. Reversion: true when nothing failed or skipped undeclared."""
    only = "import pytest\n\ndef test_needs_db():\n    pytest.skip('no database')\n"
    part = {"kind": "pytest", "tests": ["t_only.py"], "optional_skips": [{"test": "t_only.py::test_needs_db", "reason": "no database"}]}
    assert _c16(tmp_path, part, {"t_only.py": only}) is None


def test_c16_a_bound_file_none_of_whose_tests_ran_is_null_not_true(tmp_path):
    """Not-run of a bound test: file b's only test is deselected, file a passes and pytest exits 0 -- the old reader said true. Reversion: drop the bound-test check."""
    files = {"t_a.py": PASSING, "t_b.py": "def test_b():\n    assert True\n"}
    part = {"kind": "pytest", "tests": ["t_a.py", "t_b.py"], "deselect": ["t_b.py::test_b"]}
    assert _c16(tmp_path, part, files) is None
    assert _c16(tmp_path, {"kind": "pytest", "tests": ["t_a.py", "t_b.py"]}, files, name="all_run") is True


def test_c16_the_shipped_registry_declares_no_optional_skip_without_a_reason():
    for c in json.loads((REPO_ROOT / tr.DEFAULT_REGISTRY).read_text(encoding="utf-8"))["checks"]:
        for part in c["parts"]:
            for e in part.get("optional_skips", []):
                assert e["test"].count("::") >= 1 and e["reason"].strip(), (c["id"], e)
# ── C17 T24 bound to the native VM run's own record (SR-T24-NATIVE) ──────────────────────────────────────────────────────────────────────

EQ_ENV = "TRIAL_READY_EQ_RECORD"


@pytest.fixture(autouse=True)
def _no_ambient_eq_record(monkeypatch):
    """The cockpit sets TRIAL_READY_EQ_RECORD for the real evaluation; no test may read it from the ambient environment."""
    monkeypatch.delenv(EQ_ENV, raising=False)
VM_READ = "vm_probe (os.uname on the VM)"


def vm_records(eq_dir, sha, *, complete=True, kind="qualifying_run", commit=None, emulated=False, read_from=VM_READ, pin_kind="qualifying_run", arch="linux/amd64"):
    """What the VM's TR leaves under <out>/s5/tr/equivalence/ (vmkit stages/s5_tr.sh + lib/vm_probe.py + equivalence_record.py): the record, whose E6 copies the pinned
    provenance verbatim, and the pinned inputs, whose runtime block the VM probe read on the machine."""
    d = Path(eq_dir)
    d.mkdir(parents=True, exist_ok=True)
    (d / "equivalence_record.json").write_text(json.dumps({"complete": complete, "runtime_kind": kind, "E6": {"commit": commit or sha, "platform_notes": {"native_vm": {
        "emulated": emulated, "arch_read_from": read_from, "vm_type": "c3-standard-8"}}}}))
    (d / "eq_pinned_inputs.json").write_text(json.dumps({"runtime": {"kind": pin_kind, "arch": arch}}))
    return d / "equivalence_record.json"


def vm_t24(tmp_path, monkeypatch, name, write, *, env=True, fallback=None):
    """The SHIPPED T24 (both alternatives); the Docker slice directory is moved under a scratch directory that holds a slice run only when `fallback` writes one."""
    run_dir = tmp_path / (name + "_run")
    repo, sha = make(tmp_path, registry({"T24": retarget(shipped_check("T24"), run_dir)["parts"]}), name=name)
    rec = write(tmp_path / (name + "_eq") / "equivalence", sha)
    if fallback:
        fallback(run_dir, sha)
    if env and rec is not None:
        monkeypatch.setenv(EQ_ENV, str(rec))
    elif env:
        monkeypatch.setenv(EQ_ENV, str(tmp_path / (name + "_eq") / "equivalence" / "equivalence_record.json"))
    else:
        monkeypatch.delenv(EQ_ENV, raising=False)
    return values(run(repo, tmp_path))["T24"]


def test_c17_t24_reads_true_from_the_complete_native_qualifying_record_of_this_head(tmp_path, monkeypatch):
    assert vm_t24(tmp_path, monkeypatch, "ok", lambda d, sha: vm_records(d, sha)) is True


@pytest.mark.parametrize("name,over", [
    ("incomplete", {"complete": False}),                                   # record.complete == true
    ("rolling_record", {"kind": "rolling_diagnostic"}),                      # record.runtime_kind == qualifying_run
    ("other_head", {"commit": "3" * 40}),                                    # record E6.commit == the evaluated head
    ("emulated", {"emulated": True}),                                        # native, not emulated
    ("arch_not_read_in_run", {"read_from": "asserted by a file"}),           # the arch was read inside the run
    ("rolling_pinned", {"pin_kind": "rolling_diagnostic"}),                  # pinned runtime.kind == qualifying_run
    ("arm64", {"arch": "linux/arm64"}),                                      # pinned runtime.arch == linux/amd64
])
def test_c17_each_field_of_the_native_claim_is_measured_and_reads_false(tmp_path, monkeypatch, name, over):
    assert vm_t24(tmp_path, monkeypatch, name, lambda d, sha: vm_records(d, sha, **over)) is False


def test_c17_t24_is_null_when_no_record_is_named_or_the_named_one_is_absent(tmp_path, monkeypatch):
    assert vm_t24(tmp_path, monkeypatch, "noenv", lambda d, sha: vm_records(d, sha), env=False) is None            # the record exists, but nothing names it for this run
    assert vm_t24(tmp_path, monkeypatch, "nofile", lambda d, sha: None) is None                                      # named, not there
    monkeypatch.setenv(EQ_ENV, "")
    repo, _ = make(tmp_path, registry({"T24": retarget(shipped_check("T24"), tmp_path / "e_run")["parts"]}), name="empty_env")
    assert values(run(repo, tmp_path))["T24"] is None                                                               # an empty value names nothing


def test_c17_a_pinned_inputs_file_missing_beside_the_record_is_null_not_true(tmp_path, monkeypatch):
    def only_record(d, sha):
        rec = vm_records(d, sha)
        (d / "eq_pinned_inputs.json").unlink()
        return rec
    assert vm_t24(tmp_path, monkeypatch, "nopin", only_record) is None


def test_c17_the_docker_slice_stays_a_fallback_alternative(tmp_path, monkeypatch):
    nothing = lambda d, sha: None
    assert vm_t24(tmp_path, monkeypatch, "fb_ok", nothing, env=False, fallback=lambda d, sha: slice_records(d, sha)) is True        # no VM record: the complete Docker slice qualifies
    assert vm_t24(tmp_path, monkeypatch, "fb_bad", nothing, env=False, fallback=lambda d, sha: slice_records(d, sha, arch="linux/arm64")) is False
    assert vm_t24(tmp_path, monkeypatch, "fb_none", nothing, env=False) is None                                                   # no evidence of either kind


def test_c17_a_failed_native_record_does_not_hide_a_qualifying_fallback_but_never_rescues_itself(tmp_path, monkeypatch):
    assert vm_t24(tmp_path, monkeypatch, "both", lambda d, sha: vm_records(d, sha, emulated=True), fallback=lambda d, sha: slice_records(d, sha)) is True
    assert vm_t24(tmp_path, monkeypatch, "vmbad", lambda d, sha: vm_records(d, sha, emulated=True)) is False


@pytest.mark.parametrize("alts,want", [([[GOOD], [{"kind": "unbound"}]], True), ([[{"kind": "unbound"}], [{"kind": "unbound"}]], None),
                                       ([[{"kind": "unbound"}], [{"kind": "git_file", "path": "evidence.txt", "contains": ["red"]}]], False),
                                       ([[{"kind": "git_file", "path": "evidence.txt", "contains": ["red"]}], [GOOD]], True),
                                       ([[GOOD, {"kind": "unbound"}]], None), ([], None), ([[]], None)])
def test_c17_any_of_is_true_for_a_true_alternative_false_for_a_failed_one_and_never_true_from_no_evidence(tmp_path, alts, want):
    repo, _ = make(tmp_path, registry({"T24": [{"kind": "any_of", "alternatives": alts}]}))
    assert values(run(repo, tmp_path))["T24"] is want


def test_c17_the_shipped_t24_names_the_native_record_first_and_the_docker_slice_as_fallback():
    t24 = shipped_check("T24")
    assert [p["kind"] for p in t24["parts"]] == ["any_of"]
    native, fallback = t24["parts"][0]["alternatives"]
    assert all(p["kind"] == "json_field_eq" and p["path_env"] == EQ_ENV for p in native)
    assert all("path" in p and "path_env" not in p for p in fallback) and "amd64_slice" in json.dumps(fallback)
    assert "SR-T24-NATIVE" in t24["note"] and "fallback" in t24["note"]


# ── C18 no name-level deselect in the shipped registry (SR-NO-DESELECT) ──────────────────────────────────────────────────────────────────

def deselect_paths(node, path="$"):
    """Every JSON path whose key mentions `deselect`, at any depth (a nested part, an `any_of` alternative, a `deselect_why` left behind)."""
    found = []
    if isinstance(node, dict):
        for k, v in node.items():
            if "deselect" in k.lower():
                found.append(f"{path}.{k}")
            found += deselect_paths(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            found += deselect_paths(v, f"{path}[{i}]")
    return found


def test_c18_the_shipped_registry_carries_no_deselect_anywhere():
    """Reads the registry file as shipped (not through the evaluator). Reversion: put back a `deselect` on any part, at any depth -> this test fails (next test)."""
    doc = json.loads((REPO_ROOT / tr.DEFAULT_REGISTRY).read_text(encoding="utf-8"))
    assert deselect_paths(doc) == []


def test_c18_the_guard_reads_a_planted_deselect_at_any_depth_as_a_failure():
    doc = json.loads((REPO_ROOT / tr.DEFAULT_REGISTRY).read_text(encoding="utf-8"))
    assert deselect_paths(doc) == []
    top = json.loads(json.dumps(doc))
    next(p for p in shipped_check_in(top, "T14")["parts"] if p["kind"] == "pytest")["deselect"] = ["tests/test_driver.py::test_x"]
    assert len(deselect_paths(top)) == 1
    nested = json.loads(json.dumps(doc))
    t24 = shipped_check_in(nested, "T24")["parts"][0]["alternatives"][0][0]
    t24["deselect_why"] = "left behind"
    assert deselect_paths(nested) and deselect_paths(nested)[0].endswith(".deselect_why")


def shipped_check_in(doc, cid):
    return next(c for c in doc["checks"] if c["id"] == cid)
