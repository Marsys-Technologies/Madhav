"""Apply the actual migration to the test connection's isolated schema."""
from pathlib import Path

from psycopg import sql


def apply_schema_migration(conn, path: Path) -> None:
    # Migration content stays unchanged except its public-schema namespace.
    # This also qualifies regclass literals and the migration's ACL targets.
    schema = conn.execute('SELECT current_schema()').fetchone()[0]
    qualifier = sql.Identifier(schema).as_string(conn) + '.'
    conn.execute(path.read_text().replace('public.', qualifier))


def apply_stage_verification_migration(conn, *tables: str) -> None:
    """Apply 1376 verbatim for the stage tables this minimal fixture defines.

    Full production migrations reference six tables; focused storage fixtures
    deliberately construct only their own tables. Keep the real CHECK and
    nullable/no-default semantics, including its column comment.
    """
    import re
    path = Path(__file__).resolve().parents[4] / 'supabase/migrations/1376_k7_stage_verification_status.sql'
    body = path.read_text()
    schema = conn.execute('SELECT current_schema()').fetchone()[0]
    qualifier = sql.Identifier(schema).as_string(conn) + '.'
    for table in tables:
        # A semicolon inside a SQL string is not a statement terminator (the
        # real migration's column comment contains one). Preserve quoted text,
        # including SQL's doubled-quote escape, when selecting each statement.
        statements = re.findall(
            rf"^(?:ALTER TABLE public\.{re.escape(table)}\b|COMMENT ON COLUMN public\.{re.escape(table)}\.)"
            r"(?:'(?:(?:'')|[^'])*'|[^;'])*;",
            body, re.MULTILINE,
        )
        assert len(statements) == 2, f"K7 migration statements missing for {table}"
        for statement in statements:
            conn.execute(statement.replace('public.', qualifier))
