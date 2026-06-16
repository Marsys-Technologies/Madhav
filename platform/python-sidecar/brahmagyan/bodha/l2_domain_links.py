"""
brahmagyan.bodha.l2_domain_links — BRAHMA-BO-2-3 (L2 Bodha, l2-bodha-scaffold)
================================================================================

Scaffolds CDLM (Cross-Domain Linkage Matrix) cross-domain linkages into chart_facts:
  fact_category = 'bodha.domain_links'
  fact_subject  = link_id  (e.g. 'CDLM.D1.D2')
  fact_value    = {source_domain, target_domain, link_type, msr_anchors, strength,
                   direction, valence, key_finding, provenance_envelope}

Source: 025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md (81-cell matrix, 9×9 domains)
Volume floor: ≥ 20 cross-domain links (actual: 81 cells)

All rows UNGROUNDED (rule_id=null, awaiting WS-3).

Layer:  L2 Bodha (scaffold)
Asset:  bodha.domain_links (BO-2-3)
Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
        chart_id: 482012f1-710e-4a25-994a-93821f5871aa

BRAHMA-BO-2-3 / l2-bodha-scaffold
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 20
NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
SOURCE_CITATION = "025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md"
CDLM_REL_PATH = "025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md"

PROVENANCE_ENVELOPE = {
    "layer": "L2",
    "asset": "bodha.domain_links",
    "asset_id": "BO-2-3",
    "scaffold_pass": "l2-bodha-scaffold",
    "grounding_status": "UNGROUNDED",
    "grounding_note": "Scaffold pass — awaiting WS-3 rule_base",
    "rule_id": None,
}

DOMAIN_NAMES = {
    "D1": "Career",
    "D2": "Wealth",
    "D3": "Relationships",
    "D4": "Health",
    "D5": "Children",
    "D6": "Spirit",
    "D7": "Parents",
    "D8": "Mind",
    "D9": "Travel",
}

# ── CDLM parser ───────────────────────────────────────────────────────────────

_CELL_HEADER_RE = re.compile(r"^(CDLM\.D\d\.D\d):\s*$", re.MULTILINE)


def _resolve_cdlm(cdlm_path: Path | None = None) -> Path:
    if cdlm_path and cdlm_path.exists():
        return cdlm_path
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent,
                   here.parent.parent.parent,
                   here.parent.parent.parent.parent]:
        candidate = parent / CDLM_REL_PATH
        if candidate.exists():
            return candidate
    repo_root = Path(os.environ.get("MARSYS_REPO_ROOT", ""))
    if repo_root:
        candidate = repo_root / CDLM_REL_PATH
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"CDLM not found at {CDLM_REL_PATH}")


def _parse_cdlm(cdlm_path: Path) -> list[dict[str, Any]]:
    """
    Parse CDLM_v1_1.md and return list of link dicts.
    """
    text = cdlm_path.read_text(encoding="utf-8")
    links: list[dict[str, Any]] = []

    parts = _CELL_HEADER_RE.split(text)
    # parts[0] = preamble; then (cell_id, cell_body) pairs
    i = 1
    while i + 1 < len(parts):
        cell_id = parts[i].strip()
        body = parts[i + 1]
        link = _parse_cell(cell_id, body)
        links.append(link)
        i += 2

    logger.info("[l2_domain_links] Parsed %d CDLM cells", len(links))
    return links


def _parse_cell(cell_id: str, body: str) -> dict[str, Any]:
    """Parse a single CDLM cell body."""
    link: dict[str, Any] = {"link_id": cell_id}

    # Extract domain codes from cell_id: CDLM.DX.DY
    m = re.match(r"CDLM\.(D\d)\.(D\d)", cell_id)
    if m:
        d_src, d_tgt = m.group(1), m.group(2)
        link["source_domain_id"] = d_src
        link["target_domain_id"] = d_tgt
        link["source_domain"] = DOMAIN_NAMES.get(d_src, d_src)
        link["target_domain"] = DOMAIN_NAMES.get(d_tgt, d_tgt)
    else:
        link["source_domain_id"] = "unknown"
        link["target_domain_id"] = "unknown"
        link["source_domain"] = "unknown"
        link["target_domain"] = "unknown"

    # Parse simple key: value fields
    for line in body.splitlines():
        m2 = re.match(r"^\s{2}(\w[\w_-]*):\s*(.*)", line)
        if not m2:
            continue
        key = m2.group(1)
        value = m2.group(2).strip().strip('"').strip("'")

        if key == "linkage_type":
            link["link_type"] = value
        elif key == "strength":
            try:
                link["strength"] = float(value)
            except (ValueError, TypeError):
                link["strength"] = None
        elif key == "direction":
            link["direction"] = value
        elif key == "valence":
            link["valence"] = value
        elif key == "key_finding":
            link["key_finding"] = value
        elif key == "msr_anchors":
            inner = re.sub(r"[\[\]]", "", value)
            anchors = [a.strip() for a in inner.split(",") if a.strip()]
            link["msr_anchors"] = anchors
        elif key == "primary_mechanism":
            link["primary_mechanism"] = value[:500]  # Truncate long text

    # Defaults
    link.setdefault("link_type", "feeds")
    link.setdefault("strength", None)
    link.setdefault("direction", "row→col")
    link.setdefault("valence", "mixed")
    link.setdefault("key_finding", f"{link['source_domain']} → {link['target_domain']}")
    link.setdefault("msr_anchors", [])
    link.setdefault("primary_mechanism", "")

    return link


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l2_domain_links] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


# ── chart_facts writer ─────────────────────────────────────────────────────────

def seed_domain_links(
    chart_id: str,
    *,
    build_id: str | None = None,
    cdlm_path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Parse CDLM and write cross-domain links into chart_facts.

    Each row: fact_category='bodha.domain_links', fact_subject=cell_id (CDLM.D1.D2)
    All rows are UNGROUNDED (rule_id=null).

    Returns: { seeded: int, volume_floor: int, volume_met: bool }
    """
    from datetime import date
    build_id = build_id or f"l2-domain-links-{date.today().isoformat()}"

    path = _resolve_cdlm(cdlm_path)
    links = _parse_cdlm(path)

    if dry_run:
        return {
            "seeded": 0, "dry_run": True, "parsed": len(links),
            "volume_floor": VOLUME_FLOOR,
            "volume_met": len(links) >= VOLUME_FLOOR,
        }

    rows_written = 0
    with _conn() as conn:
        for link in links:
            fact_value = {
                "link_id":              link["link_id"],
                "source_domain":        link["source_domain"],
                "source_domain_id":     link["source_domain_id"],
                "target_domain":        link["target_domain"],
                "target_domain_id":     link["target_domain_id"],
                "link_type":            link["link_type"],
                "strength":             link["strength"],
                "direction":            link["direction"],
                "valence":              link["valence"],
                "key_finding":          link["key_finding"],
                "msr_anchors":          link["msr_anchors"],
                "primary_mechanism":    link.get("primary_mechanism", ""),
                "layer":                "L2",
                "rule_id":              None,  # NULL — WS-3 provides rules
                "provenance_envelope": {
                    **PROVENANCE_ENVELOPE,
                    "link_id": link["link_id"],
                },
            }
            conn.execute(
                """
                INSERT INTO chart_facts
                  (chart_id, fact_category, fact_subject, fact_value,
                   source_citation, build_id)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (chart_id, fact_category, fact_subject) DO UPDATE SET
                  fact_value      = EXCLUDED.fact_value,
                  source_citation = EXCLUDED.source_citation,
                  build_id        = EXCLUDED.build_id,
                  updated_at      = NOW()
                """,
                [
                    chart_id,
                    "bodha.domain_links",
                    link["link_id"],
                    json.dumps(fact_value),
                    SOURCE_CITATION,
                    build_id,
                ],
            )
            rows_written += 1
        conn.commit()

    logger.info("[l2_domain_links] Wrote %d links for chart=%s", rows_written, chart_id)
    return {
        "seeded":       rows_written,
        "volume_floor": VOLUME_FLOOR,
        "volume_met":   rows_written >= VOLUME_FLOOR,
        "grounding_status": "UNGROUNDED",
        "rule_id":      None,
        "build_id":     build_id,
    }


