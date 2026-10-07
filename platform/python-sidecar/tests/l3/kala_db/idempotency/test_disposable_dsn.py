"""The fast precheck may use the local server's disposable postgres database."""

import pytest

from conftest import _disposable_test_dsn


def test_local_precheck_postgres_endpoint_is_permitted(monkeypatch):
    """Allow the fleet's TEMP-table endpoint while retaining the opt-in guard."""
    monkeypatch.setenv("KALA_REQUIRE_DB", "1")
    monkeypatch.setenv(
        "KALA_ADMIN_DSN", "postgresql://postgres:postgres@127.0.0.1:55433/postgres",
    )
    monkeypatch.setenv("KY_LANE", "k3")

    assert _disposable_test_dsn().endswith(":55433/postgres")


def test_non_campaign_database_is_rejected(monkeypatch):
    """Catch a regression that broadens the disposable-DB allowlist."""
    monkeypatch.setenv("KALA_REQUIRE_DB", "1")
    monkeypatch.setenv(
        "KALA_ADMIN_DSN", "postgresql://postgres:postgres@127.0.0.1:55433/other_database",
    )
    monkeypatch.setenv("KY_LANE", "k3")

    with pytest.raises(RuntimeError, match="must name the lane or CI disposable database"):
        _disposable_test_dsn()
