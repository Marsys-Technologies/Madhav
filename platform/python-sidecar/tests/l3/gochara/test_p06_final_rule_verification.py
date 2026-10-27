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
                          'ruling_ref': 'ST-P5-HOLD-20261001'},
                    # FOURQ-CLOSURE-20261027: P4 is switched off -- the verifier is told so independently
                    'p4': {'reason': 'tier_withheld_by_ruling', 'basis': 'ruling:FOURQ-CLOSURE-20261027',
                          'ruling_ref': 'FOURQ-CLOSURE-20261027'}}
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


# Ruling 18 §1, FB-34/35: same identity, CORE licence subsumes DVI.
def test_core_absorbs_dvi_and_independent_context_records_the_exact_keys():
    es = evaluator.enumerate_edges('achievement_recognition', 'P4', CHART, rule_version='1.2.0')
    target = evaluator._point_target(CHART['natal']['Saturn'])
    keys = sorted(f'{a}|{r}|{target}|lord' for a in ('jupiter', 'saturn') for r in ('conjunction', 'aspect'))
    ctx = evaluator.final_rule_context('achievement_recognition', 'P4', CHART, '1.2.0')
    assert ctx['dvi_absorbed_by_core'] == keys
    assert ctx['ruling_ref'] == 'SURROGATE_ANSWER_18'
    assert ctx['support']['state'] == 'annotation_unstored'
    assert ctx == verifier.derive_final_rule_context('achievement_recognition', 'P4', VCHART, '1.2.0')
    assert all(e.tier == 'core' for e in es if e.object_role == 'lord' and e.obj.canonical_target == target)
    assert len(es) == len({(e.agent, e.relation, e.obj.canonical_target, e.object_role) for e in es})


def test_fb36_authored_default_satisfies_the_persisted_factor_discipline():
    from services.gochara_kernel import rule_registry as rr
    row = next(r for r in rr.factor_rows() if r['factor_id'] == 'karaka_agent')
    assert row['calibration_status'] == 'uncalibrated_default'
    assert row['category_mapping'] == {'karaka': 1.0, 'non_karaka': 0.0}
    assert row['doctrine_ordering'] == ['non_karaka', 'karaka']
    assert (row['range_lower'], row['range_upper'], row['null_state']) == (0.0, 1.0, 'omit')


def test_a1_a2_a3_are_resolved_for_scope_and_bereavement_remains_unmapped():
    from services.gochara_rules import registry as reg
    assert {'A1', 'A2', 'A3'} <= reg.RESOLVED_POINTS.keys()
    assert not nd.OPEN_POINTS
    assert {'A1', 'A2', 'A3', 'A4'} <= nd.RESOLVED_POINTS.keys()
    assert nd.KARAKATVA[('psychological_arc', 'native')] == {'moon'}
    assert not any(c == 'bereavement' for c, _ in nd.KARAKATVA)


def test_fb38_fb70_builder_fixture_verifier_three_way_equality():
    import hashlib, json
    from pathlib import Path
    from services.gochara_rules import registry as reg
    fixture = Path(__file__).resolve().parent / 'fixtures/fb35_table_v1_2.json'
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == 'acfa58c79c85515b6728d1f32347032be3a9542f206177217474b4cc5cffeb2e'
    rows = json.loads(fixture.read_text())['classes']
    for cls, row in rows.items():
        b = reg.nd_h_row(cls, '1.2.0'); v = nd.TIERS[cls]
        assert {k: sorted(getattr(v, k)) for k in ('core', 'dvi', 'support', 'noted')} == {k: row[k] for k in ('core', 'dvi', 'support', 'noted')}
        # Builder parental houses are offsets from the 9th; fixture and verifier are lagna-counted.
        for tier in ('core', 'dvi', 'support'):
            got = b[tier]
            if b['anchor_house'] is not None:
                got = {nd.frame_house(b['anchor_house'], h) for h in got}
            assert sorted(got) == row[tier]
        assert sorted(nd.KARAKA_A[cls]) == row['karaka_a']
        assert sorted(k['karaka'].lower() for k in b['karakas'] if 'K-A' in k['roles']) == row['karaka_a']
        assert sorted(k['karaka'].lower() for k in b['karakas'] if 'K-B' in k['roles']) == row['karaka_b']




