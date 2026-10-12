"""
test_nakshatra_vocabulary_alias_table_golden.py -- the FULL alias table is byte-identical before and after the leaf change.

Engine condition on #3460: not counts -- the complete alias -> canonical map (105 entries), the 8-token ambiguity set, the
3 suppressed registrations, the 27 canonical names and the 3 legacy L1 spellings. The golden
(tests/fixtures/nakshatra_vocabulary_alias_table.golden.json) was generated from the PRE-leaf head b5aad5a92 (the
vocabulary importing l0_nakshatra / l0_ontology directly); the leaf head must reproduce it exactly. Any intentional
change to the alias table must regenerate this golden in the same change and say why.
"""
from __future__ import annotations

import json
import pathlib
import sys

SIDECAR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIDECAR))

from brahmagyan import nakshatra_vocabulary as v  # noqa: E402

GOLDEN = pathlib.Path(__file__).resolve().parent / "fixtures" / "nakshatra_vocabulary_alias_table.golden.json"


def _live_table() -> dict:
    return {
        "canonical_names": list(v.CANONICAL_NAKSHATRA_NAMES),
        "legacy_l1_spellings": dict(v.LEGACY_L1_SPELLINGS),
        "alias_to_canonical": dict(sorted(v.NAKSHATRA_SYNONYMS.items())),
        "ambiguous_bare_tokens": sorted(v.AMBIGUOUS_BARE_TOKENS),
        "suppressed_ambiguous_aliases": {k: list(val) for k, val in sorted(v.SUPPRESSED_AMBIGUOUS_ALIASES.items())},
    }


def test_the_golden_was_generated_from_the_pre_leaf_head():
    g = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert "b5aad5a92" in g["_source"] and "pre-leaf" in g["_source"]
    assert len(g["alias_to_canonical"]) == 105 and len(g["ambiguous_bare_tokens"]) == 8 and len(g["suppressed_ambiguous_aliases"]) == 3


def test_the_full_alias_table_is_byte_identical_to_the_pre_leaf_golden():
    g = json.loads(GOLDEN.read_text(encoding="utf-8")); g.pop("_source")
    live = _live_table()
    canon = lambda d: json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True)  # noqa: E731
    assert canon(live) == canon(g), "the normaliser's alias table changed; if intended, regenerate the golden and say why"
    # and every one of the 105 aliases still resolves to exactly its golden canonical through the public normaliser
    for alias_key, canonical in g["alias_to_canonical"].items():
        assert v._SYNONYMS[alias_key] == canonical
    for token in g["ambiguous_bare_tokens"]:
        try:
            v.normalize_nakshatra(token)
        except v.AmbiguousNakshatraError:
            continue
        raise AssertionError(f"{token!r} no longer raises AmbiguousNakshatraError")
