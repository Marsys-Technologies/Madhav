"""
brahmagyan.bodha.bo22 — BRAHMA-BO-2-2: bodha.graph (CGM signal graph)
=======================================================================

Builds and queries the CGM signal graph — valenced edges (DISPOSITED_BY,
NAKSHATRA_LORD_IS, ASPECTS_3RD/4TH/8TH, REINFORCES, CONTRADICTS, MODULATES)
between CGM nodes (PLN.*, HSE.*, SGN.*, etc.) for a given chart.

Contract (BRAHMA_L1_L5_REGISTRY_SEED §C):
  - owns: CGM signal graph — valenced edges between signals
  - tool: cgm_subgraph(chart_id, signal_ids?) → edges with provenance
  - table: bodha_graph (chart_id, from_signal_id, to_signal_id, edge_type,
           weight, source_citation)
  - acceptance gate: valenced edges present; traversal returns provenance;
                     no self-loops
  - FORENSIC: at least 5 edges for native's chart

Source data:
  22 reconciled edges from 035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json
  (Batch 2, session Madhav_M2A_Exec_5/6; 0 P2 violations)
  Note: CGM_EDGE_014 (PLN.VENUS → PLN.VENUS NAKSHATRA_LORD_IS self-loop) is
  excluded per the no-self-loops contract constraint.

Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
  chart_id: 482012f1-710e-4a25-994a-93821f5871aa (FORENSIC canonical)

Usage:
    # Seed native chart
    python -m brahmagyan.bodha.bo22 seed --chart-id 482012f1-...

    # Query subgraph
    python -m brahmagyan.bodha.bo22 query --chart-id 482012f1-... \\
        --signal-ids PLN.SATURN PLN.MARS

    # Run acceptance gate
    python -m brahmagyan.bodha.bo22 gate --chart-id 482012f1-...
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Native chart constant ──────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)

# ── Canonical edge data from cgm_edges_manifest_v1_0.json ─────────────────────
# 22 reconciled edges; CGM_EDGE_014 (self-loop PLN.VENUS→PLN.VENUS) excluded
# per contract constraint (no self-loops). 21 edges remain for seeding.
#
# Weight conventions:
#   DISPOSITED_BY     → 0.90 (fundamental sign-lord relationship)
#   NAKSHATRA_LORD_IS → 0.80 (stellar nakshatra-lord relationship)
#   ASPECTS_3RD       → 0.85 (Saturn 3rd-house special aspect)
#   ASPECTS_4TH       → 0.85 (Mars 4th-house special aspect)
#   ASPECTS_8TH       → 0.85 (Mars 8th-house special aspect)

# Gate-1 contract enum (lowercase, matches DB CHECK constraint):
#   reinforce  — two signals amplify each other's theme
#   contradict — two signals pull in opposite directions
#   modulate   — one signal contextually modulates another
#   amplify    — one signal intensifies another's expression
#   suppress   — one signal dampens or blocks another
VALID_EDGE_TYPES: frozenset[str] = frozenset(
    {"reinforce", "contradict", "modulate", "amplify", "suppress"}
)

# Map legacy manifest edge_type labels → Gate-1 contract enum
_EDGE_TYPE_MAP: dict[str, str] = {
    "DISPOSITED_BY":    "modulate",   # sign-lord modulates planet's expression
    "NAKSHATRA_LORD_IS": "amplify",   # nakshatra lord amplifies planet's significations
    "ASPECTS_3RD":      "reinforce",  # Saturn 3rd drishti reinforces target planet's themes
    "ASPECTS_4TH":      "reinforce",  # Mars 4th drishti reinforces target planet's themes
    "ASPECTS_8TH":      "reinforce",  # Mars 8th drishti reinforces (pressurises) themes
    "REINFORCES":       "reinforce",
    "CONTRADICTS":      "contradict",
    "MODULATES":        "modulate",
}

WEIGHT_MAP: dict[str, float] = {
    "modulate":   0.90,  # DISPOSITED_BY: fundamental sign-lord relationship
    "amplify":    0.80,  # NAKSHATRA_LORD_IS: stellar lord amplification
    "reinforce":  0.85,  # ASPECTS_*: aspect-based reinforcement
    "contradict": 0.70,
    "suppress":   0.70,
}


def _normalise_edge_type(raw: str) -> str:
    """Map a raw/legacy edge_type to the Gate-1 contract enum value."""
    if raw in VALID_EDGE_TYPES:
        return raw
    mapped = _EDGE_TYPE_MAP.get(raw)
    if mapped:
        return mapped
    raise ValueError(
        f"Unknown edge_type {raw!r}. Valid values: {sorted(VALID_EDGE_TYPES)}"
    )

# Canonical edges (from cgm_edges_manifest_v1_0.json, batch 2 reconciled)
# CGM_EDGE_014 excluded: PLN.VENUS→PLN.VENUS self-loop (Venus NAKSHATRA_LORD_IS Venus)
# edge_type values use Gate-1 contract enum (lowercase):
#   modulate  ← DISPOSITED_BY  (sign-lord modulates planet's expression)
#   amplify   ← NAKSHATRA_LORD_IS (nakshatra lord amplifies significations)
#   reinforce ← ASPECTS_3RD/4TH/8TH (aspect reinforces target's themes)
# source_citation cites both signal endpoints per BO-2-2 contract.
CANONICAL_EDGES: list[dict[str, str]] = [
    {
        "edge_id": "CGM_EDGE_001",
        "from_signal_id": "PLN.SUN",
        "to_signal_id": "PLN.SATURN",
        "edge_type": "modulate",
        "source_citation": "L2:BO-2-1:PLN.SUN + L2:BO-2-1:PLN.SATURN | FORENSIC_v8_0 §2.1: Sun in Capricorn (291.96°); Saturn rules Capricorn — sign-lord modulates Sun's expression",
    },
    {
        "edge_id": "CGM_EDGE_002",
        "from_signal_id": "PLN.MOON",
        "to_signal_id": "PLN.SATURN",
        "edge_type": "modulate",
        "source_citation": "L2:BO-2-1:PLN.MOON + L2:BO-2-1:PLN.SATURN | FORENSIC_v8_0 §2.1: Moon in Aquarius (327.05°); Saturn rules Aquarius — sign-lord modulates Moon's expression",
    },
    {
        "edge_id": "CGM_EDGE_003",
        "from_signal_id": "PLN.MARS",
        "to_signal_id": "PLN.VENUS",
        "edge_type": "modulate",
        "source_citation": "L2:BO-2-1:PLN.MARS + L2:BO-2-1:PLN.VENUS | FORENSIC_v8_0 §2.1: Mars in Libra (198.53°); Venus rules Libra — sign-lord modulates Mars's expression",
    },
    {
        "edge_id": "CGM_EDGE_004",
        "from_signal_id": "PLN.MERCURY",
        "to_signal_id": "PLN.SATURN",
        "edge_type": "modulate",
        "source_citation": "L2:BO-2-1:PLN.MERCURY + L2:BO-2-1:PLN.SATURN | FORENSIC_v8_0 §2.1: Mercury in Capricorn (270.84°); Saturn rules Capricorn — sign-lord modulates Mercury's expression",
    },
    {
        "edge_id": "CGM_EDGE_005",
        "from_signal_id": "PLN.VENUS",
        "to_signal_id": "PLN.JUPITER",
        "edge_type": "modulate",
        "source_citation": "L2:BO-2-1:PLN.VENUS + L2:BO-2-1:PLN.JUPITER | FORENSIC_v8_0 §2.1: Venus in Sagittarius (259.17°); Jupiter rules Sagittarius — sign-lord modulates Venus's expression",
    },
    {
        "edge_id": "CGM_EDGE_006",
        "from_signal_id": "PLN.SATURN",
        "to_signal_id": "PLN.VENUS",
        "edge_type": "modulate",
        "source_citation": "L2:BO-2-1:PLN.SATURN + L2:BO-2-1:PLN.VENUS | FORENSIC_v8_0 §2.1: Saturn in Libra (202.45°); Venus rules Libra — sign-lord modulates Saturn's expression",
    },
    {
        "edge_id": "CGM_EDGE_007",
        "from_signal_id": "PLN.RAHU",
        "to_signal_id": "PLN.VENUS",
        "edge_type": "modulate",
        "source_citation": "L2:BO-2-1:PLN.RAHU + L2:BO-2-1:PLN.VENUS | FORENSIC_v8_0 §2.1: Rahu in Taurus (49.03°); Venus rules Taurus — sign-lord modulates Rahu's expression",
    },
    {
        "edge_id": "CGM_EDGE_008",
        "from_signal_id": "PLN.KETU",
        "to_signal_id": "PLN.MARS",
        "edge_type": "modulate",
        "source_citation": "L2:BO-2-1:PLN.KETU + L2:BO-2-1:PLN.MARS | FORENSIC_v8_0 §2.1: Ketu in Scorpio (229.03°); Mars rules Scorpio (traditional) — sign-lord modulates Ketu's expression",
    },
    {
        "edge_id": "CGM_EDGE_009",
        "from_signal_id": "PLN.SUN",
        "to_signal_id": "PLN.MOON",
        "edge_type": "amplify",
        "source_citation": "L2:BO-2-1:PLN.SUN + L2:BO-2-1:PLN.MOON | FORENSIC_v8_0 §2.1: Sun in Shravana pada 4 (291.96°); Shravana lord = Moon — nakshatra lord amplifies Sun's significations",
    },
    {
        "edge_id": "CGM_EDGE_010",
        "from_signal_id": "PLN.MOON",
        "to_signal_id": "PLN.JUPITER",
        "edge_type": "amplify",
        "source_citation": "L2:BO-2-1:PLN.MOON + L2:BO-2-1:PLN.JUPITER | FORENSIC_v8_0 §2.1: Moon in Purva Bhadrapada pada 3 (327.05°); lord = Jupiter — nakshatra lord amplifies Moon's significations",
    },
    {
        "edge_id": "CGM_EDGE_011",
        "from_signal_id": "PLN.MARS",
        "to_signal_id": "PLN.RAHU",
        "edge_type": "amplify",
        "source_citation": "L2:BO-2-1:PLN.MARS + L2:BO-2-1:PLN.RAHU | FORENSIC_v8_0 §2.1: Mars in Swati pada 4 (198.53°); Swati lord = Rahu — nakshatra lord amplifies Mars's significations",
    },
    {
        "edge_id": "CGM_EDGE_012",
        "from_signal_id": "PLN.MERCURY",
        "to_signal_id": "PLN.SUN",
        "edge_type": "amplify",
        "source_citation": "L2:BO-2-1:PLN.MERCURY + L2:BO-2-1:PLN.SUN | FORENSIC_v8_0 §2.1: Mercury in Uttara Ashadha pada 2 (270.84°); lord = Sun — nakshatra lord amplifies Mercury's significations",
    },
    {
        "edge_id": "CGM_EDGE_013",
        "from_signal_id": "PLN.JUPITER",
        "to_signal_id": "PLN.KETU",
        "edge_type": "amplify",
        "source_citation": "L2:BO-2-1:PLN.JUPITER + L2:BO-2-1:PLN.KETU | FORENSIC_v8_0 §2.1: Jupiter in Moola pada 3 (249.81°); Moola lord = Ketu — nakshatra lord amplifies Jupiter's significations",
    },
    # CGM_EDGE_014 excluded: PLN.VENUS→PLN.VENUS self-loop (contract: no self-loops)
    {
        "edge_id": "CGM_EDGE_015",
        "from_signal_id": "PLN.SATURN",
        "to_signal_id": "PLN.JUPITER",
        "edge_type": "amplify",
        "source_citation": "L2:BO-2-1:PLN.SATURN + L2:BO-2-1:PLN.JUPITER | FORENSIC_v8_0 §2.1: Saturn in Vishakha pada 1 (202.45°); lord = Jupiter — nakshatra lord amplifies Saturn's significations",
    },
    {
        "edge_id": "CGM_EDGE_016",
        "from_signal_id": "PLN.RAHU",
        "to_signal_id": "PLN.MOON",
        "edge_type": "amplify",
        "source_citation": "L2:BO-2-1:PLN.RAHU + L2:BO-2-1:PLN.MOON | FORENSIC_v8_0 §2.1: Rahu in Rohini pada 3 (49.03°); Rohini lord = Moon — nakshatra lord amplifies Rahu's significations",
    },
    {
        "edge_id": "CGM_EDGE_017",
        "from_signal_id": "PLN.KETU",
        "to_signal_id": "PLN.MERCURY",
        "edge_type": "amplify",
        "source_citation": "L2:BO-2-1:PLN.KETU + L2:BO-2-1:PLN.MERCURY | FORENSIC_v8_0 §2.1: Ketu in Jyeshtha pada 1 (229.03°); lord = Mercury — nakshatra lord amplifies Ketu's significations",
    },
    {
        "edge_id": "CGM_EDGE_018",
        "from_signal_id": "PLN.SATURN",
        "to_signal_id": "PLN.JUPITER",
        "edge_type": "reinforce",
        "source_citation": (
            "L2:BO-2-1:PLN.SATURN + L2:BO-2-1:PLN.JUPITER | "
            "FORENSIC_v8_0 §2.1: Saturn in Libra H7 (202.45°); "
            "3rd drishti from H7 = H9 (Sagittarius); Jupiter in H9 (249.81°) — aspect reinforces Jupiter's themes"
        ),
    },
    {
        "edge_id": "CGM_EDGE_019",
        "from_signal_id": "PLN.SATURN",
        "to_signal_id": "PLN.VENUS",
        "edge_type": "reinforce",
        "source_citation": (
            "L2:BO-2-1:PLN.SATURN + L2:BO-2-1:PLN.VENUS | "
            "FORENSIC_v8_0 §2.1: Saturn in Libra H7 (202.45°); "
            "3rd drishti from H7 = H9 (Sagittarius); Venus in H9 (259.17°) — aspect reinforces Venus's themes"
        ),
    },
    {
        "edge_id": "CGM_EDGE_020",
        "from_signal_id": "PLN.MARS",
        "to_signal_id": "PLN.SUN",
        "edge_type": "reinforce",
        "source_citation": (
            "L2:BO-2-1:PLN.MARS + L2:BO-2-1:PLN.SUN | "
            "FORENSIC_v8_0 §2.1: Mars in Libra H7 (198.53°); "
            "4th drishti from H7 = H10 (Capricorn); Sun in H10 (291.96°) — aspect reinforces Sun's themes"
        ),
    },
    {
        "edge_id": "CGM_EDGE_021",
        "from_signal_id": "PLN.MARS",
        "to_signal_id": "PLN.MERCURY",
        "edge_type": "reinforce",
        "source_citation": (
            "L2:BO-2-1:PLN.MARS + L2:BO-2-1:PLN.MERCURY | "
            "FORENSIC_v8_0 §2.1: Mars in Libra H7 (198.53°); "
            "4th drishti from H7 = H10 (Capricorn); Mercury in H10 (270.84°) — aspect reinforces Mercury's themes"
        ),
    },
    {
        "edge_id": "CGM_EDGE_022",
        "from_signal_id": "PLN.MARS",
        "to_signal_id": "PLN.RAHU",
        "edge_type": "reinforce",
        "source_citation": (
            "L2:BO-2-1:PLN.MARS + L2:BO-2-1:PLN.RAHU | "
            "FORENSIC_v8_0 §2.1: Mars in Libra H7 (198.53°); "
            "8th drishti from H7 = H2 (Taurus); Rahu in H2 (49.03°) — aspect reinforces Rahu's themes"
        ),
    },
]

# ── DB helpers ─────────────────────────────────────────────────────────────────


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "[STOP] DATABASE_URL not set. "
            "Set DATABASE_URL=postgresql://... and ensure DB is reachable."
        )
    return url


def _get_conn():  # type: ignore[return]
    """Return a psycopg connection. Raises ImportError if psycopg not installed."""
    try:
        import psycopg  # type: ignore
        return psycopg.connect(_db_url())
    except ImportError as exc:
        raise ImportError(
            "psycopg (v3) is required for DB operations. "
            "Install with: pip install psycopg[binary]"
        ) from exc


# ── Core: load edges from manifest (file-based) ───────────────────────────────


def load_edges_from_manifest(manifest_path: str | Path) -> list[dict[str, Any]]:
    """
    Load edges from cgm_edges_manifest_v1_0.json.
    Returns the canonical 21 non-self-loop edges.
    Warns if a self-loop is encountered (CGM_EDGE_014).
    """
    path = Path(manifest_path)
    if not path.exists():
        logger.warning(
            "Manifest not found at %s — falling back to CANONICAL_EDGES constant", path
        )
        return list(CANONICAL_EDGES)

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    raw_edges = data.get("edges", [])
    edges: list[dict[str, Any]] = []
    skipped_self_loops = 0

    for e in raw_edges:
        src = e.get("source_node_id", "")
        tgt = e.get("target_node_id", "")
        if src == tgt:
            logger.warning(
                "Self-loop excluded per contract: %s (%s → %s)",
                e.get("edge_id"), src, tgt,
            )
            skipped_self_loops += 1
            continue

        edge_type = e.get("edge_type", "")
        citation_parts = [
            e.get("l1_source_section", ""),
            e.get("l1_derivation", ""),
        ]
        source_citation = ": ".join(p for p in citation_parts if p)

        edges.append(
            {
                "edge_id": e["edge_id"],
                "from_signal_id": src,
                "to_signal_id": tgt,
                "edge_type": edge_type,
                "source_citation": source_citation,
            }
        )

    if skipped_self_loops:
        logger.info("Skipped %d self-loop edge(s) per no-self-loops contract", skipped_self_loops)

    return edges


# ── Core: seed bodha_graph ────────────────────────────────────────────────────


def seed_bodha_graph(
    chart_id: str,
    *,
    edges: list[dict[str, Any]] | None = None,
    ayanamsha_id: str = "lahiri",
    build_id: str | None = None,
    dry_run: bool = False,
) -> int:
    """
    Seed bodha_graph for a given chart_id from the canonical edge set.

    Args:
        chart_id:     UUID of the chart (FORENSIC native: 482012f1-...).
        edges:        Override the canonical edge list (default: CANONICAL_EDGES).
        ayanamsha_id: Ayanamsha key (default 'lahiri').
        build_id:     Optional build provenance tag.
        dry_run:      If True, log rows without writing to DB.

    Returns:
        Number of rows upserted.
    """
    if edges is None:
        edges = list(CANONICAL_EDGES)

    now = datetime.now(timezone.utc).isoformat()
    if build_id is None:
        build_id = f"bo22-{now[:10]}"

    rows = []
    for e in edges:
        from_id = e["from_signal_id"]
        to_id = e["to_signal_id"]
        if from_id == to_id:
            logger.warning(
                "Skipping self-loop edge %s (%s → %s)", e["edge_id"], from_id, to_id
            )
            continue

        edge_type = _normalise_edge_type(e["edge_type"])
        weight = WEIGHT_MAP.get(edge_type, 0.70)
        rows.append(
            (
                e["edge_id"],          # edge_id
                chart_id,              # chart_id
                from_id,               # from_signal_id
                to_id,                 # to_signal_id
                edge_type,             # edge_type (normalised Gate-1 enum)
                weight,                # weight
                e["source_citation"],  # source_citation
                ayanamsha_id,          # ayanamsha_id
                build_id,              # build_id
            )
        )

    if dry_run:
        logger.info("[dry_run] Would upsert %d rows into bodha_graph", len(rows))
        for r in rows:
            logger.info("  %s | %s → %s | %s | w=%.2f", r[0], r[2], r[3], r[4], r[5])
        return len(rows)

    with _get_conn() as conn:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO bodha_graph
                    (edge_id, chart_id, from_signal_id, to_signal_id,
                     edge_type, weight, source_citation, ayanamsha_id, build_id, computed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (edge_id) DO UPDATE SET
                    chart_id       = EXCLUDED.chart_id,
                    from_signal_id = EXCLUDED.from_signal_id,
                    to_signal_id   = EXCLUDED.to_signal_id,
                    edge_type      = EXCLUDED.edge_type,
                    weight         = EXCLUDED.weight,
                    source_citation = EXCLUDED.source_citation,
                    ayanamsha_id   = EXCLUDED.ayanamsha_id,
                    build_id       = EXCLUDED.build_id,
                    computed_at    = NOW()
            """
            cur.executemany(sql, rows)
        conn.commit()

    logger.info("bodha_graph: upserted %d edges for chart_id=%s", len(rows), chart_id)
    return len(rows)


