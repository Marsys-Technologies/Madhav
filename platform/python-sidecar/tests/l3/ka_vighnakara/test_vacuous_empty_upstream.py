"""SR-K9-ADMITTED-ZERO: ka_vighnakara's zero-row pass from an EMPTY upstream is a LABELLED outcome, never a silent one (as ka_sangam, #3904).

With target_floor = 0 (migration 1409) the orchestrator no longer reads "0 rows" as a silent failure for this asset, and its integrity contract reads
TRUE on an empty kala_obstruction (nothing violates it). The orchestrator persists no WriterResult.notes (FROZEN contract), so the label is in the notes AND
in the run log: `upstream_convergence_rows=<n>; vacuous=true reason=<named>`. Rows are never invented (CLAUDE.md §N.7.6, B.10).

Claims:
E1 an empty upstream (0 peak-dated convergence windows) -> 0 rows written, notes AND a WARNING run-log line carry the label with the count and a named reason;
E2 a non-empty upstream is NOT labelled (the label is measured from the upstream rows, not asserted).
"""
import logging
from datetime import date
from types import SimpleNamespace

from pipeline.orchestrator.writers import ka_vighnakara as kv


class _Cursor:
    def __init__(self, conv_rows, log):
        self._rows, self._log = conv_rows, log

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._log.append(sql)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return None


class _Conn:
    def __init__(self, conv_rows):
        self.sql = []
        self._rows = conv_rows

    def cursor(self, *a, **kw):
        return _Cursor(self._rows, self.sql)


def _run(monkeypatch, conv_rows):
    monkeypatch.setattr(kv, 'bound_candidate', lambda conn, build_id, chart_id: None)
    monkeypatch.setattr(kv, 'predicate_generation', lambda conn, chart_id, candidate: 'legacy')
    monkeypatch.setattr(kv, 'refuse_unbound_rewrite', lambda conn, chart_id, asset: None)
    monkeypatch.setattr(kv, 'convergence_read_generation', lambda conn, chart_id, candidate: 'legacy')
    monkeypatch.setattr(kv, 'has_stored_verification', lambda cur, table: False)
    cls = kv._LegacyKaVighnakaraWriter
    monkeypatch.setattr(cls, '_resolve_native_location', staticmethod(lambda c, ch, bp: {}))
    monkeypatch.setattr(cls, '_fetch_combustion_orbs', lambda self, c: {})
    monkeypatch.setattr(cls, '_fetch_natal_lagna_lon', lambda self, c, ch: None)
    monkeypatch.setattr(cls, '_fetch_natal_moon_lon', lambda self, c, ch: None)
    monkeypatch.setattr(cls, '_dasha_anchor_peaks', lambda self, c, ch, covered, gen: [])
    monkeypatch.setattr(kv, '_detect_all', lambda **kw: [])
    ctx = SimpleNamespace(db_conn=_Conn(conv_rows), build_id=None, config={'chart_id': 'c', 'birth_params': {'datetime_iso': '1984-02-05T10:43:00+05:30'}})
    return cls().run(ctx)


def test_e1_empty_upstream_is_labelled_vacuous_in_the_notes_and_the_run_log(monkeypatch, caplog):
    with caplog.at_level(logging.WARNING, logger=kv.logger.name):
        result = _run(monkeypatch, [])
    assert result.rows_inserted == 0                                         # never invent rows
    assert 'upstream_convergence_rows=0; vacuous=true reason=empty_upstream_convergence' in result.notes
    assert any(rec.levelno == logging.WARNING and 'upstream_convergence_rows=0; vacuous=true reason=empty_upstream_convergence' in rec.getMessage()
               for rec in caplog.records)


def test_e2_a_non_empty_upstream_is_not_labelled_vacuous(monkeypatch, caplog):
    peak = (1, 'S1', 'A', date(2030, 3, 3), 0.9, 0.5, date(2030, 3, 1), date(2030, 3, 5))
    with caplog.at_level(logging.WARNING, logger=kv.logger.name):
        result = _run(monkeypatch, [peak])
    assert 'vacuous' not in (result.notes or '')
    assert not any('vacuous' in rec.getMessage() for rec in caplog.records)


def test_label_is_empty_for_a_non_empty_upstream():
    assert kv._vacuous_label(3, 'legacy') == ''
    assert 'upstream_convergence_rows=0' in kv._vacuous_label(0, 'legacy')
