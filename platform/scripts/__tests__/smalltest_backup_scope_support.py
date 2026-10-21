"""Static write-target scanner for the J-2a scoped small-test backup (binding condition 1).

Finds every SQL statement that can WRITE a table in the code the small test runs
(dispatch, teardown, shared policy, the orchestrator modules, the Gochara kernel
and the first-party import closure of the ka_gochara_v5 writer). Only string
literals are read (comments and docstrings are not SQL), so a prose sentence
that happens to contain "insert into" is not a write target.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SIDECAR = ROOT / 'platform/python-sidecar'
SCRIPTS = ROOT / 'platform/scripts'
WRITER = SIDECAR / 'pipeline/orchestrator/writers/ka_gochara_v5.py'

_ID = r'(?:public\.)?"?([A-Za-z_][A-Za-z0-9_]*|\{[^}]*\})"?'
_WRITES = {
    'INSERT': re.compile(r'\bINSERT\s+INTO\s+(?:ONLY\s+)?' + _ID +
                         r'(?=\s*(?:\(|VALUES|SELECT|DEFAULT|OVERRIDING|ON\s+CONFLICT|WITH\b))', re.I),
    'UPDATE': re.compile(r'\bUPDATE\s+(?:ONLY\s+)?' + _ID + r'(?:\s+(?:AS\s+)?[A-Za-z_]\w*)?\s+SET\b', re.I),
    'DELETE': re.compile(r'\bDELETE\s+FROM\s+(?:ONLY\s+)?' + _ID, re.I),
    'MERGE': re.compile(r'\bMERGE\s+INTO\s+' + _ID, re.I),
    # upper-case only: lower-case "copy them from" / "truncate" are English
    'TRUNCATE': re.compile(r'\bTRUNCATE\s+(?:TABLE\s+)?(?:ONLY\s+)?' + _ID),
    'COPY': re.compile(r'\bCOPY\s+' + _ID + r'\s*(?:\(|FROM\b|TO\b)'),
}


def first_party_import_closure(start: Path) -> list[Path]:
    seen, todo = set(), [start]
    while todo:
        path = todo.pop()
        if path in seen:
            continue
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names += [node.module] + [f'{node.module}.{a.name}' for a in node.names]
            elif isinstance(node, ast.Import):
                names += [a.name for a in node.names]
            for name in names:
                if name.split('.')[0] not in ('pipeline', 'services'):
                    continue
                base = SIDECAR / name.replace('.', '/')
                for candidate in (base.with_suffix('.py'), base / '__init__.py'):
                    if candidate.exists() and candidate not in seen:
                        todo.append(candidate)
    return sorted(seen)


def scanned_files() -> list[Path]:
    files = {SCRIPTS / 'dispatch_v5_small_test_job.py', SCRIPTS / 'teardown_v5_small_test_job.py',
             SCRIPTS / 'v5_small_test_shared.py'}
    files |= set((SIDECAR / 'pipeline/orchestrator').glob('*.py'))
    files |= set((SIDECAR / 'services/gochara_kernel').rglob('*.py'))
    files |= set(first_party_import_closure(WRITER))
    return sorted(f for f in files if not {'tests', '__tests__'} & set(f.relative_to(ROOT).parts))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def _text(node) -> str:
    if isinstance(node, ast.Constant):
        return node.value
    parts = []
    for part in node.values:
        if isinstance(part, ast.Constant):
            parts.append(str(part.value))
        else:
            expr = part.value
            parts.append('{%s}' % (expr.id if isinstance(expr, ast.Name) else '...'))
    return ''.join(parts)


def sql_strings(tree: ast.AST):
    """(lineno, qualified function name, text) of every non-docstring string literal."""
    out = []

    def visit(node, stack):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant) and isinstance(child.value.value, str):
                continue                                        # docstring / bare string statement
            if (isinstance(child, ast.Constant) and isinstance(child.value, str)) or isinstance(child, ast.JoinedStr):
                out.append((child.lineno, '.'.join(stack) or '<module>', _text(child)))
                continue                                        # do not descend into the f-string's parts
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                visit(child, stack + [child.name])
            else:
                visit(child, stack)
    visit(tree, [])
    return out


def write_sites(files=None) -> list[dict]:
    """Every write statement: {table, kind, file, function, line}. A placeholder target stays '{name}'."""
    sites = []
    for path in files or scanned_files():
        for line, function, text in sql_strings(ast.parse(path.read_text())):
            for kind, pattern in _WRITES.items():
                for match in pattern.finditer(text):
                    table = match.group(1)
                    if table.lower() == 'set':
                        continue
                    sites.append({'table': table, 'kind': kind, 'file': rel(path), 'function': function, 'line': line})
    return sites


def eval_constant(paths, name: str):
    """Evaluate a module-level constant built from literals, earlier constants and '+'.

    `paths` may name several files (a constant imported from another module is
    defined by the earlier file), evaluated in order into one namespace.
    """
    values = {}

    def ev(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, (ast.Tuple, ast.List)):
            return tuple(ev(e) for e in node.elts)
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return ev(node.left) + ev(node.right)
        raise ValueError(ast.dump(node))
    for path in paths:
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                try:
                    values[node.targets[0].id] = ev(node.value)
                except (ValueError, KeyError):
                    pass
    return values[name]


def call_first_literals(path: Path, method: str) -> list[str]:
    """First string argument of every `<obj>.method("...")` call in a file."""
    found = []
    for node in ast.walk(ast.parse(path.read_text())):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == method
                and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            found.append(node.args[0].value)
    return found


def resolve_dynamic(resolver: str) -> list[str]:
    """`const:<file>:<NAME>:<first|plain|scalar>` or `calls:<file>:<method>` -> sorted table names."""
    kind, *rest = resolver.split(':')
    if kind == 'const':
        path, name, mode = rest
        value = eval_constant([ROOT / p for p in path.split('+')], name)
        if mode == 'scalar':                                    # a module constant that is one table name
            return [value]
        return sorted({v[0] if mode == 'first' else v for v in value})
    if kind == 'calls':
        path, method = rest
        return sorted(set(call_first_literals(ROOT / path, method)))
    raise ValueError(resolver)


def references(function_names, aliases, files) -> list[tuple[str, int, str]]:
    """Call sites `alias.name(...)` (or a bare `name(...)` inside the defining module) in the given files."""
    hits = []
    for path in files:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in function_names and isinstance(func.value, ast.Name) \
                    and func.value.id in aliases:
                hits.append((rel(path), node.lineno, func.attr))
            elif isinstance(func, ast.Name) and func.id in function_names:
                hits.append((rel(path), node.lineno, func.id))
    return hits


def imported_module_names(files) -> set[str]:
    names = set()
    for path in files:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split('.')[-1])
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.Import):
                names.update(a.name.split('.')[-1] for a in node.names)
    return names


def uncovered_targets(sites, scope) -> list[str]:
    """Write targets (or undeclared placeholder sites) that the reviewed scope does not account for."""
    written = {e['table'].split('.', 1)[1] for e in scope['written']}
    unreached = {t for u in scope['unreached'] for t in u['tables']}
    dynamic = {(d['file'], d['function']): d['tables'] for d in scope['dynamic_sites']}
    bad = set()
    for site in sites:
        if site['table'].startswith('{'):
            names = dynamic.get((site['file'], site['function']))
            if names is None:
                bad.add(f"{site['file']}::{site['function']} writes a placeholder table that the scope does not declare")
                continue
        else:
            names = [site['table']]
        bad |= {n for n in names if n not in written and n not in unreached}
    return sorted(bad)


def internal_callers(path: Path, names) -> set[str]:
    """Names of the functions in one module that call (by bare name) any function in `names`."""
    callers = set()
    for fn in ast.walk(ast.parse(path.read_text())):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in names:
                    callers.add(fn.name)
    return callers
