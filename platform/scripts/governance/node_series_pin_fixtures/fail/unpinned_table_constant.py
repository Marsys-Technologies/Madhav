# FAIL fixture: the table is named through a file-level constant (the Pravaha readers' style); no pin.
EPHEMERIS_TABLE = "ephemeris_daily"


def read_many(cur, bodies):
    sql = (
        f"SELECT body, date, tropical_longitude FROM {EPHEMERIS_TABLE} "
        f"WHERE ayanamsha_id = %s AND body = ANY(%s)"
    )
    cur.execute(sql, ["tropical", list(bodies)])
    return cur.fetchall()
