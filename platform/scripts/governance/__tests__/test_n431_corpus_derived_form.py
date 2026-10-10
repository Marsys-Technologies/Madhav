"""test_n431_corpus_derived_form.py: SS N-431 R1, the `corpus_derived` declaration form and its validator (source only: no database, no sandbox run).

UNRUN DRAFT: written to the scratchpad because the Write tool was denied for the worktree path; it must be copied to
platform/scripts/governance/__tests__/test_n431_corpus_derived_form.py and run before it is relied on.

An asset whose rows are a pure function of a committed deterministic parser over cited source chunks (bg_rules: `extract_rules_from_chunk` over classical_text_chunks) declares `corpus_derived`. This file pins
the DECLARATION side: the shape and cross-field validator (`corpus_derived_problem`, run at load time like its neighbours), the defaults-filled `normalise_corpus_derived`, the pin helper `pin_files`, the pin
check against the tree (`corpus_derived_pin_problem`: sha256 of every pinned file, the function by AST, the import closure), the pure `corpus_derived_na_problem` and the unwired cell-mapping data.
"""
from __future__ import annotations

import ast
import copy
import json
import os
import pathlib
import shutil
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

EVID = "platform/scripts/governance/__tests__/test_n431_corpus_derived_form.py:1"      # a real repo file that names the fixture parser function (extract_fixture)
REAL_MODULE_ROOT = "platform/python-sidecar"
REAL_PARSER = "platform/python-sidecar/brahmagyan/l0_rules.py"
REAL_FILES = [REAL_PARSER, "platform/python-sidecar/brahmagyan/__init__.py", "platform/python-sidecar/brahmagyan/graha_vocabulary.py",
              "platform/python-sidecar/brahmagyan/l0_semantic_release.py", "platform/python-sidecar/brahmagyan/l0_semantic_release_v1.json"]
WHY = "the rows of this table are verbatim slices and templated output of the pinned deterministic parser over the cited chunks, produced by no model and no hand"

PARSER_SRC = '''from __future__ import annotations

import json
from pkg.helper import h

LIVE = 0.6


def extract_fixture(chunk, valid_ids):
    for i, w in enumerate(chunk["content"].split()):
        yield {"rule_id": h(chunk["id"]) + str(i), "text_id": chunk["text_id"], "_quality": 0.7, "pass_log": json.dumps([{"chunk_id": chunk["id"]}])}
'''


def _fixture_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "repo"
    (root / "mod" / "pkg").mkdir(parents=True)
    (root / "mod" / "parser.py").write_text(PARSER_SRC, encoding="utf-8")
    (root / "mod" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "mod" / "pkg" / "helper.py").write_text("def h(x):\n    return str(x)\n", encoding="utf-8")
    (root / "mod" / "data.json").write_text('{"k": 1}', encoding="utf-8")
    return root


FIX_FILES = ["mod/parser.py", "mod/pkg/__init__.py", "mod/pkg/helper.py"]


def _cd(root: pathlib.Path, files=None, **over) -> dict:
    cd = dict(
        table="rules_out", key_columns=["rule_id"], cite_column="pass_log", cite_path=[0, "chunk_id"],
        source=dict(table="chunks_in", id_column="id", text_columns=["content"], extra_columns=["text_id"], order_by=["text_id", "id"]),
        parser=dict(module_root="mod", file="mod/parser.py", function="extract_fixture", pinned_files=ac.pin_files(root, files or FIX_FILES), input_shape="chunk_row_dict",
                    extra_args=[dict(name="valid_ids", kind="distinct_values", table="chunks_in", column="text_id")]),
        derived=dict(drop_keys=["_quality"], keep_when=dict(key="_quality", at_least_constant="LIVE"), null_unless_in=[], json_columns=["pass_log"], numeric_columns=[], duplicate_policy="first_wins"),
        ignore_columns=["created_at"], scope=dict(stored="all", uncited_chunks=dict(sample=200)), why=WHY, evidence=EVID)
    cd.update(over)
    return cd


def _entry(cd, **over) -> dict:
    e = dict(kind="data", prose_fields=None, corpus_derived=cd)
    e.update(over)
    return e


@pytest.fixture()
def fx(tmp_path):
    root = _fixture_repo(tmp_path)
    return root, _cd(root)


# ───────────────────────── a valid declaration ─────────────────────────

def test_a_valid_declaration_over_a_tiny_fixture_repo_passes_shape_and_pins(fx):
    root, cd = fx
    assert ac.corpus_derived_problem(_entry(cd)) is None
    assert ac.corpus_derived_pin_problem(_entry(cd), root) is None
    assert ac.corpus_derived_pin_problem(cd, root) is None            # the inner object is accepted too
    assert ac.corpus_derived_import_closure(root, "mod", "mod/parser.py") == sorted(FIX_FILES)


