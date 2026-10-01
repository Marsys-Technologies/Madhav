# FAIL fixture (multi-formula rule): `formula_id IS NOT NULL` mentions the column in the WHERE but pins
# NOTHING -- both the canonical and the variant row satisfy it. A pin is an equality / IN.
def yogi_longitude(conn, chart_id):
    cur = conn.cursor()
    cur.execute(
        """SELECT fact_value_num FROM chart_facts
           WHERE chart_id=%s AND fact_category='esoteric_point_yogi' AND fact_key='longitude_sidereal'
             AND formula_id IS NOT NULL""",
        [chart_id],
    )
    return cur.fetchone()
