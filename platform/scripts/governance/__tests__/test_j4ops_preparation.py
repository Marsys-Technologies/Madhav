"""J4OPS preparation is immutable, phase-specific and never earns operation acceptance.

Automatically collected by governance ci_shard.py. No DB, cloud or credentials.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
BUNDLE = ROOT / 'platform/scripts/j4ops'


def load(name):
    spec = importlib.util.spec_from_file_location(name, BUNDLE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def prepare():
    return load('prepare')


@pytest.fixture
def packet_request(tmp_path, prepare):
    item = 'J-4a-a25'
    inputs = {}
    for name in prepare.declarations()['items'][item]['required_inputs']:
        path = tmp_path / (name + '.json')
        path.write_text('{}\n')  # opaque binding-only fixture; never acceptance evidence
        inputs[name] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'schema': 'ky.j4ops_preparation_request/1', 'item': item, 'phase': 6,
            'operation_id': 'OP-J4A-fixture', 'request_id': 'REQ-J4A-fixture',
            'reviewed_commit': 'a' * 40, 'chart_id': '482012f1-710e-4a25-994a-93821f5871aa',
            'generation': '4.1', 'enabled': False, 'inputs': inputs}


def test_three_phase_specific_declarations_are_disabled_and_executable(prepare):
    entries = prepare.declarations()['items']
    assert set(entries) == {'J-4a-a25', 'J-4b-a55j', 'J-4c-a55m'}
    assert [v['phase'] for v in entries.values()] == [6, 7, 8]
    for item, entry in entries.items():
        assert entry['enabled'] is False
        assert entry['executor_entry']['enabled'] is False
        assert entry['executor_entry']['enabled_by'] == item
        assert (ROOT / entry['executor_entry']['script']).is_file()
        assert entry['executor_entry']['fixed_args'] == ['--item', item]
        assert entry['executor_entry']['allowed_args'] == ['request-file', 'request-sha256']


def test_binding_hashes_complete_request_and_input_bytes_without_claiming_acceptance(prepare, packet_request):
    proof = prepare.bind(packet_request)
    assert proof['request_sha256'] == prepare.digest(packet_request)
    assert proof['status'] == 'PREPARATION_ONLY'
    assert proof['enabled'] is False
    assert proof['dry_run_passed'] is False
    assert proof['operation_completed'] is False
    assert proof['inputs'] == packet_request['inputs']
    assert proof['runner_sha256'] == hashlib.sha256((BUNDLE / 'prepare.py').read_bytes()).hexdigest()


@pytest.mark.parametrize('key,value', [('phase', 7), ('generation', '5.0'), ('enabled', True),
    ('chart_id', '482012f1-710e-4a25-994a-93821f5871ab'), ('reviewed_commit', 'main'),
    ('request_id', ''), ('operation_id', '../x'), ('unexpected', True)])
def test_wrong_or_extra_request_fields_refuse(prepare, packet_request, key, value):
    packet_request[key] = value
    with pytest.raises(ValueError):
        prepare.bind(packet_request)


def test_missing_extra_changed_or_empty_input_refuses(prepare, packet_request):
    for mode in ('missing', 'extra', 'changed', 'empty'):
        changed = copy.deepcopy(packet_request)
        name = next(iter(changed['inputs']))
        if mode == 'missing':
            del changed['inputs'][name]
        elif mode == 'extra':
            changed['inputs']['invented'] = changed['inputs'][name]
        elif mode == 'changed':
            changed['inputs'][name]['sha256'] = '0' * 64
        else:
            Path(changed['inputs'][name]['path']).write_bytes(b'')
        with pytest.raises(ValueError):
            prepare.bind(changed)


def test_raw_request_digest_is_checked_before_json_and_duplicate_keys_refuse(prepare, tmp_path):
    path = tmp_path / 'request.json'
    path.write_text('{"item":"J-4a-a25","item":"J-4b-a55j"}')
    with pytest.raises(ValueError, match='digest'):
        prepare.read_bound(path, '0' * 64)
    with pytest.raises(ValueError, match='duplicate'):
        prepare.read_bound(path, hashlib.sha256(path.read_bytes()).hexdigest())


def test_declaration_tamper_refuses_before_binding(prepare, packet_request, tmp_path, monkeypatch):
    path = tmp_path / 'declarations.json'
    path.write_text((BUNDLE / 'operations.json').read_text().replace('"enabled": false', '"enabled": true', 1))
    monkeypatch.setattr(prepare, 'DECLARATIONS', path)
    with pytest.raises(ValueError, match='digest'):
        prepare.bind(packet_request)


def test_cli_requires_expected_item_and_never_supports_execute(prepare, packet_request, tmp_path):
    path = tmp_path / 'request.json'
    path.write_text(json.dumps(packet_request))
    args = [sys.executable, '-B', str(BUNDLE / 'prepare.py'), '--item', packet_request['item'],
            '--request-file', str(path), '--request-sha256', hashlib.sha256(path.read_bytes()).hexdigest()]
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['operation_completed'] is False
    for tail in (['--execute'], ['--item', 'J-4b-a55j']):
        refused = subprocess.run(args + tail, capture_output=True, text=True)
        assert refused.returncode != 0
        assert not refused.stdout


def test_grant_matrix_requires_every_cell_and_checks_column_writes():
    rb = load('readback')
    cells = []
    for role in ('gochara_verifier', 'gochara_sealer'):
        for table in ('chart_facts', 'chart_dashas'):
            for privilege in rb.PRIVILEGES:
                cells.append({'role': role, 'table': table, 'privilege': privilege,
                              'present': privilege == 'SELECT'})
    for table in rb.VERIFICATION_TABLES:
        for privilege in rb.WRITE_PRIVILEGES:
            cells.append({'role': 'data_plane_builder', 'table': table, 'privilege': privilege, 'present': False})
    assert rb.grant_problems(cells) == []
    assert rb.grant_problems(cells[:-1])
    assert rb.grant_problems(cells + cells[:1])
    changed = copy.deepcopy(cells)
    changed[1]['present'] = True
    assert rb.grant_problems(changed)
    changed[0]['present'] = None
    assert rb.grant_problems(changed)


def test_sql_bundle_is_pinned_and_meta_commands_or_tamper_refuse(tmp_path):
    rb = load('readback')
    for name in ('provision.sql', 'second_window.sql'):
        sql = rb.sql_bytes(name)
        assert b'has_any_column_privilege' in sql or name == 'second_window.sql'
        assert not any(line.lstrip().startswith(b'\\') for line in sql.splitlines())
    path = tmp_path / 'sql'
    path.mkdir()
    (path / 'provision.sql').write_text('SELECT true;\n')
    with pytest.raises(ValueError, match='digest'):
        rb.sql_bytes('provision.sql', directory=path)


def test_second_window_requires_exact_pinned_ledger_functions_triggers_and_no_dormant_writes():
    rb = load('readback')
    capture = {'server_major': 16, 'ledger': [{'filename': 'fixture.sql', 'sha256': 'a' * 64}],
               'functions': [{'signature': 'public.fixture()', 'definition': 'fixture definition'}],
               'triggers': [{'table': 'fixture', 'name': 'fixture', 'enabled': 'O', 'definition': 'fixture trigger'}],
               'dormant_writes': [], 'app_schema_create': False}
    expected = copy.deepcopy(capture)
    assert rb.window_problems(capture, expected) == []
    for field in capture:
        broken = copy.deepcopy(capture)
        broken[field] = (17 if field == 'server_major' else True if field == 'app_schema_create' else [])
        if broken == capture:
            broken[field] = [{'unexpected': True}]
        assert rb.window_problems(broken, expected), field
    for field in ('ledger', 'functions', 'triggers'):
        broken = copy.deepcopy(expected)
        broken[field] = []
        with pytest.raises(ValueError):
            rb.window_problems(capture, broken)


def test_runner_forces_readonly_and_checks_identity_before_using_capture():
    rb = load('readback')
    env = rb.readonly_environment({'PGOPTIONS': '-c statement_timeout=0', 'PGHOST': 'fixture'})
    assert env['PGOPTIONS'].endswith('-c default_transaction_read_only=on -c statement_timeout=840000')
    identity = {'current_database': 'fixture', 'transaction_read_only': 'on', 'default_transaction_read_only': 'on'}
    rb.check_identity(identity, 'fixture')
    for key in identity:
        broken = dict(identity, **{key: 'wrong'})
        with pytest.raises(ValueError):
            rb.check_identity(broken, 'fixture')


def test_ephemeris_block_no_longer_demands_unused_auxiliaries_and_probes_true_node():
    shell = (ROOT / 'platform/python-sidecar/scripts/kala_gochara_cutover/century_run_4_1.sh').read_text()
    block = shell.split("python - <<'PYEOF'\n", 1)[1].split('\nPYEOF', 1)[0]
    assert 'SIZE_FLOORS' not in block
    assert 'swe.TRUE_NODE' in block  # Moon retflag alone can mask a missing lunar file.
    assert 'FLG_MOSEPH' in block and 'retflag & swe.FLG_SWIEPH' in block
    assert '1998, 1, 1' in block and '2026, 4, 18' in block
    assert 'sha256' in block and len(__import__('re').findall(r'"[0-9a-f]{64}"', block)) == 3


def test_new_tests_are_in_existing_ci_pattern_discovery():
    spec = importlib.util.spec_from_file_location('j4ops_ci_shard', ROOT / 'platform/scripts/governance/ci_shard.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert Path(__file__).resolve() in module.test_files()


def test_declarations_preserve_original_dependency_edges_and_historical_prerequisites(prepare):
    model = json.loads((ROOT / '00_ARCHITECTURE/control/kalayantra/plan_model.json').read_text())
    items = {item['id']: item for item in model['items']}
    inherited = {'J-4a-a25': ['detector:db_query'], 'J-4b-a55j': ['A5.5e'], 'J-4c-a55m': ['A5.5e', 'A5.5l']}
    for item, declaration in prepare.declarations()['items'].items():
        assert declaration['depends_on'] == items[item]['depends_on']
        assert declaration['inherited_prerequisites'] == inherited[item]
    # Preparation does not silently become an operational dependency/step.
    assert all('op' not in items[item]['brief'] for item in inherited)


def test_all_three_disabled_preparation_entries_bind_their_exact_scope(prepare, packet_request, tmp_path):
    for item, declaration in prepare.declarations()['items'].items():
        changed = copy.deepcopy(packet_request)
        changed.update(item=item, phase=declaration['phase'], generation=declaration['generation'], inputs={})
        for name in declaration['required_inputs']:
            path = tmp_path / (name + '.input')
            path.write_bytes(b'opaque unit binding fixture\n')
            changed['inputs'][name] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        assert prepare.bind(changed)['item'] == item
        changed['enabled'] = True
        with pytest.raises(ValueError):
            prepare.bind(changed)


def test_snapshot_transport_is_one_readonly_session_and_refuses_identity_drift():
    rb = load('readback')
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        identity = {'current_database': 'fixture', 'transaction_read_only': 'on', 'default_transaction_read_only': 'on'}
        return subprocess.CompletedProcess(argv, 0, json.dumps(identity) + '\n[]\n', '')
    identity, data, raw = rb.capture('provision', 'fixture', runner=run, environ={})
    assert data == [] and raw
    assert len(calls) == 1
    argv, options = calls[0]
    assert argv == ['psql', '-X', '-q', '-t', '-A', '-v', 'ON_ERROR_STOP=1']
    assert options['input'].startswith('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;')
    assert options['input'].endswith('ROLLBACK;\n')
    assert options['timeout'] == 900
    with pytest.raises(ValueError, match='identity'):
        rb.capture('provision', 'another', runner=run, environ={})


def test_self_hash_and_second_window_expectations_refuse_before_any_connection(tmp_path, monkeypatch):
    rb = load('readback')
    def must_not_connect(*_args, **_kwargs):
        pytest.fail('invalid preparation reached the connection boundary')
    monkeypatch.setattr(rb, 'capture', must_not_connect)
    args = ['--phase', 'provision', '--expect-db', 'fixture', '--out', str(tmp_path / 'out'),
            '--runner-sha256', '0' * 64]
    assert rb.main(args) == 2
    args = ['--phase', 'second-window', '--expect-db', 'fixture', '--out', str(tmp_path / 'out'),
            '--runner-sha256', hashlib.sha256((BUNDLE / 'readback.py').read_bytes()).hexdigest()]
    assert rb.main(args) == 2
    assert not (tmp_path / 'out').exists()


def test_db_and_ephemeris_suites_run_by_glob_in_the_required_db_job():
    workflow = (ROOT / '.github/workflows/ci.yml').read_text()
    step = workflow.split('      - name: Pravāha A5.3 — migration 1240 / 1233 live-DB suites', 1)[1].split('\n      - name:', 1)[0]
    assert "GOCHARA_A53_REQUIRE_DB: '1'" in step
    assert 'export GOCHARA_SE1_REQUIRE=1' in step
    # The suites run through the sharded discovery profile of this very step, from the sidecar directory.
    assert 'ci_discovery.py" pytest db-integration-tests-9-12 --' in step
    assert {p.name for p in (ROOT / 'platform/python-sidecar/tests/l3/gochara').glob('test_j4ops_*.py')} == {
        'test_j4ops_readback_db.py', 'test_j4ops_ephemeris_preflight.py'}
    sys.path.insert(0, str(ROOT / 'platform/scripts/governance'))
    import ci_discovery
    selected = ci_discovery.discover(ROOT, ci_discovery.profiles()['db-integration-tests-9-12'])
    assert {'tests/l3/gochara/test_j4ops_readback_db.py', 'tests/l3/gochara/test_j4ops_ephemeris_preflight.py'} <= set(selected)


def test_existing_db_discovery_expands_the_workflow_glob_and_detects_a_dropped_selection():
    spec = importlib.util.spec_from_file_location('j4ops_existing_ci_guard', ROOT / 'platform/scripts/governance/__tests__/test_ci_changes.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    command = 'python -B -m pytest tests/l3/gochara/test_j4ops_*.py -q -p no:cacheprovider'
    assert set(module._pytest_suites(command)) == {
        'tests/l3/gochara/test_j4ops_readback_db.py', 'tests/l3/gochara/test_j4ops_ephemeris_preflight.py'}
    assert module._pytest_suites(command.replace('test_j4ops_*', 'test_j4ops_no_such_suite_*')) == []
    assert module._pytest_suites('# ' + command) == []
