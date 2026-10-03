"""test_ci_shard.py: the governance-tests CI split cannot silently drop, duplicate or re-balance a test file, and the workflow keeps its contract.

  * every shard count partitions exactly the files pytest collects (complete + disjoint), deterministically;
  * `--verify` FAILS for a dropped file, a doubled file, an alien file and an empty shard (mutation tests);
  * ci.yml: the matrix, the `--count` in both steps and the shard-name suffix agree; the aggregate job keeps the original required name, needs
    the shard job, runs `if: always()` and fails on any result but success.
"""
from __future__ import annotations

import re
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
    loads = [sum(f.stat().st_size for f in s) for s in a]
    assert max(loads) - min(loads) <= max(f.stat().st_size for f in files)     # LPT: never off by more than the largest file


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
    assert out and all(l.startswith("platform/scripts/governance/__tests__/") and (ROOT / l).is_file() for l in out)


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
    assert sh.get("timeout-minutes", 0) <= 10


def test_the_aggregate_job_keeps_the_original_required_name_and_fails_on_any_non_success(jobs):
    agg = jobs["governance-tool-tests"]
    assert agg["name"] == "Governance Tool Tests (pytest)"
    assert agg["needs"] == "governance-tool-tests-shard" or agg["needs"] == ["governance-tool-tests-shard"]
    assert "always()" in str(agg["if"])
    step = agg["steps"][0]
    assert step["env"]["SHARDS_RESULT"] == "${{ needs.governance-tool-tests-shard.result }}"
    assert '!= "success"' in step["run"] and "exit 1" in step["run"]


def test_no_other_job_still_runs_the_whole_directory_as_one_pytest_call(jobs):
    for name, j in jobs.items():
        for s in j.get("steps", []):
            assert "pytest platform/scripts/governance/__tests__ " not in str(s.get("run", "")) + " ", name


@pytest.mark.parametrize("result,ok", [("success", True), ("skipped", False), ("cancelled", False), ("failure", False), ("", False)])
def test_a_skipped_or_cancelled_or_failed_shard_fails_the_aggregate(jobs, result, ok):
    """N-98 A: run the aggregate job's own script with each possible `needs.<shard>.result`: only `success` may pass."""
    script = jobs["governance-tool-tests"]["steps"][0]["run"]
    p = subprocess.run(["bash", "-c", script], env={"SHARDS_RESULT": result, "PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    assert (p.returncode == 0) is ok, (result, p.stdout, p.stderr)
    assert ("::error::" in p.stdout) is (not ok)


def test_the_aggregate_script_fails_when_the_result_is_not_even_set(jobs):
    script = jobs["governance-tool-tests"]["steps"][0]["run"]
    p = subprocess.run(["bash", "-c", script], env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    assert p.returncode != 0


def test_no_step_can_turn_a_failing_shard_green_or_narrow_what_runs(jobs):
    """Review N-103: continue-on-error, `|| true`, --co/--collect-only and --deselect would each make the aggregate green without the tests passing."""
    for jname in ("governance-tool-tests-shard", "governance-tool-tests"):
        job = jobs[jname]
        assert "continue-on-error" not in job, jname
        for st in job["steps"]:
            assert "continue-on-error" not in st, (jname, st.get("name"))
            run = str(st.get("run", ""))
            assert "|| true" not in run and "--co " not in run + " " and "--collect-only" not in run and "--deselect" not in run, (jname, run)


def test_the_shard_step_stops_when_ci_shard_returns_no_files(jobs):
    run = next(st["run"] for st in jobs["governance-tool-tests-shard"]["steps"] if "python -m pytest" in str(st.get("run", "")))
    assert "mapfile -t FILES < <(python platform/scripts/governance/ci_shard.py --count 3 --index ${{ matrix.shard }})" in run and '"${#FILES[@]}" -gt 0' in run and '"${FILES[@]}"' in run and "$(python" not in run


def test_verify_exits_nonzero_on_a_broken_partition(tmp_path):
    (tmp_path / "test_only.py").write_text("x")
    p = subprocess.run([sys.executable, str(HERE.parent / "ci_shard.py"), "--count", "2", "--verify", "--root", str(tmp_path)], capture_output=True, text=True)
    assert p.returncode == 1 and "empty shard" in p.stderr           # two shards, one file: an empty shard fails the run
