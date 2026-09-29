"""§12.10b — pure unit tests for the citation-derived stamp helpers (no database).

Each case pins a direction: doubt must resolve toward "uncited", never toward
"cited" (CLAUDE.md §N.7 item 6).
"""
from __future__ import annotations

import pytest

from services.ka_vedha_gochara.logic import (
    HOUSE_VEDHA,
    LATTA,
    SARVATOBHADRA,
    corpus_verifiable_for,
    house_vedha_uncited_extension,
    is_unsourced_citation,
    source_qualification_for,
)

VERSE = "Phaladipika Adh. XXVI, Sloka 3 (PG322:C1)"
UNSRC = "UNSOURCED — no house-transit vedha doctrine for the nodes (ruling N-14)"
# The L0 UNSOURCED reason text may or may not name the struck source; the stamp
# must not depend on that incidental wording.
UNSRC_NO_BPHS_WORDING = "UNSOURCED"


@pytest.mark.parametrize("citation", [UNSRC, UNSRC_NO_BPHS_WORDING, "unsourced", "Unsourced (x)", "  UNSOURCED", None, "", "   "])
def test_unsourced_or_missing_is_uncited(citation):
    assert is_unsourced_citation(citation) is True
    assert house_vedha_uncited_extension(citation) is True
    assert source_qualification_for(HOUSE_VEDHA, None, classical_citation=citation) == "unsourced"
    assert corpus_verifiable_for(HOUSE_VEDHA, classical_citation=citation) is False


@pytest.mark.parametrize("citation", [VERSE, "Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)", "BPHS Ch.29 (Gochara Phala — Transit Results)"])
def test_cited_rules_are_not_marked_uncited(citation):
    assert is_unsourced_citation(citation) is False
    assert house_vedha_uncited_extension(citation) is False
    assert source_qualification_for(HOUSE_VEDHA, None, classical_citation=citation) == "verse_cited"


def test_struck_marker_still_blocks_corpus_verifiable_but_stays_verse_cited():
    """The refuted-source case is a separate axis: cited, but not verifiable."""
    bphs = "BPHS Ch.29 (Gochara Phala — Transit Results)"
    assert corpus_verifiable_for(HOUSE_VEDHA, classical_citation=bphs) is False
    assert corpus_verifiable_for(HOUSE_VEDHA, classical_citation=VERSE) is True


def test_unsourced_wording_that_does_not_name_bphs_still_reads_false():
    """Guards the exact hole: a marker-only test returns True for this string."""
    assert "BPHS Ch.29" not in UNSRC_NO_BPHS_WORDING
    assert corpus_verifiable_for(HOUSE_VEDHA, classical_citation=UNSRC_NO_BPHS_WORDING) is False


def test_source_qualification_stays_backward_compatible_for_other_kinds():
    # Two-positional-argument call shape used elsewhere must keep working.
    assert source_qualification_for(LATTA, None) == "verse_cited"
    assert source_qualification_for(SARVATOBHADRA, "algorithmic_approximation") == "algorithmic_approximation"
    assert source_qualification_for(SARVATOBHADRA, "db_sourced_grid") == "verse_cited"


def test_house_vedha_without_citation_arg_is_now_unsourced_not_verse_cited():
    """The OLD behaviour returned 'verse_cited' with no citation supplied. That was
    the defect: an absent source promoted to a cited one."""
    assert source_qualification_for(HOUSE_VEDHA, None) == "unsourced"
