"""Candidate validation before replacement, without a database server."""
from types import SimpleNamespace

import pytest

from services.ka_vighnakara import storage
from tests.l3.ka_vighnakara.test_negative_space import finding, protection


class CandidateCursor:
    def __enter__(self):
        return self

    def __exit__(self,*args):
        pass

    def execute(self,sql,params):
        self.result = ((str(finding().chart_id),'candidate:fixture','building',{'fixture':True})
                       if 'kala_layer_candidate' in sql else None)
        return self

    def fetchone(self):
        return self.result


@pytest.mark.parametrize('changes', [ {'assertion_id':'alias'},
    {'assertion_id':'alias','roots':{'record_ids':['fixture:judge'],
        'contact_ids':[], 'fact_ids':['fixture:additional-evidence']}},
    {'assertion_id':'alias','source':{'text':'another citation','locator':'alias locator'}}])
def test_physical_alias_rejected_before_replacement(monkeypatch,changes):
    replacements = []
    monkeypatch.setattr(storage,'replace_candidate_partition',lambda *args: replacements.append(args))
    cursor = CandidateCursor()
    ctx = SimpleNamespace(dry_run=False,config={'chart_id':str(finding().chart_id)},
        build_id='fixture:build',db_conn=SimpleNamespace(cursor=lambda **kwargs:cursor))
    protected = finding(protections=[protection()])
    alias = finding(**changes,protections=[protection()])
    with pytest.raises(ValueError,match='duplicate physical'):
        storage.write_fixture_candidate(ctx,[protected,alias])
    assert replacements == []