def test_normalise_fills_every_default_and_returns_a_copy(fx):
    root, _ = fx
    minimal = dict(table="rules_out", key_columns=["rule_id"], cite_column="chunk_id", source=dict(table="chunks_in", id_column="id", text_columns=["content"]),
                   parser=dict(module_root="mod", file="mod/parser.py", function="extract_fixture", pinned_files=ac.pin_files(root, FIX_FILES)), why=WHY, evidence=EVID)
    n = ac.normalise_corpus_derived(_entry(minimal))
    assert n["cite_path"] is None and n["ignore_columns"] == [] and n["scope"] == dict(stored="all", uncited_chunks=dict(sample=200))
    assert n["source"]["extra_columns"] == [] and n["source"]["order_by"] == ["id"]
    assert n["parser"]["input_shape"] == "chunk_row_dict" and n["parser"]["extra_args"] == []
    assert n["derived"] == dict(drop_keys=[], keep_when=None, null_unless_in=[], json_columns=[], numeric_columns=[], duplicate_policy="first_wins")
    assert ac.normalise_corpus_derived(minimal) == n                    # the inner object gives the same result
    n["source"]["text_columns"].append("x")
    assert minimal["source"]["text_columns"] == ["content"]               # a copy: mutating the result touches no declaration
    with pytest.raises(ac.DeclarationsError, match="no corpus_derived"):
        ac.normalise_corpus_derived({"kind": "data", "corpus_derived": None})
    with pytest.raises(ac.DeclarationsError, match="^corpus_derived"):
        ac.normalise_corpus_derived(dict(minimal, table="not ident"))


def test_the_normalised_form_of_a_full_declaration_is_stable(fx):
    _, cd = fx
    n = ac.normalise_corpus_derived(cd)
    assert ac.normalise_corpus_derived(n) == n and n["derived"]["keep_when"] == dict(key="_quality", at_least_constant="LIVE")


# ───────────────────────── every shape refusal ─────────────────────────

