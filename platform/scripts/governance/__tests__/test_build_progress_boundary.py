"""Build owns the reviewed Sangam/Kshetra progress SQL on borrowed contexts.

These source/trace controls complement retained disposable-PG evidence. They do
not prove arbitrary dynamic SQL, installed roles or full runtime discovery.
"""
import ast
import hashlib
import json
from pathlib import Path
import pytest
SIDECAR = Path(__file__).resolve().parents[3] / 'python-sidecar'
EXPECTED = {'pipeline/orchestrator/substep_progress.py': {'load_sangam_completed_substeps': '256e9a1d85f2074da0573870670f65876cda2d3313930ba3a20c2c5ce9d6f8b2',
                                               'sum_sangam_rows_written': '746c165cdf23a190cdf5f12dc6b8b628e669912ffee0623efae5398a708d85a3',
                                               'clear_sangam_substeps': 'c972f962f118d335441644c4c7f9457419c2d86bd5be92666a6775d3517562e9',
                                               'record_sangam_substep': '6ec08d6cb86fe563adc33bd8e16e5450d21b65abf56285b846d248789daf5cb8'},
 'pipeline/orchestrator/substep_progress_kshetra.py': {'_progress_rows': 'a3b85381b3fbf092e5b958d0e4f1b6268d3d28497ff32e1c20b3119cf3aa907b',
                                                       'list_substep_keys': '5e4dbe94012560e8e6de8ea32a2e460634875507906627a1462bfb3c4b02eec7',
                                                       'list_substep_fingerprints': '9d87a228c79d3a0fc88c639d9f3dd185b3fb266d35914b7380a24b7c5dad5fa5',
                                                       'delete_substep_progress': '84e3afb71ea0a17ff6eb86dd3acbd52363cd54ed7d8b4d578091599ddc2fcd2a',
                                                       'upsert_substep_progress': 'd1850966615695f09c8336e1f3ad8b1bf1efcffb2b7cc38119a09641dbceabda'}}
DOMAINS = {'pipeline/orchestrator/writers/ka_sangam.py': ('pipeline.orchestrator.substep_progress',
                                                ['clear_sangam_substeps',
                                                 'load_sangam_completed_substeps',
                                                 'record_sangam_substep',
                                                 'sum_sangam_rows_written']),
 'services/ka_kshetra/writer.py': ('pipeline.orchestrator.substep_progress_kshetra',
                                   ['delete_substep_progress',
                                    'list_substep_fingerprints',
                                    'list_substep_keys',
                                    'upsert_substep_progress'])}
CALLS = {'pipeline/orchestrator/writers/ka_sangam.py': [('_LegacyKaSangamWriter.plan_substeps',
                                                 'sum_sangam_rows_written(conn, chart_id)'),
                                                ('_LegacyKaSangamWriter.run_substep',
                                                 'clear_sangam_substeps(cur, chart_id)'),
                                                ('_LegacyKaSangamWriter._load_completed_substeps',
                                                 'load_sangam_completed_substeps(conn, chart_id, '
                                                 'fingerprint)'),
                                                ('_LegacyKaSangamWriter._record_substep',
                                                 'record_sangam_substep(conn, chart_id, '
                                                 'substep_key, self._resume_fingerprint, rows)')],
 'services/ka_kshetra/writer.py': [('KaKshetraWriter._bind_preparation',
                                    'list_substep_keys(cur, chart_id=self._chart_id, '
                                    'asset_id=ASSET_ID)'),
                                   ('KaKshetraWriter._delete_prior_rows',
                                    'delete_substep_progress(cur, chart_id=chart_id, '
                                    'asset_id=ASSET_ID)'),
                                   ('KaKshetraWriter._load_completed_substeps',
                                    'list_substep_fingerprints(cur, chart_id=chart_id, '
                                    'asset_id=ASSET_ID)'),
                                   ('KaKshetraWriter._record_substep',
                                    'upsert_substep_progress(cur, chart_id=self._chart_id, '
                                    'asset_id=ASSET_ID, substep_key=substep_key, '
                                    'build_fingerprint=self._fingerprint(), rows_written=rows)')]}

RETAINED_DYNAMIC_CALLS = [('KaKshetraWriter._optional_stage_plugins', '__import__(module_name, fromlist=[attr])'),
 ('KaKshetraWriter._run_plugin_substep', "__import__(module_name, fromlist=['run_substep'])")]

def _project(value):
    """Keep semantic AST fields; normalize empty Python-version additions."""
    if isinstance(value, ast.AST):
        return [type(value).__name__, [[key, _project(item)] for key, item in ast.iter_fields(value) if key != 'type_params' or item]]
    if isinstance(value, list):
        return [_project(item) for item in value]
    return value

