"""J4P-B3: only the governed reader and independent verifier may read daśās."""
import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ALLOWED = {
    'services/gochara_kernel/dasha_read.py',
    'services/gochara_kernel/inventory_verifier.py',
}
READ = re.compile(r"""\b(?:from|join)\s+(?:only\s+)?(?:"?public"?\s*\.\s*)?["\']?chart_dashas\b""", re.I)


def violations(source, path):
    if path in ALLOWED:
        return []
    tree = ast.parse(source)
    docstrings = {id(n.value) for n in ast.walk(tree)
                  if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                  and isinstance(n.value.value, str)}
    found = []
    string_names = {}
    query_aliases = {'dasha_query'}
    private_names = {'_fetch_dasha_periods_multilevel', '_DASHA_QUERIES'}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.endswith('dasha_read'):
            query_aliases.update(a.asname or a.name for a in node.names if a.name == 'dasha_query')

    def static_text(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return string_names.get(node.id, '')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == 'format':
                template = static_text(node.func.value)
                try:
                    return template.format(*(static_text(a) for a in node.args),
                                           **{k.arg: static_text(k.value) for k in node.keywords if k.arg})
                except (ValueError, IndexError, KeyError):
                    return template
            if node.func.attr == 'Identifier':
                return '.'.join(static_text(a) for a in node.args)
            if node.func.attr == 'SQL':
                return ''.join(static_text(a) for a in node.args)
        if isinstance(node, (ast.JoinedStr, ast.FormattedValue, ast.BinOp)):
            return ''.join(static_text(c) for c in ast.iter_child_nodes(node))
        return ''

    assignments = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)]
    for _ in range(len(assignments) + 1):
        before = dict(string_names)
        for node in assignments:
            value = static_text(node.value)
            if value:
                string_names.update({t.id: value for t in node.targets if isinstance(t, ast.Name)})
        if before == string_names:
            break

    query_names = set(query_aliases)
    def uses_query(node):
        return any(isinstance(n, ast.Name) and n.id in query_names or
                   isinstance(n, ast.Attribute) and n.attr == 'dasha_query'
                   for n in ast.walk(node))
    for _ in range(len(assignments) + 1):
        before = set(query_names)
        for node in assignments:
            if uses_query(node.value):
                query_names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        if before == query_names:
            break

    def dasha_reference(node):
        return static_text(node) == 'chart_dashas' or (
            isinstance(node, (ast.Name, ast.Attribute)) and
            (node.id if isinstance(node, ast.Name) else node.attr).lower().replace('_', '')
            in {'chartdasha', 'chartdashas'})

    for node in ast.walk(tree):
        if isinstance(node, (ast.Constant, ast.BinOp, ast.JoinedStr, ast.Call)):
            if id(node) not in docstrings and READ.search(static_text(node)):
                found.append(f'{path}:{node.lineno}: direct SQL daśā read')
        if isinstance(node, ast.ImportFrom) and any(a.name in private_names for a in node.names):
            found.append(f'{path}:{node.lineno}: private loader access')
        if isinstance(node, ast.Attribute) and node.attr in private_names or (
            isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in private_names
        ):
            found.append(f'{path}:{node.lineno}: private loader access')
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else (
                node.func.id if isinstance(node.func, ast.Name) else '')
            if name in {'select', 'query', 'table', 'from_', 'Identifier'}:
                if any(dasha_reference(a) for a in node.args):
                    found.append(f'{path}:{node.lineno}: direct ORM/composed SQL daśā access')
            if name in {'execute', 'executemany'} and node.args and uses_query(node.args[0]):
                found.append(f'{path}:{node.lineno}: unguarded registered projection')
    return found


def scan_source_tree(root):
    paths = list((root / 'services').rglob('*.py'))
    writers = root / 'pipeline/orchestrator/writers'
    paths += [p for p in writers.rglob('*.py')
              if p.relative_to(writers).parts[0].startswith('ka_')]
    paths += list((root / 'scripts/kala_gochara_cutover').rglob('*.py'))
    paths += list((root / 'routers').rglob('*.py'))
    found = []
    for path in paths:
        if 'tests' not in path.parts and not path.name.startswith('test_'):
            found.extend(violations(path.read_text(), path.relative_to(root).as_posix()))
    return found


def test_no_direct_dasha_reads():
    assert not (found := scan_source_tree(ROOT)), '\n'.join(found)


@pytest.mark.parametrize('source', [
    'conn.execute("SELECT * FROM chart_dashas WHERE chart_id=%s", (chart_id,))',
    'sql = "SELECT d.* " "FROM public.chart_dashas d"\nconn.execute(sql)',
    'conn.execute("select a.* from chart_facts a JOIN chart_dashas d ON true")',
    'db.table("chart_dashas").select("*")',
    'sql = "SELECT * FROM " + "chart_dashas"\nconn.execute(sql)',
    'sql = dasha_query("timeline")\nconn.execute(sql)',
    'DD._fetch_dasha_periods_multilevel(conn, chart_id)',
    'table = "chart_dashas"\nsql = f"SELECT * FROM {table}"\nconn.execute(sql)',
    'session.query(ChartDashas).all()',
    'conn.execute(DR.dasha_query("clock_rows"), params)',
    'raw = DR._fetch_dasha_periods_multilevel\nraw(conn, chart_id)',
    'getattr(DR, "_fetch_dasha_periods_multilevel")(conn, chart_id)',
    'conn.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier("chart_dashas")))',
    'conn.execute("SELECT * FROM {}".format("chart_dashas"))',
    'from services.gochara_kernel.dasha_read import dasha_query as raw_query\nconn.execute(raw_query("clock_rows"))',
    'table = "chart_" + "dashas"\nconn.execute(f"SELECT * FROM {table}")',
    'query = DR.dasha_query("clock_rows")\nconn.execute(query)',
    'select(ChartDasha)',
    'conn.execute(\'SELECT * FROM ONLY "public"."chart_dashas"\')',
])
def test_guard_catches_planted_bypass(source, tmp_path):
    planted = tmp_path / 'services/gochara_grammar/planted.py'
    planted.parent.mkdir(parents=True)
    planted.write_text(source)
    assert scan_source_tree(tmp_path), 'a planted bypass must fail the production-tree guard'


def test_guard_scans_nested_kala_writer_packages(tmp_path):
    planted = tmp_path / 'pipeline/orchestrator/writers/ka_future/__init__.py'
    planted.parent.mkdir(parents=True)
    planted.write_text('conn.execute("SELECT * FROM chart_dashas")')
    assert scan_source_tree(tmp_path), 'Kāla writer packages must share the same source boundary'