def test_near_miss_seal_status_is_computed_from_the_absent_version_pin():
    from services.gochara_kernel import seal_brief as sb
    assert sb.near_miss_layer_status({}) == 'stored_uncovered'
    assert sb.near_miss_layer_status({'near_miss_layer_version': '1'}) != 'stored_uncovered'


@pytest.mark.parametrize('output', ['supports', 'p4_influence', 'candidate_counts', 'coverage_accounting'])
def test_fb29_negative_control_injects_a_near_miss_into_a_forbidden_output(output):
    import copy
    from services.gochara_kernel import near_miss_verifier as nm
    off = {k: [] for k in nm.NONINTERFERENCE_KEYS}
    off.update(candidate_counts=1, coverage_accounting={'searched': 1})
    assert nm.noninterference_problems(copy.deepcopy(off), off) == []
    on = copy.deepcopy(off)
    near_miss = {'standing': 'near_miss', 'score': None, 't_in': '2025-01-01', 't_out': '2025-01-03'}
    if output == 'candidate_counts':
        on[output] += len([near_miss])
    elif output == 'coverage_accounting':
        on[output]['searched'] += len([near_miss])
    else:
        on[output].append(near_miss)
    assert f'noninterference_violated: {output}' in nm.noninterference_problems(on, off)


@pytest.mark.parametrize('mutation,refusal', [
    ('category', 'karaka_agent_mismatch'),
    ('reverse_tier', 'dvi_core_subsumption_refused'),
    ('absorption', 'dvi_absorption_context_mismatch'),
    ('kb_extra', 'kb_edge_unlicensed'),
    ('kb_missing', 'kb_edge_missing'),
])
def test_fb38b_per_record_detector_refuses_each_independent_mismatch(mutation, refusal):
    import copy
    from services.gochara_kernel import record_derivation as rd
    cls, path, version = 'parental_event', 'P4', '1.2.0'
    es = evaluator.enumerate_edges(cls, path, CHART, rule_version=version)
    records = [dict(id=str(i), agent=e.agent, relation=e.relation, role=e.object_role,
                    target=e.obj.canonical_target, contact=str(i), person=e.affected_person,
                    class_context=verifier.derive_final_rule_context(cls, path, VCHART, version),
                    final_rules={'tier': e.tier, 'karaka_agent': nd.karaka_agent_value(cls, e.agent)})
               for i, e in enumerate(es)]
    contacts = [dict(id=r['contact'], body=r['agent'], relation=r['relation'], target=r['target']) for r in records]
    contexts = [verifier.derive_final_rule_context(cls, path, VCHART, version)]
    assert rd.final_rule_record_problems(cls, path, VCHART, records, contacts, contexts) == []
    records, contexts = copy.deepcopy(records), copy.deepcopy(contexts)
    if mutation == 'category':
        records[0]['final_rules']['karaka_agent'] = 'karaka' # Jupiter/Saturn are non-karaka for father.
    elif mutation == 'reverse_tier':
        records[0]['final_rules']['tier'] = 'dvi'
    elif mutation == 'absorption':
        contexts[0]['dvi_absorbed_by_core'] = ['invented|key']
    elif mutation == 'kb_extra':
        next(r for r in records if r['role'] == 'karaka')['agent'] = 'mars'
    elif mutation == 'kb_missing':
        records.pop(next(i for i, r in enumerate(records) if r['role'] == 'karaka'))
    assert any(refusal in p for p in rd.final_rule_record_problems(cls, path, VCHART, records, contacts, contexts))


def test_fb38b_karaka_values_are_checked_on_every_agent_including_the_class_karaka():
    from services.gochara_kernel import record_derivation as rd
    cls, path = 'business_launch', 'P3'
    es = evaluator.enumerate_edges(cls, path, CHART, rule_version='1.2.0')
    records = [dict(id=str(i), agent=e.agent, relation=e.relation, role=e.object_role,
                    target=e.obj.canonical_target, contact=str(i) if e.transit else None, person=e.affected_person,
                    class_context=verifier.derive_final_rule_context(cls, path, VCHART, '1.2.0'),
                    final_rules={'tier': e.tier, 'karaka_agent': nd.karaka_agent_value(cls, e.agent) if e.transit else None})
               for i, e in enumerate(es)]
    contacts = [dict(id=r['contact'], body=r['agent'], relation=r['relation'], target=r['target']) for r in records if r['contact']]
    contexts = [verifier.derive_final_rule_context(cls, path, VCHART, '1.2.0')]
    assert not rd.final_rule_record_problems(cls, path, VCHART, records, contacts, contexts)
    for r in records:
        if r['agent'] == 'mercury' and r['contact']:
            r['final_rules']['karaka_agent'] = 'non_karaka'
    problems = rd.final_rule_record_problems(cls, path, VCHART, records, contacts, contexts)
    assert problems and all('karaka_agent_mismatch' in p and 'record ' in p for p in problems)



