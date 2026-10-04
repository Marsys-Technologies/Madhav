"""test_e6_census_head_stamp.py: strategist ruling N-44 A. Every layer head main() writes carries `registry_revision`,
`registry_fingerprint` (the repo's own registry_fingerprint()) and `tool_commit` (git rev-parse HEAD of the tool checkout, or
null + `tool_commit_unavailable`), so a certificate can never be written from a census measured under a different registry
revision. The stamp is verdict-neutral: the rollup ignores it. Offline (the E1.9 stub harness); no database, no network.

Review round (ACCEPT-WITH-CHANGES): `tool_commit` is HEAD only for a clean, tracked, verifiably-the-right checkout; a dirty
checkout gives `tool_commit` null + `tool_dirty` true; git is run from a scrubbed environment; the stamp is computed once
per run; sha1 and sha256 object ids are accepted. The git behaviour is tested against REAL temporary repositories."""
from __future__ import annotations

import copy
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e1_9_assets_scope as e19  # noqa: E402

STAMP_KEYS = {"registry_revision", "registry_fingerprint", "tool_commit", "tool_dirty", "declarations_sha256", "declarations_version", "db_identity"}   # db_identity: E1.7


@pytest.fixture(autouse=True)
def _carriage_d1_from_the_real_module_path():
    """Several tests here re-point `ac.__file__` at a temporary repo that holds only the tool file. Since the first carriage spec
    (#2991) `ac._carriage_d1()` loads its sibling `carriage_d1.py` from `Path(__file__)`, so a test that ran first (or alone) and
    reached it after the re-point failed (the sibling is absent in the temp repo); it passed only when an earlier test had cached
    the module. Load it from the REAL module path before any re-point, so no test depends on the cache's state."""
    ac._carriage_d1()
    yield

NEEDS_GIT = pytest.mark.skipif(shutil.which("git") is None, reason="git binary not available: real-repository stamp tests cannot run")

_CLEAN_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _g(cwd, *args):
    p = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=30, env=_CLEAN_ENV)
    assert p.returncode == 0, (args, p.stderr)
    return p.stdout.strip()


def _make_repo(root, fmt=None):
    """A real git repo laid out like the checkout (platform/scripts/governance/<tool>.py, the dag guard module, a README),
    one commit. Returns (tool_file, head_sha)."""
    root.mkdir(parents=True, exist_ok=True)
    _g(root, "init", "-q", *([f"--object-format={fmt}"] if fmt else []))
    gov = root / "platform" / "scripts" / "governance"
    guard = root / "platform" / "python-sidecar" / "pipeline" / "orchestrator"
    gov.mkdir(parents=True)
    guard.mkdir(parents=True)
    (gov / "tool.py").write_text("x = 1\n", encoding="utf-8")
    (gov / "sibling_lint.py").write_text("y = 1\n", encoding="utf-8")
    (guard / "dag_edge_guard.py").write_text("z = 1\n", encoding="utf-8")
    (root / "README.md").write_text("r\n", encoding="utf-8")
    _g(root, "add", "-A")
    _g(root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "c1")
    return gov / "tool.py", _g(root, "rev-parse", "HEAD")


def _git_head():
    """HEAD of the tool checkout, computed independently of the code under test; None (caller skips) if unavailable."""
    if shutil.which("git") is None:
        return None
    p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(HERE.parent), capture_output=True, text=True, timeout=10, env=_CLEAN_ENV)
    return p.stdout.strip() if p.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", p.stdout.strip()) else None


def _run(monkeypatch, tmp_path, argv, regs=None):
    e19._stub(monkeypatch, tmp_path, regs)
    out = tmp_path / "census.json"
    monkeypatch.setattr(sys, "argv", ["asset_census.py", *argv, "--out", str(out)])
    rc = ac.main()
    return rc, json.loads(out.read_text(encoding="utf-8"))


def _layer_heads(doc):
    return {k: v for k, v in doc.items() if k in ac.LAYERS}