REFUSALS = [
    ("unknown top-level key", lambda d: d.update(extra=1), "unknown field"),
    ("unknown source key", lambda d: d["source"].update(extra=1), "corpus_derived.source: unknown field"),
    ("unknown parser key", lambda d: d["parser"].update(extra=1), "corpus_derived.parser: unknown field"),
    ("unknown derived key", lambda d: d["derived"].update(extra=1), "corpus_derived.derived: unknown field"),
    ("unknown scope key", lambda d: d["scope"].update(extra=1), "corpus_derived.scope: unknown field"),
    ("missing why", lambda d: d.pop("why"), "missing field"),
    ("missing parser", lambda d: d.pop("parser"), "missing field"),
    ("table not an identifier", lambda d: d.update(table="a b"), "corpus_derived.table"),
    ("no key columns", lambda d: d.update(key_columns=[]), "key_columns"),
    ("duplicate key column", lambda d: d.update(key_columns=["rule_id", "rule_id"]), "lists a name twice"),
    ("cite column not an identifier", lambda d: d.update(cite_column="x-y"), "cite_column"),
    ("cite_path a bool index", lambda d: d.update(cite_path=[True]), "cite_path"),
    ("cite_path too long", lambda d: d.update(cite_path=[0, "a", "b", "c", "d"]), "cite_path"),
    ("cite_path without json_columns", lambda d: d["derived"].update(json_columns=[]), "json_columns"),
    ("json cite column with no path", lambda d: d.update(cite_path=None), "no cite_path"),
    ("ignore_columns a value column", lambda d: d.update(ignore_columns=["confidence"]), "not write-time timestamp columns"),
    ("ignore_columns the key", lambda d: d.update(ignore_columns=["rule_id"]), "not write-time timestamp columns"),
    ("ignore_columns the same name twice", lambda d: d.update(ignore_columns=["created_at", "created_at"]), "lists a name twice"),
    ("ignore_columns not a list", lambda d: d.update(ignore_columns="created_at"), "ignore_columns"),
    ("sample zero", lambda d: d["scope"]["uncited_chunks"].update(sample=0), "sample must be an integer 1 to 2000"),
    ("sample over the bound", lambda d: d["scope"]["uncited_chunks"].update(sample=2001), "sample must be an integer 1 to 2000"),
    ("sample a bool", lambda d: d["scope"]["uncited_chunks"].update(sample=True), "sample must be an integer"),
    ("sample a float", lambda d: d["scope"]["uncited_chunks"].update(sample=10.0), "sample must be an integer"),
    ("uncited check null", lambda d: d["scope"].update(uncited_chunks=None), "may not be null"),
    ("uncited check extra key", lambda d: d["scope"]["uncited_chunks"].update(all=True), "exactly {sample"),
    ("stored slice malformed", lambda d: d["scope"].update(stored={"column": "x"}), "scope.stored"),
    ("stored not all", lambda d: d["scope"].update(stored="some"), "scope.stored"),
    ("why too short", lambda d: d.update(why="short"), "why"),
    ("why a placeholder", lambda d: d.update(why="todo todo todo todo todo todo todo"), "why"),
    ("evidence missing file", lambda d: d.update(evidence="platform/no/such/file.py:3"), "evidence"),
    ("evidence without a line", lambda d: d.update(evidence=EVID.rsplit(":", 1)[0]), "must name the line"),
    ("evidence line past the end", lambda d: d.update(evidence=EVID.rsplit(":", 1)[0] + ":999999"), "evidence"),
    ("evidence unverified", lambda d: d.update(evidence="unverified: somewhere in the writer"), "evidence"),
    ("evidence that does not name the parser", lambda d: d.update(evidence="platform/scripts/governance/README.md:1"), "does not mention"),
    ("evidence escaping the repo", lambda d: d.update(evidence="../outside.py:1"), "evidence"),
    ("source table is the produced table", lambda d: d["source"].update(table="rules_out"), "two different tables"),
    ("source id column also a text column", lambda d: d["source"].update(text_columns=["id"]), "distinct columns"),
    ("source no text column", lambda d: d["source"].update(text_columns=[]), "text_columns"),
    ("source extra_columns not a list", lambda d: d["source"].update(extra_columns="text_id"), "extra_columns"),
    ("source missing id_column", lambda d: d["source"].pop("id_column"), "missing field"),
    ("parser pin sha not hex", lambda d: d["parser"]["pinned_files"][0].update(sha256="XYZ"), "64 lower-case hex"),
    ("parser pin sha upper case", lambda d: d["parser"]["pinned_files"][0].update(sha256="A" * 64), "64 lower-case hex"),
    ("parser pin listed twice", lambda d: d["parser"]["pinned_files"].append(dict(d["parser"]["pinned_files"][0])), "pinned twice"),
    ("parser pin extra field", lambda d: d["parser"]["pinned_files"][0].update(size=1), "exactly the fields"),
    ("parser pin path traversal", lambda d: d["parser"]["pinned_files"][1].update(path="mod/../x.py"), "repo-relative path"),
    ("parser pin absolute path", lambda d: d["parser"]["pinned_files"][1].update(path="/etc/passwd"), "repo-relative path"),
    ("parser pin empty list", lambda d: d["parser"].update(pinned_files=[]), "pinned_files"),
    ("parser pin list too long", lambda d: d["parser"].update(pinned_files=[dict(path=f"mod/f{i}.py", sha256="0" * 64) for i in range(33)]), "1 to 32"),
    ("parser file not pinned", lambda d: d["parser"].update(pinned_files=d["parser"]["pinned_files"][1:]), "not among pinned_files"),
    ("parser file outside module_root", lambda d: d["parser"].update(module_root="other"), "under parser.module_root"),
    ("parser file not .py", lambda d: d["parser"].update(file="mod/data.json"), "must end .py"),
    ("parser function not an identifier", lambda d: d["parser"].update(function="a.b"), "parser.function"),
    ("parser input shape unknown", lambda d: d["parser"].update(input_shape="rows"), "input_shape"),
    ("parser extra arg kind unknown", lambda d: d["parser"]["extra_args"][0].update(kind="sql"), "kind must be one of"),
    ("parser extra arg twice", lambda d: d["parser"]["extra_args"].append(dict(d["parser"]["extra_args"][0])), "listed twice"),
    ("parser extra arg extra field", lambda d: d["parser"]["extra_args"][0].update(x=1), "exactly the fields"),
    ("derived duplicate policy unknown", lambda d: d["derived"].update(duplicate_policy="last_wins"), "duplicate_policy"),
    ("derived keep_when key not a dropped key", lambda d: d["derived"].update(drop_keys=[]), "listed in derived.drop_keys"),
    ("derived keep_when malformed", lambda d: d["derived"].update(keep_when={"key": "_quality"}), "keep_when"),
    ("derived json and numeric overlap", lambda d: d["derived"].update(numeric_columns=["pass_log"]), "both json_columns and numeric_columns"),
    ("derived null_unless_in malformed", lambda d: d["derived"].update(null_unless_in=[{"column": "yoga"}]), "null_unless_in"),
    ("derived null_unless_in on the key", lambda d: d["derived"].update(null_unless_in=[dict(column="rule_id", table="t", ref_column="c")]), "key or ignored"),
    ("derived drop_keys holds a key column", lambda d: d["derived"].update(drop_keys=["_quality", "rule_id"]), "dropped derived key"),
    ("derived drop_keys not a list", lambda d: d["derived"].update(drop_keys="_quality"), "drop_keys"),
    ("cite column ignored", lambda d: d.update(ignore_columns=["created_at"], cite_column="created_at", cite_path=None), "cite column"),
]


