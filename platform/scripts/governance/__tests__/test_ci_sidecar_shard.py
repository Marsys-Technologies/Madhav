"""test_ci_sidecar_shard.py: the Governance Gates python-sidecar split cannot silently drop, duplicate or re-balance a test, and the workflow keeps
its contract (sharded 2026-10-08; same discipline as test_ci_shard.py for the governance tool tests).

  * the plugin partitions a real pytest collection completely and disjointly, deterministically, balanced by weight;
  * `verify` FAILS for a dropped, a doubled, an alien file and an empty shard (mutation tests), and the plugin turns any such problem into a
    usage error before a single test runs;
  * run for real in a subprocess: the K shards' selected tests are exactly the full collection after -m deselection, each test once;
  * ci.yml: every shard runs the unsharded command unchanged plus `-p sidecar_shard --ci-shard I/K`, K agrees with the matrix, the environment
    is the original job's; the static job keeps every other original step in order; the aggregate keeps the required name, needs both
    jobs, runs `if: always()` and passes ONLY when both finished `success`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PLUGINS = HERE.parent / "pytest_plugins"
sys.path.insert(0, str(PLUGINS))

import sidecar_shard  # noqa: E402

ROOT = HERE.parents[3]
CI = ROOT / ".github" / "workflows" / "ci.yml"
SIDECAR = ROOT / "platform" / "python-sidecar"

SHARD_JOB = "governance-gates-py-sidecar-shard"
STATIC_JOB = "governance-gates-static"
AGG_JOB = "governance-gates"
REQUIRED_NAME = "Governance Gates (drift / schema / edge / native-literal / py-sidecar)"

#: The unsharded command, token for token (2026-10-08). A shard must run exactly this plus the shard arguments.
ORIGINAL_ARGS = (
    "tests/ bodha_writers/__tests__ ga_writers/__tests__ pipeline/orchestrator/tests/ "
    "pipeline/orchestrator/writers/tests/test_bg_sky_calendar.py "
    "pipeline/orchestrator/writers/tests/test_bg_texts_metadata_upsert.py "
    "pipeline/orchestrator/writers/tests/test_bg_texts_source_manifest.py "
    "--ignore=tests/test_pyjhora_adapter --ignore=tests/test_dasha_chain.py "
    "--ignore=tests/extractors/test_cgm_extractor.py --ignore=tests/test_l0_remedy_corpus.py "
    '-m "not integration"'
)
#: The steps of the original job other than the sidecar pytest step, in order: they now run in the static job.
STATIC_STEPS = (
    "Checkout", "Setup Python", "Install Python dependencies",
    "drift_detector — repo scan", "schema_validator — repo scan",
    "msr_referential_integrity — self-test (§N.5 constituent guard)",
    "schema_pin_mimamsa_predictions — self-test (SAMĀPTI B-PB-SCHEMA-PIN)",
    "public-schema migration privilege guard — self-test + repo scan (Kāla outage 2026-10-08)",
    "assert_no_native_literal — repo scan",
    "dag_edge_guard — self-test (§N.8 / SAMĀPTI F-02)",
    "kala_derivation_completeness_guard — self-test (§N.8 / SAMĀPTI F-02)",
    "edge_security_smoke — sanity",
    "Install python-sidecar dependencies (for the Nirmāṇa probe)",
    "Nirmāṇa L0 — pinned Swiss Ephemeris corpus probe",
)


def _ids(spec: dict[str, int]) -> list[str]:
    """Synthetic nodeids: {file: number of tests}."""
    return [f"{f}::test_{n}" for f, c in spec.items() for n in range(c)]


# ---------------------------------------------------------------- the partition ----------------------------------------------------------

@pytest.mark.parametrize("k", [1, 2, 3, 4, 6])
def test_every_count_partitions_completely_disjointly_and_deterministically(k):
    ids = _ids({f"tests/test_{c}.py": (c % 7) + 1 for c in range(40)})
    a, b = sidecar_shard.partition(ids, k), sidecar_shard.partition(list(reversed(ids)), k)
    assert a == b and sidecar_shard.verify(ids, a) == []


def test_largest_first_greedy_balances_by_weight(monkeypatch):
    monkeypatch.setattr(sidecar_shard, "FILE_SECONDS", {"tests/test_big.py": 100.0})
    monkeypatch.setattr(sidecar_shard, "DEFAULT_SECONDS_PER_TEST", 1.0)
    ids = _ids({"tests/test_big.py": 1, "tests/test_m1.py": 40, "tests/test_m2.py": 40, "tests/test_s.py": 20})
    assert sidecar_shard.partition(ids, 2) == [["tests/test_big.py"], ["tests/test_m1.py", "tests/test_m2.py", "tests/test_s.py"]]
    w = sidecar_shard.weights(ids)
    loads = [sum(w[f] for f in s) for s in sidecar_shard.partition(ids, 3)]
    assert max(loads) - min(loads) <= max(w.values())            # LPT: never off by more than the heaviest file


def test_a_file_is_never_split_across_shards():
    ids = _ids({"tests/test_a.py": 50, "tests/test_b.py": 1, "tests/test_c.py": 1})
    shards = sidecar_shard.partition(ids, 3)
    assert sorted(len(s) for s in shards) == [1, 1, 1]


def test_verify_fails_for_a_dropped_a_doubled_an_alien_file_and_an_empty_shard():
    ids = _ids({"a.py": 3, "b.py": 2, "c.py": 1})
    good = sidecar_shard.partition(ids, 2)
    assert sidecar_shard.verify(ids, good) == []
    assert any("in no shard" in p for p in sidecar_shard.verify(ids, [good[0][1:], good[1]]))
    assert any("more than one shard" in p for p in sidecar_shard.verify(ids, [good[0] + good[1][:1], good[1]]))
    assert any("not collected" in p for p in sidecar_shard.verify(ids, [good[0] + ["zzz.py"], good[1]]))
    assert any("empty shard" in p for p in sidecar_shard.verify(ids, [good[0] + good[1], []]))


def test_a_corrupted_partition_stops_the_run_before_any_test(monkeypatch):
    """The plugin's own guard: whatever partition() returns is verified against the collection, and a broken one is a usage error."""
    class Cfg:
        def getoption(self, name):
            return "1/2"
    items = [type("I", (), {"nodeid": n})() for n in _ids({"a.py": 1, "b.py": 1})]
    monkeypatch.setattr(sidecar_shard, "partition", lambda ids, k: [["a.py"], []])
    with pytest.raises(pytest.UsageError, match="not exactly the full collection"):
        sidecar_shard.pytest_collection_modifyitems(Cfg(), items)


