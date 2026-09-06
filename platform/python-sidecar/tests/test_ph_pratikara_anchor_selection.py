"""ph_pratikara: the anchor that was always the same one, regardless of domain.

F-3.4 (L4_W1_ANALYSIS_BATCH_C.md §3.4): the writer picked "the first influenceable
anchor found across ALL domains" and used it for every obstruction in the chart --
measured live: all 536 CANON rows linked to a single career anchor, chosen from 107
influenceable candidates across 4 domains. No domain match, no window overlap, no
graha relation. That collapsed P4 proportionality (anchor_magnitude frozen at
'minor' -> 'intensive' structurally unreachable) and made the L5 outcome-loop hook
mis-keyed on every row.

The fix: match the obstruction's own domain (bridged from kala_convergence.domain),
prefer a window-overlapping anchor within that domain, and fall back to an honest
(None, None) rather than a plausible-looking wrong anchor when no domain-relevant
anchor exists (linked_anchor_id is nullable with ON DELETE SET NULL for exactly
this -- §N.7 item 6).
"""
from __future__ import annotations

from datetime import date

import pytest

from pipeline.orchestrator.writers.ph_pratikara import _select_anchor, _windows_overlap


class TestWindowsOverlap:
    def test_overlapping_windows(self):
        assert _windows_overlap(
            date(2026, 1, 1), date(2026, 3, 1), date(2026, 2, 1), date(2026, 4, 1),
        ) is True

    def test_non_overlapping_windows(self):
        assert _windows_overlap(
            date(2026, 1, 1), date(2026, 2, 1), date(2026, 6, 1), date(2026, 7, 1),
        ) is False

    def test_identical_windows_overlap(self):
        d1, d2 = date(2026, 1, 1), date(2026, 2, 1)
        assert _windows_overlap(d1, d2, d1, d2) is True

    def test_missing_bounds_are_non_restrictive(self):
        # Unknown windows are not treated as "excludes everything" -- an obstruction
        # or anchor with no window data must not be disqualified purely for that.
        assert _windows_overlap(None, None, date(2026, 1, 1), date(2026, 2, 1)) is True
        assert _windows_overlap(date(2026, 1, 1), date(2026, 2, 1), None, None) is True
        assert _windows_overlap(None, None, None, None) is True


class TestSelectAnchor:
    CAREER = [
        {'anchor_id': 'career-major', 'magnitude': 'major',
         'window_start': date(2026, 1, 1), 'window_end': date(2026, 2, 1)},
        {'anchor_id': 'career-minor', 'magnitude': 'minor',
         'window_start': date(2026, 6, 1), 'window_end': date(2026, 7, 1)},
    ]
    ANCHORS_BY_DOMAIN = {'career': CAREER, 'wealth': [
        {'anchor_id': 'wealth-moderate', 'magnitude': 'moderate',
         'window_start': None, 'window_end': None},
    ]}

    def test_no_domain_is_honest_none(self):
        # F-3.4 point 3: no domain-relevant anchor was determined -> NULL, not a guess.
        assert _select_anchor(self.ANCHORS_BY_DOMAIN, None, date(2026, 1, 1), date(2026, 2, 1)) == (None, None)

    def test_domain_with_no_candidates_is_honest_none(self):
        assert _select_anchor(self.ANCHORS_BY_DOMAIN, 'health', date(2026, 1, 1), date(2026, 2, 1)) == (None, None)

    def test_never_reaches_across_domains(self):
        # The original bug: picked the first anchor in ANY domain. A 'health'
        # obstruction must never come back with a 'career' or 'wealth' anchor.
        anchor_id, _ = _select_anchor(self.ANCHORS_BY_DOMAIN, 'health', None, None)
        assert anchor_id is None

    def test_window_overlap_preferred_over_magnitude_priority(self):
        # career-major is first in magnitude-priority order, but its window doesn't
        # overlap the obstruction's; career-minor's does. The overlapping one wins.
        anchor_id, magnitude = _select_anchor(
            self.ANCHORS_BY_DOMAIN, 'career', date(2026, 6, 10), date(2026, 6, 20),
        )
        assert anchor_id == 'career-minor'
        assert magnitude == 'minor'

    def test_falls_back_to_highest_magnitude_when_no_window_overlaps(self):
        anchor_id, magnitude = _select_anchor(
            self.ANCHORS_BY_DOMAIN, 'career', date(2026, 12, 1), date(2026, 12, 31),
        )
        assert anchor_id == 'career-major'
        assert magnitude == 'major'

    def test_unknown_obstruction_window_matches_first_candidate(self):
        # Unknown obstruction window is non-restrictive, so the first (highest
        # magnitude-priority) candidate's overlap check passes immediately.
        anchor_id, magnitude = _select_anchor(self.ANCHORS_BY_DOMAIN, 'career', None, None)
        assert anchor_id == 'career-major'
        assert magnitude == 'major'

    def test_single_candidate_with_no_window_data_still_selected(self):
        anchor_id, magnitude = _select_anchor(
            self.ANCHORS_BY_DOMAIN, 'wealth', date(2026, 1, 1), date(2026, 2, 1),
        )
        assert anchor_id == 'wealth-moderate'
        assert magnitude == 'moderate'
