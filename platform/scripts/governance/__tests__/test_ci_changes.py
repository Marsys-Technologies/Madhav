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


NO_PINS = frozenset()


@pytest.mark.parametrize("files,expected", [
    (["00_ARCHITECTURE/briefs/suvarna/exec/NOTE.md", "00_ARCHITECTURE/briefs/x/plan.txt"], True),
    (["00_ARCHITECTURE/SOME_NEW_NOTE_v1_0.md"], True),
    (["99_ARCHIVE/old/report.md"], True),
    (["00_ARCHITECTURE/briefs/x/NOTE.MD"], True),                                   # extension compared case-insensitively
    # anything else never skips: markdown beside code, canonical corpora (read by the unit tests), root files, outside the docs roots
    (["README.md"], False), (["CLAUDE.md"], False), (["docs/guide.txt"], False), (["notes.md"], False),
    (["025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"], False), (["01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md"], False),
    (["platform/scripts/governance/README.md"], False), (["services/gochara_v3/README.md"], False),
    (["platform/scripts/governance/__tests__/NOTES.md"], False),
    # code / data / config / workflow
    (["platform/scripts/governance/asset_census.py"], False), (["platform/src/lib/x.ts"], False), (["platform/supabase/migrations/900_x.sql"], False),
    ([".github/workflows/ci.yml"], False), ([".github/pull_request_template.md"], False), ([".github/CODEOWNERS"], False),
    (["package.json"], False), (["Dockerfile"], False), (["x.sh"], False),
    # each deny rule isolated (a docs-looking md that only ONE rule excludes)
    (["00_ARCHITECTURE/control/NOTES.md"], False),                                  # control dir
    (["00_ARCHITECTURE/autonomy/NOTES.md"], False),                                 # autonomy dir
    (["00_ARCHITECTURE/briefs/x/tests/a.md"], False), (["00_ARCHITECTURE/briefs/x/Tests/a.md"], False),
    (["00_ARCHITECTURE/briefs/x/__tests__/a.md"], False), (["00_ARCHITECTURE/briefs/x/fixtures/a.md"], False),
    (["00_ARCHITECTURE/briefs/x/migrations/a.md"], False), (["00_ARCHITECTURE/briefs/x/node_modules/a.md"], False),
    # extension rules under the docs roots: only md/txt
    (["00_ARCHITECTURE/briefs/x/run"], False), (["00_ARCHITECTURE/briefs/x/data.jsonl"], False), (["00_ARCHITECTURE/briefs/x/data.json"], False),
    (["00_ARCHITECTURE/briefs/x/tool.py"], False), (["00_ARCHITECTURE/briefs/x/tool.PY"], False), (["00_ARCHITECTURE/briefs/x/tool.pl"], False),
    (["99_ARCHIVE/x/data.xlsx"], False), (["99_ARCHIVE/x/script.bash"], False),
    # exact names (no stripping): a trailing/leading space is not a docs file
    (["00_ARCHITECTURE/briefs/x/a.md "], False), ([" 00_ARCHITECTURE/briefs/x/a.md"], False),
    # mixed => everything runs
    (["00_ARCHITECTURE/briefs/x/a.md", "platform/src/a.ts"], False), (["00_ARCHITECTURE/briefs/a.md", "b.py"], False),
    (["00_ARCHITECTURE/briefs/a.md", ".github/workflows/ci.yml"], False),
    # fail closed
    ([], False), ([""], False), (["../etc/passwd.md"], False), (["/abs/path.md"], False), (["00_ARCHITECTURE/../b.md"], False),
    (["00_ARCHITECTURE//a.md"], False), (["00_ARCHITECTURE/./a.md"], False), (["00_ARCHITECTURE\\a.md"], False),
])
def test_classification(files, expected):
    assert ci_changes.docs_only(files, NO_PINS) is expected


def test_a_document_a_test_names_is_never_skippable():
    f = "00_ARCHITECTURE/briefs/x/PINNED_NOTE.md"
    assert ci_changes.docs_only([f], NO_PINS) is True
    assert ci_changes.docs_only([f], frozenset({f})) is False
    assert ci_changes.docs_only([f, "00_ARCHITECTURE/briefs/x/other.md"], frozenset({f})) is False
    assert ci_changes.docs_only([f], frozenset({"*"})) is False                      # the wildcard sentinel: nothing is provably unpinned


