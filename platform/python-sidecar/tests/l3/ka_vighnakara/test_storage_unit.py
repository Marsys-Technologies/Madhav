"""Candidate validation before replacement, without a database server."""
from types import SimpleNamespace

import pytest

from services.ka_vighnakara import storage
from tests.l3.ka_vighnakara.test_negative_space import finding, protection


class CandidateCursor:
    def __enter__(self):
        return self

    def __exit__(self,*args):
        pass

    def execute(self,sql,params):
        if 'FROM pg_attribute' in sql:
            self.result = (False,)
        else:
            self.result = ((str(finding().chart_id),'candidate:fixture','building',{'fixture':True})
                           if 'kala_layer_candidate' in sql else None)
        return self

    def fetchone(self):
        return self.result


@pytest.mark.parametrize('changes', [ {'assertion_id':'alias'},
    {'assertion_id':'alias','roots':{'record_ids':['fixture:judge'],
        'contact_ids':[], 'fact_ids':['fixture:additional-evidence']}},
    {'assertion_id':'alias','source':{'text':'another citation','locator':'alias locator'}}])
def test_physical_alias_rejected_before_replacement(monkeypatch,changes):
    replacements = []
    monkeypatch.setattr(storage,'replace_candidate_partition',lambda *args: replacements.append(args))
    cursor = CandidateCursor()
    ctx = SimpleNamespace(dry_run=False,config={'chart_id':str(finding().chart_id)},
        build_id='fixture:build',db_conn=SimpleNamespace(cursor=lambda **kwargs:cursor))
    protected = finding(protections=[protection()])
    alias = finding(**changes,protections=[protection()])
    with pytest.raises(ValueError,match='duplicate physical'):
        storage.write_fixture_candidate(ctx,[protected,alias])
    assert replacements == []


def captured_states(monkeypatch, values):
    """Exercise real row preparation, replacing only its final SQL boundary."""
    rows = []
    def replace(cursor, table, chart, generation, grain, prepared):
        rows.extend(prepared)
        return len(prepared)
    monkeypatch.setattr(storage, 'replace_candidate_partition', replace)
    ctx = SimpleNamespace(dry_run=False, config={'chart_id':str(finding().chart_id)},
        build_id='fixture:build', db_conn=SimpleNamespace(cursor=lambda **kwargs:CandidateCursor()))
    storage.write_fixture_candidate(ctx, values)
    return [row['effective_state'] for row in rows]


def test_overlapping_physical_alias_cannot_reactivate_cancelled_finding(monkeypatch):
    protected = finding(protections=[protection()])
    alias = finding(assertion_id='alias:segment', protections=[protection()],
        interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-01-15T00:00:00Z'},
        release={'kind':'instant','instant':'2026-01-15T00:00:00Z'})
    try:
        states = captured_states(monkeypatch, [protected, alias])
    except ValueError:
        return  # Conservative rejection until physical target resolution is admitted.
    assert 'obstruction_in_force' not in states, states


def test_label_only_rebuild_cannot_reactivate_same_physical_finding(monkeypatch):
    before = captured_states(monkeypatch, [finding(protections=[protection()])])
    alias = finding(assertion_id='alias:replacement', protections=[protection()])
    try:
        after = captured_states(monkeypatch, [alias])
    except ValueError:
        return
    assert before == after, (before, after)


@pytest.mark.parametrize('order', [False, True])
def test_overlapping_root_alias_with_retargeted_edge_is_rejected(monkeypatch, order):
    protected = finding(protections=[protection()])
    alias = finding(assertion_id='alias:segment',
        protections=[protection(target_assertion_id='alias:segment')],
        interval={'t0':'2026-01-10T00:00:00Z','t1':'2026-01-15T00:00:00Z'},
        release={'kind':'instant','instant':'2026-01-15T00:00:00Z'})
    values = [alias, protected] if order else [protected, alias]
    with pytest.raises(ValueError, match='duplicate physical'):
        captured_states(monkeypatch, values)


def test_adjacent_same_root_segments_remain_distinct(monkeypatch):
    first = finding(interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-01-15T00:00:00Z'},
        release={'kind':'instant','instant':'2026-01-15T00:00:00Z'})
    second = finding(assertion_id='fixture:next',
        interval={'t0':'2026-01-15T00:00:00Z','t1':'2026-02-01T00:00:00Z'})
    assert captured_states(monkeypatch, [first, second]) == ['obstruction_in_force'] * 2
