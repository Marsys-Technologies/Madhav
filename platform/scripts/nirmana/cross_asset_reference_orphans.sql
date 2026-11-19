-- cross_asset_reference_orphans.sql -- READ-ONLY orphan detector for the seven references whose ON DELETE CASCADE
-- foreign keys migration 1260 drops. No DB object: this is a plain SELECT, run by cross_asset_reference_orphans.py
-- (or `psql -f`) as a pre/post check for W7 / S-L3. It never writes and is REPORTED, NEVER BUILD-BLOCKING.
--
-- Statement 1: ALWAYS exactly seven rows (one per reference), so an empty or unreadable child table reads
--   child_rows_with_reference = 0 and a zero orphan_rows is visibly vacuous, never "no row".
-- Statement 2: the same counts per (reference, chart_id), only for charts that have a child row with a reference.
--
-- An orphan is a child row whose referenced parent row does not exist. A parent that exists on a DIFFERENT chart is not
-- reported. A NULL reference is not a reference. Non-vacuity: a zero means something only where
-- child_rows_with_reference > 0 for that reference.
--
-- The seven references (constraint name that 1260 drops | child.column -> parent.column):
--   phala_anchors_convergence_id_fkey         phala_anchors.convergence_id          -> kala_convergence.convergence_id
--   kala_darshana_convergence_id_fkey         kala_darshana.convergence_id          -> kala_convergence.convergence_id
--   kala_obstruction_convergence_id_fkey      kala_obstruction.convergence_id       -> kala_convergence.convergence_id
--   phala_pramana_anchor_id_fkey              phala_pramana.anchor_id               -> phala_anchors.anchor_id
--   phala_sankrama_source_anchor_id_fkey      phala_sankrama.source_anchor_id       -> phala_anchors.anchor_id
--   phala_sodhana_anchor_id_fkey              phala_sodhana.anchor_id               -> phala_anchors.anchor_id
--   phala_suddha_sodhana_anchor_id_fkey       phala_suddha_sodhana.anchor_id        -> phala_anchors.anchor_id

-- STATEMENT 1: summary (seven rows)
WITH refs AS (
  SELECT 'phala_anchors_convergence_id_fkey'::text AS reference_name, 'phala_anchors'::text AS child_table, 'convergence_id'::text AS child_column,
         'kala_convergence'::text AS parent_table, 'convergence_id'::text AS parent_column,
         count(*) FILTER (WHERE c.convergence_id IS NOT NULL) AS child_rows_with_reference,
         count(*) FILTER (WHERE c.convergence_id IS NOT NULL AND p.convergence_id IS NULL) AS orphan_rows,
         count(DISTINCT c.chart_id) FILTER (WHERE c.convergence_id IS NOT NULL AND p.convergence_id IS NULL) AS orphan_chart_count
    FROM phala_anchors c LEFT JOIN kala_convergence p ON p.convergence_id = c.convergence_id
  UNION ALL
  SELECT 'kala_darshana_convergence_id_fkey', 'kala_darshana', 'convergence_id', 'kala_convergence', 'convergence_id',
         count(*) FILTER (WHERE c.convergence_id IS NOT NULL),
         count(*) FILTER (WHERE c.convergence_id IS NOT NULL AND p.convergence_id IS NULL),
         count(DISTINCT c.chart_id) FILTER (WHERE c.convergence_id IS NOT NULL AND p.convergence_id IS NULL)
    FROM kala_darshana c LEFT JOIN kala_convergence p ON p.convergence_id = c.convergence_id
  UNION ALL
  SELECT 'kala_obstruction_convergence_id_fkey', 'kala_obstruction', 'convergence_id', 'kala_convergence', 'convergence_id',
         count(*) FILTER (WHERE c.convergence_id IS NOT NULL),
         count(*) FILTER (WHERE c.convergence_id IS NOT NULL AND p.convergence_id IS NULL),
         count(DISTINCT c.chart_id) FILTER (WHERE c.convergence_id IS NOT NULL AND p.convergence_id IS NULL)
    FROM kala_obstruction c LEFT JOIN kala_convergence p ON p.convergence_id = c.convergence_id
  UNION ALL
  SELECT 'phala_pramana_anchor_id_fkey', 'phala_pramana', 'anchor_id', 'phala_anchors', 'anchor_id',
         count(*) FILTER (WHERE c.anchor_id IS NOT NULL),
         count(*) FILTER (WHERE c.anchor_id IS NOT NULL AND p.anchor_id IS NULL),
         count(DISTINCT c.chart_id) FILTER (WHERE c.anchor_id IS NOT NULL AND p.anchor_id IS NULL)
    FROM phala_pramana c LEFT JOIN phala_anchors p ON p.anchor_id = c.anchor_id
  UNION ALL
  SELECT 'phala_sankrama_source_anchor_id_fkey', 'phala_sankrama', 'source_anchor_id', 'phala_anchors', 'anchor_id',
         count(*) FILTER (WHERE c.source_anchor_id IS NOT NULL),
         count(*) FILTER (WHERE c.source_anchor_id IS NOT NULL AND p.anchor_id IS NULL),
         count(DISTINCT c.chart_id) FILTER (WHERE c.source_anchor_id IS NOT NULL AND p.anchor_id IS NULL)
    FROM phala_sankrama c LEFT JOIN phala_anchors p ON p.anchor_id = c.source_anchor_id
  UNION ALL
  SELECT 'phala_sodhana_anchor_id_fkey', 'phala_sodhana', 'anchor_id', 'phala_anchors', 'anchor_id',
         count(*) FILTER (WHERE c.anchor_id IS NOT NULL),
         count(*) FILTER (WHERE c.anchor_id IS NOT NULL AND p.anchor_id IS NULL),
         count(DISTINCT c.chart_id) FILTER (WHERE c.anchor_id IS NOT NULL AND p.anchor_id IS NULL)
    FROM phala_sodhana c LEFT JOIN phala_anchors p ON p.anchor_id = c.anchor_id
  UNION ALL
  SELECT 'phala_suddha_sodhana_anchor_id_fkey', 'phala_suddha_sodhana', 'anchor_id', 'phala_anchors', 'anchor_id',
         count(*) FILTER (WHERE c.anchor_id IS NOT NULL),
         count(*) FILTER (WHERE c.anchor_id IS NOT NULL AND p.anchor_id IS NULL),
         count(DISTINCT c.chart_id) FILTER (WHERE c.anchor_id IS NOT NULL AND p.anchor_id IS NULL)
    FROM phala_suddha_sodhana c LEFT JOIN phala_anchors p ON p.anchor_id = c.anchor_id
)
SELECT reference_name, child_table, child_column, parent_table, parent_column,
       child_rows_with_reference, orphan_rows, orphan_chart_count
  FROM refs ORDER BY reference_name;

