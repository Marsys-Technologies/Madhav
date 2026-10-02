-- node_series_digest v1 (the ONE definition; L0-owned; Pravaha reuses it VERBATIM as the upstream identity of a node series).
-- sha256 over the Rahu + Ketu rows of ONE node_mode of public.ephemeris_daily.
--   bind     node_mode = 'mean' | 'true'      psql: psql -v node_mode=mean -f node_series_digest_v1.sql   (the file uses :'node_mode')
--            a driver binds the same value in place of :'node_mode' (e.g. %(node_mode)s / $1); nothing else is parameterised.
--   preimage 'node_series_digest_v1' LF, then one line per row, rows ordered by (ayanamsha_id, body, date) under COLLATE "C",
--            lines joined by LF (no trailing LF), fields joined by '|', in this order:
--              ayanamsha_id | body | date as YYYY-MM-DD | node_mode | round(tropical_longitude, 9)::text | round(speed_dps, 9)::text | 1 or 0
--            numerics are the stored values rounded half away from zero to 9 decimals and printed by numeric::text with exactly 9
--            decimals (no locale, no float repr); is_retrograde is 1/0. UTF-8, sha256, lowercase hex.
--   columns  the key (date, body, ayanamsha_id, node_mode) plus tropical_longitude, speed_dps, is_retrograde: the position series.
--            sign_number, degree_in_sign, nakshatra_number are DERIVED from the longitude and stay OUT; latitude (0 on every node row),
--            epoch_convention (constant), source_citation, computed_at and id are provenance/bookkeeping and stay OUT.
--   result   n_rows, node_series_digest; the digest is NULL when the series has no row ("absent", never the hash of nothing).
--   moves on any change to a row of THIS series (a longitude or speed at the 6th decimal, a flag flip, a row added/removed/re-keyed);
--   does NOT move when non-node rows change, when the other node_mode's rows are present or change, or with insertion order.
SELECT count(*) AS n_rows,
       encode(sha256(convert_to(
         'node_series_digest_v1' || E'\n' ||
         string_agg(
           concat_ws('|',
             ayanamsha_id,
             body,
             to_char(date, 'YYYY-MM-DD'),
             node_mode,
             round(tropical_longitude, 9)::text,
             round(speed_dps, 9)::text,
             CASE WHEN is_retrograde THEN '1' ELSE '0' END),
           E'\n'
           ORDER BY ayanamsha_id COLLATE "C", body COLLATE "C", date),
         'UTF8')), 'hex') AS node_series_digest
FROM public.ephemeris_daily
WHERE node_mode = :'node_mode'
  AND body IN ('Rahu', 'Ketu');
