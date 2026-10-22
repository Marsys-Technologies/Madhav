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
  C11 a `pytest` part passes `env` with `{repo}` expanded and `--deselect` for each named node id (T14); a part whose every test is deselected is null;
     a relative scratch directory is resolved first (the part runs in another cwd, so its junit file would otherwise be written elsewhere and read null).
  C12 the trial harness landed under fleet/trial_harness is the accepted v3.1 (content digest pinned), not a later or edited copy.
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

# the checks whose detector is another job's (TR_GAPS B1 NDH, B2 SELECT-130, B7 DASH-READBACK, B6 LANE-LEDGER); binding one removes it from this set, a new unbound check fails
STILL_UNBOUND = {"T11", "T12", "T13", "T22"}


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
                assert p["fields"] and all(("equals" in f) != bool(f.get("equals_head")) for f in p["fields"]), (c["id"], p)
            if p["kind"] == "db_migrations":
                assert p.get("mode") == "all" or p.get("prefixes"), (c["id"], p)


def test_c8_only_the_four_checks_that_wait_for_another_job_are_unbound():
    doc = json.loads((REPO_ROOT / tr.DEFAULT_REGISTRY).read_text(encoding="utf-8"))
    unbound = {c["id"] for c in doc["checks"] if any(p["kind"] == "unbound" for p in c["parts"])}
    assert unbound <= STILL_UNBOUND, sorted(unbound - STILL_UNBOUND)


def test_c8_a_check_with_no_bound_detector_cannot_read_true_from_the_shipped_registry(tmp_path):
    """Plan: 'Nothing in the list is a rolling run is green' - the shipped registry binds nothing to a lane state."""
    doc = json.loads((REPO_ROOT / tr.DEFAULT_REGISTRY).read_text(encoding="utf-8"))
    repo, _ = make(tmp_path, doc)
    v = values(run(repo, tmp_path))
    unbound_only = [c["id"] for c in doc["checks"] if all(p["kind"] == "unbound" for p in c["parts"])]
    assert unbound_only and all(v[i] is None for i in unbound_only)
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
HARNESS_V31_DIGEST = "efb0922aa74aaefb07b981fd019fa334301448a37d877536802657020569787c"     # review X-20261022T075423Z-review-t1b-harness2 (ACCEPTED, round 2)


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
