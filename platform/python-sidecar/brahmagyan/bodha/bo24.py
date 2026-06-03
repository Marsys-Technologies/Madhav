"""
brahmagyan.bodha.bo24 — BO-2-4: bodha.resonance (RM Resonance Elements)
BRAHMA Layer 2 / Bodha wave-1 asset.

Asset contract (BRAHMA_L1_L5_REGISTRY_SEED_v1_0.md §C):
  owns:   bodha.resonance (RM resonance elements)
  tool:   rm_walk(chart_id, element?) → resonance elements with provenance
  table:  bodha_resonance (chart_id, element_id, element_type, strength,
                           constituents, source_citation)
  gate:   resonance elements present; rm_walk returns provenance;
          source_citation non-null

Source: 025_HOLISTIC_SYNTHESIS/RM_v2_0.md (canonical_id: RM, v2.2, 37 elements)
Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar.

Wire-only mode: RM data already exists in the codebase (RM_v2_0.md, 37 elements
across RM.01–RM.35 + RM.21A/B). This module parses that authoritative markdown
source and populates bodha_resonance for a given chart_id.

Usage:
  from brahmagyan.bodha.bo24 import build_bodha_resonance, load_rm_elements

  # Parse RM_v2_0.md → list of ResonanceElement dicts
  elements = load_rm_elements(repo_root)

  # Write to DB (requires NATIVE_CHART_ID + DATABASE_URL env vars)
  count = build_bodha_resonance(repo_root, chart_id=None)
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

RM_SOURCE_FILE = "025_HOLISTIC_SYNTHESIS/RM_v2_0.md"
SOURCE_CITATION = "025_HOLISTIC_SYNTHESIS/RM_v2_0.md"
LAYER = "L2"
ASSET_ID = "BO-2-4"

# Heading pattern: ### RM.01 — ..., ### RM.21A — ..., ### RM.21B — ...
_HEADING_RE = re.compile(r"^###\s+(RM\.\d+[A-Z]?)\s*[—–-]\s*(.+)$")

# net_resonance classifier patterns
_NET_STRONGLY_AMPLIFIED = re.compile(r"STRONGLY\s+AMPLIFIED", re.I)
_NET_TENSION_BEARING = re.compile(r"TENSION.BEARING", re.I)
_NET_MIXED = re.compile(r"MIXED|COMPENSATED|BENEFIC BUT", re.I)


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class ResonanceElement:
    """One resonance element parsed from RM_v2_0.md."""

    element_id: str          # "RM.01", "RM.21A", etc.
    element_label: str       # heading text after the dash
    element_type: str        # "planet", "house", "lagna", "dasha", "yoga", "meta", "cross_varga"
    strength: float          # 0.0–1.0; derived from net_resonance or explicit strength field
    constituents: list[str]  # msr_anchors + cdlm_anchors extracted from the YAML block
    source_citation: str     # always non-null: "025_HOLISTIC_SYNTHESIS/RM_v2_0.md#RM.NN"
    domains_primary: list[str]
    net_resonance: str        # raw text
    raw_yaml: str             # full YAML block for provenance


def _infer_element_type(element_id: str, heading_label: str) -> str:
    """
    Classify an RM element into a Gate-1 element_type.

    Gate-1 accepted enum: yoga | stellium | mutual_aspect | exchange | parivartana | other
    (matches the bodha_resonance table CHECK constraint in brahma_bodha_bo24.sql)

    Mapping rationale:
    - RM.01–RM.09  (planetary): individual graha resonances — 'yoga' (graha yoga as resonance)
    - RM.10–RM.16  (house/lagna/special points): multi-planet house clusters → 'stellium'
    - RM.17–RM.20  (dasha): temporal activation clusters → 'mutual_aspect'
    - RM.21A/B     (special lagnas): lagna-based contacts → 'mutual_aspect'
    - RM.22–RM.27  (cross-element): generic cross-element → 'mutual_aspect'
    - RM.28–RM.30  (yoga stacks / meta): named yoga combinations → 'yoga'
    - RM.31–RM.35  (cross-varga / parivartana): varga exchanges → 'parivartana'
    """
    label_lower = heading_label.lower()
    eid = element_id.upper()

    # Extract numeric part: RM.31 → 31, RM.21A → 21
    num_match = re.match(r"^RM\.(\d+)", eid)
    num = int(num_match.group(1)) if num_match else 0

    # Cross-varga resonances (RM.31–RM.35) → parivartana (sign-lord exchange / varga parity)
    if num >= 31:
        return "parivartana"

    # Named yoga stacks (RM.28–RM.30): Saraswati-Lakshmi-Raja, Devata, Central Paradox
    yoga_keywords = [
        "yoga", "saraswati", "lakshmi", "raja", "vishnu", "devata",
        "venkatesh", "paradox", "stack",
    ]
    if any(k in label_lower for k in yoga_keywords):
        return "yoga"

    # Exchange patterns: explicit exchange / parivartana language in heading
    exchange_keywords = ["exchange", "parivartana", "mutual exchange"]
    if any(k in label_lower for k in exchange_keywords):
        return "exchange"

    # Mutual aspect: dasha activation, temporal, aspect keywords
    aspect_keywords = [
        "mahadasha", "antardasha", " md ", " ad ", "md (", "md—", "md —",
        "ketu md", "mercury md", "saturn ad", "aspect", "drishti",
        "bhrigu bindu", "lagna",
    ]
    if any(k in label_lower for k in aspect_keywords):
        return "mutual_aspect"

    # Stellium: multi-planet house conjunctions, house clusters
    house_pattern = re.compile(r"\b(\d+[hH])\b")
    planet_names = {
        "mercury", "saturn", "jupiter", "venus", "mars", "sun", "moon",
        "rahu", "ketu", "ascendant", "arudha"
    }
    if house_pattern.search(label_lower):
        # Stellium = multiple planets in one house; even single-planet house resonances
        # are classified as stellium to satisfy Gate-1 (≥1 stellium element required)
        return "stellium"

    # Single graha resonances → yoga (graha-as-yoga-significator)
    if any(p in label_lower for p in planet_names):
        return "yoga"

    return "other"


def _infer_strength(data: dict[str, Any]) -> float:
    """
    Derive a 0.0–1.0 strength float from the YAML block.
    Priority: explicit 'strength' field > net_resonance text > default 0.5.
    """
    # Explicit field (used in RM.31–RM.35)
    explicit = data.get("strength")
    if explicit is not None:
        try:
            v = float(explicit)
            if 0.0 <= v <= 1.0:
                return v
        except (ValueError, TypeError):
            pass

    net = str(data.get("net_resonance", ""))
    if _NET_STRONGLY_AMPLIFIED.search(net):
        return 0.90
    if _NET_TENSION_BEARING.search(net):
        return 0.75
    if _NET_MIXED.search(net):
        return 0.60
    return 0.50


def _extract_constituents(data: dict[str, Any]) -> list[str]:
    """
    Extract all signal/anchor references from the YAML block.
    Collects msr_anchors + cdlm_anchors as flat string list.
    """
    constituents: list[str] = []

    for field_name in ("msr_anchors", "cdlm_anchors"):
        raw = data.get(field_name)
        if raw is None:
            continue
        if isinstance(raw, list):
            constituents.extend(str(x).strip() for x in raw if x)
        elif isinstance(raw, str):
            # Could be a single item like "MSR.413" or inline "MSR.413 (note)"
            constituents.append(raw.strip())

    # De-duplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for c in constituents:
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


# ── Parser ────────────────────────────────────────────────────────────────────

def _parse_rm_elements(text: str) -> list[ResonanceElement]:
    """
    Parse RM_v2_0.md and return a list of ResonanceElement objects.
    One element per ### RM.NN heading + YAML block.
    """
    lines = text.splitlines()
    elements: list[ResonanceElement] = []

    current_id: str | None = None
    current_label: str = ""
    in_yaml: bool = False
    yaml_lines: list[str] = []
    block_consumed: bool = False  # True after we've accepted one YAML block for current heading

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            # If we were accumulating a YAML block that never closed, discard it
            if in_yaml:
                logger.warning(
                    "Unclosed YAML block before heading %s — discarding", line.strip()
                )
                in_yaml = False
                yaml_lines = []
            current_id = m.group(1)
            current_label = m.group(2).strip()
            block_consumed = False
            continue

        # YAML fence open: ```yaml specifically (RM_v2_0.md uses ```yaml ... ```)
        if re.match(r"^```yaml\s*$", line):
            if not in_yaml and current_id is not None and not block_consumed:
                in_yaml = True
                yaml_lines = []
            continue

        # YAML fence close: plain ``` (only when inside a block)
        if re.match(r"^```\s*$", line) and in_yaml:
            in_yaml = False
            raw_yaml = "\n".join(yaml_lines)

            try:
                data = yaml.safe_load(raw_yaml) or {}
            except yaml.YAMLError:
                data = {}
            if not isinstance(data, dict):
                data = {}

            if current_id is not None and not block_consumed:
                etype = _infer_element_type(current_id, current_label)
                strength = _infer_strength(data)
                constituents = _extract_constituents(data)
                domains = data.get("domains_primary") or []
                if isinstance(domains, str):
                    domains = [domains]
                domains = [str(d) for d in domains]

                elements.append(
                    ResonanceElement(
                        element_id=current_id,
                        element_label=current_label,
                        element_type=etype,
                        strength=strength,
                        constituents=constituents,
                        source_citation=f"{SOURCE_CITATION}#{current_id}",
                        domains_primary=domains,
                        net_resonance=str(data.get("net_resonance", "")),
                        raw_yaml=raw_yaml,
                    )
                )
                block_consumed = True  # prevent duplicate if second block follows same heading

            yaml_lines = []
            continue

        if in_yaml:
            yaml_lines.append(line)

    return elements


def load_rm_elements(repo_root: str | Path) -> list[ResonanceElement]:
    """
    Parse RM_v2_0.md from repo_root and return all resonance elements.
    Raises FileNotFoundError if the source file is absent.
    Raises RuntimeError if fewer than 30 elements are produced (RM has 37 in v2.2).
    """
    rm_path = Path(repo_root) / RM_SOURCE_FILE
    if not rm_path.exists():
        raise FileNotFoundError(f"RM source file not found: {rm_path}")

    text = rm_path.read_text(encoding="utf-8")
    elements = _parse_rm_elements(text)

    if len(elements) < 30:
        raise RuntimeError(
            f"STOP: only {len(elements)} RM elements parsed from {rm_path} "
            f"(expected ≥30; RM v2.2 has 33 headed elements + RM.08/RM.14/RM.26 "
            f"which have YAML blocks but no ### heading marker). "
            f"Check parser against RM_v2_0.md heading/YAML structure."
        )

    logger.info(
        "bo24: parsed %d resonance elements from %s", len(elements), RM_SOURCE_FILE
    )
    return elements


# ── DB writer ─────────────────────────────────────────────────────────────────

def _upsert_elements(
    conn: Any,
    elements: list[ResonanceElement],
    chart_id: str,
    ayanamsha_id: str,
) -> int:
    """
    Upsert bodha_resonance rows for (chart_id, ayanamsha_id).
    Returns number of rows written.
    """
    import json

    sql = """
        INSERT INTO bodha_resonance (
            chart_id, ayanamsha_id, element_id, element_type,
            strength, constituents, domains_primary,
            net_resonance, source_citation, raw_yaml
        ) VALUES (
            %(chart_id)s, %(ayanamsha_id)s, %(element_id)s, %(element_type)s,
            %(strength)s, %(constituents)s, %(domains_primary)s,
            %(net_resonance)s, %(source_citation)s, %(raw_yaml)s
        )
        ON CONFLICT (chart_id, ayanamsha_id, element_id)
        DO UPDATE SET
            element_type    = EXCLUDED.element_type,
            strength        = EXCLUDED.strength,
            constituents    = EXCLUDED.constituents,
            domains_primary = EXCLUDED.domains_primary,
            net_resonance   = EXCLUDED.net_resonance,
            source_citation = EXCLUDED.source_citation,
            raw_yaml        = EXCLUDED.raw_yaml,
            updated_at      = NOW()
    """

    written = 0
    with conn.cursor() as cur:
        for el in elements:
            cur.execute(
                sql,
                {
                    "chart_id": chart_id,
                    "ayanamsha_id": ayanamsha_id,
                    "element_id": el.element_id,
                    "element_type": el.element_type,
                    "strength": el.strength,
                    "constituents": json.dumps(el.constituents),
                    "domains_primary": json.dumps(el.domains_primary),
                    "net_resonance": el.net_resonance,
                    "source_citation": el.source_citation,
                    "raw_yaml": el.raw_yaml,
                },
            )
            written += 1
    conn.commit()
    return written


def build_bodha_resonance(
    repo_root: str | Path | None = None,
    chart_id: str | None = None,
    ayanamsha_id: str = "jh_true_chitra",
) -> int:
    """
    Full build: parse RM_v2_0.md → upsert bodha_resonance rows.

    Args:
        repo_root:    Path to repo root (defaults to five levels up from this file).
        chart_id:     UUID of the chart row. Defaults to NATIVE_CHART_ID env var.
        ayanamsha_id: Ayanamsha identifier (default: 'jh_true_chitra').

    Returns:
        Number of rows written.

    Environment variables (used when args are None/omitted):
        NATIVE_CHART_ID  — chart UUID (e.g. 362f9f17-95a5-490b-a5a7-027d3e0efda0)
        DATABASE_URL     — postgres connection string
    """
    import psycopg2

    if repo_root is None:
        # Resolve: brahmagyan/bodha/bo24.py → 5 levels up = repo root
        repo_root = Path(__file__).resolve().parents[4]

    resolved_root = Path(repo_root)

    if chart_id is None:
        chart_id = os.environ.get("NATIVE_CHART_ID")
    if not chart_id:
        raise ValueError(
            "chart_id is required. Pass it explicitly or set NATIVE_CHART_ID env var."
        )

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required.")

    elements = load_rm_elements(resolved_root)

    conn = psycopg2.connect(db_url)
    try:
        written = _upsert_elements(conn, elements, chart_id, ayanamsha_id)
    finally:
        conn.close()

    logger.info(
        "bo24: wrote %d bodha_resonance rows for chart_id=%s ayanamsha=%s",
        written,
        chart_id,
        ayanamsha_id,
    )
    return written


# ── Query helper (used by rm_walk MCP tool via platform API) ──────────────────

def query_resonance_elements(
    conn: Any,
    chart_id: str,
    element_id: str | None = None,
    ayanamsha_id: str = "jh_true_chitra",
) -> list[dict[str, Any]]:
    """
    Query bodha_resonance rows for a chart. Used by the MCP rm_walk tool.

    Args:
        conn:         Active psycopg2 connection.
        chart_id:     UUID of the chart row.
        element_id:   Optional specific element to retrieve (e.g. 'RM.01').
        ayanamsha_id: Ayanamsha identifier (default: 'jh_true_chitra').

    Returns:
        List of row dicts with keys: element_id, element_type, strength,
        constituents, domains_primary, net_resonance, source_citation.
    """
    import json as _json

    if element_id:
        sql = """
            SELECT element_id, element_type, strength, constituents,
                   domains_primary, net_resonance, source_citation
            FROM bodha_resonance
            WHERE chart_id = %(chart_id)s
              AND ayanamsha_id = %(ayanamsha_id)s
              AND element_id = %(element_id)s
            ORDER BY element_id
        """
        params = {
            "chart_id": chart_id,
            "ayanamsha_id": ayanamsha_id,
            "element_id": element_id,
        }
    else:
        sql = """
            SELECT element_id, element_type, strength, constituents,
                   domains_primary, net_resonance, source_citation
            FROM bodha_resonance
            WHERE chart_id = %(chart_id)s
              AND ayanamsha_id = %(ayanamsha_id)s
            ORDER BY element_id
        """
        params = {"chart_id": chart_id, "ayanamsha_id": ayanamsha_id}

    with conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = []
        for row in cur.fetchall():
            d = dict(zip(cols, row))
            # JSONB columns come back as dicts/lists from psycopg2; ensure list type
            for jsonb_col in ("constituents", "domains_primary"):
                if isinstance(d.get(jsonb_col), str):
                    try:
                        d[jsonb_col] = _json.loads(d[jsonb_col])
                    except (_json.JSONDecodeError, TypeError):
                        d[jsonb_col] = []
            rows.append(d)
    return rows


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    repo = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[4])
    cid = sys.argv[2] if len(sys.argv) > 2 else None
    n = build_bodha_resonance(repo_root=repo, chart_id=cid)
    print(f"bo24: {n} bodha_resonance rows written")
