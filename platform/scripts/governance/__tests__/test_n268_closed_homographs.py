"""test_n268_closed_homographs.py: SS N-268 on the Vocab.alias value detector.

reference_nakshatra_pada.pada_akshara holds the naming syllables (aksharas) of the pada, a closed vocabulary of 91 words committed as `_AKSHARAS`. Six of them (Ju Ke Ma Me Mo Ra) are spelled like two-letter graha
abbreviations and read as non-canonical spellings of a graha (FAIL). The pada's graha is the separate column `pada_lord`; these are syllables. `vocab_closed_homographs` is the CHECKED declaration of that:
the closed set is resolved from the committed constant (never typed), only a SHORT collision that is a member of it is lifted, and any other finding in the column still stands.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

T, C = "reference_nakshatra_pada", "pada_akshara"
KEY = (T, C)
OWN = {T: ([C, "pada_lord"], {C: "text", "pada_lord": "text"}, None)}
DECLS = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["assets"]
ENTRY = DECLS["bg_nakshatra"]
SYLLABLES = ["Chu", "Che", "La", "Ju", "Ke", "Ma", "Me", "Mo", "Ra"]


def _sample(values):
    return dict(values=list(values), emb=[], key_hits=[], complete=True, rows=len(values), oversized=0, deep=0, leaves=0, keys=0)


def _sets():
    return ac.vocab_closed_homograph_sets(ENTRY, "bg_nakshatra", OWN)


def test_the_closed_set_is_read_from_the_committed_constant_and_holds_the_six_collisions():
    sets, problems = _sets()
    assert problems == [] and set(sets) == {KEY}
    s = sets[KEY]
    assert len(s) == 91 and {"Ju", "Ke", "Ma", "Me", "Mo", "Ra"} <= s and "Chu" in s


def test_without_the_declaration_the_syllables_are_the_fail_the_census_reported():
    rec = ac.vocab_grade_column(T, C, "text", _sample(SYLLABLES))
    assert rec["carries"] and set(rec["spellings"]) >= {"Ju", "Ke", "Ma", "Me", "Mo", "Ra"}


def test_with_the_checked_declaration_the_syllables_are_lifted_and_named():
    sets, _ = _sets()
    rec = ac.vocab_grade_column(T, C, "text", _sample(SYLLABLES), closed=sets[KEY])
    assert not rec.get("carries") and not rec.get("weak") and not rec.get("spellings")
    assert rec["closed_homographs"] == ["Ju", "Ke", "Ma", "Me", "Mo", "Ra"]


def test_forgery_a_value_outside_the_closed_set_is_still_graded():
    sets, _ = _sets()
    rec = ac.vocab_grade_column(T, C, "text", _sample(SYLLABLES + ["Zz", "MA", "Su"]), closed=sets[KEY])
    assert rec["weak"] and rec["short_aliases"] == ["MA"]      # a case variant is not a syllable of the set: still a (weak, single) graha-alias finding
    # 'Su' IS in the resolved set (a syllable), so it is lifted; 'MA' and 'Zz' are not syllables
    assert "Su" in rec["closed_homographs"] and "MA" not in rec["closed_homographs"]


def test_forgery_a_full_length_graha_word_in_the_column_is_never_lifted_even_if_the_set_held_it():
    rec = ac.vocab_grade_column(T, C, "text", _sample(["Mars", "Ju"]), closed=frozenset({"Mars", "Ju"}))
    assert rec["carries"] and "Mars" in rec["canonical"] and "Ju" not in rec.get("spellings", []) and rec["closed_homographs"] == ["Ju"]


def test_a_declaration_is_refused_when_the_column_is_not_a_closed_column_with_values_from():
    e = copy.deepcopy(ENTRY)
    e["prose_none"]["closed_columns"] = [c for c in e["prose_none"]["closed_columns"] if c["column"] != C]
    sets, problems = ac.vocab_closed_homograph_sets(e, "bg_nakshatra", OWN)
    assert sets == {} and problems and "closed column" in problems[0]
    # a typed `values` list (no committed constant) is not a basis either
    e2 = copy.deepcopy(ENTRY)
    for c in e2["prose_none"]["closed_columns"]:
        if c["column"] == C:
            c.pop("values_from")
            c["values"] = ["Chu", "Ju"]
    sets, problems = ac.vocab_closed_homograph_sets(e2, "bg_nakshatra", OWN)
    assert sets == {} and problems


def test_a_declaration_is_refused_for_a_table_not_owned_or_a_column_not_present_and_voids_all():
    assert ac.vocab_closed_homograph_sets(ENTRY, "bg_nakshatra", {})[0] == {}
    assert ac.vocab_closed_homograph_sets(ENTRY, "bg_nakshatra", {T: (["pada_lord"], {}, None)})[0] == {}
    assert ac.vocab_closed_homograph_sets(ENTRY, "bg_nakshatra", {T: (None, None, None)})[0] == {}


def test_a_malformed_declaration_fails_validation():
    e = copy.deepcopy(ENTRY)
    e["vocab_closed_homographs"][0]["extra"] = 1
    assert ac.vocab_closed_homographs_problem(e)
    e = copy.deepcopy(ENTRY)
    e["vocab_closed_homographs"] = e["vocab_closed_homographs"] * 2
    assert "twice" in ac.vocab_closed_homographs_problem(e)
    e = copy.deepcopy(ENTRY)
    e["vocab_closed_homographs"][0]["evidence"] = "no/such/file.py:1"
    assert ac.vocab_closed_homographs_problem(e)


def test_the_committed_declarations_validate_and_the_asset_carries_the_declaration():
    assert ENTRY["vocab_closed_homographs"][0]["column"] == C
    ac.validate_vocab_closed_homographs_declaration("bg_nakshatra", ENTRY)


def test_the_record_names_the_lifted_syllables_and_is_no_longer_a_fail():
    sets, _ = _sets()
    recs = [ac.vocab_grade_column(T, C, "text", _sample(SYLLABLES), closed=sets[KEY]),
            ac.vocab_grade_column(T, "pada_lord", "text", _sample(["mars", "venus"]))]
    out = ac.vocab_values_record(recs, [], [T])
    assert out["v"] != ac.FAIL and out["vocab_values"]["closed_homographs"] == {f"{T}.{C}": ["Ju", "Ke", "Ma", "Me", "Mo", "Ra"]}


def test_the_refusal_record_is_no_detector_and_names_the_problem():
    r = ac.vocab_closed_homographs_refuse({"vocab_values": {"x": 1}}, ["a: b"], ENTRY)
    assert r["v"] == ac.NO_DET and "a: b" in r["measured"] and r["declaration_disagreements"][0]["field"] == "vocab_closed_homographs"
