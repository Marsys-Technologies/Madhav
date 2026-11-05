"""test_node_series_pin_lint.py: check_node_series_pin.py (the reader-pin lint for the ephemeris_daily node series, with a RATCHET).

This is how the lint runs in CI WITHOUT a workflow edit: the existing "Governance Tool Tests (pytest)" step runs
`python -m pytest platform/scripts/governance/__tests__`, and this module runs the lint's self-test, the real repo scan against the
committed baseline (the ratchet), the GROWTH GUARD against origin/main (fetched here under CI; a base that cannot be fetched under CI
is a FAILURE, not a skip), the independent review's scratch cases as permanent fixtures (`node_series_pin_fixtures/cases.py`), the
known blind spots as strict xfails, and a mutation proof (each rule mutated in the SOURCE turns the suite red).

Run:  python -m pytest platform/scripts/governance/__tests__/test_node_series_pin_lint.py -v
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import types

import pytest

HERE = pathlib.Path(__file__).resolve().parent
GOV = HERE.parent
REPO = GOV.parent.parent.parent
FIX = GOV / "node_series_pin_fixtures"
SCRIPT = GOV / "check_node_series_pin.py"


def _load(src: str, name: str = "check_node_series_pin") -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__file__ = str(SCRIPT)
    sys.modules[name] = mod
    exec(compile(src, str(SCRIPT), "exec"), mod.__dict__)
    return mod


SRC = SCRIPT.read_text(encoding="utf-8")
lint = _load(SRC)

_cs = importlib.util.spec_from_file_location("node_series_pin_cases", FIX / "cases.py")
_cases = importlib.util.module_from_spec(_cs)
_cs.loader.exec_module(_cases)
CASES = _cases.CASES

LANG = {".py": "py", ".ts": "ts", ".sql": "sql"}


def _read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------------- fixtures, exactly
FAIL_EXPECT = {                      # fixture -> number of UNPINNED reads the scanner must report
    "unpinned_query.py": 1, "unpinned_table_constant.py": 1, "join_and_bad_marker.py": 2, "unpinned_mixed_body.py": 1,
    "unpinned_group_by_node_mode.py": 1, "unpinned_limit_zero.py": 1,
    "unpinned_template.ts": 1, "unpinned_concat.ts": 1, "unpinned.sql": 1,
}
PASS_READS = {                       # fixture -> number of reads the scanner must SEE (all pinned/exempt); 0 = no read at all
    "pinned_predicate_token.py": 1, "explicit_node_mode.py": 3, "literal_non_node_body.py": 3, "documented_exemption.py": 2,
    "not_a_read.py": 0, "pinned_template.ts": 3, "pinned.sql": 3,
}


@pytest.mark.parametrize("name,n", sorted(FAIL_EXPECT.items()))
def test_fail_fixtures_report_exactly_their_unpinned_reads(name, n):
    p = FIX / "fail" / name
    sites = lint.scan_text(_read(p), p.name, LANG[p.suffix])
    assert len(lint.unpinned(sites)) == n, [(s.line, s.pinned, s.reason) for s in sites]


@pytest.mark.parametrize("name,n", sorted(PASS_READS.items()))
def test_pass_fixtures_see_their_reads_and_report_none_unpinned(name, n):
    p = FIX / "pass" / name
    sites = lint.scan_text(_read(p), p.name, LANG[p.suffix])
    assert len(sites) == n, [(s.line, s.reason) for s in sites]          # a scanner that sees nothing would also be "clean"
    assert not lint.unpinned(sites), [(s.line, s.reason) for s in lint.unpinned(sites)]


def test_every_fixture_is_accounted_for():
    on_disk = {(k, p.name) for k in ("fail", "pass") for p in (FIX / k).iterdir() if p.suffix in LANG}
    assert on_disk == {("fail", n) for n in FAIL_EXPECT} | {("pass", n) for n in PASS_READS}


# ------------------------------------------------------------------------------------------- the review's cases, as permanent fixtures
BLIND_REASON = {
    "py '+' concat across 2 literals": "python + concatenation is not traced (known blind spot)",
    "py ' '.join list": "python \" \".join([...]) is not traced (known blind spot)",
    "ts supabase .from()": "query builders (Supabase .from) are not modelled (known blind spot)",
    "ts supabase .from template": "query builders (Supabase .from) are not modelled (known blind spot)",
    "py table via imported constant": "a table name imported from another file is not resolved (known blind spot)",
    "py sqlalchemy Table autoload": "SQLAlchemy Table(...) is not modelled (known blind spot)",
    'py "{}".format("ephemeris_daily")': ".format(\"ephemeris_daily\") is not modelled (known blind spot)",
    "py psycopg2 sql.SQL + Identifier": "sql.Identifier(...) is not modelled (known blind spot)",
}


def _case_params():
    out = []
    for name, lang, text, expect in CASES:
        marks = []
        if expect == "blind":
            marks = [pytest.mark.xfail(strict=True, reason=BLIND_REASON[name])]
        out.append(pytest.param(name, lang, text, expect, id=name, marks=marks))
    return out


def _flagged(mod, lang, text) -> bool:
    return bool(mod.unpinned(mod.scan_text(text, "x." + lang, lang)))


@pytest.mark.parametrize("name,lang,text,expect", _case_params())
def test_reviewer_and_revision_cases(name, lang, text, expect):
    # `blind` cases state the DESIRED verdict (flagged); today they are missed, so strict xfail: an improvement forces an update here
    want_flag = expect in ("flag", "blind")
    assert _flagged(lint, lang, text) == want_flag


def test_blind_spot_reasons_cover_every_blind_case():
    assert {c[0] for c in CASES if c[3] == "blind"} == set(BLIND_REASON)


def test_the_cases_cover_the_review_classes():
    names = " | ".join(c[0] for c in CASES)
    for needle in ("body IN ({placeholders})", "body = '{b}'", "body IN ('Sun', ${list})", "conditional pin", "conditional NODE_SERIES_PREDICATE",
                   "sql /* node_mode", "UNION", "UPDATE .. FROM", "DELETE ... USING", "l0.ephemeris_daily", "comma join", "schema interpolated",
                   "CASE WHEN body=Sun", "LIMIT 0 elsewhere", "marker belonging to previous function", "vacuous marker",
                   "comment ending with colon", "dict key colon"):
        assert needle in names, needle
    assert len(CASES) >= 100


# ------------------------------------------------------------------------------------------- positive-proof rules, spelled out
def test_invalid_marker_reasons_are_reported():
    sites = lint.scan_text(_read(FIX / "fail" / "join_and_bad_marker.py"), "x.py", "py")
    assert any("invalid node-agnostic marker" in s.reason for s in sites)
    ok = lint._valid_marker
    assert ok(["# node-agnostic: nope: some fine text here"])[0] is False
    assert ok(["# node-agnostic: count_only_table_level: short"])[0] is False
    assert ok(["# node-agnostic: schema_introspection: probe that returns Ketu rows"])[0] is False
    assert ok(["# node-agnostic: schema_introspection: probe that never returns rows"]) == (True, "schema_introspection")
    assert ok(["# nothing here"]) == (None, "")


def test_the_closed_set_of_reason_codes_is_documented_in_the_docstring():
    for code in lint.MARKER_CODES:
        assert code in (lint.__doc__ or SRC)


def test_variable_body_filters_are_never_a_literal_non_node_proof():
    for text in ('q = f"SELECT * FROM ephemeris_daily WHERE body IN ({ph})"\n',
                 "q = f\"SELECT * FROM ephemeris_daily WHERE body = '{b}'\"\n",
                 "q = f\"SELECT * FROM ephemeris_daily WHERE body IN ('Sun', {extra})\"\n",
                 'q = "SELECT * FROM ephemeris_daily WHERE body IN (%s, %s)"\n',
                 'q = "SELECT * FROM ephemeris_daily WHERE body = %(b)s"\n',
                 'q = "SELECT * FROM ephemeris_daily WHERE body = ANY(%s)"\n'):
        assert _flagged(lint, "py", text), text
    assert _flagged(lint, "ts", "const q = `SELECT * FROM ephemeris_daily WHERE body = '${b}'`;\n")
    assert _flagged(lint, "ts", "const q = `SELECT * FROM ephemeris_daily WHERE body IN ('Sun', ${extra})`;\n")


def test_comments_never_satisfy_a_pin():
    for lang, text in (("sql", "SELECT date FROM ephemeris_daily /* node_mode = true */ WHERE date > 1;\n"),
                       ("sql", "SELECT date FROM ephemeris_daily -- node_mode = true\n WHERE date > 1;\n"),
                       ("py", 'q = """SELECT date FROM ephemeris_daily /* node_mode = true */"""\n'),
                       ("py", 'q = """SELECT date FROM ephemeris_daily\n -- TODO node_mode = true later\n"""\n'),
                       ("py", 'q = "SELECT * FROM ephemeris_daily -- NODE_SERIES_PREDICATE"\n'),
                       ("py", '# node_mode = true\nq = "SELECT * FROM ephemeris_daily"\n'),
                       ("ts", '// node_mode = true\nconst q = `SELECT * FROM ephemeris_daily`;\n')):
        assert _flagged(lint, lang, text), text


# ------------------------------------------------------------------------------------------- anchors
def _anchors(text, lang="py"):
    return [s.anchor for s in lint.scan_text(text, "x." + lang, lang)]


def test_anchor_is_the_enclosing_def_not_the_assignment_name():
    base = ['def read(c):\n    c.execute("SELECT 1 FROM ephemeris_daily")\n',
            'def read(c):\n    sql = "SELECT 1 FROM ephemeris_daily"\n    c.execute(sql)\n',
            'def read(c):\n    sql = (\n        "SELECT 1 FROM ephemeris_daily"\n    )\n    c.execute(sql)\n',
            'def read(c):\n    sql = """SELECT 1\n      FROM ephemeris_daily"""\n',
            'def read(c):\n    sql = (\n      """SELECT 1\n      FROM ephemeris_daily""")\n',
            'async def read(c):\n    await c.execute("SELECT 1 FROM ephemeris_daily")\n']
    for t in base:
        assert _anchors(t) == ["read"], t                       # a behaviour-preserving refactor does not change the key
    assert _anchors('class K:\n    def read(self,c):\n        c.execute("SELECT 1 FROM ephemeris_daily")\n') == ["K.read"]
    assert _anchors('def read(c):\n    def inner():\n        c.execute("SELECT 1 FROM ephemeris_daily")\n    inner()\n') == ["read.inner"]
    # generic local names no longer collide across functions
    assert _anchors('def a(c):\n    sql = "SELECT 1 FROM ephemeris_daily"\ndef b(c):\n    sql = "SELECT 2 FROM ephemeris_daily"\n') == ["a", "b"]
    # a module-level constant keeps its name (nothing else identifies it)
    assert _anchors('_SQL = """SELECT 1 FROM ephemeris_daily"""\n') == ["<module>._SQL"]
    assert _anchors('def f(\n    a: int,\n) -> int:\n    return c.execute("SELECT 1 FROM ephemeris_daily")\n') == ["f"]
    assert _anchors('export const getX = async (db) => {\n  return db.query(`SELECT 1 FROM ephemeris_daily`);\n};\n', "ts") == ["getX"]
    assert _anchors('class A {\n  async getX(db) {\n    return db.query(`SELECT 1 FROM ephemeris_daily`);\n  }\n}\n', "ts") == ["A.getX"]
    assert _anchors('export async function getX(db) {\n  const r = await db.query(`SELECT 1 FROM ephemeris_daily`);\n}\n', "ts") == ["getX"]


def test_fix_one_reader_add_another_in_the_same_file_is_not_hidden_by_a_generic_name(tmp_path):
    root = _mini_repo(tmp_path, {F: 'def a(c):\n    sql = "SELECT 1 FROM ephemeris_daily"\ndef b(c):\n    sql = "SELECT 2 FROM ephemeris_daily WHERE node_mode = \'true\'"\n'})
    # baseline says 'a' unpinned once; the author pinned a and added an unpinned b: counts per anchor catch it
    pinned_a = 'def a(c):\n    sql = "SELECT 1 FROM ephemeris_daily WHERE node_mode = \'true\'"\ndef b(c):\n    sql = "SELECT 2 FROM ephemeris_daily"\n'
    (root / F).write_text(pinned_a)
    errs = lint.ratchet(lint.scan_repo(root), _bl((F, "a", 1)), 1)
    assert any(e.startswith("R1 NEW") and "::b" in e for e in errs) and any(e.startswith("R2 STALE") and "::a" in e for e in errs)


# ------------------------------------------------------------------------------------------- self-test and the real repo
def test_self_test_passes():
    assert lint.run_self_test() == 0


def test_cli_self_test_and_repo_scan_pass():
    for args in (["--self-test"], []):
        r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=REPO)
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


def test_the_real_miss_v13_production_gate_is_seen_and_baselined():
    sites = lint.scan_repo(REPO)
    assert any(s.file.endswith("governance/v13_production_gate.py") and not s.pinned for s in sites)
    assert any(e["file"].endswith("v13_production_gate.py") for e in lint.load_baseline()["entries"])


def test_baseline_invariants():
    b = lint.load_baseline()
    keys = [(e["file"], e["anchor"]) for e in b["entries"]]
    assert len(keys) == len(set(keys))
    assert all(e["note"].strip() and e["owner"].strip() and isinstance(e["count"], int) and e["count"] >= 1 for e in b["entries"])
    assert sum(e["count"] for e in b["entries"]) == lint.RATCHET_CEILING_TOTAL
    assert not ({f"{e['file']}::{e['anchor']}" for e in b["entries"]} & {f"{r['file']}::{r['anchor']}" for r in b["retired"]})
    for e in b["entries"]:
        assert (REPO / e["file"]).is_file(), e["file"]


def test_scan_roots_cover_the_review_additions():
    g = " ".join(sum(lint.SCAN_GLOBS.values(), []))
    for needle in ("evals/", "infra/", "*.js", "*.mjs", "*.sh", "platform/scripts/", "scripts/**"):
        assert needle in g, needle


# ------------------------------------------------------------------------------------------- scan_repo exclusions
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


def test_tests_and_generated_trees_are_excluded_but_everything_else_is_scanned(tmp_path):
    root = _mini_repo(tmp_path, {
        "platform/python-sidecar/tests/test_x.py": UNPINNED, "platform/python-sidecar/services/tests/helper.py": UNPINNED,
        "platform/python-sidecar/services/test_y.py": UNPINNED, "platform/src/lib/__tests__/a.ts": "const q = `SELECT 1 FROM ephemeris_daily`;\n",
        "platform/src/generated/a.ts": "const q = `SELECT 1 FROM ephemeris_daily`;\n", "platform/src/lib/a.test.ts": "const q = `SELECT 1 FROM ephemeris_daily`;\n",
        "platform/src/lib/live.ts": "const q = `SELECT 1 FROM ephemeris_daily`;\n",
        "evals/runner.js": "const q = `SELECT 1 FROM ephemeris_daily`;\n", "infra/x/run.mjs": "const q = `SELECT 1 FROM ephemeris_daily`;\n",
        "infra/x/run.sh": 'psql -c "SELECT 1 FROM ephemeris_daily"\n', "scripts/x.py": UNPINNED,
        "platform/migrations/1999_x.sql": "SELECT 1 FROM ephemeris_daily;\n",
    })
    got = {s.file for s in lint.scan_repo(root)}
    assert got == {"platform/src/lib/live.ts", "evals/runner.js", "infra/x/run.mjs", "infra/x/run.sh", "scripts/x.py", "platform/migrations/1999_x.sql"}


# ------------------------------------------------------------------------------------------- the ratchet, on synthetic trees
def _bl(*entries, retired=()):
    return {"entries": [{"file": f, "anchor": a, "count": n, "note": "n", "owner": "o"} for f, a, n in entries],
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


def test_r2_a_fixed_reader_must_shrink_the_baseline_and_the_message_is_right_for_a_partial_shrink(tmp_path):
    root = _mini_repo(tmp_path, {F: PINNED})
    errs = lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1)), 1)
    assert any(e.startswith("R2 STALE") and "remove the entry, record the key under `retired`" in e for e in errs)
    assert lint.ratchet(lint.scan_repo(root), _bl(retired=[(F, "read")]), 0) == []        # the honest full shrink
    # partial shrink: one of two readers fixed: the message says LOWER THE COUNT, not "retire the key"; the lowered baseline passes
    two = _mini_repo(tmp_path / "t", {F: UNPINNED + '    c.execute("SELECT 1 FROM ephemeris_daily")\n'.replace("SELECT 1", "SELECT 2")})
    (two / F).write_text('def read(c):\n    c.execute("SELECT 1 FROM ephemeris_daily")\n    c.execute("SELECT 2 FROM ephemeris_daily WHERE node_mode = \'true\'")\n')
    errs = lint.ratchet(lint.scan_repo(two), _bl((F, "read", 2)), 2)
    msg = [e for e in errs if e.startswith("R2 STALE")]
    assert msg and "lower the entry's count to 1" in msg[0] and "do not retire a key that still has a reader" in msg[0]
    assert lint.ratchet(lint.scan_repo(two), _bl((F, "read", 1)), 1) == []


def test_r3_a_retired_reader_may_not_come_back(tmp_path):
    root = _mini_repo(tmp_path, {F: UNPINNED})
    assert any(e.startswith("R3 RETIRED") for e in lint.ratchet(lint.scan_repo(root), _bl(retired=[(F, "read")]), 0))


def test_r4_the_ceiling_must_equal_the_baseline_total(tmp_path):
    root = _mini_repo(tmp_path, {F: UNPINNED})
    assert any(e.startswith("R4 CEILING") for e in lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1)), 2))
    assert any(e.startswith("R4 CEILING") for e in lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1)), 0))


def test_r5_shape_errors(tmp_path):
    root = _mini_repo(tmp_path, {F: UNPINNED})
    for field in ("note", "owner"):
        bad = _bl((F, "read", 1))
        bad["entries"][0][field] = " "
        assert any(e.startswith("R5 SHAPE") for e in lint.ratchet(lint.scan_repo(root), bad, 1)), field
    assert any("duplicate baseline key" in e for e in lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1), (F, "read", 1)), 2))
    assert any("both a live baseline entry and retired" in e for e in lint.ratchet(lint.scan_repo(root), _bl((F, "read", 1), retired=[(F, "read")]), 1))


# ------------------------------------------------------------------------------------------- the growth guard (real git)
def _git_repo(tmp_path, baseline, ceiling_src="RATCHET_CEILING_TOTAL = 2\n", name="g"):
    repo = tmp_path / name
    (repo / "platform/scripts/governance").mkdir(parents=True)

    def git(*a, cwd=repo):
        return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "init.defaultBranch=main", *a], cwd=cwd, capture_output=True, text=True)

    if git("init", "-q").returncode != 0:
        pytest.skip("git unavailable")
    (repo / lint.BASELINE_REL).write_text(json.dumps(baseline))
    (repo / lint.SCRIPT_REL).write_text(ceiling_src)
    git("add", "-A")
    git("commit", "-q", "-m", "base")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    return repo, git


def test_growth_guard_blocks_new_keys_counts_totals_and_ceiling_but_allows_shrink(tmp_path):
    old = _bl((F, "read", 2), (G, "other", 1))
    repo, git = _git_repo(tmp_path, old, "RATCHET_CEILING_TOTAL = 3\n")
    ref = "origin/main"
    assert lint.against_ref(old, ref, repo, 3)[0] == []
    assert lint.against_ref(_bl((F, "read", 1)), ref, repo, 1)[0] == []                                 # shrink is fine
    errs = lint.against_ref(_bl((F, "read", 3), (G, "other", 1)), ref, repo, 4)[0]
    assert any("rose 2 -> 3" in e for e in errs) and any("RATCHET_CEILING_TOTAL 3 -> 4" in e for e in errs) and any("ceiling_raise_approved" in e for e in errs)
    errs = lint.against_ref(_bl((F, "read", 2), (G, "other", 1), ("platform/new.py", "x", 1)), ref, repo, 4)[0]
    assert any("not in" in e for e in errs)
    # the dodge the review found: a new reader + its baseline entry + a bumped ceiling in ONE commit passes ratchet() but not the guard
    grown = _bl((F, "read", 2), (G, "other", 1), ("platform/python-sidecar/z.py", "z", 1))
    assert lint.against_ref(grown, ref, repo, 4)[0]


def test_growth_guard_accepts_growth_only_with_a_new_explicit_approval_marker(tmp_path, capsys):
    old = _bl((F, "read", 1))
    repo, git = _git_repo(tmp_path, old, "RATCHET_CEILING_TOTAL = 1\n")
    grown = _bl((F, "read", 1), (G, "other", 1))
    assert lint.against_ref(grown, "origin/main", repo, 2)[0]
    grown["ceiling_raise_approved"] = "step-1 split of S1-S6 adds one wrapper reader until the legacy copy is deleted"
    errs, note = lint.against_ref(grown, "origin/main", repo, 2)
    assert errs == [] and "APPROVED" in note
    assert "CEILING_RAISE_APPROVED: step-1 split" in capsys.readouterr().out                           # the test output prints it
    # a stale approval (already present at the base) does not authorise a NEW raise
    old2 = dict(old, ceiling_raise_approved="earlier raise")
    repo2, _ = _git_repo(tmp_path, old2, "RATCHET_CEILING_TOTAL = 1\n", name="g2")
    again = _bl((F, "read", 1), (G, "other", 1))
    again["ceiling_raise_approved"] = "earlier raise"
    assert lint.against_ref(again, "origin/main", repo2, 2)[0]


def test_growth_guard_is_merge_base_aware_so_a_branch_behind_main_gets_no_false_grown(tmp_path):
    old = _bl((F, "read", 2), (G, "other", 1))
    repo, git = _git_repo(tmp_path, old, "RATCHET_CEILING_TOTAL = 3\n")
    git("checkout", "-q", "-b", "feature")
    git("checkout", "-q", "main")
    (repo / lint.BASELINE_REL).write_text(json.dumps(_bl((F, "read", 1))))                              # main shrinks after the branch point
    git("commit", "-q", "-am", "shrink on main")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    git("checkout", "-q", "feature")                                                                    # feature still has the OLD, larger baseline
    errs, note = lint.against_ref(old, "origin/main", repo, 3)
    assert errs == [] and "compared with" in note                                                       # compared with the merge-base, not main's tip


def test_growth_guard_initial_introduction_and_absent_ref(tmp_path):
    repo = tmp_path / "e"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], capture_output=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x"], cwd=repo, capture_output=True)
    subprocess.run(["git", "update-ref", "refs/remotes/origin/main", "HEAD"], cwd=repo, capture_output=True)
    errs, note = lint.against_ref(_bl((F, "read", 1)), "origin/main", repo, 1)
    assert errs == [] and note.startswith("initial introduction")
    errs, note = lint.against_ref(_bl((F, "read", 1)), "no-such-ref", repo, 1)
    assert errs == [] and note.startswith("skipped")


def test_growth_guard_fails_under_ci_when_the_base_cannot_be_fetched_and_skips_only_outside_ci(tmp_path):
    repo = tmp_path / "nofetch"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], capture_output=True)
    errs, note = lint.growth_guard(_bl(), 0, repo, "origin/main", in_ci=True)
    assert errs and "CANNOT RUN" in errs[0] and "do not skip" in errs[0]
    errs, note = lint.growth_guard(_bl(), 0, repo, "origin/main", in_ci=False)
    assert errs == [] and note.startswith("skipped")


def test_the_growth_guard_against_origin_main_runs_for_real():
    """Under CI (GITHUB_ACTIONS=true) this FETCHES origin/main itself (`git fetch --depth=1`) and FAILS if it cannot; locally it uses the
    ref if present. The baseline, any count, the total and RATCHET_CEILING_TOTAL may not exceed the base's without a NEW approval marker."""
    errs, note = lint.growth_guard(lint.load_baseline(), lint.RATCHET_CEILING_TOTAL, REPO)
    print("growth guard:", note)
    assert errs == [], errs
    if os.environ.get("GITHUB_ACTIONS") == "true":
        assert not note.startswith("skipped"), note


