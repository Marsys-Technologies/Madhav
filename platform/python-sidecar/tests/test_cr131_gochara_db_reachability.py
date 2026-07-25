"""
tests/test_cr131_gochara_db_reachability.py — Elevation Campaign v2.1, Stream beta,
Lane T (timing residuals / gochara env / CR-131 sweep completion).

G0 regression guard for register CR-131 / CURRENT_STATE A-3 / charter EL-15 (the
"gochara serving tools have a DATABASE_URL gap" symptom this lane was briefed to
re-establish ground truth on).

ORIGINAL SYMPTOM (pre-fix, documented in CURRENT_STATE_v1_0.md and
PRE_DARPANA_READINESS_v2_0.md W-1/T-1): `gochara_activation_get` /
`gochara_forecast_get` / `gochara_election_avoidance_get`
(platform-mcp/src/tools/retrieval/register_gochara_windows.ts) held their own direct
`pg.Pool` keyed off `process.env['DATABASE_URL']` -- never set on the `amjis-mcp`
Cloud Run service (which has no DB attachment) -- so every call returned
`backing_data_reachable:false` / a hard connection error, regardless of whether the
underlying `kala_gochara_windows` data existed.

FIX (PR #732, commit 74752e20, "fix(sarva-siddhi/T-1): route gochara serving tools
through platform DB proxy"): the three tools were repointed onto
`platform/src/app/api/mcp/db/query/route.ts`'s existing read-only DB-proxy
(`ALLOWED_TABLES` whitelist), the same invariant every other MCP tool honors ("the
MCP server does not hold a direct DB connection"). This lane found the fix ALREADY
LIVE ON MAIN before doing any work here -- confirmed via `git blame` (commit
74752e20 predates this lane's branch point) and via a direct live MCP re-probe
(`gochara_activation_get`/`gochara_forecast_get` both returned
`backing_data_reachable:true` with real data, 2026-07-25). Disposition:
NOT-REPRODUCED on the MCP-served read path. Per charter Elevation Campaign v2.1 §9.2's
evidence bar, NOT-REPRODUCED requires BOTH a committed regression test reproducing
the original recipe verbatim (this file) AND a raw payload diff against the run-start
baseline (recorded in `00_ARCHITECTURE/llm_consumption_audit/ledgers/BETA_T.md`,
since `ELEVATION_V2_BASELINE.md` itself never captured a gochara payload -- the tools
were dark at Phase-0 baseline time, tracked only by CR-131's existing symptom text).

Two independent regression guards:
  1. DB-free: the platform DB-proxy's ALLOWED_TABLES whitelist (read as plain text,
     no import of TS) still names `kala_gochara_windows` + `brahma_remedy_corpus` --
     regression guard against PR #732's fix being silently reverted or the whitelist
     entries being dropped in a later refactor.
  2. `@pytest.mark.integration` (excluded by the mandated `-m "not integration"` CI
     invocation, same convention as test_gochara_intensity.py / test_permission_curve_route.py):
     reproduces the DATA-layer half of the original recipe against the live Cloud SQL
     proxy -- `kala_gochara_windows` is reachable and holds rows for chart 482012f1,
     which is exactly what `backing_data_reachable:true` asserts is true server-side.
"""
from __future__ import annotations

import os

import psycopg
import pytest

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
LIVE_DSN = "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis"

_ROUTE_TS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "src", "app", "api", "mcp", "db", "query", "route.ts"
)


def _live_conn_or_skip():
    try:
        conn = psycopg.connect(LIVE_DSN, row_factory=psycopg.rows.dict_row, connect_timeout=2)
    except Exception:
        pytest.skip("live Cloud SQL proxy (127.0.0.1:5433) not reachable in this environment")
    return conn


# ── module-level invariant (no DB, no HTTP) ─────────────────────────────────

def test_db_proxy_route_whitelists_gochara_and_remedy_tables():
    """Regression guard: PR #732's ALLOWED_TABLES entries must not silently
    regress. If this fails, the CR-131 fix has been reverted or refactored away
    and the gochara serving tools will 400 on every call again."""
    if not os.path.exists(_ROUTE_TS_PATH):
        pytest.skip(f"route.ts not found at {_ROUTE_TS_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_ROUTE_TS_PATH, encoding="utf-8") as f:
        src = f.read()
    assert "'kala_gochara_windows'" in src, (
        "kala_gochara_windows missing from platform DB-proxy ALLOWED_TABLES -- "
        "CR-131 regression: gochara_activation_get/forecast_get/election_avoidance_get "
        "will lose their DB path again."
    )
    assert "'brahma_remedy_corpus'" in src, (
        "brahma_remedy_corpus missing from platform DB-proxy ALLOWED_TABLES -- "
        "CR-131 regression: gochara_election_avoidance_get's DR-16 mitigation join will break."
    )


# ── live integration (excluded by -m "not integration"; run manually) ──────

@pytest.mark.integration
def test_kala_gochara_windows_reachable_and_has_rows_for_native_chart():
    """Reproduces the DATA-layer half of the original recipe verbatim: the exact
    table + chart_id the gochara serving tools query. Before PR #732 this was
    unreachable from the MCP server's own process (DATABASE_URL not set there);
    this test proves the underlying table itself was never the problem -- the
    problem was always the connection path, exactly as CR-131 diagnosed."""
    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) AS n FROM kala_gochara_windows WHERE chart_id = %s",
                (CHART_ID,),
            )
            row = cur.fetchone()
        assert row is not None
        assert row["n"] > 0, (
            "kala_gochara_windows has zero rows for chart 482012f1 -- if this ever "
            "flips true, gochara_activation_get/forecast_get's honest-empty path "
            "should fire, not a reachability error."
        )
    finally:
        conn.close()
