"""review_bundle.py (L.12r): the independent-review bundle builder. Temp dirs only. The fake
secrets below are assembled at runtime so this file itself never matches a secret pattern (it is
shipped inside the bundle)."""
import hashlib
import os
import subprocess
import zipfile
from pathlib import Path

import pytest

from suvarna_tracker import review_bundle as RB

# ---------------------------------------------------------------------------------------------
# Fakes (assembled, never literal)
# ---------------------------------------------------------------------------------------------

FAKE_SECRETS = {
    # (values on their own line: a `"…password": "<8+ chars>"` line is itself a genuine hit)
    "connection-url-with-password":
        "DATABASE_URL=" + "postgresql://" + "svc_app" + ":" + "Zq8vT3rLm9Wx" + "@db:5432/x",
    "PGPASSWORD-with-value": "export PG" + "PASSWORD=" + "s3cr3tValue9",
    "quoted-password":
        "db_pass" + "word: \"" + "Kd83jfLq0pZ" + "\"",
    "private-key-header": "-----BEGIN " + "RSA PRIVATE" + " KEY-----",
    "aws-access-key-id": "id = " + "AK" + "IA" + "ABCDEFGHIJ234567",
    "gcp-api-key": "key=" + "AI" + "za" + "Sy0123456789abcdefghijABCDEFGHIJ_-x",
    "base64-run-near-key/secret/token": "api_token = " + "Qm9vdGhWYXJpYW50" + "S2V5TWF0ZXJpYWwxMjM0NTY3ODk",
}

NOT_SECRETS = [
    "commit 21b3ec65e8d2aa3a7504446fd212078365cb170c is the token of record",
    "sha256 addd01be84f239f68fa4b5c1e0d7e1c9b1c8f6f0a2b3c4d5e6f7a8b9c0d1e2f3 key",
    "the key file 00_ARCHITECTURE/control/registry_coverage_report.json",
    "PG" + "PASSWORD=$PGADMINPW psql",
    "PG" + "PASSWORD=${PGADMINPW} psql",
    "return 1, '', 'connection to " + "postgres://user:" + "hunter2" + "@10.0.0.5:5432/db failed'",
    "const PASSWORD_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'",
    "read -rs -p 'postgres pass" + "word: ' PGADMINPW; echo",
    "test_isolation_decided_no_blocks_on_group_writable_decisions_log token",
]


def _git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t",
                    "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)


def _repo(tmp_path, files):
    root = tmp_path / "repo"
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    _git(root.parent, "init", "-q", str(root))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    return root, head


