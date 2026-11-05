# FAIL fixture: a read of ephemeris_daily that can return Rahu/Ketu and says nothing about which series.
def read_positions(conn, body, start, end):
    return conn.execute(
        "SELECT date, tropical_longitude FROM ephemeris_daily "
        "WHERE body = %s AND ayanamsha_id = 'tropical' AND date BETWEEN %s AND %s ORDER BY date",
        [body, start, end],
    ).fetchall()
