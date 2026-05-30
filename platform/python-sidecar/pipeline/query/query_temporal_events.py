"""
UTEE-S4: Temporal event retrieval tools (META-ζ surface)
6 tools backed by vw_temporal_unified_lattice.
Per: TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §3.C
[BUILD-ORCH-STREAM-D-UTEE-S4]
"""
from typing import Optional, List, Dict, Any

UTEE_SELECT_COLS = """
    source_asset,
    source_row_id,
    chart_id::TEXT,
    ayanamsha_id,
    build_id,
    event_iso::TEXT,
    event_window_start_iso::TEXT,
    event_window_end_iso::TEXT,
    severity_normalized_0_1,
    confidence_normalized_0_1,
    confidence_class,
    expected_outcome_class,
    outcome_ontology_class,
    falsifiability_statement,
    falsifier_date_iso::TEXT,
    cross_ayanamsha_stability_score,
    inside_a15_cluster_ids_array,
    associated_synchronicity_ids_array,
    seeds_anchor_ids_array,
    mitigates_event_ids_array,
    amplifies_event_ids_array,
    mitigated_by_vedha_ids_array,
    channel_render_priority_jsonb,
    m6_outcome_tracking_placeholder_jsonb,
    citation_ref,
    citation_human,
    computed_at::TEXT
"""


def _rows_to_dicts(cur) -> List[Dict[str, Any]]:
    """Convert cursor results to list of dicts."""
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def query_temporal_events_in_range(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    start_iso: str,
    end_iso: str,
    source_asset_filter: Optional[str] = None,
    severity_min: Optional[float] = None,
    confidence_min: Optional[float] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """
    All temporal events in a date range for a chart, across all 7 temporal sources.

    Uses vw_temporal_unified_lattice (META-ζ). Results ordered by event_iso ascending.

    Parameters
    ----------
    conn                 : active psycopg2 connection
    chart_id             : UUID string of the chart
    ayanamsha_id         : ayanamsha identifier (e.g. 'lahiri')
    start_iso            : ISO 8601 start of range (inclusive)
    end_iso              : ISO 8601 end of range (inclusive)
    source_asset_filter  : optional — restrict to one asset (A15/A16/A18/A19/A20/A21/A22)
    severity_min         : optional float 0.0-1.0 — only rows >= this severity
    confidence_min       : optional float 0.0-1.0 — only rows >= this confidence
    limit                : max rows returned (default 200)

    Returns
    -------
    List of UTEE-envelope dicts, ordered by event_iso ASC.
    Note: A18 rows have chart_id=NULL (vedha table has no chart_id column).
    """
    conditions = [
        "chart_id = %s::UUID",
        "ayanamsha_id = %s OR ayanamsha_id IS NULL",
        "event_iso >= %s::TIMESTAMPTZ",
        "event_iso <= %s::TIMESTAMPTZ",
    ]
    params: List[Any] = [chart_id, ayanamsha_id, start_iso, end_iso]

    if source_asset_filter is not None:
        conditions.append("source_asset = %s")
        params.append(source_asset_filter)

    if severity_min is not None:
        conditions.append("severity_normalized_0_1 >= %s")
        params.append(severity_min)

    if confidence_min is not None:
        conditions.append("confidence_normalized_0_1 >= %s")
        params.append(confidence_min)

    params.append(limit)

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {UTEE_SELECT_COLS} FROM vw_temporal_unified_lattice "
            f"WHERE {' AND '.join(conditions)} "
            f"ORDER BY event_iso ASC NULLS LAST LIMIT %s",
            params,
        )
        return _rows_to_dicts(cur)