def _manifest_rows(out):
    rows = {}
    for line in (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        rel, src, commit, state, digest = line.split("\t")
        rows[rel] = (src, commit, state, digest)
    return rows


# ---------------------------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(FAKE_SECRETS))
def test_scan_text_finds_each_fake_secret(name):
    hits = RB.scan_text("line one\n" + FAKE_SECRETS[name] + "\n")
    assert (2, name) in hits


@pytest.mark.parametrize("line", NOT_SECRETS)
def test_scan_text_ignores_hashes_paths_placeholders_and_known_fixtures(line):
    assert RB.scan_text(line) == []


def test_module_and_this_test_file_do_not_trip_the_scanner():
    """Both ship inside the bundle; if either tripped the scan, the real build would abort."""
    assert RB.scan_text(Path(RB.__file__).read_text(encoding="utf-8")) == []
    assert RB.scan_text(Path(__file__).read_text(encoding="utf-8")) == []


# ---------------------------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------------------------

def test_build_copies_files_and_manifest_hashes_and_git_state_are_correct(tmp_path):
    root, head = _repo(tmp_path, {
        "docs/PACKAGE.md": "# package\n",
        "docs/plan.md": "plan v1\n",
        "code/mod.py": "x = 1\n",
    })
    (root / "code/mod.py").write_text("x = 2\n", encoding="utf-8")         # modified
    (root / "code/new.py").write_text("y = 1\n", encoding="utf-8")         # untracked
    outside = tmp_path / "home" / "run" / "DECISIONS.jsonl"                # not in git
    outside.parent.mkdir(parents=True)
    outside.write_text('{"id":"N-2","state":"decided"}\n', encoding="utf-8")

    entries = [RB.Entry("docs/PACKAGE.md", root / "docs/PACKAGE.md"),
               RB.Entry("docs/plan.md", root / "docs/plan.md"),
               RB.Entry("code/mod.py", root / "code/mod.py"),
               RB.Entry("code/new.py", root / "code/new.py"),
               RB.Entry("run/DECISIONS.jsonl", outside)]
    out = tmp_path / "bundle"
    res = RB.build_bundle(out, entries, package_rel="docs/PACKAGE.md")

    assert res["files"] == 5 and res["zip"] is None
    rows = _manifest_rows(out)
    assert set(rows) == {"docs/PACKAGE.md", "docs/plan.md", "code/mod.py", "code/new.py",
                         "run/DECISIONS.jsonl"}
    for rel, (src, commit, state, digest) in rows.items():
        copied = (out / rel).read_bytes()
        assert copied == Path(src).read_bytes()
        assert digest == hashlib.sha256(copied).hexdigest()
    assert rows["docs/plan.md"][1:3] == (head, "clean")
    assert rows["code/mod.py"][1:3] == (head, "modified")
    assert rows["code/new.py"][1:3] == (head, "untracked")
    assert rows["run/DECISIONS.jsonl"][1:3] == ("-", "not-in-git")
    assert "docs/PACKAGE.md" in (out / "README_FIRST.md").read_text(encoding="utf-8")


def test_executable_bit_is_preserved_in_folder_and_zip(tmp_path):
    root, _ = _repo(tmp_path, {"P.md": "p\n", "hook.sh": "#!/bin/sh\nexit 0\n"})
    (root / "hook.sh").chmod(0o755)
    out = tmp_path / "bundle"
    res = RB.build_bundle(out, [RB.Entry("P.md", root / "P.md"), RB.Entry("hook.sh", root / "hook.sh")],
                          make_zip=True, package_rel="P.md")
    assert os.access(out / "hook.sh", os.X_OK)
    with zipfile.ZipFile(res["zip"]) as zf:
        assert (zf.getinfo("bundle/hook.sh").external_attr >> 16) & 0o111


def test_planted_secret_aborts_and_writes_nothing(tmp_path):
    root, _ = _repo(tmp_path, {"PACKAGE.md": "# p\n",
                               "notes.md": "fine\nfine\n" + FAKE_SECRETS["connection-url-with-password"] + "\n"})
    out = tmp_path / "bundle"
    with pytest.raises(RB.SecretFound) as ei:
        RB.build_bundle(out, [RB.Entry("PACKAGE.md", root / "PACKAGE.md"),
                              RB.Entry("notes.md", root / "notes.md")],
                        make_zip=True, package_rel="PACKAGE.md")
    assert ei.value.hits == [(str(root / "notes.md"), 3, "connection-url-with-password")]
    assert not out.exists()
    assert not out.with_name("bundle.zip").exists()


def test_superseded_are_named_in_manifest_but_not_copied(tmp_path):
    root, head = _repo(tmp_path, {"P.md": "p\n", "old/PLAN_v1_0.md": "old\n"})
    out = tmp_path / "b"
    RB.build_bundle(out, [RB.Entry("P.md", root / "P.md")],
                    superseded=[RB.Entry("old/PLAN_v1_0.md", root / "old/PLAN_v1_0.md")],
                    package_rel="P.md")
    assert not (out / "old").exists()
    text = (out / "MANIFEST.txt").read_text(encoding="utf-8")
    assert "NOT-INCLUDED:old/PLAN_v1_0.md" in text
    assert "old/PLAN_v1_0.md" not in _manifest_rows(out)


def test_zip_mirrors_the_folder(tmp_path):
    root, _ = _repo(tmp_path, {"P.md": "p\n", "a/b.txt": "b\n"})
    out = tmp_path / "bundle"
    res = RB.build_bundle(out, [RB.Entry("P.md", root / "P.md"), RB.Entry("a/b.txt", root / "a/b.txt")],
                          make_zip=True, package_rel="P.md")
    with zipfile.ZipFile(res["zip"]) as zf:
        names = set(zf.namelist())
        assert names == {"bundle/P.md", "bundle/a/b.txt", "bundle/MANIFEST.txt", "bundle/README_FIRST.md"}
        assert zf.read("bundle/a/b.txt") == b"b\n"


def test_refuses_existing_output_unless_forced(tmp_path):
    root, _ = _repo(tmp_path, {"P.md": "p\n"})
    out = tmp_path / "bundle"
    out.mkdir()
    (out / "stale.txt").write_text("old", encoding="utf-8")
    entries = [RB.Entry("P.md", root / "P.md")]
    with pytest.raises(RB.BundleError):
        RB.build_bundle(out, entries, package_rel="P.md")
    RB.build_bundle(out, entries, package_rel="P.md", force=True)
    assert not (out / "stale.txt").exists() and (out / "P.md").exists()


def test_refuses_missing_source_collision_and_absent_package(tmp_path):
    root, _ = _repo(tmp_path, {"P.md": "p\n", "Q.md": "q\n"})
    with pytest.raises(RB.BundleError, match="missing"):
        RB.build_bundle(tmp_path / "b1", [RB.Entry("P.md", root / "P.md"),
                                          RB.Entry("X.md", root / "X.md")], package_rel="P.md")
    with pytest.raises(RB.BundleError, match="collision"):
        RB.build_bundle(tmp_path / "b2", [RB.Entry("P.md", root / "P.md"),
                                          RB.Entry("P.md", root / "Q.md")], package_rel="P.md")
    with pytest.raises(RB.BundleError, match="review package"):
        RB.build_bundle(tmp_path / "b3", [RB.Entry("Q.md", root / "Q.md")], package_rel="P.md")
    assert not any((tmp_path / n).exists() for n in ("b1", "b2", "b3"))


# ---------------------------------------------------------------------------------------------
# Default contents and the CLI, over a fake set of roots
# ---------------------------------------------------------------------------------------------

def _fake_roots(tmp_path, secret_in=None):
    plan, nik, mad, home = (tmp_path / n for n in ("plan", "nikasha", "madhav", "home"))
    b = RB.SUVARNA_BRIEFS
    files = {plan: [RB.PACKAGE_REL] + [f"{b}/{n}" for n in (
        "SUVARNA_CAMPAIGN_PLAN_v1_5.md", "NATIVE_SETUP_v1_0.md", "SUVARNA_CAMPAIGN_PLAN_v1_4.md",
        "SUVARNA_AUTONOMY_CHARTER_v1_0.md",
        "SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md", "SUVARNA_RUNBOOK_v1_0.md",
        "D6_SUVARNA_READER_RUNBOOK_v1_0.md", "SUVARNA_L3_FOCUS_FAMILIES_v1_0.md",
        "SUVARNA_DOCUMENT_MAP_v1_0.md", "SUVARNA_CAMPAIGN_PLAN_v1_3.md",
        "tracks/TRACK_E.md", "roles/ROLE_X.md", "prompts/P.md", "runtime/settings.template.json",
        "reviews/R.md", "l3_recon/G.md")] + [
        "00_ARCHITECTURE/control/suvarna/plan_model.json",
        f"{RB.TRACKER_REL}/__init__.py", f"{RB.TRACKER_REL}/tests/test_x.py",
        f"{RB.TRACKER_REL}/__pycache__/x.cpython-312.pyc", f"{RB.TRACKER_REL}/stray.pyc",
        "platform/scripts/suvarna-reader-bootstrap.ts"],
        nik: ["00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md",
              "00_ARCHITECTURE/briefs/nirmana/NIKASHA_IMPLEMENTATION_PLAN_v1_0.md"],
        mad: ["CLAUDE.md"],
        home: ["run/DECISIONS.jsonl"]}
    for root, rels in files.items():
        for rel in rels:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"content of {rel}\n", encoding="utf-8")
    if secret_in:
        (plan / secret_in).write_text("ok\n" + FAKE_SECRETS["private-key-header"] + "\n", encoding="utf-8")
    return plan, nik, mad, home


