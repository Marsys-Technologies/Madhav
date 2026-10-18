#!/usr/bin/env python3
"""Derive Kāla window membership once for CI, migrate.ts and deploy.yml (A5 D-33).

The old list is an immutable seed (existing protection is never removed). Every numbered
migration above the guard's pinned production baseline with public-schema DDL joins the
window automatically. Explicit exclusions are reviewed exceptions, not guard exemptions:
the privilege scan still rejects excluded public DDL unless another protected window owns it.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
EXCLUSIONS = 'platform/scripts/kala_protected_migrations_exclusions.json'


def derive(root: Path = ROOT) -> list[str]:
    from check_public_schema_migration_privilege import (BASELINE_MAX_APPLIED, MIGRATION_DIRS,
                                                        KALA_LIST, find_violations)
    seed = set()
    previous = -1
    for raw in (root / KALA_LIST).read_text().splitlines():
        name = raw.split('#', 1)[0].strip()
        if not name:
            continue
        match = re.fullmatch(r'(\d+)_[A-Za-z0-9_]+\.sql', name)
        if not match or int(match[1]) <= previous:
            raise ValueError(f'invalid or unordered legacy protected filename: {name}')
        previous = int(match[1])
        seed.add(name)
    exclusions_path = root / EXCLUSIONS
    exclusions = json.loads(exclusions_path.read_text()) if exclusions_path.exists() else {}
    if not isinstance(exclusions, dict) or any(not re.fullmatch(r'\d+_[A-Za-z0-9_]+\.sql', k)
                                             or not isinstance(v, str) or len(v.strip()) < 12 for k, v in exclusions.items()):
        raise ValueError('protected exclusions must map numbered SQL filenames to a reviewable reason')
    if seed & exclusions.keys():
        raise ValueError('an exclusion cannot remove legacy protected membership')
    # An intentionally empty window retains the pre-discovery privilege-guard
    # semantics: protect nothing here, so its scan still reports uncovered DDL.
    # The deployment CLI below separately rejects empty windows.
    if not seed:
        return []
    selected = set(seed)
    for directory in MIGRATION_DIRS:
        for path in (root / directory).glob('*.sql'):
            match = re.match(r'^(\d+)_', path.name)
            if match and int(match[1]) > BASELINE_MAX_APPLIED and path.name not in exclusions and find_violations(path.read_text()):
                selected.add(path.name)
    return sorted(selected, key=lambda s: (int(s.split('_', 1)[0]), s))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo-root', type=Path, default=ROOT)
    args = ap.parse_args()
    selected = derive(args.repo_root)
    if not selected:
        raise ValueError('empty legacy protected seed would remove existing protection')
    print('\n'.join(selected))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f'protected migration discovery refused: {exc}', file=sys.stderr)
        sys.exit(5)
