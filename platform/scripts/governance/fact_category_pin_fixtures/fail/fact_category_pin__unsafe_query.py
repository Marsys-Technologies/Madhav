# Fixture: reproduces the exact D1-class defect (brief §5 C.7 / the bo_laksana
# P0-5 bug) — a chart_facts selection scoped only by fact_category, with no
# fact_key pin and no deterministic ORDER BY + LIMIT 1 to reduce the set. If
# chart_facts ever holds more than one row for this (chart_id, ayanamsha_id,
# fact_category) tuple, which row callers see is undefined.
def _build_strength_lookup(conn, chart_id, ayanamsha_id):
    rows = _fetch_dict(
        conn,
        """SELECT fact_subject, fact_value_num FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s AND fact_category='graha_shadbala_total'""",
        [chart_id, ayanamsha_id],
    )
    return rows
