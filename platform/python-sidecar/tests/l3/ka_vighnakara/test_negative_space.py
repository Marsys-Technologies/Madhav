"""ALGO3.4 consumer oracles; planted data proves no live doctrine admission."""
import importlib.util
import ast
import json
import re
from types import SimpleNamespace
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[3]

# Independent regression floor, never the lint's source of table ownership.
# ka_kshetra/writer.py:_OWNED_TABLES; ka_bhavishya_lekha.py's SQL targets.
EXPECTED_FORECASTER_TABLES = {
    'kala_field_provenance', 'kala_field_salience', 'kala_insights',
    'kala_timeline_spec', 'kala_field_windows', 'kala_field_null', 'kala_field',
    'kala_field_snapshots', 'kala_field_primitives', 'kala_field_boundaries',
    'kala_field_clocks', 'kala_field_routes', 'kala_field_promise_edges',
    'kala_field_promise_nodes', 'kala_field_kinematics', 'kala_bhavishya',
    'issued_forecast',
}


def api():
    assert importlib.util.find_spec('services.ka_vighnakara.model') is not None, 'K3 typed model missing'
    from services.ka_vighnakara import model
    return model


def finding(**changes):
    data = dict(contract_version='k3-negative-space/1.0.0', assertion_id='fixture:vedha',
                chart_id='00000000-0000-0000-0000-000000000392', generation='candidate:fixture',
                event_class_id='career', mechanism='vedha', exposure='in_risk_set', knowledge='complete',
                rule_conclusion='obstructed', defeat_state='active', measurement='not_estimated_here',
                judge_state='active', coverage='complete', binding='fixture_only',
                interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-02-01T00:00:00Z'},
                roots={'record_ids':['fixture:judge'],'fact_ids':[],'contact_ids':[]},
                source={'text':'Phaladipika','locator':'XXVI; planted fixture'},
                what='vedha obstruction', by_what='fixture:obstructor', protections=[],
                release={'kind':'instant','instant':'2026-02-01T00:00:00Z'}, null_reason=None)
    data.update(changes)
    return api().Finding.model_validate(data)


def evaluate(**changes):
    return api().interpret(finding(**changes))


