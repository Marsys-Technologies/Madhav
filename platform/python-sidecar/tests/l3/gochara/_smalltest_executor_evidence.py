"""Verifier-bound request fixture for the inherited C37/C38 SQL guard suites.

No policy guard is disabled. All tested operation code still reads and validates
real filesystem evidence; only the prior independent verifier is a fixture.
"""
import functools
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[5] / 'platform/scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / '__tests__'))


@pytest.fixture(autouse=True)
def executor_bound_smalltest(monkeypatch, tmp_path):
    import json
    import teardown_v5_small_test_job as td
    import dispatch_v5_small_test_job as dispatch
    import smalltest_safety_support as S
    real_teardown, real_main = td.teardown, dispatch.main

    @functools.wraps(real_teardown)
    def teardown(*, dry_run=True):
        dsn = os.environ.get('DATABASE_URL', '')
        if not dsn or 'hunter2' in dsn or 'malformed' in dsn or 'not-' in dsn:
            return real_teardown(dry_run=dry_run)
        with S.database_request(dsn, dry_run=dry_run):
            return real_teardown(dry_run=dry_run)

    @functools.wraps(real_main)
    def main(argv=None):
        argv = argv or []
        rr, ar = S.absence_for(tmp_path)
        args = {key: argv[argv.index('--' + key) + 1] for key in
                ('run', 'classes', 'horizon-start', 'horizon-end') if '--' + key in argv}
        args.setdefault('classes', 'all')
        req = S.authorize(tmp_path, dict(kind='smalltest_dispatch', operation_id='dispatch', args=args,
                                         absence_receipt=rr, absence_acceptance=ar))
        with monkeypatch.context() as patch:
            patch.setenv('KY_ROOT', str(tmp_path)); patch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
            return real_main(argv)
    monkeypatch.setattr(td, 'teardown', teardown)
    monkeypatch.setattr(dispatch, 'main', main)
