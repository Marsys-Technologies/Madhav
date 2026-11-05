# FAIL fixture: a JOIN read, and an exemption comment that is NOT valid (it names Rahu).
_SQL = """
SELECT c.id, e.tropical_longitude
FROM charts c
JOIN ephemeris_daily e ON e.date = c.birth_date
"""
# node-agnostic: reads Rahu as well, which is exactly why this marker is invalid
_SQL2 = "SELECT date, body FROM ephemeris_daily WHERE date = %s"
