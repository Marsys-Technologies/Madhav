# FAIL fixture (multi-formula rule): reads a declared multi-formula category pinned by
# fact_category AND fact_key (so the older fact_key rule is satisfied) but with no formula_id pin and
# no all-variants disclosure. ga_sensitive writes one row per formula_id for esoteric_point_yogi, so
# which row `fetchone()` returns is physical-order dependent -- the exact defect of
# INVESTIGATION_L1_DUPLICATE_KEYS_v1_0.md.
def yogi_longitude(conn, chart_id, ayanamsha_id):
    cur = conn.cursor()
    cur.execute(
        """SELECT fact_value_num FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s
             AND fact_category='esoteric_point_yogi' AND fact_key='longitude_sidereal'""",
        [chart_id, ayanamsha_id],
    )
    return cur.fetchone()