# ── Core: query subgraph ───────────────────────────────────────────────────────


def query_cgm_subgraph(
    chart_id: str,
    signal_ids: list[str] | None = None,
    *,
    edge_types: list[str] | None = None,
    hops: int = 1,
    ayanamsha_id: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve the CGM signal subgraph for a chart.

    Args:
        chart_id:    UUID of the chart.
        signal_ids:  Optional list of CGM node IDs to seed the traversal.
                     If None, returns all edges for the chart.
        edge_types:  Optional filter on edge_type (e.g. ['DISPOSITED_BY']).
        hops:        Traversal depth (default 1; 0 = no traversal, return seed edges only).
        ayanamsha_id: Optional filter on ayanamsha (default: all).

    Returns:
        {
          "chart_id": str,
          "signal_ids_requested": list[str] | None,
          "edge_count": int,
          "edges": [
            {
              "edge_id": str,
              "from_signal_id": str,
              "to_signal_id": str,
              "edge_type": str,
              "weight": float,
              "source_citation": str,
              "ayanamsha_id": str,
              "build_id": str | None,
            }, ...
          ]
        }
    """
    import psycopg  # type: ignore

    conditions: list[str] = ["chart_id = %s"]
    params: list[Any] = [chart_id]

    if ayanamsha_id:
        conditions.append("ayanamsha_id = %s")
        params.append(ayanamsha_id)

    if edge_types:
        placeholders = ", ".join("%s" for _ in edge_types)
        conditions.append(f"edge_type IN ({placeholders})")
        params.extend(edge_types)

    # BFS traversal over signal_ids
    if signal_ids:
        visited_nodes: set[str] = set(signal_ids)
        frontier: set[str] = set(signal_ids)

        with _get_conn() as conn:
            for _hop in range(hops):
                if not frontier:
                    break
                phs = ", ".join("%s" for _ in frontier)
                hop_conds = list(conditions)
                hop_params = list(params)
                hop_conds.append(
                    f"(from_signal_id IN ({phs}) OR to_signal_id IN ({phs}))"
                )
                hop_params.extend(frontier)
                hop_params.extend(frontier)

                where = " AND ".join(hop_conds)
                sql = f"""
                    SELECT edge_id, from_signal_id, to_signal_id,
                           edge_type, weight, source_citation, ayanamsha_id, build_id
                    FROM bodha_graph
                    WHERE {where}
                    ORDER BY edge_type, edge_id
                """
                rows = conn.execute(sql, hop_params).fetchall()
                new_frontier: set[str] = set()
                for r in rows:
                    for nid in (r[1], r[2]):
                        if nid not in visited_nodes:
                            new_frontier.add(nid)
                            visited_nodes.add(nid)
                frontier = new_frontier

            # Final fetch: all edges touching any visited node
            phs = ", ".join("%s" for _ in visited_nodes)
            final_conds = list(conditions)
            final_params = list(params)
            final_conds.append(
                f"(from_signal_id IN ({phs}) OR to_signal_id IN ({phs}))"
            )
            final_params.extend(visited_nodes)
            final_params.extend(visited_nodes)

            where = " AND ".join(final_conds)
            sql = f"""
                SELECT edge_id, from_signal_id, to_signal_id,
                       edge_type, weight, source_citation, ayanamsha_id, build_id
                FROM bodha_graph
                WHERE {where}
                ORDER BY edge_type, edge_id
            """
            rows = conn.execute(sql, final_params).fetchall()
    else:
        where = " AND ".join(conditions)
        sql = f"""
            SELECT edge_id, from_signal_id, to_signal_id,
                   edge_type, weight, source_citation, ayanamsha_id, build_id
            FROM bodha_graph
            WHERE {where}
            ORDER BY edge_type, edge_id
        """
        with _get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()

    edges = [
        {
            "from": r[1],
            "to": r[2],
            "type": r[3],
            "weight": float(r[4]) if r[4] is not None else None,
            "source_citation": r[5],
            # extended fields for internal / gate use
            "edge_id": r[0],
            "ayanamsha_id": r[6],
            "build_id": r[7],
        }
        for r in rows
    ]

    return {
        "edges": edges,
        "provenance_envelope": {
            "source": "bodha.graph",
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "chart_id": chart_id,
            "signal_ids_requested": signal_ids,
            "edge_count": len(edges),
        },
    }


# ── Ayanamsha-context re-derivation (Stream E, e4) ───────────────────────────

# Graha name → signal ID prefix (matches CGM node IDs in CANONICAL_EDGES)
_GRAHA_TO_SIGNAL: dict[str, str] = {
    "Sun":     "PLN.SUN",
    "Moon":    "PLN.MOON",
    "Mars":    "PLN.MARS",
    "Mercury": "PLN.MERCURY",
    "Jupiter": "PLN.JUPITER",
    "Venus":   "PLN.VENUS",
    "Saturn":  "PLN.SATURN",
    "Rahu":    "PLN.RAHU",
    "Ketu":    "PLN.KETU",
}

# Threshold: if two ayanamshas place a planet this many degrees from a sign or
# nakshatra boundary, the edge is flagged as potentially ayanamsha_dependent.
BOUNDARY_PROXIMITY_DEG: float = 0.30  # ~18 arc-minutes

# Sign boundaries: every 30.0°; Nakshatra boundaries: every 13.333°
SIGN_BOUNDARY_INTERVAL = 30.0
NAKSHATRA_BOUNDARY_INTERVAL = 360.0 / 27  # ~13.333°


def _distance_to_nearest_boundary(lon: float, interval: float) -> float:
    """Return the minimum angular distance from lon to the nearest multiple of interval."""
    remainder = lon % interval
    return min(remainder, interval - remainder)


def detect_ayanamsha_dependent_edges(
    chart_id: str,
    *,
    ayanamsha_pair: tuple[str, str] = ("lahiri", "kp"),
    boundary_threshold_deg: float = BOUNDARY_PROXIMITY_DEG,
) -> dict[str, Any]:
    """
    Detect bodha_graph edges whose involved planets fall near sign/nakshatra
    boundaries under at least one of the two ayanamshas in the pair.

    When a planet is near a boundary, different ayanamsha offsets may place it
    in different signs or nakshatras, changing the edge's semantic meaning
    (sign-lord changes → 'modulate' target changes; nakshatra-lord changes →
    'amplify' target changes). These edges are tagged AYANAMSHA_DEPENDENT.

    Args:
        chart_id:             UUID of the chart.
        ayanamsha_pair:       Pair of ayanamsha keys to compare (default lahiri+kp).
        boundary_threshold_deg: Minimum distance from boundary to flag (default 0.30°).

    Returns:
        {
          "chart_id": str,
          "ayanamsha_pair": [str, str],
          "boundary_threshold_deg": float,
          "ayanamsha_dependent_edges": [
            {
              "edge_id": str,
              "from_signal_id": str,
              "to_signal_id": str,
              "planet": str,
              "distance_to_boundary_deg": float,
              "boundary_type": "sign" | "nakshatra",
              "ayanamsha_context": str,
              "sidereal_longitude": float,
            }
          ],
          "total_edges_scanned": int,
          "dependent_count": int,
          "provenance_envelope": dict,
        }
    """
    aya_a, aya_b = ayanamsha_pair

    # Step 1: Fetch current edges for the chart (all ayanamshas)
    try:
        with _get_conn() as conn:
            rows = conn.execute(
                """
                SELECT edge_id, from_signal_id, to_signal_id, edge_type, ayanamsha_id
                FROM bodha_graph
                WHERE chart_id = %s
                ORDER BY edge_id
                """,
                (chart_id,),
            ).fetchall()
    except Exception as exc:
        logger.error("[bo22] detect_ayanamsha_dependent_edges DB read failed: %s", exc)
        return {
            "chart_id": chart_id,
            "error": str(exc),
            "ayanamsha_dependent_edges": [],
        }

    # Step 2: Fetch ganita_positions for both ayanamshas
    positions_by_aya: dict[str, dict[str, dict]] = {}
    try:
        with _get_conn() as conn:
            pos_rows = conn.execute(
                """
                SELECT ayanamsha_id, planet, sidereal_longitude
                FROM ganita_positions
                WHERE chart_id = %s AND ayanamsha_id = ANY(%s)
                ORDER BY ayanamsha_id, planet
                """,
                (chart_id, list(ayanamsha_pair)),
            ).fetchall()
        for pr in pos_rows:
            aya_id, planet, sid_lon = pr[0], pr[1], pr[2]
            positions_by_aya.setdefault(aya_id, {})[planet] = {
                "sidereal_longitude": float(sid_lon),
            }
    except Exception as exc:
        logger.warning(
            "[bo22] ganita_positions not available, skipping boundary check: %s", exc
        )
        positions_by_aya = {}

    # Step 3: Identify signal IDs that map to grahas near boundaries
    dependent_entries: list[dict[str, Any]] = []

    # Build reverse map: signal_id → graha name
    _SIGNAL_TO_GRAHA = {v: k for k, v in _GRAHA_TO_SIGNAL.items()}

    scanned = 0
    for row in rows:
        edge_id, from_sig, to_sig, edge_type, aya_id = row
        scanned += 1

        # Check both from_signal_id and to_signal_id
        for sig_id in (from_sig, to_sig):
            graha = _SIGNAL_TO_GRAHA.get(sig_id)
            if graha is None:
                continue  # Not a planet signal (e.g. HSE.* or SGN.*)

            # Check across both ayanamshas
            for check_aya in (aya_a, aya_b):
                pos = positions_by_aya.get(check_aya, {}).get(graha)
                if pos is None:
                    continue  # Position not available for this ayanamsha

                sid_lon = pos["sidereal_longitude"]

                # Check sign boundary proximity
                sign_dist = _distance_to_nearest_boundary(sid_lon, SIGN_BOUNDARY_INTERVAL)
                if sign_dist <= boundary_threshold_deg:
                    dependent_entries.append({
                        "edge_id":                   edge_id,
                        "from_signal_id":            from_sig,
                        "to_signal_id":              to_sig,
                        "planet":                    graha,
                        "distance_to_boundary_deg":  round(sign_dist, 4),
                        "boundary_type":             "sign",
                        "ayanamsha_context":         check_aya,
                        "sidereal_longitude":        round(sid_lon, 6),
                    })

                # Check nakshatra boundary proximity
                nak_dist = _distance_to_nearest_boundary(sid_lon, NAKSHATRA_BOUNDARY_INTERVAL)
                if nak_dist <= boundary_threshold_deg:
                    dependent_entries.append({
                        "edge_id":                   edge_id,
                        "from_signal_id":            from_sig,
                        "to_signal_id":              to_sig,
                        "planet":                    graha,
                        "distance_to_boundary_deg":  round(nak_dist, 4),
                        "boundary_type":             "nakshatra",
                        "ayanamsha_context":         check_aya,
                        "sidereal_longitude":        round(sid_lon, 6),
                    })

    # Deduplicate by (edge_id, planet, boundary_type, ayanamsha_context)
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for entry in dependent_entries:
        key = (entry["edge_id"], entry["planet"],
               entry["boundary_type"], entry["ayanamsha_context"])
        if key not in seen:
            seen.add(key)
            deduped.append(entry)

    logger.info(
        "[bo22] detect_ayanamsha_dependent_edges: chart=%s scanned=%d dependent=%d",
        chart_id, scanned, len(deduped),
    )

    return {
        "chart_id":                    chart_id,
        "ayanamsha_pair":              list(ayanamsha_pair),
        "boundary_threshold_deg":      boundary_threshold_deg,
        "ayanamsha_dependent_edges":   deduped,
        "total_edges_scanned":         scanned,
        "dependent_count":             len(deduped),
        "provenance_envelope": {
            "source":      "bodha.graph + ganita_positions",
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "chart_id":    chart_id,
            "method":      "boundary_proximity",
        },
    }


# ── Acceptance gate ───────────────────────────────────────────────────────────


def run_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    Run the BO-2-2 acceptance gate against a seeded chart.

    Gate criteria:
      1. bodha_graph has ≥5 edges for this chart_id (FORENSIC minimum).
      2. All edges carry a non-empty source_citation (provenance present).
      3. No self-loops exist (from_signal_id = to_signal_id).
      4. At least 3 distinct edge_types are present.
      5. cgm_subgraph traversal on ['PLN.SATURN', 'PLN.MARS'] returns ≥3 edges.

    Returns dict with keys: passed (bool), checks (list of check results).
    """
    checks: list[dict[str, Any]] = []

    # Check 1: minimum edge count
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM bodha_graph WHERE chart_id = %s", (chart_id,)
            ).fetchone()
            total_edges = int(row[0]) if row else 0

        checks.append(
            {
                "id": "AC1",
                "desc": f"bodha_graph has ≥5 edges for chart_id={chart_id}",
                "passed": total_edges >= 5,
                "value": total_edges,
            }
        )
    except Exception as exc:
        checks.append(
            {
                "id": "AC1",
                "desc": "bodha_graph row count",
                "passed": False,
                "error": str(exc),
            }
        )

    # Check 2: all edges have non-empty source_citation
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM bodha_graph "
                "WHERE chart_id = %s AND (source_citation IS NULL OR source_citation = '')",
                (chart_id,),
            ).fetchone()
            null_citations = int(row[0]) if row else 0

        checks.append(
            {
                "id": "AC2",
                "desc": "All edges have non-empty source_citation (provenance)",
                "passed": null_citations == 0,
                "value": null_citations,
            }
        )
    except Exception as exc:
        checks.append(
            {
                "id": "AC2",
                "desc": "source_citation completeness",
                "passed": False,
                "error": str(exc),
            }
        )

    # Check 3: no self-loops
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM bodha_graph "
                "WHERE chart_id = %s AND from_signal_id = to_signal_id",
                (chart_id,),
            ).fetchone()
            self_loops = int(row[0]) if row else 0

        checks.append(
            {
                "id": "AC3",
                "desc": "No self-loops (from_signal_id ≠ to_signal_id)",
                "passed": self_loops == 0,
                "value": self_loops,
            }
        )
    except Exception as exc:
        checks.append(
            {
                "id": "AC3",
                "desc": "Self-loop check",
                "passed": False,
                "error": str(exc),
            }
        )

    # Check 4: at least 3 distinct edge types
    try:
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT edge_type FROM bodha_graph WHERE chart_id = %s",
                (chart_id,),
            ).fetchall()
            distinct_types = [r[0] for r in rows]

        checks.append(
            {
                "id": "AC4",
                "desc": "At least 3 distinct edge_types present",
                "passed": len(distinct_types) >= 3,
                "value": distinct_types,
            }
        )
    except Exception as exc:
        checks.append(
            {
                "id": "AC4",
                "desc": "Distinct edge types",
                "passed": False,
                "error": str(exc),
            }
        )

    # Check 5: traversal on seed nodes returns ≥3 edges
    try:
        result = query_cgm_subgraph(
            chart_id, signal_ids=["PLN.SATURN", "PLN.MARS"], hops=1
        )
        traversal_edges = result["provenance_envelope"]["edge_count"]
        checks.append(
            {
                "id": "AC5",
                "desc": "Traversal on [PLN.SATURN, PLN.MARS] returns ≥3 edges",
                "passed": traversal_edges >= 3,
                "value": traversal_edges,
            }
        )
    except Exception as exc:
        checks.append(
            {
                "id": "AC5",
                "desc": "Traversal returns ≥3 edges",
                "passed": False,
                "error": str(exc),
            }
        )

    passed = all(c["passed"] for c in checks)
    result = {"chart_id": chart_id, "gate_passed": passed, "checks": checks}

    if passed:
        logger.info("BO-2-2 acceptance gate PASSED for chart_id=%s", chart_id)
    else:
        failed = [c["id"] for c in checks if not c["passed"]]
        logger.error("BO-2-2 acceptance gate FAILED for chart_id=%s — %s", chart_id, failed)

    return result