@pytest.mark.parametrize("name,mut,needle", REFUSALS, ids=[r[0] for r in REFUSALS])
def test_every_malformed_declaration_is_refused_with_a_named_reason(fx, name, mut, needle):
    root, cd = fx
    cd = copy.deepcopy(cd)
    mut(cd)
    bad = ac.corpus_derived_problem(_entry(cd))
    assert bad and needle in bad, bad
    with pytest.raises(ac.DeclarationsError, match="corpus_derived"):
        ac.normalise_corpus_derived(cd)
    assert ac.corpus_derived_pin_problem(cd, root)          # a refused declaration never reaches the pin check as sound


def test_the_object_itself_must_be_an_object(fx):
    for v in ([], "x", 3, True):
        assert "must be an object" in ac.corpus_derived_problem({"corpus_derived": v})
    assert ac.corpus_derived_problem({"corpus_derived": None}) is None and ac.corpus_derived_problem({}) is None and ac.corpus_derived_problem(None) is None


def test_ignore_columns_are_a_closed_timestamp_list_and_each_is_accepted(fx):
    root, cd = fx
    for c in ("created_at", "updated_at", "computed_at"):
        assert ac.corpus_derived_problem(_entry(_cd(root, ignore_columns=[c]))) is None
    assert ac.corpus_derived_problem(_entry(_cd(root, ignore_columns=["created_at", "updated_at", "computed_at"]))) is None
    assert ac.corpus_derived_problem(_entry(_cd(root, ignore_columns=[]))) is None
    assert ac.CORPUS_DERIVED_IGNORABLE == ("created_at", "updated_at", "computed_at")
    for c in ("synced_at", "extracted_by", "confidence", "text_id", "CREATED_AT", "created_at "):
        assert ac.corpus_derived_problem(_entry(_cd(root, ignore_columns=[c])))


def test_sample_bounds_are_inclusive(fx):
    root, _ = fx
    for n in (1, 200, 2000):
        assert ac.corpus_derived_problem(_entry(_cd(root, scope=dict(stored="all", uncited_chunks=dict(sample=n))))) is None
    assert ac.normalise_corpus_derived(_cd(root, scope=dict(uncited_chunks=dict(sample=7))))["scope"] == dict(stored="all", uncited_chunks=dict(sample=7))
    assert ac.normalise_corpus_derived(_cd(root, scope={}))["scope"]["uncited_chunks"] == dict(sample=200)
    assert ac.corpus_derived_problem(_entry(_cd(root, scope=dict(stored=dict(column="extracted_by", equals="python_regex_v2"))))) is None


# ───────────────────────── the entry-level rules and the generic validator path ─────────────────────────

def test_the_form_is_exclusive_with_every_other_account_of_the_rows(fx):
    root, cd = fx
    assert "prose_fields null" in ac.corpus_derived_problem(_entry(cd, prose_fields=["x"]))
    assert ac.corpus_derived_problem(_entry(cd, prose_fields=[])) is not None
    for k in ("prose_none", "prose_coupling", "curated_corpus", "writer_constant_phrases", "no_table"):
        bad = ac.corpus_derived_problem(_entry(cd, **{k: {"x": 1}}))
        assert bad and k in bad and bad.startswith("corpus_derived")
    assert ac.corpus_derived_problem(_entry(cd, prose_none=None, curated_corpus=None)) is None


def test_table_must_be_one_of_a_declared_produced_tables_set(fx):
    _, cd = fx
    assert ac.corpus_derived_problem(_entry(cd, produced_tables=[{"table": "rules_out"}])) is None
    bad = ac.corpus_derived_problem(_entry(cd, produced_tables=[{"table": "other_table"}]))
    assert bad and "not one of the asset's declared produced_tables" in bad
    assert ac.corpus_derived_problem(_entry(cd, produced_tables=[{"table": "other_table"}, {"table": "rules_out", "filter": {"column": "k", "equals": "v"}}])) is None


