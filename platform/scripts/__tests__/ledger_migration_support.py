"""Reads the committed-substep LEDGER's schema from the WRITER lane's migration (SR-RESUME-INTEGRATION: "the WRITER lane's migration 1410 is the source of truth; the executor
side adapts to it, never the reverse"). Nothing here restates a column: the table name, the column names and their types are PARSED out of the migration's CREATE TABLE.

`find_migration()` returns (path-or-label, text) of the migration that creates `public.ka_gochara_build_ledger`:
  1. the repository's own platform/migrations (the normal case once the writer lane has merged);
  2. else, for a local run before the merge, the writer lane's branch (`git show`, read-only) — `KALA_LEDGER_MIGRATION_REF` overrides the ref;
  3. else None: the caller skips with the reason, or FAILS when `KALA_REQUIRE_LEDGER_MIGRATION=1`. (A skip is "not measured", never green: see the tests.)
"""
import os
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TABLE = 'ka_gochara_build_ledger'
DEFAULT_REF = 'origin/kalayantra/century-resume-writer'
CREATE = re.compile(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?' + TABLE + r'\s*\(', re.I)


def _strip_comments(text):
    return re.sub(r'--[^\n]*', '', text)


def find_migration():
    for path in sorted((REPO / 'platform/migrations').glob('*.sql')):
        text = path.read_text(encoding='utf-8', errors='ignore')
        if CREATE.search(_strip_comments(text)):
            return str(path.relative_to(REPO)), text
    ref = os.environ.get('KALA_LEDGER_MIGRATION_REF', DEFAULT_REF)
    for git_dir in (REPO, Path('/Users/Dev/Vibe-Coding/Apps/Madhav')):
        try:
            names = subprocess.run(['git', '-C', str(git_dir), 'ls-tree', '--name-only', ref, 'platform/migrations/'], capture_output=True, text=True, timeout=30,
                                   env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
            if names.returncode:
                continue
            for name in sorted(n for n in names.stdout.split() if n.endswith('.sql')):
                shown = subprocess.run(['git', '-C', str(git_dir), 'show', f'{ref}:{name}'], capture_output=True, text=True, timeout=30, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
                if shown.returncode == 0 and CREATE.search(_strip_comments(shown.stdout)):
                    return f'{ref}:{name}', shown.stdout
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def _top_level_items(body):
    items, depth, current = [], 0, ''
    for char in body:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        if char == ',' and depth == 0:
            items.append(current)
            current = ''
        else:
            current += char
    items.append(current)
    return [' '.join(item.split()) for item in items if item.strip()]


def parse_ledger(text):
    """{'table': name, 'columns': {column: type token}} of the ledger table created by `text`. Constraint clauses are not columns."""
    text = _strip_comments(text)
    match = CREATE.search(text)
    if match is None:
        raise ValueError('the migration does not create ' + TABLE)
    depth, end = 1, match.end()
    while depth and end < len(text):
        depth += {'(': 1, ')': -1}.get(text[end], 0)
        end += 1
    columns = {}
    for item in _top_level_items(text[match.end():end - 1]):
        words = item.split()
        if words[0].upper() in ('CONSTRAINT', 'PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'EXCLUDE', 'LIKE'):
            continue
        columns[words[0]] = words[1].lower()
    return {'table': TABLE, 'columns': columns}


def sql_references(sql, alias='l'):
    """Every `<alias>.<column>` an SQL text reads."""
    return set(re.findall(r'\b' + re.escape(alias) + r'\.([a-z_][a-z0-9_]*)', sql))


def rename_column(text, old, new):
    """The migration text with ONE column renamed in its CREATE TABLE column definition (a planted schema drift for the fail-on-revert proof)."""
    match = CREATE.search(text)
    head, tail = text[:match.end()], text[match.end():]
    pattern = re.compile(r'(?m)^(\s*)' + re.escape(old) + r'(\s+(?:UUID|TEXT|INTEGER|TSTZRANGE|JSONB|TIMESTAMPTZ)\b)', re.I)
    if len(pattern.findall(tail)) != 1:
        raise RuntimeError('planted rename anchor not unique: ' + old)        # a bad anchor must never read as a failed oracle
    return head + pattern.sub(lambda m: m.group(1) + new + m.group(2), tail, count=1)
