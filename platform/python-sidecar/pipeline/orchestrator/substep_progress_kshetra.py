"""Kshetra ledger queries on a borrowed Build cursor.

Candidate callers supply a cursor that already scopes the generation. Build
owns the surrounding transaction.
"""


def _progress_rows(cur) -> list[dict]:
    rows = cur.fetchall()
    if not rows:
        return []
    if isinstance(rows[0], dict):
        return [dict(row) for row in rows]
    columns = [column[0] for column in cur.description]
    return [dict(zip(columns, row)) for row in rows]


def list_substep_keys(cur, *, chart_id: str, asset_id: str) -> list[str]:
    """Read step keys through the cursor already scoped by the caller."""
    cur.execute(
        'SELECT substep_key FROM build_substep_progress '
        'WHERE chart_id = %s AND asset_id = %s',
        (chart_id, asset_id),
    )
    return [row['substep_key'] for row in _progress_rows(cur)]


def list_substep_fingerprints(
    cur, *, chart_id: str, asset_id: str,
) -> list[tuple[str, str]]:
    """Read key and fingerprint pairs for the caller's resume decision."""
    cur.execute(
        'SELECT substep_key, build_fingerprint FROM build_substep_progress '
        'WHERE chart_id = %s AND asset_id = %s',
        (chart_id, asset_id),
    )
    return [(row['substep_key'], row['build_fingerprint']) for row in _progress_rows(cur)]


def delete_substep_progress(cur, *, chart_id: str, asset_id: str) -> None:
    """Clear the scoped ledger in the same transaction as the caller's reset."""
    cur.execute(
        'DELETE FROM build_substep_progress WHERE chart_id = %s AND asset_id = %s',
        (chart_id, asset_id),
    )


def upsert_substep_progress(
    cur, *, chart_id: str, asset_id: str, substep_key: str,
    build_fingerprint: str, rows_written: int,
) -> None:
    """Record one step through the caller-owned cursor."""
    cur.execute(
        """INSERT INTO build_substep_progress
                       (chart_id, asset_id, substep_key, build_fingerprint,
                        rows_written, completed_at)
                   VALUES (%s,%s,%s,%s,%s, now())
                   ON CONFLICT (chart_id, asset_id, substep_key) DO UPDATE SET
                       build_fingerprint = EXCLUDED.build_fingerprint,
                       rows_written = EXCLUDED.rows_written,
                       completed_at = EXCLUDED.completed_at""",
        (chart_id, asset_id, substep_key, build_fingerprint, rows_written),
    )
