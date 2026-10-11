"""bo_laksana does not COMPOSE nakshatra names: every nakshatra spelling in its rows is an L1 value
it forwards (CLAUDE.md section N.5), so L1's spelling reaches the signal unchanged.

SS N-458 asked for bo_laksana's nakshatra spellings to be mapped to the L0 bg_nakshatra canonical form
(`Moola`, `Dhanishtha`, `Mrigasira`) the way the graha names were.  Unlike the graha code paths
(`_SIGN_LORD`, `_DOSHA_GROUP_GRAHA`, `_GRAHA_NAME_MAP`) there is no composition site here: the writer has no
nakshatra literal, table or lookup.  The non-canonical forms in bodha_msr_signals ("Mula", "Dhanishta",
"Mrigashira") are the spelling chart_facts carries, written by L1 from `pyjhora_adapter._names`.  Re-spelling
them at L2 would be exactly the L2 restatement of an L1 value that section N.5 forbids.

This file pins that claim with detectors that can read false:
  * the canonical-vs-L1 mismatch set is computed from the two tables (not asserted by hand);
  * an AST scan finds no nakshatra spelling among bo_laksana's string constants (a composed literal would fail it);
  * all 27 L1 spellings pass through `_build_signal_row` unchanged (a re-spelling at L2 would fail it);
  * an unknown token passes through unchanged.

No DB.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from brahmagyan import l0_ontology
from brahmagyan.l0_nakshatra import NAKSHATRAS_ENRICHED
from pipeline.orchestrator.writers import bo_laksana as bo
from pyjhora_adapter._names import NAKSHATRA_NAMES

_NOW = "2026-10-11T00:00:00+00:00"
_ONTOLOGY = [e for e in l0_ontology.ENTITIES if e["entity_class"] == "nakshatra"]
_CANON = {i: e["canonical_name_en"] for i, e in enumerate(_ONTOLOGY, 1)}


def test_the_two_canonical_l0_tables_agree_on_all_27():
    assert len(_ONTOLOGY) == 27
    for i, row in enumerate(NAKSHATRAS_ENRICHED[:27], 1):
        assert row["nakshatra_id"] == i
        assert row["name_en"] == _CANON[i]


def test_the_mismatch_set_between_the_l1_adapter_and_the_l0_lexicon_is_exactly_three():
    """Computed, not asserted by hand: the L1 adapter's 27 names against L0 bg_nakshatra's canonical_name_en."""
    mismatch = {i: (NAKSHATRA_NAMES[i], _CANON[i]) for i in _CANON if NAKSHATRA_NAMES[i] != _CANON[i]}
    assert mismatch == {
        5: ("Mrigashira", "Mrigasira"),
        19: ("Mula", "Moola"),
        23: ("Dhanishta", "Dhanishtha"),
    }


def _every_known_nakshatra_spelling() -> set[str]:
    """Casefolded: the L1 adapter's names, the L0 canonical names (English and Sanskrit), the ontology
    synonyms and the bg_nakshatra alternate names."""
    out: set[str] = set(NAKSHATRA_NAMES[1:])
    for i, e in enumerate(_ONTOLOGY, 1):
        out |= {e["canonical_name_en"], e["canonical_name_sa"], *e["synonyms"]}
        out |= {NAKSHATRAS_ENRICHED[i - 1]["name_en"], *NAKSHATRAS_ENRICHED[i - 1]["alt_names"]}
    return {s.casefold() for s in out if isinstance(s, str) and s.strip()}


def test_bo_laksana_source_holds_no_nakshatra_spelling_constant():
    """A composed nakshatra literal / table / lookup key in the writer would be a string constant equal to one
    of the known spellings; the writer has none (the nakshatra values in its rows are all forwarded from L1)."""
    spellings = _every_known_nakshatra_spelling()
    tree = ast.parse(Path(bo.__file__).read_text(encoding="utf-8"))
    hits = sorted(
        (n.lineno, n.value) for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.strip().casefold() in spellings
    )
    assert hits == [], f"bo_laksana composes a nakshatra spelling at {hits}"


def _fact(fid, cat, key, subject, *, text=None, fvj=None):
    return {
        "fact_id": fid, "fact_category": cat, "fact_key": key, "fact_subject": subject,
        "fact_value_text": text, "fact_value_num": None, "ayanamsha_id": "lahiri_chitrapaksha",
        "source_calculation": "ga_panchanga", "formula_id": None,
        "fact_value_jsonb": json.dumps(fvj) if fvj is not None else None,
    }


def _row(fact):
    row = bo._build_signal_row(fact, "chart-1", "b1", {}, {}, {}, _NOW, valid_fact_ids={fact["fact_id"]})
    return row, json.loads(row["configuration_jsonb"])


@pytest.mark.parametrize("number", range(1, 28))
def test_every_l1_nakshatra_spelling_is_forwarded_unchanged(number):
    name = NAKSHATRA_NAMES[number]
    # a panchanga fact carrying the nakshatra as its value text
    row, cfg = _row(_fact(f"p{number}", "panchanga_nakshatra_moon", "nakshatra", "MOON",
                          text=name, fvj={"nakshatra": name, "janma_nakshatra": name}))
    assert cfg["fact_value_text"] == name
    assert cfg["nakshatra"] == name
    assert cfg["janma_nakshatra"] == name
    assert f"value_text={name}" in row["signal_summary_text"]
    assert f"= {name}" in row["signal_headline_text"]
    # and a graha_position fact carrying it as a jsonb leaf
    _, cfg2 = _row(_fact(f"g{number}", "graha_position", "nakshatra", "MOON", text=name,
                         fvj={"graha": "MOON", "nakshatra": name}))
    assert cfg2["nakshatra"] == name


@pytest.mark.parametrize("token", ["Nonexistent", "Moola ", "dhanishta", "MULA", ""])
def test_unknown_or_odd_tokens_are_forwarded_unchanged_too(token):
    _, cfg = _row(_fact("u1", "graha_position", "nakshatra", "MOON", fvj={"graha": "MOON", "nakshatra": token}))
    assert cfg["nakshatra"] == token