def _shape(fn):
    if fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant) and isinstance(fn.body[0].value.value, str):
        fn.body.pop(0)
    return hashlib.sha256(json.dumps(_project(fn), separators=(',', ':')).encode()).hexdigest()

def _check_helper(text, expected):
    tree = ast.parse(text)
    assert all((isinstance(n, ast.FunctionDef) or (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)) for n in tree.body)), 'Build progress helper has undeclared module effects/imports'
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    assert len(functions) == len(expected) and {n.name for n in functions} == set(expected), 'Build progress interface changed'
    assert all((_shape(n) == expected[n.name] for n in functions)), 'SQL/order/binds/row adaptation/borrow contract changed'

def _static_text(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _static_text(node.left) + _static_text(node.right)
    if isinstance(node, ast.JoinedStr):
        return ''.join((_static_text(n) for n in node.values))
    return ''

def _check_domain(text, owner, names, expected_calls):
    tree = ast.parse(text)
    bindings = []
    parents = {id(child): parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in names:
            parent = parents[id(n)]
            assert isinstance(parent, ast.Call) and parent.func is n, 'Build callable escaped direct invocation'
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)):
            targets = n.targets if isinstance(n, (ast.Assign, ast.Delete)) else [n.target]
            assert not any(isinstance(child, ast.Name) and child.id in names for target in targets for child in ast.walk(target)), 'Build callable attribute mutation'

        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                bound = a.asname or (a.name.split('.')[0] if isinstance(n, ast.Import) else a.name)
                if isinstance(n, ast.ImportFrom) and n.module == owner:
                    assert a.name in names and a.asname is None, 'undeclared Build progress alias'
                if isinstance(n, ast.Import):
                    assert a.name != owner, 'indirect Build module import'
                if bound in names:
                    bindings.append((getattr(n, 'module', None), getattr(n, 'level', 0), a.name, a.asname))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            assert n.func.attr not in {'commit', 'rollback', 'close'}, 'domain borrower ended a transaction or connection'
        if isinstance(n, ast.Attribute) and isinstance(n.ctx, (ast.Store, ast.Del)):
            assert n.attr != 'autocommit', 'domain borrower changed transaction mode'
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            assert n.id not in names, 'Build interface rebound'
        if isinstance(n, ast.Import):
            assert not any((a.name == 'importlib' or a.name.startswith('importlib.') or a.name == 'builtins' or a.name.startswith('builtins.') for a in n.names)), 'dynamic progress import'
        if isinstance(n, ast.ImportFrom):
            assert n.module not in ('importlib', 'builtins') and (not any((a.name == '*' for a in n.names))), 'dynamic progress binding'
        if isinstance(n, ast.Name):
            assert n.id not in ('__builtins__', 'eval', 'exec', 'globals', 'locals', 'setattr', 'delattr'), 'dynamic progress namespace'
        if isinstance(n, ast.ExceptHandler):
            assert n.name not in names, 'Build interface exception shadow'
        if isinstance(n, ast.arg):
            assert n.arg not in names, 'Build interface parameter shadow'
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            assert n.name not in names, 'Build interface redefined'
        if isinstance(n, (ast.BinOp, ast.JoinedStr, ast.Constant)):
            sql = _static_text(n).upper()
            if 'BUILD_SUBSTEP_PROGRESS' in sql:
                assert not any((op in sql for op in ('SELECT ', 'DELETE ', 'INSERT ', 'UPDATE '))), 'domain writer owns progress SQL again'
    assert sorted(bindings) == sorted(((owner, 0, name, None) for name in names)), 'wrong Build progress owner/import'
    calls = []
    dynamic_calls = []

    def walk(n, scope):
        if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            scope = scope + [n.name]
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and (n.func.id in names):
            calls.append(('.'.join(scope), ast.unparse(n)))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == '__import__':
            dynamic_calls.append(('.'.join(scope), ast.unparse(n)))
        for child in ast.iter_child_nodes(n):
            walk(child, scope)
    walk(tree, [])
    # Retain the two reviewed domain-loader call sites. Their transitive
    # module_name/attr targets need separate dynamic-discovery qualification.
    allowed_dynamic = RETAINED_DYNAMIC_CALLS if owner.endswith('_kshetra') else []
    assert sorted(dynamic_calls) == sorted(allowed_dynamic), 'unreviewed dynamic import call site'
    assert sorted(calls) == sorted((tuple(row) for row in expected_calls)), 'borrowed cursor, selector or fingerprint binding changed'
    if 'ASSET_ID' in text and owner.endswith('_kshetra'):
        values = [n.value for n in ast.walk(tree) if isinstance(n, ast.Assign) and any((isinstance(t, ast.Name) and t.id == 'ASSET_ID' for t in n.targets))]
        assert len(values) == 1 and isinstance(values[0], ast.Constant) and (values[0].value == 'ka_kshetra'), 'Kshetra asset namespace changed'

