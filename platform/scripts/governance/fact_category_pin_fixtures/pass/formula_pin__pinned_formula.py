# PASS fixture (multi-formula rule): the same read as fail/formula_pin__unpinned_declared_category.py,
# pinned to the canonical formula. ga_structural's karaka-web reader has exactly this shape.
def yogi_longitude(conn, chart_id, ayanamsha_id):
    cur = conn.cursor()
    cur.execute(
        """SELECT fact_value_num FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id=%s
             AND fact_category='esoteric_point_yogi' AND fact_key='longitude_sidereal'
             AND formula_id='bphs_93_20'""",
        [chart_id, ayanamsha_id],
    )
    return cur.fetchone()