def test_a_failing_scan_fails_closed(monkeypatch):
    def boom(*a, **k):
        raise OSError("git ls-files failed")
    monkeypatch.setattr(ci_changes, "scan_pinned", boom)
    assert ci_changes._pinned() == frozenset({"*"}) and ci_changes.docs_only(["00_ARCHITECTURE/briefs/x/a.md"]) is False


def test_a_scan_that_finds_nothing_classifies_nothing_as_docs_only(monkeypatch):
    """A real tree always has tests naming documents: an EMPTY scan means the scan did not see the tests, so it must never read as 'nothing is pinned'."""
    monkeypatch.setattr(ci_changes, "scan_pinned", lambda *a, **k: [])
    assert ci_changes._pinned() == frozenset({"*"})
    assert ci_changes.docs_only(["00_ARCHITECTURE/briefs/x/a.md"]) is False
    assert ci_changes.is_doc("00_ARCHITECTURE/briefs/x/a.md") is False


def test_the_live_scan_is_non_empty_and_agrees_with_the_classifier():
    try:
        pins = ci_changes._pinned()
    except (OSError, subprocess.SubprocessError):
        pytest.skip("not a git checkout")
    if "*" in pins:
        pytest.skip("no git checkout to scan (the classifier fails closed here, which the tests above pin)")
    assert pins, "a repo whose tests name no documents at all is not credible"
    sample = sorted(pins)[0]
    assert ci_changes.docs_only([sample], pins) is False                              # a pinned document never takes the fast path
    assert ci_changes.docs_only([sample, "00_ARCHITECTURE/briefs/zz/unpinned_new_note.md"], pins) is False
    assert ci_changes.docs_only(["00_ARCHITECTURE/briefs/zz/unpinned_new_note.md"], pins) is True


def test_a_tracked_test_file_that_cannot_be_read_fails_closed(tmp_path, monkeypatch):
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "test_ok.py").write_text('open("00_ARCHITECTURE/a.md")')
    files = ["t/test_ok.py", "t/test_gone.py", "00_ARCHITECTURE/a.md"]
    monkeypatch.setattr(ci_changes, "tracked_files", lambda: files)
    monkeypatch.setattr(ci_changes, "HERE", tmp_path / "a" / "b" / "c")                  # HERE.parents[2] == tmp_path: the repo root the scan reads
    assert ci_changes.scan_pinned(files=files) == ["00_ARCHITECTURE/a.md"]               # the lenient scan skips the unreadable file and still pins a.md
    assert ci_changes._pinned() == frozenset({"*"})                                      # the classifier's scan is strict: an unread test could hide a pin


def _fixture_tree(tmp_path, monkeypatch):
    """A tree whose tests name two documents; only OTHER.md still exists (GONE.md is what the change deletes / renames away)."""
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "test_a.py").write_text('open("00_ARCHITECTURE/briefs/x/GONE.md"); open("00_ARCHITECTURE/briefs/x/OTHER.md")')
    monkeypatch.setattr(ci_changes, "tracked_files", lambda: ["t/test_a.py", "00_ARCHITECTURE/briefs/x/OTHER.md"])
    monkeypatch.setattr(ci_changes, "HERE", tmp_path / "a" / "b" / "c")


GONE = "00_ARCHITECTURE/briefs/x/GONE.md"


def test_deleting_a_pinned_document_is_not_docs_only(tmp_path, monkeypatch):
    """Review N-103 (H1): the checked-out tree no longer lists a document the change deletes, so a test token naming it matched nothing. The change's own
    file list is part of the scan, so the deleted document stays pinned."""
    _fixture_tree(tmp_path, monkeypatch)
    assert ci_changes.docs_only([GONE]) is False
    assert ci_changes.docs_only(["00_ARCHITECTURE/briefs/x/UNRELATED.md"]) is True            # a deleted/edited document no test names is still skippable


def test_renaming_a_pinned_document_away_is_not_docs_only(tmp_path, monkeypatch):
    _fixture_tree(tmp_path, monkeypatch)
    assert ci_changes.docs_only([GONE, "00_ARCHITECTURE/briefs/x/GONE_renamed.md"]) is False  # `--no-renames` lists the old path as a deletion
    assert ci_changes.docs_only(["00_ARCHITECTURE/briefs/x/UNRELATED.md", "00_ARCHITECTURE/briefs/x/UNRELATED_renamed.md"]) is True


def test_the_change_file_list_cannot_shrink_the_pinned_set(tmp_path, monkeypatch):
    _fixture_tree(tmp_path, monkeypatch)
    assert ci_changes._pinned([]) <= ci_changes._pinned([GONE, "other/file.py"])
    assert ci_changes._pinned([GONE, 7, None, ""]) >= {GONE}                                # junk entries are ignored, never fatal


