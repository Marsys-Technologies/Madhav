"""Public ephemeris preconditions; compatibility, lock and source boundaries.

The tests execute only the two selected pure helpers against fake Swiss/file
objects. They do not import a writer, invoke Swiss or read ephemeris bytes.
"""
import ast
import copy
from functools import wraps
from inspect import iscoroutinefunction
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import pytest

SIDECAR = Path(__file__).resolve().parents[3] / 'python-sidecar'
OWNER = 'brahmagyan.ephemeris_file_contract'
LEAF = 'brahmagyan/ephemeris_file_contract.py'
WRITERS = {
    'bg_sky_calendar.py': ['_require_swiss_file_backend', '_require_pinned_ephemeris_files'],
    'bg_ephemeris.py': ['_require_swiss_file_backend', '_require_pinned_ephemeris_files'],
    'bg_muhurta_lattice.py': ['_require_pinned_ephemeris_files', '_require_swiss_file_backend'],
}
EXPECTED_OWNER_SHAPES = {'require_swiss_file_backend': 'fd1a5d446e6497153a5c346d2a60c3bec6c17ed827720d2f55ade10453789121', 'require_pinned_ephemeris_files': 'ee7f4b40fd6c9f9ac08e7b14b06eb269350c56d77df65fd0b96e5ae3a892b056'}
EXPECTED_PIN_MAP = '888251c64a70dcc932427f78be63fdfb635faef446a5d76da043ec422e68f891'
EXPECTED_COMPAT_SHAPE = '80826fcba8888f449d6e6a92af382d8d0b4f0de4e465648f705d7f11ef45b6da'

def _shape(node):
    node = copy.deepcopy(node)
    if isinstance(node, ast.FunctionDef) and ast.get_docstring(node):
        node.body.pop(0)
    def project(value):
        if isinstance(value, ast.AST):
            return [type(value).__name__, [[key, project(item)] for key, item in ast.iter_fields(value) if key != 'type_params' or item]]
        if isinstance(value, list):
            return [project(item) for item in value]
        return value
    return hashlib.sha256(json.dumps(project(node), separators=(',', ':')).encode()).hexdigest()

def _functions(text):
    return {node.name: node for node in ast.parse(text).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

def _check_owner(text):
    tree = ast.parse(text)
    expected_imports = {
        ('__future__', 'annotations', None), ('typing', 'Any', None),
        ('panchang_engine.swiss_state', 'serialized_swiss_state', None),
    }
    imports = []
    pins = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.extend((node.module, a.name, a.asname) for a in node.names)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == 'EPHEMERIS_FILE_SHA256':
            pins.append(ast.literal_eval(node.value))
        else:
            assert isinstance(node, ast.FunctionDef) or isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str), 'undeclared owner module effect'
    assert len(imports) == len(expected_imports) and set(imports) == expected_imports, 'owner/bootstrap import changed'
    assert len(pins) == 1 and hashlib.sha256(json.dumps(pins[0], sort_keys=True).encode()).hexdigest() == EXPECTED_PIN_MAP, 'canonical file pins changed'
    functions = _functions(text)
    assert len(functions) == len(EXPECTED_OWNER_SHAPES) and set(functions) == set(EXPECTED_OWNER_SHAPES)
    assert all(_shape(functions[name]) == expected for name, expected in EXPECTED_OWNER_SHAPES.items()), 'backend/file/lock/error contract changed'

