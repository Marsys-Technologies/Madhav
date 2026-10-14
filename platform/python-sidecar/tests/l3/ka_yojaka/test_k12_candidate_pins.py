"""Exercise the real writer on a SQL-aware fixture without opening a DB."""
from types import SimpleNamespace
from copy import deepcopy
import json
import pytest
from pipeline.orchestrator.writers import SubStep
from pipeline.orchestrator.writers.ka_yojaka import KaYojakaWriter

PIN = dict(build_id='A', ayanamsha_id='a', tier='two_pass_verified')


class Conn:
    def __init__(self, candidate=True):
        self.candidate = [dict(generation='candidate:G', state='building', build_id='owner',
            conventions={'natal': deepcopy(PIN), 'yoga': deepcopy(PIN), 'msr': deepcopy(PIN)})] if candidate else []
        self.writes, self.facts, self.firings, self.signals = [], [], [], []
    def cursor(self, **kwargs): return self
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def execute(self, sql, params=()):
        if not sql.lstrip().startswith('SELECT'): self.writes.append((sql, params)); self.rows=[]; return self
        if 'FROM kala_layer_head' in sql: self.rows=[]
        elif 'FROM kala_layer_candidate_grain' in sql: self.rows=[]
        elif 'FROM kala_layer_candidate' in sql: self.rows=self.candidate
        elif 'FROM chart_facts' in sql: self.rows=self.select(sql, params, self.facts)
        elif 'FROM ga_yoga_firings' in sql: self.rows=self.select(sql, params, self.firings)
        elif 'FROM bodha_msr_signals' in sql: self.rows=self.select(sql, params, self.signals)
        else: self.rows=[]
        return self
    def select(self, sql, params, rows):
        selected = rows
        if 'build_id = %s' in sql: selected=[r for r in selected if r['build_id'] == params[1]]
        if 'ayanamsha_id = %s' in sql:
            idx = 2 if 'build_id = %s' in sql else 1
            selected=[r for r in selected if r['ayanamsha_id'] == params[idx]]
        if 'verification_pass_status = %s' in sql: selected=[r for r in selected if r['verification_pass_status'] == params[3]]
        return deepcopy(selected)
    def fetchall(self): return self.rows
    def fetchone(self): return self.rows[0] if self.rows else None
    def executemany(self, sql, params): self.writes.append((sql, list(params)))


def run(conn):
    ctx=SimpleNamespace(dry_run=False, db_conn=conn, build_id='owner', config={'chart_id': 'chart', 'candidate_generation': 'candidate:G'})
    return KaYojakaWriter().run_substep(ctx, SubStep('class:unqualified'))


def test_unregistered_candidate_refused():
    conn=Conn(False)
    with pytest.raises(ValueError, match='registered'): run(conn)
    assert not conn.writes


def test_foreign_build_candidate_refused():
    conn=Conn(); conn.candidate[0]['build_id']='foreign'
    with pytest.raises(ValueError, match='build'): run(conn)
    assert not conn.writes


def test_writer_preserves_unassessed_reason_in_the_consumer_state():
    """Exercise real adapter/evaluator/serialization; only the SQL transport is fake."""
    from tests.l3.ka_yojaka.test_source_adapter import sources
    facts, firings = sources()
    facts.append(dict(facts[0], fact_id='f:saturn', fact_subject='Saturn'))
    firings[0]['constituent_fact_ids'] = ['f:moon', 'f:saturn']
    firings[1]['bhanga_rules_jsonb'] = [dict(rule_id='NB-1', kind='defeats',
        target_yoga_canonical_id='sunapha', target_event_class_id='major_gain',
        rule_version='fixture-v1', source_locator='fixture:source:1')]
    firings[1]['grounds_jsonb'] = {'cancellation_evidence': [
        {'rule_id': 'NB-1', 'fact_ids': ['f:moon']}]}
    conn = Conn()
    conn.facts = [dict(r, build_id='A') for r in facts]
    conn.firings = [dict(r, build_id='A') for r in firings]
    ctx = SimpleNamespace(dry_run=False, db_conn=conn, build_id='owner',
        config={'chart_id': 'chart', 'candidate_generation': 'candidate:G'})
    result = KaYojakaWriter().run_substep(ctx, SubStep('class:major_gain'))
    assert result.rows_inserted == 1
    inserted = next(params for sql, params in conn.writes
                    if 'INSERT INTO kala_activation_predicates' in sql)[0]
    ledger = json.loads(inserted[7])
    state = json.loads(inserted[10])
    assert state['effective_state'] == 'unresolved' and state['scored'] is False
    assert state['null_reason'] == 'partial_defeat_unassessed'
    assert state['effective_reason'] == ledger['effective_reason']
    assert state['effective_reason']['conclusion_ids'] == ['a:sunapha:major_gain:conclusion']
    assert state['effective_reason']['defeat_ids'] == [state['defeats'][0]['defeat_id']]