@pytest.mark.parametrize("spec", ["0/4", "5/4", "1/0", "x/4", "4", "1/4/2", ""])
def test_a_malformed_shard_spec_is_a_usage_error(spec):
    with pytest.raises(pytest.UsageError):
        sidecar_shard.parse_shard(spec)


def test_every_measured_file_exists_on_the_tree():
    """FILE_SECONDS cannot rot silently: every listed path is a sidecar test file."""
    missing = sorted(f for f in sidecar_shard.FILE_SECONDS if not (SIDECAR / f).is_file())
    assert not missing, missing


# ---------------------------------------------------------------- the plugin, run for real -----------------------------------------------

def _tree(tmp_path: Path) -> Path:
    (tmp_path / "conftest.py").write_text("def pytest_configure(config):\n    config.addinivalue_line('markers', 'integration: x')\n")
    for n in range(9):
        body = "\n".join(f"def test_{j}():\n    pass\n" for j in range(n + 1))
        (tmp_path / "tests" / f"sub{n % 2}").mkdir(parents=True, exist_ok=True)
        (tmp_path / "tests" / f"sub{n % 2}" / f"test_m{n}.py").write_text(body)
    (tmp_path / "tests" / "test_int.py").write_text("import pytest\n\n@pytest.mark.integration\ndef test_db():\n    pass\n\ndef test_ok():\n    pass\n")
    (tmp_path / "tests" / "test_param.py").write_text("import pytest\n\n@pytest.mark.parametrize('x', range(5))\ndef test_p(x):\n    pass\n")
    return tmp_path