def test_fb41_guard_reports_adverse_protocol_budget_beside_the_outcome_independent_band():
    from datetime import date
    from services.gochara_eval.density import AdmittedSpan, admitted_day_share_report
    h = (date(2000, 1, 1), date(2000, 4, 9)) # 100 days
    spans = [AdmittedSpan('financial_deception', 'P4', h[0], date(2000, 2, 10))]
    report = admitted_day_share_report(spans, h, dvi_members={'financial_deception': [6]},
                                      protocol_adverse_budgets={'financial_deception': 0.0261})
    guard = report['classes']['financial_deception']['dvi_guard']
    assert guard['exceeds_band'] and guard['band_upper'] == 0.4
    assert guard['protocol_adverse_budget_share'] == 0.0261
    assert guard['protocol_adverse_budget_basis'] == 'EVALUATION_PROTOCOL_v2_3 §6.4 T-FP (separate from FB-41)'
    assert guard['revert_dvi_to_support_next_generation'] == [6]


def test_fb50_absorbed_keys_disclose_that_the_dvi_lord_adds_no_edges():
    from datetime import date
    from services.gochara_eval.density import admitted_day_share_report
    ctx = evaluator.final_rule_context('achievement_recognition', 'P4', CHART, '1.2.0')
    report = admitted_day_share_report([], (date(2000, 1, 1), date(2000, 1, 31)),
         dvi_members={'achievement_recognition': [11]},
         class_contexts={'achievement_recognition': ctx})
    row = report['classes']['achievement_recognition']
    assert row['dvi_absorbed_by_core'] == ctx['dvi_absorbed_by_core']
    assert 'absorbed DVI lord identities add no P4 edges' in row['dvi_absorption_note']
    assert 'DVI house edges remain distinct' in row['dvi_absorption_note']


def test_the_inventory_plans_no_p4_interval_once_p4_is_switched_off_by_ruling():
    """FOURQ-CLOSURE-20261027: P4 is a standing exclusion (`tier_withheld_by_ruling`), so the planner
    pins it `excluded` with the ruling BEFORE enumerating -- no P4 obligation, interval or absorption
    context is planned (the test that stood here asserted the P4 intervals' absorption context; that
    context is now never produced because the path is off)."""
    from services.gochara_kernel import rule_registry as rr
    from datetime import datetime, timezone
    exclusions, unknown = inventory.standing_exclusions()
    assert exclusions['P4'].ruling_ref == 'FOURQ-CLOSURE-20261027'
    plan = inventory.plan_class_inventory(event_class='achievement_recognition', chart=CHART,
        horizon=(datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc)),
        sealed_paths=rr.bound_path_refs(), selected_versions=rr.selected_versions_for('achievement_recognition'),
        capability=inventory.SearchCapability(position_probe=True, arc_index=True),
        path_exclusions=exclusions, h_unknown_exclusion=unknown, dasha_rows=[])
    p4 = [p for p in plan.pins if p.path_id == 'P4']
    assert p4 and all(p.disposition == 'excluded' and p.exclusion_reason == 'tier_withheld_by_ruling'
                      and p.ruling_ref == 'FOURQ-CLOSURE-20261027' and not p.obligations for p in p4)
    by_ob = {o.ob_id: p for p in plan.pins for o in p.obligations}
    assert not [i for i in plan.intervals if by_ob[i.ob_id].path_id == 'P4']



def test_p06_circularity_and_independence_rails_and_mandatory_record_stage():
    import ast
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    forbidden = {'life_events', 'life_event_log', 'life_event_reader'}
    for name in ('evaluator', 'inventory', 'record_store'):
        text = (root / 'services/gochara_kernel' / (name + '.py')).read_text()
        assert not any(t in text for t in forbidden), name
    independent = (root / 'services/gochara_kernel/nd_h_tables.py').read_text()
    imports = [n.module for n in ast.walk(ast.parse(independent)) if isinstance(n, ast.ImportFrom)]
    assert imports == ['__future__']
    stage = (root / 'services/gochara_kernel/verification_job.py').read_text()
    assert 'rd.verify_final_rule_records(conn, chart=chart, **g)' in stage



