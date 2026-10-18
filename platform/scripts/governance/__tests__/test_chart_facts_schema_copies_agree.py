"""
test_chart_facts_schema_copies_agree.py -- SS N-568: CHART_FACTS_SCHEMA.json exists three times
(00_ARCHITECTURE/ = governance-canonical, platform/scripts/governance/ = its byte-identical mirror,
platform/python-sidecar/ga_writers/ = the writers' own, different-shaped copy). The two governance copies must
stay byte-identical, and every nakshatra enum in all three must be exactly the L0 lexicon's 27 names
(Mrigasira / Moola / Dhanishtha) -- never the adapter's spellings.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "platform" / "python-sidecar"))

from brahmagyan.nakshatra_vocabulary import CANONICAL_NAKSHATRA_NAMES, LEGACY_L1_SPELLINGS, normalize_nakshatra  # noqa: E402

GOVERNANCE_CANONICAL = REPO / "00_ARCHITECTURE" / "CHART_FACTS_SCHEMA.json"
GOVERNANCE_MIRROR = REPO / "platform" / "scripts" / "governance" / "CHART_FACTS_SCHEMA.json"
WRITERS_COPY = REPO / "platform" / "python-sidecar" / "ga_writers" / "CHART_FACTS_SCHEMA.json"
COPIES = (GOVERNANCE_CANONICAL, GOVERNANCE_MIRROR, WRITERS_COPY)
CANON = set(CANONICAL_NAKSHATRA_NAMES)
NAK_MARKERS = CANON | set(LEGACY_L1_SPELLINGS)


def _nakshatra_enums(node, path=""):
    """Every `enum` list that names at least one nakshatra (canonical or legacy spelling), with its JSON path."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "enum" and isinstance(v, list) and any(x in NAK_MARKERS for x in v):
                yield path, v
            else:
                yield from _nakshatra_enums(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _nakshatra_enums(v, f"{path}[{i}]")


def test_the_two_governance_copies_are_byte_identical():
    assert GOVERNANCE_CANONICAL.read_bytes() == GOVERNANCE_MIRROR.read_bytes()


def test_every_nakshatra_enum_in_every_copy_normalises_exactly_onto_the_lexicons_27_names():
    """The writers' copy lists the 27 names; the governance copies list them plus their underscore variants
    ('Purva_Phalguni'). Every value must be a registered spelling of a canonical name (through the ONE
    normaliser), the canonical names themselves must all be present, and no adapter spelling may remain."""
    for copy in COPIES:
        enums = dict(_nakshatra_enums(json.loads(copy.read_text(encoding="utf-8"))))
        assert enums, f"{copy}: no nakshatra enum found"
        for path, values in enums.items():
            assert {normalize_nakshatra(v) for v in values} == CANON, (copy.name, path)
            assert not set(values) & set(LEGACY_L1_SPELLINGS), (copy.name, path, sorted(set(values) & set(LEGACY_L1_SPELLINGS)))


def test_the_three_copies_agree_on_the_normalised_nakshatra_enum_set():
    sets = {f"{copy.parent.name}/{copy.name}": {frozenset(normalize_nakshatra(v) for v in values) for _p, values in _nakshatra_enums(json.loads(copy.read_text(encoding="utf-8")))}
            for copy in COPIES}
    assert all(s == {frozenset(CANON)} for s in sets.values()), {k: [sorted(x ^ CANON) for x in v] for k, v in sets.items()}
