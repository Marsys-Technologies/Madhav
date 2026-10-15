"""Writer integration for the shared instant-grain sky facade."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from pipeline.orchestrator.writers.ka_graha_sancara import KaGrahaSancaraWriter


def test_writer_selftest_accepts_the_shared_sky_facade() -> None:
    """Restoring the legacy day-grade source check makes this writer unhealthy."""
    health, detail = KaGrahaSancaraWriter()._run_selftest(SimpleNamespace(db_conn=None))

    assert health == "healthy"
    assert detail["errors"] == []


def test_writer_selftest_rejects_a_closed_registry_connection() -> None:
    """Dropping the connection-state guard can falsely mark a non-writable registry healthy."""
    connection = MagicMock()
    connection.closed = True

    health, detail = KaGrahaSancaraWriter()._run_selftest(SimpleNamespace(db_conn=connection))

    assert health == "unhealthy"
    assert detail["errors"] == ["asset registry connection is closed"]
