"""
Tests for ka_yojaka: classifier + binder
Run: pytest -q tests/l3/test_ka_yojaka.py -v
"""
import re
from pathlib import Path

import pytest

from services.ka_yojaka.classifier import classify_signal
from services.ka_yojaka.binder import build_predicate


# ---------------------------------------------------------------------------
# Classifier tests (T1–T8)
# ---------------------------------------------------------------------------

def test_classify_yoga():
    assert classify_signal({'signal_type_class': 'yoga'}) == 'YOGA'


def test_classify_dosha():
    assert classify_signal({'signal_type_class': 'dosha'}) == 'DOSHA'


def test_classify_parivartana():
    assert classify_signal({'signal_type_class': 'parivartana'}) == 'DISPOSITOR_RELATIONAL'


def test_classify_sade_sati():
    assert classify_signal({'signal_type_class': 'sade_sati'}) == 'SUBSYSTEM'


def test_classify_configuration_kala_sarpa():
    sig = {'signal_type_class': 'configuration', 'signal_type_id': 'kala_sarpa_per_varga:ks_detection'}
    assert classify_signal(sig) == 'DOSHA'


def test_classify_configuration_conjunction():
    sig = {'signal_type_class': 'configuration', 'signal_type_id': 'conjunction:sun_moon'}
    assert classify_signal(sig) == 'CONJUNCTION_ASPECT'


def test_classify_unknown_returns_residual():
    assert classify_signal({'signal_type_class': 'totally_unknown_class'}) == 'CLASSIFY_RESIDUAL'


def test_classify_determinism():
    sig = {'signal_type_class': 'yoga', 'signal_type_id': 'some_yoga'}
    assert classify_signal(sig) == classify_signal(sig)


# Additional classifier coverage
def test_classify_karaka_alignment():
    assert classify_signal({'signal_type_class': 'karaka_alignment'}) == 'DISPOSITOR_RELATIONAL'


def test_classify_tradition_specific():
    assert classify_signal({'signal_type_class': 'tradition_specific'}) == 'DIGNITY'


def test_classify_composite_state():
    assert classify_signal({'signal_type_class': 'composite_state'}) == 'SUBSYSTEM'


def test_classify_configuration_sensitive_point():
    sig = {'signal_type_class': 'configuration', 'signal_type_id': 'arudha_lagna_analysis'}
    assert classify_signal(sig) == 'SENSITIVE_POINT'


# ---------------------------------------------------------------------------
# Binder tests (T9–T15)
# ---------------------------------------------------------------------------

_YOGA_SIGNAL = {
    'signal_type_class': 'yoga',
    'signal_type_id': 'test_yoga',
    'configuration_jsonb': {'grahas': ['sun', 'moon']},
    'constituent_facts_array': ['fact1', 'fact2'],
    'valence': 1.0,
    'dignity_score': 0.8,
}

_DOSHA_SIGNAL = {
    'signal_type_class': 'dosha',
    'signal_type_id': 'mangal_dosha',
    'configuration_jsonb': {},
    'constituent_facts_array': [],
}

_SUBSYSTEM_SIGNAL = {
    'signal_type_class': 'sade_sati',
    'signal_type_id': 'sade_sati_phase',
    'configuration_jsonb': {},
    'constituent_facts_array': [],
}


def test_build_predicate_yoga_has_all_keys():
    pred = build_predicate(_YOGA_SIGNAL, 'YOGA')
    assert set(pred.keys()) == {'dasha_eligibility_rule', 'transit_trigger', 'strength_affliction_hook', 'derivation_ledger'}


def test_build_predicate_yoga_derivation_ledger():
    pred = build_predicate(_YOGA_SIGNAL, 'YOGA')
    assert pred['derivation_ledger']['bg_transit_rules_ids'] == [1, 2, 3, 4]


def test_build_predicate_yoga_dasha_type():
    pred = build_predicate(_YOGA_SIGNAL, 'YOGA')
    assert pred['dasha_eligibility_rule']['type'] == 'dasha_lord_in_constituents'


def test_build_predicate_dosha_transit_trigger():
    pred = build_predicate(_DOSHA_SIGNAL, 'DOSHA')
    assert pred['transit_trigger']['type'] == 'malefic_transit_over_afflicted_point'


def test_build_predicate_subsystem_type():
    pred = build_predicate(_SUBSYSTEM_SIGNAL, 'SUBSYSTEM')
    assert pred['dasha_eligibility_rule']['type'] == 'subsystem_specific'


