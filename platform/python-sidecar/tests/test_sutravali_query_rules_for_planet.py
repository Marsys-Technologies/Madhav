"""
test_sutravali_query_rules_for_planet.py — regression guard for the R3 boundary
"remaining residual classification" fix (packet 4).

query_sutravali_rules_for_planet (routers/sutravali.py) was deliberately left
uncontracted in the capability-knowledge availability system because its
implementation mis-bound SQL parameters: `params: list = [planet, planet]`
duplicated the planet value against a query with only ONE `%s` placeholder for
it, so `cur.execute(sql, params)` always received one more (or, with `house`
set, a misaligned) parameter than the SQL's placeholder count. Postgres/psycopg
reject a parameter-count mismatch outright — the route could never succeed.

These tests assert params length always equals the SQL's own `%s` placeholder
count, for both the default (no house filter) and house-filtered branches —
the exact invariant the bug violated.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _install_fake_db(monkeypatch, rows):
    """Patch sutravali.get_conn so no real DB connection is ever attempted."""
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)

    connection = MagicMock()
    connection.cursor = MagicMock(return_value=cursor)
    connection.__enter__ = MagicMock(return_value=connection)
    connection.__exit__ = MagicMock(return_value=False)

    from routers import sutravali as mod
    monkeypatch.setattr(mod, "get_conn", lambda: connection)
    return mod, cursor


def _placeholder_count(sql: str) -> int:
    return sql.count("%s")


class TestQueryRulesForPlanetParamBinding:
    def test_without_house_filter_params_match_placeholders(self, monkeypatch):
        mod, cursor = _install_fake_db(monkeypatch, rows=[])

        mod.query_rules_for_planet(planet="Saturn", house=None, limit=50)

        assert cursor.execute.call_count == 1
        sql, params = cursor.execute.call_args[0]
        assert len(params) == _placeholder_count(sql), (
            f"params={params!r} does not match the SQL's own placeholder count "
            f"({_placeholder_count(sql)}) in:\n{sql}"
        )
        assert params == ["Saturn", 50]

    def test_with_house_filter_params_match_placeholders_and_order(self, monkeypatch):
        mod, cursor = _install_fake_db(monkeypatch, rows=[])

        mod.query_rules_for_planet(planet="Saturn", house=7, limit=25)

        sql, params = cursor.execute.call_args[0]
        assert len(params) == _placeholder_count(sql), (
            f"params={params!r} does not match the SQL's own placeholder count "
            f"({_placeholder_count(sql)}) in:\n{sql}"
        )
        # Order matters: planet filter, then house filter, then LIMIT.
        assert params == ["Saturn", mod._house_str(7), 25]
