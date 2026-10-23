"""test_ci_shard.py: the governance-tests CI split cannot silently drop, duplicate or re-balance a test file, and the workflow keeps its contract.

  * every shard count partitions exactly the files pytest collects (complete + disjoint), deterministically;
  * `--verify` FAILS for a dropped file, a doubled file, an alien file and an empty shard (mutation tests);
  * ci.yml: the matrix, the `--count` in both steps and the shard-name suffix agree; the aggregate job keeps the original required name, needs
    the shard job, runs `if: always()` and fails on any result but success.
"""
from __future__ import annotations

import re
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import ci_shard  # noqa: E402

ROOT = HERE.parents[3]
CI = ROOT / ".github" / "workflows" / "ci.yml"


def _files(tmp_path: Path, sizes: dict[str, int]) -> Path:
    for name, n in sizes.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x" * n)
    return tmp_path


@pytest.mark.parametrize("count", [1, 2, 3, 5])
def test_every_count_partitions_the_real_test_files_completely_and_disjointly(count):
    files = ci_shard.test_files()
    assert files and ci_shard.verify(files, ci_shard.partition(files, count)) == []


def test_the_partition_is_deterministic_and_balanced_by_size():
    files = ci_shard.test_files()
    a, b = ci_shard.partition(files, 3), ci_shard.partition(files, 3)
    assert a == b
    loads = [sum(ci_shard.weight(f) for f in s) for s in a]
    assert max(loads) - min(loads) <= max(ci_shard.weight(f) for f in files)   # LPT: never off by more than the heaviest file


def test_every_weighted_file_exists_and_the_heaviest_suites_do_not_share_a_shard():
    """The CI_SECONDS table cannot rot silently, and the shard run time is balanced by it: the five heaviest files (measured on the 2026-10-05
    merge-group runs) are in five different shards (a shard that held two of them timed out at the 20-minute cap), and no shard is estimated
    more than 25 percent above the mean. The workflow runs 5 shards."""
    files = ci_shard.test_files()
    assert set(ci_shard.CI_SECONDS) <= {f.name for f in files}, sorted(set(ci_shard.CI_SECONDS) - {f.name for f in files})
    shards = ci_shard.partition(files, 5)
    where = {f.name: i for i, s in enumerate(shards) for f in s}
    heaviest = [n for n, _ in sorted(ci_shard.CI_SECONDS.items(), key=lambda kv: -kv[1])[:5]]
    assert len({where[n] for n in heaviest}) == 5, heaviest
    est = [sum(ci_shard.CI_SECONDS.get(f.name, f.stat().st_size / ci_shard.BYTES_PER_SECOND) for f in s) for s in shards]
    assert max(est) <= 1.25 * (sum(est) / len(est)), est                       # no shard is estimated more than 25 percent above the mean


def test_collection_matches_pytest_default_patterns(tmp_path):
    root = _files(tmp_path, {"test_a.py": 1, "b_test.py": 1, "helper.py": 1, "sub/test_c.py": 1, "sub/_util.py": 1, "conftest.py": 1})
    assert [p.relative_to(root).as_posix() for p in ci_shard.test_files(root)] == ["b_test.py", "sub/test_c.py", "test_a.py"]


def test_largest_first_greedy_assignment(tmp_path):
    root = _files(tmp_path, {"test_big.py": 100, "test_m1.py": 40, "test_m2.py": 40, "test_s.py": 20})
    sh = ci_shard.partition(ci_shard.test_files(root), 2)
    assert [[p.name for p in s] for s in sh] == [["test_big.py"], ["test_m1.py", "test_m2.py", "test_s.py"]]


def test_verify_fails_for_a_dropped_a_doubled_an_alien_file_and_an_empty_shard(tmp_path):
    root = _files(tmp_path, {"test_a.py": 3, "test_b.py": 2, "test_c.py": 1})
    files = ci_shard.test_files(root)
    good = ci_shard.partition(files, 2)
    assert ci_shard.verify(files, good) == []
    dropped = [good[0][1:], good[1]]
    assert any("in no shard" in p for p in ci_shard.verify(files, dropped))
    doubled = [good[0] + good[1][:1], good[1]]
    assert any("more than one shard" in p for p in ci_shard.verify(files, doubled))
    alien = [good[0] + [root / "test_zzz.py"], good[1]]
    assert any("not test files" in p for p in ci_shard.verify(files, alien))
    assert any("empty shard" in p for p in ci_shard.verify(files, [good[0] + good[1], []]))


