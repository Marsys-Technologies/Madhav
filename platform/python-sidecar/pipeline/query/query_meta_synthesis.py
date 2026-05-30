"""META-β/γ/δ/ε query tools.

Retrieval interface for the four synthesis-layer enhancements:
  META-β  (Π-CATALOG)  — query_patterns, query_pattern_links, query_pattern_peers
  META-γ  (Δ-LEDGER)   — query_divergences, query_divergence_at_structural_point
  META-δ  (Ω-SPACE)    — query_negative_space, query_distinctive_absences
  META-ε  (Φ-TRAIL)    — query_derivation_trail, query_derivation_upstream,
                          query_supporting_l1_facts

All functions use parameterized queries only.
"""
from typing import Optional, List, Dict


def _rows(cur) -> List[Dict]:
    """Convert cursor result to list of dicts."""
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# ============================================================
# META-β: Pattern Catalog queries
# ============================================================

def query_patterns(conn, chart_id: str, ayanamsha_id: str,
                   pattern_kind: Optional[str] = None,
                   active_only: bool = True,
                   limit: int = 100) -> List[Dict]:
    """
    Return patterns from l25_pattern_catalog for a chart+ayanamsha.
    Optionally filter by pattern_kind and active_only.
    """
    conds = ["chart_id = %s::UUID", "ayanamsha_id = %s"]
    params = [chart_id, ayanamsha_id]
    if pattern_kind:
        conds.append("pattern_kind = %s")
        params.append(pattern_kind)
    if active_only:
        conds.append("active_flag = true")
    params.append(limit)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT pattern_catalog_id::TEXT, chart_id::TEXT, ayanamsha_id, "
            "pattern_kind, pattern_name, pattern_strength, active_flag, "
            "source_asset, source_row_id, classical_citation, "
            "verification_pass_status, computed_at::TEXT "
            "FROM l25_pattern_catalog "
            f"WHERE {' AND '.join(conds)} "
            "ORDER BY pattern_strength DESC NULLS LAST "
            "LIMIT %s",
            params
        )
        return _rows(cur)


def query_pattern_links(conn, pattern_catalog_id: str) -> Dict:
    """
    Return cross-pattern linkage (reinforced_by, contradicted_by, cross_links)
    for a single pattern by its UUID.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT pattern_catalog_id::TEXT, pattern_name, "
            "cross_pattern_link_ids_array, "
            "reinforced_by_pattern_ids_array, "
            "contradicted_by_pattern_ids_array "
            "FROM l25_pattern_catalog "
            "WHERE pattern_catalog_id = %s::UUID "
            "LIMIT 1",
            [pattern_catalog_id]
        )
        rows = _rows(cur)
        return rows[0] if rows else {}


def query_pattern_peers(conn, chart_id: str, ayanamsha_id: str,
                        pattern_name: str, limit: int = 10) -> List[Dict]:
    """
    Return patterns with the same name from OTHER chart+ayanamsha combinations
    (cross-chart cohort matching by pattern name).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT pattern_catalog_id::TEXT, chart_id::TEXT, ayanamsha_id, "
            "pattern_name, pattern_strength "
            "FROM l25_pattern_catalog "
            "WHERE pattern_name = %s "
            "  AND NOT (chart_id = %s::UUID AND ayanamsha_id = %s) "
            "ORDER BY pattern_strength DESC NULLS LAST "
            "LIMIT %s",
            [pattern_name, chart_id, ayanamsha_id, limit]
        )
        return _rows(cur)


# ============================================================
# META-γ: Divergence Ledger queries
# ============================================================

def query_divergences(conn, chart_id: str,
                      ayanamsha_id: Optional[str] = None,
                      severity: Optional[str] = None,
                      status: str = 'open',
                      limit: int = 50) -> List[Dict]:
    """
    Return divergences from l25_divergence_ledger.
    Filter by ayanamsha_id, severity, and resolution_status.
    """
    conds = ["chart_id = %s::UUID"]
    params = [chart_id]
    if ayanamsha_id:
        conds.append("ayanamsha_id = %s")
        params.append(ayanamsha_id)
    if severity:
        conds.append("divergence_severity = %s")
        params.append(severity)
    conds.append("resolution_status = %s")
    params.append(status)
    params.append(limit)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT divergence_id::TEXT, chart_id::TEXT, ayanamsha_id, "
            "divergence_class, system_a, system_b, claim_a, claim_b, "
            "divergence_severity, resolution_status, resolution_note, "
            "computed_at::TEXT "
            "FROM l25_divergence_ledger "
            f"WHERE {' AND '.join(conds)} "
            "ORDER BY "
            "  CASE divergence_severity "
            "    WHEN 'critical' THEN 1 WHEN 'significant' THEN 2 "
            "    WHEN 'moderate' THEN 3 ELSE 4 END, "
            "computed_at "
            "LIMIT %s",
            params
        )
        return _rows(cur)


