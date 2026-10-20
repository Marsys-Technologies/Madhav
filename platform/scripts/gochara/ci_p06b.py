#!/usr/bin/env python3
"""P06b profiles in the required jobs, compatible with ci.test_suites/1.

This base predates the shared ci_discovery.py consumer. Keep this bounded
consumer until that consumer and P06 have landed; no file allowlists in ci.yml.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
SUITES=('p06b-python','p06b-typescript')


def discover(root: Path, suite: str):
    if suite not in SUITES:
        raise ValueError(f'unknown P06b suite: {suite}')
    config=json.loads((root/'platform/scripts/governance/ci_test_suites.json').read_text())
    if config['schema']!='ci.test_suites/1':
        raise ValueError('unsupported CI profile schema')
    profile=config['suites'][suite]
    cwd=root/profile['cwd']
    files=set()
    for pattern in profile['include']:
        if not any(char in pattern for char in '*?['):
            raise ValueError(f'CI include must be a glob: {pattern}')
        matched={p.relative_to(cwd).as_posix() for p in cwd.glob(pattern) if p.is_file()}
        if not matched:
            raise ValueError(f'empty P06b test family: {pattern}')
        files.update(matched)
    if not files:
        raise ValueError('empty P06b suite')
    return cwd,profile['engine'],sorted(files)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--suite',choices=SUITES)
    group.add_argument('--check',action='store_true')
    args=parser.parse_args(argv)
    if args.check:
        for suite in SUITES:
            discover(ROOT,suite)
        print('current')
        return 0
    cwd,engine,files=discover(ROOT,args.suite)
    if engine=='pytest':
        command=[sys.executable,'-m','pytest',*files,'-q','--tb=short','-rs','-p','no:cacheprovider']
    elif engine=='vitest':
        command=[str(ROOT/'platform/node_modules/.bin/vitest'),'run','--no-cache',*files]
    else:
        raise ValueError(f'unsupported engine: {engine}')
    return subprocess.run(command,cwd=cwd).returncode


if __name__=='__main__':
    raise SystemExit(main())
