"""Tests for ka_kota_chakra (ṢAḌ-DARŚANA W3, registry item 16 — Kota-Chakra fort chart).

TDD: written before services/ka_kota_chakra/logic.py existed. Pure-logic unit
tests only here (no DB) — mirrors tests/l3/test_ka_gochara_resonance.py's split
between DB-free helper tests and the writer's own DB-touching behaviour.

Spec: SHAD_DARSHANA_BRIEF_v2_0.md item 16 — "the fort chakra: transiting grahas
mapped to the kota's stambha/madhya/prakara/bahya rings relative to the janma
nakshatra, with entry/exit and the attack/defence reading."

Ring table citation: this classical technique is NOT present in the ingested
corpus as of this writing (checked: no `brahma_*` ontology row, no
`bg_muhurta_lattice`/`bg_parihara_rules` factor census entry for "kota" —
those tables are items 36/41, not yet built at W3-parallel dispatch time).
Per the W3K citation-source hierarchy (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K
Gate — "(iii) published reader examples transcribed into a committed fixture
file; if only (iii) is available, the item is VERIFIED against the fixture
and the corpus gap is filed as an ingestion work item"), the ring table below
is transcribed from a secondary published description (cited in
services/ka_kota_chakra/logic.py's own docstring) and is treated as tier-(iii)
evidence: the writer marks it honestly (not a primary-corpus citation), and
this is filed as an ADJUDICATION-PENDING corpus-ingestion gap in the PR, not
silently upgraded to `classical_citation` status.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_kota_chakra.logic import (
    ALL_RING_NAMES,
    STAMBHA_COUNTS,
    DURGANTARA_COUNTS,
    PRAKARA_COUNTS,
    BAHYA_COUNTS,
    count_from_janma,
    ring_for_count,
    attack_defence_reading,
    detect_ring_runs,
    NATURAL_MALEFICS,
    NATURAL_BENEFICS,
)


class TestRingTableInvariant:
    """The four ring sets must partition {1..27} exactly — no gap, no overlap.
    This is the single most important correctness property of the whole
    writer: if this invariant breaks, every downstream ring assignment is
    silently wrong for at least one nakshatra-count."""

    def test_partition_covers_1_to_27_exactly_once(self):
        all_counts = STAMBHA_COUNTS | DURGANTARA_COUNTS | PRAKARA_COUNTS | BAHYA_COUNTS
        assert all_counts == set(range(1, 28))
        total_len = (
            len(STAMBHA_COUNTS) + len(DURGANTARA_COUNTS) + len(PRAKARA_COUNTS) + len(BAHYA_COUNTS)
        )
        assert total_len == 27  # disjoint — no count double-counted

    def test_stambha_is_the_four_pillar_positions(self):
        # Transcribed source (see logic.py docstring): 4th, 11th, 18th, 25th from janma.
        assert STAMBHA_COUNTS == {4, 11, 18, 25}

    def test_janma_itself_falls_in_bahya(self):
        # count=1 (the janma nakshatra itself, 0 nakshatras away) is not listed in any of
        # stambha/durgantara/prakara in the source table, so it falls to bahya by the
        # partition — see logic.py docstring for the explicit disclosure of this point.
        assert ring_for_count(1) == "bahya"


class TestCountFromJanma:
    def test_same_nakshatra_as_janma_is_count_1(self):
        assert count_from_janma(nak_idx_0based=5, janma_nak_idx_0based=5) == 1

    def test_next_nakshatra_is_count_2(self):
        assert count_from_janma(nak_idx_0based=6, janma_nak_idx_0based=5) == 2

    def test_wraps_around_27(self):
        # janma = index 26 (Revati), graha at index 0 (Ashwini) -> 2nd from janma
        assert count_from_janma(nak_idx_0based=0, janma_nak_idx_0based=26) == 2

    def test_wraps_backward(self):
        # janma = index 0 (Ashwini), graha at index 26 (Revati) -> 27th from janma
        assert count_from_janma(nak_idx_0based=26, janma_nak_idx_0based=0) == 27

    def test_full_cycle_produces_every_count_exactly_once(self):
        janma = 12
        counts = {count_from_janma(nak_idx_0based=i, janma_nak_idx_0based=janma) for i in range(27)}
        assert counts == set(range(1, 28))


class TestRingForCount:
    def test_out_of_range_raises(self):
        import pytest
        with pytest.raises(ValueError):
            ring_for_count(0)
        with pytest.raises(ValueError):
            ring_for_count(28)

    def test_all_ring_names_are_the_four_classical_rings(self):
        assert ALL_RING_NAMES == ("stambha", "durgantara", "prakara", "bahya")


class TestNaturalBeneficMaleficClassification:
    # Matches the codebase's own repeated convention (ga_sensitive_degree_writer.py,
    # ga_yoga_writer.py, ga_structural_writer.py) — not invented for this writer.
    def test_malefics(self):
        assert NATURAL_MALEFICS == {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

    def test_benefics(self):
        assert NATURAL_BENEFICS == {"Moon", "Mercury", "Jupiter", "Venus"}


class TestAttackDefenceReading:
    def test_malefic_in_bahya_is_attacking(self):
        r = attack_defence_reading("Saturn", "bahya")
        assert r["is_natural_malefic"] is True
        assert r["posture"] == "attacking"
        assert r["severity"] == "watch"

    def test_benefic_in_bahya_is_reinforcing(self):
        r = attack_defence_reading("Jupiter", "bahya")
        assert r["is_natural_malefic"] is False
        assert r["posture"] == "reinforcing_perimeter"

    def test_malefic_at_stambha_is_acute(self):
        r = attack_defence_reading("Mars", "stambha")
        assert r["posture"] == "at_the_heart"
        assert r["severity"] == "acute"

    def test_benefic_at_stambha_is_strong_support(self):
        r = attack_defence_reading("Venus", "stambha")
        assert r["posture"] == "anchoring_the_heart"
        assert r["severity"] == "strong_support"

    def test_every_ring_x_nature_combination_returns_a_reading(self):
        for ring in ALL_RING_NAMES:
            for graha in ("Sun", "Moon"):
                r = attack_defence_reading(graha, ring)
                assert set(r.keys()) == {"posture", "severity", "is_natural_malefic"}

    def test_unknown_ring_raises(self):
        import pytest
        with pytest.raises(ValueError):
            attack_defence_reading("Sun", "not_a_ring")


class TestDetectRingRuns:
    """Contiguous-run detection over a daily (date, nakshatra_idx) series — the
    honest entry/exit mechanism. B.10 discipline: a run touching either edge of
    the SCANNED horizon is marked truncated (we genuinely do not know when it
    really started/ended beyond what we scanned), never silently presented as
    a precise, fully-known boundary."""

    def test_single_run_no_change(self):
        days = [(date(2026, 1, 1 + i), 5) for i in range(5)]
        runs = detect_ring_runs(days, horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 5))
        assert len(runs) == 1
        assert runs[0]["nakshatra_idx"] == 5
        assert runs[0]["start_date"] == date(2026, 1, 1)
        assert runs[0]["end_date"] == date(2026, 1, 5)
        # both edges touch the scanned horizon -> both truncated
        assert runs[0]["start_truncated"] is True
        assert runs[0]["end_truncated"] is True

    def test_two_runs_boundary_not_truncated_in_the_middle(self):
        days = [
            (date(2026, 1, 1), 5), (date(2026, 1, 2), 5),
            (date(2026, 1, 3), 6), (date(2026, 1, 4), 6),
        ]
        runs = detect_ring_runs(days, horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 4))
        assert len(runs) == 2
        first, second = runs
        assert first["nakshatra_idx"] == 5
        assert first["start_date"] == date(2026, 1, 1)
        assert first["end_date"] == date(2026, 1, 2)
        assert first["start_truncated"] is True   # touches horizon_start
        assert first["end_truncated"] is False     # a REAL observed transition
        assert second["nakshatra_idx"] == 6
        assert second["start_truncated"] is False
        assert second["end_truncated"] is True     # touches horizon_end

    def test_empty_input_returns_no_runs(self):
        assert detect_ring_runs([], horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 1)) == []

    def test_run_containing_date_helper(self):
        from services.ka_kota_chakra.logic import run_containing_date
        days = [
            (date(2026, 1, 1), 5), (date(2026, 1, 2), 5),
            (date(2026, 1, 3), 6), (date(2026, 1, 4), 6),
        ]
        runs = detect_ring_runs(days, horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 4))
        current = run_containing_date(runs, date(2026, 1, 3))
        assert current is not None
        assert current["nakshatra_idx"] == 6
        assert run_containing_date(runs, date(2026, 6, 1)) is None
