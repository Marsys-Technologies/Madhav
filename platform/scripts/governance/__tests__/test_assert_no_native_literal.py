"""Self-test of the native-literal ratchet in assert_no_native_literal.sh (SS N-380 PR-S5).

The gate has two jobs, both proved here against synthetic trees (the real repo is only run once, at the end):
  1. it FAILS on a file that carries a native birth/identity token that is not allowlisted, and PASSES on a clean tree;
  2. it is a ratchet: an allowlist entry whose file no longer carries a token (or no longer exists) is reported STALE and
     fails the gate, so the allowlist can only shrink.

Every token below is built from fragments at run time, so this file never matches the gate it tests.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
GATE = HERE.parent / "assert_no_native_literal.sh"
REPO = HERE.parents[3]

# Tokens (fragments joined at run time)
NAME = "Abhi" + "sek"
SURNAME = "Moh" + "anty"
DOB = "1984" + "-02-05"
CLOCK = "10" + ":43"
PHANTOM = "362f9f17" + "-95a5-490b-a5a7-027d3e0efda0"
ANCHOR = "TITHI_" + "BIRTH"
SECOND_CHART_OWNER = "Abhi" + "nandan"


def run_gate(tmp_path: Path, files: dict[str, str], allowlist: str = "", retrieval: dict[str, str] | None = None):
    scripts = tmp_path / "scripts"
    for rel, body in files.items():
        p = scripts / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    retr = tmp_path / "retrieval"
    retr.mkdir(exist_ok=True)
    for rel, body in (retrieval or {}).items():
        (retr / rel).write_text(body)
    al = tmp_path / "allowlist.txt"
    al.write_text(allowlist)
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "G4_SCRIPTS_DIR": str(scripts), "G4_SCRIPTS_ALLOWLIST": str(al), "G4_RETRIEVAL_DIR": str(retr)}
    return subprocess.run(["bash", str(GATE)], capture_output=True, text=True, env=env, timeout=60)


CLEAN = {"a.py": "print('hello')\nCHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'\n", "sub/b.ts": "export const x = 1\n"}


def test_clean_tree_passes(tmp_path):
    r = run_gate(tmp_path, CLEAN)
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize(
    "label,line",
    [
        ("name", f"# owner: {NAME}"),
        ("name-slug", f"native_id = '{NAME.lower()}_{SURNAME.lower()}'"),
        ("name-const", f"const {NAME.upper()}_CHART = 'x'"),
        ("surname", f"# the {SURNAME} family"),
        ("dob", f"birth = '{DOB}'"),
        ("birth-time", f"born {DOB[:4]}-01-01 {CLOCK} IST"),
        ("birth-time-offset", f"x = 'T{CLOCK}:00+05:30'"),
        ("phantom", f"CHART_ID={PHANTOM}"),
        ("anchor", f"('{ANCHOR}', 'name')"),
    ],
)
def test_synthetic_offending_file_fails_and_names_the_file(tmp_path, label, line):
    r = run_gate(tmp_path, {**CLEAN, "offender.py": line + "\n"})
    assert r.returncode == 1, (label, r.stdout, r.stderr)
    assert "offender.py:1" in r.stderr and "not allowlisted" in r.stderr, r.stderr
    assert "a.py" not in r.stderr  # the clean files are not blamed


def test_second_chart_owner_line_is_exempt_for_the_surname_only(tmp_path):
    # the consented second chart's owner shares the family name: a line naming that owner is not a hit...
    ok = run_gate(tmp_path, {**CLEAN, "ok.py": f"# {SECOND_CHART_OWNER} {SURNAME} (consented test chart)\n"})
    assert ok.returncode == 0, ok.stderr
    # ...but the exemption does not shield the given name or the birth date
    bad = run_gate(tmp_path, {**CLEAN, "bad.py": f"# {SECOND_CHART_OWNER} {SURNAME} and {NAME}\n"})
    assert bad.returncode == 1 and "bad.py:1" in bad.stderr


def test_clock_time_without_a_birth_context_is_not_a_hit(tmp_path):
    r = run_gate(tmp_path, {**CLEAN, "t.py": f"cron = 'runs at {CLOCK} daily'\n"})
    assert r.returncode == 0, r.stderr


def test_bare_phantom_prefix_in_a_refusal_guard_is_not_a_hit(tmp_path):
    r = run_gate(tmp_path, {**CLEAN, "guard.py": "PHANTOM_PREFIX = '362f9f17'  # refused\n"})
    assert r.returncode == 0, r.stderr


def test_allowlisted_offender_passes(tmp_path):
    r = run_gate(tmp_path, {**CLEAN, "offender.py": f"x = '{DOB}'\n"}, allowlist="offender.py\toracle: reason text\n")
    assert r.returncode == 0, r.stderr


def test_allowlist_covers_only_the_listed_file(tmp_path):
    r = run_gate(
        tmp_path,
        {**CLEAN, "listed.py": f"x = '{DOB}'\n", "other.py": f"y = '{DOB}'\n"},
        allowlist="listed.py\treason\n",
    )
    assert r.returncode == 1 and "other.py:1" in r.stderr and "listed.py:1" not in r.stderr


def test_stale_allowlist_entry_is_reported_and_fails_the_ratchet(tmp_path):
    # the entry names a file that exists but no longer carries any token
    r = run_gate(tmp_path, CLEAN, allowlist="a.py\twas an oracle, now clean\n")
    assert r.returncode == 1, r.stdout
    assert "STALE" in r.stderr and "a.py" in r.stderr


def test_allowlist_entry_for_a_deleted_file_is_stale(tmp_path):
    r = run_gate(tmp_path, CLEAN, allowlist="gone/deleted.py\tfile removed\n")
    assert r.returncode == 1 and "STALE" in r.stderr and "gone/deleted.py" in r.stderr


def test_malformed_and_duplicate_allowlist_entries_fail(tmp_path):
    noreason = run_gate(tmp_path, {**CLEAN, "o.py": f"x = '{DOB}'\n"}, allowlist="o.py\n")
    assert noreason.returncode == 1 and "no '<path><TAB><reason>'" in noreason.stderr
    dup = run_gate(tmp_path, {**CLEAN, "o.py": f"x = '{DOB}'\n"}, allowlist="o.py\tr1\no.py\tr2\n")
    assert dup.returncode == 1 and "duplicates" in dup.stderr


def test_comments_and_blank_lines_in_the_allowlist_are_ignored(tmp_path):
    r = run_gate(tmp_path, {**CLEAN, "o.py": f"x = '{DOB}'\n"}, allowlist="# header\n\no.py\treason\n# trailing\n")
    assert r.returncode == 0, r.stderr


def test_the_allowlist_file_itself_is_never_scanned(tmp_path):
    # allowlist entries may name files whose names contain a token; the gate must not flag the allowlist for it
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "native_literal_allowlist.txt").write_text(f"_archived/seed-{NAME.lower()}.ts\treason\n")
    (scripts / "a.py").write_text("pass\n")
    (tmp_path / "retrieval").mkdir()
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "G4_SCRIPTS_DIR": str(scripts),
           "G4_SCRIPTS_ALLOWLIST": str(scripts / "native_literal_allowlist.txt"), "G4_RETRIEVAL_DIR": str(tmp_path / "retrieval")}
    r = subprocess.run(["bash", str(GATE)], capture_output=True, text=True, env=env, timeout=60)
    # the only reason to fail is the stale entry (the named file does not exist), never a hit inside the allowlist
    assert "not allowlisted" not in r.stderr, r.stderr
    assert r.returncode == 1 and "STALE" in r.stderr


def test_part1_retrieval_identifier_check_still_fails(tmp_path):
    r = run_gate(tmp_path, CLEAN, retrieval={"prod.ts": "const NATIVE_CHART_ID = 'x'\n"})
    assert r.returncode == 1 and "NATIVE_CHART_ID/DEFAULT_CHART_ID" in r.stderr


def test_the_gate_script_and_allowlist_do_not_match_themselves():
    for f in (GATE, HERE / "test_assert_no_native_literal.py", GATE.parent / "native_literal_allowlist.txt"):
        text = f.read_text()
        for tok in (NAME, SURNAME, DOB, PHANTOM):
            if f.name == "native_literal_allowlist.txt":
                continue  # the allowlist is excluded from the scan by name; its file names may contain a token
            assert tok.lower() not in text.lower(), (f.name, tok)


def test_real_repo_is_green_and_the_real_allowlist_has_no_stale_entry():
    r = subprocess.run(["bash", str(GATE)], capture_output=True, text=True, cwd=REPO, timeout=120)
    assert r.returncode == 0, r.stderr
