"""The code the W5/W6 window can run, for the `w5w6_union` scoped-backup scope (M-W56-6): the J-6 head change plus the K9 closed-plan rebuild,
verify, publish, rollback, cancel and teardown. The scan itself is smalltest_backup_scope_support's (the J-2a scanner); this module only names WHICH
files it is run over and adds the two detectors the J-2a scan has no need for: the literal table arguments of `replace_candidate_partition` (the
only dynamic write path of the K9 writers) and the foreign-key referrers of a table read from the migrations.
"""
from __future__ import annotations

import ast
import re

import smalltest_backup_scope_support as support

ROOT, SIDECAR = support.ROOT, support.SIDECAR
FLEET = ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet'
WRITERS_DIR = SIDECAR / 'pipeline/orchestrator/writers'
KALA_CORE = SIDECAR / 'services/kala_core'
HEAD_OPERATION = FLEET / 'head_operation.py'
# The K9 closed plan (K9 rehearsal r5: "closed 6-writer plan", ka_gochara_resonance between ka_yojaka and ka_gochara; brief 06). A later change of the
# plan is a change of this tuple AND of the scope file's `plan`; test U1 ties the two.
CLOSED_PLAN = ('ka_yojaka', 'ka_vedha_gochara', 'ka_gochara_resonance', 'ka_gochara', 'ka_sangam', 'ka_vighnakara')
CONTROL_MODULES = ('publication', 'publication_admission', 'rebuild_control', 'final_rebuild')   # K9-23 verify/publish/rollback/cancel/teardown + the offline preparation
IDEMPOTENCY = 'platform/python-sidecar/services/kala_core/idempotency/__init__.py'


def union_scanned_files():
    files = {HEAD_OPERATION}
    for name in CLOSED_PLAN:
        files |= set(support.first_party_import_closure(WRITERS_DIR / f'{name}.py'))
    for name in CONTROL_MODULES:
        files |= set(support.first_party_import_closure(KALA_CORE / f'{name}.py'))
    files |= set((SIDECAR / 'pipeline/orchestrator').glob('*.py'))          # the orchestrator bookkeeping every rebuild run writes
    return sorted(f for f in files if not {'tests', '__tests__'} & set(f.relative_to(ROOT).parts))


def partition_calls(files):
    """Every `replace_candidate_partition(conn, <table>, ...)` call: ([(file, line, literal table)], [(file, line, source of a non-literal table)])."""
    literal, other = [], []
    for path in files:
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (func.id if isinstance(func, ast.Name) else getattr(func, 'attr', None)) != 'replace_candidate_partition' or len(node.args) < 2:
                continue
            arg = node.args[1]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                literal.append((support.rel(path), node.lineno, arg.value))
            else:
                other.append((support.rel(path), node.lineno, ast.unparse(arg)))
    return literal, other


_FK_STATEMENT = re.compile(r'(?is)\b(?:CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?|ALTER\s+TABLE\s+(?:ONLY\s+)?(?:IF\s+EXISTS\s+)?)(?:public\.)?"?([a-z_][a-z0-9_]*)"?')
_FK_REFERENCE = re.compile(r'(?is)\bREFERENCES\s+(?:public\.)?"?([a-z_][a-z0-9_]*)"?')


def fk_referrers(migrations_dir, root_table):
    """Tables that (transitively) declare a foreign key to `root_table` in a literal CREATE/ALTER TABLE of the migrations: {table: migration file}.
    A table created through format()/%I in a DO block is not found; the caller states what it needs, never that the set is complete."""
    edges = set()
    for path in sorted(migrations_dir.glob('*.sql')):
        sql = re.sub(r'--[^\n]*', '', re.sub(r'(?s)/\*.*?\*/', '', path.read_text()))
        statements = [(m.start(), m.group(1)) for m in _FK_STATEMENT.finditer(sql)]
        for ref in _FK_REFERENCE.finditer(sql):
            before = [name for start, name in statements if start < ref.start()]
            if before and before[-1] != 'public':
                edges.add((before[-1], ref.group(1), path.name))
    found, todo = {}, [root_table]
    while todo:
        parent = todo.pop()
        for child, target, file in sorted(edges):
            if target == parent and child != root_table and child not in found:
                found[child] = file
                todo.append(child)
    return found
