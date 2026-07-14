"""
rebuild_d1_5a_wave.py — D-1.5a scope-limited rebuild (cascade-aware)

Rebuilds Abhisek's chart (482012f1) ONLY, scoped to every asset the A7 aspect-
calculation fix (ga_structural_writer.py) and the A1/A2 valence fixes cascade
into — NOT full L1->L5, since most of L1 (bg_*/other ga_* writers) is untouched
and still 'lit'. A7 changes _graha_aspects_house, a shared-substrate computation
consumed across L2->L5, so the orchestrator correctly marked everything
downstream of ga_structural (and ga_vichara's own downstream) as 'stale' — 46
of 91 total writer-backed assets. This IS the Binder-detected "shared-substrate
change" trigger the native-ratified rebuild policy calls out as the exception
to minimal-scope rebuilds (CLAUDECODE_BRIEF.md R-5 / protocol §8.2).

Abhinandan (1c826d5a) is not rebuilt — read-only reference for the CR-87 guard.

Usage (Cloud SQL Auth Proxy must be running on port 5433):
  cd <repo-root>/platform
  python -m scripts.rebuild_d1_5a_wave
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "rebuild-script-d1-5a-wave-cascade"

_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = (10, 30)

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_sidecar = os.path.join(os.path.dirname(__file__), "..", "python-sidecar")
if _sidecar not in sys.path:
    sys.path.insert(0, _sidecar)


def _resolve_cascade_plan(cur) -> list[str]:
    """Every non-'lit' writer-backed asset for CHART_ID, topologically sorted via
    asset_registry.depends_on (the real dependency source — see asset_runner.deps_unsatisfied)."""
    cur.execute(
        """SELECT asset_id FROM asset_throughput WHERE chart_id = %s AND state != 'lit'""",
        (CHART_ID,),
    )
    targets = {r["asset_id"] for r in cur.fetchall()}
    if not targets:
        return []

    cur.execute(
        "SELECT asset_id, COALESCE(depends_on, '{}') AS deps FROM asset_registry"
    )
    all_deps = {r["asset_id"]: list(r["deps"] or []) for r in cur.fetchall()}

    # Kahn's algorithm restricted to `targets`, edges only among targets (deps outside
    # the target set are assumed already 'lit' — the query above only returns non-lit ones).
    in_degree = {a: 0 for a in targets}
    edges: dict[str, list[str]] = {a: [] for a in targets}
    for a in targets:
        for dep in all_deps.get(a, []):
            if dep in targets:
                edges[dep].append(a)
                in_degree[a] += 1

    from collections import deque
    queue = deque(sorted(a for a in targets if in_degree[a] == 0))
    ordered: list[str] = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for nxt in sorted(edges[node]):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    if len(ordered) != len(targets):
        missing = targets - set(ordered)
        raise RuntimeError(f"[plan] cycle or unresolved deps among target assets: {missing}")
    return ordered


def _execute_run_with_bounded_retry(run_id: str, chart_id: str, assets: list[str]) -> None:
    import psycopg
    from pipeline.orchestrator.db import db_url
    from pipeline.orchestrator.runner import execute_run

    current_run_id = run_id
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            execute_run(current_run_id)
            return
        except (psycopg.OperationalError, OSError) as exc:
            if attempt >= _MAX_ATTEMPTS:
                logger.error("[run] execute_run(%s) failed after %d/%d attempts: %s: %s",
                             current_run_id, attempt, _MAX_ATTEMPTS, type(exc).__name__, exc)
                raise
            backoff = _RETRY_BACKOFF_SECONDS[min(attempt - 1, len(_RETRY_BACKOFF_SECONDS) - 1)]
            logger.warning("[run] attempt %d/%d hit connection error (%s: %s) — retrying in %ds",
                           attempt, _MAX_ATTEMPTS, type(exc).__name__, exc, backoff)
            time.sleep(backoff)

            conn = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
            conn.autocommit = False
            cur = conn.cursor()
            current_run_id = str(uuid.uuid4())
            cur.execute(
                """INSERT INTO build_runs
                     (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
                   VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
                (current_run_id, chart_id, json.dumps(assets), f"{TRIGGERED_BY}-retry{attempt}"),
            )
            for position, asset_id in enumerate(assets):
                cur.execute(
                    """INSERT INTO build_run_assets (run_id, asset_id, position, state)
                       VALUES (%s, %s, %s, 'queued')""",
                    (current_run_id, asset_id, position),
                )
            conn.commit()
            conn.close()


def main() -> None:
    import psycopg
    import psycopg.rows

    from pipeline.orchestrator.db import db_url
    from pipeline.orchestrator.writers import discover_all
    discover_all()

    conn = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    assets = _resolve_cascade_plan(cur)
    logger.info("[plan] %d non-lit assets to rebuild (topological order): %s", len(assets), assets)

    # Reset error-state assets to dormant so the runner doesn't skip them as "already handled";
    # stale assets are already correctly skippable-as-pending, but forcing dormant is harmless
    # and guarantees re-execution for everything in the cascade.
    for asset_id in assets:
        cur.execute(
            """INSERT INTO asset_throughput (chart_id, asset_id, state)
               VALUES (%s, %s, 'dormant')
               ON CONFLICT (chart_id, asset_id)
               WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
            (CHART_ID, asset_id),
        )
    conn.commit()
    logger.info("[reset] %d assets -> dormant", len(assets))

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
        (run_id, CHART_ID, json.dumps(assets), TRIGGERED_BY),
    )
    for position, asset_id in enumerate(assets):
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, %s, 'queued')""",
            (run_id, asset_id, position),
        )
    conn.commit()
    logger.info("[run] created build_run %s with %d-asset plan", run_id, len(assets))
    conn.close()

    logger.info("[run] invoking execute_run(%s) with bounded retry…", run_id)
    _execute_run_with_bounded_retry(run_id, CHART_ID, assets)
    logger.info("[run] execute_run complete — verifying throughput…")

    conn2 = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    cur2 = conn2.cursor()
    cur2.execute(
        """SELECT asset_id, state, rows_written, last_built_at, last_error
           FROM asset_throughput
           WHERE chart_id = %s AND asset_id = ANY(%s)
           ORDER BY asset_id""",
        (CHART_ID, assets),
    )
    err_count = 0
    for r in cur2.fetchall():
        logger.info("[post] %s: state=%s rows_written=%s last_built_at=%s last_error=%s",
                    r["asset_id"], r["state"], r["rows_written"], r["last_built_at"], r["last_error"])
        if r["state"] == "error":
            err_count += 1
    conn2.close()
    logger.info("[summary] %d/%d assets in error state", err_count, len(assets))


if __name__ == "__main__":
    main()