def test_fb38b_record_stage_reads_the_stored_normalized_annotation_and_refuses_corruption():
    import copy
    from services.gochara_kernel import record_derivation as rd, rule_registry as rr
    from datetime import datetime, timezone
    cls, path = 'business_launch', 'P3'
    lo, hi = datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc)
    exclusions, unknown = inventory.standing_exclusions()
    plan = inventory.plan_class_inventory(event_class=cls, chart=CHART, horizon=(lo, hi),
        sealed_paths=rr.bound_path_refs(), selected_versions=rr.selected_versions_for(cls),
        capability=inventory.SearchCapability(position_probe=True, arc_index=True),
        path_exclusions=exclusions, h_unknown_exclusion=unknown, dasha_rows=[])
    keys = {o.ob_id for pin in plan.pins if pin.path_id == path for o in pin.obligations}
    details = [copy.deepcopy(i.detail) for i in plan.intervals if i.ob_id in keys]
    edges = evaluator.enumerate_edges(cls, path, CHART, rule_version='1.2.0')
    stored = [(str(i), e.agent, e.relation, e.object_role, e.obj.canonical_target,
               str(i) if e.transit else None, e.affected_person) for i, e in enumerate(edges)]
    contacts = [(str(i), e.agent, e.relation, e.obj.canonical_target, lo, hi)
                for i, e in enumerate(edges) if e.transit]
    class Conn:
        def execute(self, sql, params):
            assert 'life_events' not in sql
            if 'FROM public.ka_gochara_search_interval' in sql:
                assert params == ('chart', '5.0', cls, path, '1.2.0')
                rows = [(d,) for d in details]
            elif 'FROM public.ka_gochara_relationship_record' in sql:
                rows = stored
            elif 'FROM public.ka_gochara_contact' in sql:
                rows = contacts
            else:
                raise AssertionError(sql)
            class Result:
                def fetchall(self): return rows
            return Result()
    grain = dict(chart_id='chart', generation='5.0', event_class=cls, path_id=path, rule_version='1.2.0', chart=VCHART)
    assert rd.verify_final_rule_records(Conn(), **grain) == {'records': len(stored), 'state': 'verified'}
    mercury_key = next(k for d in details for k in d['record_factors'] if k.startswith('mercury|'))
    for d in details:
        if mercury_key in d['record_factors']:
            d['record_factors'][mercury_key]['karaka_agent'] = 'non_karaka'
    with pytest.raises(RuntimeError, match='karaka_agent_mismatch: record '):
        rd.verify_final_rule_records(Conn(), **grain)


def test_p1_normalized_rank_category_is_stored_for_ordinary_and_delivery_edges():
    from services.gochara_kernel import rule_registry as rr
    from datetime import datetime, timezone
    lo, hi = datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc)
    rows = [inventory.DashaRow(str(i), i, 'mercury', lo, hi) for i in (1, 2, 3)]
    exclusions, unknown = inventory.standing_exclusions()
    plan = inventory.plan_class_inventory(event_class='business_launch', chart=CHART, horizon=(lo, hi),
        sealed_paths=rr.bound_path_refs(), selected_versions=rr.selected_versions_for('business_launch'),
        capability=inventory.SearchCapability(position_probe=True, arc_index=True),
        path_exclusions=exclusions, h_unknown_exclusion=unknown, dasha_rows=rows)
    keys = {o.ob_id for pin in plan.pins if pin.path_id == 'P1' for o in pin.obligations}
    factors = {k: v for iv in plan.intervals if iv.ob_id in keys for k, v in iv.detail['record_factors'].items()}
    assert any(k.startswith('mercury|') for k in factors)
    assert any(k.startswith('sun|') for k in factors) # XX.38 delivery, independent of the anchor's category
    for key, value in factors.items():
        assert value == {'tier': 'core', 'karaka_agent': 'karaka' if key.startswith('mercury|') else 'non_karaka'}


# Real 1206 store: same fixture and disposable guard as its neighbouring suite.
from .test_a53_inventory import _am5_dsn, am5  # noqa: F401


