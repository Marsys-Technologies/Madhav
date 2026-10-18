"""Preparation handoffs must preserve the real model's scope and branch semantics."""
import copy
import datetime as dt
import json
from pathlib import Path
import re
import shlex

import pytest

from pravaha_tracker.state import build_snapshot


ROOT = Path(__file__).resolve().parents[4]
BRIEFS = ROOT / '00_ARCHITECTURE/briefs/kalayantra'
MODEL = ROOT / '00_ARCHITECTURE/control/kalayantra/plan_model.json'


def test_unit_oracle_handoff_keeps_sibling_parent_and_checklist_gates_open():
    handoff = json.loads((BRIEFS / 'NB_W4_TOOLING_HANDOFF_v1_0.json').read_text())
    assert handoff['item'] == 'J1A-STEP-02'
    assert handoff['parent_item'] == 'J-1a'
    assert handoff['status'] == 'preparation_only'
    assert handoff['scope_built'] == [
        'eight unit-oracle gaps and their mandatory CI binding (PR #3586)'
    ]
    gates = {gate['id']: gate for gate in handoff['activation_gates']}
    assert {'J1A-STEP-01', 'J0M-Q055', 'J-1a', 'exact_head_ci',
            'deployed_source', 'operational_acceptance'} <= gates.keys()
    assert all(gate['status'] == 'required_before_closure' for gate in gates.values())
    assert {'sibling launch/dry-run qualification', 'parent J-1a completion',
            'operational/phase closure'} <= set(handoff['left_out'])


def test_inherited_checklist_obligation_is_preserved_before_phase_closure():
    handoff = json.loads((BRIEFS / 'NB_W4_TOOLING_HANDOFF_v1_0.json').read_text())
    gates = {gate['id']: gate for gate in handoff['activation_gates']}
    model = json.loads(MODEL.read_text())
    # Follow the committed obligation, rather than blessing an invented completion.
    # The model nests its evidence-contract questions; find the actual record.
    def records(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from records(child)
        elif isinstance(value, list):
            for child in value:
                yield from records(child)
    obligation = next(row for row in records(model) if row.get('id') == 'J0M-Q055')
    assert 'small-test prerequisite checklist' in obligation['detail']
    assert gates['J0M-Q055']['finding'] == 'STEP-3140-03'
    assert gates['J0M-Q055']['model_obligation'] == obligation['detail']
    assert gates['J0M-Q055']['status'] == 'required_before_closure'


@pytest.mark.parametrize('finding,limit', [
    ('J1A-UO-N2', '900-second timeout'),
    ('W4-SAFETY-CHILDREN-N02', 'interrupted'),
])
def test_incomplete_db_history_requires_complete_exact_head_ci(finding, limit):
    handoff = json.loads((BRIEFS / 'NB_W4_TOOLING_HANDOFF_v1_0.json').read_text())
    assert limit in handoff['validation_limits'][finding]
    assert handoff['validation_limits']['connectivity_deferral'] is False
    gate = next(gate for gate in handoff['activation_gates'] if gate['id'] == 'exact_head_ci')
    assert gate['status'] == 'required_before_closure'
    assert 'exact reviewed/admitted head before integration or operational reliance' in gate['evidence']
    assert 'complete C38 base/populated/W4, round-2 and round-3 suites and real launch checks' in gate['evidence']


@pytest.mark.parametrize('scenario', ['clean', 'not_clean', 'unknown', 'incomplete'])
def test_activation_recipe_drives_the_landed_run2_model(scenario):
    text = (BRIEFS / 'W4_RUN2_ACTIVATION_RECIPES_v1_0.md').read_text()
    details = {
        'clean': {'$ALL_FOUR_CLEAN_CLAUSES_EVIDENCE'},
        'not_clean': {'$COMPLETED_RUN1_FAILED_CLAUSE_EVIDENCE', '$RUN1_NOT_CLEAN_EVIDENCE'},
        'unknown': {'$MISSING_OR_INCONCLUSIVE_RUN1_EVIDENCE'},
        'incomplete': {'$INCOMPLETE_RUN1_EVIDENCE_AND_RECHECK'},
    }
    commands = [shlex.split(line) for line in re.findall(r'^KY_STREAM=N ky decide D-RUN2 .+$', text, re.M)]
    matches = [argv for argv in commands if argv[-1] in details[scenario]]
    assert len(matches) == 1, f'missing or ambiguous {scenario} decision recipe'
    argv = matches[0]
    assert argv[:5] == ['KY_STREAM=N', 'ky', 'decide', 'D-RUN2', '--as']
    assert argv[5:8] == ['steward', '--delegated', '--outcome']
    outcome = argv[8]
    assert argv[9] == '--detail' and len(argv) == 11
    expected = {'clean': 'approved', 'not_clean': 'refused',
                'unknown': 'insufficient_evidence', 'incomplete': 'deferred'}
    assert outcome == expected[scenario]

    model = json.loads(MODEL.read_text())
    ids = {'J-2b', 'D-RUN2', 'J-2c', 'J-2d', 'J-2d-a55i', 'J-RUN2-RESOLVED'}
    model = copy.deepcopy(model)
    model['items'] = [row for row in model['items'] if row['id'] in ids]
    # External prerequisites are granted in this local semantic fixture only.
    # Keep every conditional edge and the composite child in the real subgraph.
    for row in model['items']:
        row['depends_on'] = [dep for dep in row.get('depends_on', []) if dep in ids]
    now = dt.datetime(2026, 10, 16, tzinfo=dt.timezone.utc)
    events = [dict(kind='item', actor='stream-S', item='J-2b', state='done',
                   guarded=True, ts=now.isoformat(), evidence='synthetic accepted run 1'),
              dict(kind='decision', actor='steward', decision='D-RUN2', state='delegated',
                   outcome=outcome, ts=now.isoformat(), detail='synthetic digest-bound evidence')]
    measured = {row['id']: dict(status='pending', detail='synthetic missing receipt',
                               checked_at=now.isoformat())
                for row in model['items'] if row.get('detector')}
    snapshot = build_snapshot(model, events, measured, {}, {}, now=now)
    rows = {row['id']: row for track in snapshot['tracks'] for row in track['items']}
    if scenario == 'clean':
        for item in ('J-2c', 'J-2d', 'J-2d-a55i'):
            assert rows[item]['status'] == 'not_applicable'
            assert 'D-RUN2' in rows[item]['skip_origin']
        assert rows['J-RUN2-RESOLVED']['status'] == 'done'
    elif scenario == 'not_clean':
        assert rows['J-2c']['status'] == 'ready'
        assert rows['J-2d']['status'] == 'waiting'
        assert rows['J-RUN2-RESOLVED']['status'] == 'waiting'
    else:
        assert rows['J-2c']['status'] == 'waiting'
        assert rows['J-2d']['status'] == 'waiting'
        assert rows['J-RUN2-RESOLVED']['status'] == 'waiting'
