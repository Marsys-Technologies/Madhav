"""Owner ruling 15: L1 relations survive independently of yoga/L2 selection."""
import pytest

from services.ka_yojaka.promise_adapter import build_bundle
from services.kala_core.promise import AttachmentInput, AttachmentSource, load_l2_attachments
from tests.l3.ka_yojaka.test_source_adapter import sources


def fact(fid, category, subject, key, *, num=None, text=None, value=None, citation=None):
    return dict(fact_id=fid, ayanamsha_id='a', fact_category=category, fact_subject=subject,
                fact_key=key, fact_value_num=num, fact_value_text=text, fact_value_jsonb=value,
                citation_ref=citation, verification_pass_status='two_pass_verified')


def structural_facts():
    return [
        fact('lord', 'lord_in_house_per_varga', 'D1_H7', 'lord_placement',
             value={'lord': 'Venus', 'varga': 'D1', 'house': 7, 'lord_house_in_varga': 10}),
        fact('occupation', 'graha_position', 'VEN', 'house_d1', num=10),
        fact('aspect', 'aspect_parashari_given', 'JUP', 'house_7', num=1),
        fact('dispositor', 'graha_position', 'VEN', 'sign_lord', text='Saturn'),
        fact('karaka', 'karakatva_strength_per_significance', 'marriage', 'natural_karaka', text='Venus'),
        fact('argala', 'argala_graha_natal', 'D1_VEN', 'from_MAR_offset_2',
             value={'target_graha': 'Venus', 'source_graha': 'Mars', 'varga': 'D1',
                    'argala_grahas': ['Mars'], 'obstructor_grahas': ['Saturn'],
                    'obstruction_present': True, 'outcome_by_count': 'undetermined'}),
    ]


def test_non_yoga_structural_graph_survives_without_l2():
    rows = build_bundle(structural_facts(), [], [])
    edges = [edge for row in rows for edge in row['graph_edges']]
    assert {e['relation'] for e in edges} >= {'lordship', 'occupation', 'classical_aspect', 'dispositor', 'karaka', 'argala', 'virodha'}
    assert {fid for r in rows for fid in r['fact_ids']} == {'lord', 'occupation', 'aspect', 'dispositor', 'karaka', 'argala'}
    assert all(r['event_class_id'] is None and r['scored'] is False for r in rows)
    assert all(n['fact_ids'] for r in rows for n in r['graph_nodes'])


def test_argala_virodha_have_no_invented_rule_or_weight():
    rows = build_bundle([structural_facts()[-1]], [], [])
    assert rows
    for row in rows:
        assert row['route'] == row['operator_role'] == 'testimony'
        assert row['rule_version'] == 'unadmitted'
        assert row['scored'] is False and row['weight'] == 0
        for edge in row['graph_edges']:
            assert edge['provenance'] == 'uncited_extension'
            assert edge['method_qualification'] == 'd_local'
            assert edge['rule_id'] is None and edge['rule_version'] == 'unadmitted'


@pytest.mark.parametrize('citation,expected', [
    ('aspect.JUP.house_7@chart=fixture:eng=1', 'uncited_extension'),
    ('BPHS Ch. 26', 'uncited_extension'),
    ('bphs:PG286:C1', 'verse_cited'),
    (None, 'uncited_extension'),
])
def test_structural_provenance_requires_a_served_locator(citation, expected):
    row = fact('aspect', 'aspect_parashari_given', 'JUP', 'house_7', num=1, citation=citation)
    bundle = build_bundle([row], [], [], served_locators={'bphs:PG286:C1'})
    assert bundle and bundle[0]['graph_edges'][0]['provenance'] == expected


def test_fact_verified_structure_sorts_ahead_of_yoga_without_borrowing_its_tier():
    facts, firings = sources()
    bundle = build_bundle(facts + structural_facts()[:1], firings, [])
    assert bundle[0]['canonical_id'] is None
    yogas = [r for r in bundle if r['canonical_id']]
    assert all(r['yoga_tier'] is None and 'yoga_tier_unavailable' in r['judgment_flags'] for r in yogas)


def test_empty_fact_roots_are_missing_rather_than_vacuously_present():
    attachment = load_l2_attachments('mechanism', [AttachmentInput('cgm', AttachmentSource.CGM, ())], [])[0]
    assert attachment.state.value == 'missing_fact'
    assert attachment.null_reason == 'no_fact_root_identity_in_l2_source'


def test_jaimini_aspect_uses_the_stored_sign_relation_without_computation():
    rows = build_bundle([fact('jaimini', 'aspect_jaimini', 'Aries', 'on_Leo', num=1)], [], [])
    assert rows
    edge = rows[0]['graph_edges'][0]
    assert edge['relation'] == 'classical_aspect' and edge['frame'] == 'zodiac'
    assert edge['source_id'] == 'a:sign:Aries' and edge['target_id'] == 'a:sign:Leo'


def test_an_earned_yoga_tier_is_consumed_additively_without_borrowing_fact_tiers():
    facts, firings = sources()
    firings[0]['verification_pass_status'] = 'two_pass_verified'
    rows = build_bundle(facts, firings, [])
    row = next(r for r in rows if r['canonical_id'] == 'sunapha')
    assert row['yoga_tier'] == 'two_pass_verified'
    assert row['null_reason'] is None and row['judgment_flags'] == []


def test_unrelated_msr_roots_are_consulted_without_becoming_mechanism_attachments():
    facts, firings = sources()
    facts.append(fact('f:mars', 'graha_position', 'MAR', 'longitude_sidereal', num=10))
    signals = [dict(signal_id='unrelated', ayanamsha_id='a', constituent_facts_array=['f:mars'])]
    row = next(r for r in build_bundle(facts, firings, signals) if r['canonical_id'] == 'sunapha')
    assert row['source_states']['msr'] == 'present'
    assert row['l2_attachments'] == []


def test_rootless_sources_have_audit_rows_instead_of_invented_mechanism_bindings():
    facts, firings = sources()
    rows = build_bundle(facts, firings, [],
        cgm=[dict(edge_id='edge', ayanamsha_id='a')],
        pratijna=[dict(pratijna_id='promise', ayanamsha_id='a', event_class_id='major_gain')])
    yoga = next(r for r in rows if r['canonical_id'] == 'sunapha')
    assert yoga['source_states']['cgm'] == 'missing_fact'
    assert yoga['l2_attachments'] == []
    audit = [r for r in rows if r['qualification'] == 'no_fact_root_identity_in_l2_source']
    assert {a['attachment_id'] for r in audit for a in r['l2_attachments']} == {'edge', 'promise'}
    assert all(r['route'] == 'testimony' and r['scored'] is False for r in audit)
