"""Read-only capability probe for protected migration 1376.

Call once per writer invocation/substep, then reuse the boolean for its rows.
Resolve the same relation as unqualified DML (including isolated test schemas).
No failed-column statement or transaction rollback is needed.
"""


def has_stored_verification(cursor, table: str) -> bool:
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM pg_attribute
            WHERE attrelid = to_regclass(%s)
              AND attname = 'verification_pass_status'
              AND attnum > 0 AND NOT attisdropped
        ) AS present
    """, (table,))
    row = cursor.fetchone()
    if row is None:     # no answer (e.g. a test double) is not proof the column exists: honest absent
        return False
    return bool(row['present'] if isinstance(row, dict) else row[0])
