"""An empty included-grain set needs its own inventory attestation, not invented windows."""
import json

import pytest

from services.gochara_kernel import seal_brief as sb
from tests.test_gochara_seal_approval_scripts import payload, pair, check, CHART, GEN, bc

DIGEST = 'c' * 64
TABLE = 'ka_gochara_search_inventory_verification'


def empty_class_payload():
    p = payload(classes=[{'event_class': 'spiritual_turn', 'inventory_digest': DIGEST, 'grains': []}],
                attestations={TABLE: [json.dumps({'chart_id': CHART, 'generation': GEN,
                    'event_class': 'spiritual_turn', 'rederived_inventory_digest': DIGEST})]},
                legacy_projection={'policy': 'none'},
                code={'sealing_commit': 'a' * 40, 'manifest_pinned_implementation_digest': 'b' * 64})
    return p


def test_server_accepts_an_inventory_attested_class_with_no_included_window_grains():
    assert sb._current_and_complete(empty_class_payload()) == []


def test_workflow_accepts_the_same_attested_empty_class():
    p = empty_class_payload()
    raw, compact = pair(p)
    assert check(raw, compact) == compact['sha256']


@pytest.mark.parametrize('field,value', [('chart_id', 'other'), ('generation', '4.1'),
    ('event_class', 'marriage'), ('rederived_inventory_digest', 'd' * 64)])
def test_foreign_or_stale_inventory_is_not_evidence_for_an_empty_class(field, value):
    p = empty_class_payload()
    row = json.loads(p['attestations'][TABLE][0])
    row[field] = value
    p['attestations'][TABLE] = [json.dumps(row)]
    assert sb._current_and_complete(p)
    with pytest.raises(bc.Refused, match='no persisted verification'):
        check(*pair(p))


@pytest.mark.parametrize('rows', [[], ['not json'], ['null'], ['[]']])
def test_missing_or_malformed_inventory_never_admits_an_empty_class(rows):
    p = empty_class_payload()
    p['attestations'][TABLE] = rows
    assert sb._current_and_complete(p)
    with pytest.raises(bc.Refused, match='no persisted verification'):
        check(*pair(p))


def test_a_missing_included_grain_is_still_refused_with_a_matching_inventory():
    p = empty_class_payload()
    p['candidate_gate']['violations'] = ['spiritual_turn/P2@1.0.0:window_verification_missing']
    assert sb._current_and_complete(p)
    with pytest.raises(bc.Refused, match='not clean'):
        check(*pair(p))
