"""test_n297_point_codes.py: SS N-297/N-305 `vocab_point_codes` on the Vocab.alias value detector.

chart_divisionals.fact_subject carries `MC` (Medium Coeli, the Midheaven: a standard chart point beside Lagna). The detector reads the two letters as a SHORT alias of a graha ("one short alias only,
unverified"). The declaration is CHECKED: the asset's own writer must import the declared emitter module, the code set is READ from a module-level literal of that module by AST (assigned once, never mutated,
no call / comprehension / f-string), and only an EXACT member that is a short non-canonical collision is lifted. Anything else stays graded.

No database: the detector runs on faked samples. The AST reader is exercised on tmp modules for every refusal shape and on the real ga_vargas_writer.py for the real set.
"""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402

T, C = "chart_divisionals", "fact_subject"
AID = "ga_vargas"
OWN = {T: ([C, "graha", "chart_id"], {C: "text", "graha": "text", "chart_id": "uuid"}, None)}
SRC = "platform/python-sidecar/ga_writers/ga_vargas_writer.py"
NAME = "_FLOORED_BODY_TO_SUBJECT"
EVIDENCE = "platform/python-sidecar/ga_writers/ga_vargas_writer.py:123"


def decl(**over):
    d = {"table": T, "column": C, "source_file": SRC, "source_name": NAME,
         "why": "MC is Medium Coeli, the Midheaven: a standard chart-point code beside Lagna that the ga_vargas writer itself assigns as the subject of its floored MC rows", "evidence": EVIDENCE}
    d.update(over)
    return {"vocab_point_codes": [d]}


def tmp_root(tmp_path, emitter_src: str, writer_src: str | None = None, aid: str = AID, stem: str = "ga_vargas_writer"):
    """A throw-away repo root holding an emitter module and the asset's writer, so every AST shape is exercised without touching the real files."""
    side = tmp_path / "platform" / "python-sidecar"
    (side / "ga_writers").mkdir(parents=True)
    (side / "pipeline" / "orchestrator" / "writers").mkdir(parents=True)
    (side / "ga_writers" / f"{stem}.py").write_text(emitter_src, encoding="utf-8")
    (side / "pipeline" / "orchestrator" / "writers" / f"{aid}.py").write_text(
        writer_src if writer_src is not None else f"from ga_writers.{stem} import CANONICAL\n", encoding="utf-8")
    return tmp_path


GOOD_SRC = 'CANONICAL = 1\n_FLOORED_BODY_TO_SUBJECT = {"MC": "MC", "Uranus": "URANUS", "Pluto": "PLUTO"}\n'


# ───────────────────────── the declaration's shape ─────────────────────────

def test_a_sound_declaration_has_no_problem():
    assert ac.vocab_point_codes_problem(decl()) is None
    assert ac.vocab_point_codes_problem({}) is None


@pytest.mark.parametrize("bad", [
    {"vocab_point_codes": "MC"},
    {"vocab_point_codes": []},
    {"vocab_point_codes": [decl()["vocab_point_codes"][0]] * 5},
    decl(source_file="platform/src/lib/x.py"),                                         # not under platform/python-sidecar/
    decl(source_file="platform/python-sidecar/../../etc/passwd.py"),
    decl(source_file="platform/python-sidecar/ga_writers/x.txt"),
    decl(source_file="platform/python-sidecar//ga_writers/x.py"),
    decl(source_name="not an identifier"),
    decl(source_name="X; import os"),
    decl(table="a b"),
    decl(why=""),
    decl(evidence="unverified: trust me"),
    decl(evidence="platform/python-sidecar/ga_writers/missing.py:1"),
])
def test_a_malformed_declaration_is_refused(bad):
    assert ac.vocab_point_codes_problem(bad)


def test_an_extra_missing_or_repeated_entry_is_refused():
    d = decl()
    d["vocab_point_codes"][0]["note"] = "x"
    assert "exactly the fields" in ac.vocab_point_codes_problem(d)
    d = decl()
    d["vocab_point_codes"].append(copy.deepcopy(d["vocab_point_codes"][0]))
    assert "listed twice" in ac.vocab_point_codes_problem(d)


def test_the_validator_raises_on_a_bad_declaration():
    with pytest.raises(ac.DeclarationsError):
        ac.validate_vocab_point_codes_declaration("assets.ga_x", decl(source_file="elsewhere.py"))
    ac.validate_vocab_point_codes_declaration("assets.ga_x", decl())


# ───────────────────────── the code set is READ from the emitter by AST ─────────────────────────

def test_the_real_set_is_read_from_the_real_writer_and_mc_is_in_it():
    codes = ac.vocab_point_code_values(ac.ROOT / SRC, NAME)
    assert "MC" in codes and codes == frozenset({"MC", "URANUS", "NEPTUNE", "PLUTO", "LILITH"})
    src = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert '"URANUS"' not in src and "'URANUS'" not in src                                # the engine never types the set