def _check_writer(name, text):
    tree = ast.parse(text)
    expected = {
        ('require_swiss_file_backend', '_require_swiss_file_backend'),
        ('require_pinned_ephemeris_files', '_require_pinned_ephemeris_files'),
    }
    if name == 'bg_sky_calendar.py':
        expected = {('EPHEMERIS_FILE_SHA256', None), ('require_swiss_file_backend', '_require_swiss_file_backend'), ('require_pinned_ephemeris_files', None)}
    imports = [(a.name, a.asname) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == OWNER for a in n.names]
    assert len(imports) == len(expected) and set(imports) == expected, 'wrong public precondition owner'
    protected = {'_require_swiss_file_backend', '_require_pinned_ephemeris_files', 'require_pinned_ephemeris_files', 'EPHEMERIS_FILE_SHA256'}
    compat_wrapper = next((node for node in tree.body
                           if isinstance(node, ast.FunctionDef)
                           and node.name == '_require_pinned_ephemeris_files'), None) if name == 'bg_sky_calendar.py' else None
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == 'builtins' or a.name.startswith('builtins.') or a.name == 'importlib' or a.name.startswith('importlib.') for a in node.names), 'indirect import namespace'
        if isinstance(node, ast.ImportFrom):
            assert node.module not in {'builtins', 'importlib'} and not any(a.name == '*' for a in node.names), 'indirect import namespace'
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)):
            targets = node.targets if isinstance(node, (ast.Assign, ast.Delete)) else [node.target]
            assert not any(isinstance(child, ast.Name) and child.id in protected for target in targets for child in ast.walk(target)), 'precondition binding mutation'
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {'__import__', 'eval', 'exec', 'globals', 'locals', 'setattr', 'delattr'}, 'dynamic precondition namespace'
        if isinstance(node, ast.ImportFrom) and node.module == 'pipeline.orchestrator.writers.bg_sky_calendar':
            assert not any(a.name in WRITERS[name] for a in node.names), 'private sibling precondition import'
        if isinstance(node, ast.arg):
            assert node.arg not in protected, 'precondition parameter shadow'
        if isinstance(node, ast.ExceptHandler):
            assert node.name not in protected, 'precondition exception shadow'
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in protected:
            assert node is compat_wrapper and _shape(node) == EXPECTED_COMPAT_SHAPE, 'precondition definition binding shadow'
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            assert node.id != '_require_swiss_file_backend', 'backend alias rebound'
    calls = sorted((n.lineno, n.func.id, [ast.unparse(a) for a in n.args]) for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in WRITERS[name])
    assert [callee for _, callee, args in calls] == WRITERS[name], 'precondition order/count changed'
    assert all(args == (['swe', 'ephe_path'] if callee == '_require_swiss_file_backend' else ['ephe_path']) for _, callee, args in calls), 'precondition inputs changed'
    functions = _functions(text)
    if name == 'bg_sky_calendar.py':
        assert _shape(functions['_require_pinned_ephemeris_files']) == EXPECTED_COMPAT_SHAPE, 'legacy mutable-global adapter changed'
    else:
        assert '_require_pinned_ephemeris_files' not in functions

def test_actual_owner_and_three_writer_interfaces():
    _check_owner((SIDECAR / LEAF).read_text())
    for name in WRITERS:
        _check_writer(name, (SIDECAR / 'pipeline/orchestrator/writers' / name).read_text())

def test_existing_test_locators_follow_actual_owner():
    text = (SIDECAR / 'tests/l0/test_bg_ephemeris_writer_columns.py').read_text()
    calls = [n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'setattr' and len(n.args) >= 2 and isinstance(n.args[0], ast.Name) and n.args[0].id == 'ephemeris_file_contract']
    names = {n.args[1].value for n in calls if isinstance(n.args[1], ast.Constant)}
    assert names == {'require_swiss_file_backend', 'require_pinned_ephemeris_files'}
    tree = ast.parse((SIDECAR / 'tests/test_swiss_state_boundary.py').read_text())
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'EXPECTED_OPERATION_OWNERS' for t in n.targets))
    owners = ast.literal_eval(assignment.value)
    assert ('brahmagyan/ephemeris_file_contract.py', 'require_swiss_file_backend') in owners
    assert ('pipeline/orchestrator/writers/bg_sky_calendar.py', '_require_swiss_file_backend') not in owners

@pytest.mark.parametrize('mutation', ['flags', 'lock', 'pins', 'module_effect', 'foreign_import', 'ignore_supplied_map'])
def test_owner_mutants(mutation):
    text = (SIDECAR / LEAF).read_text()
    if mutation == 'flags':
        text = text.replace('swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED', 'swe.FLG_MOSEPH')
    if mutation == 'lock':
        text = text.replace('@serialized_swiss_state', '')
    if mutation == 'pins':
        text = text.replace('EPHEMERIS_FILE_SHA256:', 'OTHER_PINS:', 1)
    if mutation == 'module_effect':
        text += '\nprint(123)\n'
    if mutation == 'foreign_import':
        text += '\nimport swisseph\n'
    if mutation == 'ignore_supplied_map':
        text = text.replace('EPHEMERIS_FILE_SHA256 if expected_digests is None else expected_digests', 'EPHEMERIS_FILE_SHA256')
    with pytest.raises(AssertionError):
        _check_owner(text)

