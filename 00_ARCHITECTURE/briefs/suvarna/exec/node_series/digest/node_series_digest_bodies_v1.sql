-- node_series_digest_bodies v1: the SAME preimage and formatting as node_series_digest_v1.sql, restricted to the bodies in `bodies`
-- (for the step-2 account, e.g. TRUE Rahu alone, TRUE Ketu alone). With bodies = '{Rahu,Ketu}' it returns exactly node_series_digest_v1.
--   bind  node_mode = 'mean' | 'true';  bodies = a text[] literal, e.g. psql -v node_mode=true -v bodies='{Rahu}' -f ...
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
  AND body IN ('Rahu', 'Ketu')
  AND body = ANY(:'bodies'::text[]);