def query_temporal_events_next(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    from_date: str,
    source_asset_filter: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Next N temporal events from a given date across all temporal sources.

    Returns events where event_iso >= from_date, ordered chronologically.

    Parameters
    ----------
    conn                 : active psycopg2 connection
    chart_id             : UUID string of the chart
    ayanamsha_id         : ayanamsha identifier (e.g. 'lahiri')
    from_date            : ISO 8601 date — return events on or after this date
    source_asset_filter  : optional — restrict to one source asset
    limit                : max rows returned (default 10)

    Returns
    -------
    List of UTEE-envelope dicts, ordered by event_iso ASC.
    """
    conditions = [
        "chart_id = %s::UUID",
        "ayanamsha_id = %s OR ayanamsha_id IS NULL",
        "event_iso >= %s::TIMESTAMPTZ",
    ]
    params: List[Any] = [chart_id, ayanamsha_id, from_date]

    if source_asset_filter is not None:
        conditions.append("source_asset = %s")
        params.append(source_asset_filter)

    params.append(limit)

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {UTEE_SELECT_COLS} FROM vw_temporal_unified_lattice "
            f"WHERE {' AND '.join(conditions)} "
            f"ORDER BY event_iso ASC NULLS LAST LIMIT %s",
            params,
        )
        return _rows_to_dicts(cur)


def query_temporal_events_within_a15_cluster(
    conn,
    cluster_id: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    All temporal events that belong to a specific A15 convergence cluster.

    Matches rows where cluster_id appears in inside_a15_cluster_ids_array.
    Results ordered by severity descending (highest-impact events first).

    Parameters
    ----------
    conn       : active psycopg2 connection
    cluster_id : UUID string of the A15 convergence cluster
    limit      : max rows returned (default 100)

    Returns
    -------
    List of UTEE-envelope dicts, ordered by severity_normalized_0_1 DESC.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {UTEE_SELECT_COLS} FROM vw_temporal_unified_lattice "
            "WHERE %s::UUID = ANY(inside_a15_cluster_ids_array) "
            "ORDER BY severity_normalized_0_1 DESC NULLS LAST LIMIT %s",
            [cluster_id, limit],
        )
        return _rows_to_dicts(cur)


def query_temporal_events_seeded_by(
    conn,
    seed_event_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    A16 anchors (and other events) seeded by a Bhrigu transit (A19) or Varsha year-lord (A20).

    Matches rows where seed_event_id appears in seeds_anchor_ids_array.
    Ordered chronologically by event_iso.

    Parameters
    ----------
    conn          : active psycopg2 connection
    seed_event_id : UUID string of the A19 Bhrigu hit or A20 varsha year-lord event
    limit         : max rows returned (default 50)

    Returns
    -------
    List of UTEE-envelope dicts, ordered by event_iso ASC.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {UTEE_SELECT_COLS} FROM vw_temporal_unified_lattice "
            "WHERE %s::UUID = ANY(seeds_anchor_ids_array) "
            "ORDER BY event_iso ASC NULLS LAST LIMIT %s",
            [seed_event_id, limit],
        )
        return _rows_to_dicts(cur)


def query_temporal_events_mitigated_by(
    conn,
    vedha_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    A16 anchors mitigated or modified by a specific A18 vedha.

    Matches rows where vedha_id appears in mitigated_by_vedha_ids_array.
    Results ordered by severity descending (most impacted anchors first).

    Parameters
    ----------
    conn     : active psycopg2 connection
    vedha_id : UUID string of the A18 vedha row
    limit    : max rows returned (default 50)

    Returns
    -------
    List of UTEE-envelope dicts, ordered by severity_normalized_0_1 DESC.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {UTEE_SELECT_COLS} FROM vw_temporal_unified_lattice "
            "WHERE %s::UUID = ANY(mitigated_by_vedha_ids_array) "
            "ORDER BY severity_normalized_0_1 DESC NULLS LAST LIMIT %s",
            [vedha_id, limit],
        )
        return _rows_to_dicts(cur)


def query_temporal_event_peers(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    source_asset: str,
    source_row_id: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Cross-chart cohort similarity for a temporal event.

    Primary path: vector similarity search via temporal_event_embedding_vec.
    Fallback path (when embedding is NULL): same source_asset + same expected_outcome_class,
    ordered by absolute severity distance from the reference event.

    Parameters
    ----------
    conn          : active psycopg2 connection
    chart_id      : UUID string of the reference chart
    ayanamsha_id  : ayanamsha identifier
    source_asset  : asset tag of the reference event (e.g. 'A19')
    source_row_id : TEXT primary key of the reference event row
    top_k         : number of similar events to return (default 10)

    Returns
    -------
    List of UTEE-envelope dicts from other charts similar to the reference event.
    Embedding-path rows include a 'distance' field (lower = more similar).
    Fallback-path rows do not include 'distance'.

    Note
    ----
    Requires temporal_event_embedding_vec to be populated (UTEE backfill step).
    Until populated, falls back to outcome-class + severity proximity matching.
    """
    # Retrieve the reference event's embedding, outcome class, and severity
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                temporal_event_embedding_vec,
                expected_outcome_class,
                severity_normalized_0_1
            FROM vw_temporal_unified_lattice
            WHERE chart_id = %s::UUID
              AND (ayanamsha_id = %s OR ayanamsha_id IS NULL)
              AND source_asset = %s
              AND source_row_id = %s
            LIMIT 1
            """,
            [chart_id, ayanamsha_id, source_asset, source_row_id],
        )
        row = cur.fetchone()
        if not row:
            return []

        embedding, outcome_class, severity = row

        if embedding is not None:
            # Vector similarity path: cosine distance via pgvector <=> operator
            cur.execute(
                f"""
                SELECT {UTEE_SELECT_COLS},
                  temporal_event_embedding_vec <=> %s::vector AS distance
                FROM vw_temporal_unified_lattice
                WHERE source_asset = %s
                  AND NOT (chart_id = %s::UUID AND source_row_id = %s)
                  AND temporal_event_embedding_vec IS NOT NULL
                ORDER BY distance ASC
                LIMIT %s
                """,
                [str(embedding), source_asset, chart_id, source_row_id, top_k],
            )
        else:
            # Fallback: same asset type + matching outcome class, ordered by severity proximity
            ref_severity = severity if severity is not None else 0.5
            cur.execute(
                f"""
                SELECT {UTEE_SELECT_COLS}
                FROM vw_temporal_unified_lattice
                WHERE source_asset = %s
                  AND expected_outcome_class = %s
                  AND NOT (chart_id = %s::UUID AND source_row_id = %s)
                ORDER BY ABS(COALESCE(severity_normalized_0_1, 0.5) - %s) ASC
                LIMIT %s
                """,
                [source_asset, outcome_class, chart_id, source_row_id, ref_severity, top_k],
            )

        return _rows_to_dicts(cur)