@NEEDS_GIT
def test_every_layer_head_of_a_full_run_carries_the_stamp(monkeypatch, tmp_path):
    """Round trip through main() on the offline stub path, with the tool file living in a real temporary repo."""
    tool, head = _make_repo(tmp_path / "repo")
    monkeypatch.setattr(ac, "__file__", str(tool))
    rc, doc = _run(monkeypatch, tmp_path, ["--layer", "all"])
    heads = _layer_heads(doc)
    assert set(heads) == set(ac.LAYERS) and rc in (0, 2, 3)
    for k, h in heads.items():
        assert h["registry_revision"] == ac.REGISTRY_REVISION, k
        assert h["registry_fingerprint"] == ac.registry_fingerprint(), k
        assert h["tool_commit"] == head and h["tool_dirty"] is False and "tool_commit_unavailable" not in h, k
        assert "generated" in h and h["layer"] == k           # next to the existing head keys, which are all still there


@NEEDS_GIT
def test_round_trip_rollup_key_is_untouched_by_the_stamp(monkeypatch, tmp_path):
    tool, head = _make_repo(tmp_path / "repo")
    monkeypatch.setattr(ac, "__file__", str(tool))
    regs = {**{k: e19.REG for k in ac.LAYERS}, "L2": e19.REG_L2}
    _, stamped = _run(monkeypatch, tmp_path, ["--layer", "L0,L2", "--rollup"], regs=regs)
    assert stamped["L0"]["tool_commit"] == head and "rollup" in stamped
    monkeypatch.setattr(ac, "census_stamp", lambda: {})       # same run, no layer stamp at all
    _, bare = _run(monkeypatch, tmp_path, ["--layer", "L0,L2", "--rollup"], regs=regs)
    assert not (STAMP_KEYS & set(bare["L0"]) - {"registry_revision", "registry_fingerprint"})
    strip = lambda r: json.dumps({k: v for k, v in r.items() if k != "generated"}, sort_keys=True, default=str)  # noqa: E731
    assert strip(stamped["rollup"]) == strip(bare["rollup"])
    assert not any(k.startswith("tool_") for k in stamped["rollup"])


def test_a_full_run_in_the_real_checkout_stamps_the_independent_head_or_says_why(monkeypatch, tmp_path):
    """The real checkout (not a temp repo): a clean tree stamps git's own HEAD; a dirty tree (a working copy mid-edit) stamps
    null + dirty. Skips, never passes silently, when git cannot answer at all."""
    head = _git_head()
    if head is None:
        pytest.skip("git unavailable or the tool directory is not a git checkout: nothing independent to compare against")
    _, doc = _run(monkeypatch, tmp_path, ["--layer", "L0"])
    h = doc["L0"]
    if h["tool_dirty"]:
        assert h["tool_commit"] is None and h["tool_commit_unavailable"].startswith("dirty checkout: ")
    else:
        assert h["tool_commit"] == head and h["tool_dirty"] is False


def test_a_scoped_run_stamps_its_layer_head_too_and_the_file_header_is_unchanged(monkeypatch, tmp_path):
    rc, doc = _run(monkeypatch, tmp_path, ["--layer", "L0", "--assets", "bg_a"])
    h = doc["L0"]
    assert h["registry_revision"] == ac.REGISTRY_REVISION and h["registry_fingerprint"] == ac.registry_fingerprint()
    assert "tool_commit" in h
    assert doc["scope"]["partial"] is True and not (STAMP_KEYS & set(doc["scope"]))


def test_the_stamp_reads_the_live_revision_and_fingerprint_not_an_import_time_copy(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "REGISTRY_REVISION", 4242)
    monkeypatch.setitem(ac.NA_CAUSES, "Build.target", ac.NA_CAUSES["Build.target"] + ("a-new-cause",))
    fp = ac.registry_fingerprint()
    _, doc = _run(monkeypatch, tmp_path, ["--layer", "L0"])
    assert doc["L0"]["registry_revision"] == 4242 and doc["L0"]["registry_fingerprint"] == fp