def test_the_key_is_registered_and_the_generic_validator_calls_the_problem_function():
    assert "corpus_derived" in ac.DECL_FORMGAP_KEYS
    doc = copy.deepcopy(json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8")))
    e = doc["assets"]["bg_rules"]
    e["corpus_derived"] = dict(_real_cd(), why="x")
    with pytest.raises(ac.DeclarationsError, match=r"assets\['bg_rules'\]\.corpus_derived.*why"):
        ac.validate_declarations(doc)
    e["corpus_derived"] = _real_cd()
    ac.validate_declarations(doc)                                                         # the real, sound declaration loads
    e["corpus_derived"] = dict(_real_cd(), surprise=1)
    with pytest.raises(ac.DeclarationsError, match="unknown field"):
        ac.validate_declarations(doc)
    # exclusivity is the form validator's own rule (the generic validator would reject the other form's malformed block first), so it is tested on the form validator directly
    with pytest.raises(ac.DeclarationsError, match="cannot stand beside prose_none"):
        ac.validate_corpus_derived_declaration("assets['bg_rules']", dict(corpus_derived=_real_cd(), prose_none={"x": 1}))


def test_validate_corpus_derived_declaration_prefixes_the_asset_location():
    with pytest.raises(ac.DeclarationsError, match=r"^assets\['a'\]\.corpus_derived"):
        ac.validate_corpus_derived_declaration("assets['a']", {"corpus_derived": {}})
    ac.validate_corpus_derived_declaration("assets['a']", {})


# ───────────────────────── pin_files and the pin check against the tree ─────────────────────────

def test_pin_files_hashes_the_bytes_in_order_and_refuses_what_is_not_a_repo_file(tmp_path):
    root = _fixture_repo(tmp_path)
    import hashlib
    got = ac.pin_files(root, ["mod/pkg/helper.py", "mod/parser.py"])
    assert [g["path"] for g in got] == ["mod/pkg/helper.py", "mod/parser.py"]
    assert got[1]["sha256"] == hashlib.sha256(PARSER_SRC.encode("utf-8")).hexdigest() and ac.pin_files(root, []) == []
    for bad in ("mod/missing.py", "../x.py", "/etc/passwd", "mod", "mod/./parser.py"):
        with pytest.raises(ValueError, match="pin_files"):
            ac.pin_files(root, [bad])
    outside = tmp_path / "outside.py"
    outside.write_text("x = 1\n", encoding="utf-8")
    os.symlink(outside, root / "mod" / "link.py")
    with pytest.raises(ValueError, match="outside the repository"):
        ac.pin_files(root, ["mod/link.py"])


def test_a_changed_pinned_file_refuses_the_declaration_naming_the_file(fx):
    root, cd = fx
    (root / "mod" / "pkg" / "helper.py").write_text("def h(x):\n    return str(x) + 'z'\n", encoding="utf-8")
    bad = ac.corpus_derived_pin_problem(_entry(cd), root)
    assert bad and "mod/pkg/helper.py" in bad and "hashes to" in bad and "changed since it was declared" in bad
    root2 = root.parent / "repo2"
    shutil.copytree(root, root2)
    (root2 / "mod" / "parser.py").write_text(PARSER_SRC + "\n# one more comment\n", encoding="utf-8")
    bad = ac.corpus_derived_pin_problem(_entry(cd), root2)
    assert bad and "mod/parser.py" in bad and "hashes to" in bad


def test_a_missing_pinned_file_refuses(fx):
    root, cd = fx
    (root / "mod" / "pkg" / "helper.py").unlink()
    bad = ac.corpus_derived_pin_problem(_entry(cd), root)
    assert bad and "mod/pkg/helper.py" in bad and "does not exist" in bad


def test_a_pin_to_a_data_file_is_checked_too(tmp_path):
    root = _fixture_repo(tmp_path)
    cd = _cd(root, files=FIX_FILES + ["mod/data.json"])
    assert ac.corpus_derived_pin_problem(cd, root) is None
    (root / "mod" / "data.json").write_text('{"k": 2}', encoding="utf-8")
    assert "mod/data.json" in ac.corpus_derived_pin_problem(cd, root)


def test_the_function_must_be_defined_once_at_module_level(tmp_path):
    root = _fixture_repo(tmp_path)

    def declare(src):
        (root / "mod" / "parser.py").write_text(src, encoding="utf-8")
        return _cd(root)

    assert "is not defined at module level" in ac.corpus_derived_pin_problem(declare(PARSER_SRC.replace("def extract_fixture", "def other_name")), root)
    nested = PARSER_SRC.replace("def extract_fixture(chunk, valid_ids):", "def wrapper():\n    def extract_fixture(chunk, valid_ids):\n        return []\n    return extract_fixture\n\n\ndef unrelated(chunk, valid_ids):")
    assert "is not defined at module level" in ac.corpus_derived_pin_problem(declare(nested), root)
    assert "is not defined at module level" in ac.corpus_derived_pin_problem(declare(PARSER_SRC.replace("def extract_fixture", "extract_fixture = lambda c, v: []\n\n\ndef unrelated")), root)
    assert "defined 2 times" in ac.corpus_derived_pin_problem(declare(PARSER_SRC + "\n\ndef extract_fixture(chunk, valid_ids):\n    return []\n"), root)
    assert "does not parse" in ac.corpus_derived_pin_problem(declare(PARSER_SRC + "\ndef broken(:\n"), root)
    assert ac.corpus_derived_pin_problem(declare(PARSER_SRC), root) is None
    assert ac.corpus_derived_pin_problem(declare(PARSER_SRC.replace("def extract_fixture", "async def extract_fixture")), root) is not None      # an async def is no parser


def test_a_keep_when_constant_must_be_a_single_numeric_module_literal(tmp_path):
    root = _fixture_repo(tmp_path)

    def problem(src):
        (root / "mod" / "parser.py").write_text(src, encoding="utf-8")
        return ac.corpus_derived_pin_problem(_cd(root), root)

    assert problem(PARSER_SRC) is None
    assert problem(PARSER_SRC.replace("LIVE = 0.6", "LIVE: float = 0.6")) is None
    assert "keep_when constant LIVE" in problem(PARSER_SRC.replace("LIVE = 0.6", "OTHER = 0.6"))
    assert "keep_when constant LIVE" in problem(PARSER_SRC.replace("LIVE = 0.6", "LIVE = 'high'"))
    assert "keep_when constant LIVE" in problem(PARSER_SRC.replace("LIVE = 0.6", "LIVE = True"))
    assert "keep_when constant LIVE" in problem(PARSER_SRC.replace("LIVE = 0.6", "LIVE = 0.6\nLIVE = 0.7"))
    assert "keep_when constant LIVE" in problem(PARSER_SRC.replace("LIVE = 0.6", "LIVE = compute()"))


def test_an_imported_repo_local_file_that_is_not_pinned_refuses_naming_it(tmp_path):
    root = _fixture_repo(tmp_path)
    cd = _cd(root, files=["mod/parser.py", "mod/pkg/__init__.py"])           # helper.py is imported but not pinned
    bad = ac.corpus_derived_pin_problem(cd, root)
    assert bad and "mod/pkg/helper.py" in bad and "not pinned" in bad
    cd = _cd(root, files=["mod/parser.py", "mod/pkg/helper.py"])             # the package __init__.py is loaded with it
    assert "mod/pkg/__init__.py" in ac.corpus_derived_pin_problem(cd, root)
    assert ac.corpus_derived_pin_problem(_cd(root), root) is None


def test_the_import_closure_follows_nested_function_level_and_relative_imports(tmp_path):
    root = tmp_path / "r"
    (root / "m" / "a" / "b").mkdir(parents=True)
    (root / "m" / "top.py").write_text("def f():\n    from a.b import deep\n    return deep\n", encoding="utf-8")
    (root / "m" / "a" / "__init__.py").write_text("", encoding="utf-8")
    (root / "m" / "a" / "b" / "__init__.py").write_text("", encoding="utf-8")
    (root / "m" / "a" / "b" / "deep.py").write_text("from . import sibling\nfrom ..up import u\nimport os, json\n", encoding="utf-8")
    (root / "m" / "a" / "b" / "sibling.py").write_text("x = 1\n", encoding="utf-8")
    (root / "m" / "a" / "up.py").write_text("u = 1\n", encoding="utf-8")
    got = ac.corpus_derived_import_closure(root, "m", "m/top.py")
    assert got == ["m/a/__init__.py", "m/a/b/__init__.py", "m/a/b/deep.py", "m/a/b/sibling.py", "m/a/up.py", "m/top.py"]
    (root / "m" / "bad.py").write_text("import a.b.deep\ndef x(:\n", encoding="utf-8")
    with pytest.raises(ValueError, match="does not parse"):
        ac.corpus_derived_import_closure(root, "m", "m/bad.py")


def test_a_stdlib_import_is_not_a_repo_file_even_when_a_same_named_dir_exists_elsewhere(tmp_path):
    root = tmp_path / "r"
    (root / "m").mkdir(parents=True)
    (root / "json").mkdir()
    (root / "json" / "__init__.py").write_text("", encoding="utf-8")                  # outside module_root: never an import of m/*.py
    (root / "m" / "p.py").write_text("import json\nimport re\n", encoding="utf-8")
    assert ac.corpus_derived_import_closure(root, "m", "m/p.py") == ["m/p.py"]


# ───────────────────────── the REAL committed parser ─────────────────────────

def _real_cd() -> dict:
    return dict(
        table="sutravali_rules", key_columns=["rule_id"], cite_column="extraction_pass_log", cite_path=[0, "chunk_id"],
        source=dict(table="classical_text_chunks", id_column="id", text_columns=["content_en"], extra_columns=["text_id", "verse_ref"], order_by=["text_id", "chapter", "verse_start"]),
        parser=dict(module_root=REAL_MODULE_ROOT, file=REAL_PARSER, function="extract_rules_from_chunk", pinned_files=ac.pin_files(ac.ROOT, REAL_FILES), input_shape="chunk_row_dict",
                    extra_args=[dict(name="valid_text_ids", kind="distinct_values", table="classical_text_chunks", column="text_id")]),
        derived=dict(drop_keys=["_quality"], keep_when=dict(key="_quality", at_least_constant="QUALITY_THRESHOLD_LIVE"),
                     null_unless_in=[dict(column="yoga_canonical_id", table="brahma_yoga_catalog", ref_column="canonical_id"),
                                     dict(column="dasha_system_id", table="brahma_dasha_systems", ref_column="canonical_id")],
                     json_columns=["antecedent_jsonb", "predicate_jsonb", "prediction_jsonb", "extraction_pass_log"], numeric_columns=["confidence", "quality_score"], duplicate_policy="first_wins"),
        ignore_columns=["created_at"], scope=dict(stored=dict(column="extracted_by", equals="python_regex_v2"), uncited_chunks=dict(sample=200)),
        why="every sutravali_rules row of extracted_by python_regex_v2 is the output of the pinned regex parser over the classical_text_chunks row its extraction_pass_log cites (verbatim slices, templated descriptions, uuid5 ids)",
        evidence=REAL_PARSER + ":1609")


def test_the_real_parser_can_be_pinned_with_its_real_import_closure_and_the_validator_accepts_it():
    cd = _real_cd()
    assert ac.corpus_derived_problem(_entry(cd)) is None
    assert ac.corpus_derived_pin_problem(_entry(cd)) is None                          # every digest equals the committed file on this checkout
    assert ac.corpus_derived_import_closure(ac.ROOT, REAL_MODULE_ROOT, REAL_PARSER) == sorted(REAL_FILES[:4])       # l0_rules -> graha_vocabulary -> l0_semantic_release (+ the package __init__)
    assert (ac.ROOT / REAL_FILES[4]).is_file() and REAL_FILES[4] in {d["path"] for d in cd["parser"]["pinned_files"]}      # the JSON the release module reads at import time is pinned as data
    n = ac.normalise_corpus_derived(_entry(cd))
    assert n["parser"]["function"] == "extract_rules_from_chunk" and len(n["parser"]["pinned_files"]) == 5


def test_the_real_parser_function_and_threshold_resolve_by_ast():
    tree = ast.parse((ac.ROOT / REAL_PARSER).read_text(encoding="utf-8"))
    assert [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "extract_rules_from_chunk"] == ["extract_rules_from_chunk"]
    args = [a.arg for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "extract_rules_from_chunk" for a in n.args.args]
    assert args[:2] == ["chunk", "valid_text_ids"]                                    # the declared extra arg name is the parser's real second parameter
    assert ac.corpus_derived_pin_problem(_entry(_real_cd())) is None                  # QUALITY_THRESHOLD_LIVE is a single numeric module literal


def test_a_changed_copy_of_the_real_parser_refuses_and_an_unpinned_real_import_refuses(tmp_path):
    root = tmp_path / "copy"
    for rel in REAL_FILES:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ac.ROOT / rel, dst)
    cd = _real_cd()
    assert ac.corpus_derived_pin_problem(_entry(cd), root) is None                     # the faithful copy still verifies
    p = root / REAL_PARSER
    p.write_text(p.read_text(encoding="utf-8").replace("QUALITY_THRESHOLD_LIVE = 0.6", "QUALITY_THRESHOLD_LIVE = 0.5"), encoding="utf-8")
    bad = ac.corpus_derived_pin_problem(_entry(cd), root)
    assert bad and REAL_PARSER in bad and "hashes to" in bad
    shutil.copy2(ac.ROOT / REAL_PARSER, p)
    j = root / REAL_FILES[4]
    j.write_text(j.read_text(encoding="utf-8") + " ", encoding="utf-8")                  # the pinned data file
    assert REAL_FILES[4] in ac.corpus_derived_pin_problem(_entry(cd), root)
    shutil.copy2(ac.ROOT / REAL_FILES[4], j)
    thin = dict(cd, parser=dict(cd["parser"], pinned_files=[d for d in cd["parser"]["pinned_files"] if not d["path"].endswith("graha_vocabulary.py")]))
    bad = ac.corpus_derived_pin_problem(_entry(thin), root)
    assert bad and "graha_vocabulary.py" in bad and "not pinned" in bad


