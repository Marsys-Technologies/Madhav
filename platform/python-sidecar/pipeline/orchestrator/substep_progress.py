"""Borrowed access to the Sangam partition of Build's substep progress ledger.

The ledger is physically keyed by chart, asset and step. The caller supplies
the fingerprint that identifies its run. Build owns the surrounding transaction.
"""


def load_sangam_completed_substeps(conn, chart_id: str, fingerprint: str) -> set[str] | None:
    """Return completed keys when every row in the partition matches the fingerprint."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT substep_key, build_fingerprint FROM build_substep_progress "
            "WHERE chart_id = %s AND asset_id = 'ka_sangam'",
            (chart_id,),
        )
        rows = cur.fetchall()
    if not rows:
        return None
    if {r['build_fingerprint'] for r in rows} != {fingerprint}:
        return None
    return {r['substep_key'] for r in rows}


def sum_sangam_rows_written(conn, chart_id: str) -> int:
    """Count the output already committed by prior steps in this partition."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(rows_written), 0) AS n FROM build_substep_progress "
            "WHERE chart_id = %s AND asset_id = 'ka_sangam'",
            (chart_id,),
        )
        row = cur.fetchone()
    return int((row['n'] if isinstance(row, dict) else row[0]) or 0)


def clear_sangam_substeps(cur, chart_id: str) -> None:
    """Clear progress alongside the caller's data reset on the same cursor."""
    cur.execute(
        "DELETE FROM build_substep_progress WHERE chart_id = %s AND asset_id = 'ka_sangam'",
        (chart_id,),
    )


def record_sangam_substep(
    conn, chart_id: str, substep_key: str, fingerprint: str, rows: int,
) -> None:
    """Record completion in the same transaction as the step's output."""
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO build_substep_progress
                       (chart_id, asset_id, substep_key, build_fingerprint, rows_written, completed_at)
                   VALUES (%s, 'ka_sangam', %s, %s, %s, now())
                   ON CONFLICT (chart_id, asset_id, substep_key)
                   DO UPDATE SET build_fingerprint = EXCLUDED.build_fingerprint,
                                 rows_written      = EXCLUDED.rows_written,
                                 completed_at      = EXCLUDED.completed_at""",
            (chart_id, substep_key, fingerprint, rows),
        )
