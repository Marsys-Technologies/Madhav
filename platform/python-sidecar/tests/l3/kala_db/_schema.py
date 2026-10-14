"""Apply the actual migration to the test connection's isolated schema."""
from pathlib import Path

from psycopg import sql


def apply_schema_migration(conn, path: Path) -> None:
    # Migration content stays unchanged except its public-schema namespace.
    # This also qualifies regclass literals and the migration's ACL targets.
    schema = conn.execute('SELECT current_schema()').fetchone()[0]
    qualifier = sql.Identifier(schema).as_string(conn) + '.'
    conn.execute(path.read_text().replace('public.', qualifier))
