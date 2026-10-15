"""bg_doshas formation_rule_jsonb: ONE spelling family (migration 1361).

The census cell Vocab.alias read the column MIXED: lowercase ontology-id graha leaves beside display-name nakshatra leaves, six of them registered non-canonical aliases and four unrecognised
spellings. This is the offline detector for the claim "the seed no longer mixes families": every graha / nakshatra string leaf of the final 66 rows (and of the authored 79-row seed list) is,
under the census' OWN classifier (`asset_census.vocab_classify`, read WITHOUT the live bg_ontology alias set, so a registered alias would still fail), the exact canonical spelling, and the
leaves share the `name` spelling family. A dict KEY is never a leaf and is never changed.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

from brahmagyan import l0_doshas as L

_REPO = pathlib.Path(__file__).resolve().parents[4]
_spec = importlib.util.spec_from_file_location("_asset_census_for_1361", _REPO / "platform" / "scripts" / "governance" / "asset_census.py")
ac = importlib.util.module_from_spec(_spec)
sys.modules["_asset_census_for_1361"] = ac
_spec.loader.exec_module(ac)

OLD_NAKSHATRA = {"Ashvini": "Ashwini", "Mrigashira": "Mrigasira", "Mula": "Moola", "Svati": "Swati", "Uttaraphalguni": "Uttara Phalguni", "Uttarashadha": "Uttara Ashadha",
                 "Purvaphalguni": "Purva Phalguni", "Purvashadha": "Purva Ashadha", "Purvabhadrapada": "Purva Bhadrapada", "Uttarabhadrapada": "Uttara Bhadrapada"}
OLD_GRAHA_IDS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu", "lagna"}
FINAL = L.pass2_doshas()


def _leaves(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from _leaves(v)
    elif isinstance(o, list):
        for v in o:
            yield from _leaves(v)
    elif isinstance(o, str):
        yield o


def _keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _keys(v)


@pytest.mark.parametrize("rows", [FINAL, L.DOSHAS], ids=["final66", "authored79"])
def test_no_old_spelling_survives_as_a_leaf(rows):
    leaves = {s for r in rows for s in _leaves(r["formation_rule_jsonb"])}
    assert not (leaves & OLD_GRAHA_IDS) and not (leaves & set(OLD_NAKSHATRA))


def test_every_vocabulary_leaf_is_the_exact_canonical_spelling_in_one_family():
    vocab = [s for r in FINAL for s in _leaves(r["formation_rule_jsonb"]) if ac.vocab_classify(s) is not None]
    assert len(set(vocab)) >= 30                                                 # the detector must see the leaves (not a vacuous pass)
    kinds = {s: ac.vocab_classify(s)["kind"] for s in set(vocab)}
    assert all(k == "canonical" for k in kinds.values()), {s: k for s, k in kinds.items() if k != "canonical"}
    assert ac.vocab_families(frozenset(vocab)) == frozenset({"name"})            # the census' own `mixed` test: bool(canon) and not families


def test_the_old_spellings_would_have_been_caught():
    """The detector measures the claim: the previous leaves read MIXED (no common family) / non-canonical, so this test fails on the previous seed."""
    assert ac.vocab_families(frozenset({"mars", "Ardra"})) == frozenset()
    assert ac.vocab_classify("Ashvini")["kind"] != "canonical" and ac.vocab_classify("Mula")["kind"] != "canonical"
    assert ac.vocab_classify("Purvaphalguni") is None                            # unrecognised: invisible to the census before this change


def test_nakshatra_leaves_are_the_ontology_canonical_names():
    nak = {s for r in FINAL for s in _leaves(r["formation_rule_jsonb"]) if "nakshatra" in (ac.vocab_classify(s) or {}).get("classes", [])}
    assert {"Ashwini", "Mrigasira", "Moola", "Swati", "Uttara Phalguni", "Uttara Ashadha", "Purva Phalguni", "Purva Ashadha", "Purva Bhadrapada", "Uttara Bhadrapada"} <= nak
    assert len(nak) == 27                                                        # the three nadi lists hold all 27 nakshatras, each once, each canonical


def test_graha_leaves_are_the_l1_display_names():
    expect = {"manglik": {"planet": "Mars", "houses": [1, 2, 4, 7, 8, 12], "reference": ["Lagna", "Moon", "Venus"]}}
    for cid, rule in expect.items():
        assert {r["canonical_id"]: r for r in FINAL}[cid]["formation_rule_jsonb"] == rule
    assert {r["canonical_id"]: r for r in FINAL}["guru_chandal"]["formation_rule_jsonb"] == {"conjunction": ["Jupiter", "Rahu"]}
    assert {r["canonical_id"]: r for r in FINAL}["grahan"]["formation_rule_jsonb"]["conjunction"] == [["Sun", "Rahu"], ["Sun", "Ketu"], ["Moon", "Rahu"], ["Moon", "Ketu"]]


def test_only_leaves_changed_keys_are_untouched():
    keys = {k for r in FINAL for k in _keys(r["formation_rule_jsonb"])}
    assert "mercury_retrograde" in keys and "venus_retrograde" in keys           # lowercase keys inside combust_dosha.orbs_degrees stay keys
    orbs = {r["canonical_id"]: r for r in FINAL}["combust_dosha"]["formation_rule_jsonb"]["orbs_degrees"]
    assert "moon" in orbs or "Moon" in orbs
