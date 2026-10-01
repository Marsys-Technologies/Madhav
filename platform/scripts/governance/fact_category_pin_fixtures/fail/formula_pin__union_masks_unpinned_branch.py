# FAIL fixture (multi-formula rule): the SECOND UNION branch is pinned, the FIRST is not. Every branch
# is judged on its own; one pinned branch must not mask an unpinned one.
def both(conn, chart_id):
    cur = conn.cursor()
    cur.execute(
        """SELECT fact_value_num FROM chart_facts
             WHERE chart_id=%s AND fact_category='esoteric_point_yogi' AND fact_key='longitude_sidereal'
           UNION ALL
           SELECT fact_value_num FROM chart_facts
             WHERE chart_id=%s AND fact_category='esoteric_point_avayogi' AND fact_key='longitude_sidereal'
               AND formula_id='bphs_93_20'""",
        [chart_id, chart_id],
    )
    return cur.fetchall()
