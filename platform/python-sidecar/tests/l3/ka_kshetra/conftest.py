"""Numerical writer harness; real partition/binding proofs live in kala_db.

The historical in-memory fake models one candidate partition. Do not pretend
that it enforces the database boundary: the real PostgreSQL suite does that.
"""
import pytest
from .fake_db import FakeConn, FakeCtx


@pytest.fixture(autouse=True)
def candidate_numerical_harness(monkeypatch, request):
    from services.ka_kshetra import candidate, g1_inputs, writer
    if not request.node.path.name.startswith('test_g1a'):
        monkeypatch.setattr(writer,'_candidate_engine',lambda:writer._engine_version())
    real_bind=candidate.bind_candidate
    real_load=g1_inputs.load_suppression
    original=FakeCtx.__init__
    def initialize(self,*args,**kwargs):
        original(self,*args,**kwargs)
        self.config.update(kshetra_g1_candidate='candidate:unit',as_of='1984-02-05T10:43:00+05:30')
    def bind(ctx,**kwargs):
        if isinstance(ctx.db_conn,FakeConn):
            ctx.db_conn.generation=ctx.config['kshetra_g1_candidate']
            return ctx.db_conn,{}
        return real_bind(ctx,**kwargs)
    def load(conn,*args):
        return ([],[]) if isinstance(conn,FakeConn) else real_load(conn,*args)
    monkeypatch.setattr(FakeCtx,'__init__',initialize)
    monkeypatch.setattr(candidate,'bind_candidate',bind)
    monkeypatch.setattr(g1_inputs,'load_suppression',load)