def protection(**changes):
    value = dict(target_assertion_id='fixture:vedha', kind='defeats', fact_ids=['fixture:Jupiter-kendra'],
                 source={'text':'Patel','locator':'PG2299; planted fixture'},
                 interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-02-01T00:00:00Z'})
    value.update(changes)
    return value


def test_active_vedha_is_in_force():
    assert evaluate().effective_state == 'obstruction_in_force'


def test_active_vedha_release_equals_interval_end():
    assert evaluate().release.instant == datetime(2026,2,1,tzinfo=timezone.utc)


@pytest.mark.parametrize('axis,value', [('exposure','in_risk_set'),('knowledge','complete'),
    ('rule_conclusion','obstructed'),('defeat_state','active'),('measurement','not_estimated_here')])
def test_five_axes_survive_independently(axis,value):
    assert getattr(evaluate(),axis) == value


def test_protection_is_cancelled_never_active():
    assert evaluate(protections=[protection()]).effective_state == 'obstruction_cancelled'


def test_protection_retains_fact_ids():
    assert evaluate(protections=[protection()]).roots.fact_ids == ('fixture:Jupiter-kendra',)


def test_cancelled_candidate_conclusion_retained():
    assert evaluate(protections=[protection()]).rule_conclusion == 'obstructed'


def test_unrelated_protection_cannot_cancel():
    assert evaluate(protections=[protection(target_assertion_id='another-conclusion')]).effective_state == 'obstruction_in_force'


def test_nonoverlapping_protection_cannot_cancel():
    assert evaluate(protections=[protection(interval={'t0':'2027-01-01T00:00:00Z','t1':'2027-02-01T00:00:00Z'})]).effective_state == 'obstruction_in_force'


def test_partial_interval_protection_is_partial():
    assert evaluate(protections=[protection(interval={'t0':'2026-01-10T00:00:00Z','t1':'2026-02-01T00:00:00Z'})]).effective_state == 'obstruction_partly_cancelled'


@pytest.mark.parametrize('kind,state', [('excepts','obstruction_cancelled'),
    ('partly_defeats','obstruction_partly_cancelled'),('contests','obstruction_contested')])
def test_targeted_edge_states(kind,state):
    assert evaluate(protections=[protection(kind=kind)]).effective_state == state


@pytest.mark.parametrize('coverage', ['absent','incomplete'])
def test_missing_coverage_never_quiet(coverage):
    assert evaluate(coverage=coverage).effective_state == 'information_unavailable'


@pytest.mark.parametrize('knowledge', ['unsearched','inputs_missing','computation_failed'])
def test_unavailable_knowledge_never_silent(knowledge):
    assert evaluate(knowledge=knowledge).effective_state == 'information_unavailable'


def test_inactive_vedha_with_complete_coverage_is_silent():
    assert evaluate(judge_state='inactive',rule_conclusion='none').effective_state == 'evaluated_silent'


def test_unqualified_vedha_retains_reason():
    assert evaluate(judge_state='unqualified',null_reason='node_obstruction_undecided').null_reason == 'node_obstruction_undecided'


def test_unbound_input_is_unavailable_even_when_planted_active():
    assert evaluate(binding='unbound',null_reason='judge_vedha_source_mapping_unadmitted').effective_state == 'information_unavailable'


def test_unknown_release_is_valid():
    assert evaluate(release={'kind':'unknown'}).release.kind == 'unknown'


def test_unknown_release_has_named_reason():
    assert evaluate(release={'kind':'unknown'}).release_reason == 'release_unknown'


def test_conditional_release_preserves_predicate():
    assert evaluate(release={'kind':'conditional','predicate_ref':'fixture:exit'}).release.predicate_ref == 'fixture:exit'


def test_rikta_produces_no_natal_row():
    assert api().interpret(finding(mechanism='rikta_tithi')) is None


@pytest.mark.parametrize('mechanism', ['daily_gandanta','kulika','transit_combustion'])
def test_non_natal_doctrines_not_admitted(mechanism):
    assert api().interpret(finding(mechanism=mechanism)) is None


def test_outside_risk_set():
    assert evaluate(exposure='outside_risk_set').effective_state == 'outside_risk_set'


def test_method_inapplicable():
    assert evaluate(exposure='method_inapplicable').effective_state == 'method_inapplicable'


def test_unresolved_defeat_not_operational():
    assert evaluate(defeat_state='unresolved').effective_state == 'information_unavailable'


@pytest.mark.parametrize('field,value', [('severity_score',0.5),('weight',0.5),('multiplier',0.45),('override_score',0.5)])
def test_numeric_weights_refused(field,value):
    with pytest.raises(ValueError): finding(**{field:value})


def test_no_obstruction_active_with_cancellation_subfield():
    assert 'obstruction_active' not in json.dumps(evaluate(protections=[protection()]).model_dump(mode='json'))


def test_invalid_release_instant_refused():
    with pytest.raises(ValueError): finding(release={'kind':'instant','instant':'2025-01-01T00:00:00Z'})


def test_unknown_binding_requires_named_reason():
    with pytest.raises(ValueError): finding(binding='unbound')


def test_missing_judge_vedha_state_never_silent():
    assert evaluate(judge_state=None,rule_conclusion='none').effective_state == 'information_unavailable'


def test_trigger_absent_doctrine_is_unqualified():
    assert importlib.util.find_spec('services.kala_trigger.negative_space') is not None, 'K3 trigger boundary missing'
    from services.kala_trigger.negative_space import unavailable_trigger
    assert unavailable_trigger('fixture:unadmitted', finding()).effective_state == 'information_unavailable'


def test_contract_survivors_are_not_invented():
    artifact=json.loads((ROOT/'services/ka_vighnakara/input_contract_v1.json').read_text())
    assert artifact['live_bindings']['trigger_mechanisms']['survivors'] is None


def _writer_lint_nodes(tree, legacy):
    """Keep legacy exemptions only for bodies unreachable from the new path."""
    definitions = {node.name: node for node in tree.body
                   if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))}
    classes = {name: node for name, node in definitions.items() if isinstance(node, ast.ClassDef)}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    definitions[target.id] = node

    def method_targets(owner, name, seen=None):
        seen = set() if seen is None else seen
        if owner in seen or owner not in classes:
            return
        seen.add(owner)
        for member in classes[owner].body:
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and member.name == name:
                yield member
        # (I) INTERPRETATION: inspect all matching ancestor implementations,
        # including overrides; this lint conservatively over-approximates dispatch.
        for base in classes[owner].bases:
            if isinstance(base, ast.Name):
                yield from method_targets(base.id, name, seen)

    writer = classes['KaVighnakaraWriter']
    run = next(node for node in writer.body if isinstance(node, ast.FunctionDef) and node.name == 'run')
    fallback = run.body[-1]
    authorized_fallback = ast.dump(ast.parse('return super().run(ctx)').body[0])
    pending = [(node, writer.name) for node in writer.body]
    visited, reachable, methods = set(), set(), set()
    while pending:
        node, owner = pending.pop()
        key = (id(node), owner)
        if key in visited:
            continue
        visited.add(key)
        if node is fallback and ast.dump(node) == authorized_fallback:
            continue
        if isinstance(node, ast.ClassDef):
            pending.extend((child, node.name) for child in node.body)
            continue
        if isinstance(node, ast.Name) and node.id in definitions and node.id not in reachable:
            reachable.add(node.id)
            pending.append((definitions[node.id], None))
        if isinstance(node, ast.Attribute):
            receiver = node.value
            if isinstance(receiver, ast.Name) and receiver.id in {'self', 'cls'} and owner:
                owners = [owner]
            elif isinstance(receiver, ast.Name) and receiver.id in classes:
                owners = [receiver.id]
            elif isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Name) and receiver.func.id == 'super' and owner:
                owners = [base.id for base in classes[owner].bases if isinstance(base, ast.Name)]
            else:
                # (I) INTERPRETATION: an untyped receiver may be any local helper
                # class; do not silently omit inherited storage/helper methods.
                owners = classes
            for receiver_owner in owners:
                for method in method_targets(receiver_owner, node.attr):
                    methods.add(method)
                    pending.append((method, receiver_owner))
            # A named base.method reference reaches that method, not the whole
            # compatibility class (whose unrelated methods remain exempt).
            if isinstance(receiver, ast.Name) and receiver.id in classes:
                continue
        pending.extend((child, owner) for child in ast.iter_child_nodes(node))
    return [node for node in tree.body
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            or node.name not in legacy or node.name in reachable] + list(methods)


