"""
rebuild_el18_manglik_ga_structural.py — EL-18 (Elevation Campaign v2.1, Lane β.D2).

Re-runs `ga_structural` through the FROZEN orchestrator for BOTH canonical charts so the
elev/beta ga_structural code lands in the live DB — specifically the Manglik / Kuja Dosha bhaṅga
this lane added (bespoke `_detect_manglik` making the already-built, BPHS-cited `_cancel_manglik`
reachable), together with the real Kemadruma-bhaṅga (#735, 2026-07-24) and the dosha-cancellation
completion (3c0c49ed, 2026-07-16) — all of which post-date the charts' last build (2026-07-14/15),
leaving the live `dosha_label` rows stale.

DEFERRED-TO-INTEGRATION (β.D2 Native-Proxy ruling, 2026-07-25): at authoring time the
`~/elev-v2-shared/locks/db-rebuild` lock was held by sibling lane β.D, concurrently rebuilding the
SAME writer (ga_sensitive/ga_structural/ga_vargas). Running this with β.D2's isolated branch
(elev/beta base + manglik, WITHOUT β.D's EL-30/40/47 fixes) would have clobbered β.D's concurrent
ga_structural output in prod. The authoritative rebuild therefore belongs to the integration phase,
on the MERGED elev/beta head containing BOTH lanes' ga_structural changes. Run then, under the
db-rebuild lock, and re-assert FORENSIC 7/7.

Usage (Cloud SQL proxy on :5433; from the MERGED head, holding the lock):
  cd <repo-root>/platform/python-sidecar
  python -m scripts.rebuild_el18_manglik_ga_structural

Verify after (per chart):
  SELECT fact_subject, fact_value_jsonb->>'fires' AS fires,
         fact_value_jsonb->>'bhanga_active' AS bhanga_active
  FROM chart_facts
  WHERE chart_id = '<chart>' AND ayanamsha_id='lahiri_chitrapaksha'
    AND fact_category='dosha_label' AND fact_subject='manglik';
  -- Abhisek 482012f1   → fires=true,  bhanga_active=false (Manglik uncancelled).
  -- Abhinandan 1c826d5a → fires=false, bhanga_active=true  (cancelled: Jupiter in kendra +
  --   Mars-Pisces-in-12th sign-specific, BPHS ch.81).
Then re-run FORENSIC 7/7 for both charts (anchors come from ga_positions/ga_panchanga, untouched
here — they must still PASS).
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

CHART_IDS = [
    "482012f1-710e-4a25-994a-93821f5871aa",  # Abhisek (primary)
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a",  # Abhinandan
]
ASSETS = ["ga_structural"]
TRIGGERED_BY = "rebuild-el18-manglik-ga-structural"

_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = (10, 30)

# This file lives at platform/python-sidecar/scripts/ ; platform/.env.local is two levels up.
_here = os.path.dirname(__file__)
_env_file = os.path.join(_here, "..", "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# Ensure the python-sidecar root (this file's grandparent) is importable.
_sidecar = os.path.abspath(os.path.join(_here, ".."))
if _sidecar not in sys.path:
    sys.path.insert(0, _sidecar)


def _execute_run_with_bounded_retry(run_id: str, chart_id: str, assets: list[str]) -> None:
    """Bounded retry ONLY on connection-interruption (psycopg.OperationalError / OSError); any
    writer/constraint error propagates immediately. Re-entry is safe because every L1+ writer is
    delete-then-insert idempotent (§N.3) and already-'lit' assets are skipped by the runner."""
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
                logger.error("[run] execute_run(%s) failed after %d attempts: %s: %s",
                             current_run_id, attempt, type(exc).__name__, exc)
                raise
            backoff = _RETRY_BACKOFF_SECONDS[min(attempt - 1, len(_RETRY_BACKOFF_SECONDS) - 1)]
            logger.warning("[run] attempt %d/%d hit %s — retrying in %ds via a fresh build_run",
                           attempt, _MAX_ATTEMPTS, type(exc).__name__, backoff)
            time.sleep(backoff)
            conn = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
            conn.autocommit = False
            cur = conn.cursor()
            current_run_id = str(uuid.uuid4())
            cur.execute(
                """INSERT INTO build_runs
                     (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
                   VALUES (%s, %s, 'per_chart', %s, 'build', %s, 'planned', %s)""",
                (current_run_id, chart_id, chart_id, json.dumps(assets),
                 f"{TRIGGERED_BY}-retry{attempt}"),
            )
            for position, asset_id in enumerate(assets):
                cur.execute(
                    """INSERT INTO build_run_assets (run_id, asset_id, position, state)
                       VALUES (%s, %s, %s, 'queued')""",
                    (current_run_id, asset_id, position),
                )
            conn.commit()
            conn.close()


def _rebuild_one_chart(chart_id: str) -> None:
    import psycopg
    import psycopg.rows
    from pipeline.orchestrator.db import db_url

    conn = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()
    for asset_id in ASSETS:
        cur.execute(
            """INSERT INTO asset_throughput (chart_id, asset_id, state)
               VALUES (%s, %s, 'dormant')
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
            (chart_id, asset_id),
        )
    conn.commit()
    logger.info("[reset] %s ga_structural throughput → dormant", chart_id[:8])

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'per_chart', %s, 'build', %s, 'planned', %s)""",
        (run_id, chart_id, chart_id, json.dumps(ASSETS), TRIGGERED_BY),
    )
    for position, asset_id in enumerate(ASSETS):
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, %s, 'queued')""",
            (run_id, asset_id, position),
        )
    conn.commit()
    conn.close()
    logger.info("[run] %s created build_run %s (plan=%s)", chart_id[:8], run_id, ASSETS)
    _execute_run_with_bounded_retry(run_id, chart_id, ASSETS)
    logger.info("[run] %s ga_structural rebuild complete", chart_id[:8])


def main() -> None:
    from pipeline.orchestrator.writers import discover_all
    discover_all()
    for chart_id in CHART_IDS:
        _rebuild_one_chart(chart_id)
    logger.info("[done] ga_structural rebuilt for both canonical charts — now assert FORENSIC 7/7.")


if __name__ == "__main__":
    main()