def test_cli_verify_and_index_bounds():
    ok = subprocess.run([sys.executable, str(HERE.parent / "ci_shard.py"), "--count", "3", "--verify"], capture_output=True, text=True)
    assert ok.returncode == 0 and "OK" in ok.stdout
    bad = subprocess.run([sys.executable, str(HERE.parent / "ci_shard.py"), "--count", "3", "--index", "4"], capture_output=True, text=True)
    assert bad.returncode == 2
    out = subprocess.run([sys.executable, str(HERE.parent / "ci_shard.py"), "--count", "3", "--index", "1"], capture_output=True, text=True).stdout.split()
    assert out and all(l.startswith(("platform/scripts/governance/__tests__/", "platform/scripts/governance/pravaha_tracker/tests/")) and (ROOT / l).is_file() for l in out)


# ---------------------------------------------------------------- the workflow contract ----------------------------------------------------

@pytest.fixture(scope="module")
def jobs():
    yaml = pytest.importorskip("yaml")
    if not CI.is_file():
        pytest.skip("no ci.yml on this tree")
    return yaml.safe_load(CI.read_text())["jobs"]


def test_ci_matrix_count_and_name_agree(jobs):
    sh = jobs["governance-tool-tests-shard"]
    shards = sh["strategy"]["matrix"]["shard"]
    n = len(shards)
    assert shards == list(range(1, n + 1)) and sh["strategy"]["fail-fast"] is False
    assert f"/{n}" in sh["name"] and "${{ matrix.shard }}" in sh["name"]
    runs = " ".join(str(s.get("run", "")) for s in sh["steps"])
    assert len(re.findall(rf"ci_shard\.py --count {n} ", runs + " ")) >= 2                       # the --verify step and the pytest step
    assert not re.findall(r"ci_shard\.py --count (?!%d\b)\d+" % n, runs)
    assert "--index ${{ matrix.shard }}" in runs and "--verify" in runs
    # raised from 10 (the shard measured 593 s on the merge-group tree), then to 35 for shard 1 only: it also runs the J-1a lane step
    # (apt + pip installs, a throwaway cluster, ~5-8 min of DB tests). Still a pin, not a free pass: the lane step must exist for the
    # extra budget to be justified, and the global A55 ceiling (45) stays above it.
    timeout = sh.get("timeout-minutes", 0)
    lane_step = any("pytest governance-tool-tests-lane --" in str(s.get("run", "")) for s in sh["steps"])
    assert timeout <= (35 if lane_step else 20)


def test_the_aggregate_job_keeps_the_original_required_name_and_fails_on_any_non_success(jobs):
    agg = jobs["governance-tool-tests"]
    assert agg["name"] == "Governance Tool Tests (pytest)"
    assert set(agg["needs"]) == {"changes", "governance-tool-tests-shard", "governance-readback-tests", "kala-db-tests", "gochara-j5s-full-class-seal"}
    assert "always()" in str(agg["if"])
    step = agg["steps"][0]
    assert step["env"]["SHARDS_RESULT"] == "${{ needs.governance-tool-tests-shard.result }}"
    assert step["env"]["READBACK_RESULT"] == "${{ needs.governance-readback-tests.result }}"
    assert step["env"]["KALA_DB_RESULT"] == "${{ needs.kala-db-tests.result }}"
    assert "'kala-db-tests'" in step["env"]["KALA_DB_EXPECTED"]
    assert step["env"]["J5S_RESULT"] == "${{ needs.gochara-j5s-full-class-seal.result }}"
    assert step["env"]["DOCS_ONLY"] == "${{ needs.changes.outputs.docs_only }}"
    assert "exit 1" in step["run"]


def test_no_other_job_still_runs_the_whole_directory_as_one_pytest_call(jobs):
    for name, j in jobs.items():
        for s in j.get("steps", []):
            assert "pytest platform/scripts/governance/__tests__ " not in str(s.get("run", "")) + " ", name


@pytest.mark.parametrize("result,docs_only,ok", [("success", "", True), ("success", "true", True), ("success", "false", True),
                                                 ("skipped", "true", True),                       # skipped by the docs-only fast path: green
                                                 ("skipped", "false", False), ("skipped", "", False),   # skipped for any other reason: NOT green
                                                 ("cancelled", "true", False), ("failure", "true", False), ("failure", "", False),
                                                 ("cancelled", "", False), ("", "true", False), ("", "", False)])
