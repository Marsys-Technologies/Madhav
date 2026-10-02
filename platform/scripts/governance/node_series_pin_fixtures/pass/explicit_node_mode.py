# PASS fixture: an explicit NULL-safe node_mode predicate in the statement.
Q = """
SELECT date, body, tropical_longitude
FROM ephemeris_daily
WHERE ayanamsha_id = 'tropical'
  AND (body NOT IN ('Rahu', 'Ketu') OR node_mode = 'true')
ORDER BY body, date
"""
Q2 = "SELECT date FROM ephemeris_daily WHERE body = 'Rahu' AND node_mode = %s AND date = %s"
Q3 = "SELECT date FROM ephemeris_daily WHERE COALESCE(node_mode, 'true') = 'true'"
