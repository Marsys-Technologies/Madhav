-- FAIL fixture: an operator script that reads node rows with no pin.
SELECT body, COUNT(*) AS n
FROM ephemeris_daily
GROUP BY body;
