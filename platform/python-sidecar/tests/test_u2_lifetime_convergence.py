"""
test_u2_lifetime_convergence.py — R3 U2 lifetime convergence acceptance tests.

Covers:
  - ka_sangam writer produces rows with horizon_tier IN ('near', 'lifetime') — both tiers
  - horizon_tier column values are valid (only 'near' or 'lifetime')
  - lifetime rows exist (count > 0)
  - near-tier rows unchanged (same generation logic, ~660 windows)
  - WriterResult.rows_inserted >= (near_count + lifetime_count)
  - convergence scores stay in [0,1] for lifetime rows
  - Contract: writer never commits/closes ctx.db_conn
  - Anti-drift: writer writes only kala_convergence (L3), never any phala_* table

DB-free: psycopg2 connection + cursor mocked; engine Mode A/B monkeypatched
to canned windows (no swisseph, no ephemeris). Mirrors the mock/fixture style
of test_ph_nimitta_spine.py.
"""
from __future__ import annotations

import os
import re
from datetime import date
from unittest.mock import MagicMock

import pytest

import pipeline.orchestrator.writers.ka_sangam as ks_mod
from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter


CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'


# ── fakes ─────────────────────────────────────────────────────────────────────

class FakeCursor:
    """
    Minimal cursor that records every INSERT and answers the writer's SELECTs.

    SELECT routing by SQL substring:
      - kala_activation_predicates → predicate rows
      - bodha_msr_signals          → dignity rows
      - kala_jivana_parva          → parva-boundary rows (lifetime anchors)
      - chart_dashas               → birth-date fallback (unused when parvas exist)
    """
    def __init__(self, store):
        self._store = store
        self._last_sql = ''
        self._result: list = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._last_sql = sql
        low = sql.lower()
        if 'insert into kala_convergence' in low:
            # Capture the horizon_tier (last positional param) + score
            self._store['inserts'].append({'sql': sql, 'params': params})
            self._result = []
        elif 'delete from' in low:
            self._result = []
        elif 'kala_activation_predicates' in low:
            self._result = self._store['predicates']
        elif 'bodha_msr_signals' in low:
            # plan_substeps SELECT includes domains_affected_array (B4-src domain enrichment).
            self._result = [
                {
                    'signal_id': sig,
                    'dignity_score': score,
                    'graha_name': None,
                    'house_num': None,
                    'domains_affected_array': None,
                }
                for sig, score in self._store['dignity']
            ]
        elif 'kala_jivana_parva' in low:
            self._result = self._store['parvas']
        elif 'chart_dashas' in low:
            self._result = [{'birth_date': date(1984, 2, 5)}]
        else:
            self._result = []

    def fetchall(self):
        return self._result

    def fetchone(self):
        return self._result[0] if self._result else None


class FakeConn:
    def __init__(self, store):
        self._store = store
        self.committed = False
        self.closed = False
        self.rolled_back = False

    def cursor(self, cursor_factory=None, row_factory=None):
        return FakeCursor(self._store)

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True

    def rollback(self):
        self.rolled_back = True


class FakeCtx:
    def __init__(self, conn):
        self.db_conn = conn
        self.config = {'chart_id': CHART_ID}
        self.dry_run = False


def _window(score=0.6, peak=date(2026, 9, 1), mode='A', sig='sig-1'):
    return {
        'mode': mode,
        'window_start': peak,
        'window_end': peak,
        'peak_date': peak,
        'convergence_score': score,
        'orb_strength': 0.5,
        'rarity_years': 7.5,
        'constituent_factors': {'dasha_score': 0.8, 'planet': 'Jupiter'},
        'source_citation': f'mode_{mode.lower()}/test',
        'is_off_dasha_discovery': mode == 'B',
        'signal_id': sig,
    }


@pytest.fixture
def store():
    return {
        'predicates': [
            {
                'id': i,
                'chart_id': CHART_ID,
                'ayanamsha_id': 'lahiri',
                'signal_id': f'sig-{i}',
                'signature_class': 'CAREER_PEAK',
                'dasha_eligibility_rule_jsonb': {},
                'transit_trigger_jsonb': {},
                'strength_affliction_hook_jsonb': {},
                'derivation_ledger_jsonb': {},
            }
            for i in range(3)
        ],
        'dignity': [(f'sig-{i}', 0.6) for i in range(3)],
        # 7 parva boundaries spanning the native's life
        'parvas': [
            (1984, 1990), (1990, 2007), (2007, 2014), (2014, 2034),
            (2034, 2050), (2050, 2070), (2070, 2090),
        ],
        'inserts': [],
    }


