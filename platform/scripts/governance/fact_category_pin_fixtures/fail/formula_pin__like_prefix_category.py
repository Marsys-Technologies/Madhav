# FAIL fixture (multi-formula rule): `LIKE 'esoteric_point_%'` reads six declared categories without
# spelling any of them, so a literal-only scan is blind to it.
def all_esoteric(conn, chart_id):
    cur = conn.cursor()
    cur.execute(
        """SELECT fact_subject, fact_value_num FROM chart_facts
           WHERE chart_id=%s AND fact_category LIKE 'esoteric_point_%%' AND fact_key='longitude_sidereal'""",
        [chart_id],
    )
    return cur.fetchall()
