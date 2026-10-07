"""Operation-specific idempotency for Kāla candidates and issued forecasts.

Only candidate tables named here may be replaced. Issued forecasts and the
published head use different operations and must never enter this path.
The caller's orchestrator transaction owns commit/rollback.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from psycopg import sql


class ImmutableIssueConflict(ValueError):
    """An already issued forecast differs from the attempted issue."""


# Literal table names are intentional: the Idem detector needs to see each
# writer-owned DELETE, and a caller must not turn this into arbitrary SQL.
_DELETE_CANDIDATE = {
    "kala_avadhi": "DELETE FROM kala_avadhi WHERE chart_id = %s AND generation = %s",
    "kala_activation_predicates": "DELETE FROM kala_activation_predicates WHERE chart_id = %s AND generation = %s",
    "kala_obstruction": "DELETE FROM kala_obstruction WHERE chart_id = %s AND generation = %s",
    "kala_convergence": "DELETE FROM kala_convergence WHERE chart_id = %s AND generation = %s",
    "kala_field": "DELETE FROM kala_field WHERE chart_id = %s AND generation = %s",
    "kala_field_null": "DELETE FROM kala_field_null WHERE chart_id = %s AND generation = %s",
    "kala_field_salience": "DELETE FROM kala_field_salience WHERE chart_id = %s AND generation = %s",
    "kala_field_snapshots": "DELETE FROM kala_field_snapshots WHERE chart_id = %s AND generation = %s",
    "kala_activation": "DELETE FROM kala_activation WHERE chart_id = %s AND generation = %s",
    "kala_darshana": "DELETE FROM kala_darshana WHERE chart_id = %s AND generation = %s",
    "kala_taranga": "DELETE FROM kala_taranga WHERE chart_id = %s AND generation = %s",
    "kala_jivana_parva": "DELETE FROM kala_jivana_parva WHERE chart_id = %s AND generation = %s",
}


def replace_candidate_partition(
    conn: Any,
    table: str,
    chart_id: str,
    generation: str,
    grain_key: tuple[str, Any] | None,
    rows: Sequence[Mapping[str, Any]],
) -> int:
    """Replace one candidate partition, including an honestly empty result.

    ``grain_key`` is ``(column, value)`` or ``None`` for a whole-candidate
    read model. Every inserted row must explicitly carry the same chart,
    generation and grain. This function deliberately never commits.
    """
    if table not in _DELETE_CANDIDATE:
        raise ValueError(f"not a replaceable candidate table: {table!r}")
    if not chart_id or not generation:
        raise ValueError("chart_id and generation must be pinned")
    if grain_key is not None:
        if (not isinstance(grain_key, tuple) or len(grain_key) != 2
                or not isinstance(grain_key[0], str) or not grain_key[0].isidentifier()
                or grain_key[0] in {"chart_id", "generation"} or grain_key[1] is None):
            raise ValueError("grain_key must be a non-null (column, value) pair")

    prepared = [dict(row) for row in rows]
    for row in prepared:
        if row.get("chart_id") != chart_id or row.get("generation") != generation:
            raise ValueError("row is outside the candidate chart and generation")
        if grain_key is not None and row.get(grain_key[0]) != grain_key[1]:
            raise ValueError("row is outside the requested grain")
        if any(not isinstance(column, str) or not column.isidentifier() for column in row):
            raise ValueError("row contains an invalid column name")
    if prepared and any(row.keys() != prepared[0].keys() for row in prepared[1:]):
        raise ValueError("candidate rows must have the same columns")

    delete_sql = _DELETE_CANDIDATE[table]
    params: list[Any] = [chart_id, generation]
    if grain_key is not None:
        delete_sql += sql.SQL(" AND {} = %s").format(sql.Identifier(grain_key[0])).as_string(conn)
        params.append(grain_key[1])
    conn.execute(delete_sql, params)
    if prepared:
        columns = tuple(prepared[0])
        insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )
        for row in prepared:
            conn.execute(insert_sql, [row[column] for column in columns])
    return len(prepared)


def insert_immutable_checked(
    conn: Any,
    table: str,
    key: Mapping[str, Any],
    row: Mapping[str, Any],
) -> bool:
    """Insert one delivered issue, or verify an identical retry.

    The issue key is ``(issue_id, version)``; an episode is not an issue key.
    The issuing contract owns the table and its unique constraint. This helper
    never deletes, updates, commits, or turns a changed issue into a new one.
    Returns ``True`` only for a new insertion.
    """
    if table != "issued_forecast":
        raise ValueError(f"not an immutable issue table: {table!r}")
    if set(key) != {"issue_id", "version"}:
        raise ValueError("issue key must contain issue_id and version")
    if any(value is None or value == "" for value in key.values()):
        raise ValueError("issue key values must be pinned")
    prepared = dict(row)
    if any(not isinstance(column, str) or not column.isidentifier() for column in prepared):
        raise ValueError("issue row contains an invalid column name")
    if any(prepared.get(column) != value for column, value in key.items()):
        raise ValueError("issue row does not match its key")

    columns = tuple(prepared)
    column_sql = sql.SQL(", ").join(map(sql.Identifier, columns))
    placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in columns)
    inserted = conn.execute(
        sql.SQL("INSERT INTO issued_forecast ({}) VALUES ({}) "
                "ON CONFLICT (issue_id, version) DO NOTHING RETURNING 1").format(
            column_sql, placeholders,
        ),
        [prepared[column] for column in columns],
    ).fetchone()
    if inserted is not None:
        return True

    # Database equality handles timestamptz and JSON values without relying on
    # Python's input adapter and result decoder producing the same object type.
    same_columns = sql.SQL(" AND ").join(
        sql.SQL("{} IS NOT DISTINCT FROM %s").format(sql.Identifier(column))
        for column in columns
    )
    identical = conn.execute(
        sql.SQL("SELECT 1 FROM issued_forecast "
                "WHERE issue_id = %s AND version = %s AND {}").format(same_columns),
        [key["issue_id"], key["version"], *(prepared[column] for column in columns)],
    ).fetchone()
    if identical is None:
        raise ImmutableIssueConflict("an issued forecast cannot be changed")
    return False
