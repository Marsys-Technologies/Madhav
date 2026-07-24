"""CR-37 (SARVA-SIDDHI W-1 T-3): YOGA/DOSHA activation-dating lord resolution.

Root cause fixed here: the ratified binder dumped L1 fact-id HASHES into a
yoga's constituent_lords (config carried no graha key), which never matched a
daśā period (→ undated) and suppressed ka_yojaka's enrichment chain. The writer
now resolves the REAL forming grahā(s) from L1 ga_yoga_firings.constituent_planets
(yoga) / kāla-sarpa nodal axis + graha_position constituent facts (dosha), and
leaves a Nabhasa/ākṛti distribution yoga honestly undated with always_on_reason.

Run: pytest -q tests/l3/test_ka_yojaka_cr37_activation.py -v
"""
import json as _json_mod

import pytest

from services.ka_yojaka.binder import _extract_constituent_lords
from pipeline.orchestrator.writers.ka_yojaka import (
    KaYojakaWriter,
    _resolve_firing_lords,
    DISTRIBUTION_YOGA_MIN_GRAHAS,
)
from pipeline.orchestrator.writers import ContextSpec


# ---------------------------------------------------------------------------
# Binder regression — the fact-id-hash fallback is GONE (root cause)
# ---------------------------------------------------------------------------

def test_binder_no_longer_returns_fact_id_hashes():
    """A yoga_label signal (config has no graha key) must NOT get its
    constituent_facts_array hashes dumped in as lords — that was the bug."""
    sig = {
        'configuration_jsonb': {'fact_key': 'yoga_name', 'fact_value_text': 'Vasi Yoga'},
        'constituent_facts_array': ['050b754375d2181d', 'bc259d75d8a47d22'],
    }
    assert _extract_constituent_lords(sig) == []


def test_binder_still_reads_real_graha_config_keys():
    """When config DOES carry a graha key, the binder still returns it."""
    sig = {'configuration_jsonb': {'grahas': ['sun', 'moon']}, 'constituent_facts_array': ['x']}
    assert _extract_constituent_lords(sig) == ['sun', 'moon']


# ---------------------------------------------------------------------------
# _resolve_firing_lords — YOGA
# ---------------------------------------------------------------------------

_AYAN = 'lahiri_chitrapaksha'


def _yoga_signal(cfa):
    return {'ayanamsha_id': _AYAN, 'signal_type_id': 'yoga_label:yoga_name',
            'constituent_facts_array': cfa}


def test_yoga_bounded_set_resolves_real_forming_grahas():
    """Vasi (sun/jupiter/venus) → those grahas, normalized to canonical names."""
    firings = {(_AYAN, 'vasi'): ['sun', 'jupiter', 'venus']}
    facts = {'yl1': ('yoga_label', 'vasi')}
    lords, reason, src = _resolve_firing_lords(
        _yoga_signal(['yl1', 'gp1']), 'YOGA', {}, firings, facts)
    assert lords == ['Sun', 'Jupiter', 'Venus']
    assert reason is None
    assert src == 'ka_yojaka:ga_yoga_firings'


def test_yoga_single_graha_pancha_mahapurusha():
    """Sasa (saturn only) → [Saturn] — datable Pañca-Mahāpuruṣa yoga."""
    firings = {(_AYAN, 'sasa'): ['saturn']}
    facts = {'yl1': ('yoga_label', 'sasa')}
    lords, reason, _ = _resolve_firing_lords(
        _yoga_signal(['yl1']), 'YOGA', {}, firings, facts)
    assert lords == ['Saturn']
    assert reason is None


def test_yoga_distribution_yoga_stays_undated_with_reason():
    """Kedāra (all 7 grahas) → no lords, always_on_reason set (correctly undated)."""
    seven = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
    firings = {(_AYAN, 'kedara'): seven}
    facts = {'yl1': ('yoga_label', 'kedara')}
    lords, reason, src = _resolve_firing_lords(
        _yoga_signal(['yl1']), 'YOGA', {}, firings, facts)
    assert lords == []
    assert reason == 'distribution_yoga_all_grahas'
    assert src == 'ka_yojaka:ga_yoga_firings'
    assert len(seven) >= DISTRIBUTION_YOGA_MIN_GRAHAS


def test_yoga_sankhya_fire_reason_marks_distribution_yoga():
    """A Nabhasa saṅkhyā yoga (fire_reason '<N>_distinct_signs') is recognized as
    a distribution yoga even when L1 ga_yoga_firings has no row for it (Gola/
    Śūla/Yuga case) — undated with a reason, never a fabricated window."""
    lords, reason, src = _resolve_firing_lords(
        _yoga_signal(['yl_gola']), 'YOGA', {'fire_reason': '4_distinct_signs'}, {}, {})
    assert lords == []
    assert reason == 'distribution_yoga_sankhya'
    assert src == 'ka_yojaka:sankhya_fire_reason'


