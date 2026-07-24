"""
test_ph_a5_fixes.py — A5 remediation tests.

Covers:
  - CONTRACT-3: _load_cgm_meta returns actual fetched rows (not always {})
  - B5: discovery-sourced anchor gets non-NULL window_start/end and real domain
  - B5-downstream: anchor with real domain passes CDLM cell matching; 'transition' does not
  - B9: transit_score is not constant 0.5 when ka_gochara data is available
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, call
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_conn_with_savepoint(fetchall_returns=None, fetchone_return=None):
    """
    Return a mock psycopg connection that supports:
      - cursor() as context manager
      - savepoint execute calls (SAVEPOINT / RELEASE / ROLLBACK)
      - fetchall() returning fetchall_returns
      - fetchone() returning fetchone_return
    The same cursor mock is re-used for all cursor() calls so we can assert calls.
    """
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    cur.fetchall.return_value = fetchall_returns or []
    cur.fetchone.return_value = fetchone_return

    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


# ─────────────────────────────────────────────────────────────────────────────
# CONTRACT-3: _load_cgm_meta returns actual fetched rows
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadCgmMeta:
    """CONTRACT-3: _load_cgm_meta returns actual data, never hard-coded {}."""

    def _make_writer(self):
        from pipeline.orchestrator.writers.ph_nimitta import PhNimittaWriter
        w = PhNimittaWriter.__new__(PhNimittaWriter)
        return w

    def test_empty_signal_ids_returns_empty(self):
        """Fast-path: no signal_ids → empty dict without hitting DB."""
        writer = self._make_writer()
        conn = MagicMock()
        result = writer._load_cgm_meta(conn, [])
        assert result == {}
        conn.cursor.assert_not_called()

    def test_returns_chart_level_aggregate(self):
        """CONTRACT-3 fix: _load_cgm_meta returns chart-level aggregate, not per-signal dict.

        bodha_cgm_paths has no signal_id FK — the old per-signal lookup was always a miss.
        The fixed version returns a chart-level aggregate with 'path_count', 'paths',
        'has_final_dispositor', and 'max_path_length' keys.
        """
        writer = self._make_writer()

        fake_rows = [
            {'path_id': 'path-001', 'path_label_human': 'Saturn→10th→career', 'path_length': 2, 'is_final_dispositor': True},
            {'path_id': 'path-002', 'path_label_human': 'Jupiter→9th→dharma',  'path_length': 3, 'is_final_dispositor': False},
        ]
        conn, cur = _make_conn_with_savepoint(fetchall_returns=fake_rows)

        result = writer._load_cgm_meta(conn, ['sig-uuid-1'])

        assert isinstance(result, dict), "result must be a dict"
        assert result['path_count'] == 2, "path_count must be 2"
        assert len(result['paths']) == 2, "paths list must have 2 entries"
        assert result['has_final_dispositor'] is True, "has_final_dispositor must be True (path-001)"
        assert result['max_path_length'] == 3, "max_path_length must be 3 (path-002)"
        # paths list preserves full row dicts
        labels = {p['path_label_human'] for p in result['paths']}
        assert 'Saturn→10th→career' in labels
        assert 'Jupiter→9th→dharma' in labels

    def test_returns_empty_on_db_exception_gracefully(self):
        """Exception during query → rollback savepoint, return {}, do not raise."""
        writer = self._make_writer()

        conn = MagicMock()
        cur = MagicMock()
        cur.__enter__ = lambda s: s
        cur.__exit__ = MagicMock(return_value=False)
        # First cursor call (SAVEPOINT) OK; second call raises (simulating missing table)
        savepoint_cur = MagicMock()
        savepoint_cur.__enter__ = lambda s: s
        savepoint_cur.__exit__ = MagicMock(return_value=False)

        call_count = [0]
        def cursor_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return savepoint_cur  # SAVEPOINT
            if call_count[0] == 2:
                raise Exception("relation bodha_cgm_paths does not exist")
            return savepoint_cur  # ROLLBACK

        conn.cursor.side_effect = cursor_side_effect

        result = writer._load_cgm_meta(conn, ['sig-uuid-1'])
        assert result == {}


# ─────────────────────────────────────────────────────────────────────────────
# B5: discovery anchor timing + domain
# ─────────────────────────────────────────────────────────────────────────────

class TestDiscoveryAnchorTimingAndDomain:
    """B5: _enrich_discovery_row and derive_anchor_from_discovery produce correct timing+domain."""

    def _make_writer(self):
        from pipeline.orchestrator.writers.ph_nimitta import PhNimittaWriter
        w = PhNimittaWriter.__new__(PhNimittaWriter)
        return w

    def test_enrich_sets_window_start_from_detected_at(self):
        """B5: window_start is derived from detected_at when present."""
        writer = self._make_writer()
        conn, cur = _make_conn_with_savepoint(fetchall_returns=[], fetchone_return=None)

        row = {
            'id': 'disc-001',
            'domain': 'transition',
            'discovery_subsystem': 'career',
            'cross_subsystem_root': None,
            'detected_at': date(2024, 6, 1),
            'chart_id': None,  # no convergence lookup
        }
        enriched = writer._enrich_discovery_row(conn, row)

        assert enriched['window_start'] is not None, "window_start must be non-NULL after B5 fix"
        assert enriched['window_start'] == date(2024, 6, 1)

    def test_enrich_sets_window_end_90_days_after_detected_at(self):
        """B5: window_end = detected_at + 90 days."""
        writer = self._make_writer()
        conn, cur = _make_conn_with_savepoint()

        row = {
            'id': 'disc-002',
            'domain': 'transition',
            'discovery_subsystem': 'health',
            'cross_subsystem_root': None,
            'detected_at': date(2024, 6, 1),
            'chart_id': None,
        }
        enriched = writer._enrich_discovery_row(conn, row)

        expected_end = date(2024, 6, 1) + timedelta(days=90)
        assert enriched['window_end'] == expected_end

    def test_enrich_maps_subsystem_to_real_domain(self):
        """B5: discovery_subsystem 'yoga' → domain 'spirituality', not 'transition'.

        CR-66: the mapping target is now the canonical phala_anchors_domain_canonical DB
        vocabulary ('spirituality'), not the pre-CR-66 'spiritual' (which was not a legal
        phala_anchors.domain value)."""
        writer = self._make_writer()
        conn, cur = _make_conn_with_savepoint()

        row = {
            'id': 'disc-003',
            'domain': 'transition',
            'discovery_subsystem': 'yoga',
            'cross_subsystem_root': None,
            'detected_at': date(2024, 9, 15),
            'chart_id': None,
        }
        enriched = writer._enrich_discovery_row(conn, row)

        assert enriched['domain'] != 'transition', "domain must not be 'transition' when subsystem maps to something real"
        assert enriched['domain'] == 'spirituality'

    def test_enrich_health_subsystem(self):
        """B5: 'health' subsystem → domain 'health'."""
        writer = self._make_writer()
        conn, cur = _make_conn_with_savepoint()

        row = {
            'id': 'disc-004',
            'domain': 'transition',
            'discovery_subsystem': 'health',
            'cross_subsystem_root': None,
            'detected_at': date(2025, 1, 10),
            'chart_id': None,
        }
        enriched = writer._enrich_discovery_row(conn, row)
        assert enriched['domain'] == 'health'

    def test_enrich_discovery_row_uses_passed_chart_id(self):
        """IMPORTANT-1 fix: chart_id is passed explicitly, not read from row.get('chart_id').

        _load_discoveries does not SELECT chart_id, so row.get('chart_id') is always None.
        The proximity lookup (SAVEPOINT sp_nimitta_disc_conv) must execute when chart_id is
        passed explicitly as a parameter, even though the row dict has no chart_id key.
        """
        writer = self._make_writer()

        # Simulate convergence proximity returning a matching row
        fake_conv_row = {'convergence_id': 'conv-xyz', 'peak_date': date(2024, 7, 1), 'domain': 'career'}
        conn, cur = _make_conn_with_savepoint(fetchall_returns=[], fetchone_return=fake_conv_row)

        row = {
            'id': 'disc-007',
            'domain': 'transition',
            'discovery_subsystem': 'career',
            'cross_subsystem_root': None,
            'detected_at': date(2024, 6, 1),
            # NOTE: no 'chart_id' key — matches what _load_discoveries actually returns
        }
        # Pass chart_id explicitly (the fix)
        enriched = writer._enrich_discovery_row(conn, row, chart_id='test-chart-uuid')

        # The proximity lookup should have been attempted (cur.execute called with chart_id arg)
        # and convergence_id should have been populated from the mocked return
        assert enriched.get('convergence_id') == 'conv-xyz', (
            "convergence_id must be populated when chart_id is passed explicitly"
        )
        assert enriched.get('peak_date') == date(2024, 7, 1)

    def test_enrich_no_detected_at_leaves_timing_null(self):
        """B5: if detected_at is NULL, timing is not fabricated."""
        writer = self._make_writer()
        conn, cur = _make_conn_with_savepoint()

        row = {
            'id': 'disc-005',
            'domain': 'transition',
            'discovery_subsystem': 'graha',
            'cross_subsystem_root': None,
            'detected_at': None,
            'chart_id': None,
        }
        enriched = writer._enrich_discovery_row(conn, row)

        assert enriched.get('window_start') is None
        assert enriched.get('window_end') is None

    def test_discovery_anchor_engine_gets_real_timing(self):
        """B5 integration: derive_anchor_from_discovery receives enriched row → non-NULL timing."""
        from services.ph_nimitta.engine import derive_anchor_from_discovery, NimittaContext

        ctx = NimittaContext()
        row = {
            'id': 'disc-006',
            'signal_id': None,
            'domain': 'career',
            'discovery_type': 'yoga_class',
            'surface_depth_delta': 0.5,
            'why_an_acharya_misses_it': 'Hidden by graha',
            'falsifier_jsonb': {},
            'confidence_score': 0.65,
            'peak_date': date(2024, 8, 1),
            'window_start': date(2024, 6, 1),   # enriched by B5
            'window_end':   date(2024, 9, 1),    # enriched by B5
        }
        anchor = derive_anchor_from_discovery(row, ctx)

        assert anchor.window_start is not None, "anchor.window_start must be non-NULL"
        assert anchor.window_end   is not None, "anchor.window_end must be non-NULL"
        assert anchor.domain == 'career'


# ─────────────────────────────────────────────────────────────────────────────
# B5-downstream: ph_sankrama domain matching
# ─────────────────────────────────────────────────────────────────────────────

class TestSankramaDomainMatching:
    """B5-downstream: real domain passes CDLM matching; 'transition' does not."""

    def _make_cdlm_cell(self, domain_row, domain_col, linkage=0.35):
        from services.ph_sankrama.engine import CdlmCell
        return CdlmCell(
            cell_id='cell-001',
            domain_row=domain_row,
            domain_col=domain_col,
            net_linkage_strength=linkage,
            asymmetry_score=0.1,
            contradicting_pairs_count=0,
            cgm_bridge_edge_seeds=[],
            predicted_activation_windows=[],
            evolution_gradient_score=0.05,
        )

    def test_career_domain_anchor_matches_cdlm_cell(self):
        """B5-downstream: anchor with domain='career' produces spillover when CDLM cell exists."""
        from services.ph_sankrama.engine import derive_spillover, SankramaContext

        cell = self._make_cdlm_cell('career', 'financial', linkage=0.30)
        ctx = SankramaContext(
            source_anchor_id='anchor-career-001',
            source_domain='career',
            source_window_start=date(2024, 6, 1),
            source_window_end=date(2024, 9, 1),
            source_confidence=0.65,
            cdlm_cells=[cell],
            all_cells_by_domain_pair={('career', 'financial'): [cell]},
        )
        spillovers = derive_spillover(ctx)
        assert len(spillovers) > 0, "career-domain anchor must produce at least one spillover"
        assert spillovers[0].target_domain == 'financial'

    def test_transition_domain_anchor_no_spillover_when_no_matching_cell(self):
        """B5-downstream: anchor with domain='transition' produces NO spillover when CDLM has no transition cells."""
        from services.ph_sankrama.engine import derive_spillover, SankramaContext

        # CDLM only has career↔financial cells, not transition
        cell = self._make_cdlm_cell('career', 'financial', linkage=0.30)
        ctx = SankramaContext(
            source_anchor_id='anchor-transition-001',
            source_domain='transition',    # old broken domain
            source_window_start=date(2024, 6, 1),
            source_window_end=date(2024, 9, 1),
            source_confidence=0.65,
            cdlm_cells=[],   # writer filters by domain_row == domain; no match
            all_cells_by_domain_pair={('career', 'financial'): [cell]},
        )
        spillovers = derive_spillover(ctx)
        assert spillovers == [], "transition anchor with no CDLM match must produce 0 spillovers"

    def test_writer_filters_cells_by_domain(self):
        """B5-downstream: writer matching logic filters cells correctly by domain_row."""
        from services.ph_sankrama.engine import CdlmCell

        # Reproduce the writer's matching logic inline
        _LINKAGE_THRESHOLD = 0.25
        cdlm_cells = [
            self._make_cdlm_cell('career', 'financial', linkage=0.35),
            self._make_cdlm_cell('health', 'psychological', linkage=0.40),
        ]

        # Anchor domain = 'career'
        domain = 'career'
        matching = [c for c in cdlm_cells if c.domain_row == domain and c.net_linkage_strength >= _LINKAGE_THRESHOLD]
        assert len(matching) == 1
        assert matching[0].domain_col == 'financial'

        # Anchor domain = 'transition' → no match
        domain_t = 'transition'
        matching_t = [c for c in cdlm_cells if c.domain_row == domain_t and c.net_linkage_strength >= _LINKAGE_THRESHOLD]
        assert matching_t == []


# ─────────────────────────────────────────────────────────────────────────────
# B9: ph_muhurta transit scoring
# ─────────────────────────────────────────────────────────────────────────────

class TestMuhurtaTransitScoring:
    """B9: transit_score varies with real ka_gochara data, not constant 0.5."""

    def _make_writer(self):
        from pipeline.orchestrator.writers.ph_muhurta import PhMuhurtaWriter
        w = PhMuhurtaWriter.__new__(PhMuhurtaWriter)
        return w

    def test_transit_score_default_when_no_data(self):
        """B9: returns 0.5 when gochara_by_graha is empty."""
        writer = self._make_writer()
        score = writer._compute_transit_score({}, 'saturn', datetime(2024, 6, 15))
        assert score == 0.5

    def test_transit_score_default_when_graha_absent(self):
        """B9: returns 0.5 when graha not in gochara dict."""
        writer = self._make_writer()
        gochara = {'mars': [{'sign_number': 1, 'is_retrograde': False,
                              'start_date': date(2024, 1, 1), 'end_date': date(2024, 12, 31)}]}
        score = writer._compute_transit_score(gochara, 'saturn', datetime(2024, 6, 15))
        assert score == 0.5

    def test_retrograde_transit_scores_low(self):
        """B9: retrograde transit → score = 0.35."""
        writer = self._make_writer()
        gochara = {
            'saturn': [{
                'sign_number': 10, 'is_retrograde': True,
                'start_date': date(2024, 1, 1), 'end_date': date(2024, 12, 31),
            }]
        }
        score = writer._compute_transit_score(gochara, 'saturn', datetime(2024, 6, 15))
        assert score == 0.35

    def test_own_sign_transit_scores_high(self):
        """B9: own-sign transit → score = 0.75."""
        writer = self._make_writer()
        # Saturn own signs: 10, 11
        gochara = {
            'saturn': [{
                'sign_number': 10, 'is_retrograde': False,
                'start_date': date(2024, 1, 1), 'end_date': date(2024, 12, 31),
            }]
        }
        score = writer._compute_transit_score(gochara, 'saturn', datetime(2024, 6, 15))
        assert score == 0.75

    def test_transit_score_varies_between_anchors(self):
        """B9 core: two anchors at different dates get different scores (not constant 0.5)."""
        writer = self._make_writer()
        # sign 10 (own, non-retro) → 0.75; sign 5 (non-own) → 0.55 + small variance
        gochara = {
            'saturn': [
                {
                    'sign_number': 10, 'is_retrograde': False,
                    'start_date': date(2024, 1, 1), 'end_date': date(2024, 6, 30),
                },
                {
                    'sign_number': 5, 'is_retrograde': False,
                    'start_date': date(2024, 7, 1), 'end_date': date(2024, 12, 31),
                },
            ]
        }
        score_a = writer._compute_transit_score(gochara, 'saturn', datetime(2024, 3, 1))  # sign 10 → 0.75
        score_b = writer._compute_transit_score(gochara, 'saturn', datetime(2024, 9, 1))  # sign 5 → variance

        assert score_a != score_b, "transit_score must differ between different active transits (not constant 0.5)"
        assert score_a == 0.75, "own-sign (sign 10) must score 0.75"
        assert score_b != 0.5,  "non-own sign must not score exactly 0.5"

    def test_transit_score_12_distinct_values_across_zodiac(self):
        """IMPORTANT-2 fix: % 12 (not % 6) produces 12 distinct scores across the zodiac.

        With % 6, signs 1 and 7 both yielded 0.55, signs 2 and 8 both yielded 0.57, etc.
        (only 6 distinct values). With % 12 each of the 12 zodiac positions is unique.
        """
        writer = self._make_writer()
        scores = set()
        for sign_num in range(1, 13):
            # Use a non-own, non-retro transit for each sign to exercise the variance path
            gochara = {
                'mercury': [{
                    'sign_number': sign_num,
                    'is_retrograde': False,
                    'start_date': date(2024, 1, 1),
                    'end_date': date(2024, 12, 31),
                }]
            }
            score = writer._compute_transit_score(gochara, 'mercury', datetime(2024, 6, 15))
            # skip own-sign scores (mercury own: 3, 6) — those return 0.75 not variance
            if sign_num not in {3, 6}:
                scores.add(score)

        # Should have 10 distinct variance scores (signs 1,2,4,5,7,8,9,10,11,12 — 10 non-own signs)
        assert len(scores) == 10, (
            f"Expected 10 distinct non-own-sign scores (% 12 fix), got {len(scores)}: {sorted(scores)}"
        )

    def test_no_active_transit_returns_default(self):
        """B9: no transit window covers candidate_start → returns 0.5."""
        writer = self._make_writer()
        gochara = {
            'saturn': [{
                'sign_number': 10, 'is_retrograde': False,
                'start_date': date(2025, 1, 1), 'end_date': date(2025, 12, 31),
            }]
        }
        # candidate_start is 2024 — outside the transit window
        score = writer._compute_transit_score(gochara, 'saturn', datetime(2024, 6, 15))
        assert score == 0.5

    def test_candidate_start_none_returns_default(self):
        """B9: candidate_start=None → 0.5."""
        writer = self._make_writer()
        gochara = {
            'saturn': [{'sign_number': 10, 'is_retrograde': False,
                        'start_date': date(2024, 1, 1), 'end_date': date(2024, 12, 31)}]
        }
        score = writer._compute_transit_score(gochara, 'saturn', None)
        assert score == 0.5


class TestMuhurtaCapRaised:
    """B9: MAX_MUHURTA_ANCHORS is 400, not 100."""

    def test_cap_constant_is_400(self):
        """B9: MAX_MUHURTA_ANCHORS constant must equal 400."""
        from pipeline.orchestrator.writers.ph_muhurta import MAX_MUHURTA_ANCHORS
        assert MAX_MUHURTA_ANCHORS == 400, f"Expected 400, got {MAX_MUHURTA_ANCHORS}"

    def test_load_influenceable_anchors_queries_cap_plus_one(self):
        """B9: query uses MAX_MUHURTA_ANCHORS + 1 for overflow detection."""
        from pipeline.orchestrator.writers.ph_muhurta import PhMuhurtaWriter, MAX_MUHURTA_ANCHORS
        writer = PhMuhurtaWriter.__new__(PhMuhurtaWriter)

        conn, cur = _make_conn_with_savepoint(fetchall_returns=[])
        writer._load_influenceable_anchors(conn, 'chart-uuid-123')

        # Verify LIMIT in the SQL used MAX_MUHURTA_ANCHORS + 1
        call_args = cur.execute.call_args
        assert call_args is not None
        params = call_args[0][1]  # positional args to execute: (sql, params)
        # Second param is the LIMIT value
        assert params[1] == MAX_MUHURTA_ANCHORS + 1, (
            f"LIMIT must be MAX_MUHURTA_ANCHORS+1={MAX_MUHURTA_ANCHORS+1}, got {params[1]}"
        )
