import json, sys
from _db import conn
Q = {}
Q['now'] = "SELECT now() AS now"
Q['at_state_dist'] = "SELECT state, count(*) AS n FROM asset_throughput GROUP BY state ORDER BY state"
Q['at_total'] = "SELECT count(*) AS n FROM asset_throughput"
Q['orphans'] = """SELECT asset_id, chart_id::text, state, last_built_at::text, rows_written, last_error
FROM asset_throughput
WHERE state IN ('dormant','building')
  AND (last_built_at IS NULL OR last_built_at < now() - interval '24 hours')
ORDER BY asset_id"""
Q['inactive_rows'] = """SELECT t.asset_id, t.chart_id::text, t.state, r.is_active, r.catalog_status
FROM asset_throughput t JOIN asset_registry r ON r.asset_id=t.asset_id
WHERE r.is_active IS DISTINCT FROM true ORDER BY t.asset_id, t.chart_id"""
Q['reg_total'] = "SELECT count(*) AS n FROM asset_registry"
Q['est_notnull'] = "SELECT count(*) AS n FROM asset_registry WHERE estimated_seconds IS NOT NULL"
Q['est_null'] = "SELECT count(*) AS n FROM asset_registry WHERE estimated_seconds IS NULL"
Q['t5_affected'] = """WITH d AS (
  SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at)) AS secs
  FROM build_run_assets WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL
), s AS (SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs) AS m FROM d GROUP BY asset_id)
SELECT count(*) AS n FROM asset_registry r JOIN s ON s.asset_id=r.asset_id
WHERE r.estimated_seconds IS DISTINCT FROM ceil(s.m)::int"""
Q['t5_computable'] = """WITH d AS (
  SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at)) AS secs
  FROM build_run_assets WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL
), s AS (SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs) AS m FROM d GROUP BY asset_id)
SELECT count(*) AS n FROM asset_registry r JOIN s ON s.asset_id=r.asset_id"""
Q['t5_no_run'] = """WITH d AS (
  SELECT asset_id FROM build_run_assets WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL GROUP BY asset_id)
SELECT count(*) AS n FROM asset_registry r LEFT JOIN d ON d.asset_id=r.asset_id WHERE d.asset_id IS NULL"""
Q['t5_null_and_measurable'] = """WITH d AS (
  SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at)) AS secs
  FROM build_run_assets WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL
), s AS (SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs) AS m FROM d GROUP BY asset_id)
SELECT count(*) AS n FROM asset_registry r JOIN s ON s.asset_id=r.asset_id WHERE r.estimated_seconds IS NULL"""
Q['t5_stored_and_diff'] = """WITH d AS (
  SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at)) AS secs
  FROM build_run_assets WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL
), s AS (SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs) AS m FROM d GROUP BY asset_id)
SELECT count(*) AS n FROM asset_registry r JOIN s ON s.asset_id=r.asset_id
WHERE r.estimated_seconds IS NOT NULL AND r.estimated_seconds IS DISTINCT FROM ceil(s.m)::int"""
Q['t3'] = """SELECT count(*) AS n FROM build_run_assets a JOIN build_runs r ON r.id=a.run_id
WHERE a.state='queued' AND r.state IN ('completed','failed','stopped')"""
Q['t4_derivable'] = """SELECT count(*) AS n FROM build_runs r WHERE r.ended_at IS NULL AND r.state IN ('completed','failed','stopped')
 AND EXISTS (SELECT 1 FROM build_run_assets a WHERE a.run_id=r.id AND a.ended_at IS NOT NULL)"""
Q['t4_not'] = """SELECT count(*) AS n FROM build_runs r WHERE r.ended_at IS NULL AND r.state IN ('completed','failed','stopped')
 AND NOT EXISTS (SELECT 1 FROM build_run_assets a WHERE a.run_id=r.id AND a.ended_at IS NOT NULL)"""
Q['run_states'] = "SELECT state, count(*) AS n FROM build_runs GROUP BY state ORDER BY state"
Q['bra_states'] = "SELECT state, count(*) AS n FROM build_run_assets GROUP BY state ORDER BY state"
Q['nonterminal_runs'] = "SELECT count(*) AS n FROM build_runs WHERE state NOT IN ('completed','failed','stopped')"
Q['stored_9'] = """WITH d AS (
  SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at)) AS secs
  FROM build_run_assets WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL
), s AS (SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs) AS m, count(*) AS runs FROM d GROUP BY asset_id)
SELECT r.asset_id, r.estimated_seconds AS stored, s.runs, round(s.m::numeric,2) AS median_s, ceil(s.m)::int AS proposed
FROM asset_registry r JOIN s ON s.asset_id=r.asset_id WHERE r.estimated_seconds IS NOT NULL ORDER BY r.asset_id"""
out={}
with conn() as c:
    cur=c.cursor()
    for k,q in Q.items():
        cur.execute(q); out[k]=cur.fetchall()
print(json.dumps(out, indent=1, default=str))
