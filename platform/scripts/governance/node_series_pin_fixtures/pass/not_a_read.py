"""Docstring prose: this module reads from ephemeris_daily to select positions. (select ... from ephemeris_daily is prose here.)"""
# comment: SELECT date FROM ephemeris_daily is just a comment
INSERT_SQL = """
INSERT INTO ephemeris_daily (date, body, ayanamsha_id, node_mode, tropical_longitude)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (date, body, ayanamsha_id, node_mode) DO NOTHING
"""
DELETE_SQL = "DELETE FROM ephemeris_daily WHERE date < %s"
UPDATE_SQL = "UPDATE ephemeris_daily SET speed_dps = 0 WHERE date = %s"
DELETE_SUB = "DELETE FROM ephemeris_daily WHERE date = (SELECT min(d) FROM other_table)"