def test_actual_build_owned_helpers():
    for path, expected in EXPECTED.items():
        _check_helper((SIDECAR / path).read_text(), expected)

def test_actual_domain_callers():
    for path, (owner, names) in DOMAINS.items():
        _check_domain((SIDECAR / path).read_text(), owner, names, CALLS[path])

@pytest.mark.parametrize('mutation', ['commit', 'close', 'autocommit', 'wrong_selector', 'wrong_sql_owner', 'wrong_function', 'top_level_effect', 'duplicate_function'])
def test_helper_transaction_and_SQL_mutants(mutation):
    path = 'pipeline/orchestrator/substep_progress.py'
    text = (SIDECAR / path).read_text()
    if mutation == 'commit':
        text = text.replace('with conn.cursor() as cur:', 'conn.commit()\n    with conn.cursor() as cur:', 1)
    if mutation == 'close':
        text = text.replace('with conn.cursor() as cur:', 'conn.close()\n    with conn.cursor() as cur:', 1)
    if mutation == 'autocommit':
        text = text.replace('with conn.cursor() as cur:', 'conn.autocommit=True\n    with conn.cursor() as cur:', 1)
    if mutation == 'wrong_selector':
        text = text.replace("asset_id = 'ka_sangam'", "asset_id = 'other'", 1)
    if mutation == 'wrong_sql_owner':
        text = text.replace('build_substep_progress', 'other_progress')
    if mutation == 'wrong_function':
        text = text.replace('def clear_sangam_substeps', 'def generic_clear')
    if mutation == 'top_level_effect':
        text += '\nprint(123)\n'
    if mutation == 'duplicate_function':
        text += '\ndef clear_sangam_substeps(cur, chart_id):pass\n'
    with pytest.raises(AssertionError):
        _check_helper(text, EXPECTED[path])

@pytest.mark.parametrize('mutation', ['wrongowner', 'rebind', 'cursor', 'fingerprint', 'direct_sql', 'constructed_sql', 'asset', 'alias', 'dynamic', 'shadow', 'exception_shadow', 'dynamic_builtin', 'commit', 'rollback', 'close', 'autocommit'])
def test_domain_owner_and_selector_mutants(mutation):
    path = 'services/ka_kshetra/writer.py'
    owner, names = DOMAINS[path]
    text = (SIDECAR / path).read_text()
    if mutation in {'commit', 'rollback', 'close'}:
        text += f'\ndef hidden(conn):conn.{mutation}()\n'
    if mutation == 'autocommit':
        text += '\ndef hidden(conn):conn.autocommit=True\n'
    if mutation == 'wrongowner':
        text = text.replace(owner, 'services.ka_kshetra.progress')
    if mutation == 'rebind':
        text += '\nlist_substep_keys=lambda *a,**k: []\n'
    if mutation == 'cursor':
        text = text.replace('list_substep_keys(cur,', 'list_substep_keys(other_cur,', 1)
    if mutation == 'fingerprint':
        text = text.replace('build_fingerprint=self._fingerprint()', "build_fingerprint='wrong'", 1)
    if mutation == 'direct_sql':
        text += "\ndef hidden(cur):cur.execute('DELETE FROM build_substep_progress')\n"
    if mutation == 'constructed_sql':
        text += "\ndef hidden(cur):cur.execute('DELETE FROM build_substep_'+'progress')\n"
    if mutation == 'asset':
        text = text.replace("ASSET_ID = 'ka_kshetra'", "ASSET_ID = 'other'", 1)
    if mutation == 'alias':
        text += f'\nfrom {owner} import list_substep_keys as hidden_progress\n'
    if mutation == 'dynamic':
        text += '\nimport importlib\n'
    if mutation == 'dynamic_builtin':
        text += "\n__import__('pipeline.orchestrator.substep_progress_kshetra')\n"
    if mutation == 'shadow':
        text += '\ndef hidden(list_substep_keys):return list_substep_keys(None)\n'
    if mutation == 'exception_shadow':
        text += '\ntry:pass\nexcept Exception as list_substep_keys:pass\n'
    assert text != (SIDECAR / path).read_text(), 'causal mutation did not change source'
    with pytest.raises(AssertionError):
        _check_domain(text, owner, names, CALLS[path])