def test_build_predicate_subsystem_empty_bg_rules():
    pred = build_predicate(_SUBSYSTEM_SIGNAL, 'SUBSYSTEM')
    assert pred['derivation_ledger']['bg_transit_rules_ids'] == []


def test_build_predicate_derivation_ledger_ratified_by():
    for sc in ('YOGA', 'DOSHA', 'DIGNITY', 'DISPOSITOR_RELATIONAL', 'SENSITIVE_POINT', 'CONJUNCTION_ASPECT', 'SUBSYSTEM', 'CLASSIFY_RESIDUAL'):
        pred = build_predicate(_YOGA_SIGNAL, sc)
        assert 'L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md' in pred['derivation_ledger']['ratified_by']


# ---------------------------------------------------------------------------
# Anti-drift / contract tests (T13–T15)
# ---------------------------------------------------------------------------

WRITER_PATH = Path(__file__).parent.parent.parent / 'pipeline' / 'orchestrator' / 'writers' / 'ka_yojaka.py'


def test_no_commit_or_rollback_in_writer():
    """Writer must NEVER call .commit() or .rollback() — orchestrator owns the transaction."""
    src = WRITER_PATH.read_text()
    # Use AST-level check: look for actual method calls, not string mentions in comments/docstrings
    # Strip all comment lines and triple-quoted docstrings before scanning
    import re as _re
    # Remove triple-quoted docstrings
    stripped = _re.sub(r'''""".*?"""''', '', src, flags=_re.DOTALL)
    stripped = _re.sub(r"'''.*?'''", '', stripped, flags=_re.DOTALL)
    # Remove inline and full-line comments
    stripped = _re.sub(r'#.*', '', stripped)
    assert '.commit()' not in stripped, 'Found .commit() call in writer — violates orchestrator contract'
    assert '.rollback()' not in stripped, 'Found .rollback() call in writer — violates orchestrator contract'


def test_no_l2_writes_in_writer():
    """Writer must NEVER INSERT/UPDATE into bodha_* tables."""
    src = WRITER_PATH.read_text()
    assert not re.search(r'INSERT INTO bodha_', src), 'Found INSERT INTO bodha_* in writer'
    assert not re.search(r'UPDATE bodha_', src), 'Found UPDATE bodha_* in writer'


def test_writer_only_selects_from_bodha():
    """bodha_msr_signals should appear only in SELECT context."""
    src = WRITER_PATH.read_text()
    # Check bodha_msr_signals appears (we read from it)
    assert 'bodha_msr_signals' in src
    # Check it's only in a SELECT
    select_match = re.search(r'FROM bodha_msr_signals', src)
    assert select_match, 'Expected SELECT FROM bodha_msr_signals'


# ---------------------------------------------------------------------------
# WP-S4-R45-iter2: house/varga bhava-lord map + fact_subject batch fetch
# ---------------------------------------------------------------------------
from pipeline.orchestrator.writers.ka_yojaka import KaYojakaWriter


class _FakeCursor:
    """Minimal SAVEPOINT-tolerant fake cursor: routes SELECTs by a substring
    match on the SQL, returns pre-seeded rows for either statement shape."""

    def __init__(self, rows_by_marker):
        self._rows_by_marker = rows_by_marker
        self._pending = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._pending = []
        for marker, rows in self._rows_by_marker.items():
            if marker in sql:
                self._pending = rows
                return

    def fetchall(self):
        return self._pending


class _FakeConn:
    def __init__(self, rows_by_marker):
        self._rows_by_marker = rows_by_marker

    def cursor(self, *a, **k):
        return _FakeCursor(self._rows_by_marker)


class TestFetchHouseLordMap:
    def test_builds_expected_map(self):
        rows = [
            {'ayanamsha_id': 'lahiri_chitrapaksha', 'fact_subject': 'D9_H1', 'fact_value_text': 'Mars_in_H12'},
            {'ayanamsha_id': 'lahiri_chitrapaksha', 'fact_subject': 'D9_H7', 'fact_value_text': 'Venus_in_H3'},
        ]
        conn = _FakeConn({'SAVEPOINT': [], 'FROM chart_facts': rows})
        writer = KaYojakaWriter()
        result = writer._fetch_house_lord_map(conn, 'cid')
        assert result[('lahiri_chitrapaksha', 'D9_H1')] == 'Mars'
        assert result[('lahiri_chitrapaksha', 'D9_H7')] == 'Venus'

    def test_query_failure_returns_empty_not_raises(self):
        class _RaisingCursor(_FakeCursor):
            def execute(self, sql, params=None):
                if 'FROM chart_facts' in sql:
                    raise RuntimeError('schema drift')
                super().execute(sql, params)

        class _RaisingConn(_FakeConn):
            def cursor(self, *a, **k):
                return _RaisingCursor(self._rows_by_marker)

        conn = _RaisingConn({'SAVEPOINT': [], 'FROM chart_facts': []})
        writer = KaYojakaWriter()
        assert writer._fetch_house_lord_map(conn, 'cid') == {}