def test_the_real_declaration_sets_resolve_for_the_real_asset():
    sets, problems = ac.vocab_point_code_sets(decl(), AID, OWN)
    assert problems == [] and sets == {(T, C): frozenset({"MC", "URANUS", "NEPTUNE", "PLUTO", "LILITH"})}


@pytest.mark.parametrize("src, why", [
    ('N = {"MC": "MC"}\nN = {"MC": "MC", "X": "Y"}\n', "assigned 2 times"),                                   # reassigned: which one counts?
    ('N = {"MC": "MC"}\nN.update({"EVIL": "EVIL"})\n', "mutated"),                                          # the real BODY_TO_SUBJECT shape
    ('N = {"MC": "MC"}\nN["EVIL"] = "EVIL"\n', "mutated"),
    ('N = ["MC"]\nN += ["EVIL"]\n', "mutated"),
    ('N = dict(MC="MC")\n', "not a dict / list / tuple / set literal"),                                      # built by a call
    ('N = {k: k for k in ("MC", "X")}\n', "not a dict / list / tuple / set literal"),                        # comprehension
    ('N = {"MC": f"M{1}"}\n', "something other than"),                                                       # f-string value
    ('X = "MC"\nN = {"MC": X}\n', "something other than"),                                                   # a name, not a constant
    ('N = {"MC": 1}\n', "something other than"),
    ('N = {**{"MC": "MC"}}\n', "unpacks"),
    ('N = []\n', "empty"),
    ('N = {"MC": " "}\n', "something other than"),                                                           # blank constant
    ('M = {"MC": "MC"}\n', "assigned 0 times"),                                                              # the declared name does not exist
    ('def f(:\n', "could not be read"),                                                                      # a syntax error
])
def test_forgery_a_code_set_the_engine_cannot_read_exactly_is_refused(tmp_path, src, why):
    p = tmp_path / "m.py"
    p.write_text(src, encoding="utf-8")
    with pytest.raises(ac.Unknown) as ei:
        ac.vocab_point_code_values(p, "N")
    assert why in str(ei.value), (src, str(ei.value))


def test_a_list_tuple_or_set_literal_contributes_its_elements_and_a_dict_its_values():
    for src, want in (('N = ["MC", "IC"]\n', {"MC", "IC"}), ('N = ("MC",)\n', {"MC"}), ('N = {"MC", "IC"}\n', {"MC", "IC"}), ('N: dict = {"Midheaven": "MC"}\n', {"MC"})):
        p = pathlib.Path(__file__).parent / "_n297_tmp.py"
        try:
            p.write_text(src, encoding="utf-8")
            assert ac.vocab_point_code_values(p, "N") == frozenset(want), src
        finally:
            p.unlink(missing_ok=True)


# ───────────────────────── the sets: the table / column / writer the declaration names ─────────────────────────

def test_a_table_not_owned_a_missing_or_non_text_column_is_refused():
    assert "not an owned table" in ac.vocab_point_code_sets(decl(), AID, {})[1][0]
    assert "not a column" in ac.vocab_point_code_sets(decl(), AID, {T: (["chart_id"], {"chart_id": "uuid"}, None)})[1][0]
    assert "not a text column" in ac.vocab_point_code_sets(decl(), AID, {T: ([C], {C: "jsonb"}, None)})[1][0]
    assert ac.vocab_point_code_sets(decl(), AID, {T: (None, None, None)})[0] == {}


def test_forgery_an_emitter_the_assets_writer_does_not_import_is_refused():
    sets, problems = ac.vocab_point_code_sets(decl(), "ga_nakshatra", OWN)               # another asset's writer does not import ga_vargas_writer
    assert sets == {} and "not the asset's emitter" in problems[0]
    sets, problems = ac.vocab_point_code_sets(decl(), "ga_no_such_asset", OWN)
    assert sets == {} and "could not be read" in problems[0]


def test_forgery_a_writer_that_imports_a_different_module_of_the_same_name_is_refused(tmp_path):
    root = tmp_path
    tmp_root(root, GOOD_SRC, writer_src="from other_pkg.ga_vargas_writer import CANONICAL\n")
    sets, problems = ac.vocab_point_code_sets(decl(), AID, OWN, root=root)
    assert sets == {} and "not the asset's emitter" in problems[0]


def test_an_import_of_the_module_by_either_form_is_accepted(tmp_path):
    for writer_src in ("from ga_writers.ga_vargas_writer import CANONICAL\n", "import ga_writers.ga_vargas_writer\n"):
        root = tmp_root(tmp_path / str(abs(hash(writer_src))), GOOD_SRC, writer_src=writer_src)
        sets, problems = ac.vocab_point_code_sets(decl(), AID, OWN, root=root)
        assert problems == [] and sets[(T, C)] == frozenset({"MC", "URANUS", "PLUTO"}), writer_src


