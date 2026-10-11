"""test_n431_rev28_registry_merge.py: the ONE revision-28 bump (SS N-429/N-431) merged R1's DATA constants into the registry; this pins that the merge is complete and has not drifted.

R1 (corpus_derived) left three constants as data (CORPUS_DERIVED_NA_CAUSES, CORPUS_DERIVED_NA_RULE_DECISIONS, CORPUS_DERIVED_APPLICABILITY_ADDITIONS). The bump copied them into NA_CAUSES, NA_RULE_DECISIONS and the
five criteria's applicability text by exact edit; if the constants or the registry change without the other, one of these fails. Offline."""
from __future__ import annotations

import ast
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

# the revision each bumped criterion carries at 28 (previous revision + exactly ONE, whatever the number of sentences appended)
REV28 = {"Vocab.identity": 3, "Idem.pattern": 5, "Build.count_integrity": 4, "Null.schema_default": 10, "Null.blank_rows": 10,
         "Narr.checkable": 7, "Narr.agree": 8, "Narr.fidelity_test": 7, "Vocab.alias": 9}


def test_the_registry_revision_is_28_and_each_bumped_criterion_moved_by_exactly_one():
    assert ac.REGISTRY_REVISION == 28
    for crit, rev in REV28.items():
        assert ac.CRITERION_REGISTRY[crit]["revision"] == rev, crit


def test_the_corpus_derived_cause_is_registered_for_exactly_the_five_criteria():
    got = {c for c, causes in ac.NA_CAUSES.items() if "corpus-derived" in causes}
    assert got == set(ac.CORPUS_DERIVED_NA_CRITERIA)
    for crit, cs in ac.CORPUS_DERIVED_NA_CAUSES.items():
        assert set(cs) <= set(ac.NA_CAUSES[crit])


def test_the_corpus_derived_rule_decisions_are_declared_verbatim():
    for rid, text in ac.CORPUS_DERIVED_NA_RULE_DECISIONS.items():
        assert ac.NA_RULE_DECISIONS.get(rid) == text, rid
    ac.validate_na_rule_decisions()


def test_the_corpus_derived_applicability_text_is_appended_verbatim_to_each_criterion():
    for crit, tail in ac.CORPUS_DERIVED_APPLICABILITY_ADDITIONS.items():
        assert ac.CRITERION_REGISTRY[crit]["applicability"].endswith(tail), crit
        assert ac.CRITERION_REGISTRY[crit]["applicability"].count("corpus-derived") >= 1


def test_the_w2_w9_and_ownership_sentences_are_in_the_registry():
    reg = ac.CRITERION_REGISTRY
    assert "`logical_key`" in reg["Vocab.identity"]["applicability"] and "pg_get_viewdef" in reg["Vocab.identity"]["applicability"]
    assert "passive_projection" in reg["Idem.pattern"]["applicability"] and "passive_projection" in reg["Build.count_integrity"]["applicability"]
    for crit in ("Null.schema_default", "Null.blank_rows"):
        assert "literal_max" in reg[crit]["applicability"] and "`closed`" in reg[crit]["applicability"], crit
    for crit in ("Narr.checkable", "Null.blank_rows"):
        assert "object-key wildcard" in reg[crit]["applicability"], crit
    for crit in ("Vocab.alias", "Narr.checkable"):
        assert "fact_category_ownership" in reg[crit]["applicability"] and "ownership-join-shape-not-recognised" in reg[crit]["applicability"], crit


def test_the_vocab_json_extensions_and_the_mode_wording_are_in_the_registry():
    reg = ac.CRITERION_REGISTRY
    for adds in (ac.VOCAB_JSON_GROUPS_APPLICABILITY_ADDITIONS, ac.VOCAB_JSON_KEYS_APPLICABILITY_ADDITIONS, ac.VOCAB_JSON_IDENTIFIERS_APPLICABILITY_ADDITIONS):
        assert adds["Vocab.alias"] in reg["Vocab.alias"]["applicability"]
    for crit in ac.CORPUS_DERIVED_NA_CRITERIA_BESIDE_PROSE:                 # mode 2 (SS N-457): the only cells the form may release beside a declared prose_fields
        assert "Mode 2" in reg[crit]["applicability"], crit
    for crit in set(ac.CORPUS_DERIVED_NA_CRITERIA) - set(ac.CORPUS_DERIVED_NA_CRITERIA_BESIDE_PROSE):
        assert "ONLY in mode 1" in reg[crit]["applicability"] and "Mode 2" not in reg[crit]["applicability"].split("N-431 (REGISTRY_REVISION 28)")[-1].split("This cell")[0], crit


def test_the_changed_file_parses_under_the_311_grammar():
    ast.parse((HERE.parent / "asset_census.py").read_text(encoding="utf-8"), feature_version=(3, 11))
    ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"), feature_version=(3, 11))
