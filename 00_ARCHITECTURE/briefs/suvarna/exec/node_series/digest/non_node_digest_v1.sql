-- non_node_digest v1: the same preimage and formatting over the seven NON-node bodies (node_mode IS NULL). Used by the step-2 account
-- ("non-node rows byte-identical before and after"). node_mode is NULL on these rows, so it is written as the marker '~' (concat_ws would
-- otherwise drop the field and shift the rest). No bind.
SELECT count(*) AS n_rows,
       encode(sha256(convert_to(
         'non_node_digest_v1' || E'\n' ||
         string_agg(
           concat_ws('|',
             ayanamsha_id,
             body,
             to_char(date, 'YYYY-MM-DD'),
             coalesce(node_mode, '~'),
             round(tropical_longitude, 9)::text,
             round(speed_dps, 9)::text,
             CASE WHEN is_retrograde THEN '1' ELSE '0' END),
           E'\n'
           ORDER BY ayanamsha_id COLLATE "C", body COLLATE "C", date),
         'UTF8')), 'hex') AS non_node_digest
FROM public.ephemeris_daily
WHERE node_mode IS NULL
  AND body NOT IN ('Rahu', 'Ketu');