def _forecaster_output_tables():
    """Read ownership as data, without importing/registering downstream writers."""
    tree = ast.parse((ROOT/'services/ka_kshetra/writer.py').read_text())
    inventories = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in {'_OWNED_TABLES', '_HASHED_TABLES'}:
                inventories[node.target.id] = ast.literal_eval(node.value)
    tables = {table for table, _ in inventories['_OWNED_TABLES']}
    assert tables and set(inventories['_HASHED_TABLES']) <= tables, 'field ownership inventory drift'

    declarations = json.loads((ROOT.parent/'scripts/governance/asset_declarations.json').read_text())
    family = re.compile(r'(?:^|_)(?:forecaster|bhavishya|insights?|timeline)(?:_|$)')
    for asset_id, declaration in declarations['assets'].items():
        if not asset_id.startswith('ka_') or not (asset_id == 'ka_kshetra' or family.search(asset_id)):
            continue
        # (I) INTERPRETATION: the registrar and any declared insight/timeline
        # family are downstream too; a shared output table is forbidden whole.
        if declaration.get('read_table'):
            tables.add(declaration['read_table'])
        writer = ROOT/f'pipeline/orchestrator/writers/{asset_id}.py'
        if not writer.is_file():
            assert declaration.get('read_table'), f'{asset_id}: no output ownership evidence'
            continue
        for node in ast.walk(ast.parse(writer.read_text())):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Writer SQL declares targets absent from the serving inventory.
                tables.update(re.findall(r'\bINSERT\s+INTO\s+([a-z_][a-z_0-9]*)',
                                         node.value, re.IGNORECASE))
            if (isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute))
                    and (node.func.id if isinstance(node.func, ast.Name) else node.func.attr)
                    in {'insert_immutable_checked', 'replace_candidate_partition'}):
                # Both helpers' actual contract has table at positional index 1.
                assert len(node.args) > 1, f'{asset_id}: output target must be explicit'
                table = ast.literal_eval(node.args[1])
                assert isinstance(table, str), f'{asset_id}: output target must be a literal table'
                tables.add(table)
    assert all(re.fullmatch(r'[a-z_][a-z_0-9]*', table) for table in tables)
    return tables


def test_derived_inventory_covers_every_current_forecaster_output():
    assert EXPECTED_FORECASTER_TABLES <= _forecaster_output_tables()