# ------------------------------------------------------------------------------------------- mutation proof (mutates the SOURCE)
def _extra_checks(mod) -> bool:
    """The detector for the mutation proof: self-test, every case, the fixtures, the anchors and a few marker/ratchet specifics."""
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        if mod.run_self_test() != 0:
            return False
    for name, lang, text, expect in CASES:
        if expect == "blind":
            continue
        if _flagged(mod, lang, text) != (expect == "flag"):
            return False
    for kind, table in (("fail", FAIL_EXPECT), ("pass", PASS_READS)):
        for n, cnt in table.items():
            p = FIX / kind / n
            sites = mod.scan_text(_read(p), p.name, LANG[p.suffix])
            if kind == "fail" and len(mod.unpinned(sites)) != cnt:
                return False
            if kind == "pass" and (len(sites) != cnt or mod.unpinned(sites)):
                return False
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = _mini_repo(pathlib.Path(td), {"platform/python-sidecar/tests/test_x.py": UNPINNED, "platform/python-sidecar/services/tests/h.py": UNPINNED,
                                             "platform/python-sidecar/services/live.py": UNPINNED})
        if {x.file for x in mod.scan_repo(root)} != {"platform/python-sidecar/services/live.py"}:
            return False
    an = mod.scan_text('def read(c):\n    sql = "SELECT 1 FROM ephemeris_daily"\n', "x.py", "py")
    if [s.anchor for s in an] != ["read"]:
        return False
    two = mod.scan_text('def a(c):\n    sql = "SELECT 1 FROM ephemeris_daily"\ndef b(c):\n    sql = "SELECT 2 FROM ephemeris_daily"\n', "x.py", "py")
    return [s.anchor for s in two] == ["a", "b"]