def test_the_new_keys_are_only_those_and_no_measurement_or_asset_is_touched(monkeypatch, tmp_path):
    e19._stub(monkeypatch, tmp_path)
    raw = ac.measure("L0")
    raw.pop("generated")
    _, doc = _run(monkeypatch, tmp_path, ["--layer", "L0"])
    h = copy.deepcopy(doc["L0"])
    h.pop("generated")
    extra = set(h) - set(raw)
    assert extra == STAMP_KEYS | ({"tool_commit_unavailable"} if h["tool_commit"] is None else set()) \
        | ({"declarations_unavailable"} if h["declarations_sha256"] is None or h["declarations_version"] is None else set()), extra
    assert h["tool_commit"] is None or h["tool_dirty"] is False
    assert {k: v for k, v in h.items() if k in raw} == json.loads(json.dumps(raw, default=str))


def test_the_rollup_ignores_the_head_keys_and_moves_no_cell(monkeypatch, tmp_path):
    _, doc = _run(monkeypatch, tmp_path, ["--layer", "L0,L2", "--rollup"], regs={**{k: e19.REG for k in ac.LAYERS}, "L2": e19.REG_L2})
    assert doc["rollup"]["registry_revision"] == doc["L0"]["registry_revision"] == doc["L2"]["registry_revision"]
    assert doc["rollup"]["registry_fingerprint"] == doc["L0"]["registry_fingerprint"]
    for k in ("L0", "L2"):
        stamped = ac.rollup_census(doc[k])
        bare = ac.rollup_census({kk: v for kk, v in doc[k].items() if kk not in STAMP_KEYS | {"tool_commit_unavailable", "declarations_unavailable"}})
        assert json.dumps(stamped, sort_keys=True) == json.dumps(bare, sort_keys=True)
        assert json.dumps(doc["rollup"]["layers"][k], sort_keys=True) == json.dumps(stamped, sort_keys=True)


def test_a_head_stamped_under_another_revision_is_distinguishable(monkeypatch, tmp_path):
    """The point of the stamp: two censuses measured under different registry revisions cannot be mistaken for one."""
    _, a = _run(monkeypatch, tmp_path, ["--layer", "L0"])
    monkeypatch.setattr(ac, "REGISTRY_REVISION", ac.REGISTRY_REVISION + 1)
    _, b = _run(monkeypatch, tmp_path, ["--layer", "L0"])
    assert a["L0"]["registry_revision"] != b["L0"]["registry_revision"]
    assert a["L0"]["registry_fingerprint"] == b["L0"]["registry_fingerprint"]    # the fingerprint is content-only (revision is not in it)
    monkeypatch.setitem(ac.NA_CAUSES, "Build.target", ac.NA_CAUSES["Build.target"] + ("a-new-cause",))
    _, c = _run(monkeypatch, tmp_path, ["--layer", "L0"])
    assert c["L0"]["registry_fingerprint"] != a["L0"]["registry_fingerprint"]    # changed content moves it, with or without a bump


@pytest.mark.parametrize("how", ["no_git_binary", "not_a_repo", "garbage_output", "timeout"])
def test_tool_commit_is_null_with_a_reason_when_git_cannot_answer(monkeypatch, tmp_path, how):
    def fake(*a, **k):
        if how == "no_git_binary":
            raise FileNotFoundError("git")
        if how == "timeout":
            raise subprocess.TimeoutExpired("git", 10)
        if how == "not_a_repo":
            return subprocess.CompletedProcess(a[0], 128, "", "fatal: not a git repository (or any of the parent directories): .git\n")
        return subprocess.CompletedProcess(a[0], 0, f"{tmp_path}\nHEAD\n", "")
    monkeypatch.setattr(ac.subprocess, "run", fake)
    s = ac.census_stamp()
    assert s["tool_commit"] is None and s["tool_commit_unavailable"].strip() and s["tool_dirty"] is None
    assert s["registry_revision"] == ac.REGISTRY_REVISION and s["registry_fingerprint"] == ac.registry_fingerprint()


# ───────────────────────── real-git behaviour (temporary repositories, no mocks) ─────────────────────────
@NEEDS_GIT
def test_clean_repo_gives_head_and_not_dirty(tmp_path):
    tool, head = _make_repo(tmp_path / "r")
    assert ac._git_provenance(tool) == dict(tool_commit=head, tool_dirty=False)


@NEEDS_GIT
@pytest.mark.parametrize("rel", ["platform/scripts/governance/tool.py", "platform/scripts/governance/sibling_lint.py",
                                 "platform/python-sidecar/pipeline/orchestrator/dag_edge_guard.py"])