def test_the_final_rule_annotations_are_stored_verbatim_in_the_frozen_inventory_detail(am5):
    from . import test_a53_inventory as fixture
    from services.gochara_kernel import rule_registry as rr
    store, sky, _ = fixture._boot(am5, '5.38')
    exclusions, unknown = inventory.standing_exclusions()
    plan = inventory.plan_class_inventory(event_class='achievement_recognition', chart=fixture.CHART,
        horizon=(fixture.H0, fixture.H1), sealed_paths=rr.bound_path_refs(),
        selected_versions=rr.selected_versions_for('achievement_recognition'), capability=fixture.FULL,
        path_exclusions=exclusions, h_unknown_exclusion=unknown, dasha_rows=fixture.DASHA)
    fixture._write(am5, store, sky, '5.38', plan)
    rows = am5.execute('SELECT ob_id::text, lower(search_range), upper(search_range), detail'
        ' FROM public.ka_gochara_search_interval WHERE chart_id = %s AND generation = %s AND event_class = %s',
        (fixture.CHART_ID, '5.38', 'achievement_recognition')).fetchall()
    assert {(str(iv.ob_id), iv.start, iv.end): iv.detail for iv in plan.intervals} == {
        (oid, lo, hi): detail for oid, lo, hi, detail in rows}
    # P4 is switched off (FOURQ-CLOSURE-20261027): it plans no obligation, so it stores no interval. P4 was this
    # class's only path with DVI edges absorbed by CORE; the remaining paths still store the context verbatim.
    assert not [o for pin in plan.pins if pin.path_id == 'P4' for o in pin.obligations]
    from services.gochara_kernel.evaluator import final_rule_context
    by_ob = {o.ob_id: pin for pin in plan.pins for o in pin.obligations}
    annotated = [(by_ob[iv.ob_id], iv.detail) for iv in plan.intervals if 'final_rule_context' in (iv.detail or {})]
    assert annotated
    for pin, detail in annotated:
        assert pin.path_id != 'P4'
        assert detail['final_rule_context'] == final_rule_context('achievement_recognition', pin.path_id, fixture.CHART, pin.rule_version)
        assert isinstance(detail['record_factors'], dict)
    assert any(detail['record_factors'] for _, detail in annotated)


@pytest.fixture(autouse=True)
def _explicit_final_candidate_profile():
    from services.gochara_kernel import rule_registry
    with rule_registry.rule_profile(final_rules=True):
        yield


def test_verification_job_refuses_final_metadata_before_window_verification(monkeypatch):
    """The real job must call the independent metadata detector, and fail closed."""
    from services.gochara_kernel import verification_job as job, record_derivation as rd
    from services.gochara_kernel import contact_certify, window_gate, result_policy
    lo, hi = datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(job, 'take_locks', lambda *a: None)
    monkeypatch.setattr(job, '_inventory_header', lambda *a: (lo, hi, 'inventory', 'ledger'))
    monkeypatch.setattr(job, 'class_fingerprint', lambda *a: {})
    monkeypatch.setattr(job, '_sealed_paths', lambda *a: [('P3', '1.2.0')])
    monkeypatch.setattr(job, '_included_pins', lambda *a: [('P3', '1.2.0')])
    monkeypatch.setattr(window_gate, 'generation_output_problems', lambda *a: [])
    monkeypatch.setattr(result_policy, 'manifest_policy', lambda *a: None)
    monkeypatch.setattr(verifier, 'stored_selection', lambda *a, **k: {'p3': '1.2.0'})
    monkeypatch.setattr(verifier, 'rederive_inventory_digest', lambda *a, **k: {'digest': 'inventory', 'obligations': []})
    monkeypatch.setattr(verifier, 'rederive_ledger_digest', lambda *a, **k: 'ledger')
    monkeypatch.setattr(verifier, 'read_chart', lambda *a: VCHART)
    monkeypatch.setattr(verifier, 'read_chart_snapshot', lambda *a: VCHART)      # G12: the job reads the snapshot's COPY of the natal rows
    monkeypatch.setattr(contact_certify, 'certify_contact_geometry', lambda *a, **k: {})
    def refuse(conn, **kw):
        assert kw['chart'] == VCHART and kw['rule_version'] == '1.2.0'
        raise RuntimeError('karaka_agent_mismatch: record corrupt')
    monkeypatch.setattr(rd, 'verify_final_rule_records', refuse)
    def must_not_run(*a, **kw):
        pytest.fail('record/window checks ran without checking final metadata')
    monkeypatch.setattr(rd, 'verify_path_records', must_not_run)
    class Conn:
        def execute(self, *a, **kw):
            return self
        def fetchone(self):
            return (['snapshot-fact'],)
        def fetchall(self):              # merge-back wave 3c-a: the geometry stage now reconciles near-misses (the stub's truthy fetchone says the layer exists) and reads the stored rows: none here
            return []
    with pytest.raises(job.VerificationDisagrees, match='karaka_agent_mismatch'):
        job._verify_class(Conn(), chart_id='chart', generation='candidate', event_class='business_launch',
            position_at=None, configured_selection={'P3': '1.2.0'}, path_rulings={}, h_unknown={},
            moon_scope_domain=False, factor_rows_for=lambda *a: [], drishti_bound=False,
            vedha_bound=False, persist=False)