@pytest.mark.parametrize("readback", ["success", "skipped", "cancelled", "failure", ""])
@pytest.mark.parametrize("kala_db", ["success", "skipped", "cancelled", "failure", ""])
@pytest.mark.parametrize("kala_db_expected", ["false", "true"])
def test_a_skipped_or_cancelled_or_failed_shard_fails_the_aggregate_unless_docs_only_skipped_it(jobs, result, docs_only, ok, readback, kala_db, kala_db_expected):
    """N-98 A + the fast path: run the aggregate job's own script with each shard, readback and Kāla DB result and docs_only: only success, or skipped
    together with docs_only=true, may pass."""
    script = jobs["governance-tool-tests"]["steps"][0]["run"]
    p = subprocess.run(["bash", "-c", script], env={**os.environ, "SHARDS_RESULT": result, "READBACK_RESULT": readback, "KALA_DB_RESULT": kala_db, "KALA_DB_EXPECTED": kala_db_expected, "DOCS_ONLY": docs_only, "EVENT_NAME": "pull_request", "READBACK_EXPECTED": "false", "J5S_RESULT": "success", "J5S_EXPECTED": "true"}, capture_output=True, text=True)
    ok = ok and (readback in ("success", "skipped") if result == "success" else readback == "skipped")
    ok = ok and (kala_db == "success" or (kala_db == "skipped" and (docs_only == "true" or kala_db_expected == "false")))
    assert (p.returncode == 0) is ok, (result, readback, kala_db, kala_db_expected, docs_only, p.stdout, p.stderr)
    assert ("::error::" in p.stdout) is (not ok)


@pytest.mark.parametrize("event,shards,readback,expected,run_combination,ok", [
    ("pull_request", "skipped", "success", "true", "false", True),         # PR touched a readback: readbacks ran, shards deferred to the queue (SR-BOLD-08a)
    ("pull_request", "skipped", "failure", "true", "false", False),        # the readback that ran failed
    ("pull_request", "skipped", "skipped", "true", "false", False),        # an expected readback never ran
    ("pull_request", "skipped", "success", "false", "false", False),       # a readback nothing selected is not evidence for a deferral
    ("pull_request", "failure", "success", "true", "false", False),        # a shard that ran and failed is never "deferred"
    ("merge_group", "skipped", "success", "true", "true", False),          # the queue never defers the shards
    ("pull_request", "skipped", "success", "true", "true", False),         # shards run on this PR (scoper touched), so skipped is not the deferral
])
def test_a_pr_deferring_the_shards_still_passes_when_its_selected_readbacks_succeed(jobs, event, shards, readback, expected, run_combination, ok):
    """SR-BOLD-08a: shards are merge_group-only on a PR; a PR whose diff selects governance-readback-tests must not fail the aggregate for that deferral."""
    script = jobs["governance-tool-tests"]["steps"][0]["run"]
    env = {**os.environ, "EVENT_NAME": event, "SHARDS_RESULT": shards, "READBACK_RESULT": readback, "READBACK_EXPECTED": expected, "RUN_COMBINATION": run_combination,
           "CHANGES_RESULT": "success", "DOCS_ONLY": "false", "KALA_DB_RESULT": "skipped", "KALA_DB_EXPECTED": "false", "J5S_RESULT": "skipped", "J5S_EXPECTED": "false",
           "GITHUB_STEP_SUMMARY": os.devnull}
    p = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
    assert (p.returncode == 0) is ok, (p.stdout, p.stderr)


