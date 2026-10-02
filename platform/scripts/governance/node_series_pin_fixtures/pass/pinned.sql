-- PASS fixture: pinned, exempt-by-comment and comment-only mentions.
-- SELECT * FROM ephemeris_daily;   (only a comment)
SELECT body, node_mode, COUNT(*) AS n
FROM ephemeris_daily
GROUP BY body, node_mode;

-- node-agnostic: counts all rows as a floor check, no node value is read
SELECT COUNT(*) FROM ephemeris_daily;

SELECT date FROM ephemeris_daily WHERE body = 'Sun' AND date = '2000-01-01';
