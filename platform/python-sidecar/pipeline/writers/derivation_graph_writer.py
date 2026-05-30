"""META-ε: Derivation Trail Writer (Φ-TRAIL) — L1→L2.5 claim DAG.

Implements META_ENHANCEMENTS_SPEC_v1_0.md §5.
Writes to l25_derivation_graph_nodes and l25_derivation_graph_edges.
All inserts use ON CONFLICT DO NOTHING.
"""
import uuid
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def write_derivation_nodes_from_chart_facts(conn, chart_id: str, ayanamsha_id: str, build_id: str) -> int:
    """Seed derivation graph with L1 fact nodes from chart_facts."""
    count = 0
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT fact_id::TEXT, fact_category, fact_key, fact_value_text, confidence_score
                FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                LIMIT 1000
            """, [chart_id, ayanamsha_id])
            facts = cur.fetchall()
        except Exception as e:
            logger.debug(f"chart_facts for derivation nodes: {e}")
            conn.rollback()
            facts = []

        for (fact_id, category, key, value, confidence) in facts:
            cur.execute("""
                INSERT INTO l25_derivation_graph_nodes
                  (node_id, chart_id, ayanamsha_id, build_id,
                   node_kind, node_label, source_table, source_row_id,
                   claim_text, confidence, computed_at)
                VALUES (%s,%s::UUID,%s,%s::UUID,'l1_fact',%s,'chart_facts',%s,%s,%s,NOW())
                ON CONFLICT (chart_id, ayanamsha_id, node_kind, source_table, source_row_id) DO NOTHING
            """, (str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                  f"{category}/{key}", fact_id,
                  f"{key}={value}", float(confidence or 0.5)))
            count += cur.rowcount

    conn.commit()
    logger.info(f"META-ε: {count} L1 fact derivation nodes written")
    return count


def write_derivation_edges_for_patterns(conn, chart_id: str, ayanamsha_id: str, build_id: str) -> int:
    """
    Create 'derives_from' edges from l25_pattern_catalog entries → chart_facts nodes.
    Matches by source_row_id across pattern catalog and derivation nodes.
    """
    count = 0
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT p.pattern_catalog_id::TEXT, p.source_row_id, n.node_id::TEXT
                FROM l25_pattern_catalog p
                JOIN l25_derivation_graph_nodes n
                  ON n.source_row_id = p.source_row_id
                 AND n.chart_id = p.chart_id
                 AND n.ayanamsha_id = p.ayanamsha_id
                WHERE p.chart_id = %s AND p.ayanamsha_id = %s
                LIMIT 500
            """, [chart_id, ayanamsha_id])
            links = cur.fetchall()
        except Exception as e:
            logger.debug(f"pattern → derivation edge links: {e}")
            conn.rollback()
            links = []

        for (pattern_id, _source_row, node_id) in links:
            # Ensure l25_claim node exists for the pattern
            new_node_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO l25_derivation_graph_nodes
                  (node_id, chart_id, ayanamsha_id, build_id, node_kind, node_label,
                   source_table, source_row_id, computed_at)
                VALUES (%s,%s::UUID,%s,%s::UUID,'l25_claim',%s,'l25_pattern_catalog',%s,NOW())
                ON CONFLICT (chart_id, ayanamsha_id, node_kind, source_table, source_row_id) DO NOTHING
                RETURNING node_id
            """, (new_node_id, chart_id, ayanamsha_id, build_id,
                  f'pattern_{pattern_id[:8]}', pattern_id))
            row = cur.fetchone()
            if not row:
                # Already existed — look it up
                cur.execute("""
                    SELECT node_id::TEXT FROM l25_derivation_graph_nodes
                    WHERE chart_id = %s AND ayanamsha_id = %s
                      AND node_kind = 'l25_claim' AND source_table = 'l25_pattern_catalog'
                      AND source_row_id = %s
                    LIMIT 1
                """, [chart_id, ayanamsha_id, pattern_id])
                existing = cur.fetchone()
                if not existing:
                    continue
                claim_node_id = existing[0]
            else:
                claim_node_id = str(row[0])

            cur.execute("""
                INSERT INTO l25_derivation_graph_edges
                  (edge_id, chart_id, ayanamsha_id, build_id,
                   source_node_id, target_node_id, edge_kind, computed_at)
                VALUES (%s,%s::UUID,%s,%s::UUID,%s::UUID,%s::UUID,'derives_from',NOW())
                ON CONFLICT (source_node_id, target_node_id, edge_kind) DO NOTHING
            """, (str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                  claim_node_id, node_id))
            count += cur.rowcount

    conn.commit()
    logger.info(f"META-ε: {count} derivation edges written (pattern → L1)")
    return count


def write_derivation_nodes_from_msr_signals(conn, chart_id: str, ayanamsha_id: str, build_id: str) -> int:
    """Seed derivation nodes from msr_signals (l25_claim kind)."""
    count = 0
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT signal_id::TEXT, signal_code, signal_category, confidence_score
                FROM msr_signals
                WHERE chart_id = %s AND ayanamsha_id = %s
                LIMIT 600
            """, [chart_id, ayanamsha_id])
            signals = cur.fetchall()
        except Exception as e:
            logger.debug(f"msr_signals for derivation nodes: {e}")
            conn.rollback()
            signals = []

        for (sig_id, code, category, confidence) in signals:
            cur.execute("""
                INSERT INTO l25_derivation_graph_nodes
                  (node_id, chart_id, ayanamsha_id, build_id,
                   node_kind, node_label, source_table, source_row_id,
                   confidence, computed_at)
                VALUES (%s,%s::UUID,%s,%s::UUID,'l25_claim',%s,'msr_signals',%s,%s,NOW())
                ON CONFLICT (chart_id, ayanamsha_id, node_kind, source_table, source_row_id) DO NOTHING
            """, (str(uuid.uuid4()), chart_id, ayanamsha_id, build_id,
                  f"msr/{code or sig_id[:12]}", sig_id, float(confidence or 0.5)))
            count += cur.rowcount

    conn.commit()
    logger.info(f"META-ε: {count} MSR signal derivation nodes written")
    return count
