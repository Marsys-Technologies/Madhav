"""
BRIDGE-S3: query_vedha_anchor_interactions MCP tool
Returns vedha-anchor interaction rows for a chart from l25_vedha_anchor_interactions.
Per: TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §2 + RETRIEVAL_INTERFACE_REGISTER
"""

from typing import Optional, List


def query_vedha_anchor_interactions(
    conn,
    chart_id: str,
    ayanamsha_id: str,
    build_id: Optional[str] = None,
    interaction_class_filter: Optional[str] = None,
    min_mitigation_strength: Optional[float] = None,
    limit: int = 100,
) -> List[dict]:
    """
    Returns vedha-anchor interactions for a chart.

    Parameters
    ----------
    conn                    : active psycopg2 connection
    chart_id                : UUID string of the chart
    ayanamsha_id            : ayanamsha identifier (e.g. 'lahiri')
    build_id                : optional — filter to a specific computation build
    interaction_class_filter: optional — one of full_mitigation/partial_mitigation/
                              inversion/amplification/neutralizing
    min_mitigation_strength : optional float 0-1 — only return rows >= this strength
    limit                   : max rows to return (default 100)

    Columns returned
    ----------------
    interaction_id, chart_id, ayanamsha_id, build_id, vedha_id, anchor_id,
    interaction_class, mitigation_strength, expected_outcome_modification_class,
    severity_after_mitigation, confidence_after_mitigation,
    classical_resolution_methodology, classical_citation, computed_at
    """
    conditions = ['chart_id = %s', 'ayanamsha_id = %s']
    params: list = [chart_id, ayanamsha_id]

    if build_id is not None:
        conditions.append('build_id = %s')
        params.append(build_id)

    if interaction_class_filter is not None:
        conditions.append('interaction_class = %s')
        params.append(interaction_class_filter)

    if min_mitigation_strength is not None:
        conditions.append('mitigation_strength >= %s')
        params.append(min_mitigation_strength)

    params.append(limit)

    where_clause = ' AND '.join(conditions)

    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT
              interaction_id::TEXT,
              chart_id::TEXT,
              ayanamsha_id,
              build_id::TEXT,
              vedha_id::TEXT,
              anchor_id::TEXT,
              interaction_class,
              mitigation_strength,
              expected_outcome_modification_class,
              severity_after_mitigation,
              confidence_after_mitigation,
              classical_resolution_methodology,
              classical_citation,
              computed_at::TEXT
            FROM l25_vedha_anchor_interactions
            WHERE {where_clause}
            ORDER BY mitigation_strength DESC NULLS LAST, computed_at DESC
            LIMIT %s
        """, params)

        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