def _cli_args(tmp_path, roots, *extra):
    plan, nik, mad, home = roots
    return ["--out", str(tmp_path / "out"), "--plan-root", str(plan), "--nikasha-root", str(nik),
            "--madhav-root", str(mad), "--home", str(home), *extra]


def test_cli_builds_default_contents_without_caches(tmp_path, capsys):
    roots = _fake_roots(tmp_path)
    assert RB.main(_cli_args(tmp_path, roots, "--zip")) == 0
    out = tmp_path / "out"
    rows = _manifest_rows(out)
    assert RB.PACKAGE_REL in rows
    assert "run/DECISIONS.jsonl" in rows and "CLAUDE.md" in rows
    assert "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md" in rows
    assert f"{RB.TRACKER_REL}/tests/test_x.py" in rows
    assert not any("__pycache__" in r or r.endswith(".pyc") for r in rows)
    assert f"{RB.SUVARNA_BRIEFS}/SUVARNA_CAMPAIGN_PLAN_v1_3.md" not in rows
    assert f"NOT-INCLUDED:{RB.SUVARNA_BRIEFS}/SUVARNA_CAMPAIGN_PLAN_v1_3.md" in \
        (out / "MANIFEST.txt").read_text(encoding="utf-8")
    assert (tmp_path / "out.zip").is_file()


def test_cli_planted_secret_exits_3_listing_file_and_line(tmp_path, capsys):
    roots = _fake_roots(tmp_path, secret_in=f"{RB.SUVARNA_BRIEFS}/roles/ROLE_X.md")
    assert RB.main(_cli_args(tmp_path, roots, "--zip")) == 3
    err = capsys.readouterr().err
    assert f"{RB.SUVARNA_BRIEFS}/roles/ROLE_X.md:2: private-key-header" in err
    assert not (tmp_path / "out").exists() and not (tmp_path / "out.zip").exists()


def test_cli_missing_source_exits_2(tmp_path, capsys):
    roots = _fake_roots(tmp_path)
    (roots[3] / "run/DECISIONS.jsonl").unlink()
    assert RB.main(_cli_args(tmp_path, roots)) == 2
    assert "DECISIONS.jsonl" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()