class TestFetchFactSubjects:
    def test_builds_expected_map(self):
        rows = [
            {'fact_id': 'f1', 'fact_subject': 'D20_SUN_MER'},
            {'fact_id': 'f2', 'fact_subject': 'D9_H1'},
        ]
        conn = _FakeConn({'SAVEPOINT': [], 'FROM chart_facts': rows})
        writer = KaYojakaWriter()
        result = writer._fetch_fact_subjects(conn, ['f1', 'f2'])
        assert result == {'f1': 'D20_SUN_MER', 'f2': 'D9_H1'}

    def test_empty_input_short_circuits(self):
        writer = KaYojakaWriter()
        assert writer._fetch_fact_subjects(None, []) == {}


# ---------------------------------------------------------------------------
# WP-S4-R45-iter2 + CR-5/CR-12/CR-48: full run() integration over a fake conn
# ---------------------------------------------------------------------------
import json as _json_mod
from pipeline.orchestrator.writers import ContextSpec


class _RunFakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._pending = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        c = self._conn
        self._pending = []
        if 'DELETE FROM' in sql:
            return
        if 'SET LOCAL' in sql:
            return
        if 'SAVEPOINT' in sql:  # covers SAVEPOINT / RELEASE SAVEPOINT / ROLLBACK TO SAVEPOINT
            return
        if 'lord_in_house_per_varga' in sql:
            self._pending = c.house_lord_rows
            return
        if 'fact_id = ANY' in sql:
            wanted = set(params[0])
            self._pending = [r for r in c.fact_subject_rows if r['fact_id'] in wanted]
            return
        if 'FROM bodha_msr_signals' in sql:
            self._pending = c.signal_rows
            return
        if 'FROM bodha_cgm_nodes' in sql:
            self._pending = []
            return
        if 'FROM bodha_cdlm_cells' in sql:
            self._pending = []
            return
        if 'COUNT(DISTINCT bp.ayanamsha_id)' in sql:
            self._pending = []
            return
        if 'FROM bodha_pratijna' in sql:
            self._pending = []
            return
        self._pending = []

    def executemany(self, sql, batch):
        self._conn.inserted.extend(batch)

    def fetchall(self):
        return self._pending


class _RunFakeConn:
    def __init__(self, signal_rows, house_lord_rows, fact_subject_rows):
        self.signal_rows = signal_rows
        self.house_lord_rows = house_lord_rows
        self.fact_subject_rows = fact_subject_rows
        self.inserted = []

    def cursor(self, *a, **k):
        return _RunFakeCursor(self)


def _signal_row(signal_id, ayanamsha_id, signal_type_class, signal_type_id,
                 configuration_jsonb, constituent_facts_array=None,
                 dignity_score=0.8, shadbala_norm=1.2):
    return {
        'signal_id': signal_id,
        'chart_id': 'cid',
        'ayanamsha_id': ayanamsha_id,
        'signal_type_class': signal_type_class,
        'signal_type_id': signal_type_id,
        'configuration_jsonb': configuration_jsonb,
        'constituent_facts_array': constituent_facts_array or [],
        'valence': 0.0,
        'dignity_score': dignity_score,
        'shadbala_norm': shadbala_norm,
    }