# ───────────────────────── the cell mapping (unwired design data + the pure N/A check) ─────────────────────────

BLOCK = dict(verified=True, table="sutravali_rules", stored_rows=3002, matched_rows=3002, mismatches=0, chunks_run=900, uncited_sampled=200, uncited_yield=0, blank_leaves=0,
             parser=dict(file=REAL_PARSER, function="extract_rules_from_chunk", sha256="0" * 64), pinned_files=list(REAL_FILES), loaded_repo_files=list(REAL_FILES[:4]))


def _na(**over):
    b = dict(copy.deepcopy(BLOCK), **over)
    return dict(v=ac.NA, cause="corpus-derived", measured="x", corpus_derived=b)


def test_the_na_check_is_silent_for_any_other_record_and_accepts_a_verified_block():
    for crit in ac.CORPUS_DERIVED_NA_CRITERIA:
        assert ac.corpus_derived_na_problem(crit, _na()) is None
    assert ac.corpus_derived_na_problem("Narr.lint", _na()) is None                                  # not a criterion of this form
    assert ac.corpus_derived_na_problem("Narr.agree", dict(v=ac.PASS, cause="corpus-derived")) is None
    assert ac.corpus_derived_na_problem("Narr.agree", dict(v=ac.NA, cause="no-prose")) is None
    assert ac.corpus_derived_na_problem("Narr.agree", None) is None


