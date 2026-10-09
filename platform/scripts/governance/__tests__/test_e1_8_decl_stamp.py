"""test_e1_8_decl_stamp.py: E1.8 declarations stamp. The census head also carries `declarations_sha256` (sha256 of the BYTES of
asset_declarations.json as read by this run) and `declarations_version` (the file's `version`), in EVERY layer head next to
registry_revision / registry_fingerprint / tool_commit, so a certificate cannot cite a census taken before a declaration existed or
changed (the registry fingerprint does not cover that file). Verdict-neutral: REGISTRY_REVISION and the fingerprint are unchanged and
the rollup ignores the new keys. Real temporary git repositories for the git interplay (same pattern as test_e6_census_head_stamp.py);
the main() round trips run on the offline stub path."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import shutil
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402


@pytest.fixture(autouse=True)
def _no_evaluation_copy_marker(monkeypatch):
    """SS N-327: census_stamp now LOOKS for the evaluation-copy marker. These tests fake the database wholesale (every query gets an arbitrary answer), so the lookup is answered 'no marker' here;
    test_n317_evaluation_copy.py covers the lookup itself (fakes and a real PostgreSQL)."""
    monkeypatch.setattr(ac, "read_eval_copy_marker", lambda: dict(checked=True, marker_present=False))
import test_e1_9_assets_scope as e19  # noqa: E402
from test_e6_census_head_stamp import NEEDS_GIT, _g, _layer_heads, _make_repo, _run  # noqa: E402

REAL = ac.DECLARATIONS_PATH
DECL_KEYS = {"declarations_sha256", "declarations_version"}
sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731


def _repo_with_declarations(root, mutate=None, commit_mutated=False):
    """A real temp repo (tool file + the real asset_declarations.json committed). Returns (tool, declarations_path, head_sha, committed_bytes)."""
    tool, head = _make_repo(root)
    d = tool.parent / "asset_declarations.json"
    shutil.copy(REAL, d)
    _g(root, "add", "-A")
    _g(root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "decl")
    head = _g(root, "rev-parse", "HEAD")
    committed = d.read_bytes()
    if mutate:
        d.write_bytes(mutate(committed))
        if commit_mutated:
            _g(root, "add", "-A")
            _g(root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "decl2")
            head = _g(root, "rev-parse", "HEAD")
    return tool, d, head, committed


# ───────────────────────── the stamp itself ─────────────────────────

def test_the_stamp_is_the_sha_of_the_bytes_and_the_files_own_version():
    s = ac.census_stamp()
    raw = REAL.read_bytes()
    assert s["declarations_sha256"] == sha(raw) and s["declarations_version"] == json.loads(raw)["version"]
    assert "declarations_unavailable" not in s
    assert s["registry_revision"] == ac.REGISTRY_REVISION and s["registry_fingerprint"] == ac.registry_fingerprint()
    assert len(s["declarations_sha256"]) == 64 and s["declarations_sha256"] == s["declarations_sha256"].lower()


def test_it_is_the_sha_of_the_BYTES_not_of_the_parsed_content(monkeypatch, tmp_path):
    p = tmp_path / "asset_declarations.json"
    raw = REAL.read_bytes()
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", p)
    p.write_bytes(raw)
    a = ac._declarations_provenance()
    p.write_bytes(raw + b"\n\n")                                          # same JSON, different bytes
    b = ac._declarations_provenance()
    p.write_bytes(raw.replace(b"\n", b"\r\n"))
    c = ac._declarations_provenance()
    assert a["declarations_version"] == b["declarations_version"] == c["declarations_version"]
    assert len({a["declarations_sha256"], b["declarations_sha256"], c["declarations_sha256"]}) == 3
    assert b["declarations_sha256"] == sha(raw + b"\n\n") and c["declarations_sha256"] == sha(raw.replace(b"\n", b"\r\n"))


def test_it_reads_the_file_at_call_time_not_an_import_time_copy(monkeypatch, tmp_path):
    p = tmp_path / "asset_declarations.json"
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", p)
    p.write_text('{"version": "9.9.9"}', encoding="utf-8")
    assert ac.census_stamp()["declarations_version"] == "9.9.9"
    p.write_text('{"version": "9.9.10"}', encoding="utf-8")
    assert ac.census_stamp()["declarations_version"] == "9.9.10"


def test_the_stamp_does_not_move_the_registry_fingerprint_or_revision(monkeypatch, tmp_path):
    before = (ac.REGISTRY_REVISION, ac.registry_fingerprint())
    p = tmp_path / "asset_declarations.json"
    p.write_bytes(REAL.read_bytes() + b" ")
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", p)
    assert ac.census_stamp()["declarations_sha256"] != sha(REAL.read_bytes())
    assert (ac.REGISTRY_REVISION, ac.registry_fingerprint()) == before


# ───────────────────────── never a guess ─────────────────────────

def test_a_missing_declarations_file_stamps_null_with_the_reason(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", tmp_path / "nope.json")
    s = ac.census_stamp()
    assert s["declarations_sha256"] is None and s["declarations_version"] is None
    assert "nope.json" in s["declarations_unavailable"] and "FileNotFoundError" in s["declarations_unavailable"]
    assert s["registry_revision"] == ac.REGISTRY_REVISION                       # the rest of the stamp is intact


def test_a_directory_in_place_of_the_file_is_unreadable_not_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", tmp_path)
    s = ac._declarations_provenance()
    assert s["declarations_sha256"] is None and s["declarations_version"] is None and s["declarations_unavailable"]
    assert s["declarations_sha256"] != sha(b"")                                 # never the sha of nothing


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read a mode-000 file")
def test_an_unreadable_permission_denied_file_stamps_null(monkeypatch, tmp_path):
    p = tmp_path / "asset_declarations.json"
    p.write_bytes(REAL.read_bytes())
    p.chmod(0)
    try:
        monkeypatch.setattr(ac, "DECLARATIONS_PATH", p)
        s = ac._declarations_provenance()
    finally:
        p.chmod(0o600)
    assert s["declarations_sha256"] is None and s["declarations_version"] is None and "PermissionError" in s["declarations_unavailable"]


@pytest.mark.parametrize("body", [b"not json at all", b"\xff\xfe\x00bad utf8", b"[]", b'{"nope": 1}', b'{"version": 3}', b'{"version": " "}', b""])
def test_a_readable_file_with_no_string_version_keeps_the_byte_sha_and_a_null_version_with_a_reason(monkeypatch, tmp_path, body):
    p = tmp_path / "asset_declarations.json"
    p.write_bytes(body)
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", p)
    s = ac._declarations_provenance()
    assert s["declarations_sha256"] == sha(body) and s["declarations_version"] is None and "version" in s["declarations_unavailable"]


# ───────────────────────── real-git interplay ─────────────────────────

@NEEDS_GIT
def test_a_modified_tracked_declarations_file_stamps_the_sha_of_the_bytes_read_and_makes_the_tool_dirty(tmp_path, monkeypatch):
    tool, d, head, committed = _repo_with_declarations(tmp_path / "r", mutate=lambda b: b + b"\n")
    monkeypatch.setattr(ac, "__file__", str(tool))
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", d)
    s = ac.census_stamp()
    assert s["declarations_sha256"] == sha(committed + b"\n") != sha(committed)          # the bytes READ, not the committed ones
    assert s["tool_commit"] is None and s["tool_dirty"] is True and s["tool_commit_unavailable"] == "dirty checkout: 1 modified files"
    assert s["declarations_version"] == json.loads(committed)["version"]


@NEEDS_GIT
def test_a_clean_tree_stamps_the_committed_bytes_and_a_clean_commit_with_other_declarations_has_another_sha(tmp_path, monkeypatch):
    tool, d, head, committed = _repo_with_declarations(tmp_path / "a")
    monkeypatch.setattr(ac, "__file__", str(tool))
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", d)
    one = ac.census_stamp()
    assert one["tool_commit"] == head and one["tool_dirty"] is False and one["declarations_sha256"] == sha(committed)
    doc = json.loads(committed)
    doc["version"] = doc["version"] + ".1"
    tool2, d2, head2, committed2 = _repo_with_declarations(tmp_path / "b", mutate=lambda b: json.dumps(doc).encode(), commit_mutated=True)
    monkeypatch.setattr(ac, "__file__", str(tool2))
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", d2)
    two = ac.census_stamp()
    assert two["tool_commit"] == head2 and two["tool_dirty"] is False                     # BOTH clean: only the declarations stamp tells them apart
    assert two["declarations_sha256"] != one["declarations_sha256"] and two["declarations_version"] == doc["version"] != one["declarations_version"]


# ───────────────────────── round trip through main() ─────────────────────────

def test_every_layer_head_of_a_full_run_carries_both_fields_identically(monkeypatch, tmp_path):
    _, doc = _run(monkeypatch, tmp_path, ["--layer", "all"])
    heads = _layer_heads(doc)
    assert set(heads) == set(ac.LAYERS)
    want = (sha(REAL.read_bytes()), json.loads(REAL.read_bytes())["version"])
    for k, h in heads.items():
        assert (h["declarations_sha256"], h["declarations_version"]) == want and "declarations_unavailable" not in h, k


def test_the_stamp_is_computed_once_per_run(monkeypatch, tmp_path):
    calls = []

    def prov():
        calls.append(1)
        return dict(declarations_sha256=f"{len(calls):064x}", declarations_version=str(len(calls)))
    monkeypatch.setattr(ac, "_declarations_provenance", prov)
    _, doc = _run(monkeypatch, tmp_path, ["--layer", "all"])
    heads = _layer_heads(doc)
    assert len(calls) == 1 and {h["declarations_sha256"] for h in heads.values()} == {f"{1:064x}"} and {h["declarations_version"] for h in heads.values()} == {"1"}


def test_an_unreadable_file_is_stamped_null_with_the_reason_in_every_head_of_a_run(monkeypatch, tmp_path):
    e19._stub(monkeypatch, tmp_path)
    monkeypatch.setattr(ac, "_declarations_provenance", lambda: dict(declarations_sha256=None, declarations_version=None,
                                                                    declarations_unavailable="x could not be read: OSError"))
    out = tmp_path / "census.json"
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "all", "--out", str(out)])
    ac.main()
    for k, h in _layer_heads(json.loads(out.read_text(encoding="utf-8"))).items():
        assert h["declarations_sha256"] is None and h["declarations_version"] is None and h["declarations_unavailable"].startswith("x could"), k


def test_the_rollup_key_is_untouched_and_no_cell_moves(monkeypatch, tmp_path):
    regs = {**{k: e19.REG for k in ac.LAYERS}, "L2": e19.REG_L2}
    _, stamped = _run(monkeypatch, tmp_path, ["--layer", "L0,L2", "--rollup"], regs=regs)
    assert DECL_KEYS <= set(stamped["L0"]) and DECL_KEYS <= set(stamped["L2"]) and "rollup" in stamped
    real_stamp = ac.census_stamp
    monkeypatch.setattr(ac, "census_stamp", lambda: {k: v for k, v in real_stamp().items() if not k.startswith("declarations_")})
    _, bare = _run(monkeypatch, tmp_path, ["--layer", "L0,L2", "--rollup"], regs=regs)
    assert not (DECL_KEYS & set(bare["L0"]))
    strip = lambda r: json.dumps({k: v for k, v in r.items() if k != "generated"}, sort_keys=True, default=str)  # noqa: E731
    assert strip(stamped["rollup"]) == strip(bare["rollup"]) and strip(stamped["rollup_excluded"]) == strip(bare["rollup_excluded"])
    assert not any(k.startswith("declarations_") for k in stamped["rollup"])
    for k in ("L0", "L2"):
        s, b = copy.deepcopy(stamped[k]), copy.deepcopy(bare[k])
        for x in (s, b):
            x.pop("generated")
            for key in list(x):
                if key.startswith("declarations_") or key.startswith("tool_"):
                    x.pop(key)
        assert json.dumps(s, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str), k
        assert json.dumps(ac.rollup_census(stamped[k]), sort_keys=True) == json.dumps(ac.rollup_census(bare[k]), sort_keys=True)


def test_a_scoped_run_stamps_its_head_and_not_the_file_header(monkeypatch, tmp_path):
    _, doc = _run(monkeypatch, tmp_path, ["--layer", "L0", "--assets", "bg_a"])
    assert DECL_KEYS <= set(doc["L0"]) and not (DECL_KEYS & set(doc["scope"]))
