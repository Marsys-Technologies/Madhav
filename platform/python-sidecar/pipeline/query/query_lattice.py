"""
META-α-S2: Chart Lattice Query Tools (4 tools)
================================================
Four retrieval functions over l25_chart_lattice_snapshots.

Per: META_ENHANCEMENTS_SPEC_v1_0.md §1 — retrieval tools.

Tools
-----
1. query_lattice_at_date          — exact single-date snapshot
2. query_lattice_in_range         — date-window scan, optional attention filter
3. query_lattice_high_resonance_windows — top-K dates by total_active_pattern_count
4. query_lattice_peers            — cross-chart moments with similar lattice shape
                                    (embedding cosine when available, resonance fallback)

[BUILD-ORCH-STREAM-D-META-ALPHA-S2]
"""
from __future__ import annotations

from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Shared column list — every query selects the same shape for uniform callers.
# ---------------------------------------------------------------------------

LATTICE_COLS = """
    snapshot_id::TEXT,
    chart_id::TEXT,
    ayanamsha_id,
    date_iso::TEXT,
    active_dasha_jsonb,
    active_synchronicity_jsonb,
    active_anchors_jsonb,
    active_vedhas_jsonb,
    nearby_bhrigu_hits_jsonb,
    nearby_exact_aspects_jsonb,
    total_active_pattern_count,
    resonance_class_at_date,
    high_priority_attention_flag,
    computed_at::TEXT
"""


def _rows(cur) -> List[Dict]:
    """Convert cursor result to list-of-dicts."""
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Tool 1: exact single-date lookup
# ---------------------------------------------------------------------------

def query_lattice_at_date(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    date_iso: str,
    depth_class: Optional[str] = None,
) -> Optional[Dict]:
    """
    Return the lattice snapshot for exactly one (chart_id, ayanamsha_id, date_iso).

    Parameters
    ----------
    conn         : psycopg2 connection
    chart_id     : UUID string
    ayanamsha_id : e.g. 'lahiri'
    date_iso     : YYYY-MM-DD
    depth_class  : reserved for future caller hint (ignored by this implementation)

    Returns None if no snapshot has been computed for that date yet.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {LATTICE_COLS}"
            " FROM l25_chart_lattice_snapshots"
            " WHERE chart_id = %s::UUID"
            "   AND ayanamsha_id = %s"
            "   AND date_iso = %s::DATE"
            " LIMIT 1",
            [chart_id, ayanamsha_id, date_iso],
        )
        rows = _rows(cur)
    return rows[0] if rows else None


# ---------------------------------------------------------------------------
# Tool 2: date-window range scan
# ---------------------------------------------------------------------------

def query_lattice_in_range(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    start_iso: str,
    end_iso: str,
    attention_only: bool = False,
    limit: int = 365,
) -> List[Dict]:
    """
    Return lattice snapshots for all dates in [start_iso, end_iso].

    Parameters
    ----------
    attention_only : when True, return only dates where high_priority_attention_flag=true.
    limit          : hard cap on result rows (default 365 = one calendar year).

    Ordered by date_iso ascending.
    """
    where = (
        "chart_id = %s::UUID"
        " AND ayanamsha_id = %s"
        " AND date_iso >= %s::DATE"
        " AND date_iso <= %s::DATE"
    )
    params: list = [chart_id, ayanamsha_id, start_iso, end_iso]

    if attention_only:
        where += " AND high_priority_attention_flag = true"

    params.append(limit)

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {LATTICE_COLS}"
            " FROM l25_chart_lattice_snapshots"
            f" WHERE {where}"
            " ORDER BY date_iso"
            " LIMIT %s",
            params,
        )
        return _rows(cur)


# ---------------------------------------------------------------------------
# Tool 3: top-K highest-resonance windows
# ---------------------------------------------------------------------------

def query_lattice_high_resonance_windows(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    top_k: int = 10,
) -> List[Dict]:
    """
    Return the top-K dates for this chart ordered by total_active_pattern_count DESC.

    Useful for surfacing peak-intensity windows across the entire computed span
    without specifying a date range.  Ties broken by date_iso ascending.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {LATTICE_COLS}"
            " FROM l25_chart_lattice_snapshots"
            " WHERE chart_id = %s::UUID"
            "   AND ayanamsha_id = %s"
            " ORDER BY total_active_pattern_count DESC, date_iso"
            " LIMIT %s",
            [chart_id, ayanamsha_id, top_k],
        )
        return _rows(cur)


# ---------------------------------------------------------------------------
# Tool 4: cross-chart peer moments (embedding cosine or resonance fallback)
# ---------------------------------------------------------------------------

def query_lattice_peers(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    date_iso: str,
    top_k: int = 10,
) -> List[Dict]:
    """
    Find other (chart_id, date_iso) moments whose lattice shape is most similar
    to the reference moment identified by (chart_id, ayanamsha_id, date_iso).

    Strategy
    --------
    1. Primary: if the reference row has a non-NULL lattice_moment_embedding_vec,
       use HNSW cosine-distance (<=> operator) to find the top-K nearest neighbours
       across ALL charts, excluding the exact reference point.
    2. Fallback: if no embedding is present, match on resonance_class_at_date and
       order by closeness in total_active_pattern_count.

    Returns an empty list if the reference snapshot does not exist.
    """
    # Fetch the reference row's embedding + resonance info
    with conn.cursor() as cur:
        cur.execute(
            "SELECT lattice_moment_embedding_vec,"
            "       resonance_class_at_date,"
            "       total_active_pattern_count"
            " FROM l25_chart_lattice_snapshots"
            " WHERE chart_id = %s::UUID"
            "   AND ayanamsha_id = %s"
            "   AND date_iso = %s::DATE"
            " LIMIT 1",
            [chart_id, ayanamsha_id, date_iso],
        )
        ref = cur.fetchone()

    if ref is None:
        return []

    embedding, resonance, count = ref

    with conn.cursor() as cur:
        if embedding is not None:
            # Embedding-based similarity across all charts
            cur.execute(
                f"SELECT {LATTICE_COLS}"
                " FROM l25_chart_lattice_snapshots"
                " WHERE NOT (chart_id = %s::UUID AND date_iso = %s::DATE)"
                "   AND lattice_moment_embedding_vec IS NOT NULL"
                " ORDER BY lattice_moment_embedding_vec <=> %s::vector"
                " LIMIT %s",
                [chart_id, date_iso, str(embedding), top_k],
            )
        else:
            # Resonance-class + count proximity fallback
            cur.execute(
                f"SELECT {LATTICE_COLS}"
                " FROM l25_chart_lattice_snapshots"
                " WHERE NOT (chart_id = %s::UUID AND date_iso = %s::DATE)"
                "   AND resonance_class_at_date = %s"
                " ORDER BY ABS(total_active_pattern_count - %s)"
                " LIMIT %s",
                [chart_id, date_iso, resonance, count, top_k],
            )
        return _rows(cur)