def test_yoga_requires_pass_point_yoga_not_marked_distribution():
    """A point yoga (fire_reason 'requires_pass') must NOT be caught by the
    saṅkhyā rule — it resolves its real forming grahas instead."""
    firings = {(_AYAN, 'vasi'): ['sun', 'jupiter', 'venus']}
    facts = {'yl1': ('yoga_label', 'vasi')}
    lords, reason, _ = _resolve_firing_lords(
        _yoga_signal(['yl1']), 'YOGA', {'fire_reason': 'requires_pass'}, firings, facts)
    assert reason is None
    assert lords == ['Sun', 'Jupiter', 'Venus']


def test_yoga_no_firing_match_stays_empty_no_fabrication():
    """A panchanga / karaka-flag yoga with no ga_yoga_firings match → empty."""
    lords, reason, src = _resolve_firing_lords(
        _yoga_signal(['unknown_fact']), 'YOGA', {}, {}, {})
    assert (lords, reason, src) == ([], None, None)


def test_yoga_five_graha_still_datable_below_threshold():
    """A 5-graha yoga (e.g. NBRY) is below the distribution threshold → datable."""
    firings = {(_AYAN, 'nbry'): ['venus', 'mercury', 'saturn', 'mars', 'sun']}
    facts = {'yl1': ('yoga_label', 'nbry')}
    lords, reason, _ = _resolve_firing_lords(
        _yoga_signal(['yl1']), 'YOGA', {}, firings, facts)
    assert reason is None
    assert set(lords) == {'Venus', 'Mercury', 'Saturn', 'Mars', 'Sun'}


# ---------------------------------------------------------------------------
# _resolve_firing_lords — DOSHA
# ---------------------------------------------------------------------------

def _dosha_signal(stid, cfa=None):
    return {'ayanamsha_id': _AYAN, 'signal_type_id': stid,
            'constituent_facts_array': cfa or []}


def test_dosha_kala_sarpa_fired_resolves_nodal_axis():
    sig = _dosha_signal('kala_sarpa_per_varga:ks_detection')
    lords, reason, src = _resolve_firing_lords(sig, 'DOSHA', {'fires': True}, {}, {})
    assert lords == ['Rahu', 'Ketu']
    assert reason is None
    assert src == 'ka_yojaka:kala_sarpa_nodal_axis'


def test_dosha_kala_sarpa_not_fired_stays_empty():
    sig = _dosha_signal('kala_sarpa_per_varga:ks_detection')
    assert _resolve_firing_lords(sig, 'DOSHA', {'fires': False}, {}, {}) == ([], None, None)


def test_dosha_label_fired_resolves_constituent_grahas():
    """Kemadruma (fired) → Moon, via its graha_position constituent facts."""
    facts = {'dl1': ('dosha_label', 'kemadruma'),
             'gp1': ('graha_position', 'MOON'),
             'gp2': ('graha_position', 'MOON')}
    sig = _dosha_signal('dosha_label:dosha_name', ['dl1', 'gp1', 'gp2'])
    lords, reason, src = _resolve_firing_lords(sig, 'DOSHA', {'fires': True}, {}, facts)
    assert lords == ['Moon']
    assert src == 'ka_yojaka:dosha_constituent_grahas'


def test_dosha_label_requires_pass_catalog_only_stays_empty():
    """An unfired (requires_pass) catalog-only dosha must NOT be dated (B.10)."""
    facts = {'dl1': ('dosha_label', 'mangala'), 'gp1': ('graha_position', 'MARS')}
    sig = _dosha_signal('dosha_label:dosha_name', ['dl1', 'gp1'])
    # No 'fires' key at all → requires_pass catalog row.
    assert _resolve_firing_lords(sig, 'DOSHA', {'fire_reason': 'requires_pass'}, {}, facts) == ([], None, None)


# ---------------------------------------------------------------------------
# Prefetch helper methods (SAVEPOINT-guarded soft dependencies)
# ---------------------------------------------------------------------------

class _FakeCursor:
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


class TestFetchYogaFiringPlanets:
    def test_builds_map_and_parses_list(self):
        rows = [
            {'ayanamsha_id': _AYAN, 'yoga_canonical_id': 'vasi',
             'constituent_planets': ['sun', 'jupiter', 'venus']},
            {'ayanamsha_id': _AYAN, 'yoga_canonical_id': 'sasa',
             'constituent_planets': '["saturn"]'},  # JSON string variant
        ]
        conn = _FakeConn({'SAVEPOINT': [], 'FROM ga_yoga_firings': rows})
        w = KaYojakaWriter()
        result = w._fetch_yoga_firing_planets(conn, 'cid')
        assert result[(_AYAN, 'vasi')] == ['sun', 'jupiter', 'venus']
        assert result[(_AYAN, 'sasa')] == ['saturn']

    def test_query_failure_returns_empty(self):
        class _RaisingCursor(_FakeCursor):
            def execute(self, sql, params=None):
                if 'FROM ga_yoga_firings' in sql:
                    raise RuntimeError('drift')
                super().execute(sql, params)

        class _RaisingConn(_FakeConn):
            def cursor(self, *a, **k):
                return _RaisingCursor(self._rows_by_marker)

        conn = _RaisingConn({'SAVEPOINT': [], 'FROM ga_yoga_firings': []})
        assert KaYojakaWriter()._fetch_yoga_firing_planets(conn, 'cid') == {}


