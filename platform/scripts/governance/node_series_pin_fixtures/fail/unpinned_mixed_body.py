# FAIL fixture: a literal non-node body constraint BESIDE a parameterised one still reaches Rahu/Ketu.
Q = "SELECT date, body FROM ephemeris_daily WHERE body = 'Sun' OR body = ANY(%s)"
