"""Tests for ka_moorti_nirnaya (ṢAḌ-DARŚANA W3, registry item 4 —
Moorti-nirṇaya per ingress per chart).

TDD: written before services/ka_moorti_nirnaya/writer.py existed. Pure-logic
unit tests only here (no DB) — mirrors tests/l3/test_ka_kota_chakra.py's
split between DB-free helper tests and the writer's own DB-touching
behaviour (tested separately in test_ka_moorti_nirnaya_writer.py).

Spec: SHAD_DARSHANA_BRIEF_v2_0.md §1 item 4; KALA_SIX_VIEWS_DESIGN_v1_0.md
§1.2 ("Moorti-nirṇaya ... reference rules exist (bg_transit_moorti); the
per-chart, per-ingress computation does not. BUILD.").

Unlike ka_kota_chakra's ring table (a disclosed tier-(iii) transcription),
`bg_transit_moorti` (migration 401) is ALREADY a real, populated, cited
reference table (Phaladeepika Ch.26; BPHS Ch.28) — this writer's own logic
carries no uncited classical claim; the only invented-precision risk is
computing a moorti classification for an unverified (truncated) ingress,
which `moorti_computed` exists specifically to prevent (see writer.py).
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_moorti_nirnaya.logic import (
    MOORTI_GRAHAS,
    detect_sign_runs,
    nakshatra_offset_from_janma,
    run_containing_date,
)


class TestMoortiGrahaScope:
    def test_excludes_moon(self):
        assert "Moon" not in MOORTI_GRAHAS

    def test_includes_the_other_eight_classical_grahas(self):
        assert set(MOORTI_GRAHAS) == {
            "Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
        }

    def test_exactly_eight_grahas(self):
        assert len(MOORTI_GRAHAS) == 8


class TestNakshatraOffsetFromJanma:
    def test_same_nakshatra_as_janma_is_offset_1(self):
        assert nakshatra_offset_from_janma(moon_nak_idx_at_ingress=5, janma_nak_idx=5) == 1

    def test_next_nakshatra_is_offset_2(self):
        assert nakshatra_offset_from_janma(moon_nak_idx_at_ingress=6, janma_nak_idx=5) == 2

    def test_wraps_around_27(self):
        # janma = index 26 (Revati), Moon at index 0 (Ashwini) at ingress -> offset 2
        assert nakshatra_offset_from_janma(moon_nak_idx_at_ingress=0, janma_nak_idx=26) == 2

    def test_wraps_backward(self):
        assert nakshatra_offset_from_janma(moon_nak_idx_at_ingress=26, janma_nak_idx=0) == 27

    def test_full_cycle_produces_every_offset_exactly_once(self):
        janma = 24  # Purva Bhadrapada, the FORENSIC-anchored janma nakshatra for 482012f1
        offsets = {nakshatra_offset_from_janma(i, janma) for i in range(27)}
        assert offsets == set(range(1, 28))

    def test_matches_bg_transit_moorti_convention(self):
        # migration 401: "27 rows: count transit nakshatra from natal janma
        # nakshatra (offset 1..27)". offset=1 must mean the Moon is IN the
        # janma nakshatra itself at the moment of ingress.
        for janma in range(27):
            assert nakshatra_offset_from_janma(moon_nak_idx_at_ingress=janma, janma_nak_idx=janma) == 1


class TestDetectSignRuns:
    """Contiguous-run detection over a daily (date, sign_idx) series — the
    same honesty discipline as ka_kota_chakra.logic.detect_ring_runs, applied
    to sign index instead of nakshatra index."""

    def test_single_run_no_change(self):
        days = [(date(2026, 1, 1 + i), 3) for i in range(5)]
        runs = detect_sign_runs(days, horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 5))
        assert len(runs) == 1
        assert runs[0]["sign_idx"] == 3
        assert runs[0]["start_date"] == date(2026, 1, 1)
        assert runs[0]["end_date"] == date(2026, 1, 5)
        assert runs[0]["start_truncated"] is True
        assert runs[0]["end_truncated"] is True

    def test_two_runs_ingress_boundary_not_truncated(self):
        days = [
            (date(2026, 1, 1), 3), (date(2026, 1, 2), 3),
            (date(2026, 1, 3), 4), (date(2026, 1, 4), 4),
        ]
        runs = detect_sign_runs(days, horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 4))
        assert len(runs) == 2
        first, second = runs
        assert first["sign_idx"] == 3
        assert first["end_date"] == date(2026, 1, 2)
        assert first["start_truncated"] is True
        assert first["end_truncated"] is False
        assert second["sign_idx"] == 4
        assert second["start_date"] == date(2026, 1, 3)
        assert second["start_truncated"] is False  # a REAL observed ingress
        assert second["end_truncated"] is True

    def test_empty_input_returns_no_runs(self):
        assert detect_sign_runs([], horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 1)) == []

    def test_run_containing_date_helper(self):
        days = [
            (date(2026, 1, 1), 3), (date(2026, 1, 2), 3),
            (date(2026, 1, 3), 4), (date(2026, 1, 4), 4),
        ]
        runs = detect_sign_runs(days, horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 4))
        current = run_containing_date(runs, date(2026, 1, 3))
        assert current is not None
        assert current["sign_idx"] == 4
        assert run_containing_date(runs, date(2026, 6, 1)) is None

    def test_sign_wraps_pisces_to_aries(self):
        # sign_idx 11 (Pisces) -> 0 (Aries) is a genuine ingress, not a "wrap error".
        days = [(date(2026, 1, 1), 11), (date(2026, 1, 2), 0)]
        runs = detect_sign_runs(days, horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 2))
        assert len(runs) == 2
        assert runs[0]["sign_idx"] == 11
        assert runs[1]["sign_idx"] == 0