class Cursor:

    def __init__(self, rows=(), one=None, columns=()):
        self.rows = list(rows)
        self.one = one
        self.description = [(x,) for x in columns]
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params):
        self.statements.append((sql, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.one

class Connection:

    def __init__(self, cur):
        self.cur = cur
        self.cursor_calls = 0

    def cursor(self):
        self.cursor_calls += 1
        return self.cur

    def commit(self):
        raise AssertionError('borrower committed')

    def rollback(self):
        raise AssertionError('borrower rolled back')

    def close(self):
        raise AssertionError('borrower closed connection')

def _load(path):
    text = (SIDECAR / path).read_text()
    _check_helper(text, EXPECTED[path])
    scope = {}
    exec(compile(text, '<reviewed Build helper>', 'exec'), scope)
    return scope

@pytest.mark.parametrize('rows,expected', [([], None), ([{'substep_key': 'step', 'build_fingerprint': 'fp'}], {'step'}), ([{'substep_key': 'step', 'build_fingerprint': 'old'}], None)])
def test_sangam_resume_and_borrowed_context(rows, expected):
    funcs = _load('pipeline/orchestrator/substep_progress.py')
    cur = Cursor(rows=rows)
    conn = Connection(cur)
    assert funcs['load_sangam_completed_substeps'](conn, 'synthetic-chart', 'fp') == expected
    assert cur.statements[0][1] == ('synthetic-chart',) and "asset_id = 'ka_sangam'" in cur.statements[0][0]

@pytest.mark.parametrize('row,expected', [({'n': 4}, 4), ((5,), 5), ({'n': None}, 0), ((None,), 0)])
def test_sangam_sum_and_record(row, expected):
    funcs = _load('pipeline/orchestrator/substep_progress.py')
    cur = Cursor(one=row)
    conn = Connection(cur)
    assert funcs['sum_sangam_rows_written'](conn, 'synthetic-chart') == expected
    funcs['record_sangam_substep'](conn, 'synthetic-chart', 'step', 'fp', 2)
    assert cur.statements[-1][1] == ('synthetic-chart', 'step', 'fp', 2)
    funcs['clear_sangam_substeps'](cur, 'synthetic-chart')
    assert cur.statements[-1][1] == ('synthetic-chart',)

@pytest.mark.parametrize('tuple_rows', [False, True])
def test_kshetra_row_adaptation_and_supplied_cursor(tuple_rows):
    funcs = _load('pipeline/orchestrator/substep_progress_kshetra.py')
    rows = [('step', 'fp')] if tuple_rows else [{'substep_key': 'step', 'build_fingerprint': 'fp'}]
    cur = Cursor(rows=rows, columns=('substep_key', 'build_fingerprint'))
    assert funcs['list_substep_keys'](cur, chart_id='synthetic-chart', asset_id='ka_kshetra') == ['step']
    assert funcs['list_substep_fingerprints'](cur, chart_id='synthetic-chart', asset_id='ka_kshetra') == [('step', 'fp')]
    funcs['delete_substep_progress'](cur, chart_id='synthetic-chart', asset_id='ka_kshetra')
    funcs['upsert_substep_progress'](cur, chart_id='synthetic-chart', asset_id='ka_kshetra', substep_key='step', build_fingerprint='fp', rows_written=3)
    assert len(cur.statements) == 4 and all((p[:2] == ('synthetic-chart', 'ka_kshetra') for q, p in cur.statements))
    assert cur.statements[-1][1] == ('synthetic-chart', 'ka_kshetra', 'step', 'fp', 3)

def test_helper_comment_and_docstring_compatibility():
    path = 'pipeline/orchestrator/substep_progress.py'
    text = (SIDECAR / path).read_text()
    _check_helper('"""Review annotation."""\n' + text + '\n# unrelated formatting\n', EXPECTED[path])

@pytest.mark.parametrize('append', [
    "\nimport builtins as hidden_builtin\nhidden_builtin.__import__('pipeline.orchestrator.substep_progress_kshetra')\n",
    "\nfrom builtins import __import__ as hidden_import\n",
    "\n__builtins__['__import__']('pipeline.orchestrator.substep_progress_kshetra')\n",
    "\nlist_substep_keys.__code__ = (lambda *args, **kwargs: []).__code__\n",
    "\nlist_substep_keys.__defaults__ = ()\n",
    "\nprogress_alias = list_substep_keys\nprogress_alias.__code__ = (lambda *args, **kwargs: []).__code__\n",
    "\nprogress_alias = list_substep_keys\n",
])
def test_actual_domain_indirect_import_and_attribute_mutants(append):
    path = 'services/ka_kshetra/writer.py'
    text = (SIDECAR / path).read_text()
    owner, names = DOMAINS[path]
    _check_domain(text, owner, names, CALLS[path])
    with pytest.raises(AssertionError):
        _check_domain(text + append, owner, names, CALLS[path])


def test_actual_async_binding_redefinition_refuses():
    path = 'services/ka_kshetra/writer.py'
    text = (SIDECAR / path).read_text()
    owner, names = DOMAINS[path]
    _check_domain(text, owner, names, CALLS[path])
    changed = text + "\nasync def list_substep_keys(*args, **kwargs): return []\n"
    with pytest.raises(AssertionError):
        _check_domain(changed, owner, names, CALLS[path])