def test_the_aggregate_script_fails_when_the_result_is_not_even_set(jobs):
    script = jobs["governance-tool-tests"]["steps"][0]["run"]
    p = subprocess.run(["bash", "-c", script], env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    assert p.returncode != 0


def test_no_step_can_turn_a_failing_shard_green_or_narrow_what_runs(jobs):
    """Review N-103: continue-on-error, `|| true`, --co/--collect-only and --deselect would each make the aggregate green without the tests passing."""
    for jname in ("governance-tool-tests-shard", "governance-readback-tests", "governance-tool-tests"):
        job = jobs[jname]
        assert "continue-on-error" not in job, jname
        for st in job["steps"]:
            assert "continue-on-error" not in st, (jname, st.get("name"))
            run = str(st.get("run", ""))
            assert "|| true" not in run and "--co " not in run + " " and "--collect-only" not in run and "--deselect" not in run, (jname, run)


def test_the_shard_step_stops_when_ci_shard_returns_no_files(jobs):
    run = next(st["run"] for st in jobs["governance-tool-tests-shard"]["steps"] if "python -m pytest" in str(st.get("run", "")))
    assert "mapfile -t FILES < <(python platform/scripts/governance/ci_shard.py --count 5 --index ${{ matrix.shard }})" in run and '"${#FILES[@]}" -gt 0' in run and '"${FILES[@]}"' in run and "$(python" not in run


def test_verify_exits_nonzero_on_a_broken_partition(tmp_path):
    (tmp_path / "test_only.py").write_text("x")
    p = subprocess.run([sys.executable, str(HERE.parent / "ci_shard.py"), "--count", "2", "--verify", "--root", str(tmp_path)], capture_output=True, text=True)
    assert p.returncode == 1 and "empty shard" in p.stderr           # two shards, one file: an empty shard fails the run


def test_tracker_suite_is_mandatory_in_governance_shards():
    import yaml

    from ci_discovery import expanded_workflow
    job = expanded_workflow(yaml.safe_load(CI.read_text())["jobs"])["governance-tool-tests-shard"]
    tracker = [step for step in job["steps"]
               if "platform/scripts/governance/pravaha_tracker/tests/test_verify_priority.py" in step.get("run", "")]
    assert len(tracker) == 1, "tracker regressions must run in required governance CI"
    assert tracker[0].get("continue-on-error", False) is False
    assert tracker[0].get("if") == "matrix.shard == 1"
    assert tracker[0]["env"]["PYTHONPATH"] == "platform/scripts/governance"
    assert "-p no:cacheprovider" in tracker[0]["run"]
    assert "platform/scripts/governance/pravaha_tracker/tests/test_hang_resilience.py" in tracker[0]["run"]
    assert "test_kalayantra_control_plane.py" in tracker[0]["run"]
    assert "platform/scripts/governance/pravaha_tracker/tests/test_step_receipt_binding.py" in tracker[0]["run"]


def test_shared_discovery_includes_all_tracker_tests_and_future_files(tmp_path):
    tracker = HERE.parent / "pravaha_tracker" / "tests"
    discovered = set(ci_shard.test_files())
    expected = {p for pattern in ("test_*.py", "*_test.py") for p in tracker.rglob(pattern)}
    assert tracker / "test_built_waiting_on_gate.py" in discovered
    assert expected <= discovered
    # Discovery remains pattern based when another tracker regression is added.
    root = _files(tmp_path, {"__tests__/test_existing.py": 1,
                             "pravaha_tracker/tests/test_future.py": 1,
                             "pravaha_tracker/tests/nested/future_test.py": 1,
                             "pravaha_tracker/tests/helper.py": 1})
    assert len(ci_shard.test_files(root / "__tests__")) == 3


def test_discovered_tracker_tests_have_runtime_dependencies_in_required_shards(jobs):
    steps = jobs["governance-tool-tests-shard"]["steps"]
    run_index, step = next((i, s) for i, s in enumerate(steps)
                           if 'python -m pytest "${FILES[@]}"' in s.get("run", ""))
    assert step["env"].get("PYTHONPATH") == "platform/scripts/governance"
    assert "-p no:cacheprovider" in step["run"]
    node = [s for s in steps[:run_index] if s.get("uses", "").startswith("actions/setup-node@")]
    assert len(node) == 1 and node[0]["with"]["node-version"]
    assert "if" not in node[0], "the feature file can land in any shard"


def test_tracker_external_isolation_runs_in_required_governance_shard():
    """Dropping the sleep-60 regressions from CI must fail the required gate."""
    import shlex

    import yaml

    from ci_discovery import expanded_workflow
    jobs = expanded_workflow(yaml.safe_load(CI.read_text())["jobs"])
    shard = jobs["governance-tool-tests-shard"]
    suite = "platform/scripts/governance/pravaha_tracker/tests/test_external_isolation.py"
    commands = [step for step in shard["steps"]
                if suite in shlex.split(str(step.get("run", "")))
                or str(Path(suite).parent) in shlex.split(str(step.get("run", "")))]
    assert commands, "external isolation regressions have no required CI invocation"
    for step in commands:
        words = shlex.split(step["run"])
        assert "pytest" in words and "--collect-only" not in words
        assert "--deselect" not in words and "-k" not in words
        assert step.get("if") in (None, "matrix.shard == 1")
        assert not step.get("continue-on-error", False)
        assert "||" not in words
    assert "governance-tool-tests-shard" in jobs["governance-tool-tests"]["needs"]
