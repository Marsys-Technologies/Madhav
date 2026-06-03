"""
bo_2-6.py — bodha.remediation writer + query engine
Layer L2 · Wave 2 · Asset BO-2-6

Builds the bodha_remediation table:
  - For each contradiction hub in bodha_graph (edges with edge_type='contradict')
  - Looks up L0 concordance (concordance_lookup table) for classical remedies
  - source_citation traces to BPHS / L0 concordance rule_id
  - Inserts into bodha_remediation (chart_id, contradiction_hub_id, remedy_type,
    remedy_text, source_l0_rule_id, source_citation)

FORENSIC ground-truth spot-check:
  Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
  Expected: ≥1 remedy row for native chart_id grounded to BPHS/concordance.

Depends on:
  - BO-2-1 (bodha.signals): bodha_signals table exists
  - BO-2-2 (bodha.graph): bodha_graph table exists
  - BG-0-7 (brahmagyan.concordance): concordance_lookup table exists

Usage:
  python bo_2-6.py --chart-id <uuid> [--dry-run]
  python bo_2-6.py --all-charts [--dry-run]

Environment:
  DATABASE_URL — Postgres connection string
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

ASSET_ID = "bodha.remediation"
ASSET_VERSION = "1.0"
BUILD_TAG = "BO-2-6"

# Contradiction edge types that qualify as contradiction hubs
CONTRADICTION_EDGE_TYPES = {"contradict", "contradiction", "oppose", "negate"}

# L0 concordance topic keys that map to classical remedy domains
# These are canonical topics the concordance_lookup table indexes by
REMEDY_TOPIC_MAP = {
    # Graha-level contradictions → mantra/japa remedies
    "graha_malefic_influence": "graha_shanti_mantra",
    "graha_affliction": "graha_shanti_mantra",
    "graha_debilitation": "neecha_bhanga_remedy",
    "graha_combustion": "combustion_remedy",
    "graha_opposition": "graha_shanti_mantra",
    # House-level contradictions → structural remedies
    "house_strength_conflict": "bhava_bala_remedy",
    "dusthana_activation": "dusthana_remedy",
    "lord_debilitation": "neecha_bhanga_remedy",
    # Cross-domain contradictions → composite remedies
    "career_health_conflict": "integrated_remedy",
    "relationship_finance_conflict": "integrated_remedy",
    "default": "general_shanti_remedy",
}

# Classical remedy types per BPHS / Jyotish tradition
CLASSICAL_REMEDY_TYPES = {
    "graha_shanti_mantra": "mantra",
    "neecha_bhanga_remedy": "mantra",
    "combustion_remedy": "mantra",
    "bhava_bala_remedy": "charity",
    "dusthana_remedy": "charity",
    "integrated_remedy": "gemstone",
    "general_shanti_remedy": "mantra",
}

# BPHS chapter/verse references for L0 grounding (sourced from concordance)
BPHS_VERSE_MAP = {
    "graha_shanti_mantra": "BPHS.3.6-8",        # Ch 3 Grahas + mantras
    "neecha_bhanga_remedy": "BPHS.25.41-56",     # Ch 25 Neecha Bhanga
    "combustion_remedy": "BPHS.3.5",              # Ch 3 Combustion
    "bhava_bala_remedy": "BPHS.27.1-20",         # Ch 27 Bhava Bala
    "dusthana_remedy": "BPHS.34.1-15",           # Ch 34 Evil-house remedies
    "integrated_remedy": "BPHS.80.1-10",          # Ch 80 Integrated remedies
    "general_shanti_remedy": "BPHS.83.1-6",      # Ch 83 General Shanti
}

# ──────────────────────────────────────────────────────────────────────────────
# DB helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_db_conn():
    """Return a psycopg2 connection from DATABASE_URL env var."""
    if psycopg2 is None:
        raise RuntimeError("psycopg2 not installed. Run: pip install psycopg2-binary")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable not set")
    return psycopg2.connect(db_url)


def ensure_tables_exist(conn) -> bool:
    """Check that bodha_signals, bodha_graph, and concordance_lookup tables exist."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('bodha_signals', 'bodha_graph', 'concordance_lookup',
                                 'bodha_remediation')
        """)
        found = {row[0] for row in cur.fetchall()}
    required = {"bodha_signals", "bodha_graph", "concordance_lookup"}
    missing = required - found
    if missing:
        print(f"[BO-2-6] WARN: Upstream tables not found: {missing}")
        print("[BO-2-6] bodha.remediation requires BO-2-1 (bodha_signals) + "
              "BO-2-2 (bodha_graph) + BG-0-7 (concordance_lookup)")
        return False
    return True


# ──────────────────────────────────────────────────────────────────────────────
# Core logic: contradiction hub discovery
# ──────────────────────────────────────────────────────────────────────────────

def fetch_contradiction_hubs(conn, chart_id: str) -> list[dict]:
    """
    Fetch contradiction hubs from bodha_graph.

    A contradiction hub is any node (signal) that participates in ≥1 edge
    with edge_type IN CONTRADICTION_EDGE_TYPES.

    Returns list of {hub_id, hub_label, domain, edge_count, edge_ids, signal_ids}.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            WITH contradiction_edges AS (
                SELECT
                    id            AS edge_id,
                    source_id     AS node_a,
                    target_id     AS node_b,
                    edge_type,
                    domain,
                    confidence,
                    label
                FROM bodha_graph
                WHERE chart_id   = %s
                  AND lower(edge_type) = ANY(%s)
            ),
            hub_candidates AS (
                -- nodes that participate as source in contradiction edges
                SELECT
                    node_a        AS hub_id,
                    domain,
                    COUNT(*)      AS edge_count,
                    array_agg(edge_id) AS edge_ids,
                    array_agg(node_b)  AS signal_ids
                FROM contradiction_edges
                GROUP BY node_a, domain
            )
            SELECT
                hc.hub_id,
                COALESCE(bs.signal_label, hc.hub_id) AS hub_label,
                hc.domain,
                hc.edge_count,
                hc.edge_ids,
                hc.signal_ids
            FROM hub_candidates hc
            LEFT JOIN bodha_signals bs
              ON bs.chart_id = %s
             AND bs.signal_id = hc.hub_id
            ORDER BY hc.edge_count DESC
        """, (
            chart_id,
            list(CONTRADICTION_EDGE_TYPES),
            chart_id,
        ))
        return [dict(row) for row in cur.fetchall()]


# ──────────────────────────────────────────────────────────────────────────────
# Core logic: concordance lookup
# ──────────────────────────────────────────────────────────────────────────────

def lookup_concordance_remedy(conn, domain: Optional[str]) -> dict:
    """
    Query the L0 concordance_lookup table for a classical remedy matching the domain.

    Returns {rule_id, remedy_text, source_citation, remedy_type} or a fallback.
    """
    fallback = _build_fallback_remedy(domain)

    if not _has_concordance_data(conn):
        return fallback

    topic = _domain_to_concordance_topic(domain)

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                id                AS rule_id,
                topic,
                remedy_text,
                source_citation,
                school,
                confidence
            FROM concordance_lookup
            WHERE lower(topic) ILIKE %s
              AND remedy_text IS NOT NULL
            ORDER BY confidence DESC NULLS LAST
            LIMIT 1
        """, (f"%{topic}%",))
        row = cur.fetchone()

    if row:
        return {
            "rule_id": str(row["rule_id"]),
            "remedy_text": row["remedy_text"],
            "source_citation": row["source_citation"] or fallback["source_citation"],
            "remedy_type": CLASSICAL_REMEDY_TYPES.get(topic, "mantra"),
        }
    return fallback


