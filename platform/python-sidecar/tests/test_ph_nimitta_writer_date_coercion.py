"""test_ph_nimitta_writer_date_coercion.py — R6 fix regression test.

ph_nimitta.py's `_enrich_discovery_row` previously only coerced `detected_at` when it
arrived as a `str`, silently passing a raw `datetime.datetime` through untouched (the
real shape returned by psycopg for a `timestamptz` column, e.g. bodha_discoveries.
detected_at). window_end (= detected_at + 90 days) then stayed a datetime, and the
writer's T-5 pre-birth gate (`window_end < birth_date`, birth_date being a plain date)
crashed with "TypeError: can't compare datetime.datetime to datetime.date" — this
cascaded to fail every downstream L4/L5 asset in a real live rebuild (Abhinandan,
2026-07-11). Fixed by routing through the already-correct `_parse_iso_date` helper,
which handles datetime/date/str uniformly.
"""
from __future__ import annotations

import sys
import pathlib
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.writers.ph_nimitta import (  # noqa: E402
    PhNimittaWriter,
    _parse_iso_date,
)


class TestParseIsoDate:
    def test_handles_datetime(self):
        assert _parse_iso_date(datetime(2026, 9, 15, 14, 30, 0)) == date(2026, 9, 15)

    def test_handles_date(self):
        assert _parse_iso_date(date(2026, 9, 15)) == date(2026, 9, 15)

    def test_handles_iso_string(self):
        assert _parse_iso_date('2026-09-15') == date(2026, 9, 15)

    def test_handles_none(self):
        assert _parse_iso_date(None) is None

    def test_handles_garbage_string(self):
        assert _parse_iso_date('not-a-date') is None


class TestEnrichDiscoveryRowDateCoercion:
    def _mock_conn_no_proximity_match(self):
        """A conn whose cursor context managers succeed but find no nearby convergence row —
        isolates the date-coercion behavior from the proximity-lookup DB round-trip."""
        conn = MagicMock()
        cur = MagicMock()
        cur.__enter__ = MagicMock(return_value=cur)
        cur.__exit__ = MagicMock(return_value=False)
        cur.fetchone.return_value = None
        conn.cursor.return_value = cur
        return conn

    def test_detected_at_as_raw_datetime_produces_date_window(self):
        """The exact real-world shape: bodha_discoveries.detected_at as timestamptz."""
        w = PhNimittaWriter()
        conn = self._mock_conn_no_proximity_match()
        row = {'detected_at': datetime(2026, 6, 1, 9, 30, 0), 'domain': 'career'}

        enriched = w._enrich_discovery_row(conn, row, chart_id='1c826d5a-...')

        assert enriched['window_start'] == date(2026, 6, 1)
        assert enriched['window_end'] == date(2026, 6, 1) + timedelta(days=90)
        assert isinstance(enriched['window_start'], date) and not isinstance(enriched['window_start'], datetime)
        assert isinstance(enriched['window_end'], date) and not isinstance(enriched['window_end'], datetime)

    def test_detected_at_as_date_still_works(self):
        w = PhNimittaWriter()
        conn = self._mock_conn_no_proximity_match()
        row = {'detected_at': date(2026, 6, 1), 'domain': 'career'}

        enriched = w._enrich_discovery_row(conn, row, chart_id='1c826d5a-...')

        assert enriched['window_start'] == date(2026, 6, 1)

    def test_detected_at_as_iso_string_still_works(self):
        w = PhNimittaWriter()
        conn = self._mock_conn_no_proximity_match()
        row = {'detected_at': '2026-06-01T09:30:00', 'domain': 'career'}

        enriched = w._enrich_discovery_row(conn, row, chart_id='1c826d5a-...')

        assert enriched['window_start'] == date(2026, 6, 1)

    def test_window_end_never_crashes_comparison_against_plain_date(self):
        """The exact crash this fix closes: window_end < birth_date must not raise TypeError."""
        w = PhNimittaWriter()
        conn = self._mock_conn_no_proximity_match()
        row = {'detected_at': datetime(1980, 1, 1, 0, 0, 0), 'domain': 'career'}

        enriched = w._enrich_discovery_row(conn, row, chart_id='1c826d5a-...')
        birth_date = date(1984, 2, 5)

        # This is the literal comparison from the writer's T-5 gate — must not raise.
        assert enriched['window_end'] < birth_date
