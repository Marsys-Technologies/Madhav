# PASS fixture: a documented exemption comment (reason of 12+ characters, does not name Rahu/Ketu).
def planets_only(cur, body, d):
    # node-agnostic: callers pass only the seven classical grahas (enum-restricted upstream)
    cur.execute("SELECT tropical_longitude FROM ephemeris_daily WHERE body = %s AND date = %s", [body, d])
    return cur.fetchone()


Q_INLINE = """
SELECT date FROM ephemeris_daily WHERE date = %s  -- node-agnostic: seven classical grahas only, via the caller's enum
"""