def test_no_downstream_reads_or_multiplier_in_new_path():
    api()
    paths=list((ROOT/'services/ka_vighnakara').rglob('*.py'))+[
        ROOT/'services/kala_trigger/negative_space.py',
        ROOT/'pipeline/orchestrator/writers/ka_vighnakara.py']
    table_names = '|'.join(re.escape(table) for table in sorted(_forecaster_output_tables()))
    prohibited=re.compile(r'\b(?:'+table_names+r'|kala_field\w*|ka_kshetra\w*|kala_convergence|compose_with_ka_sangam)\b',
                          re.IGNORECASE)
    weights={'severity_score','override_score','weight','multiplier'}
    for path in paths:
        tree=ast.parse(path.read_text())
        if path == ROOT/'pipeline/orchestrator/writers/ka_vighnakara.py':
            # Exempt only named compatibility definitions. All other globals
            # are inspected, including newly introduced helper bodies. An
            # exempt helper used by the registered path loses its exemption,
            # transitively; only the explicit super().run fallback stays legacy.
            legacy = {'_LegacyKaVighnakaraWriter', '_is_rikta_tithi', '_ordinal',
                '_chart_adverse_signs', '_severity', '_coerce_date', '_get_sidereal_lon',
                '_lon_to_sign', '_jd_from_date', '_detect_all', '_check_malefic_transit',
                '_check_panchanga_obstruction', '_check_gandanta', '_check_papakartari',
                '_check_combustion', '_detect_obstructions'}
            tree.body = _writer_lint_nodes(tree, legacy)
        for node in ast.walk(tree):
            if isinstance(node,ast.Constant) and isinstance(node.value,str):
                assert not prohibited.search(node.value), (path,node.lineno)
                assert node.value not in weights, (path,node.lineno)
            if isinstance(node,(ast.Name,ast.Attribute,ast.alias)):
                name=(node.id if isinstance(node,ast.Name) else
                      node.attr if isinstance(node,ast.Attribute) else node.name)
                assert not prohibited.search(name) and name not in weights, (path,node.lineno)
            if isinstance(node,ast.keyword) and node.arg in weights:
                # Only the exact, inert legacy INSERT slots are exempt.
                assert (path in {ROOT/'services/ka_vighnakara/storage.py',
                                         ROOT/'services/ka_vighnakara/sealed_storage.py'}
                        and node.arg in {'severity_score','override_score'}
                        and isinstance(node.value,ast.Constant) and node.value.value == 0), (path,node.lineno)


@pytest.mark.parametrize('table', sorted(EXPECTED_FORECASTER_TABLES))
def test_every_forecaster_output_read_is_rejected(monkeypatch, table):
    """Execute the reviewer's real storage mutant before requiring rejection."""
    from services.ka_vighnakara import storage
    from tests.l3.ka_vighnakara.test_storage_unit import CandidateCursor

    sql = f'SELECT * FROM {table}'
    if table == 'kala_insights':
        sql += ' WHERE lel_derived = FALSE'
    target = ROOT/'services/ka_vighnakara/storage.py'
    original = Path.read_text
    source = original(target)
    marker = "    chart = str(ctx.config['chart_id'])"
    assert source.count(marker) == 1
    mutated = source.replace(marker, '    ctx.db_conn.execute('+repr(sql)+')\n'+marker)
    namespace = dict(vars(storage))
    namespace['replace_candidate_partition'] = lambda *args: 0
    exec(compile(mutated, '<forecaster output read mutant>', 'exec'), namespace)
    observed = []
    ctx = SimpleNamespace(dry_run=False, config={'chart_id':str(finding().chart_id)},
        build_id='fixture:build', db_conn=SimpleNamespace(
            execute=observed.append, cursor=lambda **kwargs: CandidateCursor()))
    assert namespace['write_fixture_candidate'](ctx, []) == 0
    assert observed == [sql]
    monkeypatch.setattr(Path, 'read_text',
        lambda path, *args, **kwargs: mutated if path == target else original(path, *args, **kwargs))
    with pytest.raises(AssertionError):
        test_no_downstream_reads_or_multiplier_in_new_path()