class TestFetchActivationSourceFacts:
    def test_builds_category_subject_map(self):
        rows = [
            {'fact_id': 'yl1', 'fact_category': 'yoga_label', 'fact_subject': 'vasi'},
            {'fact_id': 'gp1', 'fact_category': 'graha_position', 'fact_subject': 'SUN'},
        ]
        conn = _FakeConn({'SAVEPOINT': [], 'FROM chart_facts': rows})
        result = KaYojakaWriter()._fetch_activation_source_facts(conn, 'cid')
        assert result['yl1'] == ('yoga_label', 'vasi')
        assert result['gp1'] == ('graha_position', 'SUN')


# ---------------------------------------------------------------------------
# Integration — run() dates a yoga_label signal from ga_yoga_firings
# ---------------------------------------------------------------------------

class _RunCursor:
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
        if 'DELETE FROM' in sql or 'SET LOCAL' in sql or 'SAVEPOINT' in sql:
            return
        if 'FROM ga_yoga_firings' in sql:
            self._pending = c.yoga_firing_rows
            return
        if "fact_category IN ('yoga_label'" in sql:
            self._pending = c.activation_fact_rows
            return
        if 'lord_in_house_per_varga' in sql:
            self._pending = []
            return
        if 'fact_id = ANY' in sql:
            self._pending = []
            return
        if 'FROM bodha_msr_signals' in sql:
            self._pending = c.signal_rows
            return
        self._pending = []

    def executemany(self, sql, batch):
        self._conn.inserted.extend(batch)

    def fetchall(self):
        return self._pending


class _RunConn:
    def __init__(self, signal_rows, yoga_firing_rows, activation_fact_rows):
        self.signal_rows = signal_rows
        self.yoga_firing_rows = yoga_firing_rows
        self.activation_fact_rows = activation_fact_rows
        self.inserted = []

    def cursor(self, *a, **k):
        return _RunCursor(self)


def _sig(signal_id, stid, cfa, stc='yoga'):
    return {'signal_id': signal_id, 'chart_id': 'cid', 'ayanamsha_id': _AYAN,
            'signal_type_class': stc, 'signal_type_id': stid,
            'configuration_jsonb': {'fact_key': 'yoga_name', 'fact_value_text': 'X'},
            'constituent_facts_array': cfa, 'valence': 0.0,
            'dignity_score': 0.8, 'shadbala_norm': 1.0}


def _run(signal_rows, yoga_firing_rows, activation_fact_rows):
    conn = _RunConn(signal_rows, yoga_firing_rows, activation_fact_rows)
    ctx = ContextSpec(asset_id='ka_yojaka', build_id='b1', db_conn=conn,
                      config={'chart_id': 'cid'})
    KaYojakaWriter().run(ctx)
    return conn


def test_run_dates_bounded_yoga_from_firings():
    """End-to-end: a yoga_label signal whose canonical id (via its yoga_label
    constituent fact) matches a bounded ga_yoga_firings row gets the REAL
    forming grahas as constituent_lords — the fix that un-dark-ens CR-37."""
    sig = _sig('s1', 'yoga_label:yoga_name', ['yl1', 'gp1'])
    firing = [{'ayanamsha_id': _AYAN, 'yoga_canonical_id': 'vasi',
               'constituent_planets': ['sun', 'jupiter', 'venus']}]
    facts = [{'fact_id': 'yl1', 'fact_category': 'yoga_label', 'fact_subject': 'vasi'},
             {'fact_id': 'gp1', 'fact_category': 'graha_position', 'fact_subject': 'SUN'}]
    conn = _run([sig], firing, facts)
    assert len(conn.inserted) == 1
    rule = _json_mod.loads(conn.inserted[0][4])
    assert rule['constituent_lords'] == ['Sun', 'Jupiter', 'Venus']
    assert rule['constituent_lords_source'] == 'ka_yojaka:ga_yoga_firings'
    assert 'always_on_reason' not in rule


def test_run_distribution_yoga_marks_always_on():
    """A 7-graha distribution yoga gets no lords but an always_on_reason."""
    sig = _sig('s2', 'yoga_label:yoga_name', ['yl1'])
    seven = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
    firing = [{'ayanamsha_id': _AYAN, 'yoga_canonical_id': 'kedara',
               'constituent_planets': seven}]
    facts = [{'fact_id': 'yl1', 'fact_category': 'yoga_label', 'fact_subject': 'kedara'}]
    conn = _run([sig], firing, facts)
    rule = _json_mod.loads(conn.inserted[0][4])
    assert rule['constituent_lords'] == []
    assert rule['always_on_reason'] == 'distribution_yoga_all_grahas'