# ── CLI ────────────────────────────────────────────────────────────────────────


def _cmd_seed(args: argparse.Namespace) -> None:
    chart_id = args.chart_id or NATIVE_CHART_ID
    count = seed_bodha_graph(
        chart_id,
        ayanamsha_id=getattr(args, "ayanamsha_id", "lahiri"),
        build_id=getattr(args, "build_id", None),
        dry_run=getattr(args, "dry_run", False),
    )
    print(f"bodha_graph seeded: {count} edges for chart_id={chart_id}")


def _cmd_query(args: argparse.Namespace) -> None:
    chart_id = args.chart_id or NATIVE_CHART_ID
    signal_ids = getattr(args, "signal_ids", None) or None
    result = query_cgm_subgraph(chart_id, signal_ids=signal_ids)
    print(json.dumps(result, indent=2))


def _cmd_gate(args: argparse.Namespace) -> None:
    chart_id = args.chart_id or NATIVE_CHART_ID
    result = run_acceptance_gate(chart_id)
    print(json.dumps(result, indent=2))
    if not result["gate_passed"]:
        sys.exit(1)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="BRAHMA-BO-2-2: bodha.graph CGM signal graph"
    )
    parser.add_argument(
        "--chart-id", default=None, help="Chart UUID (default: native FORENSIC chart)"
    )

    sub = parser.add_subparsers(dest="command")

    # seed
    p_seed = sub.add_parser("seed", help="Seed bodha_graph for a chart")
    p_seed.add_argument("--ayanamsha-id", default="lahiri")
    p_seed.add_argument("--build-id", default=None)
    p_seed.add_argument("--dry-run", action="store_true")

    # query
    p_query = sub.add_parser("query", help="Query cgm_subgraph for a chart")
    p_query.add_argument(
        "--signal-ids",
        nargs="*",
        help="Seed signal node IDs (e.g. PLN.SATURN PLN.MARS)",
    )

    # gate
    sub.add_parser("gate", help="Run acceptance gate (exits 1 if FAIL)")

    args = parser.parse_args()
    if args.command == "seed":
        _cmd_seed(args)
    elif args.command == "query":
        _cmd_query(args)
    elif args.command == "gate":
        _cmd_gate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