@pytest.mark.parametrize('name', list(WRITERS))
@pytest.mark.parametrize('mutation', ['wrong_owner', 'wrong_input', 'rebind', 'duplicate_probe', 'builtin_alias', 'code_mutation', 'builtin_from', 'importlib_prefix', 'parameter_shadow'])
def test_writer_owner_input_mutants(name, mutation):
    text = (SIDECAR / 'pipeline/orchestrator/writers' / name).read_text()
    if mutation == 'wrong_owner':
        text = text.replace(OWNER, 'pipeline.orchestrator.writers.bg_sky_calendar')
    if mutation == 'wrong_input':
        text = text.replace('_require_swiss_file_backend(swe, ephe_path)', '_require_swiss_file_backend(swe, other_path)')
    if mutation == 'rebind':
        text += '\n_require_swiss_file_backend = lambda *a: None\n'
    if mutation == 'builtin_alias':
        text += '\nimport builtins as hidden_builtin\nhidden_builtin.__import__("unexpected_module")\n'
    if mutation == 'builtin_from':
        text += '\nfrom builtins import __import__ as hidden_import\n'
    if mutation == 'importlib_prefix':
        text += '\nimport importlib.util as hidden_importlib\n'
    if mutation == 'parameter_shadow':
        text += '\ndef hidden(_require_swiss_file_backend): return None\n'
    if mutation == 'code_mutation':
        text += '\n_require_swiss_file_backend.__code__ = (lambda *args: None).__code__\n'
    if mutation == 'duplicate_probe':
        text += '\ndef _require_swiss_file_backend(swe, ephe_path): pass\n'
    with pytest.raises(AssertionError):
        _check_writer(name, text)

class Lock:
    def __init__(self):
        self.depth = 0
        self.events = []
    def __enter__(self):
        self.depth += 1
        self.events.append('enter')
    def __exit__(self, *args):
        self.events.append('exit')
        self.depth -= 1

class Swiss:
    SIDM_LAHIRI = 1
    SUN = 0
    FLG_SWIEPH = 2
    FLG_MOSEPH = 4
    FLG_SIDEREAL = 64
    FLG_SPEED = 256
    def __init__(self, lock, flags):
        self.lock = lock
        self.flags = flags
        self.calls = []
    def record(self, name, args):
        assert self.lock.depth == 1
        self.calls.append((name, args))
    def set_ephe_path(self, *args):
        self.record('path', args)
    def set_sid_mode(self, *args):
        self.record('mode', args)
    def julday(self, *args):
        self.record('julday', args)
        return 123.0
    def calc_ut(self, *args):
        self.record('calc_ut', args)
        return [0.0] * 6, self.flags

def _load():
    text = (SIDECAR / LEAF).read_text()
    _check_owner(text)
    lock = Lock()
    state = ast.parse((SIDECAR / 'panchang_engine/swiss_state.py').read_text())
    decorator = next(n for n in state.body if isinstance(n, ast.FunctionDef) and n.name == 'serialized_swiss_state')
    functions = list(_functions(text).values())
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    tree = ast.fix_missing_locations(ast.Module(body=[future, decorator] + functions, type_ignores=[]))
    scope = {'SWISS_STATE_LOCK': lock, 'wraps': wraps, 'iscoroutinefunction': iscoroutinefunction}
    exec(compile(tree, '<actual pure helpers with fake state>', 'exec'), scope)
    scope['EPHEMERIS_FILE_SHA256'] = {'fixture.ephe': hashlib.sha256(b'old').hexdigest()}
    return scope, lock

@pytest.mark.parametrize('flags', [0, 2, 4, 6, 322, 326])
def test_backend_real_helper_fake_flags_and_lock(flags):
    scope, lock = _load()
    fake = Swiss(lock, flags)
    method = scope['require_swiss_file_backend']
    assert method.__swiss_state_serialized__ is True and method.__swiss_state_lock__ is lock
    if flags & fake.FLG_SWIEPH and not flags & fake.FLG_MOSEPH:
        method(fake, '/synthetic-only')
    else:
        with pytest.raises(RuntimeError, match='silent Moshier analytic fallback'):
            method(fake, '/synthetic-only')
    assert [name for name, args in fake.calls] == ['path', 'mode', 'julday', 'calc_ut']
    assert fake.calls[-1][1] == (123.0, 0, 322)
    assert lock.events == ['enter', 'exit'] and lock.depth == 0