@pytest.fixture
def patched_engine(monkeypatch):
    """Monkeypatch Mode A/B so each predicate × span yields deterministic windows."""
    counter = {'n': 0}

    def fake_mode_a(predicate, horizon_start_jd, horizon_end_jd, **kw):
        counter['n'] += 1
        # vary peak by horizon so dedup keeps distinct rows per span
        base = int(horizon_start_jd) % 9000
        return [_window(score=0.55, peak=date(2000 + (base % 90), 6, 1),
                        mode='A', sig=predicate.get('signal_id'))]

    def fake_mode_b(signal_id, predicate, horizon_start_jd, horizon_end_jd, **kw):
        base = int(horizon_start_jd) % 9000
        return [_window(score=0.42, peak=date(2000 + (base % 90), 9, 1),
                        mode='B', sig=signal_id)]

    monkeypatch.setattr(ks_mod, 'mode_a_search', fake_mode_a)
    monkeypatch.setattr(ks_mod, 'mode_b_sweep', fake_mode_b)
    # Avoid touching swisseph for dasha/gochara service construction
    monkeypatch.setattr(ks_mod, 'KaDashaKalaService', lambda conn: MagicMock())
    monkeypatch.setattr(ks_mod, 'KaGocharaService', lambda swe: MagicMock())
    return counter


def _run(store):
    conn = FakeConn(store)
    writer = KaSangamWriter()
    result = writer.run(FakeCtx(conn))
    # INSERT tuple tail: ..., horizon_tier, domain, confidence_label_relative, tier_basis
    # (JL-014 appended the last two — see test_ka_sangam_a3_fixes.py for the same fix).
    tiers = [ins['params'][-4] for ins in store['inserts']]
    return result, conn, tiers


# ── tests ─────────────────────────────────────────────────────────────────────

class TestBothTiers:
    def test_both_tiers_present(self, store, patched_engine):
        _, _, tiers = _run(store)
        assert 'near' in tiers
        assert 'lifetime' in tiers

    def test_horizon_tier_values_valid(self, store, patched_engine):
        _, _, tiers = _run(store)
        assert set(tiers) <= {'near', 'lifetime'}

    def test_lifetime_rows_exist(self, store, patched_engine):
        _, _, tiers = _run(store)
        assert tiers.count('lifetime') > 0

    def test_near_rows_exist(self, store, patched_engine):
        _, _, tiers = _run(store)
        assert tiers.count('near') > 0


class TestRowAccounting:
    def test_rows_inserted_matches_total(self, store, patched_engine):
        result, _, tiers = _run(store)
        near_n = tiers.count('near')
        life_n = tiers.count('lifetime')
        assert result.rows_inserted == len(tiers)
        assert result.rows_inserted >= near_n + life_n

    def test_asset_id_correct(self, store, patched_engine):
        result, _, _ = _run(store)
        assert result.asset_id == 'ka_sangam'

    def test_lifetime_budget_respected(self, store, patched_engine):
        _, _, tiers = _run(store)
        assert tiers.count('lifetime') <= ks_mod._LIFETIME_MAX_ROWS


class TestScores:
    def test_scores_in_unit_interval(self, store, patched_engine):
        _, _, _ = _run(store)
        # INSERT tuple positional layout: (chart_id=0, window_start=1, window_end=2,
        # convergence_score=3, ...).  Index 3 = convergence_score.
        # If the INSERT column order ever changes, update this index accordingly.
        for ins in store['inserts']:
            cs = ins['params'][3]  # index 3 = convergence_score
            assert 0.0 <= cs <= 1.0


class TestContract:
    def test_writer_never_commits_or_closes(self, store, patched_engine):
        _, conn, _ = _run(store)
        assert conn.committed is False
        assert conn.closed is False
        assert conn.rolled_back is False

    def test_source_has_no_commit_calls(self):
        """No real .commit()/.close()/.rollback() call sites (docstrings/comments excluded)."""
        import ast
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator',
            'writers', 'ka_sangam.py',
        )
        with open(path) as f:
            src = f.read()
        tree = ast.parse(src)
        forbidden = {'commit', 'close', 'rollback'}
        bad = [
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in forbidden
        ]
        assert not bad, f'writer must not call {bad} on its connection'


class TestAntiDrift:
    def test_writer_only_writes_kala_convergence(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator',
            'writers', 'ka_sangam.py',
        )
        with open(path) as f:
            src = f.read()
        inserts = re.findall(r'INSERT INTO (\w+)', src)
        assert inserts, 'expected at least one INSERT'
        for tbl in inserts:
            assert tbl == 'kala_convergence', f'unexpected INSERT target: {tbl}'

    def test_writer_writes_no_phala_table(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator',
            'writers', 'ka_sangam.py',
        )
        with open(path) as f:
            src = f.read()
        assert 'phala_' not in src.lower(), 'ka_sangam must not reference any phala_* table'


class TestLifetimeFallback:
    def test_fallback_when_no_parvas(self, store, patched_engine):
        """No parvas → lifetime tier falls back to a single birth+100y span."""
        store['parvas'] = []
        _, _, tiers = _run(store)
        assert tiers.count('lifetime') > 0  # fallback span still produces windows
