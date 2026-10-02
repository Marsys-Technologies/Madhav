# FAIL fixture: node_mode only in GROUP BY / the select list is not a pin (the read still returns both series).
Q = "SELECT body, node_mode, count(*) FROM ephemeris_daily GROUP BY body, node_mode"
