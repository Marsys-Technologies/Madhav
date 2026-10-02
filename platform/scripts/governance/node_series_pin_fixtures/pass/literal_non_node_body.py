# PASS fixture: a statement that provably cannot return a node row.
Q = "SELECT tropical_longitude FROM ephemeris_daily WHERE body = 'Saturn' AND date = %s LIMIT 1"
Q2 = "SELECT body, date FROM ephemeris_daily WHERE body IN ('Sun', 'Moon', 'Mars') AND date = %s"
Q3 = "SELECT date FROM ephemeris_daily WHERE body NOT IN ('Rahu', 'Ketu') AND date = %s"
Q4 = "SELECT date FROM ephemeris_daily LIMIT 0"
