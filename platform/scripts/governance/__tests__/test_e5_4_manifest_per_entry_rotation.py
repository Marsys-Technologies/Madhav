"""test_e5_4_manifest_per_entry_rotation.py: E5.4 — per-entry fingerprint ROTATION for CAPABILITY_MANIFEST.json.

Before E5.4, manifest_fingerprint.py stamped only the ROOT fingerprint. Each entry's own fingerprint (sha256 of the file the entry
points at; drift_detector reports a mismatch as `fingerprint_mismatch`) had no tool that rotated it. These tests prove the new
`--rotate` / `--check-rotation` modes rotate EACH changed entry and not only the root, and (CLAUDE.md §N.8) that every check can
fail: each rule has a seeded defect that makes it exit non-zero, and a mutation harness (see the task report) kills a mutant of
every rule.

Real temporary directories / git repos (no machine-local paths). The module under test is loaded from the real file unless
`E5_4_MF_PATH` points at a mutant copy (the mutation harness sets it; nothing else should).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
MF_PATH = pathlib.Path(os.environ.get("E5_4_MF_PATH") or (HERE.parent / "manifest_fingerprint.py"))

_spec = importlib.util.spec_from_file_location("manifest_fingerprint_under_test", MF_PATH)
mf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mf)

NEEDS_GIT = pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731


def root_fp(entries):
    """The root-fingerprint definition, restated INDEPENDENTLY of the module under test (a test that called the module's own
    function could not catch a mutated definition): sha256(canonical_json(entries))[:16]."""
    blob = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# ───────────────────────────── fixtures / helpers ─────────────────────────────

def _entry(cid, path, content, key="fingerprint", extra=None):
    e = {"canonical_id": cid}
    if path is not None:
        e["path"] = path
    e.update({"version": "1", "status": "CURRENT", "layer": "L1"})
    if extra:
        e.update(extra)
    if key:
        e[key] = sha(content)
    return e


def _render(entries, styles=None, nl="\n", root_extra=None, fp=None, generated_at="2026-01-01T00:00:00+00:00"):
    """Hand-render a manifest with deliberately uneven formatting so a re-serialising rotator would be caught."""
    styles = styles or {}
    parts = []
    for e in entries:
        if styles.get(e["canonical_id"]) == "inline":
            parts.append("    " + json.dumps(e, ensure_ascii=False))
        else:
            body = json.dumps(e, indent=2, ensure_ascii=False).replace("\n", nl + "    ")
            parts.append("    " + body)
    fp = fp if fp is not None else root_fp(entries)
    lines = [
        "{",
        f'  "generated_at": "{generated_at}",',
        '  "generator_version": "1.0",',
        f'  "entry_count": {len(entries)},',
        f'  "fingerprint": "{fp}",',
    ]
    # raw text with a REAL \\u escape next to a literal non-ASCII char: a re-serialising rotator would normalise these
    lines.append('  "note": "caf\\u00e9 \u00e9 raw",')
    lines.append('  "entries": [')
    lines.append(("," + nl).join(parts))
    lines.append("  ]")
    lines.append("}")
    return nl.join(lines) + nl


FILES = {
    "docs/a.md": b"alpha v1\n",
    "docs/b.md": b"bravo v1\n",
    "docs/c.md": b"charlie v1\n",
    "docs/z.md": b"zulu v1 \xc3\xa9\n",
}


def make_repo(root, files=None, entries_fn=None, nl="\n"):
    """A temp repo laid out like the real one: <root>/00_ARCHITECTURE/CAPABILITY_MANIFEST.json + pointed-at files."""
    files = dict(FILES if files is None else files)
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    entries = (entries_fn or _default_entries)(files)
    manifest = root / "00_ARCHITECTURE" / "CAPABILITY_MANIFEST.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(_render(entries, styles={"B": "inline"}, nl=nl), encoding="utf-8", newline="")
    return manifest


def _default_entries(files):
    return [
        _entry("A", "docs/a.md", files["docs/a.md"]),
        _entry("B", "docs/b.md", files["docs/b.md"]),                                   # inline-formatted entry
        _entry("C", "docs/c.md", files["docs/c.md"], key="fingerprint_sha256"),          # the other key spelling
        _entry("V", None, b"", key="fingerprint", extra=None) | {"fingerprint": "virtualfp"},  # virtual: no path
        _entry("Z", "docs/z.md", files["docs/z.md"], extra={"label": "café \\u00e9"}),
    ]


def cli(*argv):
    """In-process main(); returns (rc, stdout, stderr). argparse usage errors surface as rc 5 via _Parser.error."""
    import io
    import contextlib
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = mf.main([str(a) for a in argv])
        except SystemExit as exc:
            rc = exc.code
    return rc, out.getvalue(), err.getvalue()


def sub(*argv, cwd=None):
    r = subprocess.run([sys.executable, str(MF_PATH), *[str(a) for a in argv]], capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout, r.stderr


def git(root, *args):
    env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    r = subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def git_commit_all(root, msg="c"):
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", msg)
    return git(root, "rev-parse", "HEAD")


def mfst(root):
    return root / "00_ARCHITECTURE" / "CAPABILITY_MANIFEST.json"


def entry_text_block(text, cid):
    """The exact source text of one entry object (for byte-for-byte comparisons)."""
    root_spans, entry_spans = mf.locate_spans(text)
    parsed = json.loads(text)
    for i, e in enumerate(parsed["entries"]):
        if e["canonical_id"] == cid:
            start = min(s for s, _ in entry_spans[i].values())
            end = max(e_ for _, e_ in entry_spans[i].values())
            return text[start:end]
    raise KeyError(cid)


def args_for(root, *more):
    return ["--manifest", mfst(root), "--repo-root", root, *more]


# ───────────────────────────── check-rotation ─────────────────────────────

def test_check_rotation_clean_exits_0(tmp_path):
    make_repo(tmp_path)
    rc, out, _ = cli("--check-rotation", *args_for(tmp_path))
    assert rc == 0, out
    assert "4 fingerprinted, 1 virtual" in out and "0 stale" in out


def test_check_rotation_names_the_stale_entry_with_all_four_facts(tmp_path):
    """Seeded defect: edit one pointed-at file. Exit 2 and the line carries id, path, recorded AND actual."""
    make_repo(tmp_path)
    old = sha(FILES["docs/b.md"])
    (tmp_path / "docs/b.md").write_bytes(b"bravo v2\n")
    rc, out, _ = cli("--check-rotation", *args_for(tmp_path))
    assert rc == 2
    stale = [ln for ln in out.splitlines() if ln.startswith("STALE ")]
    assert len(stale) == 1
    new = sha(b"bravo v2\n")
    assert "B docs/b.md" in stale[0] and f"recorded={old}" in stale[0] and f"actual={new}" in stale[0]


def test_check_rotation_lists_every_stale_entry(tmp_path):
    make_repo(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"x\n")
    (tmp_path / "docs/c.md").write_bytes(b"y\n")
    rc, out, _ = cli("--check-rotation", *args_for(tmp_path))
    assert rc == 2
    ids = sorted(ln.split()[1] for ln in out.splitlines() if ln.startswith("STALE "))
    assert ids == ["A", "C"]
    assert "[fingerprint_sha256]" in out  # C reports the key it actually carries


def test_check_rotation_is_read_only(tmp_path):
    make_repo(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"x\n")
    before = mfst(tmp_path).read_bytes()
    cli("--check-rotation", *args_for(tmp_path))
    assert mfst(tmp_path).read_bytes() == before
    assert [p.name for p in mfst(tmp_path).parent.iterdir()] == ["CAPABILITY_MANIFEST.json"]


def test_check_rotation_reports_root_status_without_changing_exit_code(tmp_path):
    """Entries all fresh but the root stale: --check-rotation is about ENTRIES (exit 0); root is informational (--check owns it)."""
    make_repo(tmp_path)
    text = mfst(tmp_path).read_text(encoding="utf-8")
    fp = json.loads(text)["fingerprint"]
    mfst(tmp_path).write_text(text.replace(fp, "0" * 16), encoding="utf-8")
    rc, out, _ = cli("--check-rotation", *args_for(tmp_path))
    assert rc == 0 and "MISMATCH" in out


# ───────────────────────────── rotate: the core proof ─────────────────────────────

def test_rotate_rotates_the_changed_entry_and_the_root_and_nothing_else(tmp_path):
    make_repo(tmp_path)
    before = mfst(tmp_path).read_text(encoding="utf-8")
    old_b = sha(FILES["docs/b.md"])
    (tmp_path / "docs/b.md").write_bytes(b"bravo v2\n")
    new_b = sha(b"bravo v2\n")

    rc, out, err = cli("--rotate", *args_for(tmp_path))
    assert rc == 0, (out, err)
    assert f"ROTATED B docs/b.md [fingerprint]: {old_b} -> {new_b}" in out
    assert out.count("ROTATED ") == 1

    after = mfst(tmp_path).read_text(encoding="utf-8")
    parsed = json.loads(after)
    by_id = {e["canonical_id"]: e for e in parsed["entries"]}
    assert by_id["B"]["fingerprint"] == new_b
    # the OTHER entries' source text is byte-identical (diff of an unrelated entry is empty)
    for cid in ("A", "C", "V", "Z"):
        assert entry_text_block(after, cid) == entry_text_block(before, cid), cid
    # exact diff: B's value + the three root stamp values; nothing else
    import difflib
    changed = [ln for ln in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0)
               if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
    assert len(changed) == 6, changed  # 3 lines out + 3 in: B's inline entry, root fingerprint, generated_at (entry_count is 5 -> 5)
    # the root equals the canonical definition recomputed over the rotated entries
    assert parsed["fingerprint"] == root_fp(parsed["entries"])
    assert parsed["entry_count"] == 5
    assert parsed["generated_at"] != "2026-01-01T00:00:00+00:00"
    # and the whole thing now passes both existing/new checks
    assert cli("--check-rotation", *args_for(tmp_path))[0] == 0
    assert cli("--check", "--manifest", mfst(tmp_path))[0] == 0


def test_rotate_changes_only_value_bytes_not_formatting(tmp_path):
    """The edit is surgical: removing the replaced values from both texts leaves identical text (key order, indentation, escapes)."""
    make_repo(tmp_path)
    before = mfst(tmp_path).read_text(encoding="utf-8")
    (tmp_path / "docs/z.md").write_bytes(b"zulu v2\n")
    assert cli("--rotate", *args_for(tmp_path))[0] == 0
    after = mfst(tmp_path).read_text(encoding="utf-8")
    old_vals = [sha(FILES["docs/z.md"]), json.loads(before)["fingerprint"], json.loads(before)["generated_at"]]
    new_vals = [sha(b"zulu v2\n"), json.loads(after)["fingerprint"], json.loads(after)["generated_at"]]
    strip_b, strip_a = before, after
    for v in old_vals:
        strip_b = strip_b.replace(v, "§")
    for v in new_vals:
        strip_a = strip_a.replace(v, "§")
    assert strip_a == strip_b
    assert '"note": "caf\\u00e9 \u00e9 raw"' in after  # an escaped and a literal non-ASCII char survive exactly as written


def test_rotate_each_changed_entry_individually_listed(tmp_path):
    make_repo(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    (tmp_path / "docs/c.md").write_bytes(b"c2\n")
    rc, out, _ = cli("--rotate", *args_for(tmp_path))
    assert rc == 0
    rot = [ln for ln in out.splitlines() if ln.startswith("ROTATED ")]
    assert [ln.split()[1] for ln in rot] == ["A", "C"]
    old_c, new_c = sha(FILES["docs/c.md"]), sha(b"c2\n")
    assert f"{old_c} -> {new_c}" in out
    parsed = json.loads(mfst(tmp_path).read_text(encoding="utf-8"))
    by_id = {e["canonical_id"]: e for e in parsed["entries"]}
    assert by_id["A"]["fingerprint"] == sha(b"a2\n")
    assert by_id["C"]["fingerprint_sha256"] == sha(b"c2\n")
    assert "fingerprint" not in by_id["C"]  # never invents the other key spelling


def test_rotate_is_idempotent_second_run_changes_nothing(tmp_path):
    make_repo(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    assert cli("--rotate", *args_for(tmp_path))[0] == 0
    first = mfst(tmp_path).read_bytes()
    mtime = mfst(tmp_path).stat().st_mtime_ns
    rc, out, _ = cli("--rotate", *args_for(tmp_path))
    assert rc == 0 and "no-op" in out and "ROTATED" not in out
    assert mfst(tmp_path).read_bytes() == first          # incl. generated_at: no gratuitous restamp
    assert mfst(tmp_path).stat().st_mtime_ns == mtime    # not even rewritten


def test_rotate_with_nothing_stale_but_root_stale_restamps_root_only(tmp_path):
    make_repo(tmp_path)
    text = mfst(tmp_path).read_text(encoding="utf-8")
    fp = json.loads(text)["fingerprint"]
    mfst(tmp_path).write_text(text.replace(fp, "f" * 64), encoding="utf-8")
    before_entries = json.loads(mfst(tmp_path).read_text(encoding="utf-8"))["entries"]
    rc, out, _ = cli("--rotate", *args_for(tmp_path))
    assert rc == 0 and "ROTATED" not in out
    parsed = json.loads(mfst(tmp_path).read_text(encoding="utf-8"))
    assert parsed["entries"] == before_entries
    assert parsed["fingerprint"] == root_fp(before_entries)


def test_rotate_root_fingerprint_changes_when_an_entry_rotates(tmp_path):
    """The root is re-derived over the ROTATED entries (it covers the per-entry fingerprints)."""
    make_repo(tmp_path)
    root_before = json.loads(mfst(tmp_path).read_text(encoding="utf-8"))["fingerprint"]
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    cli("--rotate", *args_for(tmp_path))
    assert json.loads(mfst(tmp_path).read_text(encoding="utf-8"))["fingerprint"] != root_before


def test_rotate_preserves_crlf_and_file_mode(tmp_path):
    make_repo(tmp_path, nl="\r\n")
    os.chmod(mfst(tmp_path), 0o640)
    before = mfst(tmp_path).read_bytes()
    assert before.count(b"\r\n") == before.count(b"\n")
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    assert cli("--rotate", *args_for(tmp_path))[0] == 0
    after = mfst(tmp_path).read_bytes()
    assert after.count(b"\r\n") == after.count(b"\n") == before.count(b"\n")
    assert (mfst(tmp_path).stat().st_mode & 0o777) == 0o640
    assert [p.name for p in mfst(tmp_path).parent.iterdir()] == ["CAPABILITY_MANIFEST.json"]  # no temp litter


def test_rotate_key_spellings_both_keys_rotates_both(tmp_path):
    def entries(files):
        e = _entry("A", "docs/a.md", files["docs/a.md"], key="fingerprint_sha256")
        e["fingerprint"] = sha(files["docs/a.md"])
        return [e]
    make_repo(tmp_path, entries_fn=entries)
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    rc, out, _ = cli("--rotate", *args_for(tmp_path))
    assert rc == 0 and out.count("ROTATED ") == 2
    e = json.loads(mfst(tmp_path).read_text(encoding="utf-8"))["entries"][0]
    assert e["fingerprint"] == e["fingerprint_sha256"] == sha(b"a2\n")


def test_entry_option_restricts_rotation_to_the_named_entries(tmp_path):
    make_repo(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    (tmp_path / "docs/c.md").write_bytes(b"c2\n")
    before = mfst(tmp_path).read_text(encoding="utf-8")
    rc, out, _ = cli("--rotate", *args_for(tmp_path, "--entry", "A"))
    assert rc == 0 and out.count("ROTATED ") == 1
    after = mfst(tmp_path).read_text(encoding="utf-8")
    assert entry_text_block(after, "C") == entry_text_block(before, "C")  # stale C deliberately left alone
    assert cli("--check-rotation", *args_for(tmp_path))[0] == 2           # ...and still reported stale
    assert cli("--check-rotation", *args_for(tmp_path, "--entry", "A"))[0] == 0


# ───────────────────────────── refusals (each exits 5 and writes NOTHING) ─────────────────────────────

def _refused(tmp_path, *extra, mode="--rotate"):
    before = mfst(tmp_path).read_bytes()
    rc, out, err = cli(mode, *args_for(tmp_path, *extra))
    assert rc == 5, (rc, out, err)
    assert mfst(tmp_path).read_bytes() == before, "a refused run must not write"
    assert [p.name for p in mfst(tmp_path).parent.iterdir()] == ["CAPABILITY_MANIFEST.json"]
    return out + err


@pytest.mark.parametrize("mode", ["--rotate", "--check-rotation"])
def test_missing_pointed_at_file_refuses_never_drops_or_invents(tmp_path, mode):
    make_repo(tmp_path)
    (tmp_path / "docs/b.md").write_bytes(b"b2\n")        # a legitimately stale sibling must NOT be half-rotated
    (tmp_path / "docs/c.md").unlink()
    msg = _refused(tmp_path, mode=mode)
    assert "ERROR C docs/c.md" in msg and "missing" in msg
    if mode == "--rotate":
        assert "REFUSED" in msg


def test_unreadable_file_refuses(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("root reads anything")
    make_repo(tmp_path)
    os.chmod(tmp_path / "docs/a.md", 0)
    try:
        msg = _refused(tmp_path)
    finally:
        os.chmod(tmp_path / "docs/a.md", 0o644)
    assert "ERROR A" in msg and "unreadable" in msg


def test_directory_pointer_refused(tmp_path):
    make_repo(tmp_path)
    shutil.rmtree(tmp_path / "docs/a.md", ignore_errors=True)
    (tmp_path / "docs/a.md").unlink()
    (tmp_path / "docs/a.md").mkdir()
    assert "is a directory" in _refused(tmp_path)


def test_symlink_outside_repo_refused_and_inside_repo_followed(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_bytes(b"secret\n")
    make_repo(repo)
    (repo / "docs/a.md").unlink()
    (repo / "docs/a.md").symlink_to(outside)
    assert "resolves outside the repository" in _refused(repo)
    # a link whose target stays inside the repo is fine and fingerprints the TARGET bytes
    (repo / "docs/a.md").unlink()
    (repo / "docs/a.md").symlink_to(repo / "docs/b.md")
    rc, out, _ = cli("--rotate", *args_for(repo))
    assert rc == 0, out
    e = {x["canonical_id"]: x for x in json.loads(mfst(repo).read_text(encoding="utf-8"))["entries"]}
    assert e["A"]["fingerprint"] == sha(FILES["docs/b.md"])


def test_duplicate_canonical_id_refused(tmp_path):
    def entries(files):
        return [_entry("A", "docs/a.md", files["docs/a.md"]), _entry("A", "docs/b.md", files["docs/b.md"])]
    make_repo(tmp_path, entries_fn=entries)
    assert "duplicate canonical_id" in _refused(tmp_path)
    assert "duplicate canonical_id" in _refused(tmp_path, mode="--check-rotation")


def test_duplicate_path_refused_even_when_spelled_differently(tmp_path):
    def entries(files):
        return [_entry("A", "docs/a.md", files["docs/a.md"]), _entry("B", "docs/./a.md", files["docs/a.md"])]
    make_repo(tmp_path, entries_fn=entries)
    assert "duplicate path" in _refused(tmp_path)


@pytest.mark.parametrize("bad", ["/etc/passwd", "../outside.md", "docs/../../outside.md", "..", "."])
def test_absolute_or_escaping_path_refused(tmp_path, bad):
    def entries(files):
        return [_entry("A", bad, b"x")]
    make_repo(tmp_path, entries_fn=entries)
    msg = _refused(tmp_path)
    assert "absolute" in msg or "climbs out" in msg


def test_entry_without_any_fingerprint_key_refused_not_invented(tmp_path):
    def entries(files):
        return [_entry("A", "docs/a.md", files["docs/a.md"], key=None)]
    make_repo(tmp_path, entries_fn=entries)
    assert "refusing to invent" in _refused(tmp_path)


def test_empty_or_non_string_path_refused(tmp_path):
    def entries(files):
        return [_entry("A", "docs/a.md", files["docs/a.md"]) | {"path": ""}]
    make_repo(tmp_path, entries_fn=entries)
    assert "non-empty string" in _refused(tmp_path)


def test_unknown_entry_option_refused(tmp_path):
    make_repo(tmp_path)
    assert "no such canonical_id" in _refused(tmp_path, "--entry", "NOPE")


def test_selecting_a_virtual_entry_is_refused(tmp_path):
    make_repo(tmp_path)
    assert "virtual entry" in _refused(tmp_path, "--entry", "V")


@pytest.mark.parametrize("mode", ["--rotate", "--check-rotation", "--check", "--write"])
def test_corrupted_manifest_json_exits_5(tmp_path, mode):
    make_repo(tmp_path)
    mfst(tmp_path).write_text('{"entries": [ {"canonical_id": "A", ', encoding="utf-8")
    before = mfst(tmp_path).read_bytes()
    rc, out, err = sub(mode, "--manifest", mfst(tmp_path), "--repo-root", tmp_path) if mode in ("--rotate", "--check-rotation") \
        else sub(mode, "--manifest", mfst(tmp_path))
    assert rc == 5, (out, err)
    assert mfst(tmp_path).read_bytes() == before


def test_duplicate_key_inside_an_object_refused(tmp_path):
    make_repo(tmp_path)
    text = mfst(tmp_path).read_text(encoding="utf-8")
    mfst(tmp_path).write_text(text.replace('"generator_version": "1.0",', '"generator_version": "1.0",\n  "entry_count": 99,'), encoding="utf-8")
    assert "duplicate key" in _refused(tmp_path)


@pytest.mark.parametrize("body", ['{"entries": {}}', '{"entries": [1]}', '[]', '{"fingerprint": "x"}'])
def test_structurally_wrong_manifest_refused(tmp_path, body):
    make_repo(tmp_path)
    mfst(tmp_path).write_text(body, encoding="utf-8")
    _refused(tmp_path)


def test_root_missing_a_stamp_key_refuses_rather_than_adding_keys(tmp_path):
    make_repo(tmp_path)
    text = mfst(tmp_path).read_text(encoding="utf-8")
    mfst(tmp_path).write_text(text.replace('  "generated_at": "2026-01-01T00:00:00+00:00",\n', ""), encoding="utf-8")
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    assert "lacks generated_at" in _refused(tmp_path)


def test_usage_errors_exit_5_not_2(tmp_path):
    make_repo(tmp_path)
    assert cli(*[])[0] == 5                                              # no mode
    assert cli("--rotate", "--check-rotation", *args_for(tmp_path))[0] == 5  # two modes
    assert cli("--check", "--manifest", mfst(tmp_path), "--entry", "A")[0] == 5  # --entry is rotation-only
    assert cli("--bogus")[0] == 5


# ───────────────────────────── atomicity ─────────────────────────────

def test_failed_replace_leaves_manifest_intact_and_no_temp_file(tmp_path, monkeypatch):
    make_repo(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    before = mfst(tmp_path).read_bytes()

    def boom(src, dst):
        raise OSError("disk on fire")
    monkeypatch.setattr(mf.os, "replace", boom)
    with pytest.raises(OSError):
        mf.main(["--rotate", *map(str, args_for(tmp_path))])
    assert mfst(tmp_path).read_bytes() == before
    assert [p.name for p in mfst(tmp_path).parent.iterdir()] == ["CAPABILITY_MANIFEST.json"]


def test_manifest_changed_between_read_and_write_abandons_the_write(tmp_path, monkeypatch):
    make_repo(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    real_build = mf.build_rotated_text
    raced = b"{}"

    def racing_build(*a, **k):
        res = real_build(*a, **k)
        mfst(tmp_path).write_bytes(raced)          # someone else edits the manifest after we read it
        return res
    monkeypatch.setattr(mf, "build_rotated_text", racing_build)
    rc, out, err = cli("--rotate", *args_for(tmp_path))
    assert rc == 5 and "changed on disk" in err
    assert mfst(tmp_path).read_bytes() == raced


def test_self_check_refuses_to_write_a_patch_that_does_not_parse(tmp_path, monkeypatch):
    """The post-patch verification can fail: feed it a patch that corrupts an unrelated entry."""
    make_repo(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    real_build = mf.build_rotated_text

    def corrupting_build(text, manifest, changes, stamp_root):
        new_text, ne, nr = real_build(text, manifest, changes, stamp_root)
        return new_text.replace('"label": "caf', '"label": "CAF'), ne, nr    # alters a field of an UNCHANGED entry
    monkeypatch.setattr(mf, "build_rotated_text", corrupting_build)
    before = mfst(tmp_path).read_bytes()
    rc, _, err = cli("--rotate", *args_for(tmp_path))
    assert rc == 5 and "nothing written" in err
    assert mfst(tmp_path).read_bytes() == before


# ───────────────────────────── --ref (real git repos) ─────────────────────────────

@NEEDS_GIT
def test_ref_mode_uses_committed_blobs_not_the_working_tree(tmp_path):
    make_repo(tmp_path)
    git(tmp_path, "init", "-q")
    head = git_commit_all(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"dirty working tree edit\n")
    assert cli("--check-rotation", *args_for(tmp_path))[0] == 2                      # working tree: stale
    rc, out, _ = cli("--check-rotation", *args_for(tmp_path, "--ref", head))        # committed bytes: fresh
    assert rc == 0 and f"ref {head}" in out


@NEEDS_GIT
def test_ref_mode_rotate_stamps_from_the_ref(tmp_path):
    make_repo(tmp_path)
    git(tmp_path, "init", "-q")
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    head = git_commit_all(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"a3 uncommitted\n")
    rc, out, _ = cli("--rotate", *args_for(tmp_path, "--ref", head))
    assert rc == 0, out
    e = {x["canonical_id"]: x for x in json.loads(mfst(tmp_path).read_text(encoding="utf-8"))["entries"]}
    assert e["A"]["fingerprint"] == sha(b"a2\n")


@NEEDS_GIT
def test_ref_mode_missing_directory_symlink_and_bad_ref_refused(tmp_path):
    make_repo(tmp_path)
    git(tmp_path, "init", "-q")
    head = git_commit_all(tmp_path)
    # bad refs
    assert "does not resolve" in _refused(tmp_path, "--ref", "no-such-ref")
    assert "starts with '-'" in _refused(tmp_path, "--ref=--orphan")
    # file removed in a later commit: missing at that ref
    (tmp_path / "docs/c.md").unlink()
    head2 = git_commit_all(tmp_path, "rm")
    assert "does not exist at" in _refused(tmp_path, "--ref", head2)
    assert cli("--check-rotation", *args_for(tmp_path, "--ref", head))[0] == 0      # ...but fine at the old ref
    # directory at ref
    (tmp_path / "docs/a.md").unlink()
    (tmp_path / "docs/a.md").mkdir()
    (tmp_path / "docs/a.md/x").write_bytes(b"x")
    head3 = git_commit_all(tmp_path, "dir")
    assert "is a directory at" in _refused(tmp_path, "--ref", head3)
    # symlink blob at ref
    shutil.rmtree(tmp_path / "docs/a.md")
    (tmp_path / "docs/a.md").symlink_to("b.md")
    head4 = git_commit_all(tmp_path, "link")
    assert "symlink or submodule" in _refused(tmp_path, "--ref", head4)


# ───────────────────────────── CLI contract via a real process ─────────────────────────────

def test_cli_exit_codes_end_to_end(tmp_path):
    make_repo(tmp_path)
    base = ["--manifest", mfst(tmp_path), "--repo-root", tmp_path]
    assert sub("--check-rotation", *base)[0] == 0
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    rc, out, _ = sub("--check-rotation", *base)
    assert rc == 2 and "STALE A docs/a.md" in out
    rc, out, _ = sub("--rotate", *base)
    assert rc == 0 and "ROTATED A" in out
    assert sub("--check-rotation", *base)[0] == 0
    (tmp_path / "docs/a.md").unlink()
    assert sub("--rotate", *base)[0] == 5


def test_default_repo_root_is_two_levels_above_the_manifest(tmp_path):
    make_repo(tmp_path)
    (tmp_path / "docs/a.md").write_bytes(b"a2\n")
    rc, out, _ = cli("--check-rotation", "--manifest", mfst(tmp_path))     # no --repo-root
    assert rc == 2 and "STALE A" in out


# ───────────────────────────── the scanner itself ─────────────────────────────

def test_span_scanner_matches_the_parser_on_awkward_json():
    text = ('{ "k":"v\\"}]", "entries" : [ {"canonical_id":"A","path":"p","fingerprint":"%s",\n'
            '"nested":{"a":[1,2,{"b":"]"}],"c":null,"d":-1.5e3}}, {"canonical_id":"B","fingerprint" : "%s" } ] }' % ("a" * 64, "b" * 64))
    root, ents = mf.locate_spans(text)
    parsed = json.loads(text)
    assert len(ents) == 2
    for spans, e in zip(ents, parsed["entries"]):
        s, en = spans["fingerprint"]
        assert json.loads(text[s:en]) == e["fingerprint"]
    s, en = ents[0]["nested"]
    assert json.loads(text[s:en]) == parsed["entries"][0]["nested"]
