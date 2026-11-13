"""Reviewed Mīmāṃsā signal-family interface; source-only synthetic boundary controls."""
import ast
import hashlib
import json
from pathlib import Path
import pytest
SIDECAR = Path(__file__).resolve().parents[3] / 'python-sidecar'
OWNER = 'services.mimamsa.signal_family'
EXPECTED_FUNCTION_SHAPE = '30f7aa3c72fc6df418b4390d384b81f7ccef8fe7653933ce85388b272b771833'

def _shape(node):
    """Bind reviewed computation independently of source lines and comments."""

    def project(value):
        if isinstance(value, ast.AST):
            return [type(value).__name__, [[key, project(item)] for key, item in ast.iter_fields(value) if key != 'type_params' or item]]
        if isinstance(value, list):
            return [project(item) for item in value]
        return value
    return hashlib.sha256(json.dumps(project(node), separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()

def _check_writer(text):
    tree = ast.parse(text)
    bindings = [(getattr(n, 'module', None), getattr(n, 'level', 0), a.name, a.asname) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names if (a.asname or (a.name.split('.')[0] if isinstance(n, ast.Import) else a.name)) == '_signal_family_key']
    assert bindings == [(OWNER, 0, 'signal_family_key', '_signal_family_key')], 'signal family binding must use its domain public interface'
    assert not any((isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == '_signal_family_key' or (isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)) and (n.id == '_signal_family_key')) for n in ast.walk(tree))), 'shared binding was replaced'
    parents = {id(child): parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == '_signal_family_key':
            parent = parents[id(node)]
            # Current consumers invoke the imported callable directly; copying
            # it elsewhere is an unreviewed mutable interface escape.
            assert isinstance(parent, ast.Call) and parent.func is node, 'shared callable escaped direct invocation'
        if isinstance(node, ast.Import):
            assert not any((a.name == 'importlib' or a.name.startswith('importlib.') or a.name == 'builtins' or a.name.startswith('builtins.') for a in node.names)), 'dynamic family import'
        if isinstance(node, ast.ImportFrom):
            assert node.module not in ('importlib', 'builtins') and (not any((a.name == '*' for a in node.names))), 'indirect builtin or wildcard import'
        if isinstance(node, ast.arg):
            assert node.arg != '_signal_family_key', 'shared callable parameter shadow'
        if isinstance(node, ast.ExceptHandler):
            assert node.name != '_signal_family_key', 'shared callable exception shadow'
        if isinstance(node, ast.Name):
            assert node.id not in ('__import__', '__builtins__', 'eval', 'exec', 'globals', 'locals', 'setattr', 'delattr'), 'dynamic namespace mutation'
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)):
            targets = node.targets if isinstance(node, (ast.Assign, ast.Delete)) else [node.target]
            assert not any((isinstance(n, ast.Name) and n.id == '_signal_family_key' for t in targets for n in ast.walk(t))), 'shared callable mutation'

def _check_owner(text):
    tree = ast.parse(text)
    assert all((isinstance(n, ast.FunctionDef) or (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)) or (isinstance(n, ast.ImportFrom) and n.module == '__future__' and ([a.name for a in n.names] == ['annotations'])) for n in tree.body)), 'family owner has undeclared effects/imports'
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    assert len(functions) == 1 and functions[0].name == 'signal_family_key'
    fn = functions[0]
    if fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant) and isinstance(fn.body[0].value.value, str):
        fn.body.pop(0)
    assert _shape(fn) == EXPECTED_FUNCTION_SHAPE, 'family semantics need explicit requalification'

DELEGATION = {
    'mi_adhilepa.py': [('MiAdhilepaWriter.run', '_signal_family_key(sig)')],
    'mi_bhavisya.py': [
        ('MiBhavisyaWriter.run', '_signal_family_key(dict(r))'),
        ('MiBhavisyaWriter.run', '_signal_family_key(msr_signals[sid])'),
    ],
}

def _check_delegation(text, expected):
    calls = []
    def walk(node, scope):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            scope = scope + [node.name]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_signal_family_key':
            calls.append(('.'.join(scope), ast.unparse(node)))
        for child in ast.iter_child_nodes(node):
            walk(child, scope)
    walk(ast.parse(text), [])
    assert sorted(calls) == sorted(expected), 'shared family call/input delegation changed'

def test_actual_writer_interfaces():
    for name in ('mi_adhilepa.py', 'mi_bhavisya.py'):
        text = (SIDECAR / 'pipeline/orchestrator/writers' / name).read_text()
        _check_writer(text)
        _check_delegation(text, DELEGATION[name])