def test_scan_reads_ts_tests_and_matches_extensions_case_insensitively(tmp_path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "a.test.ts").write_text("readFileSync('00_ARCHITECTURE/briefs/x/Upper.MD')")
    files = ["web/a.test.ts", "00_ARCHITECTURE/briefs/x/Upper.MD", "00_ARCHITECTURE/briefs/x/lower.txt"]
    assert ci_changes.scan_pinned(tmp_path, files) == ["00_ARCHITECTURE/briefs/x/Upper.MD"]


def test_there_is_no_committed_pinned_list():
    assert not (HERE.parent / "ci_docs_pinned.json").exists(), "the pinned set is computed at classify time; a committed copy would go stale and conflict"
    assert "PINNED_FILE" not in vars(ci_changes) and "pinned_document" not in vars(ci_changes)


def test_scan_pinned_resolves_paths_and_basenames(tmp_path):
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "test_a.py").write_text('open("00_ARCHITECTURE/briefs/x/A.md"); read("B.md"); read("sub/C.txt"); "unrelated.md"')
    files = ["t/test_a.py", "00_ARCHITECTURE/briefs/x/A.md", "00_ARCHITECTURE/B.md", "00_ARCHITECTURE/z/B.md", "00_ARCHITECTURE/sub/C.txt",
             "00_ARCHITECTURE/briefs/other.md", "platform/x/B.md"]
    got = ci_changes.scan_pinned(tmp_path, files)
    assert got == ["00_ARCHITECTURE/B.md", "00_ARCHITECTURE/briefs/x/A.md", "00_ARCHITECTURE/sub/C.txt", "00_ARCHITECTURE/z/B.md"]


def test_a_rename_from_code_to_md_is_not_docs_only():
    """`--no-renames` lists the OLD path too: moving platform/x.py to a doc deletes code."""
    assert ci_changes.docs_only(["00_ARCHITECTURE/briefs/x/notes.md", "platform/x.py"], NO_PINS) is False


# Built by concatenation on purpose: the classifier scans THIS file for document names, and a literal "<name>.md" would pin the fixture document in
# the (real-repo) scan that the CLI tests run, which is the behaviour under test in the opposite direction.
NOTE_NAME = "n" + ".md"


def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout


def _repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "00_ARCHITECTURE" / "briefs").mkdir(parents=True)
    (tmp_path / "00_ARCHITECTURE" / "briefs" / NOTE_NAME).write_text("n\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def _run(repo, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True)


def test_cli_on_a_real_git_diff(tmp_path):
    r = _repo(tmp_path)
    (r / "00_ARCHITECTURE" / "briefs" / NOTE_NAME).write_text("changed\n")
    _git(r, "commit", "-qam", "docs")
    assert _run(r, "--event", "pull_request", "--base", "HEAD^1", "--head", "HEAD").stdout.strip() == "docs_only=true"
    (r / "a.py").write_text("x = 2\n")
    (r / "00_ARCHITECTURE" / "briefs" / NOTE_NAME).write_text("changed again\n")
    _git(r, "commit", "-qam", "mixed")
    assert _run(r, "--event", "pull_request", "--base", "HEAD^1", "--head", "HEAD").stdout.strip() == "docs_only=false"
    _git(r, "mv", "a.py", "00_ARCHITECTURE/briefs/a_moved.md")                                                # a code file renamed to .md
    _git(r, "commit", "-qm", "rename")
    assert _run(r, "--event", "pull_request", "--base", "HEAD^1", "--head", "HEAD").stdout.strip() == "docs_only=false"


def test_cli_a_real_git_rename_of_a_pinned_document_is_not_docs_only(tmp_path):
    """Review N-103 round 2: `--no-renames` makes git report the OLD path of a rename too. The scan pins 00_ARCHITECTURE/AGENTS.md (a real test names it),
    so moving it must not take the fast path; without --no-renames git would report only the new, unpinned path (the new name is concatenated so this file does not pin it)."""
    r = _repo(tmp_path)
    (r / "00_ARCHITECTURE" / "AGENTS.md").write_text("agents\n")
    _git(r, "add", ".")
    _git(r, "commit", "-qm", "add pinned doc")
    _git(r, "mv", "00_ARCHITECTURE/AGENTS.md", "00_ARCHITECTURE/briefs/AGENTS_zz_moved" + ".md")
    _git(r, "commit", "-qm", "rename")
    assert _run(r, "--event", "pull_request", "--base", "HEAD^1", "--head", "HEAD").stdout.strip() == "docs_only=false"


def test_cli_fails_closed(tmp_path):
    r = _repo(tmp_path)
    (r / "00_ARCHITECTURE" / "briefs" / NOTE_NAME).write_text("changed\n")
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


# ---------------------------------------------------------------- the classify STEP itself, run for real (review N-103: Y4/Y5/Y6/Y9) -------

def _step_script():
    yaml = pytest.importorskip("yaml")
    if not CI.is_file():
        pytest.skip("no ci.yml on this tree")
    ch = yaml.safe_load(CI.read_text())["jobs"]["changes"]
    return next(st["run"] for st in ch["steps"] if st.get("id") == "classify")


def _run_step(tmp_path, event, *, files, script_text=None):
    """Run the workflow's own classify script in a throwaway repo whose HEAD^1..HEAD diff touches `files` (relative path -> content)."""
    import os
    repo = tmp_path
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    gov = repo / "platform" / "scripts" / "governance"
    gov.mkdir(parents=True)
    (gov / "ci_changes.py").write_text(script_text if script_text is not None else SCRIPT.read_text())
    (gov / "__tests__").mkdir()
    (gov / "__tests__" / "test_canary.py").write_text('open("00_ARCHITECTURE/briefs/x/CANARY_PINNED.md")')   # a real tree's tests always name some document
    (repo / "00_ARCHITECTURE" / "briefs" / "x").mkdir(parents=True)
    (repo / "00_ARCHITECTURE" / "briefs" / "x" / "CANARY_PINNED.md").write_text("c")
    (repo / "base.txt").write_text("b")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    for rel, content in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(content)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "change")
    out = repo / "gh_output"
    out.write_text("")
    env = {"GITHUB_EVENT_NAME": event, "GITHUB_OUTPUT": str(out), "PATH": os.environ["PATH"], "HOME": str(tmp_path)}
    p = subprocess.run(["bash", "-e", "-c", _step_script()], cwd=repo, env=env, capture_output=True, text=True)
    return p.returncode, out.read_text().strip()


