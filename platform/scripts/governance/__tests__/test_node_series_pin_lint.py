"""test_node_series_pin_lint.py: check_node_series_pin.py (the reader-pin lint for the ephemeris_daily node series, with a RATCHET).

This is how the lint runs in CI WITHOUT a workflow edit: the existing "Governance Tool Tests (pytest)" step runs
`python -m pytest platform/scripts/governance/__tests__`, and this module runs the lint's self-test, the real repo scan against the
committed baseline (the ratchet), the baseline's own invariants, and a mutation proof (each detector neutered in turn must turn
the self-test red). A new unpinned reader of ephemeris_daily therefore fails the existing step.

Run:  python -m pytest platform/scripts/governance/__tests__/test_node_series_pin_lint.py -v
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
GOV = HERE.parent
REPO = GOV.parent.parent.parent
FIX = GOV / "node_series_pin_fixtures"

_spec = importlib.util.spec_from_file_location("check_node_series_pin", GOV / "check_node_series_pin.py")
lint = importlib.util.module_from_spec(_spec)
sys.modules["check_node_series_pin"] = lint
_spec.loader.exec_module(lint)


def _read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


def _lang(p: pathlib.Path) -> str:
    return {".py": "py", ".ts": "ts", ".sql": "sql"}[p.suffix]


# ------------------------------------------------------------------------------------------- fixtures, exactly
FAIL_EXPECT = {                      # fixture -> number of UNPINNED reads the scanner must report
    "unpinned_query.py": 1, "unpinned_table_constant.py": 1, "join_and_bad_marker.py": 2,
    "unpinned_mixed_body.py": 1, "unpinned_template.ts": 1, "unpinned_concat.ts": 1, "unpinned.sql": 1,
}
PASS_READS = {                       # fixture -> number of reads the scanner must SEE (all pinned/exempt); 0 = no read at all
    "pinned_predicate_token.py": 1, "explicit_node_mode.py": 4, "literal_non_node_body.py": 4, "documented_exemption.py": 2,
    "not_a_read.py": 0, "pinned_template.ts": 3, "pinned.sql": 3,
}


@pytest.mark.parametrize("name,n", sorted(FAIL_EXPECT.items()))
def test_fail_fixtures_report_exactly_their_unpinned_reads(name, n):
    p = FIX / "fail" / name
    sites = lint.scan_text(_read(p), p.name, _lang(p))
    assert len(lint.unpinned(sites)) == n, [(s.line, s.pinned, s.reason) for s in sites]


@pytest.mark.parametrize("name,n", sorted(PASS_READS.items()))
def test_pass_fixtures_see_their_reads_and_report_none_unpinned(name, n):
    p = FIX / "pass" / name
    sites = lint.scan_text(_read(p), p.name, _lang(p))
    assert len(sites) == n, [(s.line, s.reason) for s in sites]          # a scanner that sees nothing would also be "clean"
    assert not lint.unpinned(sites), [(s.line, s.reason) for s in lint.unpinned(sites)]


def test_every_fixture_is_accounted_for():
    on_disk = {("fail", p.name) for p in (FIX / "fail").iterdir() if p.suffix in (".py", ".ts", ".sql")} | \
              {("pass", p.name) for p in (FIX / "pass").iterdir() if p.suffix in (".py", ".ts", ".sql")}
    assert on_disk == {("fail", n) for n in FAIL_EXPECT} | {("pass", n) for n in PASS_READS}


def test_invalid_marker_reasons_are_reported():
    sites = lint.scan_text(_read(FIX / "fail" / "join_and_bad_marker.py"), "x.py", "py")
    assert any("invalid node-agnostic marker" in s.reason for s in sites)
    assert lint.classify("SELECT 1 FROM ephemeris_daily", "# node-agnostic: short")[0] is False
    assert lint.classify("SELECT 1 FROM ephemeris_daily", "# node-agnostic: this reader also takes Ketu rows")[0] is False
    assert lint.classify("SELECT 1 FROM ephemeris_daily", "# node-agnostic: seven classical grahas only")[0] is True


def test_writers_and_comments_and_docstrings_are_not_reads():
    assert lint.scan_text('X = "INSERT INTO ephemeris_daily (a) VALUES (1)"\n', "x.py", "py") == []
    assert lint.scan_text("# SELECT a FROM ephemeris_daily\n", "x.py", "py") == []
    assert lint.scan_text('def f():\n    """SELECT a FROM ephemeris_daily"""\n    return 1\n', "x.py", "py") == []
    assert lint.scan_text("// SELECT a FROM ephemeris_daily\n", "x.ts", "ts") == []
    assert lint.scan_text("-- SELECT a FROM ephemeris_daily;\n", "x.sql", "sql") == []
    assert lint.scan_text('X = "DELETE FROM ephemeris_daily WHERE d = (SELECT 1)"\n', "x.py", "py") == []


# ------------------------------------------------------------------------------------------- self-test and the real repo
def test_self_test_passes():
    assert lint.run_self_test() == 0


def test_cli_self_test_and_repo_scan_pass():
    for args in (["--self-test"], []):
        r = subprocess.run([sys.executable, str(GOV / "check_node_series_pin.py"), *args], capture_output=True, text=True, cwd=REPO)
        assert r.returncode == 0, r.stdout + r.stderr


def test_the_real_repo_passes_the_ratchet_against_the_committed_baseline():
    sites = lint.scan_repo(REPO)
    baseline = lint.load_baseline()
    errs = lint.ratchet(sites, baseline, lint.RATCHET_CEILING_TOTAL)
    assert not errs, "\n".join(errs)
    assert len(sites) > 40 and len(lint.unpinned(sites)) == lint.RATCHET_CEILING_TOTAL     # the scanner is not blind


def test_pravaha_readers_are_pinned_and_seen():
    sites = lint.scan_repo(REPO)
    seen = {s.file.rsplit("/", 1)[-1] for s in sites if s.pinned and s.reason == "NODE_SERIES_PREDICATE"}
    assert {"db_source.py", "v2_ephemeris_coverage.py", "v4_transition_sizing.py", "writer.py"} <= seen


def test_baseline_invariants():
    b = lint.load_baseline()
    keys = [(e["file"], e["anchor"]) for e in b["entries"]]
    assert len(keys) == len(set(keys))
    assert all(e["note"].strip() and isinstance(e["count"], int) and e["count"] >= 1 for e in b["entries"])
    assert sum(e["count"] for e in b["entries"]) == lint.RATCHET_CEILING_TOTAL
    assert not ({f"{e['file']}::{e['anchor']}" for e in b["entries"]} & {f"{r['file']}::{r['anchor']}" for r in b["retired"]})
    for e in b["entries"]:
        assert (REPO / e["file"]).is_file(), e["file"]


# ------------------------------------------------------------------------------------------- the ratchet, on synthetic trees
def _mini_repo(tmp_path, files: dict):
    root = tmp_path / "repo"
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


UNPINNED = 'def read(c):\n    return c.execute("SELECT date FROM ephemeris_daily WHERE body = %s", [1])\n'
PINNED = 'def read(c):\n    return c.execute("SELECT date FROM ephemeris_daily WHERE body = %s AND node_mode = \'true\'", [1])\n'
OTHER = 'def other(c):\n    return c.execute("SELECT date FROM ephemeris_daily")\n'
F = "platform/python-sidecar/services/x/reader.py"
G = "platform/python-sidecar/services/y/other.py"


def _bl(*entries, retired=()):
    return {"entries": [{"file": f, "anchor": a, "count": n, "note": "n"} for f, a, n in entries],
            "retired": [{"file": f, "anchor": a} for f, a in retired]}


def test_ratchet_clean_when_the_baseline_matches(tmp_path):
    root = _mini_repo(tmp_path, {F: UNPINNED})
    assert lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1)), 1) == []


def test_r1_a_new_unpinned_reader_fails_and_says_do_not_baseline_it(tmp_path):
    root = _mini_repo(tmp_path, {F: UNPINNED, G: OTHER})
    errs = lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1)), 1)
    assert len(errs) == 1 and errs[0].startswith("R1 NEW") and "other" in errs[0] and "Do NOT add it to the baseline" in errs[0]


def test_r1_a_second_unpinned_reader_under_the_same_anchor_fails(tmp_path):
    root = _mini_repo(tmp_path, {F: UNPINNED + '    c.execute("SELECT 1 FROM ephemeris_daily")\n'})
    errs = lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1)), 1)
    assert any(e.startswith("R1 NEW") and "baseline allows 1" in e for e in errs)


def test_r2_a_fixed_reader_must_shrink_the_baseline(tmp_path):
    root = _mini_repo(tmp_path, {F: PINNED})
    errs = lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1)), 1)
    assert any(e.startswith("R2 STALE") for e in errs)
    assert lint.ratchet(lint.scan_repo(root), _bl(retired=[(F, "read")]), 0) == []        # the honest shrink


def test_r3_a_retired_reader_may_not_come_back(tmp_path):
    root = _mini_repo(tmp_path, {F: UNPINNED})
    errs = lint.ratchet(lint.scan_repo(root), _bl(retired=[(F, "read")]), 0)
    assert any(e.startswith("R3 RETIRED") for e in errs)


def test_r4_the_ceiling_must_equal_the_baseline_total(tmp_path):
    root = _mini_repo(tmp_path, {F: UNPINNED})
    assert any(e.startswith("R4 CEILING") for e in lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1)), 2))   # raised
    assert any(e.startswith("R4 CEILING") for e in lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1)), 0))   # not lowered after a fix


def test_r5_shape_errors(tmp_path):
    root = _mini_repo(tmp_path, {F: UNPINNED})
    bad = _bl((F, "read", 1))
    bad["entries"][0]["note"] = " "
    assert any(e.startswith("R5 SHAPE") for e in lint.ratchet(lint.scan_repo(root), bad, 1))
    dup = _bl((F, "read", 1), (F, "read", 1))
    assert any("duplicate baseline key" in e for e in lint.ratchet(lint.scan_repo(root), dup, 2))
    both = _bl((F, "read", 1), retired=[(F, "read")])
    assert any("both a live baseline entry and retired" in e for e in lint.ratchet(lint.scan_repo(root), both, 1))


def test_a_pin_added_to_a_baselined_reader_is_the_only_way_down_and_a_move_is_not_free(tmp_path):
    """Reformatting the SQL or moving the line does not change the key (file, anchor); renaming the function does."""
    reformatted = 'def read(c):\n    return c.execute("""\n        SELECT\n          date\n        FROM ephemeris_daily\n        WHERE body = %s\n    """, [1])\n'
    root = _mini_repo(tmp_path, {F: "\n\n" + reformatted})
    assert lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1)), 1) == []
    root2 = _mini_repo(tmp_path / "b", {F: UNPINNED.replace("def read", "def read_renamed")})
    assert lint.ratchet(lint.scan_repo(root2), _bl((F, "read", 1)), 1) != []


def test_against_ref_blocks_growth_and_skips_when_the_ref_is_absent(tmp_path):
    repo = tmp_path / "g"
    (repo / "platform/scripts/governance").mkdir(parents=True)
    bl_path = repo / lint.BASELINE_REL

    def git(*a):
        return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=repo, capture_output=True, text=True)

    if git("init", "-q").returncode != 0:
        pytest.skip("git unavailable")
    old = _bl((F, "read", 2), (G, "other", 1))
    bl_path.write_text(json.dumps(old))
    git("add", "-A")
    git("commit", "-q", "-m", "base")
    ref = git("rev-parse", "HEAD").stdout.strip()
    assert lint.against_ref(old, ref, repo)[0] == []
    assert lint.against_ref(_bl((F, "read", 1)), ref, repo)[0] == []                                   # shrink is fine
    errs = lint.against_ref(_bl((F, "read", 3), (G, "other", 1)), ref, repo)[0]
    assert errs and "rose 2 -> 3" in errs[0]
    errs = lint.against_ref(_bl((F, "read", 2), (G, "other", 1), ("platform/new.py", "x", 1)), ref, repo)[0]
    assert errs and "not in" in errs[0]
    errs, note = lint.against_ref(old, "no-such-ref", repo)
    assert errs == [] and note.startswith("skipped")


def test_against_origin_main_when_it_is_available():
    """On a full clone the committed baseline may not be larger than origin/main's; on a shallow CI checkout this is skipped (stated)."""
    errs, note = lint.against_ref(lint.load_baseline(), "origin/main")
    assert errs == [], errs


