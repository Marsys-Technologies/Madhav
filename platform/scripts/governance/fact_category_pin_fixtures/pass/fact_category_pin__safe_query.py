# Fixture: the corrected form — fact_category is scoped further by a
# fact_key pin AND the set is reduced with a deterministic ORDER BY + LIMIT 1.
# This must NOT be flagged (precision check — the lint must not cry wolf on
# correct code).
def _load_dignity_state(conn, chart_id, ayanamsha_id, graha):
    rows = _fetch_dict(
        conn,
        """SELECT fact_value_text FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s
             AND fact_category='graha_dignity_per_varga'
             AND fact_key='dignity_state'
             AND fact_subject=%s
           ORDER BY verified_at DESC
           LIMIT 1""",
        [chart_id, ayanamsha_id, graha],
    )
    return rows[0] if rows else None