DOC = {"00_ARCHITECTURE/briefs/x/NOTE.md": "n"}
CODE = {"platform/scripts/governance/x.py": "x = 1"}


def test_the_step_classifies_a_docs_only_pull_request_as_true(tmp_path):
    assert _run_step(tmp_path, "pull_request", files=DOC) == (0, "docs_only=true")


def test_the_step_runs_everything_for_code_mixed_and_non_pull_request_events(tmp_path_factory):
    assert _run_step(tmp_path_factory.mktemp("a"), "pull_request", files=CODE) == (0, "docs_only=false")
    assert _run_step(tmp_path_factory.mktemp("b"), "pull_request", files={**DOC, **CODE}) == (0, "docs_only=false")
    for ev in ("merge_group", "push", "workflow_dispatch"):
        assert _run_step(tmp_path_factory.mktemp(ev), ev, files=DOC) == (0, "docs_only=false"), ev       # a hard-coded pull_request would say true


def test_the_step_fails_closed_when_the_classifier_breaks_or_prints_garbage(tmp_path_factory):
    assert _run_step(tmp_path_factory.mktemp("crash"), "pull_request", files=DOC, script_text="import sys\nsys.exit(3)\n") == (0, "docs_only=false")
    assert _run_step(tmp_path_factory.mktemp("syntax"), "pull_request", files=DOC, script_text="def (:\n") == (0, "docs_only=false")
    assert _run_step(tmp_path_factory.mktemp("garbage"), "pull_request", files=DOC, script_text='print("docs_only=maybe")\n') == (0, "docs_only=false")
    assert _run_step(tmp_path_factory.mktemp("empty"), "pull_request", files=DOC, script_text="") == (0, "docs_only=false")
    assert _run_step(tmp_path_factory.mktemp("liar"), "pull_request", files=CODE, script_text='print("docs_only=true")\n') == (0, "docs_only=true")   # the step trusts a well-formed answer (the classifier is what is tested)


def test_the_step_diffs_the_merge_commit_against_its_first_parent(tmp_path):
    """A mutant that diffs HEAD against HEAD classifies an empty diff (false); a docs change must come out true."""
    assert _run_step(tmp_path, "pull_request", files=DOC)[1] == "docs_only=true"


def test_the_classifier_has_no_unhandled_exception_path(monkeypatch):
    monkeypatch.setattr(ci_changes, "changed_files", lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
    assert ci_changes.main(["--event", "pull_request"]) == 0