# ------------------------------------------------------------------------------------------- mutation proof
def _red(monkeypatch, attr, new):
    monkeypatch.setattr(lint, attr, new)
    return lint.run_self_test() != 0


def test_mutation_classify_always_pinned_is_caught(monkeypatch):
    assert _red(monkeypatch, "classify", lambda *a, **k: (True, "mutated"))


def test_mutation_scanner_blind_to_every_read_is_caught(monkeypatch):
    import re
    monkeypatch.setattr(lint, "read_re_for", lambda text: re.compile(r"(?!x)x"))
    assert lint.run_self_test() != 0


@pytest.mark.parametrize("attr,new", [
    ("PIN_TOKEN_RE", None), ("MARKER_RE", None), ("LIMIT0_RE", None), ("ALIAS_DEF_RE", None),
], ids=["pin-token", "marker", "limit0", "table-alias-constant"])
def test_mutation_neutered_regex_is_caught(monkeypatch, attr, new):
    import re
    never = re.compile(r"(?!x)x")
    monkeypatch.setattr(lint, attr, never)
    assert lint.run_self_test() != 0, f"neutering {attr} was not detected by the self-test"


def test_mutation_node_mode_predicates_removed_is_caught(monkeypatch):
    assert _red(monkeypatch, "PIN_PRED_RES", [])


