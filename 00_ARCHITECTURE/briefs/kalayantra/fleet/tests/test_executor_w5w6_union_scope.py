"""M-W56-6 / KIND-backup_snapshot (W5W6-READINESS WP6, oracle U3, executor side): a `backup_snapshot` request for scope `w5w6_union` is admitted by the
executor's real `validate()`, and the scope it names is one the scoped-backup script really offers.

The pack's declared awaiting reason for the kind was "the script does not name the 'w5w6_union' scope". Two detectors, each able to read false:
  A1 the real validate() over the repository's own executor_ops.json admits `backup_snapshot` with args {label, scope: w5w6_union} (a signer's bound acceptance,
     as every production kind), and still refuses an arg the table does not list -- so the admission is the table's `allowed_args`, not a vacuous pass;
  A2 the scope the executor would pass on (`--scope w5w6_union`) is accepted by the script's own argument parser and has a reviewed scope file whose digest the
     executor-loaded policy pins -- a request the executor admits is a request the script can run.
No database, program or credential is used.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_executor_table import ALL_CAPS, OPS_FILE, World, copy_with  # noqa: E402

REPO = HERE.parents[4]
SCRIPTS = REPO / 'platform/scripts'


def load_script(name):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location('w56_' + name, SCRIPTS / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def world(tmp_path, monkeypatch):
    # the repository's own table with backup_snapshot enabled on a fixture script (a production kind needs a landed script); allowed_args stay the table's own
    w = World(tmp_path, monkeypatch, copy_with(OPS_FILE.read_text(), 'backup_snapshot', script='platform/scripts/fixture_backup.sh'))
    return w, w.table()


def test_a1_a_union_scope_request_is_admitted_and_an_unlisted_argument_is_not(world):
    w, table = world
    assert 'scope' in table['backup_snapshot']['allowed_args']
    req = w.accept(w.production_request('backup_snapshot', args={'label': 'w56_union_a', 'scope': 'w5w6_union'}))
    assert w.mod.validate(req, table, ALL_CAPS) is None
    other = w.accept(w.production_request('backup_snapshot', args={'label': 'w56_union_a', 'scope': 'w5w6_union', 'scopes': 'x'}))
    assert w.mod.validate(other, table, ALL_CAPS) == "disallowed args ['scopes']"


def test_a1_the_admission_is_the_tables_allowed_args(world):
    w, table = world
    table = {**table, 'backup_snapshot': {**table['backup_snapshot'], 'allowed_args': ['label']}}                       # the table without `scope`
    req = w.accept(w.production_request('backup_snapshot', args={'label': 'w56_union_a', 'scope': 'w5w6_union'}))
    assert w.mod.validate(req, table, ALL_CAPS) == "disallowed args ['scope']"


def test_a2_the_scope_the_executor_passes_on_is_one_the_script_runs_and_the_policy_pins():
    backup = load_script('backup_v5_small_test_job')
    shared = load_script('v5_small_test_shared')
    ns = backup._parse_args(['--operation', 'snapshot', '--label', 'w56_union_a', '--scope', 'w5w6_union', '--dry-run'])
    assert ns.scope == 'w5w6_union'
    assert backup.load_scope(name='w5w6_union')['sha256'] == shared.SCOPED_BACKUP_SCOPE_SHA256S['w5w6_union']
    with pytest.raises(SystemExit):
        backup._parse_args(['--operation', 'snapshot', '--label', 'w56_union_a', '--scope', 'w5w6_union_typo', '--dry-run'])
