"""
dispatch_d2_cycle1_rebuild_job.py — D-2 cycle-1's scope-limited REBUILD.

Per BIND_D-2.md §B.10 / STATE_D-2.md's rebuild_scope_ruling: the exact 58-asset
closure computed live from asset_registry.depends_on, seeded from this cycle's
actually-changed writers (bg_vidhi_primitives, bg_vidhi_floors, bo_karanajala,
bo_laksana, ka_yojaka, ga_structural, ga_dashas, bo_yantra_mechanism,
bo_laksana_rerank, bo_nakshatra_semantic, bo_arudha, bo_special_lagna,
bo_vargottama_dhana). asset_set scope, action='rebuild' (force every listed
asset back to 'dormant' regardless of current 'lit' state, per the D-1.5b/D-1.6
precedent scripts in this directory). Abhisek's chart (482012f1) ONLY;
Abhinandan is never rebuilt by this campaign.

Uses the already-running local Cloud SQL Auth Proxy (127.0.0.1:5433) for THIS
QUICK INSERT ONLY — per O8_LOCAL_PROXY_KILL_ROOT_CAUSE_v1_0.md, the proxy is
unreliable for LONG-RUNNING connections (e.g. bo_samskara's embedding loop),
not for a single fast multi-row INSERT. The actual rebuild execution happens
entirely inside the Cloud Run job (brahma-build-pipeline-job), dispatched
separately via `gcloud run jobs execute ... --args=--run-id,<id>` after this
script prints the run_id.

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_d2_cycle1_rebuild_job.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from collections import deque

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "d2-cycle1-conductor-rebuild"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# The exact closure computed live 2026-07-17 from asset_registry.depends_on
# (STATE_D-2.md rebuild_scope_ruling.exact_closure) — the changed-writer seeds
# plus their true downstream dependents. 58 assets.
TARGET_ASSETS = [
    "bg_vidhi_floors", "bg_vidhi_primitives", "bo_anveshana", "bo_arudha",
    "bo_bimba", "bo_cdlm_summary", "bo_cgm_motifs", "bo_cgm_paths",
    "bo_chart_gestalt", "bo_drishti", "bo_karanajala", "bo_laksana",
    "bo_laksana_rerank", "bo_nakshatra_semantic", "bo_pramana_mapa",
    "bo_pratijna", "bo_samskara", "bo_samvada", "bo_sangati",
    "bo_special_lagna", "bo_upaya", "bo_vargottama_dhana", "bo_yantra_mechanism",
    "ga_condition", "ga_dashas", "ga_medical", "ga_sade_sati", "ga_structural",
    "ga_tajaka", "ga_vastu", "ga_vichara", "ga_yoga",
    "ka_avadhi", "ka_bhavishya_lekha", "ka_dasha_kala", "ka_jivana_parva",
    "ka_kala_darshana", "ka_kalasutra", "ka_sangam", "ka_taranga", "ka_tulana",
    "ka_vighnakara", "ka_yojaka",
    "mi_abhilekha", "mi_adhilepa", "mi_bhavisya", "mi_darshana", "mi_gunanaka",
    "mi_pariksha", "mi_pramana", "mi_sambandha", "mi_seva",
    "ph_muhurta", "ph_nimitta", "ph_phaladesa", "ph_pramana", "ph_pratikara",
    "ph_rectification", "ph_sankrama", "ph_sodhana", "ph_suddha_sodhana",
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

    # Force every target asset -> dormant regardless of current state ('lit'
    # included) so the orchestrator treats this as a genuine rebuild, not a
    # no-op over already-lit assets (D-1.5b/D-1.6 precedent). Global-scope
    # assets (bg_vidhi_primitives/bg_vidhi_floors, chart-agnostic L0 reference
    # data) use chart_id IS NULL per the asset_throughput integrity constraint.
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
    print(f"[dispatch] created D-2 cycle-1 rebuild build_run {run_id} with {len(assets)} assets: {assets}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