-- STATEMENT 2: per (reference, chart)
SELECT 'phala_anchors_convergence_id_fkey'::text AS reference_name, c.chart_id, count(*) AS child_rows_with_reference,
       count(*) FILTER (WHERE p.convergence_id IS NULL) AS orphan_rows
  FROM phala_anchors c LEFT JOIN kala_convergence p ON p.convergence_id = c.convergence_id
 WHERE c.convergence_id IS NOT NULL GROUP BY c.chart_id
UNION ALL
SELECT 'kala_darshana_convergence_id_fkey', c.chart_id, count(*), count(*) FILTER (WHERE p.convergence_id IS NULL)
  FROM kala_darshana c LEFT JOIN kala_convergence p ON p.convergence_id = c.convergence_id
 WHERE c.convergence_id IS NOT NULL GROUP BY c.chart_id
UNION ALL
SELECT 'kala_obstruction_convergence_id_fkey', c.chart_id, count(*), count(*) FILTER (WHERE p.convergence_id IS NULL)
  FROM kala_obstruction c LEFT JOIN kala_convergence p ON p.convergence_id = c.convergence_id
 WHERE c.convergence_id IS NOT NULL GROUP BY c.chart_id
UNION ALL
SELECT 'phala_pramana_anchor_id_fkey', c.chart_id, count(*), count(*) FILTER (WHERE p.anchor_id IS NULL)
  FROM phala_pramana c LEFT JOIN phala_anchors p ON p.anchor_id = c.anchor_id
 WHERE c.anchor_id IS NOT NULL GROUP BY c.chart_id
UNION ALL
SELECT 'phala_sankrama_source_anchor_id_fkey', c.chart_id, count(*), count(*) FILTER (WHERE p.anchor_id IS NULL)
  FROM phala_sankrama c LEFT JOIN phala_anchors p ON p.anchor_id = c.source_anchor_id
 WHERE c.source_anchor_id IS NOT NULL GROUP BY c.chart_id
UNION ALL
SELECT 'phala_sodhana_anchor_id_fkey', c.chart_id, count(*), count(*) FILTER (WHERE p.anchor_id IS NULL)
  FROM phala_sodhana c LEFT JOIN phala_anchors p ON p.anchor_id = c.anchor_id
 WHERE c.anchor_id IS NOT NULL GROUP BY c.chart_id
UNION ALL
SELECT 'phala_suddha_sodhana_anchor_id_fkey', c.chart_id, count(*), count(*) FILTER (WHERE p.anchor_id IS NULL)
  FROM phala_suddha_sodhana c LEFT JOIN phala_anchors p ON p.anchor_id = c.anchor_id
 WHERE c.anchor_id IS NOT NULL GROUP BY c.chart_id
ORDER BY 1, 2;