def test_actual_pure_owner():
    _check_owner((SIDECAR / 'services/mimamsa/signal_family.py').read_text())

@pytest.mark.parametrize('bad', ['from pipeline.orchestrator.writers.mi_adhilepa import _signal_family_key', 'from .mi_adhilepa import _signal_family_key', 'from services.other import signal_family_key as _signal_family_key', "from services.mimamsa.signal_family import signal_family_key as _signal_family_key\n_signal_family_key=lambda x:'wrong'", 'from services.mimamsa.signal_family import signal_family_key as _signal_family_key\nimport importlib', 'from services.mimamsa.signal_family import signal_family_key as _signal_family_key\nfrom importlib import import_module', "from services.mimamsa.signal_family import signal_family_key as _signal_family_key\nglobals()['_signal_family_key']=None", 'from services.mimamsa.signal_family import signal_family_key as _signal_family_key\n_signal_family_key.__code__=None', 'from services.mimamsa.signal_family import signal_family_key as _signal_family_key\nimport other as _signal_family_key', 'from services.mimamsa.signal_family import signal_family_key as _signal_family_key\ndef f(_signal_family_key):return _signal_family_key({})', 'from services.mimamsa.signal_family import signal_family_key as _signal_family_key\nfrom other import *', "from services.mimamsa.signal_family import signal_family_key as _signal_family_key\nsetattr(_signal_family_key,'__code__',None)"])
def test_forbidden_edge_or_rebound_callable(bad):
    with pytest.raises(AssertionError):
        _check_writer(bad)

def test_public_binding_positive():
    _check_writer('from services.mimamsa.signal_family import signal_family_key as _signal_family_key')

@pytest.mark.parametrize('mutation', ['semantics', 'interface', 'module_effect', 'foreign_import'])
def test_owner_contract_mutants(mutation):
    text = (SIDECAR / 'services/mimamsa/signal_family.py').read_text()
    if mutation == 'semantics':
        text = text.replace('return ', 'return "wrong", ', 1)
    if mutation == 'interface':
        text = text.replace('def signal_family_key(', 'def _signal_family_key(', 1)
    if mutation == 'module_effect':
        text += '\nprint(123)\n'
    if mutation == 'foreign_import':
        text += '\nimport os\n'
    assert text != (SIDECAR / 'services/mimamsa/signal_family.py').read_text()
    with pytest.raises(AssertionError):
        _check_owner(text)

def test_owner_comments_compatible():
    text = (SIDECAR / 'services/mimamsa/signal_family.py').read_text()
    _check_owner(text + '\n# review annotation\n')

@pytest.mark.parametrize('name', list(DELEGATION))
@pytest.mark.parametrize('mutation', ['missing', 'wrong_input', 'duplicate'])
def test_writer_delegation_mutants(name, mutation):
    text = (SIDECAR / 'pipeline/orchestrator/writers' / name).read_text()
    if mutation == 'missing':
        text = text.replace('_signal_family_key(', 'unreviewed_family_key(', 1)
    if mutation == 'wrong_input':
        text = text.replace('_signal_family_key(', '_signal_family_key(None, ', 1)
    if mutation == 'duplicate':
        text += '\n_signal_family_key({})\n'
    with pytest.raises(AssertionError):
        _check_delegation(text, DELEGATION[name])

@pytest.mark.parametrize('append', [
    "\nimport builtins as hidden_builtin\nhidden_builtin.__import__('pipeline.orchestrator.writers.mi_adhilepa')\n",
    "\nimport builtins\nbuiltins.__import__('pipeline.orchestrator.writers.mi_adhilepa')\n",
    "\nfrom builtins import __import__ as hidden_import\n",
    "\n__builtins__['__import__']('pipeline.orchestrator.writers.mi_adhilepa')\n",
    "\nfamily_alias = _signal_family_key\nfamily_alias.__code__ = (lambda *args: 'changed').__code__\n",
])
def test_actual_writer_indirect_import_and_alias_mutants(append):
    text = (SIDECAR / 'pipeline/orchestrator/writers/mi_bhavisya.py').read_text()
    _check_writer(text)
    with pytest.raises(AssertionError):
        _check_writer(text + append)


def test_actual_async_binding_redefinition_refuses():
    text = (SIDECAR / 'pipeline/orchestrator/writers/mi_bhavisya.py').read_text()
    _check_writer(text)
    changed = text + "\nasync def _signal_family_key(*args, **kwargs): return 'changed'\n"
    with pytest.raises(AssertionError):
        _check_writer(changed)
