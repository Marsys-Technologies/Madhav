"""Packet integration oracles: the independent verifier understands the selected final rules."""
import pytest

from services.gochara_kernel import evaluator, inventory, inventory_verifier as verifier, nd_h_tables as nd
from datetime import datetime, timezone

CHART = {'lagna_deg': 0., 'natal': {
    'Sun': 12., 'Moon': 48., 'Mars': 75., 'Mercury': 103., 'Jupiter': 144.,
    'Venus': 171., 'Saturn': 205., 'Rahu': 240., 'Ketu': 60.}}
VCHART = {'lagna': CHART['lagna_deg'], 'natal': {k.lower(): v for k, v in CHART['natal'].items()}}


@pytest.mark.parametrize('event_class', sorted(nd.EIGHT | {'bereavement', 'marriage'}))
@pytest.mark.parametrize('path', ['P1', 'P3', 'P4'])
def test_final_rule_inventory_is_independently_rederived(event_class, path):
    version = '1.2.0' if event_class in nd.EIGHT or (event_class == 'bereavement' and path != 'P1') else '1.0.0'
    try:
        edges = evaluator.enumerate_edges(event_class, path, CHART, rule_version=version)
    except evaluator.TierIdentityCollision:
        # Until an authority resolves CORE/DVI collisions, neither side may certify one.
        with pytest.raises(verifier.Unverifiable, match='tier'):
            verifier.derive_path_pin(event_class, VCHART, path, version, excluded_agents=('moon',),
                                     path_exclusions={}, h_unknown_exclusion=None)
        return
    if path == 'P1':
        obligations, _ = inventory._plan_p1(event_class, CHART, datetime(2025, 1, 1, tzinfo=timezone.utc),
                                           datetime(2025, 2, 1, tzinfo=timezone.utc),
                                           inventory.SearchCapability(position_probe=True, arc_index=True), [], version)
        expected = sorted({o.canonical_bytes for o in obligations})
    else:
        expected = sorted({inventory.obligation_of_edge(e).canonical_bytes for e in edges})
    derived = verifier.derive_path_pin(event_class, VCHART, path, version, excluded_agents=('moon',),
                                      path_exclusions={}, h_unknown_exclusion=None)
    assert derived['obligations'] == expected


def test_parental_p2_is_suppressed_only_under_the_final_selection():
    final = verifier.derive_path_pin('parental_event', VCHART, 'P2', '1.0.0',
                                    excluded_agents=('moon',), path_exclusions={}, h_unknown_exclusion=None,
                                    selected_versions={'p1': '1.2.0', 'p2': '1.0.0', 'p3': '1.2.0', 'p4': '1.2.0'})
    assert final['disposition'] == 'excluded'
    assert final['obligations'] == []
    legacy = verifier.derive_path_pin('parental_event', VCHART, 'P2', '1.0.0',
                                     excluded_agents=('moon',), path_exclusions={}, h_unknown_exclusion=None)
    assert legacy['obligations']


@pytest.mark.parametrize('level', ['md', 'ad', 'pd'])
def test_karakatva_permission_is_independently_rederived(level):
    chart = {'lagna': 0., 'natal': dict(VCHART['natal'], mercury=70.)}
    result = verifier.period_lord_relation('mercury', 'business_launch', chart, rule_version='1.2.0',
                                          affected_person='native', level=level)
    assert result == ({'relation': 'karakatva', 'licence': 'scored'} if level != 'pd'
                      else {'relation': 'none', 'licence': 'none'})

@pytest.mark.parametrize('path,role,level,want', [
    ('P1', 'period_lord', 'md', ('scored', 'uncited_extension', 'ND-H-20261005')),
    ('P1', 'period_lord', 'pd', ('testimony', 'uncited_extension', 'ST-P1-PD-TESTIMONY-20261002')),
    ('P3', 'karaka', None, ('scored', 'uncited_extension', 'ND-H-20261005')),
    ('P4', 'signature_house', None, ('scored', 'uncited_extension', 'ND-H-20261005')),
    ('P3', 'maraka_of_house', None, ('testimony', 'uncited_extension', 'D-PADMIT')),
])
def test_final_record_stamps_have_independent_literal_expectations(path, role, level, want):
    assert nd.record_stamp('parental_event', path, '1.2.0', role, level) == want
    assert nd.record_stamp('parental_event', path, '1.0.0', role, level) is None


def test_bereavement_luminary_keeps_its_own_source_and_legacy_house_stamp():
    assert nd.record_stamp('bereavement', 'P3', '1.2.0', 'karaka') == (
        'scored', 'uncited_extension', 'ND-P2-20261005')
    assert nd.record_stamp('bereavement', 'P3', '1.2.0', 'lord') is None


@pytest.mark.parametrize('event_class', ['marriage', 'bereavement', 'business_launch', 'parental_event'])
def test_whole_bound_catalogue_has_independent_dispositions(event_class):
    from services.gochara_kernel import rule_registry as rr
    lo, hi = datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc)
    selection = rr.selected_versions_for(event_class)
    exclusions, h_unknown = inventory.standing_exclusions()
    built = inventory.plan_class_inventory(event_class=event_class, chart=CHART, horizon=(lo, hi),
        sealed_paths=rr.bound_path_refs(), selected_versions=selection,
        capability=inventory.SearchCapability(position_probe=True, arc_index=True),
        path_exclusions=exclusions, h_unknown_exclusion=h_unknown, dasha_rows=[])
    v_exclusions = {'p5': {'reason': 'tier_withheld_by_ruling', 'basis': 'ruling:ST-P5-HOLD-20261001',
                          'ruling_ref': 'ST-P5-HOLD-20261001'}}
    v_unknown = {'reason': 'inputs_unavailable', 'basis': 'ruling:ST-H-UNKNOWN-20261002',
                 'ruling_ref': 'ST-H-UNKNOWN-20261002'}
    checked = verifier.derive_class_pins(event_class, VCHART, rr.bound_path_refs(),
        selected_versions=selection, excluded_agents=('moon',),
        path_exclusions=v_exclusions, h_unknown_exclusion=v_unknown)
    expected = {(p.path_id.lower(), p.rule_version):
        (p.disposition, p.exclusion_reason or '', p.basis or '', sorted(o.canonical_bytes for o in p.obligations))
        for p in built.pins}
    assert {(p['path'], p['version']): (p['disposition'], p['reason'], p['basis'], p['obligations'])
            for p in checked} == expected