def test_a_modified_tracked_runtime_file_is_dirty_and_uncertifiable(tmp_path, rel):
    tool, head = _make_repo(tmp_path / "r")
    (tmp_path / "r" / rel).write_text("# edited after the commit\n", encoding="utf-8")
    s = ac._git_provenance(tool)
    assert s["tool_commit"] is None and s["tool_dirty"] is True
    assert s["tool_commit_unavailable"] == "dirty checkout: 1 modified files"


@NEEDS_GIT
def test_a_staged_only_change_is_dirty_too_and_the_count_is_exact(tmp_path):
    tool, _ = _make_repo(tmp_path / "r")
    for n in ("tool.py", "sibling_lint.py"):
        (tool.parent / n).write_text("# edit\n", encoding="utf-8")
    _g(tmp_path / "r", "add", "-A")
    assert ac._git_provenance(tool)["tool_commit_unavailable"] == "dirty checkout: 2 modified files"


@NEEDS_GIT
def test_an_untracked_file_alone_is_not_dirty_and_a_change_outside_the_runtime_paths_is_ignored(tmp_path):
    tool, head = _make_repo(tmp_path / "r")
    (tool.parent / "scratch_untracked.py").write_text("q = 1\n", encoding="utf-8")
    (tmp_path / "r" / "README.md").write_text("changed, but not code the census runs\n", encoding="utf-8")
    assert ac._git_provenance(tool) == dict(tool_commit=head, tool_dirty=False)


@NEEDS_GIT
def test_a_non_repo_temp_dir_is_null_with_a_reason(tmp_path):
    d = tmp_path / "plain" / "platform" / "scripts" / "governance"
    d.mkdir(parents=True)
    tool = d / "tool.py"
    tool.write_text("x = 1\n", encoding="utf-8")
    if subprocess.run(["git", "rev-parse", "--git-dir"], cwd=str(d), capture_output=True, env=_CLEAN_ENV).returncode == 0:
        pytest.skip("the system temp dir sits inside a git repository: no genuinely non-repo directory available")
    s = ac._git_provenance(tool)
    assert s["tool_commit"] is None and s["tool_dirty"] is None
    assert s["tool_commit_unavailable"].startswith("not a git checkout")


@NEEDS_GIT
def test_poisoned_git_dir_and_work_tree_do_not_redirect_the_stamp(tmp_path, monkeypatch):
    tool, head = _make_repo(tmp_path / "mine")
    other = tmp_path / "other"
    _, other_head = _make_repo(other)
    (other / "extra.txt").write_text("e\n", encoding="utf-8")
    _g(other, "add", "-A")
    _g(other, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "c2")
    other_head = _g(other, "rev-parse", "HEAD")
    assert other_head != head
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    monkeypatch.setenv("GIT_INDEX_FILE", str(other / ".git" / "index"))
    assert ac._git_provenance(tool) == dict(tool_commit=head, tool_dirty=False)


@NEEDS_GIT
def test_a_non_git_copy_nested_inside_another_repo_never_reports_the_outer_head(tmp_path):
    outer_tool, outer_head = _make_repo(tmp_path / "outer")
    nested = tmp_path / "outer" / "vendor_copy" / "platform" / "scripts" / "governance"
    nested.mkdir(parents=True)
    tool = nested / "tool.py"
    tool.write_text("x = 1\n", encoding="utf-8")                   # a copy: inside the outer worktree, never added to it
    s = ac._git_provenance(tool)
    assert s["tool_commit"] is None and s["tool_commit_unavailable"]
    assert "not tracked" in s["tool_commit_unavailable"] and outer_head not in json.dumps(s)


def test_a_git_toplevel_that_does_not_contain_the_tool_file_is_refused(monkeypatch, tmp_path):
    tool = tmp_path / "platform" / "scripts" / "governance" / "tool.py"
    tool.parent.mkdir(parents=True)
    tool.write_text("x = 1\n", encoding="utf-8")
    sha = "ab" * 20
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    def fake(argv, **k):                                           # git "succeeds" everywhere, but reports a foreign toplevel
        out = f"{elsewhere}\n{sha}\n" if argv[1:2] == ["rev-parse"] else ""
        return subprocess.CompletedProcess(argv, 0, out, "")
    monkeypatch.setattr(ac.subprocess, "run", fake)
    s = ac._git_provenance(tool)
    assert s["tool_commit"] is None and "does not contain the tool file" in s["tool_commit_unavailable"]


