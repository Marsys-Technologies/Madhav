# Fixture: fact_key pinned WITHOUT an ORDER BY/LIMIT — the real, widespread
# `bo_upaya.py` / `ga_structural_writer.py` pattern (verified against the live
# repo tree): fetches one row PER fact_subject (graha) as a subject-keyed
# lookup. fact_key already disambiguates which measurement is read, so this
# is NOT the P0-5/P0-1 defect class and must NOT be flagged.
def _load_shadbala_ratios(conn, chart_id, ayanamsha_id):
    rows = _fetch_dict(
        conn,
        """SELECT fact_subject, fact_value_num FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'graha_shadbala_total' AND fact_key = 'ratio'""",
        [chart_id, ayanamsha_id],
    )
    return {r["fact_subject"]: r["fact_value_num"] for r in rows}