TAMPERS = [
    ("no block", lambda r: r.pop("corpus_derived"), "no verified block"),
    ("unverified", lambda r: r["corpus_derived"].update(verified=False), "no verified block"),
    ("verified a truthy string", lambda r: r["corpus_derived"].update(verified="yes"), "no verified block"),
    ("a mismatch", lambda r: r["corpus_derived"].update(mismatches=1), "matched"),
    ("fewer matched than stored", lambda r: r["corpus_derived"].update(matched_rows=3001), "matched"),
    ("zero stored rows", lambda r: r["corpus_derived"].update(stored_rows=0, matched_rows=0), "matched"),
    ("a bool count", lambda r: r["corpus_derived"].update(stored_rows=True, matched_rows=True), "matched"),
    ("no chunk run", lambda r: r["corpus_derived"].update(chunks_run=0), "matched"),
    ("the uncited sample yielded", lambda r: r["corpus_derived"].update(uncited_yield=2), "matched"),
    ("a blank leaf", lambda r: r["corpus_derived"].update(blank_leaves=1), "matched"),
    ("no parser digest", lambda r: r["corpus_derived"]["parser"].update(sha256="short"), "parser file, function and sha256"),
    ("a loaded file that is not pinned", lambda r: r["corpus_derived"].update(loaded_repo_files=REAL_FILES[:4] + ["platform/python-sidecar/brahmagyan/other.py"]), "not all pinned"),
    ("the parser file not loaded", lambda r: r["corpus_derived"].update(loaded_repo_files=REAL_FILES[1:4]), "not all pinned"),
    ("no pins", lambda r: r["corpus_derived"].update(pinned_files=[]), "not all pinned"),
]