def test_git_runs_scrubbed_no_shell_with_timeout_and_the_tool_dir_as_cwd(monkeypatch, tmp_path):
    tool = tmp_path / "platform" / "scripts" / "governance" / "tool.py"
    tool.parent.mkdir(parents=True)
    tool.write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setenv("GIT_DIR", "/nonexistent")
    monkeypatch.setenv("GIT_WORK_TREE", "/nonexistent")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    seen = []

    def spy(argv, **k):
        seen.append((argv, k))
        return subprocess.CompletedProcess(argv, 128, "", "fatal: not a git repository\n")
    monkeypatch.setattr(ac.subprocess, "run", spy)
    ac._git_provenance(tool)
    assert seen
    for argv, k in seen:
        assert argv[0] == "git" and not k.get("shell")
        assert not [e for e in k["env"] if e.startswith("GIT_") and e != "GIT_OPTIONAL_LOCKS"], k["env"].keys()
        assert k["env"]["GIT_OPTIONAL_LOCKS"] == "0" and k["env"].get("PATH") == os.environ.get("PATH")
        assert k["timeout"] and k["timeout"] > 0 and pathlib.Path(k["cwd"]) == tool.resolve().parent


@pytest.mark.parametrize("answer", ["0123456789ab", "HEAD", "A" * 40, "a" * 41])
def test_a_malformed_head_is_never_adopted_even_when_everything_else_is_clean(monkeypatch, tmp_path, answer):
    tool = tmp_path / "platform" / "scripts" / "governance" / "tool.py"
    tool.parent.mkdir(parents=True)
    tool.write_text("x = 1\n", encoding="utf-8")
    top = tmp_path.resolve()

    def fake(argv, **k):                                           # toplevel fine, tracked fine, status clean; only HEAD is odd
        return subprocess.CompletedProcess(argv, 0, f"{top}\n{answer}\n" if argv[1] == "rev-parse" else "", "")
    monkeypatch.setattr(ac.subprocess, "run", fake)
    s = ac._git_provenance(tool)
    assert s["tool_commit"] is None and s["tool_commit_unavailable"].startswith("not a git checkout")


def test_sha_pattern_accepts_sha1_and_sha256_only_in_full_lower_case():
    for ok in ("0123456789abcdef" * 4, "0123456789abcdef0123456789abcdef01234567"):
        assert ac._GIT_SHA.fullmatch(ok)
    for bad in ("", "HEAD", "0123456789ab", "a" * 39, "a" * 41, "a" * 63, "a" * 65, "A" * 40, "g" * 40):
        assert not ac._GIT_SHA.fullmatch(bad), bad


@NEEDS_GIT
def test_a_sha256_repository_is_stamped_with_its_64_hex_head(tmp_path):
    p = subprocess.run(["git", "init", "-q", "--object-format=sha256", str(tmp_path / "probe")], capture_output=True, text=True, env=_CLEAN_ENV)
    if p.returncode != 0:
        pytest.skip(f"this git cannot create sha256 repositories: {p.stderr.strip()[:80]}")
    tool, head = _make_repo(tmp_path / "r", fmt="sha256")
    assert len(head) == 64
    assert ac._git_provenance(tool) == dict(tool_commit=head, tool_dirty=False)


def test_census_stamp_is_computed_once_per_run_and_identical_across_layers(monkeypatch, tmp_path):
    calls = []

    def prov(tool_file):
        calls.append(tool_file)
        return dict(tool_commit=f"{len(calls):040x}", tool_dirty=False)     # a HEAD that moved between calls would differ
    monkeypatch.setattr(ac, "_git_provenance", prov)
    _, doc = _run(monkeypatch, tmp_path, ["--layer", "all"])
    heads = _layer_heads(doc)
    assert set(heads) == set(ac.LAYERS)
    assert len(calls) == 1
    assert {h["tool_commit"] for h in heads.values()} == {f"{1:040x}"}