def test_a_relative_import_is_not_the_module(tmp_path):
    root = tmp_root(tmp_path, GOOD_SRC, writer_src="from . import ga_vargas_writer\nfrom .ga_vargas_writer import CANONICAL\n")
    assert ac.vocab_point_code_sets(decl(), AID, OWN, root=root)[0] == {}


def test_a_malformed_declaration_credits_nothing():
    sets, problems = ac.vocab_point_code_sets(decl(source_file="x.py"), AID, OWN)
    assert sets == {} and "malformed" in problems[0]


def test_the_refusal_record_is_no_detector_and_names_the_problem():
    r = ac.vocab_point_codes_refuse({"vocab_values": {"x": 1}}, ["a: b"], decl())
    assert r["v"] == ac.NO_DET and "a: b" in r["measured"] and r["declaration_disagreements"][0]["field"] == "vocab_point_codes"


# ───────────────────────── the lift: exact member, short collision only ─────────────────────────

def _sample(values):
    return dict(values=list(values), emb=[], key_hits=[], complete=True, rows=len(values), oversized=0, deep=0, leaves=0, keys=0)


CODES = frozenset({"MC", "URANUS", "NEPTUNE", "PLUTO", "LILITH"})


def test_without_the_declaration_a_lone_mc_is_one_short_alias_only():
    rec = ac.vocab_grade_column(T, C, "text", _sample(["MC"]))
    out = ac.vocab_values_record([rec], [], [T])
    assert out["v"] == ac.PARTIAL and "one short alias only" in out["measured"]


def test_with_the_declaration_the_exact_member_is_lifted_and_named():
    rec = ac.vocab_grade_column(T, C, "text", _sample(["MC", "JUP", "LAGNA"]), closed=CODES)
    assert rec["closed_homographs"] == ["MC"] and rec.get("weak") is not True
    out = ac.vocab_values_record([rec], [], [T])
    assert "one short alias only" not in out["measured"] and out["v"] == ac.PASS


@pytest.mark.parametrize("other", ["Mc", "mc", "MC ", " MC", "Ma", "Su", "Mercury "])
def test_forgery_a_case_variant_padding_or_other_short_alias_is_not_lifted(other):
    assert ac.vocab_classify(other) is not None                                    # each is a variant the lexicon READS as a term: the test cannot pass vacuously
    rec = ac.vocab_grade_column(T, C, "text", _sample(["MC", other]), closed=CODES)
    assert other not in (rec.get("closed_homographs") or []) and rec.get("closed_homographs") == ["MC"]
    out = ac.vocab_values_record([rec], [], [T])
    assert out["v"] in (ac.FAIL, ac.PARTIAL), other                                # never a PASS


def test_forgery_a_full_length_graha_word_in_the_declared_set_is_still_graded():
    rec = ac.vocab_grade_column(T, C, "text", _sample(["Jupiter ", "MC"]), closed=frozenset({"MC", "Jupiter "}))     # only SHORT collisions are lifted
    assert "Jupiter " not in (rec.get("closed_homographs") or [])
    assert ac.vocab_values_record([rec], [], [T])["v"] == ac.FAIL


def test_a_canonical_code_is_never_treated_as_a_homograph():
    rec = ac.vocab_grade_column(T, C, "text", _sample(["JUP", "MC"]), closed=frozenset({"JUP", "MC"}))
    assert rec["closed_homographs"] == ["MC"] and "JUP" in rec["canonical"]


def test_the_lift_is_for_the_declared_column_only():
    rec = ac.vocab_grade_column(T, "graha", "text", _sample(["MC"]))                # no closed set for another column
    assert ac.vocab_values_record([rec], [], [T])["v"] == ac.PARTIAL


# ───────────────────────── review of #3367 (Kāla): the whole-module reader and the reachable import ─────────────────────────

BASE = 'N = {"MC": "MC", "Uranus": "URANUS"}\n'