@pytest.mark.parametrize("name,mut,needle", TAMPERS, ids=[t[0] for t in TAMPERS])
def test_the_na_check_refuses_a_record_whose_block_does_not_earn_it(name, mut, needle):
    rec = _na()
    mut(rec)
    for crit in ac.CORPUS_DERIVED_NA_CRITERIA:
        bad = ac.corpus_derived_na_problem(crit, rec)
        assert bad and needle in bad and crit in bad


def test_the_data_additions_merge_into_a_consistent_registry(monkeypatch):
    causes = {k: tuple(v) for k, v in ac.NA_CAUSES.items()}
    decisions = dict(ac.NA_RULE_DECISIONS)
    for crit, cs in ac.CORPUS_DERIVED_NA_CAUSES.items():
        assert crit in ac.CRITERION_REGISTRY and cs == ("corpus-derived",)
        causes[crit] = tuple(dict.fromkeys(causes.get(crit, ()) + cs))
    decisions.update(ac.CORPUS_DERIVED_NA_RULE_DECISIONS)
    monkeypatch.setattr(ac, "NA_CAUSES", causes)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", decisions)
    ac.validate_na_rule_decisions()                                                                  # every new id is `<crit>#measured:<registered cause>` with a non-blank decision
    assert set(ac.CORPUS_DERIVED_NA_RULE_DECISIONS) == {f"{c}#measured:corpus-derived" for c in ac.CORPUS_DERIVED_NA_CRITERIA}
    assert all(v.startswith("SS N-431") for v in ac.CORPUS_DERIVED_NA_RULE_DECISIONS.values())
    assert "Narr.lint" not in ac.CORPUS_DERIVED_NA_CRITERIA                                          # the sixth cell stays on lint_none (design note)
    assert len(ac.CORPUS_DERIVED_NA_CRITERIA) == 5


def test_the_registry_text_additions_name_their_own_rule_and_extend_each_criterion():
    assert set(ac.CORPUS_DERIVED_APPLICABILITY_ADDITIONS) == set(ac.CORPUS_DERIVED_NA_CRITERIA)
    for crit, tail in ac.CORPUS_DERIVED_APPLICABILITY_ADDITIONS.items():
        assert f"{crit}#measured:corpus-derived" in tail and "REGISTRY_REVISION 28" in tail and "NO_DETECTOR" in tail and tail.startswith(" N-431")
        assert isinstance(ac.CRITERION_REGISTRY[crit]["applicability"], str)


# ───────────────────────── hygiene ─────────────────────────

def test_the_changed_python_files_parse_under_the_311_grammar():
    for p in (HERE.parent / "asset_census.py", pathlib.Path(__file__)):
        ast.parse(p.read_text(encoding="utf-8"), feature_version=(3, 11))
