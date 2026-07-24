"""
dispatch_sarva_siddhi_cr66_cr73_rebuild.py — SARVA-SIDDHI Stage-2 data-refresh rebuild.

PR #739 (CR-66, ph_nimitta phala-anchor bugs) and PR #735 (CR-73, ga_structural's
_cancel_kemadruma kendra-support bhaṅga fix) are both CODE-CLOSED, DATA-PENDING per
PRE_DARPANA_READINESS_v2_0.md: the fixes are merged + deployed but chart 482012f1's
production tables (phala_anchors, dosha_label) still reflect the pre-fix writer output.
Both are pure data-refresh, zero new code.

TARGET_ASSETS below is the exact transitive-dependents closure of {ga_structural,
ph_nimitta} computed LIVE this session via a recursive CTE over
asset_registry.depends_on (WITH RECURSIVE dependents AS (... WHERE d.asset_id =
ANY(ar.depends_on))) — 49 assets spanning ganita/bodha/kala/phala/mimamsa. Confirmed
this closure does NOT include ka_gochara_sweep (T-2 stays independent, per the
native's Stage-2/Stage-4 split — this is deliberately the SMALL rebuild, not the
~23.5h gochara materialization).

Follows the D-1.5b/D-2/D-3 precedent scripts in this directory: a brief local
Cloud SQL Auth Proxy session for the quick multi-row INSERT ONLY, then dispatch via
`gcloud run jobs execute brahma-build-pipeline-job --args=--run-id,<id>` separately.
Abhisek's chart (482012f1) ONLY.

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_sarva_siddhi_cr66_cr73_rebuild.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from collections import deque

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sarva-siddhi-stage2-cr66-cr73-rebuild"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# Exact closure computed live 2026-07-24 from asset_registry.depends_on via a
# recursive CTE seeded at {ga_structural, ph_nimitta}. 49 assets.
TARGET_ASSETS = [
    "ga_structural", "ga_sade_sati", "ga_vichara", "ga_yoga",
    "bo_anveshana", "bo_arudha", "bo_bimba", "bo_cdlm_summary", "bo_cgm_motifs",
    "bo_cgm_paths", "bo_chart_gestalt", "bo_drishti", "bo_karanajala", "bo_laksana",
    "bo_laksana_rerank", "bo_pramana_mapa", "bo_pratijna", "bo_samskara",
    "bo_samvada", "bo_sangati", "bo_upaya", "bo_yantra_mechanism",
    "ka_avadhi", "ka_bhavishya_lekha", "ka_jivana_parva", "ka_kala_darshana",
    "ka_kalasutra", "ka_sangam", "ka_taranga", "ka_tulana", "ka_vighnakara",
    "ka_yojaka",
    "ph_muhurta", "ph_nimitta", "ph_phaladesa", "ph_pramana", "ph_pratikara",
    "ph_rectification", "ph_sankrama", "ph_sodhana", "ph_suddha_sodhana",
    "mi_abhilekha", "mi_adhilepa", "mi_bhavisya", "mi_darshana", "mi_gunanaka",
    "mi_pariksha", "mi_pramana", "mi_sambandha", "mi_seva",
]


def _topo_sort(cur, targets: list[str]) -> list[str]:
    target_set = set(targets)
    cur.execute(
        "SELECT asset_id, COALESCE(depends_on, '{}') AS deps FROM asset_registry "
        "WHERE asset_id = ANY(%s)",
        (list(target_set),),
    )
    rows = cur.fetchall()
    found = {r["asset_id"] for r in rows}
    missing = target_set - found
    if missing:
        raise RuntimeError(f"asset_registry missing rows for: {sorted(missing)}")
    deps = {r["asset_id"]: [d for d in (r["deps"] or []) if d in target_set] for r in rows}

    in_degree = {a: 0 for a in target_set}
    edges: dict[str, list[str]] = {a: [] for a in target_set}
    for a in target_set:
        for dep in deps.get(a, []):
            edges[dep].append(a)
            in_degree[a] += 1

    queue = deque(sorted(a for a in target_set if in_degree[a] == 0))
    ordered: list[str] = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for nxt in sorted(edges[node]):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)
    if len(ordered) != len(target_set):
        raise RuntimeError(f"cycle/unresolved among target assets: {target_set - set(ordered)}")
    return ordered


def main() -> None:
    import psycopg
    import psycopg.rows

    database_url = os.environ["DATABASE_URL"]
    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    assets = _topo_sort(cur, TARGET_ASSETS)

    cur.execute(
        "SELECT asset_id, scope FROM asset_registry WHERE asset_id = ANY(%s)",
        (assets,),
    )
    scope_by_id = {r["asset_id"]: r["scope"] for r in cur.fetchall()}

    for asset_id in assets:
        if scope_by_id[asset_id] == "global":
            cur.execute(
                """INSERT INTO asset_throughput (chart_id, asset_id, state)
                   VALUES (NULL, %s, 'dormant')
                   ON CONFLICT (asset_id) WHERE chart_id IS NULL
                   DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
                (asset_id,),
            )
        else:
            cur.execute(
                """INSERT INTO asset_throughput (chart_id, asset_id, state)
                   VALUES (%s, %s, 'dormant')
                   ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
                   DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
                (CHART_ID, asset_id),
            )

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'rebuild', %s, 'planned', %s)""",
        (run_id, CHART_ID, json.dumps(assets), TRIGGERED_BY),
    )
    for position, asset_id in enumerate(assets):
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, %s, 'queued')""",
            (run_id, asset_id, position),
        )
    conn.commit()
    conn.close()
    print(f"[dispatch] created SARVA-SIDDHI CR-66/CR-73 rebuild build_run {run_id} with {len(assets)} assets: {assets}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