@pytest.mark.parametrize('inventory', ['owned', 'declaration', 'immutable_target'])
def test_new_forecaster_output_automatically_becomes_forbidden(monkeypatch, inventory):
    """An output outside every old naming family must still trip the lint."""
    table = 'new_prediction_output'
    original = Path.read_text
    if inventory == 'owned':
        target = ROOT/'services/ka_kshetra/writer.py'
        tree = ast.parse(original(target))
        owned = next(node for node in tree.body
                     if isinstance(node, ast.AnnAssign) and node.target.id == '_OWNED_TABLES')
        owned.value.elts.append(ast.parse(repr((table, None)), mode='eval').body)
        mutated = ast.unparse(ast.fix_missing_locations(tree))
    elif inventory == 'declaration':
        target = ROOT.parent/'scripts/governance/asset_declarations.json'
        declarations = json.loads(original(target))
        declarations['assets']['ka_forecaster_future'] = {'read_table': table}
        mutated = json.dumps(declarations)
    else:
        target = ROOT/'pipeline/orchestrator/writers/ka_bhavishya_lekha.py'
        mutated = original(target) + f'\ninsert_immutable_checked(None, {table!r}, {{}}, {{}})\n'
    monkeypatch.setattr(Path, 'read_text',
        lambda path, *args, **kwargs: mutated if path == target else original(path, *args, **kwargs))
    # Baseline is clean; rejection below must be for the actual new read.
    test_no_downstream_reads_or_multiplier_in_new_path()
    test_every_forecaster_output_read_is_rejected(monkeypatch, table)


@pytest.mark.parametrize('exposure',['outside_risk_set','method_inapplicable'])
def test_unbound_trigger_always_names_mapping_hole(exposure):
    from services.kala_trigger.negative_space import unavailable_trigger
    assert unavailable_trigger('fixture:unknown',finding(exposure=exposure)).null_reason == 'trigger_survivor_roster_and_doctrine_unadmitted'


@pytest.mark.parametrize('mechanism',['rikta_tithi','daily_gandanta','kulika','transit_combustion'])
def test_non_natal_trigger_request_is_explicitly_refused(mechanism):
    from services.kala_trigger.negative_space import unavailable_trigger
    with pytest.raises(ValueError,match='natal'): unavailable_trigger(mechanism,finding())


@pytest.mark.parametrize('conclusion',['none','supportive'])
def test_active_vedha_cannot_be_relabelled_as_quiet(conclusion):
    with pytest.raises(ValueError,match='active vedha'): finding(rule_conclusion=conclusion)


def test_unqualified_vedha_preserves_node_reason_as_unavailable():
    assert evaluate(judge_state='unqualified',null_reason='node_obstruction_undecided').effective_state == 'information_unavailable'


def test_protection_requires_cited_evidence():
    with pytest.raises(ValueError): finding(protections=[protection(fact_ids=[])])