def query_divergence_at_structural_point(conn, chart_id: str,
                                          structural_point: str,
                                          limit: int = 20) -> List[Dict]:
    """
    Return all divergences touching a specific structural point
    (partial match on claim_a or claim_b text).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT divergence_id::TEXT, chart_id::TEXT, ayanamsha_id, "
            "divergence_class, system_a, system_b, claim_a, claim_b, "
            "divergence_severity, resolution_status, computed_at::TEXT "
            "FROM l25_divergence_ledger "
            "WHERE chart_id = %s::UUID "
            "  AND (claim_a ILIKE %s OR claim_b ILIKE %s) "
            "ORDER BY "
            "  CASE divergence_severity "
            "    WHEN 'critical' THEN 1 WHEN 'significant' THEN 2 "
            "    WHEN 'moderate' THEN 3 ELSE 4 END "
            "LIMIT %s",
            [chart_id,
             f"%{structural_point}%", f"%{structural_point}%",
             limit]
        )
        return _rows(cur)


# ============================================================
# META-δ: Negative Space queries
# ============================================================

def query_negative_space(conn, chart_id: str, ayanamsha_id: str,
                          significance: Optional[str] = None,
                          limit: int = 50) -> List[Dict]:
    """
    Return negative space entries from l25_negative_space_map.
    Optionally filter by absence_significance ('high','medium','low').
    """
    conds = ["chart_id = %s::UUID", "ayanamsha_id = %s"]
    params = [chart_id, ayanamsha_id]
    if significance:
        conds.append("absence_significance = %s")
        params.append(significance)
    params.append(limit)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT absence_id::TEXT, chart_id::TEXT, ayanamsha_id, "
            "absence_class, absent_feature, absence_significance, "
            "expected_if_present, classical_pattern_violated, "
            "acharya_interpretation_cue, verified, computed_at::TEXT "
            "FROM l25_negative_space_map "
            f"WHERE {' AND '.join(conds)} "
            "ORDER BY "
            "  CASE absence_significance "
            "    WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END "
            "LIMIT %s",
            params
        )
        return _rows(cur)


def query_distinctive_absences(conn, chart_id: str, ayanamsha_id: str,
                                 top_k: int = 5) -> List[Dict]:
    """
    Return the most diagnostically significant absences — high significance first.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT absence_id::TEXT, chart_id::TEXT, ayanamsha_id, "
            "absence_class, absent_feature, absence_significance, "
            "expected_if_present, classical_pattern_violated "
            "FROM l25_negative_space_map "
            "WHERE chart_id = %s::UUID AND ayanamsha_id = %s "
            "ORDER BY "
            "  CASE absence_significance "
            "    WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END "
            "LIMIT %s",
            [chart_id, ayanamsha_id, top_k]
        )
        return _rows(cur)


# ============================================================
# META-ε: Derivation Trail queries
# ============================================================

def query_derivation_trail(conn, chart_id: str, ayanamsha_id: str,
                            node_kind: Optional[str] = None,
                            limit: int = 100) -> List[Dict]:
    """
    Return derivation graph nodes for a chart+ayanamsha.
    Optionally filter by node_kind ('l1_fact','l25_claim','mcp_tool_output','external_input').
    """
    conds = ["n.chart_id = %s::UUID", "n.ayanamsha_id = %s"]
    params = [chart_id, ayanamsha_id]
    if node_kind:
        conds.append("n.node_kind = %s")
        params.append(node_kind)
    params.append(limit)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT n.node_id::TEXT, n.chart_id::TEXT, n.ayanamsha_id, "
            "n.node_kind, n.node_label, n.source_table, n.source_row_id, "
            "n.claim_text, n.confidence, n.computed_at::TEXT "
            "FROM l25_derivation_graph_nodes n "
            f"WHERE {' AND '.join(conds)} "
            "ORDER BY n.node_kind, n.confidence DESC NULLS LAST "
            "LIMIT %s",
            params
        )
        return _rows(cur)


def query_derivation_upstream(conn, node_id: str, depth: int = 3) -> List[Dict]:
    """
    Walk upstream derivation edges from a node (find what it derives from).
    Uses recursive CTE up to `depth` hops.
    """
    with conn.cursor() as cur:
        cur.execute("""
            WITH RECURSIVE upstream AS (
              SELECT
                source_node_id,
                target_node_id,
                edge_kind,
                0 AS depth
              FROM l25_derivation_graph_edges
              WHERE target_node_id = %s::UUID

              UNION ALL

              SELECT
                e.source_node_id,
                e.target_node_id,
                e.edge_kind,
                u.depth + 1
              FROM l25_derivation_graph_edges e
              JOIN upstream u ON e.target_node_id = u.source_node_id
              WHERE u.depth < %s
            )
            SELECT DISTINCT
              n.node_id::TEXT,
              n.node_kind,
              n.node_label,
              n.claim_text,
              n.source_table,
              n.source_row_id,
              u.depth
            FROM upstream u
            JOIN l25_derivation_graph_nodes n ON n.node_id = u.source_node_id
            ORDER BY u.depth, n.node_kind
        """, [node_id, depth])
        return _rows(cur)


def query_supporting_l1_facts(conn, node_id: str) -> List[Dict]:
    """
    Return all L1 fact nodes that ultimately support a given claim node
    (via upstream derivation walk, filtered to l1_fact kind only).
    """
    with conn.cursor() as cur:
        cur.execute("""
            WITH RECURSIVE upstream AS (
              SELECT source_node_id, 0 AS depth
              FROM l25_derivation_graph_edges
              WHERE target_node_id = %s::UUID
              UNION ALL
              SELECT e.source_node_id, u.depth + 1
              FROM l25_derivation_graph_edges e
              JOIN upstream u ON e.target_node_id = u.source_node_id
              WHERE u.depth < 10
            )
            SELECT DISTINCT
              n.node_id::TEXT,
              n.node_label,
              n.source_table,
              n.source_row_id,
              n.claim_text,
              n.confidence
            FROM upstream u
            JOIN l25_derivation_graph_nodes n ON n.node_id = u.source_node_id
            WHERE n.node_kind = 'l1_fact'
            ORDER BY n.confidence DESC NULLS LAST
        """, [node_id])
        return _rows(cur)
