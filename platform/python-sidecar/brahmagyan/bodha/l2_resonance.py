"""
brahmagyan.bodha.l2_resonance — BRAHMA-BO-2-4 (L2 Bodha, l2-bodha-scaffold)
=============================================================================

Scaffolds RM (Resonance Map) resonance patterns into chart_facts:
  fact_category = 'bodha.resonance'
  fact_subject  = pattern_id  (e.g. 'RM.01')
  fact_value    = {pattern_id, element_text, domains_primary, signals_involved,
                   resonance_type, strength, constructive_resonance,
                   destructive_resonance, net_resonance, provenance_envelope}

Source: 025_HOLISTIC_SYNTHESIS/RM_v2_0.md (v2.2, 35 elements RM.01–RM.35 + RM.21A/B)
Volume floor: as many as parsed (≥ 25 expected from RM_v2_0.md)

All rows UNGROUNDED (rule_id=null, awaiting WS-3).

Layer:  L2 Bodha (scaffold)
Asset:  bodha.resonance (BO-2-4)
Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
        chart_id: 482012f1-710e-4a25-994a-93821f5871aa

BRAHMA-BO-2-4 / l2-bodha-scaffold
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

VOLUME_FLOOR = 25
NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
SOURCE_CITATION = "025_HOLISTIC_SYNTHESIS/RM_v2_0.md"
RM_REL_PATH = "025_HOLISTIC_SYNTHESIS/RM_v2_0.md"

PROVENANCE_ENVELOPE = {
    "layer": "L2",
    "asset": "bodha.resonance",
    "asset_id": "BO-2-4",
    "scaffold_pass": "l2-bodha-scaffold",
    "grounding_status": "UNGROUNDED",
    "grounding_note": "Scaffold pass — awaiting WS-3 rule_base",
    "rule_id": None,
}

# Heading pattern: ### RM.01 — ..., ### RM.21A — ...
_HEADING_RE = re.compile(r"^###\s+(RM\.\d+[A-Z]?)\s*[—–-]\s*(.+)$", re.MULTILINE)

_NET_STRONGLY_AMPLIFIED = re.compile(r"STRONGLY\s+AMPLIFIED", re.I)
_NET_TENSION_BEARING = re.compile(r"TENSION.BEARING", re.I)
_NET_MIXED = re.compile(r"MIXED|COMPENSATED|BENEFIC BUT", re.I)
_NET_ACTIVE = re.compile(r"ACTIVE|AMPLIFIED", re.I)


# ── RM parser ─────────────────────────────────────────────────────────────────

def _resolve_rm(rm_path: Path | None = None) -> Path:
    if rm_path and rm_path.exists():
        return rm_path
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent,
                   here.parent.parent.parent,
                   here.parent.parent.parent.parent]:
        candidate = parent / RM_REL_PATH
        if candidate.exists():
            return candidate
    repo_root = Path(os.environ.get("MARSYS_REPO_ROOT", ""))
    if repo_root:
        candidate = repo_root / RM_REL_PATH
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"RM not found at {RM_REL_PATH}")


def _parse_rm(rm_path: Path) -> list[dict[str, Any]]:
    """
    Parse RM_v2_0.md headings and YAML blocks.

    Returns list of resonance pattern dicts.
    """
    text = rm_path.read_text(encoding="utf-8")
    elements: list[dict[str, Any]] = []

    matches = list(_HEADING_RE.finditer(text))
    for idx, m in enumerate(matches):
        rm_id = m.group(1).strip()
        elem_title = m.group(2).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end]
        elem = _parse_element(rm_id, elem_title, body)
        elements.append(elem)

    logger.info("[l2_resonance] Parsed %d RM elements", len(elements))
    return elements


def _extract_yaml_block(body: str) -> dict[str, Any]:
    """Extract the first YAML code block from a markdown section."""
    yaml_match = re.search(r"```ya?ml\s*\n(.*?)```", body, re.DOTALL | re.IGNORECASE)
    if not yaml_match:
        return {}
    yaml_text = yaml_match.group(1)
    result: dict[str, Any] = {}
    for line in yaml_text.splitlines():
        m = re.match(r"^(\s*)(\w[\w_-]*):\s*(.*)", line)
        if m and not m.group(1):  # top-level only
            key = m.group(2)
            value = m.group(3).strip().strip('"').strip("'")
            result[key] = value
    return result


def _parse_element(rm_id: str, title: str, body: str) -> dict[str, Any]:
    """Parse a single RM element block."""
    elem: dict[str, Any] = {
        "pattern_id": rm_id,
        "element_text": title,
    }

    # Extract YAML block
    yaml_data = _extract_yaml_block(body)

    # element description
    if "element" in yaml_data:
        elem["element_text"] = yaml_data["element"]

    # domains_primary
    dp_raw = yaml_data.get("domains_primary", "")
    if dp_raw:
        inner = re.sub(r"[\[\]]", "", dp_raw)
        elem["domains_primary"] = [d.strip() for d in inner.split(",") if d.strip()]
    else:
        elem["domains_primary"] = []

    # msr_anchors as signals_involved
    msr_raw = yaml_data.get("msr_anchors", "")
    if msr_raw:
        inner = re.sub(r"[\[\]]", "", msr_raw)
        # Handle inline comments
        anchors = []
        for part in inner.split(","):
            anchor = re.sub(r"\(.*?\)", "", part).strip()
            if anchor:
                anchors.append(anchor)
        elem["signals_involved"] = anchors
    else:
        elem["signals_involved"] = []

    # net_resonance
    net_raw = yaml_data.get("net_resonance", "")
    elem["net_resonance"] = net_raw

    # Classify resonance_type from net_resonance
    if _NET_STRONGLY_AMPLIFIED.search(net_raw):
        resonance_type = "strongly_amplified"
        strength = 0.90
    elif _NET_TENSION_BEARING.search(net_raw):
        resonance_type = "tension_bearing"
        strength = 0.75
    elif _NET_MIXED.search(net_raw):
        resonance_type = "mixed"
        strength = 0.65
    elif _NET_ACTIVE.search(net_raw):
        resonance_type = "amplified"
        strength = 0.80
    else:
        resonance_type = "neutral"
        strength = 0.60

    elem["resonance_type"] = resonance_type
    elem["strength"] = strength

    # constructive / destructive summary (first 300 chars of each list)
    constructive_raw = yaml_data.get("constructive_resonance", "")
    elem["constructive_resonance"] = constructive_raw[:300] if constructive_raw else ""

    destructive_raw = yaml_data.get("destructive_resonance", "")
    elem["destructive_resonance"] = destructive_raw[:300] if destructive_raw else ""

    # interpretive_note
    elem["interpretive_note"] = yaml_data.get("interpretive_note", "")[:400]

    return elem


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l2_resonance] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


# ── chart_facts writer ─────────────────────────────────────────────────────────

def seed_resonance(
    chart_id: str,
    *,
    build_id: str | None = None,
    rm_path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Parse RM_v2_0.md and write resonance patterns into chart_facts.

    All rows UNGROUNDED (rule_id=null).
    Returns: { seeded: int, volume_floor: int, volume_met: bool }
    """
    from datetime import date
    build_id = build_id or f"l2-resonance-{date.today().isoformat()}"

    path = _resolve_rm(rm_path)
    elements = _parse_rm(path)

    if dry_run:
        return {
            "seeded": 0, "dry_run": True, "parsed": len(elements),
            "volume_floor": VOLUME_FLOOR,
            "volume_met": len(elements) >= VOLUME_FLOOR,
        }

    rows_written = 0
    with _conn() as conn:
        for elem in elements:
            fact_value = {
                "pattern_id":            elem["pattern_id"],
                "element_text":          elem["element_text"],
                "domains_primary":       elem["domains_primary"],
                "signals_involved":      elem["signals_involved"],
                "resonance_type":        elem["resonance_type"],
                "strength":              elem["strength"],
                "net_resonance":         elem["net_resonance"],
                "constructive_resonance":elem["constructive_resonance"],
                "destructive_resonance": elem["destructive_resonance"],
                "interpretive_note":     elem["interpretive_note"],
                "layer":                 "L2",
                "rule_id":               None,  # NULL — WS-3 provides rules
                "provenance_envelope": {
                    **PROVENANCE_ENVELOPE,
                    "pattern_id": elem["pattern_id"],
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
                    "bodha.resonance",
                    elem["pattern_id"],
                    json.dumps(fact_value),
                    SOURCE_CITATION,
                    build_id,
                ],
            )
            rows_written += 1
        conn.commit()

    logger.info("[l2_resonance] Wrote %d elements for chart=%s", rows_written, chart_id)
    return {
        "seeded":       rows_written,
        "volume_floor": VOLUME_FLOOR,
        "volume_met":   rows_written >= VOLUME_FLOOR,
        "grounding_status": "UNGROUNDED",
        "rule_id":      None,
        "build_id":     build_id,
    }