def _collect(root: Path, *args: str) -> tuple[int, list[str], str]:
    p = subprocess.run([sys.executable, "-m", "pytest", "tests", "-m", "not integration", "--collect-only", "-q", "-p", "no:cacheprovider", *args],
                       cwd=root, env={"PYTHONPATH": str(PLUGINS), "PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    return p.returncode, [line for line in p.stdout.splitlines() if "::" in line], p.stdout + p.stderr


@pytest.mark.parametrize("k", [2, 4])
def test_the_shards_together_run_the_full_collection_exactly_once(tmp_path, k):
    root = _tree(tmp_path)
    rc, full, _ = _collect(root, "-p", "sidecar_shard")
    assert rc == 0 and full and not any("test_db" in n for n in full)
    seen: list[str] = []
    for i in range(1, k + 1):
        rc, mine, out = _collect(root, "-p", "sidecar_shard", "--ci-shard", f"{i}/{k}")
        assert rc == 0 and mine, out
        assert f"ci-shard {i}/{k}: {len(mine)} of {len(full)} tests" in out, out
        seen += mine
    assert sorted(seen) == sorted(full) and len(seen) == len(set(seen))


def test_the_plan_prints_every_file_once(tmp_path):
    root = _tree(tmp_path)
    rc, full, out = _collect(root, "-p", "sidecar_shard", "--ci-shard", "1/3", "--ci-shard-plan")
    assert rc == 0
    planned = [line.split()[-1] for line in out.splitlines() if line.startswith("  [")]
    assert sorted(planned) == sorted({n.split("::")[0] for n in _collect(root, "-p", "sidecar_shard")[1]})


def test_more_shards_than_files_fails_before_running(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_only.py").write_text("def test_a():\n    pass\n")
    rc, _, out = _collect(tmp_path, "-p", "sidecar_shard", "--ci-shard", "1/2")
    assert rc == 4 and "empty shard" in out


# ---------------------------------------------------------------- the workflow contract ----------------------------------------------------

@pytest.fixture(scope="module")
def jobs():
    yaml = pytest.importorskip("yaml")
    if not CI.is_file():
        pytest.skip("no ci.yml on this tree")
    return yaml.safe_load(CI.read_text())["jobs"]


def _pytest_step(job: dict) -> dict:
    steps = [s for s in job["steps"] if "pytest tests/ bodha_writers/__tests__" in str(s.get("run", ""))]
    assert len(steps) == 1
    return steps[0]


def _command(run: str) -> str:
    """The pytest command line of the step, continuation lines joined."""
    joined = run.replace("\\\n", " ")
    line = next(ln for ln in joined.splitlines() if "pytest tests/ bodha_writers/__tests__" in ln)
    return " ".join(line.split())


def test_the_shard_matrix_count_and_name_agree(jobs):
    sh = jobs[SHARD_JOB]
    shards = sh["strategy"]["matrix"]["shard"]
    n = len(shards)
    assert n >= 2 and shards == list(range(1, n + 1)) and sh["strategy"]["fail-fast"] is False
    assert sh["name"] == f"Governance Gates py-sidecar shard ${{{{ matrix.shard }}}}/{n}"
    step = _pytest_step(sh)
    assert step["name"].endswith(f"(shard ${{{{ matrix.shard }}}}/{n})")
    assert _command(step["run"]).endswith(f"-p sidecar_shard --ci-shard ${{{{ matrix.shard }}}}/{n} -q -rs --tb=short --no-header")
    assert isinstance(sh.get("timeout-minutes"), int) and sh["timeout-minutes"] <= 20


def test_every_shard_runs_the_original_command_unchanged_plus_the_shard_arguments(jobs):
    cmd = _command(_pytest_step(jobs[SHARD_JOB])["run"])
    assert cmd.startswith('PYTHONPATH="$sidecar_shard_plugin_dir" pytest ' + ORIGINAL_ARGS + " -p sidecar_shard --ci-shard "), cmd
    run = _pytest_step(jobs[SHARD_JOB])["run"]
    assert 'sidecar_shard_plugin_dir="$GITHUB_WORKSPACE/platform/scripts/governance/pytest_plugins"' in run
    assert (ROOT / "platform/scripts/governance/pytest_plugins/sidecar_shard.py").is_file()


def test_every_shard_has_the_original_environment(jobs):
    sh = jobs[SHARD_JOB]
    run = _pytest_step(sh)["run"]
    for needle in ("pip install -r platform/python-sidecar/requirements-ci.txt --quiet",
                   "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66  sepl_18.se1",
                   "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7  semo_18.se1",
                   "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2  seas_18.se1",
                   "| sha256sum -c -)", 'export SE_EPHE_PATH="$se1_dir"', "export GOCHARA_SE1_REQUIRE=1",
                   "python -m pipeline.orchestrator.provenance_inventory --check", "cd platform/python-sidecar"):
        assert needle in run, needle
    steps = {s.get("name"): s for s in sh["steps"]}
    assert steps["Checkout"]["with"]["fetch-depth"] == 0
    py = steps["Setup Python"]["with"]
    assert py["python-version"] == "3.11" and py["cache"] == "pip" and "platform/python-sidecar/requirements-ci.txt" in py["cache-dependency-path"]
    assert steps["Install Python dependencies"]["run"] == "pip install pyyaml pytest"
    assert "env" not in _pytest_step(sh) and "env" not in sh             # nothing added to (or scrubbed from) the original environment


def test_the_static_job_keeps_every_other_original_step_in_order(jobs):
    st = jobs[STATIC_JOB]
    assert tuple(s.get("name") for s in st["steps"]) == STATIC_STEPS
    assert not any("pytest tests/ bodha_writers" in str(s.get("run", "")) for s in st["steps"])
    assert st["steps"][0]["with"]["fetch-depth"] == 0 and st["steps"][1]["with"]["python-version"] == "3.11"


def test_the_sidecar_suite_runs_only_sharded(jobs):
    """No job runs the whole selection unsharded any more (it would double the runtime), and only the shard job runs it at all."""
    holders = [name for name, j in jobs.items() for s in j.get("steps", []) if "pytest tests/ bodha_writers/__tests__" in str(s.get("run", ""))]
    assert holders == [SHARD_JOB]


def test_the_aggregate_keeps_the_required_name_and_needs_both_parts(jobs):
    agg = jobs[AGG_JOB]
    assert agg["name"] == REQUIRED_NAME
    assert set(agg["needs"]) == {STATIC_JOB, SHARD_JOB}
    assert str(agg["if"]) == "${{ always() }}"
    step = agg["steps"][0]
    assert step["env"]["STATIC_RESULT"] == f"${{{{ needs.{STATIC_JOB}.result }}}}"
    assert step["env"]["SHARDS_RESULT"] == f"${{{{ needs.{SHARD_JOB}.result }}}}"
    assert sum(1 for j in jobs.values() if j.get("name") == REQUIRED_NAME) == 1


RESULTS = ("success", "failure", "cancelled", "skipped", "")


@pytest.mark.parametrize("static", RESULTS)
@pytest.mark.parametrize("shards", RESULTS)
def test_the_aggregate_passes_only_when_both_parts_succeeded(jobs, static, shards):
    """Run the aggregate's own script: a failed, cancelled, skipped or unset result of EITHER part fails the required check (the parts
    never skip by design, not even on a docs-only change)."""
    script = jobs[AGG_JOB]["steps"][0]["run"]
    p = subprocess.run(["bash", "-c", script], env={"STATIC_RESULT": static, "SHARDS_RESULT": shards, "PATH": "/usr/bin:/bin"},
                       capture_output=True, text=True)
    ok = static == "success" and shards == "success"
    assert (p.returncode == 0) is ok, (static, shards, p.stdout, p.stderr)
    assert ("::error::" in p.stdout) is (not ok)


def test_the_aggregate_fails_when_no_result_is_set(jobs):
    p = subprocess.run(["bash", "-c", jobs[AGG_JOB]["steps"][0]["run"]], env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    assert p.returncode != 0


def test_no_part_can_turn_red_green_or_narrow_what_runs(jobs):
    for jname in (SHARD_JOB, STATIC_JOB, AGG_JOB):
        job = jobs[jname]
        assert "continue-on-error" not in job, jname
        needs = job.get("needs") or []
        assert "changes" not in ([needs] if isinstance(needs, str) else needs) and "docs_only" not in str(job.get("if", "")), jname
        for st in job["steps"]:
            assert "continue-on-error" not in st, (jname, st.get("name"))
    run = _pytest_step(jobs[SHARD_JOB])["run"]
    for bad in ("|| true", "--co ", "--collect-only", "--deselect", " -k ", "--lf", "--last-failed", "set +e"):
        assert bad not in run + " ", bad