@pytest.mark.parametrize('final', [False, True])
def test_verification_cli_uses_the_same_explicit_candidate_profile(final, monkeypatch):
    import psycopg
    from pipeline.orchestrator import verification_job as cli
    from services.gochara_kernel import rule_registry as rr
    monkeypatch.setenv(cli.ENV_URL, 'postgresql://postgres@127.0.0.1:55433/postgres')
    monkeypatch.setenv('GOCHARA_RUNNER_IMAGE_DIGEST', 'sha256:' + '1' * 64)      # SR-OD1 R8: a persisting launch names its image and execution
    monkeypatch.setenv('CLOUD_RUN_EXECUTION', 'projects/p/locations/l/jobs/gochara-verification-job/executions/e1')
    monkeypatch.setenv('GOCHARA_RUNNER_COMMIT', 'a' * 40)      # window_gate.runner_identity names the commit from here, else the repo HEAD: a git-less tree copy (the mutation harness) has none
    monkeypatch.setattr(cli, '_moon_scope_available', lambda conn: False)
    closed, observed = [], []
    class Conn:
        def close(self):
            closed.append(True)
    monkeypatch.setattr(psycopg, 'connect', lambda *a, **kw: Conn())
    def run(conn, **kw):
        observed.append(kw['configured_selection_for']('property_acquisition')['P3'])
        assert (('P3', '1.2.0') in kw['path_refs']) is final
        return {'exit_code': 0}
    monkeypatch.setattr(cli.vj, 'run', run)
    args = ['--chart', 'test-chart', '--ephe-path', '/unused-by-this-parser-test']
    if final:
        args.append('--final-rules')
    assert cli.main(args) == 0
    assert observed == (['1.2.0'] if final else ['1.0.0'])
    assert closed == [True]
    # The surrounding final-test fixture's context was restored after either CLI run.
    assert rr.selected_versions_for('property_acquisition')['P3'] == '1.2.0'


def test_golden_fixture_drops_its_owned_database_when_substrate_setup_is_interrupted(monkeypatch):
    """Setup failures must not leave a template DB behind on the shared local cluster."""
    import psycopg
    from . import test_a55_replace_chain as harness
    from .test_a53_record_store import ADMIN_DSN
    from ._disposable_db_guard import guarded_admin_connect
    created = []
    real_create = harness.create_am5_database
    def capture(*args, **kwargs):
        out = real_create(*args, **kwargs)
        created.append(out)
        return out
    def interrupt(*args, **kwargs):
        raise RuntimeError('deliberate substrate setup interruption')
    monkeypatch.setattr(harness, 'create_am5_database', capture)
    monkeypatch.setattr(harness.writer_mod.GocharaV5Writer, 'run_substep', interrupt)
    iterator = harness.template.__wrapped__()
    try:
        with pytest.raises(RuntimeError, match='deliberate substrate setup interruption'):
            next(iterator)
        assert len(created) == 1
        with guarded_admin_connect(ADMIN_DSN, autocommit=True) as admin:
            assert admin.execute('SELECT 1 FROM pg_database WHERE datname = %s',
                                 (created[0][1],)).fetchone() is None
    finally:
        # A red run cleans only the exact database this invocation created.
        iterator.close()
        for admin, name, _ in created:
            if not admin.closed:
                harness.drop_am5_database(admin, name)
