"""
brahmagyan/bodha/bo_2-8.py — holistic_bundle composite (L2 Bodha, BO-2-8)

B.11 whole-chart-read entrypoint. One call returns MSR signals + CGM graph edges +
CDLM domain links + RM resonance elements for a given chart_id — all 4 L2 Bodha
subsystems in a single, coherently provenance-wrapped response.

Architecture:
  - No new table. Pure aggregation over bodha_* tables populated by Wave-1.
  - DB queries run in parallel via asyncio; per-subsystem errors are isolated —
    one failure does not abort the bundle.
  - Returns the response schema:
      {
        signals: [...],
        graph_edges: [...],
        domain_links: [...],
        resonance: [...],
        provenance_envelope: {
          chart_id, queried_at, subsystems_ok, subsystems_errored,
          signal_count, graph_edge_count, domain_link_count, resonance_count,
          b11_floor_passed
        }
      }

BRAHMA-BO-2-8
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DB connection helper (reads DATABASE_URL / DIRECT_DATABASE_URL from env)
# ---------------------------------------------------------------------------

_DATABASE_URL: str | None = None


def _get_db_url() -> str:
    global _DATABASE_URL
    if _DATABASE_URL:
        return _DATABASE_URL
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key)
        if val:
            _DATABASE_URL = val
            return val
    raise RuntimeError(
        "No database URL configured. Set DATABASE_URL, DIRECT_DATABASE_URL, or POSTGRES_URL."
    )


# ---------------------------------------------------------------------------
# Per-subsystem query functions
# ---------------------------------------------------------------------------


async def _fetch_signals(conn: asyncpg.Connection, chart_id: str) -> list[dict[str, Any]]:
    """Fetch MSR signals from bodha_signals for the given chart_id."""
    rows = await conn.fetch(
        """
        SELECT
            signal_id,
            domain,
            valence,
            confidence,
            salience,
            state,
            signal_text,
            source_citation,
            graha_refs,
            house_refs,
            created_at
        FROM bodha_signals
        WHERE chart_id = $1
        ORDER BY salience DESC NULLS LAST, signal_id
        """,
        chart_id,
    )
    return [dict(r) for r in rows]


async def _fetch_graph_edges(conn: asyncpg.Connection, chart_id: str) -> list[dict[str, Any]]:
    """Fetch CGM graph edges from bodha_graph_edges for the given chart_id."""
    rows = await conn.fetch(
        """
        SELECT
            edge_id,
            from_signal_id,
            to_signal_id,
            edge_type,
            weight,
            label,
            created_at
        FROM bodha_graph_edges
        WHERE chart_id = $1
        ORDER BY weight DESC NULLS LAST, edge_id
        """,
        chart_id,
    )
    return [dict(r) for r in rows]


async def _fetch_domain_links(conn: asyncpg.Connection, chart_id: str) -> list[dict[str, Any]]:
    """Fetch CDLM cross-domain linkages from bodha_domain_links for the given chart_id."""
    rows = await conn.fetch(
        """
        SELECT
            link_id,
            from_domain,
            to_domain,
            link_type,
            signal_ids,
            strength,
            note,
            created_at
        FROM bodha_domain_links
        WHERE chart_id = $1
        ORDER BY strength DESC NULLS LAST, link_id
        """,
        chart_id,
    )
    return [dict(r) for r in rows]


async def _fetch_resonance(conn: asyncpg.Connection, chart_id: str) -> list[dict[str, Any]]:
    """Fetch RM resonance elements from bodha_resonance for the given chart_id."""
    rows = await conn.fetch(
        """
        SELECT
            resonance_id,
            theme,
            signal_ids,
            resonance_type,
            amplitude,
            note,
            created_at
        FROM bodha_resonance
        WHERE chart_id = $1
        ORDER BY amplitude DESC NULLS LAST, resonance_id
        """,
        chart_id,
    )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Serialization helpers (convert asyncpg Row to plain JSON-serialisable dict)
# ---------------------------------------------------------------------------


def _serialise(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert any non-serialisable types (datetime, UUID, etc.) to strings."""
    out: list[dict[str, Any]] = []
    for row in rows:
        clean: dict[str, Any] = {}
        for k, v in row.items():
            if isinstance(v, datetime):
                clean[k] = v.isoformat()
            elif hasattr(v, "__str__") and not isinstance(v, (str, int, float, bool, type(None))):
                clean[k] = str(v)
            else:
                clean[k] = v
        out.append(clean)
    return out


# ---------------------------------------------------------------------------
# Main bundle function
# ---------------------------------------------------------------------------


