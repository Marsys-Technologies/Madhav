"""Independent K12 clipping proof through the real writer and migration."""
from tests.l3.kala_db.conftest import kala_db_dsn  # noqa: F401 — explicit guarded fixture
from pipeline.orchestrator.writers.ka_avadhi import KaAvdhiWriter
from tests.l3.kala_db.ka_avadhi.test_writer import db, ctx, rows


def test_writer_does_not_promote_1950_window_start_to_natural_commencement(db):
    db.execute("UPDATE chart_dashas SET start_iso='1950-01-01Z',start_date='1950-01-01',is_truncated_at_window_start=true WHERE level_n=1")
    result=KaAvdhiWriter().run(ctx(db))
    assert result.rows_inserted==2
    dossier=dict(rows(db))['Mars']
    assert dossier['commencement_condition']['value'] is None, 'persisted artificial commencement at the 1950 clip'


def test_writer_preserves_the_end_clip_qualification_in_stored_dossier(db):
    writer=KaAvdhiWriter(); writer.run(ctx(db)); normal=dict(rows(db))
    db.execute("UPDATE chart_dashas SET is_truncated_at_window_end=true WHERE level_n=1")
    writer.run(ctx(db)); clipped=dict(rows(db))
    assert clipped['Mars'] != normal['Mars'], 'persisted dossier loses the window-end clip'
