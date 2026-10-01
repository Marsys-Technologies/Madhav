"""test_e6_census_head_stamp.py: strategist ruling N-44 A. Every layer head main() writes carries `registry_revision`,
`registry_fingerprint` (the repo's own registry_fingerprint()) and `tool_commit` (git rev-parse HEAD of the tool checkout, or
null + `tool_commit_unavailable`), so a certificate can never be written from a census measured under a different registry
revision. The stamp is verdict-neutral: the rollup ignores it. Offline (the E1.9 stub harness); no database, no network."""
from __future__ import annotations

import copy
import json
import pathlib
import re
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e1_9_assets_scope as e19  # noqa: E402

STAMP_KEYS = {"registry_revision", "registry_fingerprint", "tool_commit"}


def _git_head():
    p = subprocess.run(["git", "-C", str(HERE.parent), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
    return p.stdout.strip() if p.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", p.stdout.strip()) else None


def _run(monkeypatch, tmp_path, argv, regs=None):
    e19._stub(monkeypatch, tmp_path, regs)
    out = tmp_path / "census.json"
    monkeypatch.setattr(sys, "argv", ["asset_census.py", *argv, "--out", str(out)])
    rc = ac.main()
    return rc, json.loads(out.read_text(encoding="utf-8"))


def _layer_heads(doc):
    return {k: v for k, v in doc.items() if k in ac.LAYERS}


def test_every_layer_head_of_a_full_run_carries_the_stamp(monkeypatch, tmp_path):
    rc, doc = _run(monkeypatch, tmp_path, ["--layer", "all"])
    heads = _layer_heads(doc)
    assert set(heads) == set(ac.LAYERS) and rc in (0, 2, 3)
    expect_commit = _git_head()
    for k, h in heads.items():
        assert h["registry_revision"] == ac.REGISTRY_REVISION, k
        assert h["registry_fingerprint"] == ac.registry_fingerprint(), k
        assert h["tool_commit"] == expect_commit, k
        if expect_commit is None:
            assert h["tool_commit_unavailable"], k
        assert "generated" in h and h["layer"] == k           # next to the existing head keys, which are all still there


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
    assert extra == STAMP_KEYS | ({"tool_commit_unavailable"} if h["tool_commit"] is None else set()), extra
    assert {k: v for k, v in h.items() if k in raw} == json.loads(json.dumps(raw, default=str))


def test_the_rollup_ignores_the_head_keys_and_moves_no_cell(monkeypatch, tmp_path):
    _, doc = _run(monkeypatch, tmp_path, ["--layer", "L0,L2", "--rollup"], regs={**{k: e19.REG for k in ac.LAYERS}, "L2": e19.REG_L2})
    assert doc["rollup"]["registry_revision"] == doc["L0"]["registry_revision"] == doc["L2"]["registry_revision"]
    assert doc["rollup"]["registry_fingerprint"] == doc["L0"]["registry_fingerprint"]
    for k in ("L0", "L2"):
        stamped = ac.rollup_census(doc[k])
        bare = ac.rollup_census({kk: v for kk, v in doc[k].items() if kk not in STAMP_KEYS | {"tool_commit_unavailable"}})
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
def test_tool_commit_is_null_with_a_reason_when_the_checkout_is_not_readable(monkeypatch, how):
    def fake(*a, **k):
        if how == "no_git_binary":
            raise FileNotFoundError("git")
        if how == "timeout":
            raise subprocess.TimeoutExpired("git", 10)
        if how == "not_a_repo":
            return subprocess.CompletedProcess(a[0], 128, "", "fatal: not a git repository (or any of the parent directories): .git\n")
        return subprocess.CompletedProcess(a[0], 0, "HEAD\n", "")
    monkeypatch.setattr(ac.subprocess, "run", fake)
    s = ac.census_stamp()
    assert s["tool_commit"] is None and s["tool_commit_unavailable"].strip()
    assert s["registry_revision"] == ac.REGISTRY_REVISION and s["registry_fingerprint"] == ac.registry_fingerprint()


def test_tool_commit_is_a_full_lower_case_sha_when_git_answers(monkeypatch):
    sha = "0123456789abcdef0123456789abcdef01234567"
    monkeypatch.setattr(ac.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, sha + "\n", ""))
    s = ac.census_stamp()
    assert s["tool_commit"] == sha and "tool_commit_unavailable" not in s
    monkeypatch.setattr(ac.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, sha[:12] + "\n", ""))
    assert ac.census_stamp()["tool_commit"] is None          # an abbreviated or malformed answer is never adopted
