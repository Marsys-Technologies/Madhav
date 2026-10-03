"""test_ci_changes.py: the CI fast path. A docs-only pull request skips the heavy jobs; ANY code, data, config or workflow file runs everything;
a failed/empty/unreadable classification and every non-pull_request event run everything (fail closed). The workflow wiring is pinned too: every
heavy job needs `changes` and runs unless docs_only is exactly 'true'; the cheap/required gates are never skipped.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import ci_changes  # noqa: E402

ROOT = HERE.parents[3]
CI = ROOT / ".github" / "workflows" / "ci.yml"
SCRIPT = HERE.parent / "ci_changes.py"


@pytest.mark.parametrize("files,expected", [
    (["README.md"], True),
    (["00_ARCHITECTURE/CURRENT_STATE_v1_0.md", "00_ARCHITECTURE/SESSION_LOG.md"], True),
    (["00_ARCHITECTURE/briefs/suvarna/exec/NOTE.md", "00_ARCHITECTURE/briefs/x/plan.txt"], True),
    (["99_ARCHIVE/old/report.md"], True),
    (["docs/guide.txt", "notes.md"], True),
    # any code / data / config / workflow file => everything runs
    (["platform/scripts/governance/asset_census.py"], False),
    (["platform/src/lib/x.ts"], False),
    (["platform/supabase/migrations/900_x.sql"], False),
    ([".github/workflows/ci.yml"], False), ([".github/pull_request_template.md"], False), ([".github/CODEOWNERS"], False),
    (["00_ARCHITECTURE/control/asset_dispositions.jsonl"], False),
    (["00_ARCHITECTURE/control/NOTES.md"], False),                                 # control dir is read by the governance tests
    (["00_ARCHITECTURE/CAPABILITY_MANIFEST.json"], False),
    (["00_ARCHITECTURE/briefs/x/data.json"], False),
    (["00_ARCHITECTURE/briefs/x/data.yaml"], False),
    (["platform/scripts/governance/README.md"], False),                            # md next to code can be read by tests
    (["services/gochara_v3/README.md"], False),
    (["platform/scripts/governance/__tests__/NOTES.md"], False),
    (["package.json"], False), (["Dockerfile"], False), (["x.sh"], False),
    # mixed => everything runs
    (["README.md", "platform/src/a.ts"], False), (["a.md", "b.py"], False), (["a.md", ".github/workflows/ci.yml"], False),
    # fail closed
    ([], False), ([""], False), (["../etc/passwd.md"], False), (["/abs/path.md"], False), (["a/../b.md"], False), ([" "], False),
])
def test_classification(files, expected):
    assert ci_changes.docs_only(files) is expected


def test_a_rename_from_code_to_md_is_not_docs_only():
    """`--no-renames` lists the OLD path too: moving platform/x.py to notes.md deletes code."""
    assert ci_changes.docs_only(["notes.md", "platform/x.py"]) is False


def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout


def _repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "n.md").write_text("n\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def _run(repo, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True)


def test_cli_on_a_real_git_diff(tmp_path):
    r = _repo(tmp_path)
    (r / "n.md").write_text("changed\n")
    _git(r, "commit", "-qam", "docs")
    assert _run(r, "--event", "pull_request", "--base", "HEAD^1", "--head", "HEAD").stdout.strip() == "docs_only=true"
    (r / "a.py").write_text("x = 2\n")
    (r / "n.md").write_text("changed again\n")
    _git(r, "commit", "-qam", "mixed")
    assert _run(r, "--event", "pull_request", "--base", "HEAD^1", "--head", "HEAD").stdout.strip() == "docs_only=false"
    _git(r, "mv", "a.py", "a_moved.md")                                                # a code file renamed to .md
    _git(r, "commit", "-qm", "rename")
    assert _run(r, "--event", "pull_request", "--base", "HEAD^1", "--head", "HEAD").stdout.strip() == "docs_only=false"


def test_cli_fails_closed(tmp_path):
    r = _repo(tmp_path)
    (r / "n.md").write_text("changed\n")
    _git(r, "commit", "-qam", "docs")
    for event in ("push", "merge_group", "workflow_dispatch", "schedule"):
        p = _run(r, "--event", event)
        assert p.returncode == 0 and p.stdout.strip() == "docs_only=false", event
    p = _run(r, "--event", "pull_request", "--base", "no-such-ref", "--head", "HEAD")
    assert p.returncode == 0 and p.stdout.strip() == "docs_only=false"             # an unreadable diff
    p = _run(tmp_path / "nope-not-a-repo-xyz" if False else r, "--event", "pull_request", "--base", "HEAD", "--head", "HEAD")
    assert p.stdout.strip() == "docs_only=false"                                   # an empty diff


# ---------------------------------------------------------------- the workflow wiring -----------------------------------------------------

HEAVY = ("typecheck", "typecheck-mcp", "unit-tests", "db-integration-tests", "pratijna-v4-fixture-property-tests", "planner-regression",
         "icr-pr-gate", "governance-tool-tests-shard", "governance-gates-gochara")
NEVER_SKIPPED = ("changes", "secret-scan", "naming-lint", "fact-category-pin-lint", "earned-signal-lint", "registry-parity-gate", "governance-gates",
                 "coverage-gate", "density-census", "governance-tool-tests")


@pytest.fixture(scope="module")
def jobs():
    yaml = pytest.importorskip("yaml")
    if not CI.is_file():
        pytest.skip("no ci.yml on this tree")
    return yaml.safe_load(CI.read_text())["jobs"]


@pytest.mark.parametrize("name", HEAVY)
def test_every_heavy_job_needs_changes_and_runs_unless_docs_only_is_exactly_true(jobs, name):
    j = jobs[name]
    assert j["needs"] in ("changes", ["changes"]) or "changes" in j["needs"]
    cond = str(j["if"])
    assert "!cancelled()" in cond and "needs.changes.outputs.docs_only != 'true'" in cond and "== 'false'" not in cond   # an unset/failed output RUNS the job


@pytest.mark.parametrize("name", NEVER_SKIPPED)
def test_the_cheap_and_required_gates_are_never_skipped_by_the_fast_path(jobs, name):
    j = jobs[name]
    assert "docs_only" not in str(j.get("if", "")), name
    if name != "governance-tool-tests":
        assert "changes" not in (j.get("needs") if isinstance(j.get("needs"), list) else [j.get("needs")]), name


def test_the_changes_job_is_fail_closed(jobs):
    ch = jobs["changes"]
    assert ch["outputs"]["docs_only"] == "${{ steps.classify.outputs.docs_only }}" and ch["timeout-minutes"] <= 10
    run = " ".join(str(s.get("run", "")) for s in ch["steps"])
    assert 'out="docs_only=false"' in run and "case" in run and "ci_changes.py" in run
    co = next(s for s in ch["steps"] if "checkout" in str(s.get("uses", "")))
    assert co["with"]["fetch-depth"] == 2 and "continue-on-error" not in ch and all("continue-on-error" not in s for s in ch["steps"])


def test_the_trigger_set_is_unchanged_so_push_and_merge_group_still_run_everything():
    yaml = pytest.importorskip("yaml")
    if not CI.is_file():
        pytest.skip("no ci.yml on this tree")
    on = yaml.safe_load(CI.read_text())
    on = on.get("on") or on.get(True)
    assert "push" in on and "merge_group" in on and "pull_request" in on


def test_every_job_in_ci_yml_is_classified_here_so_a_new_heavy_job_is_a_conscious_choice(jobs):
    unknown = set(jobs) - set(HEAVY) - set(NEVER_SKIPPED) - {"census-battery"}
    assert not unknown, f"classify these jobs as HEAVY (skipped on docs-only) or NEVER_SKIPPED: {sorted(unknown)}"
