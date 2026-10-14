from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from pipeline.orchestrator.writers.ka_avadhi import KaAvdhiWriter


class Conn:
    def __init__(self): self.writes=[]
    def cursor(self, **kwargs): return self
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def execute(self, sql, params=()):
        self.rows=[]
        if not sql.lstrip().startswith('SELECT'): self.writes.append(sql)
        elif 'FROM kala_layer_candidate' in sql:
            pin=dict(build_id='missing', ayanamsha_id='lahiri_chitrapaksha', tier='two_pass_verified', systems=['vimshottari'])
            self.rows=[dict(generation='candidate:G', state='building', conventions={'natal': pin, 'f2':pin,'node_model':'mean'})]
        return self
    def fetchall(self): return self.rows


def test_missing_f2_pin_clears_dossiers():
    conn=Conn()
    ctx=SimpleNamespace(config={'chart_id':'chart'}, build_id='owner', db_conn=conn, dry_run=False)
    with pytest.raises((ValueError, RuntimeError), match='pin'): KaAvdhiWriter().run(ctx)
    assert not conn.writes
