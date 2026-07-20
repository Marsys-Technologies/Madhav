"""
dispatch_d3_cycle2_ka_sangam_rebuild.py — D-3 cycle-2's lifecycle-step-6 REBUILD.

PR #604 (merge SHA c40b56c2c7b5efb1bdf7574f4083cc732909fce7) deployed T-6's
CR-102 vedha reference-frame fix + the ADMITTED (0.2/0.2) TRIGGER suppression
into pipeline/orchestrator/writers/ka_sangam.py (mode_a_search/mode_b_sweep).
Per T-6's verifier receipt (STATE_D-3.md cycle2_t6_lane): this is BUILD-TIME
ONLY logic inside the writer's run_substep path — 482012f1 keeps STALE
pre-T-6 kala_* rows until a scope-limited rebuild of ka_sangam + its true
downstream dependents completes. The §G retrodiction gate must not run
against stale data.

TARGET_ASSETS below is the exact transitive-dependents closure of ka_sangam
computed LIVE this session via a Postgres recursive query over
asset_registry.depends_on (verified twice: once by manual trace over the
full asset_registry.depends_on dump, once by a recursive CTE
`WITH RECURSIVE dependents AS (... WHERE d.asset_id = ANY(ar.depends_on))`)
— NOT the secondhand "ka_sangam -> ka_kalasutra -> kala_activation" summary,
per the MINIMAL-CASCADE RULE (CONDUCTOR_PROTOCOL.md §8.2): 26 assets total,
spanning L3 (kala, 8 incl. ka_sangam itself), L4 (phala, 9), L5 (mimamsa, 9).
No L2 (bodha) or L1 (ganita) asset is a dependent of ka_sangam — L2 stays
read-only this wave per the brief's expected scope.

Follows the D-1.5b/D-2 precedent scripts in this directory: brief local
Cloud SQL Auth Proxy session for the quick multi-row INSERT ONLY (per
O8_LOCAL_PROXY_KILL_ROOT_CAUSE_v1_0.md — the proxy is unreliable for
LONG-RUNNING connections, not a single fast insert); the actual rebuild
execution happens entirely inside the Cloud Run job
(brahma-build-pipeline-job), dispatched separately via
`gcloud run jobs execute ... --args=--run-id,<id>` after this script prints
the run_id. Abhisek's chart (482012f1) ONLY; Abhinandan is never rebuilt.

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_d3_cycle2_ka_sangam_rebuild.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from collections import deque

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "d3-cycle2-t6-ka-sangam-rebuild"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# Exact closure computed live 2026-07-18 from asset_registry.depends_on via a
# recursive CTE seeded at ka_sangam (STATE_D-3.md's own T-6 GATE-SEQUENCING
# FLAG demands this rebuild before §G runs). 26 assets.
TARGET_ASSETS = [
    "ka_sangam", "ka_bhavishya_lekha", "ka_jivana_parva", "ka_kala_darshana",
    "ka_kalasutra", "ka_taranga", "ka_tulana", "ka_vighnakara",
    "ph_muhurta", "ph_nimitta", "ph_pratikara", "ph_phaladesa", "ph_pramana",
    "ph_rectification", "ph_sankrama", "ph_sodhana", "ph_suddha_sodhana",
    "mi_adhilepa", "mi_darshana", "mi_seva", "mi_bhavisya", "mi_abhilekha",
    "mi_sambandha", "mi_pramana", "mi_gunanaka", "mi_pariksha",
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
    # included) so the orchestrator treats this as a genuine rebuild (all
    # 26 targets are chart-scoped, none global — no chart_id IS NULL branch
    # needed, but kept for parity with the D-2 precedent script).
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
    print(f"[dispatch] created D-3 cycle-2 ka_sangam rebuild build_run {run_id} with {len(assets)} assets: {assets}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