@pytest.mark.parametrize('kind', ['match', 'mismatch', 'missing', 'ioerror'])
def test_file_real_helper_fake_bytes(kind):
    scope, _ = _load()
    def read(path):
        assert path == Path('/synthetic-only/fixture.ephe')
        if kind == 'missing':
            raise FileNotFoundError('SYNTHETIC_ONLY')
        if kind == 'ioerror':
            raise OSError('SYNTHETIC_ONLY')
        return b'old' if kind == 'match' else b'wrong'
    with patch.object(Path, 'read_bytes', read):
        if kind == 'match':
            scope['require_pinned_ephemeris_files']('/synthetic-only')
        else:
            with pytest.raises(RuntimeError):
                scope['require_pinned_ephemeris_files']('/synthetic-only')

def test_legacy_alias_and_rebound_global_map_compatibility():
    scope, lock = _load()
    writer = (SIDECAR / 'pipeline/orchestrator/writers/bg_sky_calendar.py').read_text()
    compat = _functions(writer)['_require_pinned_ephemeris_files']
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    target = {'require_pinned_ephemeris_files': scope['require_pinned_ephemeris_files'], 'EPHEMERIS_FILE_SHA256': {'fixture.ephe': hashlib.sha256(b'new').hexdigest()}, '_require_swiss_file_backend': scope['require_swiss_file_backend']}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future, compat], type_ignores=[])), '<actual legacy wrapper>', 'exec'), target)
    assert target['_require_swiss_file_backend'] is scope['require_swiss_file_backend']
    assert target['_require_swiss_file_backend'].__swiss_state_lock__ is lock
    with patch.object(Path, 'read_bytes', lambda path: b'new'):
        target['_require_pinned_ephemeris_files']('/synthetic-only')
        target['EPHEMERIS_FILE_SHA256'] = {'fixture.ephe': hashlib.sha256(b'other').hexdigest()}
        with pytest.raises(RuntimeError):
            target['_require_pinned_ephemeris_files']('/synthetic-only')


@pytest.mark.parametrize('name', list(WRITERS))
@pytest.mark.parametrize('alias', ['_require_swiss_file_backend', '_require_pinned_ephemeris_files'])
def test_async_precondition_rebinding_refuses(name, alias):
    text = (SIDECAR / 'pipeline/orchestrator/writers' / name).read_text()
    text += f'\nasync def {alias}(*args, **kwargs): return None\n'
    with pytest.raises(AssertionError):
        _check_writer(name, text)


@pytest.mark.parametrize('name', list(WRITERS))
@pytest.mark.parametrize('kind', ['def', 'async def', 'class'])
def test_nested_file_precondition_definition_refuses(name, kind):
    text = (SIDECAR / 'pipeline/orchestrator/writers' / name).read_text()
    call = '        _require_pinned_ephemeris_files(ephe_path)'
    assert text.splitlines().count(call) == 1
    definition = (f'        {kind} _require_pinned_ephemeris_files(*args, **kwargs):\n            pass\n'
                  if kind != 'class' else
                  '        class _require_pinned_ephemeris_files:\n            def __init__(self, *args, **kwargs): pass\n')
    with pytest.raises(AssertionError):
        _check_writer(name, text.replace(call, definition + call, 1))


@pytest.mark.parametrize('kind', ['def', 'async def', 'class'])
def test_sky_public_file_validator_definition_refuses(kind):
    text = (SIDECAR / 'pipeline/orchestrator/writers/bg_sky_calendar.py').read_text()
    definition = (f'\n{kind} require_pinned_ephemeris_files(*args, **kwargs):\n    pass\n'
                  if kind != 'class' else
                  '\nclass require_pinned_ephemeris_files:\n    def __init__(self, *args, **kwargs): pass\n')
    with pytest.raises(AssertionError):
        _check_writer('bg_sky_calendar.py', text + definition)


def test_only_single_exact_top_level_sky_compat_wrapper_is_allowed():
    text = (SIDECAR / 'pipeline/orchestrator/writers/bg_sky_calendar.py').read_text()
    _check_writer('bg_sky_calendar.py', text)
    tree = ast.parse(text)
    wrapper = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == '_require_pinned_ephemeris_files')
    with pytest.raises(AssertionError):
        _check_writer('bg_sky_calendar.py', text + '\n' + ast.get_source_segment(text, wrapper) + '\n')