@pytest.mark.parametrize("extra, why", [
    ('if cond:\n    N = {"MC": "MC", "EVIL": "EVIL"}\n', "rebound"),                                          # reassignment inside if
    ('try:\n    N = {"EVIL": "EVIL"}\nexcept Exception:\n    pass\n', "rebound"),
    ('N, other = {"EVIL": "EVIL"}, 1\n', "rebound"),                                                         # tuple unpacking
    ('(N := {"EVIL": "EVIL"})\n', "rebound"),                                                                # walrus
    ('for N in ():\n    pass\n', "rebound"),
    ('with open("x") as N:\n    pass\n', "rebound"),
    ('from os import sep as N\n', "import"),
    ('from os import N\n', "import"),
    ('import N\n', "import"),
    ('def f():\n    global N\n    N = {"EVIL": "EVIL"}\n', "global"),
    ('def f():\n    N["EVIL"] = "EVIL"\n', "item assigned"),                                                  # in-function mutation
    ('_A = N\n_A["EVIL"] = "EVIL"\n', "used in a way"),                                                      # alias
    ('_ = N.update({"EVIL": "EVIL"})\n', "attribute"),
    ('N.setdefault("EVIL", "EVIL")\n', "attribute"),
    ('N.pop("MC")\n', "attribute"),
    ('N["EVIL"] = "EVIL"\n', "item assigned"),
    ('del N\n', "deleted"),
    ('del N["MC"]\n', "item assigned"),
    ('mutate(N)\n', "passed to a call"),
    ('f(x=N)\n', "passed to a call"),
    ('def g():\n    return N\n', "used in a way"),
    ('class N:\n    pass\n', "def / class"),
    ('try:\n    pass\nexcept Exception as N:\n    pass\n', "exception name"),
    ('match 1:\n    case N:\n        pass\n', "match pattern"),
    ('N |= {"EVIL": "EVIL"}\n', "rebound"),
    ('N.x = 1\n', "attribute"),
])
def test_forgery_any_binding_alias_or_mutation_of_the_name_anywhere_in_the_module_is_refused(tmp_path, extra, why):
    p = tmp_path / "m.py"
    p.write_text(BASE + extra, encoding="utf-8")
    with pytest.raises(ac.Unknown) as ei:
        ac.vocab_point_code_values(p, "N")
    assert why in str(ei.value) or "not provably constant" in str(ei.value) or "assigned" in str(ei.value), (extra, str(ei.value))


def test_forgery_a_chained_assignment_is_refused(tmp_path):
    p = tmp_path / "m.py"
    p.write_text('N = _B = {"MC": "MC"}\n', encoding="utf-8")
    with pytest.raises(ac.Unknown) as ei:
        ac.vocab_point_code_values(p, "N")
    assert "chained" in str(ei.value)


@pytest.mark.parametrize("use", [
    'OTHER = {}\nOTHER.update(N)\n',                       # the real ga_vargas_writer shape
    'x = len(N)\n', 'y = sorted(N)\n', 'z = "MC" in N\n', 'w = N["MC"]\n', 'v = N.get("MC")\n', 'u = list(N.keys())\n',
    'for k in N:\n    pass\n', 'q = [k for k in N]\n', 'r = dict(N)\n', 's = set(N.values())\n',
])
def test_reads_that_cannot_change_the_name_are_accepted(tmp_path, use):
    p = tmp_path / "m.py"
    p.write_text(BASE + use, encoding="utf-8")
    assert ac.vocab_point_code_values(p, "N") == frozenset({"MC", "URANUS"}), use


def test_the_real_writer_is_still_accepted_and_its_computed_sibling_still_refused():
    real = ac.ROOT / SRC
    assert "MC" in ac.vocab_point_code_values(real, NAME)
    with pytest.raises(ac.Unknown):
        ac.vocab_point_code_values(real, "BODY_TO_SUBJECT")


@pytest.mark.parametrize("writer_src", [
    "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from ga_writers.ga_vargas_writer import CANONICAL\n",
    "if False:\n    from ga_writers.ga_vargas_writer import CANONICAL\n",
    "if 0:\n    import ga_writers.ga_vargas_writer\n",
    "import typing\nif typing.TYPE_CHECKING:\n    from ga_writers.ga_vargas_writer import CANONICAL\n",
])
def test_forgery_an_import_that_never_runs_does_not_make_the_module_the_emitter(tmp_path, writer_src):
    root = tmp_path / str(abs(hash(writer_src)))
    tmp_root(root, GOOD_SRC, writer_src=writer_src)
    sets, problems = ac.vocab_point_code_sets(decl(), AID, OWN, root=root)
    assert sets == {} and "not the asset's emitter" in problems[0]


@pytest.mark.parametrize("writer_src", [
    "def run():\n    from ga_writers.ga_vargas_writer import CANONICAL\n    return CANONICAL\n",              # a lazy import inside a function is how the real writer does it
    "try:\n    from ga_writers.ga_vargas_writer import CANONICAL\nexcept ImportError:\n    CANONICAL = None\n",
    "if True:\n    from ga_writers.ga_vargas_writer import CANONICAL\n",
])
def test_a_reachable_import_still_counts(tmp_path, writer_src):
    root = tmp_path / str(abs(hash(writer_src)))
    tmp_root(root, GOOD_SRC, writer_src=writer_src)
    sets, problems = ac.vocab_point_code_sets(decl(), AID, OWN, root=root)
    assert problems == [] and sets[(T, C)] == frozenset({"MC", "URANUS", "PLUTO"}), writer_src