def check_volume(cdlm_path: Path | None = None) -> dict[str, Any]:
    """Volume check — parse CDLM without DB."""
    try:
        path = _resolve_cdlm(cdlm_path)
        links = _parse_cdlm(path)
        actual = len(links)
        return {
            "status":           "GREEN" if actual >= VOLUME_FLOOR else "AMBER",
            "volume_floor":     VOLUME_FLOOR,
            "actual":           actual,
            "grounding_status": "UNGROUNDED",
            "off_diagonal":     sum(
                1 for lk in links
                if lk.get("source_domain_id") != lk.get("target_domain_id")
            ),
        }
    except Exception as exc:
        return {"status": "RED", "volume_floor": VOLUME_FLOOR, "actual": 0, "error": str(exc)}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    parser = argparse.ArgumentParser(description="l2_domain_links — bodha.domain_links (CDLM)")
    sub = parser.add_subparsers(dest="cmd")

    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--chart-id", default=NATIVE_CHART_ID)
    p_seed.add_argument("--build-id", default=None)
    p_seed.add_argument("--dry-run", action="store_true")

    p_check = sub.add_parser("check")

    args = parser.parse_args()
    if args.cmd == "seed":
        result = seed_domain_links(args.chart_id, build_id=args.build_id, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    elif args.cmd == "check":
        result = check_volume()
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
        sys.exit(1)