# K3 packet-exit counterexamples (M_K3_*); planted inputs only.
def test_split_full_protection_remains_cancelled():
    edges = [protection(interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-01-15T00:00:00Z'}),
             protection(interval={'t0':'2026-01-15T00:00:00Z','t1':'2026-02-01T00:00:00Z'})]
    assert evaluate(protections=edges).effective_state == 'obstruction_cancelled'
    assert evaluate(protections=list(reversed(edges))).effective_state == 'obstruction_cancelled'


@pytest.mark.parametrize('incoming,expected', [('cancelled','obstruction_cancelled'),
    ('excepted','obstruction_cancelled'), ('unresolved','information_unavailable'),
    ('contested','obstruction_contested')])
def test_partial_protection_preserves_f1_state(incoming,expected):
    row = evaluate(defeat_state=incoming, protections=[protection(interval={
        't0':'2026-01-10T00:00:00Z','t1':'2026-02-01T00:00:00Z'})])
    assert row.defeat_state == incoming
    assert row.effective_state == expected


@pytest.mark.parametrize('incoming', ['cancelled','excepted','partly_cancelled'])
@pytest.mark.parametrize('edges', [[], [protection(target_assertion_id='unrelated')],
    [protection(interval={'t0':'2027-01-01T00:00:00Z','t1':'2027-02-01T00:00:00Z'})],
    [protection(kind='contests')]])
def test_cancellation_requires_retained_defeating_evidence(incoming,edges):
    row = evaluate(defeat_state=incoming,protections=edges)
    assert row.effective_state == 'information_unavailable'
    assert row.null_reason == 'defeating_evidence_unavailable'


def test_partial_edge_cannot_substantiate_full_cancellation():
    row = evaluate(defeat_state='cancelled',protections=[protection(kind='partly_defeats')])
    assert row.effective_state == 'information_unavailable'


@pytest.mark.parametrize('release', [{'kind':'instant','instant':'2026-02-01T00:00:00Z'},
    {'kind':'instant','instant':'2026-01-10T00:00:00Z'}, {'kind':'unknown'}])
def test_protection_onset_releases_remaining_obstruction(release):
    row = evaluate(protections=[protection(interval={
        't0':'2026-01-10T00:00:00Z','t1':'2026-02-01T00:00:00Z'})],release=release)
    assert row.release.instant == datetime(2026,1,10,tzinfo=timezone.utc)
    assert row.release_reason is None


def test_split_terminal_protection_uses_earliest_continuous_onset():
    row = evaluate(protections=[
        protection(interval={'t0':'2026-01-10T00:00:00Z','t1':'2026-01-15T00:00:00Z'}),
        protection(interval={'t0':'2026-01-15T00:00:00Z','t1':'2026-02-01T00:00:00Z'})])
    assert row.release.instant == datetime(2026,1,10,tzinfo=timezone.utc)


def test_protection_gap_is_partial_and_release_uses_terminal_suffix():
    row = evaluate(protections=[
        protection(interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-01-14T00:00:00Z'}),
        protection(kind='excepts',interval={'t0':'2026-01-15T00:00:00Z','t1':'2026-02-01T00:00:00Z'})])
    assert row.effective_state == 'obstruction_partly_cancelled'
    assert row.release.instant == datetime(2026,1,15,tzinfo=timezone.utc)


def test_conditional_protection_release_is_not_assumed_satisfied():
    row = evaluate(protections=[protection()],release={'kind':'conditional','predicate_ref':'fixture:condition'})
    assert row.release.kind == 'conditional'
    assert row.release.predicate_ref == 'fixture:condition'


@pytest.mark.parametrize('changes', [{'defeat_state':'unresolved'}, {'coverage':'absent'},
    {'knowledge':'unsearched'}, {'defeat_state':'contested'}])
def test_unavailable_or_contested_input_cannot_license_early_release(changes):
    row = evaluate(**changes,protections=[protection()])
    assert row.release.instant == datetime(2026,2,1,tzinfo=timezone.utc)


@pytest.mark.parametrize('edge', [protection(kind='partly_defeats'),
    protection(kind='contests'), protection(target_assertion_id='unrelated'),
    protection(interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-01-15T00:00:00Z'})])
def test_nonterminal_or_unqualified_protection_does_not_advance_release(edge):
    assert evaluate(protections=[edge]).release.instant == datetime(2026,2,1,tzinfo=timezone.utc)


def test_arbitrary_early_vedha_release_is_refused():
    with pytest.raises(ValueError,match='release'):
        finding(release={'kind':'instant','instant':'2026-01-10T00:00:00Z'})


@pytest.mark.parametrize('relative', ['services/ka_vighnakara/storage.py',
    'pipeline/orchestrator/writers/ka_vighnakara.py'])
def test_forecaster_read_mutant_is_detected(monkeypatch,relative):
    target = ROOT/relative
    original = Path.read_text
    def mutated(path,*args,**kwargs):
        source = original(path,*args,**kwargs)
        if path == target:
            if path.name == 'storage.py':
                source = source.replace("    if ctx.dry_run:",
                    "    ctx.db_conn.execute('SELECT * FROM kala_field')\n    if ctx.dry_run:")
            else:
                source = source.replace("        if 'negative_space_fixture_inputs' in ctx.config:",
                    "        if 'negative_space_fixture_inputs' in ctx.config:\n            ctx.db_conn.execute('SELECT * FROM kala_field')")
        return source
    monkeypatch.setattr(Path,'read_text',mutated)
    with pytest.raises(AssertionError):
        test_no_downstream_reads_or_multiplier_in_new_path()


def test_forecaster_read_in_reachable_writer_helper_is_rejected(monkeypatch):
    target = ROOT/'pipeline/orchestrator/writers/ka_vighnakara.py'
    original = Path.read_text
    def with_helper(path,*args,**kwargs):
        source = original(path,*args,**kwargs)
        if path == target:
            marker = "        if 'negative_space_fixture_inputs' in ctx.config:"
            assert source.count(marker) == 1
            source = source.replace(marker, marker+'\n            _review_fixture_helper(ctx)')
            source += '\n\ndef _review_fixture_helper(ctx):\n    return ctx.db_conn.execute("SELECT * FROM kala_field")\n'
            helper = ast.parse(source).body[-1]
            ns = {}
            exec(compile(ast.Module(body=[helper], type_ignores=[]), '<review helper>', 'exec'), ns)
            calls = []
            ns['_review_fixture_helper'](SimpleNamespace(db_conn=SimpleNamespace(execute=calls.append)))
            assert calls == ['SELECT * FROM kala_field']
        return source
    monkeypatch.setattr(Path, 'read_text', with_helper)
    with pytest.raises(AssertionError):
        test_no_downstream_reads_or_multiplier_in_new_path()


@pytest.mark.parametrize('call,helper', [
    ('_review_outer(ctx)', '\n\ndef _review_outer(ctx):\n    return _review_inner(ctx)\n\ndef _review_inner(ctx):\n    return ctx.db_conn.execute("SELECT * FROM kala_field")\n'),
    ('_detect_obstructions(None)', ''),
])
def test_reachable_transitive_or_legacy_helper_cannot_escape_lint(monkeypatch, call, helper):
    target = ROOT/'pipeline/orchestrator/writers/ka_vighnakara.py'
    original = Path.read_text
    def mutated(path,*args,**kwargs):
        source = original(path,*args,**kwargs)
        if path == target:
            marker = "        if 'negative_space_fixture_inputs' in ctx.config:"
            assert source.count(marker) == 1
            source = source.replace(marker, marker+'\n            '+call) + helper
        return source
    monkeypatch.setattr(Path, 'read_text', mutated)
    with pytest.raises(AssertionError):
        test_no_downstream_reads_or_multiplier_in_new_path()


@pytest.mark.parametrize('dispatch', ['inherited', 'transitive', 'super_attribute'])
def test_inherited_reachable_helper_cannot_escape_lint(monkeypatch, dispatch):
    """K3-B5 reviewer oracle: execute the read, then require lint rejection."""
    from pipeline.orchestrator.writers import WriterResult
    from services.ka_vighnakara import storage

    target = ROOT/'pipeline/orchestrator/writers/ka_vighnakara.py'
    original = Path.read_text
    source = original(target)
    marker = "        if 'negative_space_fixture_inputs' in ctx.config:"
    assert source.count(marker) == 1
    call = ('super()._fetch_combustion_orbs(ctx.db_conn)'
            if dispatch == 'super_attribute' else 'self._fetch_combustion_orbs(ctx.db_conn)')
    tree = ast.parse(source.replace(marker, marker+'\n            '+call))
    legacy = next(node for node in tree.body
                  if isinstance(node, ast.ClassDef) and node.name == '_LegacyKaVighnakaraWriter')
    helper = next(node for node in legacy.body
                  if isinstance(node, ast.FunctionDef) and node.name == '_fetch_combustion_orbs')
    read = ast.parse('return conn.execute("SELECT * FROM kala_field")').body
    methods = [helper]
    if dispatch == 'transitive':
        helper.body = ast.parse('return self._review_inner(conn)').body
        inner = ast.parse('def _review_inner(self, conn):\n    pass').body[0]
        inner.body = read
        legacy.body.append(inner)
        methods.append(inner)
    else:
        helper.body = read
    mutated = ast.unparse(ast.fix_missing_locations(tree))

    # Run the real fixture branch with only candidate storage replaced and a
    # recording connection; neither this helper nor its transitive call is mocked.
    registered = next(node for node in tree.body
                      if isinstance(node, ast.ClassDef) and node.name == 'KaVighnakaraWriter')
    registered.decorator_list = []
    test_legacy = ast.ClassDef(name='_LegacyKaVighnakaraWriter', bases=[], keywords=[],
                              body=methods, decorator_list=[])
    executable = ast.fix_missing_locations(ast.Module(body=[test_legacy, registered], type_ignores=[]))
    namespace = {'WriterResult': WriterResult}
    exec(compile(executable, '<inherited fixture mutant>', 'exec'), namespace)
    calls = []
    monkeypatch.setattr(storage, 'write_fixture_candidate', lambda ctx, inputs: 0)
    ctx = SimpleNamespace(dry_run=False, db_conn=SimpleNamespace(execute=calls.append),
                          config={'negative_space_fixture_inputs': []})
    assert namespace['KaVighnakaraWriter']().run(ctx).rows_inserted == 0
    assert calls == ['SELECT * FROM kala_field']
    monkeypatch.setattr(Path, 'read_text',
        lambda path, *args, **kwargs: mutated if path == target else original(path, *args, **kwargs))
    with pytest.raises(AssertionError):
        test_no_downstream_reads_or_multiplier_in_new_path()


@pytest.mark.parametrize('call', [
    'self._fetch_combustion_orbs(ctx.db_conn)',
    'super()._fetch_combustion_orbs(ctx.db_conn)',
    '_LegacyKaVighnakaraWriter._fetch_combustion_orbs(self, ctx.db_conn)',
])
def test_clean_inherited_helper_keeps_unrelated_legacy_methods_exempt(monkeypatch, call):
    target = ROOT/'pipeline/orchestrator/writers/ka_vighnakara.py'
    original = Path.read_text
    source = original(target)
    marker = "        if 'negative_space_fixture_inputs' in ctx.config:"
    assert source.count(marker) == 1
    tree = ast.parse(source.replace(marker, marker+'\n            '+call))
    legacy = next(node for node in tree.body
                  if isinstance(node, ast.ClassDef) and node.name == '_LegacyKaVighnakaraWriter')
    helper = next(node for node in legacy.body
                  if isinstance(node, ast.FunctionDef) and node.name == '_fetch_combustion_orbs')
    helper.body = ast.parse('return {}').body
    mutated = ast.unparse(ast.fix_missing_locations(tree))
    monkeypatch.setattr(Path, 'read_text',
        lambda path, *args, **kwargs: mutated if path == target else original(path, *args, **kwargs))
    test_no_downstream_reads_or_multiplier_in_new_path()


@pytest.mark.parametrize('call', [
    '_review_storage(ctx)',
    '_review_storage_callback(ctx)',
])
def test_storage_helper_hierarchy_and_bound_method_are_inspected(monkeypatch, call):
    target = ROOT/'pipeline/orchestrator/writers/ka_vighnakara.py'
    original = Path.read_text
    source = original(target)
    marker = "        if 'negative_space_fixture_inputs' in ctx.config:"
    assert source.count(marker) == 1
    # The read lives two bases away in the second inheritance branch; the
    # intermediate inherited method uses self to reach an exempt global helper.
    source = source.replace(marker, marker+'\n            '+call) + '''

class _ReviewEmpty:
    pass

class _ReviewStorageAncestor(_LegacyKaVighnakaraWriter):
    def prepare(self, ctx):
        return self._review_read(ctx)

class _ReviewStorageMiddle(_ReviewStorageAncestor):
    pass

class _ReviewStorage(_ReviewEmpty, _ReviewStorageMiddle):
    pass

def _review_storage(ctx):
    helper = _ReviewStorage()
    return helper.prepare(ctx)

def _review_storage_callback(ctx):
    callback = _ReviewStorage().prepare
    return callback(ctx)
'''
    tree = ast.parse(source)
    legacy = next(node for node in tree.body
                  if isinstance(node, ast.ClassDef) and node.name == '_LegacyKaVighnakaraWriter')
    legacy.body.append(ast.parse('def _review_read(self, ctx):\n    return _detect_obstructions(ctx)').body[0])
    detector = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == '_detect_obstructions')
    detector.body = ast.parse('return peak_date.db_conn.execute("SELECT * FROM kala_field")').body
    mutated = ast.unparse(ast.fix_missing_locations(tree))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name.startswith('_Review')]
    test_legacy = ast.ClassDef(name='_LegacyKaVighnakaraWriter', bases=[], keywords=[],
                              body=[legacy.body[-1]], decorator_list=[])
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in {'_review_storage', '_review_storage_callback'}]
    namespace = {}
    executable = ast.fix_missing_locations(ast.Module(body=[detector, test_legacy]+classes+functions,
                                                       type_ignores=[]))
    exec(compile(executable, '<storage helper mutant>', 'exec'), namespace)
    calls = []
    namespace[call.split('(')[0]](SimpleNamespace(db_conn=SimpleNamespace(execute=calls.append)))
    assert calls == ['SELECT * FROM kala_field']
    monkeypatch.setattr(Path, 'read_text',
        lambda path, *args, **kwargs: mutated if path == target else original(path, *args, **kwargs))
    with pytest.raises(AssertionError):
        test_no_downstream_reads_or_multiplier_in_new_path()


def test_only_final_legacy_fallback_is_exempt(monkeypatch):
    target = ROOT/'pipeline/orchestrator/writers/ka_vighnakara.py'
    original = Path.read_text
    source = original(target)
    marker = "        if 'negative_space_fixture_inputs' in ctx.config:"
    assert source.count(marker) == 1
    mutated = source.replace(marker, marker+'\n            super().run(ctx)')
    monkeypatch.setattr(Path, 'read_text',
        lambda path, *args, **kwargs: mutated if path == target else original(path, *args, **kwargs))
    with pytest.raises(AssertionError):
        test_no_downstream_reads_or_multiplier_in_new_path()
