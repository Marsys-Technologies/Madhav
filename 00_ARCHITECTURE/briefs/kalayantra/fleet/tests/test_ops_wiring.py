"""The only table mutations are disabled mappings; no executor launched."""
import json
import os
from pathlib import Path
import subprocess

from test_ops_backup import FLEET

TABLE = FLEET/'executor_ops.json'
REL = '00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json'
MAPPINGS = {'backup_snapshot','backup_restore_verify','orchestrator_rebuild_dryrun','orchestrator_rebuild','orchestrator_rebuild_readback'}


def test_disabled_mappings_exist_and_all_other_entries_remain_byte_equivalent():
    table=json.loads(TABLE.read_text())
    p=subprocess.run(['git','show','26806eeaa:'+REL],capture_output=True,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
    assert p.returncode==0
    before=json.loads(p.stdout)
    assert table['_doc']==before['_doc']
    assert {k for k,v in table['ops'].items() if v['enabled']}=={k for k,v in before['ops'].items() if v['enabled']}
    for key,value in before['ops'].items():
        if key not in MAPPINGS: assert table['ops'][key]==value
    for key in MAPPINGS:
        row=table['ops'][key]
        assert next(iter(row))=='enabled' and row['enabled'] is False
        assert row['production'] is True
        assert (FLEET.parents[3]/row['script']).is_file()
        assert 'scope' in row['allowed_args'] and 'idempotency-key' in row['allowed_args']
    assert table['ops']['orchestrator_rebuild_dryrun']['fixed_args']==['--dry-run']
    for key in MAPPINGS-{'orchestrator_rebuild_dryrun'}:
        assert table['ops'][key]['fixed_args']==['--execute']
