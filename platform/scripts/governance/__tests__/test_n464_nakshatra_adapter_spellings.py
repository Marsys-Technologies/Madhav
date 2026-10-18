"""test_n464_nakshatra_adapter_spellings.py: SS N-464 owner decision (1): the nakshatra L1 canonicalisation is deferred, so the three adapter spellings the L1 writers emit
(pyjhora_adapter/_names.py:49-57: Mrigashira, Mula, Dhanishta) must be honest ALIASES of the canonical lexicon terms (l0_ontology.py: Mrigasira, Moola, Dhanishtha), no wider.

The census accepts a non-canonical spelling as canonical only when it is a REGISTERED bg_ontology alias (N-233 R2: the exact canonical_name_sa or synonym of a brahma_ontology row; the set is read live from
the table that brahmagyan/l0_ontology.py ENTITIES seeds). There is no declaration that registers one. Mrigashira (canonical_name_sa of nak_05) and Mula (canonical_name_sa of nak_19) are registered already;
Dhanishta was the one adapter spelling the lexicon did not know at all (vocab_classify -> None: ungraded in a flat column, 'not a nakshatra term at all' at a vocab_json_kinds path).
Proven WITHOUT a database: the registered set is the repo's own offline stand-in (vocab_alias_report.offline_registered, the ENTITIES parsed exactly as the live JSON is)."""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
import vocab_alias_report as var  # noqa: E402

ADAPTER = ("Mrigashira", "Mula", "Dhanishta")                 # the three adapter spellings that differ from the canonical lexicon terms
CANONICAL = {"Mrigashira": "Mrigasira", "Mula": "Moola", "Dhanishta": "Dhanishtha"}


@pytest.fixture(autouse=True)
def offline_registered_set(monkeypatch):
    reg, label = var.offline_registered()
    assert label.startswith("OFFLINE STAND-IN")
    monkeypatch.setattr(ac, "_VOCAB_REGISTERED", reg)
    monkeypatch.setattr(ac, "vocab_registered_load", lambda *a, **k: ac._VOCAB_REGISTERED)


def _adapter_names():
    spec = importlib.util.spec_from_file_location("_n464_names", HERE.parents[2] / "python-sidecar" / "pyjhora_adapter" / "_names.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.NAKSHATRA_NAMES[1:]


@pytest.mark.parametrize("spelling", ADAPTER)
def test_each_adapter_spelling_is_a_registered_nakshatra_alias_not_an_unknown_word(spelling):
    r = ac.vocab_classify(spelling)
    assert r is not None, f"{spelling!r} is no vocabulary term at all (the lexicon does not know it)"
    assert r["kind"] == "registered" and r["classes"] == ["nakshatra"], (spelling, r)


# The two tests below use the vocab_json_kinds path grader (PR #3421, `vocab_path_kind_violations`), which exists only where that form is merged (the integration tree).
# On a tree without it they are SKIPPED, loudly, with this reason; they are not weakened where the form exists.
needs_json_kinds = pytest.mark.skipif(not hasattr(ac, "vocab_path_kind_violations"), reason="vocab_json_kinds (PR #3421) is not in this tree")


@needs_json_kinds
@pytest.mark.parametrize("spelling", ADAPTER)
def test_each_adapter_spelling_passes_a_declared_nakshatra_path_in_the_registered_alias_family(spelling):
    bad, ok = ac.vocab_path_kind_violations([spelling], "nakshatra", "registered_alias")
    assert bad == [] and ok == [spelling]


@needs_json_kinds
@pytest.mark.parametrize("spelling", ADAPTER)
def test_an_adapter_spelling_is_still_not_in_the_canonical_name_family(spelling):
    """Honest: a registered alias is not the canonical spelling. At a path declared family 'name' it is a violation, naming the canonical term the lexicon spells."""
    bad, _ = ac.vocab_path_kind_violations([spelling], "nakshatra", "name")
    assert len(bad) == 1 and "registered bg_ontology alias" in bad[0]
    assert ac.vocab_classify(CANONICAL[spelling])["kind"] == "canonical"


def test_the_27_adapter_names_resolve_and_exactly_the_three_are_registered_aliases():
    names = _adapter_names()
    assert len(names) == 27
    kinds = {n: (ac.vocab_classify(n) or {}).get("kind") for n in names}
    assert all(k in ("canonical", "registered") for k in kinds.values()), {n: k for n, k in kinds.items() if k not in ("canonical", "registered")}
    assert sorted(n for n, k in kinds.items() if k == "registered") == sorted(ADAPTER)


@pytest.mark.parametrize("near", ["Dhanisht", "Dhanishtaa", "Dhanista", "Mrigshira", "Mrigashiraa", "Moolaa", "Mulaa", "dhanishta ", "Dhanishta_", "Dhanishta in 7th", "Danishta"])
def test_acceptance_is_not_widened_beyond_the_registered_spellings(near):
    """Near-spellings the three adapter names must NOT drag in: they stay no-term or non-canonical spellings, never registered."""
    r = ac.vocab_classify(near)
    assert r is None or r["kind"] != "registered", (near, r)


def test_the_registered_set_gained_exactly_the_one_spelling_dhanishta():
    """The lexicon edit is one synonym on nak_23_dhanishtha: the registered nakshatra forms of that row are its English and Sanskrit names plus its synonyms and nothing else."""
    reg = ac.vocab_registered_set()
    nak23 = sorted(k for k, v in reg.items() if "nak_23_dhanishtha" in v["ids"])
    assert nak23 == ["avittam", "dhanishta", "dhanishtha", "dhanistha", "sravishtha"]
