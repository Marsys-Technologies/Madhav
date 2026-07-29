#!/usr/bin/env python3
"""READ-ONLY: recompute ka_gochara_sweep resume fingerprint from live DB state
and compare to what build_substep_progress stores. Replicates
services/ka_gochara_sweep/writer.py _compute_build_fingerprint / _derive_birth_year
/ _discover_event_classes exactly. Issues SELECTs only."""
import os, hashlib

_env = "/Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env.local"
with open(_env) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

import psycopg, psycopg.rows
conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
conn.read_only = True

_RESUME_VERSION = 7
_N_YEARS = 101
_SCORING_SPAN_END_YEAR = 2027
_PRE_REG = frozenset({"career_advancement", "major_gain", "marriage"})

CHARTS = ["482012f1-710e-4a25-994a-93821f5871aa",
          "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
          "cb73cd3d-9eba-4220-9902-0de91566e980"]

for chart_id in CHARTS:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT event_class FROM gochara_resonance_map "
                    "WHERE chart_id=%s ORDER BY event_class", (chart_id,))
        ecs = [r["event_class"] for r in cur.fetchall()]
        cur.execute("SELECT birth_date FROM public.charts WHERE id=%s OR chart_id=%s "
                    "ORDER BY birth_date NULLS LAST LIMIT 1", (chart_id, chart_id))
        row = cur.fetchone()
        birth_year = row["birth_date"].year if row and row["birth_date"] else None
        cur.execute("SELECT count(*) AS n FROM public.charts WHERE id=%s OR chart_id=%s",
                    (chart_id, chart_id))
        n_chart_rows = cur.fetchone()["n"]
        cur.execute("SELECT DISTINCT build_fingerprint FROM build_substep_progress "
                    "WHERE chart_id=%s AND asset_id='ka_gochara_sweep'", (chart_id,))
        stored = [r["build_fingerprint"] for r in cur.fetchall()]
        cur.execute("SELECT count(*) AS n FROM build_substep_progress "
                    "WHERE chart_id=%s AND asset_id='ka_gochara_sweep'", (chart_id,))
        done = cur.fetchone()["n"]

    parts = [f"v={_RESUME_VERSION}", f"chart={chart_id}",
             f"birth_year={birth_year}", f"event_classes={','.join(sorted(ecs))}"]
    fp = hashlib.sha256("|".join(parts).encode()).hexdigest()

    plan = len(ecs) * _N_YEARS
    # tier arithmetic (scheduling only)
    span_years = max(0, _SCORING_SPAN_END_YEAR - birth_year + 1) if birth_year else 0
    print(f"chart={chart_id[:8]}  public.charts_matches={n_chart_rows}  birth_year={birth_year}")
    print(f"  event_classes={ecs}")
    print(f"  plan={len(ecs)}x{_N_YEARS}={plan}  committed={done}  pct={done/plan*100:.1f}%")
    print(f"  recomputed_fp={fp[:16]}...  stored_fp={[s[:16]+'...' for s in stored]}")
    print(f"  RESUME_WOULD={'RESUME (fp match)' if stored==[fp] else 'REPLAN-ALL / WIPE (fp mismatch)'}")
    print(f"  scoring_span_end={_SCORING_SPAN_END_YEAR} -> tier1 covers year_idx 0..{span_years-1} "
          f"({span_years} yrs); tier3 (forward span) = {_N_YEARS-span_years} yrs/class")
    print(f"  hardcoded specimen year_idx: major_gain {2010-birth_year},{2011-birth_year}; "
          f"marriage {2013-birth_year}" if birth_year else "")
    print()
conn.close()