async def holistic_bundle_async(chart_id: str) -> dict[str, Any]:
    """
    Async implementation. Parallel-fetches all 4 L2 Bodha subsystems and assembles
    the provenance-wrapped response envelope.

    Args:
        chart_id: UUID of the chart to read.

    Returns:
        {
            signals: [...],
            graph_edges: [...],
            domain_links: [...],
            resonance: [...],
            provenance_envelope: { ... }
        }
    """
    queried_at = datetime.now(timezone.utc).isoformat()
    subsystems_ok: list[str] = []
    subsystems_errored: list[str] = []

    signals: list[dict] = []
    graph_edges: list[dict] = []
    domain_links: list[dict] = []
    resonance: list[dict] = []

    db_url = _get_db_url()

    try:
        conn: asyncpg.Connection = await asyncpg.connect(db_url)
    except Exception as e:
        logger.error("[bo_2-8] DB connection failed: %s", e)
        return {
            "signals": [],
            "graph_edges": [],
            "domain_links": [],
            "resonance": [],
            "provenance_envelope": {
                "chart_id": chart_id,
                "queried_at": queried_at,
                "subsystems_ok": [],
                "subsystems_errored": ["MSR", "CGM", "CDLM", "RM"],
                "signal_count": 0,
                "graph_edge_count": 0,
                "domain_link_count": 0,
                "resonance_count": 0,
                "b11_floor_passed": False,
                "error": f"DB connection failed: {e}",
            },
        }

    async def safe(name: str, coro):
        try:
            result = await coro
            subsystems_ok.append(name)
            return result
        except Exception as e:
            logger.warning("[bo_2-8] subsystem %s failed: %s", name, e)
            subsystems_errored.append(name)
            return []

    try:
        results = await asyncio.gather(
            safe("MSR", _fetch_signals(conn, chart_id)),
            safe("CGM", _fetch_graph_edges(conn, chart_id)),
            safe("CDLM", _fetch_domain_links(conn, chart_id)),
            safe("RM", _fetch_resonance(conn, chart_id)),
        )
        signals, graph_edges, domain_links, resonance = results
    finally:
        await conn.close()

    signals = _serialise(signals)
    graph_edges = _serialise(graph_edges)
    domain_links = _serialise(domain_links)
    resonance = _serialise(resonance)

    # B.11 floor: at least MSR (signals) must be non-empty
    b11_floor_passed = len(signals) > 0

    return {
        "signals": signals,
        "graph_edges": graph_edges,
        "domain_links": domain_links,
        "resonance": resonance,
        "provenance_envelope": {
            "chart_id": chart_id,
            "queried_at": queried_at,
            "subsystems_ok": subsystems_ok,
            "subsystems_errored": subsystems_errored,
            "signal_count": len(signals),
            "graph_edge_count": len(graph_edges),
            "domain_link_count": len(domain_links),
            "resonance_count": len(resonance),
            "b11_floor_passed": b11_floor_passed,
        },
    }


def holistic_bundle(chart_id: str) -> dict[str, Any]:
    """
    Synchronous wrapper for use from FastAPI endpoints.

    Delegates to holistic_bundle_async via asyncio.run() when there is no running
    event loop, or via loop.run_until_complete() when there is.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Inside an async context (e.g. pytest-asyncio, FastAPI handler) —
            # create a new loop in a thread to avoid nesting.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, holistic_bundle_async(chart_id))
                return future.result()
        else:
            return loop.run_until_complete(holistic_bundle_async(chart_id))
    except RuntimeError:
        return asyncio.run(holistic_bundle_async(chart_id))


# ---------------------------------------------------------------------------
# FastAPI router (mounted at /api/compute/brahma/bodha)
# ---------------------------------------------------------------------------


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class HolisticBundleRequest(BaseModel):
    chart_id: str


class HolisticBundleResponse(BaseModel):
    ok: bool
    result: dict[str, Any]


@router.post("/holistic_bundle", response_model=HolisticBundleResponse)
async def holistic_bundle_endpoint(body: HolisticBundleRequest) -> HolisticBundleResponse:
    """
    POST /api/compute/brahma/bodha/holistic_bundle

    B.11 whole-chart-read entrypoint. Returns MSR signals + CGM graph edges +
    CDLM domain links + RM resonance elements for the given chart_id.

    Response: { ok: true, result: { signals, graph_edges, domain_links, resonance,
                                    provenance_envelope } }
    """
    if not body.chart_id or not body.chart_id.strip():
        raise HTTPException(status_code=400, detail="chart_id is required")

    bundle = await holistic_bundle_async(body.chart_id.strip())
    return HolisticBundleResponse(ok=True, result=bundle)
