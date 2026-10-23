"""SR-K9-TRIAGE-DUP, database half: the K9 round-B2 failure, reproduced with the smallest fixture and read by the REAL registered contract.

The fixture is the shape of the failed rebuild: two predicates with NO signal_id and NO resolved target (ka_yojaka's honest NULLs), one near call and
two lifetime calls, Mode D computed by the real engine over a one-sign SAV map. The rows the writer's own `_insert_windows` would INSERT are loaded into
a table carrying the columns the contract reads, and the contract text is the stored one (migration 670 conjuncts, 1405 generation splice) - never a
reimplementation. Before the fix: conjunct (a) 1 duplicate group per lifetime window and (g) every row; after it: the contract reads true.
"""
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import psycopg
import pytest

from pipeline.orchestrator.writers import ka_sangam as ks
from services.ka_sangam.engine import EnrichmentContext, _date_to_jd

ROOT = Path(__file__).resolve().parents[6]
MIGRATIONS = ROOT / 'platform/migrations'
NATIVE = SimpleNamespace(janma_nakshatra_idx=24, moon_sign='Aquarius', location={'lat': 20.3, 'lon': 85.8})
NULL_TARGET = {'target_identity': None, 'target_longitude_deg': None, 'null_reason': 'target_unresolved'}
COLUMNS = ('chart_id', 'window_start', 'window_end', 'convergence_score', 'constituent_factors', 'source_citation', 'signal_id', 'mode',
           'peak_date', 'orb_strength', 'rarity_years', 'confidence_score', 'confidence_label', 'independent_current_count',
           'is_off_dasha_discovery', 'horizon_tier', 'domain', 'confidence_label_relative', 'tier_basis', 'generation')
SIGNAL_A, SIGNAL_B = '00000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000b'


def registered_contract() -> str:
    """The 670 ka_sangam contract with the 1405 generation-scoped accretion key spliced in, exactly as 1405 does."""
    text = (MIGRATIONS / '670_nirmana_l3_w3_integrity_contracts.sql').read_text()
    found = []
    for block in text.split('UPDATE asset_registry SET integrity_check_sql = $ck$')[1:]:
        body, _, after = block.partition('$ck$')
        if re.match(r"\s*WHERE asset_id = 'ka_sangam';", after):
            found.append(body)
    assert len(found) == 1
    return found[0].replace('GROUP BY chart_id, horizon_tier,', 'GROUP BY chart_id, generation, horizon_tier,')


class _Cursor:
    def __init__(self, sink):
        self.sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if 'INSERT INTO kala_convergence' in sql:
            self.sink.append(dict(zip(COLUMNS, params)))

    def fetchone(self):
        return None


class _Conn:
    def __init__(self):
        self.rows = []

    def cursor(self, *a, **kw):
        return _Cursor(self.rows)


def _writer(preds, monkeypatch):
    monkeypatch.setattr(ks, 'has_stored_verification', lambda cur, table: False)
    gochara = MagicMock()
    ingress = SimpleNamespace(event_jd=_date_to_jd(date(2027, 3, 21)))
    gochara.find_ingresses.side_effect = lambda planet, target_sign, start_jd, end_jd: [ingress] if target_sign == 'Aries' else []
    writer = ks.KaSangamWriter.__new__(ks.KaSangamWriter)
    writer._conv_generation = 'candidate:k9'
    writer._pred_dicts = writer._lt_preds = preds
    writer._birth_year = 1984
    writer._resume_fingerprint = 'fixture'
    writer._dks = writer._muhurta = None
    writer._gs = gochara
    writer._enrichment_ctx = EnrichmentContext(ashtakavarga_bindu={'SARVA': {1: 32}})
    writer._native_ctx = NATIVE
    return writer


def _rebuild(preds, monkeypatch):
    writer, conn = _writer(preds, monkeypatch), _Conn()
    writer._substep_near(conn, 'c', dry_run=False)
    for idx in range(len(preds)):
        writer._substep_lifetime(conn, 'c', idx, dry_run=False)
    return conn.rows


def _pred(signal_id, dignity=0.6):
    return {'signal_id': signal_id, 'signature_class': 'YOGA', 'primary_domain': 'career', 'dignity_score': dignity,
            'transit_trigger_jsonb': NULL_TARGET}


@pytest.fixture
def contract_on(kala_db_dsn):
    schema = 'sigless_' + uuid4().hex[:10]
    with psycopg.connect(kala_db_dsn) as conn:
        conn.execute(f'CREATE SCHEMA {schema}')
        conn.execute(f'SET LOCAL search_path TO {schema}, public')
        conn.execute('''CREATE TABLE kala_convergence (chart_id text, generation text, horizon_tier text, mode text, peak_date date,
            signal_id uuid, window_start date, window_end date, convergence_score numeric, constituent_factors jsonb, orb_strength numeric,
            independent_current_count int, confidence_score numeric)''')
        sql = registered_contract()

        def verdict(rows):
            conn.execute('DELETE FROM kala_convergence')
            for r in rows:
                conn.execute('''INSERT INTO kala_convergence VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                             (r['chart_id'], r['generation'], r['horizon_tier'], r['mode'], r['peak_date'], r['signal_id'],
                              r['window_start'], r['window_end'], r['convergence_score'], r['constituent_factors'], r['orb_strength'],
                              r['independent_current_count'], r['confidence_score']))
            return conn.execute(sql).fetchone()[0]
        yield verdict
        conn.rollback()


def test_the_round_b2_input_no_longer_fails_its_own_contract(contract_on, monkeypatch):
    """The failed rebuild's input: every predicate signal-less. It now writes nothing, and the contract reads true on that (a blank, not a green:
    the notes of each substep name the blanks)."""
    rows = _rebuild([_pred(None), _pred(None)], monkeypatch)
    assert rows == []
    assert contract_on(rows) is True


def test_distinct_signals_write_one_lifetime_mode_d_set_and_the_contract_reads_true(contract_on, monkeypatch):
    rows = _rebuild([_pred(None), _pred(SIGNAL_A), _pred(SIGNAL_B, dignity=0.9)], monkeypatch)
    lifetime = [r for r in rows if r['horizon_tier'] == 'lifetime']
    assert {r['signal_id'] for r in rows} == {SIGNAL_A}                     # attributed to the first attributable predicate, never NULL
    assert len(lifetime) == len({(r['mode'], r['peak_date']) for r in lifetime}) > 0     # one set, not one set per predicate
    assert contract_on(rows) is True
