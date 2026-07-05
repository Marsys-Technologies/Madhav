"""
test_ph_muhurta_bala_join.py — JL-016 (BA-2.5 P3 J6) proof tests.

Bug: ph_muhurta hardcoded 0.5 defaults for tarabala/chandrabala instead of
computing/joining real values, flattening personalization/composite scores
toward a constant.

Fix: ph_muhurta now JOINS real tarabala/chandrabala at serve time — natal
Moon nakshatra/sign already computed into chart_facts by L1, transit Moon
position from the existing panchang_engine panchanga service — and calls
the existing classical formulas in panchang_engine.tara_bala (already used
by ka_muhurta_seva / muhurat.finder). No formula is reimplemented inside
ph_muhurta or its engine.

Covers:
  - _load_natal_moon_sign_id / _load_natal_moon_nakshatra_id parse chart_facts
    correctly and return None (not a fabricated default) when data is absent.
  - _compute_tara_chandra_scores: honest placeholder when natal data or
    birth_params or the ephemeris path is unavailable — clearly labeled via
    tarabala_chandrabala_source, never silently indistinguishable from a real
    0.5 score.
  - _compute_tara_chandra_scores: real, VARYING scores for different candidate
    dates when natal data + birth_params are present (degeneracy gate —
    composite/personalization must not flatten to a constant).
  - engine.derive_muhurta_record: tarabala_chandrabala_jsonb['source'] and
    follow_up_hook_jsonb['already_satisfied'] correctly distinguish live vs
    placeholder records.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest


def _make_conn_with_savepoint(fetchone_return=None):
    """Mock psycopg connection supporting cursor()-as-context-manager +
    SAVEPOINT/RELEASE/ROLLBACK execute calls + fetchone()."""
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    cur.fetchone.return_value = fetchone_return

    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


def _writer():
    from pipeline.orchestrator.writers.ph_muhurta import PhMuhurtaWriter
    return PhMuhurtaWriter.__new__(PhMuhurtaWriter)


# ─────────────────────────────────────────────────────────────────────────────
# Natal Moon nakshatra/sign loaders — real values, None-safe on miss
# ─────────────────────────────────────────────────────────────────────────────

class TestNatalMoonLoaders:
    def test_natal_moon_nakshatra_id_purva_bhadrapada(self):
        """FORENSIC anchor: Moon = Purva Bhadrapada → 1-indexed id 25."""
        writer = _writer()
        conn, _cur = _make_conn_with_savepoint(fetchone_return=('Purva Bhadrapada',))
        result = writer._load_natal_moon_nakshatra_id(conn, 'chart-uuid')
        assert result == 25

    def test_natal_moon_nakshatra_id_none_when_absent(self):
        """No chart_facts row → None, never a fabricated default nakshatra."""
        writer = _writer()
        conn, _cur = _make_conn_with_savepoint(fetchone_return=None)
        result = writer._load_natal_moon_nakshatra_id(conn, 'chart-uuid')
        assert result is None

    def test_natal_moon_sign_id_aquarius(self):
        writer = _writer()
        conn, _cur = _make_conn_with_savepoint(fetchone_return=('Aquarius',))
        result = writer._load_natal_moon_sign_id(conn, 'chart-uuid')
        assert result == 11

    def test_natal_moon_sign_id_none_when_absent(self):
        writer = _writer()
        conn, _cur = _make_conn_with_savepoint(fetchone_return=None)
        result = writer._load_natal_moon_sign_id(conn, 'chart-uuid')
        assert result is None

    def test_natal_moon_sign_id_none_on_db_exception(self):
        """DB error → savepoint rollback, return None (not a crash, not a fake default)."""
        writer = _writer()
        conn, cur = _make_conn_with_savepoint()
        cur.execute.side_effect = [None, Exception("boom"), None]
        result = writer._load_natal_moon_sign_id(conn, 'chart-uuid')
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# _compute_tara_chandra_scores — honest placeholder vs real join
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeTaraChandraScores:
    def _writer(self):
        return _writer()

    def test_placeholder_when_natal_sign_missing(self):
        writer = self._writer()
        tara, chandra, source = writer._compute_tara_chandra_scores(
            25, None, {'latitude_deg': 20.27, 'longitude_deg': 85.84, 'tz_offset_hours': 5.5},
            datetime(2026, 9, 1, 6, 0),
        )
        assert (tara, chandra) == (0.5, 0.5)
        assert source == 'placeholder_no_ephemeris'

    def test_placeholder_when_natal_nakshatra_missing(self):
        writer = self._writer()
        tara, chandra, source = writer._compute_tara_chandra_scores(
            None, 11, {'latitude_deg': 20.27, 'longitude_deg': 85.84, 'tz_offset_hours': 5.5},
            datetime(2026, 9, 1, 6, 0),
        )
        assert (tara, chandra) == (0.5, 0.5)
        assert source == 'placeholder_no_ephemeris'

    def test_placeholder_when_birth_params_missing(self):
        writer = self._writer()
        tara, chandra, source = writer._compute_tara_chandra_scores(
            25, 11, {}, datetime(2026, 9, 1, 6, 0),
        )
        assert (tara, chandra) == (0.5, 0.5)
        assert source == 'placeholder_no_ephemeris'

    def test_placeholder_when_candidate_start_missing(self):
        writer = self._writer()
        tara, chandra, source = writer._compute_tara_chandra_scores(
            25, 11, {'latitude_deg': 20.27, 'longitude_deg': 85.84, 'tz_offset_hours': 5.5},
            None,
        )
        assert (tara, chandra) == (0.5, 0.5)
        assert source == 'placeholder_no_ephemeris'

    def test_placeholder_when_lat_lon_tz_incomplete(self):
        writer = self._writer()
        tara, chandra, source = writer._compute_tara_chandra_scores(
            25, 11, {'latitude_deg': 20.27},  # missing longitude_deg / tz_offset_hours
            datetime(2026, 9, 1, 6, 0),
        )
        assert (tara, chandra) == (0.5, 0.5)
        assert source == 'placeholder_no_ephemeris'

    def test_real_join_returns_live_source_and_valid_range(self):
        writer = self._writer()
        birth_params = {'latitude_deg': 20.27, 'longitude_deg': 85.84, 'tz_offset_hours': 5.5}
        tara, chandra, source = writer._compute_tara_chandra_scores(
            25, 11, birth_params, datetime(2026, 9, 1, 6, 0),
        )
        assert source == 'panchang_engine_live'
        assert 0.0 <= tara <= 1.0
        assert 0.0 <= chandra <= 1.0

    def test_real_join_varies_across_candidate_dates(self):
        """Degeneracy gate: tarabala/chandrabala must not flatten to a constant
        across different candidate dates once real ephemeris data is joined."""
        writer = self._writer()
        birth_params = {'latitude_deg': 20.27, 'longitude_deg': 85.84, 'tz_offset_hours': 5.5}
        dates = [
            datetime(2026, 1, 5, 6, 0),
            datetime(2026, 4, 12, 6, 0),
            datetime(2026, 9, 1, 6, 0),
            datetime(2027, 2, 20, 6, 0),
            datetime(2027, 6, 30, 6, 0),
        ]
        results = [
            writer._compute_tara_chandra_scores(25, 11, birth_params, d)
            for d in dates
        ]
        sources = {r[2] for r in results}
        assert sources == {'panchang_engine_live'}, f"expected all live, got {sources}"

        tara_scores = {r[0] for r in results}
        chandra_scores = {r[1] for r in results}
        assert len(tara_scores) > 1, (
            f"tarabala_score must vary across candidate dates, got constant set {tara_scores}"
        )
        assert len(chandra_scores) > 1, (
            f"chandrabala_score must vary across candidate dates, got constant set {chandra_scores}"
        )

    def test_ephemeris_failure_falls_back_to_labeled_placeholder(self):
        """Any exception in the live path (bad coordinates etc.) must degrade to
        the honest placeholder, never raise and never silently return a fake
        'live' label."""
        writer = self._writer()
        # Latitude out of range triggers panchang_engine's ValidationError.
        tara, chandra, source = writer._compute_tara_chandra_scores(
            25, 11, {'latitude_deg': 999.0, 'longitude_deg': 85.84, 'tz_offset_hours': 5.5},
            datetime(2026, 9, 1, 6, 0),
        )
        assert (tara, chandra) == (0.5, 0.5)
        assert source == 'placeholder_no_ephemeris'


# ─────────────────────────────────────────────────────────────────────────────
# engine.py: source label flows through to the persisted jsonb + follow-up hook
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineSourceLabeling:
    def _ctx(self, **kwargs):
        from services.ph_muhurta.engine import MuhurtaContext
        defaults = dict(
            action_class='start_business',
            window_start=datetime(2026, 9, 1, 6, 0),
            window_end=datetime(2026, 9, 30, 18, 0),
            hora_lord='saturn',
            panchanga_score=0.72,
            condition_score=0.8,
            transit_score=0.6,
            overlapping_obstruction_id=None,
            obstruction_penalty=0.0,
            linked_anchor_id='anchor-001',
        )
        defaults.update(kwargs)
        return MuhurtaContext(**defaults)

    def test_placeholder_record_labeled_and_hook_not_satisfied(self):
        from services.ph_muhurta.engine import derive_muhurta_record
        rec = derive_muhurta_record(self._ctx(
            tarabala_score=0.5, chandrabala_score=0.5,
            tarabala_chandrabala_source='placeholder_no_ephemeris',
        ))
        assert rec.tarabala_chandrabala_jsonb['source'] == 'placeholder_no_ephemeris'
        assert 'honest 0.5 placeholder' in rec.tarabala_chandrabala_jsonb['note']
        assert rec.follow_up_hook_jsonb['already_satisfied'] is False

    def test_live_record_labeled_and_hook_satisfied(self):
        from services.ph_muhurta.engine import derive_muhurta_record
        rec = derive_muhurta_record(self._ctx(
            tarabala_score=0.85, chandrabala_score=0.9,
            tarabala_chandrabala_source='panchang_engine_live',
        ))
        assert rec.tarabala_chandrabala_jsonb['source'] == 'panchang_engine_live'
        assert 'real transit-Moon' in rec.tarabala_chandrabala_jsonb['note']
        assert rec.follow_up_hook_jsonb['already_satisfied'] is True

    def test_personalization_and_composite_not_flattened_across_varying_balas(self):
        """Core degeneracy-gate assertion for JL-016: feeding varying real
        tarabala/chandrabala inputs must yield varying composite_quality —
        the whole point of not hardcoding 0.5 for every window."""
        from services.ph_muhurta.engine import derive_muhurta_record

        composites = set()
        for tara, chandra in [(0.85, 0.90), (0.0, 0.10), (0.95, 0.30), (0.50, 0.50)]:
            rec = derive_muhurta_record(self._ctx(
                tarabala_score=tara, chandrabala_score=chandra,
                tarabala_chandrabala_source='panchang_engine_live',
            ))
            composites.add(rec.composite_quality)

        assert len(composites) > 1, (
            f"composite_quality must vary with tarabala/chandrabala inputs, got constant {composites}"
        )
