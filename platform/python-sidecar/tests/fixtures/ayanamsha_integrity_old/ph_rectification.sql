
-- D-CND-03: every clause partitions on chart_id already -- the scan lattice is a per-chart
-- structure, so a defect in one chart's lattice cannot be masked by another's.
SELECT
  -- Contiguous, gap-free offset lattice at the declared step.
  NOT EXISTS (SELECT 1 FROM (
     SELECT chart_id, offset_minutes,
            lead(offset_minutes) OVER (PARTITION BY chart_id ORDER BY offset_minutes) nx
     FROM (SELECT DISTINCT chart_id, offset_minutes FROM phala_rectification) o) g
    WHERE nx IS NOT NULL AND nx - offset_minutes <> 5
    GROUP BY chart_id HAVING count(*) > 0)
  -- Symmetric and centred on the recorded birth time.
  AND NOT EXISTS (SELECT 1 FROM phala_rectification
     GROUP BY chart_id HAVING min(offset_minutes) <> -max(offset_minutes) OR NOT bool_or(offset_minutes = 0))
  -- Complete cross-product: every offset scored under every ayanamsha.
  AND NOT EXISTS (SELECT 1 FROM (SELECT chart_id, offset_minutes FROM phala_rectification
        GROUP BY 1,2 HAVING count(DISTINCT ayanamsha_id) <> 5) x
     GROUP BY chart_id HAVING count(*) > 0)
  -- lagna_stable is an all-or-nothing property of an offset across ayanamshas.
  AND NOT EXISTS (SELECT 1 FROM (SELECT chart_id, offset_minutes FROM phala_rectification
        GROUP BY 1,2 HAVING count(DISTINCT lagna_stable) > 1) x
     GROUP BY chart_id HAVING count(*) > 0)
  -- The best row must resolve to a real candidate of its OWN chart.
  AND NOT EXISTS (SELECT 1 FROM phala_rectification_best b WHERE b.best_candidate_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM phala_rectification c
             WHERE c.id = b.best_candidate_id AND c.chart_id = b.chart_id)
     GROUP BY b.chart_id HAVING count(*) > 0)
