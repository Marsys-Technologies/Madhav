#!/usr/bin/env python3
"""Measuring-only bridge, prepared disabled. Durable no-retry launch fence shared.

The executor supplies the accepted J-3c request, source and capabilities. This
module never stages through the small-test operation or changes enablement.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import smalltest_launch as bridge


def run(argv=None, *, dispatcher=None, connect=None, launcher=bridge.cloud_launcher, claim_dir=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--run', required=True, choices=('all_classes_full',))
    parser.add_argument('--classes', default='all', choices=('all',))
    args = parser.parse_args(argv)
    if dispatcher is None:
        sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'platform/scripts'))
        import dispatch_v5_measuring_job as dispatcher
    return bridge.run(['--run', args.run, '--classes', args.classes], dispatcher=dispatcher, connect=connect,
        launcher=launcher, claim_dir=claim_dir or Path(os.environ['KY_ROOT']) / 'run/ops/measuring_launch',
        launch_schema='ky.measuring_launch/1')


def cli(argv=None):
    try:
        run(argv)
        return 0
    except SystemExit as exc:
        return exc.code
    except BaseException as exc:
        print(f'measuring launch failed ({type(exc).__name__}); reconcile retained evidence, never retry', file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 1


if __name__ == '__main__':
    raise SystemExit(cli())