def check_volume(rm_path: Path | None = None) -> dict[str, Any]:
    """Volume check — parse RM without DB."""
    try:
        path = _resolve_rm(rm_path)
        elements = _parse_rm(path)
        actual = len(elements)
        type_counts: dict[str, int] = {}
        for e in elements:
            t = e.get("resonance_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "status":               "GREEN" if actual >= VOLUME_FLOOR else "AMBER",
            "volume_floor":         VOLUME_FLOOR,
            "actual":               actual,
            "grounding_status":     "UNGROUNDED",
            "resonance_type_counts":type_counts,
        }
    except Exception as exc:
        return {"status": "RED", "volume_floor": VOLUME_FLOOR, "actual": 0, "error": str(exc)}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    parser = argparse.ArgumentParser(description="l2_resonance — bodha.resonance (RM)")
    sub = parser.add_subparsers(dest="cmd")

    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--chart-id", default=NATIVE_CHART_ID)
    p_seed.add_argument("--build-id", default=None)
    p_seed.add_argument("--dry-run", action="store_true")

    p_check = sub.add_parser("check")

    args = parser.parse_args()
    if args.cmd == "seed":
        result = seed_resonance(args.chart_id, build_id=args.build_id, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    elif args.cmd == "check":
        result = check_volume()
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
        sys.exit(1)