def test_the_detector_passes_on_the_unmutated_source():
    assert _extra_checks(_load(SRC, "cnsp_clean"))


MUTATIONS = [
    ("reverse '= node_mode' pattern removed (review: survived)", 'r".* (?:=|< >|! =) (?:\\w+ \\. )?NODE_MODE"', 'r"(?!x)x"'),
    ("/tests/ exclusion removed (review: survived)", '"/__tests__/", "/tests/", ', '"/__tests__/", '),
    ("FROM ONLY handling removed (review: survived)", 'x.up in ("ONLY", "LATERAL")', 'x.up in ("LATERAL",)'),
    ("interpolation counted as a literal body string", 'return t.type == "str" and _INTERP not in t.text', 'return t.type == "str"'),
    ("any interpolation accepted as the NODE_SERIES_PREDICATE", 'r"(?:\\w+\\.)*NODE_SERIES_PREDICATE"', 'r".*NODE_SERIES_PREDICATE.*"'),
    ("block comments no longer stripped", 'if k in ("lc", "bc"):', 'if k in ("lc",):'),
    ("OR conjunct accepted when ANY disjunct is safe", "return rs[0] if all(rs) else None", "return next((x for x in rs if x), None)"),
    ("AND group accepted only when ALL parts are safe", "        for p in ands:\n            r = _safe_seq(p, rel, single)\n            if r:\n                return r\n        return None",
     "        rs2 = [_safe_seq(p, rel, single) for p in ands]\n        return rs2[0] if all(rs2) else None"),
    ("table qualifier check disabled", "        return _unq(toks[idx - 2]).lower() in (rel.alias, TABLE)\n    return single", "        return True\n    return True"),
    ("docstring heuristic swallows everything", "def _is_docstring(text: str, start: int, end: int) -> bool:\n", "def _is_docstring(text: str, start: int, end: int) -> bool:\n    return True\n"),
    ("docstring heuristic never skips", "def _is_docstring(text: str, start: int, end: int) -> bool:\n", "def _is_docstring(text: str, start: int, end: int) -> bool:\n    return False\n"),
    ("marker reason code not checked", "if code not in MARKER_CODES:", "if False:"),
    ("marker text length not checked", "elif len(txt) < 12:", "elif False:"),
    ("marker text may name Rahu/Ketu", 'elif re.search(r"\\b(rahu|ketu)\\b", txt, re.I):', "elif False:"),
    ("a marker leaks over a blank line", "        if not s:\n            break\n        only_comment", "        if not s:\n            k -= 1\n            continue\n        only_comment"),
    ("UNION no longer ends a block", 'if toks[k].up in ("UNION", "INTERSECT", "EXCEPT"):', 'if False:'),
    ("DELETE FROM target counted as a read", 'clause = "delfrom" if (kind == "DELETE" and clause == "target") else "from"', 'clause = "from"'),
    ("UPDATE blocks ignored", 'elif t.up in ("UPDATE", "DELETE") and (i == 0 or toks[i - 1].text == ")"):', 'elif t.up in ("DELETE",) and (i == 0 or toks[i - 1].text == ")"):'),
    ("same-file table constant not resolved", "and last in aliases:", "and False:"),
    ("count-helper table-name detection removed", "for m in TABLE_ARG_CALL_RE.finditer(text):", "for m in []:"),
    ("outer parentheses no longer stripped", "def _strip_parens(seq):\n", "def _strip_parens(seq):\n    return seq\n"),
    ("NOT IN accepted with only one node body", "if set(NODE_BODIES) <= low:", "if low & set(NODE_BODIES):"),
    ("python adjacent-literal merge removed", '(lang == "py" and re.fullmatch(r"\\s*[rbfuRBFU]{0,2}", gap_nc))', "False"),
    ("R1 off", "elif c > base.get(k, 0):", "elif c > base.get(k, 10**6):"),
    ("R2 off", "        if n < c:\n            if n == 0:", "        if False:\n            if n == 0:"),
    ("R3 off", "if k in retired:\n            errs.append(f\"R3", "if False:\n            errs.append(f\"R3"),
    ("R4 off", "    if total != ceiling:", "    if False:"),
    ("owner not required", 'not str(e.get("note", "")).strip() or not str(e.get("owner", "")).strip()', 'not str(e.get("note", "")).strip()'),
]


@pytest.mark.parametrize("name,old,new", MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_mutation_is_caught(name, old, new):
    assert SRC.count(old) >= 1, f"mutation anchor not found in the source: {old!r}"
    mutated = _load(SRC.replace(old, new, 1), "cnsp_mut")
    try:
        assert not _extra_checks(mutated), f"mutation survived: {name}"
    finally:
        sys.modules["check_node_series_pin"] = lint


def test_the_review_named_surviving_mutations_are_now_covered_by_dedicated_tests():
    names = [m[0] for m in MUTATIONS]
    assert sum("(review: survived)" in n for n in names) == 3
    assert len(MUTATIONS) >= 17