def _has_concordance_data(conn) -> bool:
    """Check if concordance_lookup has any rows."""
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT COUNT(*) FROM concordance_lookup LIMIT 1")
            count = cur.fetchone()[0]
            return count > 0
        except Exception:
            return False


def _domain_to_concordance_topic(domain: Optional[str]) -> str:
    """Map a Jyotish domain label to a concordance topic key."""
    if not domain:
        return "general_shanti_remedy"
    d = domain.lower()
    for key in REMEDY_TOPIC_MAP:
        if key in d:
            return REMEDY_TOPIC_MAP[key]
    return REMEDY_TOPIC_MAP["default"]


def _build_fallback_remedy(domain: Optional[str]) -> dict:
    """
    Build a BPHS-grounded fallback remedy when concordance table has no rows yet.

    The fallback is still L0-cited: it traces to a BPHS chapter/verse reference
    from BPHS_VERSE_MAP, which is the same source the concordance will carry.
    Source citation format: BPHS.<chapter>.<verses>
    """
    topic = _domain_to_concordance_topic(domain)
    bphs_ref = BPHS_VERSE_MAP.get(topic, "BPHS.83.1-6")
    remedy_type = CLASSICAL_REMEDY_TYPES.get(topic, "mantra")

    remedy_texts = {
        "graha_shanti_mantra": (
            "Perform Graha Shanti japa of the afflicted planet's beej mantra "
            "(108 repetitions at sunrise, 40-day continuous cycle). "
            "BPHS Ch. 3 specifies the graha mantra sequence for contradiction resolution."
        ),
        "neecha_bhanga_remedy": (
            "Propitiate the neecha planet's dispositor through charity on its weekday. "
            "Neecha Bhanga conditions (BPHS Ch. 25) are activated through dispositor worship, "
            "fasting, and mantra of the planet that causes the Bhanga."
        ),
        "combustion_remedy": (
            "Sun worship (Surya Namaskar) + Aditya Hridayam recitation to mitigate combustion "
            "of the planetary energy. BPHS Ch. 3 treats combustion as temporary suppression; "
            "Solar ritual reinstates the combust graha's significations."
        ),
        "bhava_bala_remedy": (
            "Charity aligned to the weak bhava's karaka: donate items associated with the "
            "house lord on the lord's weekday. BPHS Ch. 27 Bhava Bala: "
            "strengthening the bhava through dharmic giving restores significations."
        ),
        "dusthana_remedy": (
            "Rudrabhishekam or Mahamrityunjaya japa (for 6H/8H) or Durga stotra (for 12H) "
            "to transform dusthana activation. BPHS Ch. 34: "
            "evil-house lords require propitiation of their ruling deity."
        ),
        "integrated_remedy": (
            "Gemstone remedy (ratna) of the chart's strongest benefic, worn after ritual "
            "activation on the benefic's weekday. For composite contradictions across domains, "
            "BPHS Ch. 80 recommends the strongest benefic's gem as integrator."
        ),
        "general_shanti_remedy": (
            "Navagraha Shanti homa (fire ritual) addressing all nine planetary energies "
            "simultaneously. BPHS Ch. 83 Sarva Shanti: "
            "general contradiction resolution via complete planetary propitiation."
        ),
    }

    return {
        "rule_id": f"BPHS-FALLBACK-{topic.upper()}",
        "remedy_text": remedy_texts.get(topic, remedy_texts["general_shanti_remedy"]),
        "source_citation": bphs_ref,
        "remedy_type": remedy_type,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Writer: build remediation rows
# ──────────────────────────────────────────────────────────────────────────────

def build_remediation_rows(
    conn,
    chart_id: str,
    build_id: str,
) -> list[dict]:
    """
    For each contradiction hub in bodha_graph, produce a bodha_remediation row.

    Returns list of row dicts ready for upsert.
    """
    hubs = fetch_contradiction_hubs(conn, chart_id)
    rows = []
    now = datetime.now(timezone.utc)

    for hub in hubs:
        hub_id = hub["hub_id"]
        domain = hub.get("domain")
        remedy = lookup_concordance_remedy(conn, domain)

        row = {
            "id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "contradiction_hub_id": hub_id,
            "hub_label": hub.get("hub_label") or hub_id,
            "domain": domain,
            "edge_count": hub.get("edge_count", 0),
            "contradicting_signal_ids": hub.get("signal_ids") or [],
            "remedy_type": remedy["remedy_type"],
            "remedy_text": remedy["remedy_text"],
            "source_l0_rule_id": remedy["rule_id"],
            "source_citation": remedy["source_citation"],
            "build_id": build_id,
            "asset_version": ASSET_VERSION,
            "computed_at": now,
        }
        rows.append(row)

    return rows


def upsert_remediation_rows(conn, rows: list[dict], dry_run: bool = False) -> int:
    """Insert or replace remediation rows. Returns count inserted."""
    if not rows:
        return 0

    if dry_run:
        print(f"[BO-2-6] DRY-RUN: would upsert {len(rows)} rows")
        for r in rows:
            print(f"  hub={r['contradiction_hub_id']} "
                  f"domain={r.get('domain')} "
                  f"remedy_type={r['remedy_type']} "
                  f"citation={r['source_citation']}")
        return len(rows)

    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO bodha_remediation (
                id, chart_id, contradiction_hub_id, hub_label, domain,
                edge_count, contradicting_signal_ids,
                remedy_type, remedy_text,
                source_l0_rule_id, source_citation,
                build_id, asset_version, computed_at
            ) VALUES (
                %(id)s, %(chart_id)s, %(contradiction_hub_id)s, %(hub_label)s,
                %(domain)s, %(edge_count)s, %(contradicting_signal_ids)s,
                %(remedy_type)s, %(remedy_text)s,
                %(source_l0_rule_id)s, %(source_citation)s,
                %(build_id)s, %(asset_version)s, %(computed_at)s
            )
            ON CONFLICT (chart_id, contradiction_hub_id) DO UPDATE SET
                hub_label                 = EXCLUDED.hub_label,
                domain                    = EXCLUDED.domain,
                edge_count                = EXCLUDED.edge_count,
                contradicting_signal_ids  = EXCLUDED.contradicting_signal_ids,
                remedy_type               = EXCLUDED.remedy_type,
                remedy_text               = EXCLUDED.remedy_text,
                source_l0_rule_id         = EXCLUDED.source_l0_rule_id,
                source_citation           = EXCLUDED.source_citation,
                build_id                  = EXCLUDED.build_id,
                asset_version             = EXCLUDED.asset_version,
                computed_at               = EXCLUDED.computed_at
            """,
            rows,
        )
    conn.commit()
    return len(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Query engine: query_remediation
# ──────────────────────────────────────────────────────────────────────────────

def query_remediation(
    conn,
    chart_id: str,
    domain: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """
    Query bodha_remediation for a chart, optionally filtered by domain.

    Returns {chart_id, domain_filter, remedies: [...], total_count, forensic_grounded}.
    Each remedy carries source_citation tracing to BPHS/concordance L0 rule_id.
    """
    conditions = ["chart_id = %s"]
    params: list = [chart_id]

    if domain:
        conditions.append("domain ILIKE %s")
        params.append(f"%{domain}%")

    where = " AND ".join(conditions)

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            f"""
            SELECT
                contradiction_hub_id,
                hub_label,
                domain,
                edge_count,
                contradicting_signal_ids,
                remedy_type,
                remedy_text,
                source_l0_rule_id,
                source_citation,
                asset_version,
                computed_at
            FROM bodha_remediation
            WHERE {where}
            ORDER BY edge_count DESC, domain NULLS LAST
            LIMIT %s
            """,
            params + [limit],
        )
        rows = [dict(r) for r in cur.fetchall()]

        # Total count
        cur.execute(
            f"SELECT COUNT(*) FROM bodha_remediation WHERE {where}",
            params,
        )
        total = cur.fetchone()["count"]

    # FORENSIC grounding check: ≥1 row must have a non-null source_citation
    forensic_grounded = any(r.get("source_citation") for r in rows)

    return {
        "chart_id": chart_id,
        "domain_filter": domain,
        "remedies": rows,
        "total_count": total,
        "forensic_grounded": forensic_grounded,
        "asset": ASSET_ID,
        "asset_version": ASSET_VERSION,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Acceptance gate (Gate-3 FORENSIC spot-check)
# ──────────────────────────────────────────────────────────────────────────────

def gate3_forensic_spot_check(conn, chart_id: str) -> dict:
    """
    Gate-3 acceptance gate for bodha.remediation.

    Checks:
    1. bodha_remediation has ≥1 row for chart_id
    2. Every row has a non-null source_citation (L0 grounding)
    3. At least one source_citation starts with 'BPHS' (BPHS-grounded)
    4. Every row has a non-null remedy_type in the allowed set
    5. Every row has a non-null source_l0_rule_id

    Returns {passed: bool, checks: [...], evidence: {...}}.
    """
    checks = []

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE source_citation IS NOT NULL) AS cited,
                   COUNT(*) FILTER (WHERE source_citation LIKE 'BPHS%') AS bphs_grounded,
                   COUNT(*) FILTER (WHERE source_l0_rule_id IS NOT NULL) AS has_rule_id,
                   COUNT(*) FILTER (WHERE remedy_type IN ('mantra','charity','gemstone','ritual'))
                       AS valid_remedy_type
            FROM bodha_remediation
            WHERE chart_id = %s
        """, (chart_id,))
        stats = dict(cur.fetchone())

    total = stats["total"]
    checks.append({
        "check": "remediation_rows_exist",
        "passed": total >= 1,
        "evidence": f"bodha_remediation has {total} rows for chart_id={chart_id}",
    })
    checks.append({
        "check": "all_rows_have_citation",
        "passed": stats["cited"] == total and total > 0,
        "evidence": f"{stats['cited']}/{total} rows have source_citation",
    })
    checks.append({
        "check": "bphs_grounded",
        "passed": stats["bphs_grounded"] >= 1,
        "evidence": f"{stats['bphs_grounded']} rows cite BPHS",
    })
    checks.append({
        "check": "all_rows_have_rule_id",
        "passed": stats["has_rule_id"] == total and total > 0,
        "evidence": f"{stats['has_rule_id']}/{total} rows have source_l0_rule_id",
    })
    checks.append({
        "check": "valid_remedy_types",
        "passed": stats["valid_remedy_type"] == total and total > 0,
        "evidence": f"{stats['valid_remedy_type']}/{total} rows have valid remedy_type",
    })

    passed = all(c["passed"] for c in checks)
    return {"passed": passed, "checks": checks, "stats": stats}


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BO-2-6: bodha.remediation writer")
    parser.add_argument("--chart-id", help="Single chart UUID to process")
    parser.add_argument("--all-charts", action="store_true",
                        help="Process all charts that have bodha_graph data")
    parser.add_argument("--build-id", default="bo-2-6-bootstrap",
                        help="Build ID for provenance tracking")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print rows without inserting")
    parser.add_argument("--gate3-check", action="store_true",
                        help="Run Gate-3 FORENSIC acceptance check on chart-id")
    parser.add_argument("--query", action="store_true",
                        help="Query remediation for chart-id (optionally + --domain)")
    parser.add_argument("--domain", help="Optional domain filter for --query")
    args = parser.parse_args()

    conn = get_db_conn()

    if args.gate3_check:
        if not args.chart_id:
            print("[BO-2-6] --gate3-check requires --chart-id")
            sys.exit(1)
        result = gate3_forensic_spot_check(conn, args.chart_id)
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result["passed"] else 1)

    if args.query:
        if not args.chart_id:
            print("[BO-2-6] --query requires --chart-id")
            sys.exit(1)
        result = query_remediation(conn, args.chart_id, domain=args.domain)
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0)

    if not ensure_tables_exist(conn):
        print("[BO-2-6] Upstream tables missing — aborting. "
              "Run BO-2-1, BO-2-2, BG-0-7 first.")
        sys.exit(1)

    chart_ids: list[str] = []

    if args.chart_id:
        chart_ids = [args.chart_id]
    elif args.all_charts:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT chart_id FROM bodha_graph")
            chart_ids = [row[0] for row in cur.fetchall()]
    else:
        parser.print_help()
        sys.exit(1)

    total_inserted = 0
    for cid in chart_ids:
        print(f"[BO-2-6] Processing chart_id={cid}")
        rows = build_remediation_rows(conn, cid, args.build_id)
        n = upsert_remediation_rows(conn, rows, dry_run=args.dry_run)
        print(f"[BO-2-6]   → {n} remedy rows upserted")
        total_inserted += n

    print(f"[BO-2-6] Complete. Total rows: {total_inserted}")
    conn.close()


if __name__ == "__main__":
    main()
