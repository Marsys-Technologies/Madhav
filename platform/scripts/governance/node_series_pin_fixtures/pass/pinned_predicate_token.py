# PASS fixture: the Pravaha style: NODE_SERIES_PREDICATE spliced into an f-string split across adjacent literals.
from services.w2g.node_series import NODE_SERIES_PREDICATE

EPHEMERIS_TABLE = "ephemeris_daily"


def read(cur, body):
    sql = (
        f"SELECT date, tropical_longitude FROM {EPHEMERIS_TABLE} "
        f"WHERE body = %s AND ayanamsha_id = %s AND {NODE_SERIES_PREDICATE}"
    )
    cur.execute(sql, [body, "tropical"])
    return cur.fetchall()
