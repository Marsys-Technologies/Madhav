"""
Tests for pipeline.bootstrap_panchanga._check_existing_rows.

Mocks the DB cursor via sys.modules injection (psycopg2 is imported locally
inside the function, so module-level patch() cannot reach it). No live DB.
"""
import sys
import pytest
from unittest.mock import MagicMock

from pipeline.bootstrap_panchanga import _check_existing_rows


def _psycopg2_mock(fetchall_return):
    """Return a fake psycopg2 module whose .connect() yields the given rows."""
    cur = MagicMock()
    cur.fetchall.return_value = fetchall_return

    cursor_cm = MagicMock()
    cursor_cm.__enter__ = MagicMock(return_value=cur)
    cursor_cm.__exit__ = MagicMock(return_value=False)

    conn = MagicMock()
    conn.cursor.return_value = cursor_cm

    conn_cm = MagicMock()
    conn_cm.__enter__ = MagicMock(return_value=conn)
    conn_cm.__exit__ = MagicMock(return_value=False)

    module = MagicMock()
    module.connect.return_value = conn_cm
    return module


class TestCheckExistingRows:
    def setup_method(self):
        # Remove any real psycopg2/psycopg so the mock controls the import path.
        self._removed = {}
        for key in ("psycopg2", "psycopg"):
            if key in sys.modules:
                self._removed[key] = sys.modules.pop(key)

    def teardown_method(self):
        # Restore originals and remove any mocks we injected.
        sys.modules.pop("psycopg2", None)
        sys.modules.update(self._removed)

    def test_staging_empty_returns_none(self):
        """Guard returns None (run proceeds) when staging table is empty."""
        sys.modules["psycopg2"] = _psycopg2_mock([])
        result = _check_existing_rows("postgresql://fake/db", "build-abc")
        assert result is None

    def test_staging_different_build_id_raises(self):
        """Guard raises RuntimeError referencing panchanga_daily_staging when
        staging has rows under a different build_id."""
        sys.modules["psycopg2"] = _psycopg2_mock([("build-old", 73050)])
        with pytest.raises(RuntimeError, match="panchanga_daily_staging"):
            _check_existing_rows("postgresql://fake/db", "build-new")

    def test_staging_same_build_id_returns_count(self):
        """Guard returns existing count for idempotent re-run with same build_id."""
        sys.modules["psycopg2"] = _psycopg2_mock([("build-abc", 73050)])
        result = _check_existing_rows("postgresql://fake/db", "build-abc")
        assert result == 73050
