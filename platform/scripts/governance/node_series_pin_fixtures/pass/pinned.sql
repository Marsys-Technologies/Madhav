-- PASS fixture: pinned (WHERE node_mode), exempt-by-marker and comment-only mentions.
-- SELECT * FROM ephemeris_daily;   (only a comment)
SELECT body, count(*) AS n
FROM ephemeris_daily
WHERE node_mode = 'true'
GROUP BY body;

-- node-agnostic: count_only_table_level: counts all rows as a floor check, no node value is read
SELECT COUNT(*) FROM ephemeris_daily;

SELECT date FROM ephemeris_daily WHERE body = 'Sun' AND date = '2000-01-01';
