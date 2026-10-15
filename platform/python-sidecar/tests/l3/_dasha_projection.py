"""Unit-test seam for domain algebra over already governed operand fixtures.

These older tests model a projection's result, not the loader's population SQL.
J4P refusal tests exercise the real loader separately with SQL alone emulated.
Never install this adapter in a suite-wide conftest or in production.
"""
def emulated_projection(conn, chart_id, sql, params=(), *, cursor=None, **kwargs):
    executor = cursor if cursor is not None else conn
    result = executor.execute(sql, params)
    return cursor if cursor is not None else result