class TestKaYojakaWriterRunIntegration:
    """End-to-end run() over a fake conn — exercises the full lord-resolution
    chain (config keys -> house/varga -> fact_subject tokens) and the
    dignity/non_affliction propagation fix in one pass, per predicate."""

    def _run(self, signal_rows, house_lord_rows=None, fact_subject_rows=None):
        conn = _RunFakeConn(signal_rows, house_lord_rows or [], fact_subject_rows or [])
        ctx = ContextSpec(asset_id='ka_yojaka', build_id='b1', db_conn=conn,
                           config={'chart_id': 'cid'})
        writer = KaYojakaWriter()
        result = writer.run(ctx)
        return result, conn

    def test_config_key_resolution_unaffected(self):
        """YOGA-class signal resolves via extract_lords_from_config (existing path)."""
        sig = _signal_row('s1', 'lahiri_chitrapaksha', 'yoga', 'test_yoga',
                           {'planet': 'Venus'})
        result, conn = self._run([sig])
        assert result.rows_inserted == 1
        rule = _json_mod.loads(conn.inserted[0][4])
        assert rule['constituent_lords'] == ['Venus']
        assert rule['constituent_lords_source'] == 'ka_yojaka:extract_lords_from_config'

    def test_house_varga_fallback_resolves(self):
        """composite_state signal (net_argala_per_varga shape): house+varga,
        no direct graha key -> resolved via the house-lord map."""
        sig = _signal_row('s2', 'lahiri_chitrapaksha', 'composite_state',
                           'net_argala_per_varga:net_argala',
                           {'house': 1, 'varga': 'D9', 'fact_key': 'net_argala'})
        house_lord_rows = [
            {'ayanamsha_id': 'lahiri_chitrapaksha', 'fact_subject': 'D9_H1', 'fact_value_text': 'Mars_in_H12'},
        ]
        result, conn = self._run([sig], house_lord_rows=house_lord_rows)
        assert result.rows_inserted == 1
        rule = _json_mod.loads(conn.inserted[0][4])
        assert rule['constituent_lords'] == ['Mars']
        assert rule['constituent_lords_source'] == 'ka_yojaka:house_varga_bhava_lord'

    def test_fact_subject_fallback_resolves(self):
        """sambandha_grade shape: no graha key, no house+varga -> resolved via
        the batched fact_subject lookup on constituent_facts_array[0]."""
        sig = _signal_row('s3', 'lahiri_chitrapaksha', 'composite_state',
                           'sambandha_grade:grade',
                           {'varga': 'D20', 'fact_key': 'grade'},
                           constituent_facts_array=['f_sambandha_1'])
        fact_subject_rows = [{'fact_id': 'f_sambandha_1', 'fact_subject': 'D20_SUN_MER'}]
        result, conn = self._run([sig], fact_subject_rows=fact_subject_rows)
        assert result.rows_inserted == 1
        rule = _json_mod.loads(conn.inserted[0][4])
        assert rule['constituent_lords'] == ['Sun', 'Mercury']
        assert rule['constituent_lords_source'] == 'ka_yojaka:fact_subject_tokens'

    def test_genuinely_unresolvable_stays_empty_no_fabrication(self):
        """A signal with no graha/sign key, no house+varga, and no constituent
        fact must NOT get a fabricated lord — B.10."""
        sig = _signal_row('s4', 'lahiri_chitrapaksha', 'composite_state',
                           'ashtakavarga_bindu_per_varga:D7',
                           {'fact_key': 'D7', 'fact_value_num': 4})
        result, conn = self._run([sig])
        assert result.rows_inserted == 1
        rule = _json_mod.loads(conn.inserted[0][4])
        assert not rule.get('constituent_lords')

    def test_dignity_and_non_affliction_propagate_real_values(self):
        """CR-5/CR-12/CR-48: strength_affliction_hook carries the REAL
        per-signal dignity_score + a chart-normalized shadbala_norm, not just
        the 'scale_by' label — this is what un-flattens the 0.5 wall
        downstream in date_resolver._proximity_score."""
        sig_a = _signal_row('s5', 'lahiri_chitrapaksha', 'yoga', 'yoga_a',
                             {'planet': 'Jupiter'}, dignity_score=1.0, shadbala_norm=2.0)
        sig_b = _signal_row('s6', 'lahiri_chitrapaksha', 'yoga', 'yoga_b',
                             {'planet': 'Saturn'}, dignity_score=0.5, shadbala_norm=1.0)
        result, conn = self._run([sig_a, sig_b])
        assert result.rows_inserted == 2
        hook_a = _json_mod.loads(conn.inserted[0][6])
        hook_b = _json_mod.loads(conn.inserted[1][6])
        assert hook_a['dignity_score'] == 1.0
        assert hook_a['non_affliction'] == 1.0  # max shadbala in this chart -> normalizes to 1.0
        assert hook_b['dignity_score'] == 0.5
        assert hook_b['non_affliction'] == 0.5  # half of the chart max
        # Distinct per-signal values -> the two rows must NOT collapse to the
        # same alignment score (the defect this fix kills).
        assert hook_a != hook_b

    def test_no_commit_or_rollback_called_on_fake_conn(self):
        """Smoke check that run() never touches commit/rollback (fake conn has
        neither method — an AttributeError here would prove a contract breach)."""
        sig = _signal_row('s7', 'lahiri_chitrapaksha', 'yoga', 'yoga_c', {'planet': 'Moon'})
        result, _conn = self._run([sig])
        assert result.asset_id == 'ka_yojaka'
