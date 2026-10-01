# PASS fixture (multi-formula rule): every UNION branch pins its own formula_id.
def both(conn, chart_id):
    cur = conn.cursor()
    cur.execute(
        """SELECT fact_value_num FROM chart_facts
             WHERE chart_id=%s AND fact_category='esoteric_point_yogi' AND fact_key='longitude_sidereal'
               AND formula_id='bphs_93_20'
           UNION ALL
           SELECT fact_value_num FROM chart_facts
             WHERE chart_id=%s AND fact_category='esoteric_point_avayogi' AND fact_key='longitude_sidereal'
               AND formula_id='bphs_93_20'""",
        [chart_id, chart_id],
    )
    return cur.fetchall()