def test_mutation_body_literal_proof_removed_is_caught(monkeypatch):
    assert _red(monkeypatch, "_body_literals", lambda stmt: False)


def test_mutation_docstring_skipping_removed_is_caught(monkeypatch):
    assert _red(monkeypatch, "_is_docstring", lambda text, start: False)


def test_mutation_delete_from_exclusion_removed_is_caught(monkeypatch):
    import re
    assert _red(monkeypatch, "DELETE_FROM_RE", re.compile(r"(?!x)x"))


def test_mutation_adjacent_literal_merging_removed_is_caught(monkeypatch):
    orig = lint._lex_literals

    def no_merge(text, lang):
        out = []
        i, n = 0, len(text)
        # re-lex without merging: each quoted string is its own literal
        import re
        for m in re.finditer(r'"[^"\n]*"|\'[^\'\n]*\'|`[^`]*`|"""[\s\S]*?"""', text):
            out.append((m.start(), m.end(), m.group(0), "str"))
        return out

    monkeypatch.setattr(lint, "_lex_literals", no_merge)
    assert lint.run_self_test() != 0


@pytest.mark.parametrize("prefix", ["R1", "R2", "R3", "R4", "R5"])
def test_mutation_each_ratchet_rule_neutered_is_caught(monkeypatch, prefix):
    real = lint.ratchet
    monkeypatch.setattr(lint, "ratchet", lambda *a, **k: [e for e in real(*a, **k) if not e.startswith(prefix)])
    sub = subprocess.run  # noqa: F841 (documenting intent: the in-process self-test is the detector)
    if prefix in ("R1", "R2", "R3", "R4"):
        assert lint.run_self_test() != 0, f"neutering {prefix} was not detected"
    else:                                         # R5 is exercised by the pytest cases above and the 'no note' self-test case
        assert lint.run_self_test() != 0


def test_mutation_ratchet_that_ignores_the_baseline_is_caught_by_the_real_repo_test(monkeypatch):
    """If the ratchet were a no-op the 'real repo passes' test would still pass: so the SYNTHETIC tests above must be the ones
    that fail. Prove it: with a no-op ratchet, the R1 synthetic case stops reporting."""
    monkeypatch.setattr(lint, "ratchet", lambda *a, **k: [])
    assert lint.ratchet([lint.Site("a.py", 1, "f", "x", False, "r")], _bl(), 0) == []       # the mutation really neuters it
    assert lint.run_self_test() != 0                                                           # ... and the self-test notices
